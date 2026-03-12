"""Ingestion service for loading FAQ entries into Qdrant."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Sequence

try:
    from qdrant_client.models import PointStruct
except ImportError as e:
    raise ImportError(
        "qdrant-client not installed. Install with: pip install qdrant-client"
    ) from e

from app.domain.faq import FaqEntry
from app.infrastructure.ollama_client import OllamaClient
from app.infrastructure.qdrant_client import QdrantClient

logger = logging.getLogger(__name__)


@dataclass
class IngestionResult:
    """Result of an ingestion operation."""

    total_entries: int = 0
    successful_entries: int = 0
    failed_entries: int = 0
    errors: list[str] = field(default_factory=list)

    def add_error(self, entry_id: str, error: str) -> None:
        """Record an error for a failed entry.

        Args:
            entry_id: ID of the FAQ entry that failed.
            error: Error message.
        """
        self.errors.append(f"Entry {entry_id}: {error}")
        self.failed_entries += 1

    @property
    def success(self) -> bool:
        """Check if ingestion was fully successful."""
        return self.failed_entries == 0

    def __str__(self) -> str:
        """Return a summary string."""
        summary = (
            f"Ingestion Result: {self.successful_entries}/{self.total_entries} "
            f"entries successfully ingested"
        )
        if self.failed_entries > 0:
            summary += f", {self.failed_entries} failed"
        return summary


class IngestionService:
    """Service for ingesting FAQ entries into Qdrant."""

    def __init__(
        self,
        ollama_client: OllamaClient,
        qdrant_client: QdrantClient,
    ) -> None:
        """Initialize the ingestion service.

        Args:
            ollama_client: Client for generating embeddings.
            qdrant_client: Client for storing vectors in Qdrant.
        """
        self.ollama = ollama_client
        self.qdrant = qdrant_client

    async def ingest_faq_entries(
        self,
        entries: Sequence[FaqEntry],
    ) -> IngestionResult:
        """Ingest FAQ entries into Qdrant.

        Args:
            entries: Sequence of FaqEntry objects to ingest.

        Returns:
            IngestionResult with success/failure counts and errors.
        """
        result = IngestionResult(total_entries=len(entries))

        if not entries:
            logger.warning("No FAQ entries to ingest")
            return result

        try:
            # Get embedding dimension for collection creation
            embedding_dim = await self.ollama.get_embedding_dimension()
            logger.info(f"Embedding dimension: {embedding_dim}")

            # Ensure collection exists with correct dimensions
            await self.ensure_collection_exists(embedding_dim)

            # Prepare points (embed and structure data)
            points = await self._prepare_qdrant_points(entries, result)

            if not points:
                logger.error("No valid points to upsert")
                return result

            # Upsert to Qdrant
            try:
                self.qdrant.upsert_points(points)
                result.successful_entries = len(points)
            except RuntimeError as e:
                logger.error(f"Upsert failed: {e}")
                result.add_error("batch", str(e))

        except RuntimeError as e:
            logger.error(f"Ingestion failed: {e}")
            result.add_error("setup", str(e))

        logger.info(str(result))
        return result

    async def ensure_collection_exists(self, embedding_dim: int) -> None:
        """Ensure Qdrant collection exists with correct vector dimensions.

        Args:
            embedding_dim: Expected vector dimension.

        Raises:
            RuntimeError: If collection verification/creation fails.
        """
        try:
            if self.qdrant.collection_exists():
                logger.info(
                    f"Collection '{self.qdrant.collection_name}' already exists"
                )
                # TODO: Verify dimensions match once collection info API is available
            else:
                logger.info(f"Creating collection '{self.qdrant.collection_name}'")
                self.qdrant.create_collection(
                    vector_dim=embedding_dim,
                )
        except RuntimeError as e:
            raise RuntimeError(f"Failed to ensure collection: {e}") from e

    async def _prepare_qdrant_points(
        self,
        entries: Sequence[FaqEntry],
        result: IngestionResult,
    ) -> list[PointStruct]:
        """Prepare Qdrant PointStruct objects from FAQ entries.

        Args:
            entries: Sequence of FaqEntry objects.
            result: IngestionResult object to record errors.

        Returns:
            List of PointStruct objects ready for upsert.
        """
        points: list[PointStruct] = []

        for idx, entry in enumerate(entries):
            try:
                # Embed the question
                vector = await self._embed_text(entry.question)

                # Create point with FAQ data in payload
                point = PointStruct(
                    id=self._entry_id_to_point_id(entry.id, idx),
                    vector=vector,
                    payload={
                        "faq_id": entry.id,
                        "question": entry.question,
                        "answer": entry.answer,
                        "tags": entry.tags,
                        "category": entry.category,
                        "source": entry.source,
                    },
                )
                points.append(point)

            except Exception as e:
                error_msg = f"Failed to embed: {str(e)}"
                logger.warning(f"Entry {entry.id}: {error_msg}")
                result.add_error(entry.id, error_msg)

        logger.info(f"Prepared {len(points)} points for ingestion")
        return points

    async def _embed_text(self, text: str) -> list[float]:
        """Generate embedding for text.

        Args:
            text: Text to embed.

        Returns:
            Embedding vector as list of floats.

        Raises:
            RuntimeError: If embedding fails.
        """
        try:
            return await self.ollama.embed_text(text)
        except RuntimeError as e:
            raise RuntimeError(f"Embedding failed for text: {e}") from e

    @staticmethod
    def _entry_id_to_point_id(entry_id: str, idx: int) -> int | str:
        """Convert FAQ entry ID to Qdrant point ID.

        Args:
            entry_id: FAQ entry ID (may be string).
            idx: Index of entry in batch.

        Returns:
            Point ID suitable for Qdrant (int or string).
        """
        # Try to use entry_id as integer if possible, fallback to string
        try:
            return int(entry_id)
        except ValueError:
            return entry_id
