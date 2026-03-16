"""Chat application orchestration service."""

from __future__ import annotations

from dataclasses import dataclass

from app.config import AppSettings, DEFAULT_MAX_QUESTION_CHARS
from app.domain.chat_response import ChatResponse
from app.services.answer_generator import AnswerGenerator, AnswerGeneratorError
from app.services.retriever import Retriever, RetrieverError


class ChatServiceError(RuntimeError):
    """Raised when chat service operation fails."""


@dataclass(slots=True)
class ChatService:
    """UI-independent facade for one full chat turn."""

    retriever: Retriever
    answer_generator: AnswerGenerator
    max_question_chars: int = DEFAULT_MAX_QUESTION_CHARS

    @classmethod
    def from_settings(cls, settings: AppSettings) -> ChatService:
        """Build a fully wired chat service from application settings."""

        return cls(
            retriever=Retriever.from_settings(settings),
            answer_generator=AnswerGenerator.from_settings(settings),
            max_question_chars=settings.max_question_chars,
        )

    def handle_question(self, question: str) -> ChatResponse:
        """Run validation, retrieval, generation, and response mapping."""

        try:
            normalized_question = question.strip()
            if not normalized_question:
                raise ChatServiceError("Question must not be empty")
            if len(normalized_question) > self.max_question_chars:
                raise ChatServiceError(
                    "Question exceeds maximum length of "
                    f"{self.max_question_chars} characters"
                )

            retrieval_result = self.retriever.retrieve(normalized_question)

            answer_response = self.answer_generator.generate(
                normalized_question, retrieval_result
            )

            return ChatResponse(
                question=normalized_question,
                answer=answer_response.answer,
                is_fallback=answer_response.is_fallback,
                confidence=answer_response.confidence,
                source_faq_id=answer_response.source_faq_id,
                used_retrieval=answer_response.used_retrieval,
            )

        except ChatServiceError:
            raise
        except RetrieverError as exc:
            raise ChatServiceError(f"Retrieval failed: {exc}") from exc
        except AnswerGeneratorError as exc:
            raise ChatServiceError(f"Generation failed: {exc}") from exc
        except Exception as exc:
            raise ChatServiceError(f"Unexpected error during chat: {exc}") from exc
