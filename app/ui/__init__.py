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
    "FAQChatApp",
    "StubChatService",
]


def __getattr__(name: str):
    if name == "FAQChatApp":
        from app.ui.chat_app import FAQChatApp

        return FAQChatApp
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
