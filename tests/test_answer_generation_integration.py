"""Integration tests for answer generation pipeline."""

from __future__ import annotations

import pytest

from app.config import AppSettings
from app.domain import AnswerResponse, FAQEntry, PromptTemplate, RetrievalResult
from app.repositories import FAQRepository
from app.services import AnswerGenerator


@pytest.fixture
def app_settings() -> AppSettings:
    """Application settings for integration testing."""
    return AppSettings(
        faq_data_path="data/faq.json",
        fallback_message="Leider konnte ich Ihre Frage nicht verstehen.",
    )


@pytest.fixture
def faq_repository(app_settings: AppSettings) -> FAQRepository:
    """Load FAQ repository."""
    return FAQRepository.from_settings(app_settings)


@pytest.fixture
def sample_faqs(faq_repository: FAQRepository) -> list[FAQEntry]:
    """Load sample FAQ entries from repository."""
    return faq_repository.list_entries()


class TestAnswerGeneratorWithRealData:
    """Tests using real FAQ data."""

    def test_generator_from_settings(self, app_settings: AppSettings) -> None:
        """Test creating answer generator from settings."""
        generator = AnswerGenerator.from_settings(app_settings)

        assert generator is not None
        assert generator.ollama_client is not None
        assert generator.fallback_message == app_settings.fallback_message

    def test_prompt_template_with_real_faq(
        self, sample_faqs: list[FAQEntry]
    ) -> None:
        """Test prompt building with real FAQ data."""
        template = PromptTemplate()
        faq = sample_faqs[0]

        prompt = template.build("Test question", faq)

        assert "Test question" in prompt
        assert faq.question in prompt
        assert faq.answer in prompt

    def test_answer_response_structure(self, sample_faqs: list[FAQEntry]) -> None:
        """Test AnswerResponse structure with real data."""
        faq = sample_faqs[0]
        retrieval = RetrievalResult(
            matched_entry=faq,
            score=0.85,
            top_k_results=[(faq, 0.85)],
            retrieved=True,
        )

        response = AnswerResponse(
            answer="Generated answer",
            confidence=retrieval.score,
            source_faq_id=faq.id,
            is_fallback=False,
            used_retrieval=True,
        )

        assert response.answer == "Generated answer"
        assert response.confidence == 0.85
        assert response.source_faq_id == faq.id
        assert response.is_fallback is False
        assert response.used_retrieval is True


class TestFallbackBehavior:
    """Tests for fallback behavior."""

    def test_fallback_response_structure(
        self, app_settings: AppSettings
    ) -> None:
        """Test fallback response structure."""
        response = AnswerResponse(
            answer=app_settings.fallback_message,
            confidence=0.35,
            source_faq_id=None,
            is_fallback=True,
            used_retrieval=False,
        )

        assert response.answer == app_settings.fallback_message
        assert response.confidence == 0.35
        assert response.source_faq_id is None
        assert response.is_fallback is True
        assert response.used_retrieval is False

    def test_low_confidence_uses_fallback(self) -> None:
        """Test that low confidence scores indicate fallback usage."""
        response = AnswerResponse(
            answer="Fallback message",
            confidence=0.30,
            source_faq_id=None,
            is_fallback=True,
            used_retrieval=False,
        )

        assert response.is_fallback is True
        assert response.confidence < 0.70

    def test_high_confidence_uses_retrieval(self, sample_faqs: list[FAQEntry]) -> None:
        """Test that high confidence scores indicate retrieval was used."""
        faq = sample_faqs[0]
        response = AnswerResponse(
            answer="Generated answer",
            confidence=0.88,
            source_faq_id=faq.id,
            is_fallback=False,
            used_retrieval=True,
        )

        assert response.used_retrieval is True
        assert response.confidence >= 0.70
        assert response.source_faq_id is not None


class TestPromptTemplateVariations:
    """Tests for prompt template with different inputs."""

    def test_template_with_no_tags(self, sample_faqs: list[FAQEntry]) -> None:
        """Test prompt building with FAQ that has no tags."""
        template = PromptTemplate()
        faq = FAQEntry(
            id="test",
            question="Test Q",
            answer="Test A",
            tags=(),
            category=None,
        )

        prompt = template.build("User question", faq)

        assert "Tags: none" in prompt
        assert "uncategorized" in prompt

    def test_template_with_multiple_tags(self, sample_faqs: list[FAQEntry]) -> None:
        """Test prompt building with multiple tags."""
        template = PromptTemplate()
        faq = FAQEntry(
            id="test",
            question="Q",
            answer="A",
            tags=("tag1", "tag2", "tag3"),
            category="category",
        )

        prompt = template.build("Question", faq)

        assert "tag1, tag2, tag3" in prompt

    def test_template_special_characters(self) -> None:
        """Test prompt building with special characters."""
        template = PromptTemplate()
        faq = FAQEntry(
            id="test",
            question="Q: How do I...?",
            answer="A: You can use 'quotes' and \"double quotes\"",
            category="Test & Special",
        )

        prompt = template.build("Test @ Question!", faq)

        assert "Test @ Question!" in prompt
        assert "Q: How do I...?" in prompt
        assert "'quotes'" in prompt


class TestAnswerResponseDataModel:
    """Tests for AnswerResponse data model."""

    def test_response_immutability(self, sample_faqs: list[FAQEntry]) -> None:
        """Test that AnswerResponse is immutable."""
        faq = sample_faqs[0]
        response = AnswerResponse(
            answer="Answer",
            confidence=0.85,
            source_faq_id=faq.id,
            is_fallback=False,
            used_retrieval=True,
        )

        # Frozen dataclass should prevent modifications
        with pytest.raises(AttributeError):
            response.answer = "Modified"  # type: ignore

    def test_response_with_all_fields_none(self) -> None:
        """Test response with null/None fields."""
        response = AnswerResponse(
            answer=None,
            confidence=0.0,
            source_faq_id=None,
            is_fallback=True,
            used_retrieval=False,
        )

        assert response.answer is None
        assert response.source_faq_id is None
        assert response.confidence == 0.0

    def test_response_with_all_fields_set(
        self, sample_faqs: list[FAQEntry]
    ) -> None:
        """Test response with all fields populated."""
        faq = sample_faqs[0]
        response = AnswerResponse(
            answer="Full answer with all fields",
            confidence=0.95,
            source_faq_id=faq.id,
            is_fallback=False,
            used_retrieval=True,
        )

        assert response.answer == "Full answer with all fields"
        assert response.confidence == 0.95
        assert response.source_faq_id == faq.id
        assert response.is_fallback is False
        assert response.used_retrieval is True


class TestAnswerGenerationSemantics:
    """Tests for semantic behavior of answer generation."""

    def test_retrieved_answer_has_source(self, sample_faqs: list[FAQEntry]) -> None:
        """Test that retrieved answers have source FAQ ID."""
        faq = sample_faqs[0]
        response = AnswerResponse(
            answer="Answer from FAQ",
            confidence=0.85,
            source_faq_id=faq.id,
            is_fallback=False,
            used_retrieval=True,
        )

        assert response.source_faq_id is not None
        assert response.source_faq_id == faq.id

    def test_fallback_has_no_source(self) -> None:
        """Test that fallback responses have no source FAQ."""
        response = AnswerResponse(
            answer="Fallback message",
            confidence=0.30,
            source_faq_id=None,
            is_fallback=True,
            used_retrieval=False,
        )

        assert response.source_faq_id is None

    def test_consistency_between_fields(self) -> None:
        """Test consistency between is_fallback, used_retrieval, and source."""
        # If is_fallback=True, should not have source
        fallback_response = AnswerResponse(
            answer="Fallback",
            confidence=0.40,
            source_faq_id=None,
            is_fallback=True,
            used_retrieval=False,
        )
        assert fallback_response.is_fallback and fallback_response.source_faq_id is None

        # If used_retrieval=True, should have source
        retrieval_response = AnswerResponse(
            answer="Retrieved answer",
            confidence=0.85,
            source_faq_id="faq-001",
            is_fallback=False,
            used_retrieval=True,
        )
        assert (
            retrieval_response.used_retrieval
            and retrieval_response.source_faq_id is not None
        )

    def test_confidence_reflects_retrieval_score(self) -> None:
        """Test that response confidence reflects retrieval score."""
        high_confidence = AnswerResponse(
            answer="Answer",
            confidence=0.95,
            source_faq_id="faq-001",
            is_fallback=False,
            used_retrieval=True,
        )
        assert high_confidence.confidence == 0.95

        low_confidence = AnswerResponse(
            answer="Fallback",
            confidence=0.25,
            source_faq_id=None,
            is_fallback=True,
            used_retrieval=False,
        )
        assert low_confidence.confidence == 0.25
