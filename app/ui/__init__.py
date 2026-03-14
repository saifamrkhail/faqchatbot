"""Text-based UI package for the chatbot."""

from app.ui.protocol import (
    ChatResponse,
    ChatServiceAdapter,
    ChatServiceProtocol,
    StubChatService,
)

__all__ = [
    "ChatResponse",
    "ChatServiceAdapter",
    "ChatServiceProtocol",
    "StubChatService",
]
