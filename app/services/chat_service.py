"""Chat application orchestration service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

from app.config import AppSettings, DEFAULT_MAX_QUESTION_CHARS
from app.domain.chat_response import ChatResponse
from app.infrastructure import OllamaClientError
from app.services.answer_generator import AnswerGenerator, AnswerGeneratorError
from app.services.retriever import Retriever, RetrieverError


class ChatServiceError(RuntimeError):
    """Raised when chat service operation fails."""


@dataclass(slots=True)
class ChatService:
    """Orchestrates retrieval and answer generation for a single chat turn.

    Accepts a user question and returns a complete ChatResponse with
    answer, confidence, and metadata.
    """

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
        """Handle a user question through the complete chat pipeline.

        1. Normalizes the question
        2. Retrieves relevant FAQ via Retriever
        3. Generates answer via AnswerGenerator
        4. Wraps result in ChatResponse

        Raises ChatServiceError if any step fails.
        """

        try:
            normalized_question = question.strip()
            if not normalized_question:
                raise ChatServiceError("Question must not be empty")
            if len(normalized_question) > self.max_question_chars:
                raise ChatServiceError(
                    "Question exceeds maximum length of "
                    f"{self.max_question_chars} characters"
                )

            # Step 1: Retrieve relevant FAQ
            retrieval_result = self.retriever.retrieve(normalized_question)

            # Step 2: Generate answer (grounded or fallback)
            answer_response = self.answer_generator.generate(
                normalized_question, retrieval_result
            )

            # Step 3: Build and return ChatResponse
            return ChatResponse(
                question=normalized_question,
                answer=answer_response.answer,
                is_fallback=answer_response.is_fallback,
                confidence=answer_response.confidence,
                source_faq_id=answer_response.source_faq_id,
                used_retrieval=answer_response.used_retrieval,
                thinking=answer_response.thinking,
            )

        except ChatServiceError:
            raise
        except RetrieverError as exc:
            raise ChatServiceError(f"Retrieval failed: {exc}") from exc
        except AnswerGeneratorError as exc:
            raise ChatServiceError(f"Generation failed: {exc}") from exc
        except Exception as exc:
            raise ChatServiceError(f"Unexpected error during chat: {exc}") from exc

    def handle_question_streaming(self, question: str) -> Iterator[str]:
        """Streaming variant of handle_question.

        Yields text tokens for generated answers.
        Yields the complete fallback message as a single chunk when no FAQ was
        retrieved and the question does not qualify for general chat.
        """

        normalized_question = question.strip()
        if not normalized_question:
            raise ChatServiceError("Question must not be empty")
        if len(normalized_question) > self.max_question_chars:
            raise ChatServiceError(
                "Question exceeds maximum length of "
                f"{self.max_question_chars} characters"
            )

        try:
            retrieval_result = self.retriever.retrieve(normalized_question)
            yield from self.answer_generator.generate_streaming(
                normalized_question, retrieval_result
            )
        except ChatServiceError:
            raise
        except RetrieverError as exc:
            raise ChatServiceError(f"Retrieval failed: {exc}") from exc
        except OllamaClientError as exc:
            raise ChatServiceError(f"Generation failed: {exc}") from exc
        except Exception as exc:
            raise ChatServiceError(f"Unexpected error during chat: {exc}") from exc
