"""Tests for ChatService domain model (no external service dependencies)."""

import pytest

from app.domain import ChatResponse
from app.services import ChatService, ChatServiceError
from app.config import get_settings


class TestChatServiceResponseModel:
    """Test ChatResponse domain model properties."""

    def test_response_is_immutable(self):
        """ChatResponse should be immutable (frozen dataclass)."""
        response = ChatResponse(
            question="Q",
            answer="A",
            is_fallback=False,
            confidence=0.5,
            source_faq_id="id1",
            used_retrieval=True,
        )

        # All attribute assignments should fail
        with pytest.raises(AttributeError):
            response.question = "Modified"

        with pytest.raises(AttributeError):
            response.answer = "Modified"

        with pytest.raises(AttributeError):
            response.is_fallback = True

    def test_response_with_null_source_faq_id(self):
        """ChatResponse should allow None for source_faq_id."""
        response = ChatResponse(
            question="Q",
            answer="Fallback",
            is_fallback=True,
            confidence=0.2,
            source_faq_id=None,
            used_retrieval=False,
        )

        assert response.source_faq_id is None

    def test_response_all_fields_accessible(self):
        """All ChatResponse fields should be accessible."""
        response = ChatResponse(
            question="Question",
            answer="Answer",
            is_fallback=False,
            confidence=0.75,
            source_faq_id="faq_123",
            used_retrieval=True,
        )

        # All fields should be accessible
        _ = response.question
        _ = response.answer
        _ = response.is_fallback
        _ = response.confidence
        _ = response.source_faq_id
        _ = response.used_retrieval


class TestChatServiceErrorPropagation:
    """Test error handling and propagation."""

    def test_empty_question_error(self):
        """Empty question should raise ChatServiceError."""
        settings = get_settings()
        service = ChatService.from_settings(settings)

        with pytest.raises(ChatServiceError):
            service.handle_question("")

    def test_whitespace_question_error(self):
        """Whitespace-only question should raise ChatServiceError."""
        settings = get_settings()
        service = ChatService.from_settings(settings)

        with pytest.raises(ChatServiceError):
            service.handle_question("   \n\t  ")

    def test_error_message_meaningful(self):
        """Error messages should be meaningful."""
        settings = get_settings()
        service = ChatService.from_settings(settings)

        try:
            service.handle_question("")
        except ChatServiceError as e:
            assert "empty" in str(e).lower() or "must" in str(e).lower()
