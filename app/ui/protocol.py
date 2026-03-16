"""Chat service protocol and response model for the UI layer."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Iterator, Protocol, runtime_checkable

from app.domain import ChatResponse as DomainChatResponse
from app.services import ChatService


@dataclass(frozen=True, slots=True)
class ChatResponse:
    """Structured response object returned to the UI from the chat service."""

    answer: str
    source_faq: str | None = None
    is_fallback: bool = False
    thinking: str | None = None


@runtime_checkable
class ChatServiceProtocol(Protocol):
    """Minimal contract used by the terminal chat loop."""

    def ask(self, question: str) -> ChatResponse: ...


@dataclass(slots=True)
class ChatServiceAdapter:
    """Bridge the core chat service to the smaller terminal-UI response shape."""

    chat_service: ChatService

    def ask(self, question: str) -> ChatResponse:
        """Run one synchronous chat turn and map it for the UI layer."""

        response = self.chat_service.handle_question(question)
        return _to_ui_response(response)

    def ask_streaming(self, question: str) -> Iterator[str]:
        """Stream answer tokens from the core chat service."""

        yield from self.chat_service.handle_question_streaming(question)


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
            thinking=None,
        )


def _to_ui_response(response: DomainChatResponse) -> ChatResponse:
    """Shrink the domain response down to the fields the UI renders."""

    return ChatResponse(
        answer=response.answer,
        source_faq=response.source_faq_id,
        is_fallback=response.is_fallback,
        thinking=response.thinking,
    )
