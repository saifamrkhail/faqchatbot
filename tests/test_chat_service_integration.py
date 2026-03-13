"""Integration tests for ChatService with real data."""

import pytest
from urllib.error import HTTPError

from app.config import get_settings
from app.domain import ChatResponse, FAQEntry
from app.services import ChatService, ChatServiceError


class TestChatServiceRealData:
    """Integration tests with real FAQ data."""

    def test_factory_creates_working_service(self):
        """Factory method should create a functional service."""
        settings = get_settings()
        service = ChatService.from_settings(settings)

        assert service is not None
        assert service.retriever is not None
        assert service.answer_generator is not None

    def test_response_structure_with_real_services(self):
        """ChatResponse should have correct structure from real services."""
        settings = get_settings()
        service = ChatService.from_settings(settings)

        try:
            # Use a generic question (likely to trigger fallback without ingested data)
            response = service.handle_question("How does this work?")

            assert isinstance(response, ChatResponse)
            assert isinstance(response.question, str)
            assert isinstance(response.answer, str)
            assert isinstance(response.is_fallback, bool)
            assert isinstance(response.confidence, float)
            assert response.source_faq_id is None or isinstance(response.source_faq_id, str)
            assert isinstance(response.used_retrieval, bool)
        except ChatServiceError as e:
            if "Ollama" in str(e) or "not found" in str(e):
                pytest.skip(f"Ollama service not available: {e}")
            raise

    def test_all_fields_populated(self):
        """All ChatResponse fields should be populated."""
        settings = get_settings()
        service = ChatService.from_settings(settings)

        try:
            response = service.handle_question("Test question")

            # All fields must be present
            assert hasattr(response, "question")
            assert hasattr(response, "answer")
            assert hasattr(response, "is_fallback")
            assert hasattr(response, "confidence")
            assert hasattr(response, "source_faq_id")
            assert hasattr(response, "used_retrieval")

            # Values should not be None except where explicitly allowed
            assert response.question is not None
            assert response.answer is not None
            assert response.is_fallback is not None
            assert response.confidence is not None
            assert response.used_retrieval is not None
        except ChatServiceError as e:
            if "Ollama" in str(e) or "not found" in str(e):
                pytest.skip(f"Ollama service not available: {e}")
            raise

    def test_response_immutable(self):
        """ChatResponse should be immutable."""
        settings = get_settings()
        service = ChatService.from_settings(settings)

        try:
            response = service.handle_question("Test")

            with pytest.raises(AttributeError):
                response.answer = "Modified"
        except ChatServiceError as e:
            if "Ollama" in str(e) or "not found" in str(e):
                pytest.skip(f"Ollama service not available: {e}")
            raise


class TestChatServiceFallbackBehavior:
    """Test fallback behavior with real services."""

    def test_fallback_response_structure(self):
        """Fallback response should have consistent structure."""
        settings = get_settings()
        service = ChatService.from_settings(settings)

        try:
            # Question unlikely to be in FAQ
            response = service.handle_question("zzzzzzzzzzzzzzzz irrelevant zzzzzzzzz")

            # Should handle gracefully
            assert isinstance(response, ChatResponse)
            assert response.answer is not None
            assert isinstance(response.answer, str)
            assert len(response.answer) > 0
        except ChatServiceError as e:
            if "Ollama" in str(e) or "not found" in str(e):
                pytest.skip(f"Ollama service not available: {e}")
            raise

    def test_low_confidence_fallback(self):
        """Low confidence retrieval should result in fallback."""
        settings = get_settings()
        service = ChatService.from_settings(settings)

        try:
            response = service.handle_question("completely unrelated garbage text")

            # If not retrieved, should have fallback properties
            if not response.used_retrieval:
                assert response.is_fallback is True
                assert response.source_faq_id is None
        except ChatServiceError as e:
            if "Ollama" in str(e) or "not found" in str(e):
                pytest.skip(f"Ollama service not available: {e}")
            raise

    def test_high_confidence_retrieval(self):
        """High confidence retrieval should result in grounded answer."""
        # This test depends on FAQ data being ingested
        settings = get_settings()
        service = ChatService.from_settings(settings)

        try:
            # If FAQ data is available, test with a FAQ-like question
            response = service.handle_question("How do I reset my password?")

            # Response should be valid regardless of whether FAQ exists
            assert isinstance(response, ChatResponse)
            assert response.confidence >= 0.0 and response.confidence <= 1.0
        except ChatServiceError as e:
            if "Ollama" in str(e) or "not found" in str(e):
                pytest.skip(f"Ollama service not available: {e}")
            raise


class TestChatServiceSemanticBehavior:
    """Test semantic behavior of ChatService."""

    def test_question_preserved(self):
        """Original question should be preserved in response."""
        settings = get_settings()
        service = ChatService.from_settings(settings)

        try:
            question = "What is the meaning of life?"
            response = service.handle_question(question)

            # Question should be preserved (normalized but same content)
            assert response.question == question
        except ChatServiceError as e:
            if "Ollama" in str(e) or "not found" in str(e):
                pytest.skip(f"Ollama service not available: {e}")
            raise

    def test_fallback_has_no_source(self):
        """Fallback response should have no source_faq_id."""
        settings = get_settings()
        service = ChatService.from_settings(settings)

        try:
            response = service.handle_question("irrelevant xyzabc question")

            if response.is_fallback:
                assert response.source_faq_id is None
        except ChatServiceError as e:
            if "Ollama" in str(e) or "not found" in str(e):
                pytest.skip(f"Ollama service not available: {e}")
            raise

    def test_field_consistency(self):
        """Response fields should be logically consistent."""
        settings = get_settings()
        service = ChatService.from_settings(settings)

        try:
            response = service.handle_question("Test question")

            # If used_retrieval is True, source_faq_id should be set
            if response.used_retrieval:
                assert response.source_faq_id is not None
                assert response.is_fallback is False

            # If is_fallback is True, used_retrieval should be False
            if response.is_fallback:
                assert response.used_retrieval is False
        except ChatServiceError as e:
            if "Ollama" in str(e) or "not found" in str(e):
                pytest.skip(f"Ollama service not available: {e}")
            raise

    def test_confidence_reflects_score(self):
        """Confidence should reflect retrieval score."""
        settings = get_settings()
        service = ChatService.from_settings(settings)

        try:
            response = service.handle_question("test")

            # Confidence should be in valid range
            assert 0.0 <= response.confidence <= 1.0
        except ChatServiceError as e:
            if "Ollama" in str(e) or "not found" in str(e):
                pytest.skip(f"Ollama service not available: {e}")
            raise


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
