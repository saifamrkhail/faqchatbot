"""Text-based UI package for the chatbot."""

from app.ui.chat_app import FAQChatApp
from app.ui.protocol import ChatResponse, ChatServiceProtocol, StubChatService

__all__ = [
    "ChatResponse",
    "ChatServiceProtocol",
    "FAQChatApp",
    "StubChatService",
]
