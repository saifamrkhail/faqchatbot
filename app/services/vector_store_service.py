"""Vector store abstraction layer for future extensibility."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from app.config import AppSettings
from app.domain import FAQEntry
from app.infrastructure import QdrantClient, QdrantClientError


class VectorStoreError(RuntimeError):
    """Raised when vector store operations fail."""


@dataclass(slots=True)
class VectorStoreService:
    """Abstraction layer over Qdrant for vector operations."""

    qdrant_client: QdrantClient

    @classmethod
    def from_settings(cls, settings: AppSettings) -> "VectorStoreService":
        """Build a vector store service from application settings."""

        return cls(qdrant_client=QdrantClient.from_settings(settings))

    def search(
        self, vector: Sequence[float], limit: int
    ) -> list[tuple[FAQEntry, float]]:
        """Search for nearest FAQ entries by vector similarity.

        Returns list of (FAQEntry, similarity_score) tuples.
        Raises VectorStoreError if search fails or payload parsing fails.
        """

        try:
            raw_results = self.qdrant_client.search(
                vector=vector, limit=limit, with_payload=True
            )

            results: list[tuple[FAQEntry, float]] = []
            for raw_result in raw_results:
                if raw_result.payload is None:
                    continue

                entry = FAQEntry.from_dict(raw_result.payload)
                results.append((entry, raw_result.score))

            return results
        except QdrantClientError as exc:
            raise VectorStoreError(f"Vector store search failed: {exc}") from exc
        except Exception as exc:
            raise VectorStoreError(
                f"Failed to parse FAQ entry from search result: {exc}"
            ) from exc
