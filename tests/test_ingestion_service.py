from __future__ import annotations

from dataclasses import dataclass

import pytest

from app.domain import FAQEntry
from app.infrastructure import QdrantClientError
from app.repositories import FAQRepositoryError
from app.services import IngestionService, IngestionServiceError


@dataclass
class FakeRepository:
    entries: list[FAQEntry]

    def list_entries(self) -> list[FAQEntry]:
        return self.entries


@dataclass
class FakeOllamaClient:
    embeddings: dict[str, list[float]]

    def embed_text(self, text: str) -> list[float]:
        return self.embeddings[text]


@dataclass
class FakeQdrantClient:
    collection_name: str = "faq_entries"
    ensured_vector_size: int | None = None
    upserted_points: list[object] | None = None

    def ensure_collection(self, vector_size: int) -> None:
        self.ensured_vector_size = vector_size

    def upsert_points(self, points: list[object]) -> int:
        self.upserted_points = points
        return len(points)


def test_ingestion_service_loads_embeds_and_upserts_entries() -> None:
    entry = FAQEntry(
        id="faq-1",
        question="Welche Leistungen bieten Sie an?",
        answer="Wir bieten Support.",
        tags=("support",),
        category="services",
        source="fixture.json",
    )
    embedding_text = (
        "Welche Leistungen bieten Sie an?\n\n"
        "Wir bieten Support.\n\n"
        "Category: services\n\n"
        "Tags: support"
    )
    service = IngestionService(
        repository=FakeRepository([entry]),
        ollama_client=FakeOllamaClient({embedding_text: [0.1, 0.2, 0.3]}),
        qdrant_client=FakeQdrantClient(),
    )

    result = service.ingest()

    assert result.processed_entries == 1
    assert result.upserted_points == 1
    assert result.vector_size == 3
    assert service.qdrant_client.ensured_vector_size == 3
    assert service.qdrant_client.upserted_points is not None


def test_ingestion_service_rejects_inconsistent_embedding_sizes() -> None:
    entries = [
        FAQEntry(id="faq-1", question="Q1", answer="A1"),
        FAQEntry(id="faq-2", question="Q2", answer="A2"),
    ]
    service = IngestionService(
        repository=FakeRepository(entries),
        ollama_client=FakeOllamaClient(
            {
                "Q1\n\nA1": [0.1, 0.2],
                "Q2\n\nA2": [0.1, 0.2, 0.3],
            }
        ),
        qdrant_client=FakeQdrantClient(),
    )

    with pytest.raises(IngestionServiceError, match="Embedding dimensions"):
        service.ingest()


def test_ingestion_service_wraps_repository_errors() -> None:
    class BrokenRepository:
        def list_entries(self) -> list[FAQEntry]:
            raise FAQRepositoryError("bad file")

    service = IngestionService(
        repository=BrokenRepository(),
        ollama_client=FakeOllamaClient({}),
        qdrant_client=FakeQdrantClient(),
    )

    with pytest.raises(IngestionServiceError, match="FAQ loading failed"):
        service.ingest()


def test_ingestion_service_wraps_qdrant_errors() -> None:
    entry = FAQEntry(id="faq-1", question="Q1", answer="A1")

    class BrokenQdrantClient(FakeQdrantClient):
        def upsert_points(self, points: list[object]) -> int:
            raise QdrantClientError("write failed")

    service = IngestionService(
        repository=FakeRepository([entry]),
        ollama_client=FakeOllamaClient({"Q1\n\nA1": [0.1, 0.2]}),
        qdrant_client=BrokenQdrantClient(),
    )

    with pytest.raises(IngestionServiceError, match="Qdrant write failed"):
        service.ingest()
