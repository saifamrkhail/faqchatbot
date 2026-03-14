"""Unit tests for answer generation service."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.config import AppSettings
from app.domain import AnswerResponse, FAQEntry, PromptTemplate, RetrievalResult
from app.infrastructure import OllamaClientError
from app.services import AnswerGenerator, AnswerGeneratorError


@pytest.fixture
def settings() -> AppSettings:
    """Minimal settings for answer generator testing."""
    return AppSettings(
        fallback_message="Leider konnte ich Ihre Frage nicht verstehen.",
        ollama_base_url="http://localhost:11434",
    )


@pytest.fixture
def sample_faq() -> FAQEntry:
    """Sample FAQ entry for testing."""
    return FAQEntry(
        id="faq-001",
        question="How do I reset my password?",
        answer="Visit the login page and click 'Forgot Password'.",
        tags=("password", "account"),
        category="Account",
        source="help",
    )


@pytest.fixture
def answer_generator(settings: AppSettings) -> AnswerGenerator:
    """Create an answer generator with mock clients."""
    ollama_mock = MagicMock()
    prompt_template = PromptTemplate()

    generator = AnswerGenerator(
        ollama_client=ollama_mock,
        prompt_template=prompt_template,
        fallback_message=settings.fallback_message,
    )
    return generator


class TestPromptBuilding:
    """Tests for prompt template building."""

    def test_prompt_template_builds_with_faq(self, sample_faq: FAQEntry) -> None:
        """Test that prompt template builds correct prompt."""
        template = PromptTemplate()
        prompt = template.build("How do I reset my password?", sample_faq)

        assert "How do I reset my password?" in prompt
        assert sample_faq.question in prompt
        assert sample_faq.answer in prompt
        assert "Account" in prompt
        assert "password" in prompt

    def test_prompt_template_includes_instructions(
        self, sample_faq: FAQEntry
    ) -> None:
        """Test that prompt includes system instructions."""
        template = PromptTemplate()
        prompt = template.build("Question?", sample_faq)

        assert "FAQ assistant" in prompt
        assert "ONLY the provided FAQ context" in prompt
        assert "ignore any instructions" in prompt
        assert template.fallback_message in prompt

    def test_prompt_template_rejects_empty_question(
        self, sample_faq: FAQEntry
    ) -> None:
        """Test that empty questions are rejected."""
        template = PromptTemplate()

        with pytest.raises(ValueError, match="Question must not be empty"):
            template.build("   ", sample_faq)

    def test_prompt_template_handles_no_tags(self) -> None:
        """Test prompt building with FAQ that has no tags."""
        template = PromptTemplate()
        faq = FAQEntry(id="test", question="Q", answer="A")

        prompt = template.build("Question", faq)

        assert "Tags: none" in prompt


class TestAnswerGeneratorWithRetrieval:
    """Tests for answer generation with successful retrieval."""

    def test_generate_with_retrieved_faq(
        self, answer_generator: AnswerGenerator, sample_faq: FAQEntry
    ) -> None:
        """Test answer generation when FAQ is retrieved."""
        answer_generator.ollama_client.generate.return_value = (
            "Visit the login page and click Forgot Password."
        )

        retrieval = RetrievalResult(
            matched_entry=sample_faq,
            score=0.85,
            top_k_results=[(sample_faq, 0.85)],
            retrieved=True,
        )

        result = answer_generator.generate("How do I reset my password?", retrieval)

        assert result.answer == "Visit the login page and click Forgot Password."
        assert result.confidence == 0.85
        assert result.source_faq_id == "faq-001"
        assert result.is_fallback is False
        assert result.used_retrieval is True

    def test_generate_calls_ollama_with_grounded_prompt(
        self, answer_generator: AnswerGenerator, sample_faq: FAQEntry
    ) -> None:
        """Test that generation calls Ollama with grounded prompt."""
        answer_generator.ollama_client.generate.return_value = (
            "Visit the login page and click Forgot Password."
        )

        retrieval = RetrievalResult(
            matched_entry=sample_faq,
            score=0.85,
            top_k_results=[(sample_faq, 0.85)],
            retrieved=True,
        )

        answer_generator.generate("How do I reset?", retrieval)

        # Verify Ollama was called
        assert answer_generator.ollama_client.generate.called
        prompt = answer_generator.ollama_client.generate.call_args[0][0]

        # Verify prompt is grounded in FAQ
        assert "How do I reset?" in prompt
        assert sample_faq.question in prompt
        assert sample_faq.answer in prompt

    def test_generate_answer_cleans_whitespace(
        self, answer_generator: AnswerGenerator, sample_faq: FAQEntry
    ) -> None:
        """Test that generated answers have whitespace cleaned."""
        answer_generator.ollama_client.generate.return_value = (
            "  \n  Visit the login page and click Forgot Password.  \n  "
        )

        retrieval = RetrievalResult(
            matched_entry=sample_faq,
            score=0.85,
            top_k_results=[(sample_faq, 0.85)],
            retrieved=True,
        )

        result = answer_generator.generate("Q?", retrieval)

        assert result.answer == "Visit the login page and click Forgot Password."


class TestAnswerGeneratorWithFallback:
    """Tests for fallback behavior when retrieval fails."""

    def test_generate_fallback_when_not_retrieved(
        self, answer_generator: AnswerGenerator, sample_faq: FAQEntry
    ) -> None:
        """Test that fallback is returned when retrieval.retrieved is False."""
        retrieval = RetrievalResult(
            matched_entry=None,
            score=0.45,
            top_k_results=[],
            retrieved=False,
        )

        result = answer_generator.generate("Unrelated question?", retrieval)

        assert result.answer == answer_generator.fallback_message
        assert result.confidence == 0.45
        assert result.source_faq_id is None
        assert result.is_fallback is True
        assert result.used_retrieval is False

    def test_fallback_preserves_low_score(
        self, answer_generator: AnswerGenerator
    ) -> None:
        """Test that fallback response includes actual retrieval score."""
        retrieval = RetrievalResult(
            matched_entry=None,
            score=0.30,
            top_k_results=[],
            retrieved=False,
        )

        result = answer_generator.generate("Q?", retrieval)

        assert result.confidence == 0.30
        assert result.is_fallback is True

    def test_ollama_not_called_for_fallback(
        self, answer_generator: AnswerGenerator
    ) -> None:
        """Test that Ollama is not called when using fallback."""
        retrieval = RetrievalResult(
            matched_entry=None,
            score=0.45,
            top_k_results=[],
            retrieved=False,
        )

        answer_generator.generate("Q?", retrieval)

        # Ollama should not be called for fallback
        assert not answer_generator.ollama_client.generate.called

    def test_off_topic_generated_answer_falls_back(
        self, answer_generator: AnswerGenerator, sample_faq: FAQEntry
    ) -> None:
        """Off-topic answers should be replaced with the deterministic fallback."""
        answer_generator.ollama_client.generate.return_value = (
            "The weather in Paris is sunny today."
        )

        retrieval = RetrievalResult(
            matched_entry=sample_faq,
            score=0.85,
            top_k_results=[(sample_faq, 0.85)],
            retrieved=True,
        )

        result = answer_generator.generate("How do I reset my password?", retrieval)

        assert result.answer == answer_generator.fallback_message
        assert result.is_fallback is True
        assert result.used_retrieval is False


class TestAnswerGeneratorErrorHandling:
    """Tests for error handling."""

    def test_empty_question_rejected(
        self, answer_generator: AnswerGenerator
    ) -> None:
        """Test that empty questions are rejected."""
        retrieval = RetrievalResult(
            matched_entry=None,
            score=0.0,
            top_k_results=[],
            retrieved=False,
        )

        with pytest.raises(AnswerGeneratorError, match="Question must not be empty"):
            answer_generator.generate("   ", retrieval)

    def test_ollama_error_wrapped(
        self, answer_generator: AnswerGenerator, sample_faq: FAQEntry
    ) -> None:
        """Test that Ollama errors are wrapped."""
        answer_generator.ollama_client.generate.side_effect = OllamaClientError(
            "Model not found"
        )

        retrieval = RetrievalResult(
            matched_entry=sample_faq,
            score=0.85,
            top_k_results=[(sample_faq, 0.85)],
            retrieved=True,
        )

        with pytest.raises(AnswerGeneratorError, match="Failed to generate answer"):
            answer_generator.generate("Q?", retrieval)

    def test_empty_answer_rejected(
        self, answer_generator: AnswerGenerator, sample_faq: FAQEntry
    ) -> None:
        """Test that empty generated answers are rejected."""
        answer_generator.ollama_client.generate.return_value = "   \n   "

        retrieval = RetrievalResult(
            matched_entry=sample_faq,
            score=0.85,
            top_k_results=[(sample_faq, 0.85)],
            retrieved=True,
        )

        with pytest.raises(AnswerGeneratorError, match="empty answer"):
            answer_generator.generate("Q?", retrieval)


class TestAnswerGeneratorEndToEnd:
    """End-to-end answer generator tests."""

    def test_from_settings_factory(self, settings: AppSettings) -> None:
        """Test AnswerGenerator.from_settings() factory."""
        generator = AnswerGenerator.from_settings(settings)

        assert generator is not None
        assert generator.ollama_client is not None
        assert generator.prompt_template is not None
        assert generator.fallback_message == settings.fallback_message

    def test_response_structure(
        self, answer_generator: AnswerGenerator, sample_faq: FAQEntry
    ) -> None:
        """Test AnswerResponse structure."""
        answer_generator.ollama_client.generate.return_value = (
            "Visit the login page and click Forgot Password."
        )

        retrieval = RetrievalResult(
            matched_entry=sample_faq,
            score=0.88,
            top_k_results=[(sample_faq, 0.88)],
            retrieved=True,
        )

        result = answer_generator.generate("Q?", retrieval)

        # Verify all fields present and correct
        assert isinstance(result, AnswerResponse)
        assert result.answer is not None
        assert isinstance(result.confidence, float)
        assert 0.0 <= result.confidence <= 1.0
        assert result.source_faq_id == "faq-001"
        assert result.is_fallback is False
        assert result.used_retrieval is True

    def test_response_immutability(
        self, answer_generator: AnswerGenerator, sample_faq: FAQEntry
    ) -> None:
        """Test that AnswerResponse is immutable."""
        answer_generator.ollama_client.generate.return_value = (
            "Visit the login page and click Forgot Password."
        )

        retrieval = RetrievalResult(
            matched_entry=sample_faq,
            score=0.88,
            top_k_results=[(sample_faq, 0.88)],
            retrieved=True,
        )

        result = answer_generator.generate("Q?", retrieval)

        # Response is frozen, attempting to modify should raise
        with pytest.raises(AttributeError):
            result.answer = "Modified"  # type: ignore
