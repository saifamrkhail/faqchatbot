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
    """Turn retrieval output into a grounded answer or deterministic fallback."""

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
        """Generate an answer from retrieval output."""

        try:
            normalized_question = question.strip()
            if not normalized_question:
                raise AnswerGeneratorError("Question must not be empty")

            # Retrieval is the gatekeeper: no trusted match means no model answer.
            if not retrieval.retrieved:
                return AnswerResponse(
                    answer=self._get_fallback_answer(),
                    confidence=retrieval.score,
                    source_faq_id=None,
                    is_fallback=True,
                    used_retrieval=False,
                )

            if retrieval.matched_entry is None:
                # Keep the fallback deterministic even if the retrieval state is inconsistent.
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
                # A lightweight lexical overlap check blocks obvious hallucinations.
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
        """Build the prompt sent to the generation model."""

        return self.prompt_template.build(question, faq_entry)

    def _generate_answer(self, prompt: str) -> str:
        """Call Ollama and reject empty generations early."""

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
    """Collect coarse lexical anchors used by the grounding sanity check."""

    return {
        term
        for term in re.findall(r"[A-Za-z0-9À-ÿ]{4,}", text.casefold())
        if term not in {"this", "that", "with", "from", "your", "have", "will"}
    }
