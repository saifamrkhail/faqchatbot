"""Offline FAQ ingestion service."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass

from app.config import AppSettings
from app.domain import FAQEntry
from app.infrastructure import (
    QdrantPoint,
    OllamaClient,
    OllamaClientError,
    QdrantClient,
    QdrantClientError,
)
from app.repositories import FAQRepository, FAQRepositoryError


class IngestionServiceError(RuntimeError):
    """Raised when the ingestion workflow fails."""


@dataclass(frozen=True, slots=True)
class IngestionResult:
    """Summary of one completed ingestion run."""

    processed_entries: int
    upserted_points: int
    vector_size: int
    collection_name: str


@dataclass(slots=True)
class IngestionService:
    """Load FAQ entries, generate embeddings, and upsert them into Qdrant."""

    repository: FAQRepository
    ollama_client: OllamaClient
    qdrant_client: QdrantClient

    @classmethod
    def from_settings(cls, settings: AppSettings) -> "IngestionService":
        """Build a fully wired ingestion service from application settings."""

        return cls(
            repository=FAQRepository.from_settings(settings),
            ollama_client=OllamaClient.from_settings(settings),
            qdrant_client=QdrantClient.from_settings(settings),
        )

    def ingest(self) -> IngestionResult:
        """Ingest the configured FAQ dataset into Qdrant."""

        try:
            entries = self.repository.list_entries()
            if not entries:
                return IngestionResult(
                    processed_entries=0,
                    upserted_points=0,
                    vector_size=0,
                    collection_name=self.qdrant_client.collection_name,
                )

            points = self._build_points(entries)
            vector_size = len(points[0].vector)
            self.qdrant_client.ensure_collection(vector_size)
            upserted_points = self.qdrant_client.upsert_points(points)
        except FAQRepositoryError as exc:
            raise IngestionServiceError(f"FAQ loading failed: {exc}") from exc
        except OllamaClientError as exc:
            raise IngestionServiceError(f"Embedding generation failed: {exc}") from exc
        except QdrantClientError as exc:
            raise IngestionServiceError(f"Qdrant write failed: {exc}") from exc

        return IngestionResult(
            processed_entries=len(entries),
            upserted_points=upserted_points,
            vector_size=vector_size,
            collection_name=self.qdrant_client.collection_name,
        )

    def _build_points(self, entries: list[FAQEntry]) -> list[QdrantPoint]:
        points: list[QdrantPoint] = []
        expected_vector_size: int | None = None

        for entry in entries:
            vector = tuple(self.ollama_client.embed_text(self._build_embedding_text(entry)))
            if expected_vector_size is None:
                expected_vector_size = len(vector)
            elif len(vector) != expected_vector_size:
                raise IngestionServiceError(
                    "Embedding dimensions are inconsistent across FAQ entries"
                )

            # Convert string ID to UUID string (deterministic, valid Qdrant ID format)
            point_id_uuid = uuid.UUID(hashlib.md5(entry.id.encode()).hexdigest())
            points.append(
                QdrantPoint(
                    id=str(point_id_uuid),
                    vector=vector,
                    payload=entry.to_payload(),
                )
            )
        return points

    def _build_embedding_text(self, entry: FAQEntry) -> str:
        parts = [entry.question]
        if entry.alt_questions:
            parts.extend(entry.alt_questions)
        parts.append(entry.answer)
        if entry.category:
            parts.append(f"Category: {entry.category}")
        if entry.tags:
            parts.append(f"Tags: {', '.join(entry.tags)}")
        return "\n\n".join(parts)
