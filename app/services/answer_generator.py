"""Grounded answer generation service."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterator

from app.config import AppSettings
from app.domain import FAQEntry
from app.domain.answer_response import AnswerResponse
from app.domain.prompt_template import PromptTemplate
from app.domain.retrieval_result import RetrievalResult
from app.infrastructure import (
    OllamaClient,
    OllamaClientError,
    OllamaGenerationResult,
)
import logging

logger = logging.getLogger(__name__)

_GENERAL_CHAT_PATTERNS = (
    r"\b(hallo|hi|hey|servus|moin)\b",
    r"\b(guten morgen|guten tag|guten abend)\b",
    r"\b(danke|dankesch[oö]n|vielen dank|merci)\b",
    r"\b(tsch[üu]ss|auf wiedersehen|bis bald|bis sp[aä]ter)\b",
    r"\b(wie geht(?:'| )?s|wie l[aä]uft(?:'| )?s)\b",
    r"\b(wer bist du|was kannst du|wie kann ich mit dir reden)\b",
)
_COMPANY_HINT_TERMS = {
    "angebot",
    "angebote",
    "ausfallsicherheit",
    "beratung",
    "branche",
    "branchen",
    "cloud",
    "compliance",
    "cybersecurity",
    "datenschutz",
    "dienstleistung",
    "dienstleistungen",
    "dsgvo",
    "faq",
    "firma",
    "helpdesk",
    "kosten",
    "migration",
    "preis",
    "preise",
    "prozess",
    "prozesse",
    "service",
    "services",
    "software",
    "strategie",
    "support",
    "unternehmen",
    "vertr[aä]g",
}
_FACTUAL_CHAT_TERMS = {
    "ceo",
    "hauptstadt",
    "nachrichten",
    "news",
    "präsident",
    "praesident",
    "uhrzeit",
    "wetter",
    "zeit",
}


class AnswerGeneratorError(RuntimeError):
    """Raised when answer generation fails."""


@dataclass(slots=True)
class AnswerGenerator:
    """Generates grounded answers from retrieved FAQ context."""

    ollama_client: OllamaClient
    prompt_template: PromptTemplate
    fallback_message: str
    enable_thinking: bool = False

    @classmethod
    def from_settings(cls, settings: AppSettings) -> "AnswerGenerator":
        """Build a fully wired answer generator from application settings."""

        return cls(
            ollama_client=OllamaClient.from_settings(settings),
            prompt_template=PromptTemplate(fallback_message=settings.fallback_message),
            fallback_message=settings.fallback_message,
            enable_thinking=settings.ollama_enable_thinking,
        )

    def generate(self, question: str, retrieval: RetrievalResult) -> AnswerResponse:
        """Generate an answer based on question and retrieval result.

        If retrieval.retrieved is True, generates a grounded answer from the FAQ.
        If retrieval.retrieved is False, returns the fallback message.
        """

        try:
            normalized_question = question.strip()
            if not normalized_question:
                raise AnswerGeneratorError("Question must not be empty")

            # If retrieval failed (below threshold), only allow free-form
            # generation for harmless social chat. Company-specific or factual
            # questions fall back deterministically.
            if not retrieval.retrieved:
                if not self._should_allow_general_response(normalized_question):
                    return AnswerResponse(
                        answer=self._get_fallback_answer(),
                        confidence=retrieval.score,
                        source_faq_id=None,
                        is_fallback=True,
                        used_retrieval=False,
                        thinking=None,
                    )
                return self._generate_general_response(
                    normalized_question, retrieval.score
                )

            # Retrieval succeeded, generate grounded answer
            if retrieval.matched_entry is None:
                # This shouldn't happen if retrieved=True, but handle gracefully
                return AnswerResponse(
                    answer=self._get_fallback_answer(),
                    confidence=retrieval.score,
                    source_faq_id=None,
                    is_fallback=True,
                    used_retrieval=False,
                    thinking=None,
                )

            prompt = self._build_prompt(normalized_question, retrieval.matched_entry)
            generation = self._generate_answer(prompt)
            answer = generation.response
            if not self._is_grounded_answer(answer, retrieval.matched_entry):
                logger.warning(
                    "Generated answer failed lexical grounding check. "
                    "Fallback triggered. "
                    "Question: %r, Answer: %r",
                    normalized_question,
                    answer,
                )
                return AnswerResponse(
                    answer=self._get_fallback_answer(),
                    confidence=retrieval.score,
                    source_faq_id=None,
                    is_fallback=True,
                    used_retrieval=False,
                    thinking=generation.thinking,
                )

            return AnswerResponse(
                answer=answer,
                confidence=retrieval.score,
                source_faq_id=retrieval.matched_entry.id,
                is_fallback=False,
                used_retrieval=True,
                thinking=generation.thinking,
            )

        except OllamaClientError as exc:
            raise AnswerGeneratorError(f"Failed to generate answer: {exc}") from exc
        except AnswerGeneratorError:
            raise
        except Exception as exc:
            raise AnswerGeneratorError(f"Unexpected error during generation: {exc}") from exc

    def _generate_general_response(
        self, question: str, confidence: float
    ) -> AnswerResponse:
        """Generate a free-form response when no FAQ match was found.

        The LLM responds conversationally for general questions and uses
        the fallback message for unanswerable company-specific questions.
        """

        prompt = self.prompt_template.build_general(question)
        try:
            generation = self._generate_answer(prompt)
        except AnswerGeneratorError:
            return AnswerResponse(
                answer=self._get_fallback_answer(),
                confidence=confidence,
                source_faq_id=None,
                is_fallback=True,
                used_retrieval=False,
                thinking=None,
            )

        answer = generation.response
        is_fallback = answer.strip() == self.fallback_message.strip()
        return AnswerResponse(
            answer=answer,
            confidence=confidence,
            source_faq_id=None,
            is_fallback=is_fallback,
            used_retrieval=False,
            thinking=generation.thinking,
        )

    def generate_streaming(
        self, question: str, retrieval: RetrievalResult
    ) -> Iterator[str]:
        """Stream answer tokens to the caller.

        Yields the complete fallback message as a single chunk when retrieval
        failed or the question should not receive a generated response.
        Skips the grounding check (prompt instruction is the primary guard).
        """

        normalized_question = question.strip()
        if not retrieval.retrieved:
            if not self._should_allow_general_response(normalized_question):
                yield self.fallback_message
                return
            prompt = self.prompt_template.build_general(normalized_question)
        elif retrieval.matched_entry is None:
            yield self.fallback_message
            return
        else:
            prompt = self._build_prompt(normalized_question, retrieval.matched_entry)

        yield from self.ollama_client.generate_streaming(
            prompt, think=False
        )

    def _build_prompt(self, question: str, faq_entry: FAQEntry) -> str:
        """Build a grounded prompt from question and FAQ entry."""

        return self.prompt_template.build(question, faq_entry)

    def _generate_answer(self, prompt: str) -> OllamaGenerationResult:
        """Generate answer text via OllamaClient.

        Validates that the answer is non-empty and reasonable.
        """

        generation = self.ollama_client.generate_response(
            prompt,
            think=self.enable_thinking,
        )
        normalized_thinking = self._normalize_thinking(
            generation.thinking,
            truncated=not generation.response and generation.done_reason == "length",
        )
        normalized_answer = generation.response.strip()
        if normalized_answer:
            return OllamaGenerationResult(
                response=normalized_answer,
                thinking=normalized_thinking,
                done_reason=generation.done_reason,
            )

        if self.enable_thinking:
            logger.info(
                "Thinking trace exhausted the configured generation budget. "
                "Retrying final answer without thinking."
            )
            fallback_generation = self.ollama_client.generate_response(
                prompt,
                think=False,
            )
            fallback_answer = fallback_generation.response.strip()
            if fallback_answer:
                return OllamaGenerationResult(
                    response=fallback_answer,
                    thinking=normalized_thinking,
                    done_reason=fallback_generation.done_reason,
                )

        raise AnswerGeneratorError("Generation produced empty answer")

    def _get_fallback_answer(self) -> str:
        """Get the configured fallback message."""

        return self.fallback_message

    def _normalize_thinking(self, thinking: str | None, *, truncated: bool) -> str | None:
        normalized_thinking = (thinking or "").strip()
        if not normalized_thinking:
            return None
        if not truncated:
            return normalized_thinking
        return (
            f"{normalized_thinking}\n\n"
            "[Thinking trace was truncated at the token limit before the final answer.]"
        )

    def _should_allow_general_response(self, question: str) -> bool:
        normalized_question = question.casefold()
        if any(re.search(pattern, normalized_question) for pattern in _GENERAL_CHAT_PATTERNS):
            return True
        if self._contains_hint(normalized_question, _COMPANY_HINT_TERMS):
            return False
        if self._contains_hint(normalized_question, _FACTUAL_CHAT_TERMS):
            return False
        # Ambiguous question – let the LLM decide via build_general() prompt
        return True

    def _contains_hint(self, question: str, hints: set[str]) -> bool:
        return any(re.search(rf"\b{hint}\b", question) for hint in hints)

    def _is_grounded_answer(self, answer: str, faq_entry: FAQEntry) -> bool:
        """Return True if the generated answer still looks anchored in the FAQ."""

        normalized_answer = answer.strip()
        if len(normalized_answer) > max(400, len(faq_entry.answer) * 3):
            return False

        answer_terms = _extract_terms(normalized_answer)
        source_terms = _extract_terms(
            " ".join(
                part
                for part in (
                    faq_entry.question,
                    faq_entry.answer,
                    faq_entry.category or "",
                    " ".join(faq_entry.tags),
                )
                if part
            )
        )
        return not answer_terms or bool(answer_terms & source_terms)


def _extract_terms(text: str) -> set[str]:
    return {
        term
        for term in re.findall(r"[A-Za-z0-9À-ÿ]{4,}", text.casefold())
        if term not in {"this", "that", "with", "from", "your", "have", "will"}
    }
