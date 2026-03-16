"""Unit tests for the Retriever service."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.config import AppSettings
from app.domain import FAQEntry, RetrievalResult
from app.infrastructure import (
    OllamaClientError,
    OllamaGenerationResult,
    QdrantClientError,
    QdrantSearchResult,
)
from app.services import Retriever, RetrieverError


@pytest.fixture
def settings() -> AppSettings:
    """Minimal settings for retriever testing."""
    return AppSettings(
        top_k=3,
        score_threshold=0.70,
        ollama_base_url="http://localhost:11434",
        qdrant_url="http://localhost:6333",
    )


@pytest.fixture
def sample_faq_entry() -> FAQEntry:
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
def retriever(settings: AppSettings) -> Retriever:
    """Create a retriever with mock clients."""
    ollama_client = MagicMock()
    qdrant_client = MagicMock()

    retriever = Retriever(
        ollama_client=ollama_client,
        qdrant_client=qdrant_client,
        top_k=settings.top_k,
        score_threshold=settings.score_threshold,
    )
    return retriever


class TestRetrieverQuestionEmbedding:
    """Tests for question embedding."""

    def test_embed_question_success(self, retriever: Retriever) -> None:
        """Test successful question embedding."""
        test_vector = [0.1, 0.2, 0.3]
        retriever.ollama_client.embed_text.return_value = test_vector

        retriever.qdrant_client.search.return_value = []

        question = "How do I reset my password?"
        result = retriever.retrieve(question)

        retriever.ollama_client.embed_text.assert_called_once_with(question)
        assert result.matched_entry is None
        assert result.score == 0.0

    def test_retrieve_empty_question_fails(self, retriever: Retriever) -> None:
        """Test that empty questions are rejected."""
        with pytest.raises(RetrieverError, match="Question must not be empty"):
            retriever.retrieve("   ")

    def test_retrieve_embedding_error_wrapped(self, retriever: Retriever) -> None:
        """Test that embedding errors are wrapped."""
        retriever.ollama_client.embed_text.side_effect = OllamaClientError(
            "Model not found"
        )

        with pytest.raises(RetrieverError, match="Failed to embed question"):
            retriever.retrieve("How do I reset my password?")


class TestRetrieverVectorSearch:
    """Tests for vector search."""

    def test_search_with_results(
        self, retriever: Retriever, sample_faq_entry: FAQEntry
    ) -> None:
        """Test search returning results."""
        test_vector = [0.1, 0.2, 0.3]
        retriever.ollama_client.embed_text.return_value = test_vector

        search_result = QdrantSearchResult(
            id="faq-001",
            score=0.85,
            payload=sample_faq_entry.to_payload(),
        )
        retriever.qdrant_client.search.return_value = [search_result]

        result = retriever.retrieve("How do I reset my password?")

        retriever.qdrant_client.search.assert_called_once()
        call_args = retriever.qdrant_client.search.call_args
        assert call_args.kwargs["limit"] == 3
        assert call_args.kwargs["with_payload"] is True

    def test_search_error_wrapped(self, retriever: Retriever) -> None:
        """Test that search errors are wrapped."""
        test_vector = [0.1, 0.2, 0.3]
        retriever.ollama_client.embed_text.return_value = test_vector

        retriever.qdrant_client.search.side_effect = QdrantClientError(
            "Connection failed"
        )

        with pytest.raises(RetrieverError, match="Failed to search FAQ database"):
            retriever.retrieve("How do I reset my password?")

    def test_search_with_no_results(self, retriever: Retriever) -> None:
        """Test search with no results."""
        test_vector = [0.1, 0.2, 0.3]
        retriever.ollama_client.embed_text.return_value = test_vector

        retriever.qdrant_client.search.return_value = []

        result = retriever.retrieve("Unrelated question")

        assert result.matched_entry is None
        assert result.score == 0.0
        assert result.retrieved is False
        assert len(result.top_k_results) == 0


class TestRetrieverThresholdEvaluation:
    """Tests for threshold evaluation."""

    def test_high_score_above_threshold(
        self, retriever: Retriever, sample_faq_entry: FAQEntry
    ) -> None:
        """Test that high scores trigger matched_entry."""
        test_vector = [0.1, 0.2, 0.3]
        retriever.ollama_client.embed_text.return_value = test_vector

        search_result = QdrantSearchResult(
            id="faq-001",
            score=0.85,
            payload=sample_faq_entry.to_payload(),
        )
        retriever.qdrant_client.search.return_value = [search_result]

        result = retriever.retrieve("How do I reset my password?")

        assert result.matched_entry is not None
        assert result.matched_entry.id == "faq-001"
        assert result.score >= 0.85
        assert result.retrieved is True

    def test_low_score_below_threshold(
        self, retriever: Retriever, sample_faq_entry: FAQEntry
    ) -> None:
        """Test that low scores trigger fallback."""
        test_vector = [0.1, 0.2, 0.3]
        retriever.ollama_client.embed_text.return_value = test_vector

        search_result = QdrantSearchResult(
            id="faq-001",
            score=0.50,
            payload=sample_faq_entry.to_payload(),
        )
        retriever.qdrant_client.search.return_value = [search_result]

        result = retriever.retrieve("Unrelated question")

        assert result.matched_entry is None
        assert result.score == 0.50
        assert result.retrieved is False

    def test_score_exactly_at_threshold(
        self, retriever: Retriever, sample_faq_entry: FAQEntry
    ) -> None:
        """Test that scores exactly at threshold are matched."""
        test_vector = [0.1, 0.2, 0.3]
        retriever.ollama_client.embed_text.return_value = test_vector

        search_result = QdrantSearchResult(
            id="faq-001",
            score=0.70,
            payload=sample_faq_entry.to_payload(),
        )
        retriever.qdrant_client.search.return_value = [search_result]

        result = retriever.retrieve("Question")

        assert result.matched_entry is not None
        assert result.score == 0.70
        assert result.retrieved is True

    def test_multiple_results_best_used(
        self, retriever: Retriever
    ) -> None:
        """Test that best result is used from multiple results."""
        test_vector = [0.1, 0.2, 0.3]
        retriever.ollama_client.embed_text.return_value = test_vector

        faq1 = FAQEntry(
            id="faq-001",
            question="Password reset",
            answer="Click forgot password.",
        )
        faq2 = FAQEntry(
            id="faq-002",
            question="Account recovery",
            answer="Use recovery email.",
        )

        results = [
            QdrantSearchResult(id="faq-001", score=0.85, payload=faq1.to_payload()),
            QdrantSearchResult(id="faq-002", score=0.65, payload=faq2.to_payload()),
        ]
        retriever.qdrant_client.search.return_value = results

        result = retriever.retrieve("How do I reset?")

        assert result.matched_entry.id == "faq-001"
        assert result.score >= 0.85
        assert len(result.top_k_results) == 2

    def test_top_k_results_included(
        self, retriever: Retriever
    ) -> None:
        """Test that all top-k results are included in output."""
        test_vector = [0.1, 0.2, 0.3]
        retriever.ollama_client.embed_text.return_value = test_vector

        faq1 = FAQEntry(id="faq-001", question="Q1", answer="A1")
        faq2 = FAQEntry(id="faq-002", question="Q2", answer="A2")
        faq3 = FAQEntry(id="faq-003", question="Q3", answer="A3")

        results = [
            QdrantSearchResult(id="faq-001", score=0.85, payload=faq1.to_payload()),
            QdrantSearchResult(id="faq-002", score=0.75, payload=faq2.to_payload()),
            QdrantSearchResult(id="faq-003", score=0.65, payload=faq3.to_payload()),
        ]
        retriever.qdrant_client.search.return_value = results

        result = retriever.retrieve("Question")

        assert len(result.top_k_results) == 3
        assert result.top_k_results[0][1] == 0.85
        assert result.top_k_results[1][1] == 0.75
        assert result.top_k_results[2][1] == 0.65


class TestRetrieverEndToEnd:
    """End-to-end retriever tests."""

    def test_from_settings_factory(self, settings: AppSettings) -> None:
        """Test Retriever.from_settings() creates properly configured instance."""
        retriever = Retriever.from_settings(settings)

        assert retriever.top_k == 3
        assert retriever.score_threshold == 0.70
        assert retriever.query_rewrite_enabled is True
        assert retriever.query_rewrite_borderline_min_score == pytest.approx(0.35)
        assert retriever.query_rewrite_max_variants == 3
        assert retriever.ollama_client is not None
        assert retriever.qdrant_client is not None

    def test_retrieval_pipeline_success(
        self, retriever: Retriever, sample_faq_entry: FAQEntry
    ) -> None:
        """Test complete retrieval pipeline."""
        test_vector = [0.1, 0.2, 0.3]
        retriever.ollama_client.embed_text.return_value = test_vector

        search_result = QdrantSearchResult(
            id="faq-001",
            score=0.88,
            payload=sample_faq_entry.to_payload(),
        )
        retriever.qdrant_client.search.return_value = [search_result]

        result = retriever.retrieve("How do I reset my password?")

        assert isinstance(result, RetrievalResult)
        assert result.matched_entry is not None
        assert result.matched_entry.id == "faq-001"
        assert result.score >= 0.88
        assert result.retrieved is True
        assert len(result.top_k_results) == 1

    def test_retrieval_pipeline_fallback(
        self, retriever: Retriever, sample_faq_entry: FAQEntry
    ) -> None:
        """Test retrieval pipeline with fallback."""
        test_vector = [0.1, 0.2, 0.3]
        retriever.ollama_client.embed_text.return_value = test_vector

        search_result = QdrantSearchResult(
            id="faq-001",
            score=0.45,
            payload=sample_faq_entry.to_payload(),
        )
        retriever.qdrant_client.search.return_value = [search_result]

        result = retriever.retrieve("Completely unrelated question")

        assert isinstance(result, RetrievalResult)
        assert result.matched_entry is None
        assert result.score == 0.45
        assert result.retrieved is False

    def test_invalid_faq_payload_error(self, retriever: Retriever) -> None:
        """Test handling of invalid FAQ payload from search results."""
        test_vector = [0.1, 0.2, 0.3]
        retriever.ollama_client.embed_text.return_value = test_vector

        invalid_payload = {"id": "faq-001"}  # Missing required fields
        search_result = QdrantSearchResult(
            id="faq-001",
            score=0.85,
            payload=invalid_payload,
        )
        retriever.qdrant_client.search.return_value = [search_result]

        with pytest.raises(RetrieverError, match="Failed to parse FAQ entry"):
            retriever.retrieve("Question")

    def test_lexical_bonus_can_promote_better_match(self, retriever: Retriever) -> None:
        test_vector = [0.1, 0.2, 0.3]
        retriever.ollama_client.embed_text.return_value = test_vector

        weak_semantic_match = FAQEntry(
            id="faq-001",
            question="Generic help",
            answer="We offer support.",
            tags=("support",),
        )
        strong_lexical_match = FAQEntry(
            id="faq-002",
            question="24 7 support options",
            answer="We provide 24/7 helpdesk support.",
            tags=("24-7", "support", "helpdesk"),
        )

        retriever.qdrant_client.search.return_value = [
            QdrantSearchResult(
                id="faq-001",
                score=0.62,
                payload=weak_semantic_match.to_payload(),
            ),
            QdrantSearchResult(
                id="faq-002",
                score=0.56,
                payload=strong_lexical_match.to_payload(),
            ),
        ]

        result = retriever.retrieve("Habt ihr 24/7 Support?")

        assert result.matched_entry is not None
        assert result.matched_entry.id == "faq-002"


class TestRetrieverQueryRewrite:
    """Tests for the optional borderline query rewrite stage."""

    def test_query_rewrite_promotes_borderline_match(
        self,
        sample_faq_entry: FAQEntry,
    ) -> None:
        retriever = Retriever(
            ollama_client=MagicMock(),
            qdrant_client=MagicMock(),
            top_k=3,
            score_threshold=0.50,
            query_rewrite_borderline_min_score=0.35,
        )
        retriever.ollama_client.embed_text.side_effect = [
            [0.1, 0.2, 0.3],
            [0.3, 0.2, 0.1],
        ]
        retriever.ollama_client.generate_response.return_value = OllamaGenerationResult(
            response="How do I reset my password?"
        )
        retriever.qdrant_client.search.side_effect = [
            [
                QdrantSearchResult(
                    id="faq-001",
                    score=0.42,
                    payload=sample_faq_entry.to_payload(),
                )
            ],
            [
                QdrantSearchResult(
                    id="faq-001",
                    score=0.58,
                    payload=sample_faq_entry.to_payload(),
                )
            ],
        ]

        result = retriever.retrieve("Can't sign in anymore")

        assert result.retrieved is True
        assert result.matched_entry is not None
        assert result.matched_entry.id == "faq-001"
        assert result.score >= 0.58
        assert retriever.ollama_client.generate_response.called

    def test_query_rewrite_skips_low_confidence_noise(
        self,
        sample_faq_entry: FAQEntry,
    ) -> None:
        retriever = Retriever(
            ollama_client=MagicMock(),
            qdrant_client=MagicMock(),
            top_k=3,
            score_threshold=0.50,
            query_rewrite_borderline_min_score=0.35,
        )
        retriever.ollama_client.embed_text.return_value = [0.1, 0.2, 0.3]
        retriever.qdrant_client.search.return_value = [
            QdrantSearchResult(
                id="faq-001",
                score=0.20,
                payload=sample_faq_entry.to_payload(),
            )
        ]

        result = retriever.retrieve("Hello there")

        assert result.retrieved is False
        assert result.score == pytest.approx(0.20)
        assert not retriever.ollama_client.generate_response.called

    def test_query_rewrite_requires_support_for_different_faq_candidate(self) -> None:
        faq1 = FAQEntry(
            id="faq-001",
            question="Password reset",
            answer="Click forgot password.",
        )
        faq2 = FAQEntry(
            id="faq-002",
            question="Multi-factor authentication setup",
            answer="Open the security settings and enroll a device.",
        )
        retriever = Retriever(
            ollama_client=MagicMock(),
            qdrant_client=MagicMock(),
            top_k=3,
            score_threshold=0.50,
            query_rewrite_borderline_min_score=0.35,
        )
        retriever.ollama_client.embed_text.side_effect = [
            [0.1, 0.2, 0.3],
            [0.3, 0.2, 0.1],
        ]
        retriever.ollama_client.generate_response.return_value = OllamaGenerationResult(
            response="Need device enrollment"
        )
        retriever.qdrant_client.search.side_effect = [
            [QdrantSearchResult(id="faq-001", score=0.44, payload=faq1.to_payload())],
            [QdrantSearchResult(id="faq-002", score=0.55, payload=faq2.to_payload())],
        ]

        result = retriever.retrieve("I need help signing in")

        assert result.retrieved is False
        assert result.matched_entry is None
        assert result.score == pytest.approx(0.44)

    def test_query_rewrite_failure_returns_primary_result(
        self,
        sample_faq_entry: FAQEntry,
    ) -> None:
        retriever = Retriever(
            ollama_client=MagicMock(),
            qdrant_client=MagicMock(),
            top_k=3,
            score_threshold=0.50,
            query_rewrite_borderline_min_score=0.35,
        )
        retriever.ollama_client.embed_text.return_value = [0.1, 0.2, 0.3]
        retriever.ollama_client.generate_response.side_effect = OllamaClientError(
            "rewrite timeout"
        )
        retriever.qdrant_client.search.return_value = [
            QdrantSearchResult(
                id="faq-001",
                score=0.45,
                payload=sample_faq_entry.to_payload(),
            )
        ]

        result = retriever.retrieve("Can't log in anymore")

        assert result.retrieved is False
        assert result.matched_entry is None
        assert result.score == pytest.approx(0.45)
