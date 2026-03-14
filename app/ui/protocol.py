"""Chat service protocol and response model for the UI layer."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from app.domain import ChatResponse as DomainChatResponse
from app.services import ChatService


@dataclass(frozen=True, slots=True)
class ChatResponse:
    """Structured response object returned to the UI from the chat service."""

    answer: str
    source_faq: str | None = None
    is_fallback: bool = False


@runtime_checkable
class ChatServiceProtocol(Protocol):
    """Contract that the UI expects from any chat backend."""

    def ask(self, question: str) -> ChatResponse: ...


@dataclass(slots=True)
class ChatServiceAdapter:
    """Adapter wrapping the synchronous core ChatService."""

    chat_service: ChatService

    def ask(self, question: str) -> ChatResponse:
        response = self.chat_service.handle_question(question)
        return _to_ui_response(response)


class StubChatService:
    """Canned chat service for standalone UI testing and development."""

    _STUB_ANSWER = (
        "Dies ist eine Platzhalter-Antwort. "
        "Der vollständige Chat-Service ist noch nicht angebunden."
    )
    _SIMULATED_DELAY_SECONDS = 0.8

    def ask(self, question: str) -> ChatResponse:
        time.sleep(self._SIMULATED_DELAY_SECONDS)
        return ChatResponse(
            answer=self._STUB_ANSWER,
            source_faq=None,
            is_fallback=True,
        )


def _to_ui_response(response: DomainChatResponse) -> ChatResponse:
    return ChatResponse(
        answer=response.answer,
        source_faq=response.source_faq_id,
        is_fallback=response.is_fallback,
    )
