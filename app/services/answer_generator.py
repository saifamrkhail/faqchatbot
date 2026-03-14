"""Grounded answer generation service."""

from __future__ import annotations

from dataclasses import dataclass
import re

from app.config import AppSettings
from app.domain import FAQEntry
from app.domain.answer_response import AnswerResponse
from app.domain.prompt_template import PromptTemplate
from app.domain.retrieval_result import RetrievalResult
from app.infrastructure import OllamaClient, OllamaClientError
import logging

logger = logging.getLogger(__name__)


class AnswerGeneratorError(RuntimeError):
    """Raised when answer generation fails."""


@dataclass(slots=True)
class AnswerGenerator:
    """Generates grounded answers from retrieved FAQ context."""

    ollama_client: OllamaClient
    prompt_template: PromptTemplate
    fallback_message: str

    @classmethod
    def from_settings(cls, settings: AppSettings) -> "AnswerGenerator":
        """Build a fully wired answer generator from application settings."""

        return cls(
            ollama_client=OllamaClient.from_settings(settings),
            prompt_template=PromptTemplate(fallback_message=settings.fallback_message),
            fallback_message=settings.fallback_message,
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

            # If retrieval failed (below threshold), use fallback
            if not retrieval.retrieved:
                return AnswerResponse(
                    answer=self._get_fallback_answer(),
                    confidence=retrieval.score,
                    source_faq_id=None,
                    is_fallback=True,
                    used_retrieval=False,
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
                )

            prompt = self._build_prompt(normalized_question, retrieval.matched_entry)
            answer = self._generate_answer(prompt)
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
                )

            return AnswerResponse(
                answer=answer,
                confidence=retrieval.score,
                source_faq_id=retrieval.matched_entry.id,
                is_fallback=False,
                used_retrieval=True,
            )

        except OllamaClientError as exc:
            raise AnswerGeneratorError(f"Failed to generate answer: {exc}") from exc
        except AnswerGeneratorError:
            raise
        except Exception as exc:
            raise AnswerGeneratorError(f"Unexpected error during generation: {exc}") from exc

    def _build_prompt(self, question: str, faq_entry: FAQEntry) -> str:
        """Build a grounded prompt from question and FAQ entry."""

        return self.prompt_template.build(question, faq_entry)

    def _generate_answer(self, prompt: str) -> str:
        """Generate answer text via OllamaClient.

        Validates that the answer is non-empty and reasonable.
        """

        answer = self.ollama_client.generate(prompt)

        # Additional validation
        normalized_answer = answer.strip()
        if not normalized_answer:
            raise AnswerGeneratorError("Generation produced empty answer")

        return normalized_answer

    def _get_fallback_answer(self) -> str:
        """Get the configured fallback message."""

        return self.fallback_message

    def _is_grounded_answer(self, answer: str, faq_entry: FAQEntry) -> bool:
        """Return True if the generated answer still looks anchored in the FAQ."""

        normalized_answer = answer.strip()
        if len(normalized_answer) > max(400, len(faq_entry.answer) * 2):
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
