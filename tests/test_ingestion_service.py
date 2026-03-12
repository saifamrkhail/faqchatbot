"""Unit tests for the ingestion service."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.domain.faq import FaqEntry
from app.services.ingestion_service import IngestionService, IngestionResult


@pytest.fixture
def mock_ollama_client():
    """Create a mock Ollama client."""
    mock = AsyncMock()
    mock.embed_text = AsyncMock(return_value=[0.1] * 384)  # nomic-embed-text dim
    mock.get_embedding_dimension = AsyncMock(return_value=384)
    mock.health_check = AsyncMock(return_value=True)
    mock.close = AsyncMock()
    return mock


@pytest.fixture
def mock_qdrant_client():
    """Create a mock Qdrant client."""
    mock = MagicMock()
    mock.collection_exists = MagicMock(return_value=False)
    mock.create_collection = MagicMock()
    mock.upsert_points = MagicMock()
    mock.health_check = MagicMock(return_value=True)
    return mock


@pytest.fixture
def ingestion_service(mock_ollama_client, mock_qdrant_client):
    """Create an ingestion service with mocked clients."""
    return IngestionService(mock_ollama_client, mock_qdrant_client)


@pytest.fixture
def sample_faq_entries():
    """Create sample FAQ entries for testing."""
    return [
        FaqEntry(
            id="faq_001",
            question="How do I reset my password?",
            answer="Click forgot password on the login page.",
            tags=["account"],
            category="Account Management",
            source="help_center",
        ),
        FaqEntry(
            id="faq_002",
            question="What payment methods do you accept?",
            answer="We accept Visa, Mastercard, and PayPal.",
            tags=["payment"],
            category="Billing",
            source="faq",
        ),
    ]


class TestIngestionResult:
    """Tests for IngestionResult dataclass."""

    def test_success_property_when_no_failures(self):
        """Test success property returns True when no failures."""
        result = IngestionResult(total_entries=2, successful_entries=2)
        assert result.success is True

    def test_success_property_when_failures_exist(self):
        """Test success property returns False when failures exist."""
        result = IngestionResult(
            total_entries=2, successful_entries=1, failed_entries=1
        )
        assert result.success is False

    def test_add_error(self):
        """Test adding an error to the result."""
        result = IngestionResult()
        result.add_error("faq_001", "Embedding failed")
        assert result.failed_entries == 1
        assert len(result.errors) == 1
        assert "faq_001" in result.errors[0]

    def test_string_representation(self):
        """Test string representation of result."""
        result = IngestionResult(total_entries=2, successful_entries=1)
        result_str = str(result)
        assert "1/2" in result_str
        assert "successfully ingested" in result_str


class TestIngestionService:
    """Tests for IngestionService."""

    @pytest.mark.asyncio
    async def test_ensure_collection_exists_creates_when_missing(
        self, ingestion_service, mock_qdrant_client
    ):
        """Test collection creation when it doesn't exist."""
        mock_qdrant_client.collection_exists.return_value = False

        await ingestion_service.ensure_collection_exists(embedding_dim=384)

        mock_qdrant_client.create_collection.assert_called_once_with(vector_dim=384)

    @pytest.mark.asyncio
    async def test_ensure_collection_exists_when_already_exists(
        self, ingestion_service, mock_qdrant_client
    ):
        """Test collection verification when it already exists."""
        mock_qdrant_client.collection_exists.return_value = True

        await ingestion_service.ensure_collection_exists(embedding_dim=384)

        mock_qdrant_client.create_collection.assert_not_called()

    @pytest.mark.asyncio
    async def test_embed_text(self, ingestion_service, mock_ollama_client):
        """Test text embedding."""
        text = "Test question"
        expected_embedding = [0.1] * 384

        result = await ingestion_service._embed_text(text)

        assert result == expected_embedding
        mock_ollama_client.embed_text.assert_called_once_with(text)

    @pytest.mark.asyncio
    async def test_embed_text_handles_errors(self, ingestion_service, mock_ollama_client):
        """Test embedding handles errors gracefully."""
        mock_ollama_client.embed_text.side_effect = RuntimeError("Ollama unavailable")

        with pytest.raises(RuntimeError, match="Embedding failed"):
            await ingestion_service._embed_text("Test")

    @pytest.mark.asyncio
    async def test_prepare_qdrant_points(
        self, ingestion_service, sample_faq_entries, mock_ollama_client
    ):
        """Test preparing Qdrant points from FAQ entries."""
        result = IngestionResult(total_entries=len(sample_faq_entries))

        points = await ingestion_service._prepare_qdrant_points(
            sample_faq_entries, result
        )

        assert len(points) == 2
        assert points[0].id in ["faq_001", 1]  # Could be string or int
        assert "faq_001" in points[0].payload["faq_id"]
        assert points[0].payload["question"] == "How do I reset my password?"
        assert len(points[0].vector) == 384

    @pytest.mark.asyncio
    async def test_prepare_qdrant_points_with_embedding_failure(
        self, ingestion_service, mock_ollama_client
    ):
        """Test point preparation handles embedding failures."""
        entries = [
            FaqEntry(
                id="faq_001",
                question="Question 1",
                answer="Answer 1",
            ),
            FaqEntry(
                id="faq_002",
                question="Question 2",
                answer="Answer 2",
            ),
        ]

        # Fail on second embedding
        mock_ollama_client.embed_text.side_effect = [
            [0.1] * 384,
            RuntimeError("Embedding failed"),
        ]

        result = IngestionResult(total_entries=len(entries))
        points = await ingestion_service._prepare_qdrant_points(entries, result)

        assert len(points) == 1  # Only one successful point
        assert result.failed_entries == 1

    @pytest.mark.asyncio
    async def test_ingest_faq_entries_success(
        self,
        ingestion_service,
        sample_faq_entries,
        mock_ollama_client,
        mock_qdrant_client,
    ):
        """Test successful FAQ ingestion."""
        result = await ingestion_service.ingest_faq_entries(sample_faq_entries)

        assert result.total_entries == 2
        assert result.successful_entries == 2
        assert result.failed_entries == 0
        assert result.success is True

        mock_qdrant_client.create_collection.assert_called_once()
        mock_qdrant_client.upsert_points.assert_called_once()

    @pytest.mark.asyncio
    async def test_ingest_faq_entries_empty_list(self, ingestion_service):
        """Test ingestion with empty FAQ list."""
        result = await ingestion_service.ingest_faq_entries([])

        assert result.total_entries == 0
        assert result.successful_entries == 0

    @pytest.mark.asyncio
    async def test_ingest_faq_entries_qdrant_failure(
        self, ingestion_service, sample_faq_entries, mock_qdrant_client
    ):
        """Test ingestion handles Qdrant upsert failures."""
        mock_qdrant_client.upsert_points.side_effect = RuntimeError("Qdrant error")

        result = await ingestion_service.ingest_faq_entries(sample_faq_entries)

        assert result.successful_entries == 0
        assert result.failed_entries > 0

    @pytest.mark.asyncio
    async def test_ingest_faq_entries_embedding_dimension_retrieval(
        self, ingestion_service, sample_faq_entries, mock_ollama_client
    ):
        """Test that embedding dimension is retrieved and used."""
        await ingestion_service.ingest_faq_entries(sample_faq_entries)

        mock_ollama_client.get_embedding_dimension.assert_called_once()

    @pytest.mark.asyncio
    async def test_entry_id_to_point_id_with_numeric_id(self):
        """Test conversion of numeric FAQ ID to point ID."""
        point_id = IngestionService._entry_id_to_point_id("123", 0)
        assert point_id == 123
        assert isinstance(point_id, int)

    @pytest.mark.asyncio
    async def test_entry_id_to_point_id_with_string_id(self):
        """Test conversion of string FAQ ID to point ID."""
        point_id = IngestionService._entry_id_to_point_id("faq_001", 0)
        assert point_id == "faq_001"
        assert isinstance(point_id, str)
