"""Unit tests for ChatService."""

import pytest
from unittest.mock import MagicMock

from app.domain import ChatResponse, FAQEntry, RetrievalResult
from app.services import (
    AnswerGenerator,
    AnswerGeneratorError,
    ChatService,
    ChatServiceError,
    Retriever,
    RetrieverError,
)


class TestChatServiceInputValidation:
    """Test input validation in ChatService.handle_question."""

    def test_handle_empty_question(self):
        """Empty question should raise ChatServiceError."""
        retriever = MagicMock(spec=Retriever)
        answer_generator = MagicMock(spec=AnswerGenerator)
        service = ChatService(retriever, answer_generator)

        with pytest.raises(ChatServiceError, match="Question must not be empty"):
            service.handle_question("")

    def test_handle_whitespace_only_question(self):
        """Whitespace-only question should raise ChatServiceError."""
        retriever = MagicMock(spec=Retriever)
        answer_generator = MagicMock(spec=AnswerGenerator)
        service = ChatService(retriever, answer_generator)

        with pytest.raises(ChatServiceError, match="Question must not be empty"):
            service.handle_question("   \t\n  ")


class TestChatServiceSuccessfulFlow:
    """Test successful flow with valid retrieval and generation."""

    def test_response_structure(self):
        """Response should have all required fields."""
        faq_entry = FAQEntry(
            id="faq_001",
            question="What is x?",
            answer="x is y",
            tags=["test"],
            category="Test",
            source="test",
        )
        retrieval_result = RetrievalResult(
            matched_entry=faq_entry,
            score=0.85,
            top_k_results=[(faq_entry, 0.85)],
            retrieved=True,
        )

        retriever = MagicMock(spec=Retriever)
        retriever.retrieve.return_value = retrieval_result

        from app.domain import AnswerResponse

        answer_response = AnswerResponse(
            answer="The answer is y",
            confidence=0.85,
            source_faq_id="faq_001",
            is_fallback=False,
            used_retrieval=True,
        )
        answer_generator = MagicMock(spec=AnswerGenerator)
        answer_generator.generate.return_value = answer_response

        service = ChatService(retriever, answer_generator)
        response = service.handle_question("What is x?")

        assert isinstance(response, ChatResponse)
        assert response.question == "What is x?"
        assert response.answer == "The answer is y"
        assert response.is_fallback is False
        assert response.confidence == 0.85
        assert response.source_faq_id == "faq_001"
        assert response.used_retrieval is True

    def test_confidence_propagated(self):
        """Response confidence should match retrieval score."""
        faq_entry = FAQEntry(
            id="faq_002",
            question="Test Q",
            answer="Test A",
            tags=[],
            category="Test",
            source="test",
        )
        retrieval_result = RetrievalResult(
            matched_entry=faq_entry,
            score=0.72,
            top_k_results=[(faq_entry, 0.72)],
            retrieved=True,
        )

        retriever = MagicMock(spec=Retriever)
        retriever.retrieve.return_value = retrieval_result

        from app.domain import AnswerResponse

        answer_response = AnswerResponse(
            answer="Answer",
            confidence=0.72,
            source_faq_id="faq_002",
            is_fallback=False,
            used_retrieval=True,
        )
        answer_generator = MagicMock(spec=AnswerGenerator)
        answer_generator.generate.return_value = answer_response

        service = ChatService(retriever, answer_generator)
        response = service.handle_question("Test Q")

        assert response.confidence == 0.72

    def test_source_faq_id_set(self):
        """Response should include source_faq_id when retrieved."""
        faq_entry = FAQEntry(
            id="faq_abc",
            question="Question",
            answer="Answer",
            tags=[],
            category="Test",
            source="test",
        )
        retrieval_result = RetrievalResult(
            matched_entry=faq_entry,
            score=0.80,
            top_k_results=[(faq_entry, 0.80)],
            retrieved=True,
        )

        retriever = MagicMock(spec=Retriever)
        retriever.retrieve.return_value = retrieval_result

        from app.domain import AnswerResponse

        answer_response = AnswerResponse(
            answer="Generated answer",
            confidence=0.80,
            source_faq_id="faq_abc",
            is_fallback=False,
            used_retrieval=True,
        )
        answer_generator = MagicMock(spec=AnswerGenerator)
        answer_generator.generate.return_value = answer_response

        service = ChatService(retriever, answer_generator)
        response = service.handle_question("Question")

        assert response.source_faq_id == "faq_abc"


class TestChatServiceFallbackFlow:
    """Test fallback flow when retrieval does not match."""

    def test_fallback_when_not_retrieved(self):
        """Response should be fallback when retrieval.retrieved is False."""
        retrieval_result = RetrievalResult(
            matched_entry=None,
            score=0.45,
            top_k_results=[],
            retrieved=False,
        )

        retriever = MagicMock(spec=Retriever)
        retriever.retrieve.return_value = retrieval_result

        from app.domain import AnswerResponse

        answer_response = AnswerResponse(
            answer="I don't know",
            confidence=0.45,
            source_faq_id=None,
            is_fallback=True,
            used_retrieval=False,
        )
        answer_generator = MagicMock(spec=AnswerGenerator)
        answer_generator.generate.return_value = answer_response

        service = ChatService(retriever, answer_generator)
        response = service.handle_question("Unknown question")

        assert response.is_fallback is True
        assert response.answer == "I don't know"

    def test_source_faq_id_none_on_fallback(self):
        """source_faq_id should be None for fallback responses."""
        retrieval_result = RetrievalResult(
            matched_entry=None,
            score=0.50,
            top_k_results=[],
            retrieved=False,
        )

        retriever = MagicMock(spec=Retriever)
        retriever.retrieve.return_value = retrieval_result

        from app.domain import AnswerResponse

        answer_response = AnswerResponse(
            answer="Fallback",
            confidence=0.50,
            source_faq_id=None,
            is_fallback=True,
            used_retrieval=False,
        )
        answer_generator = MagicMock(spec=AnswerGenerator)
        answer_generator.generate.return_value = answer_response

        service = ChatService(retriever, answer_generator)
        response = service.handle_question("Unknown")

        assert response.source_faq_id is None

    def test_question_preserved_on_fallback(self):
        """Original question should be preserved even on fallback."""
        retrieval_result = RetrievalResult(
            matched_entry=None,
            score=0.30,
            top_k_results=[],
            retrieved=False,
        )

        retriever = MagicMock(spec=Retriever)
        retriever.retrieve.return_value = retrieval_result

        from app.domain import AnswerResponse

        answer_response = AnswerResponse(
            answer="Fallback message",
            confidence=0.30,
            source_faq_id=None,
            is_fallback=True,
            used_retrieval=False,
        )
        answer_generator = MagicMock(spec=AnswerGenerator)
        answer_generator.generate.return_value = answer_response

        service = ChatService(retriever, answer_generator)
        response = service.handle_question("Unrelated question")

        assert response.question == "Unrelated question"


class TestChatServiceErrorHandling:
    """Test error handling and wrapping."""

    def test_retriever_error_wrapped(self):
        """RetrieverError should be wrapped in ChatServiceError."""
        retriever = MagicMock(spec=Retriever)
        retriever.retrieve.side_effect = RetrieverError("Embedding failed")
        answer_generator = MagicMock(spec=AnswerGenerator)

        service = ChatService(retriever, answer_generator)

        with pytest.raises(ChatServiceError, match="Retrieval failed"):
            service.handle_question("Test question")

    def test_answer_generator_error_wrapped(self):
        """AnswerGeneratorError should be wrapped in ChatServiceError."""
        faq_entry = FAQEntry(
            id="faq_001",
            question="Q",
            answer="A",
            tags=[],
            category="Test",
            source="test",
        )
        retrieval_result = RetrievalResult(
            matched_entry=faq_entry,
            score=0.85,
            top_k_results=[(faq_entry, 0.85)],
            retrieved=True,
        )

        retriever = MagicMock(spec=Retriever)
        retriever.retrieve.return_value = retrieval_result

        answer_generator = MagicMock(spec=AnswerGenerator)
        answer_generator.generate.side_effect = AnswerGeneratorError("Generation failed")

        service = ChatService(retriever, answer_generator)

        with pytest.raises(ChatServiceError, match="Generation failed"):
            service.handle_question("Q")

    def test_unexpected_error_wrapped(self):
        """Unexpected errors should be wrapped in ChatServiceError."""
        retriever = MagicMock(spec=Retriever)
        retriever.retrieve.side_effect = ValueError("Unexpected error")
        answer_generator = MagicMock(spec=AnswerGenerator)

        service = ChatService(retriever, answer_generator)

        with pytest.raises(ChatServiceError, match="Unexpected error during chat"):
            service.handle_question("Test")


class TestChatServiceEndToEnd:
    """End-to-end service tests."""

    def test_factory_method_from_settings(self):
        """from_settings should create a functional ChatService."""
        from app.config import get_settings

        settings = get_settings()
        service = ChatService.from_settings(settings)

        assert isinstance(service, ChatService)
        assert service.retriever is not None
        assert service.answer_generator is not None

    def test_full_response_fields(self):
        """All ChatResponse fields should be set."""
        faq_entry = FAQEntry(
            id="faq_test",
            question="Q?",
            answer="A!",
            tags=["tag1"],
            category="Cat",
            source="src",
        )
        retrieval_result = RetrievalResult(
            matched_entry=faq_entry,
            score=0.91,
            top_k_results=[(faq_entry, 0.91)],
            retrieved=True,
        )

        retriever = MagicMock(spec=Retriever)
        retriever.retrieve.return_value = retrieval_result

        from app.domain import AnswerResponse

        answer_response = AnswerResponse(
            answer="Generated",
            confidence=0.91,
            source_faq_id="faq_test",
            is_fallback=False,
            used_retrieval=True,
        )
        answer_generator = MagicMock(spec=AnswerGenerator)
        answer_generator.generate.return_value = answer_response

        service = ChatService(retriever, answer_generator)
        response = service.handle_question("Q?")

        # Verify all fields are accessible
        assert hasattr(response, "question")
        assert hasattr(response, "answer")
        assert hasattr(response, "is_fallback")
        assert hasattr(response, "confidence")
        assert hasattr(response, "source_faq_id")
        assert hasattr(response, "used_retrieval")

    def test_response_immutability(self):
        """ChatResponse should be immutable."""
        response = ChatResponse(
            question="Q",
            answer="A",
            is_fallback=False,
            confidence=0.5,
            source_faq_id="id",
            used_retrieval=True,
        )

        with pytest.raises(AttributeError):
            response.answer = "Modified"


class TestChatServiceIntegration:
    """Integration tests for ChatService behavior."""

    def test_retriever_called_once(self):
        """Retriever should be called exactly once per question."""
        retrieval_result = RetrievalResult(
            matched_entry=None,
            score=0.0,
            top_k_results=[],
            retrieved=False,
        )

        retriever = MagicMock(spec=Retriever)
        retriever.retrieve.return_value = retrieval_result

        from app.domain import AnswerResponse

        answer_response = AnswerResponse(
            answer="Fallback",
            confidence=0.0,
            source_faq_id=None,
            is_fallback=True,
            used_retrieval=False,
        )
        answer_generator = MagicMock(spec=AnswerGenerator)
        answer_generator.generate.return_value = answer_response

        service = ChatService(retriever, answer_generator)
        service.handle_question("Test")

        retriever.retrieve.assert_called_once()

    def test_answer_generator_called_once(self):
        """AnswerGenerator should be called exactly once per question."""
        retrieval_result = RetrievalResult(
            matched_entry=None,
            score=0.0,
            top_k_results=[],
            retrieved=False,
        )

        retriever = MagicMock(spec=Retriever)
        retriever.retrieve.return_value = retrieval_result

        from app.domain import AnswerResponse

        answer_response = AnswerResponse(
            answer="Fallback",
            confidence=0.0,
            source_faq_id=None,
            is_fallback=True,
            used_retrieval=False,
        )
        answer_generator = MagicMock(spec=AnswerGenerator)
        answer_generator.generate.return_value = answer_response

        service = ChatService(retriever, answer_generator)
        service.handle_question("Test")

        answer_generator.generate.assert_called_once()

    def test_correct_question_passed_through(self):
        """Normalized question should be passed to both retriever and generator."""
        faq_entry = FAQEntry(
            id="faq",
            question="Q",
            answer="A",
            tags=[],
            category="C",
            source="s",
        )
        retrieval_result = RetrievalResult(
            matched_entry=faq_entry,
            score=0.8,
            top_k_results=[(faq_entry, 0.8)],
            retrieved=True,
        )

        retriever = MagicMock(spec=Retriever)
        retriever.retrieve.return_value = retrieval_result

        from app.domain import AnswerResponse

        answer_response = AnswerResponse(
            answer="Answer",
            confidence=0.8,
            source_faq_id="faq",
            is_fallback=False,
            used_retrieval=True,
        )
        answer_generator = MagicMock(spec=AnswerGenerator)
        answer_generator.generate.return_value = answer_response

        service = ChatService(retriever, answer_generator)
        service.handle_question("  Test question  ")

        # Both should be called with normalized question
        retriever.retrieve.assert_called_once_with("Test question")
        answer_generator.generate.assert_called_once_with(
            "Test question", retrieval_result
        )
