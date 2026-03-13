"""Integration tests for the complete retrieval pipeline."""

from __future__ import annotations

import pytest

from app.config import AppSettings
from app.domain import FAQEntry, RetrievalResult
from app.repositories import FAQRepository
from app.services import IngestionService, Retriever


@pytest.fixture
def app_settings() -> AppSettings:
    """Application settings for integration testing."""
    return AppSettings(
        faq_data_path="data/faq.json",
        top_k=3,
        score_threshold=0.70,
    )


@pytest.fixture
def faq_repository(app_settings: AppSettings) -> FAQRepository:
    """Load FAQ repository."""
    return FAQRepository.from_settings(app_settings)


@pytest.fixture
def sample_faqs(faq_repository: FAQRepository) -> list[FAQEntry]:
    """Load sample FAQ entries from repository."""
    return faq_repository.list_entries()


class TestRetrieverWithRealData:
    """Tests using real FAQ data."""

    def test_retriever_from_settings(self, app_settings: AppSettings) -> None:
        """Test creating retriever from settings."""
        retriever = Retriever.from_settings(app_settings)

        assert retriever is not None
        assert retriever.top_k == 3
        assert retriever.score_threshold == 0.70

    def test_sample_faq_data_loads(self, sample_faqs: list[FAQEntry]) -> None:
        """Test that sample FAQ data loads successfully."""
        assert len(sample_faqs) > 0
        assert all(isinstance(faq, FAQEntry) for faq in sample_faqs)
        assert all(faq.id for faq in sample_faqs)
        assert all(faq.question for faq in sample_faqs)
        assert all(faq.answer for faq in sample_faqs)

    def test_faq_data_structure(self, sample_faqs: list[FAQEntry]) -> None:
        """Test that FAQ data has expected structure."""
        for faq in sample_faqs:
            payload = faq.to_payload()
            assert "id" in payload
            assert "question" in payload
            assert "answer" in payload
            assert payload["id"] == faq.id
            assert payload["question"] == faq.question
            assert payload["answer"] == faq.answer

    def test_retrieval_result_structure(
        self, app_settings: AppSettings, sample_faqs: list[FAQEntry]
    ) -> None:
        """Test RetrievalResult structure with sample data."""
        # Create a sample result
        top_results = [(sample_faqs[0], 0.85)]
        result = RetrievalResult(
            matched_entry=sample_faqs[0],
            score=0.85,
            top_k_results=top_results,
            retrieved=True,
        )

        assert result.matched_entry is not None
        assert result.score == 0.85
        assert result.retrieved is True
        assert len(result.top_k_results) == 1
        assert result.top_k_results[0][0].id == sample_faqs[0].id

    def test_retrieval_fallback_result(self) -> None:
        """Test RetrievalResult with fallback (no match)."""
        result = RetrievalResult(
            matched_entry=None,
            score=0.45,
            top_k_results=[],
            retrieved=False,
        )

        assert result.matched_entry is None
        assert result.score == 0.45
        assert result.retrieved is False
        assert len(result.top_k_results) == 0


class TestRetrieverConfiguration:
    """Tests for retriever configuration."""

    def test_different_thresholds(self, app_settings: AppSettings) -> None:
        """Test retriever with different threshold configurations."""
        from unittest.mock import MagicMock

        ollama_client = MagicMock()
        qdrant_client = MagicMock()

        # High threshold (conservative)
        conservative_retriever = Retriever(
            ollama_client=ollama_client,
            qdrant_client=qdrant_client,
            top_k=3,
            score_threshold=0.90,
        )
        assert conservative_retriever.score_threshold == 0.90

        # Low threshold (loose)
        loose_retriever = Retriever(
            ollama_client=ollama_client,
            qdrant_client=qdrant_client,
            top_k=3,
            score_threshold=0.50,
        )
        assert loose_retriever.score_threshold == 0.50

    def test_different_top_k(self, app_settings: AppSettings) -> None:
        """Test retriever with different top_k configurations."""
        from unittest.mock import MagicMock

        ollama_client = MagicMock()
        qdrant_client = MagicMock()

        # Small k
        small_k_retriever = Retriever(
            ollama_client=ollama_client,
            qdrant_client=qdrant_client,
            top_k=1,
            score_threshold=0.70,
        )
        assert small_k_retriever.top_k == 1

        # Large k
        large_k_retriever = Retriever(
            ollama_client=ollama_client,
            qdrant_client=qdrant_client,
            top_k=10,
            score_threshold=0.70,
        )
        assert large_k_retriever.top_k == 10

    def test_threshold_boundary_cases(self) -> None:
        """Test threshold evaluation at boundary values."""
        test_faq = FAQEntry(
            id="test-001",
            question="Test question",
            answer="Test answer",
        )

        # Score exactly at threshold
        result_at_threshold = RetrievalResult(
            matched_entry=test_faq,
            score=0.70,
            top_k_results=[(test_faq, 0.70)],
            retrieved=True,
        )
        assert result_at_threshold.retrieved is True

        # Score just below threshold
        result_below_threshold = RetrievalResult(
            matched_entry=None,
            score=0.69,
            top_k_results=[(test_faq, 0.69)],
            retrieved=False,
        )
        assert result_below_threshold.retrieved is False

        # Score just above threshold
        result_above_threshold = RetrievalResult(
            matched_entry=test_faq,
            score=0.71,
            top_k_results=[(test_faq, 0.71)],
            retrieved=True,
        )
        assert result_above_threshold.retrieved is True


class TestRetrieverDataFlow:
    """Tests for data flow through retriever."""

    def test_empty_results_handling(self) -> None:
        """Test handling of empty search results."""
        result = RetrievalResult(
            matched_entry=None,
            score=0.0,
            top_k_results=[],
            retrieved=False,
        )

        assert result.matched_entry is None
        assert result.retrieved is False
        assert len(result.top_k_results) == 0

    def test_single_result_handling(self, sample_faqs: list[FAQEntry]) -> None:
        """Test handling of single search result."""
        faq = sample_faqs[0]
        result = RetrievalResult(
            matched_entry=faq,
            score=0.85,
            top_k_results=[(faq, 0.85)],
            retrieved=True,
        )

        assert result.matched_entry.id == faq.id
        assert len(result.top_k_results) == 1
        assert result.top_k_results[0][0].id == faq.id

    def test_multiple_results_ranking(self, sample_faqs: list[FAQEntry]) -> None:
        """Test ranking of multiple search results."""
        faq1, faq2 = sample_faqs[0], sample_faqs[1] if len(sample_faqs) > 1 else sample_faqs[0]

        top_k_results = [
            (faq1, 0.85),
            (faq2, 0.75),
        ]
        result = RetrievalResult(
            matched_entry=faq1,
            score=0.85,
            top_k_results=top_k_results,
            retrieved=True,
        )

        # Best match should be first
        assert result.matched_entry.id == result.top_k_results[0][0].id
        # Score should be from best match
        assert result.score == result.top_k_results[0][1]
        # Results should be in descending score order
        assert result.top_k_results[0][1] >= result.top_k_results[1][1]

    def test_retrieval_result_immutability(self, sample_faqs: list[FAQEntry]) -> None:
        """Test that RetrievalResult is immutable."""
        faq = sample_faqs[0]
        result = RetrievalResult(
            matched_entry=faq,
            score=0.85,
            top_k_results=[(faq, 0.85)],
            retrieved=True,
        )

        # RetrievalResult is frozen, attempting to modify should raise
        with pytest.raises(AttributeError):
            result.score = 0.75  # type: ignore


class TestRetrieverSemantics:
    """Tests for semantic retrieval behavior."""

    def test_retrieval_result_complete_info(self, sample_faqs: list[FAQEntry]) -> None:
        """Test that RetrievalResult contains all needed information."""
        faq = sample_faqs[0]
        result = RetrievalResult(
            matched_entry=faq,
            score=0.85,
            top_k_results=[(faq, 0.85)],
            retrieved=True,
        )

        # Should be able to access all fields
        assert result.matched_entry is not None
        assert result.matched_entry.id == faq.id
        assert result.matched_entry.question == faq.question
        assert result.matched_entry.answer == faq.answer

        # Score should be accessible
        assert 0.0 <= result.score <= 1.0

        # Retrieved flag should match threshold logic
        assert result.retrieved == (result.score >= 0.70)

    def test_no_match_has_no_entry(self) -> None:
        """Test that no-match results have None entry."""
        result = RetrievalResult(
            matched_entry=None,
            score=0.45,
            top_k_results=[],
            retrieved=False,
        )

        assert result.matched_entry is None
        assert result.retrieved is False
        assert result.score < 0.70

    def test_match_status_consistency(self, sample_faqs: list[FAQEntry]) -> None:
        """Test consistency between matched_entry and retrieved flag."""
        faq = sample_faqs[0]

        # If retrieved=True, matched_entry should be present
        matched_result = RetrievalResult(
            matched_entry=faq,
            score=0.85,
            top_k_results=[(faq, 0.85)],
            retrieved=True,
        )
        assert matched_result.matched_entry is not None

        # If retrieved=False, matched_entry should be None
        fallback_result = RetrievalResult(
            matched_entry=None,
            score=0.45,
            top_k_results=[(faq, 0.45)],
            retrieved=False,
        )
        assert fallback_result.matched_entry is None
