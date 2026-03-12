"""Qdrant vector database client."""

from __future__ import annotations

import logging
from typing import Any, Optional

try:
    from qdrant_client import QdrantClient as QdrantSDKClient
    from qdrant_client.models import (
        Distance,
        PointStruct,
        VectorParams,
        FieldCondition,
        MatchValue,
    )
except ImportError as e:
    raise ImportError(
        "qdrant-client not installed. Install with: pip install qdrant-client"
    ) from e

from app.config import AppSettings

logger = logging.getLogger(__name__)


class QdrantClient:
    """Client for Qdrant vector database."""

    def __init__(self, settings: AppSettings) -> None:
        """Initialize the Qdrant client.

        Args:
            settings: Application settings containing Qdrant URL and collection name.
        """
        self.url = settings.qdrant_url
        self.collection_name = settings.qdrant_collection_name
        self.client = QdrantSDKClient(url=self.url)

    def collection_exists(self, collection_name: Optional[str] = None) -> bool:
        """Check if a collection exists.

        Args:
            collection_name: Collection name (defaults to configured collection).

        Returns:
            True if collection exists, False otherwise.
        """
        name = collection_name or self.collection_name
        try:
            self.client.collection_info(name)
            return True
        except Exception as e:
            logger.debug(f"Collection {name} does not exist: {e}")
            return False

    def create_collection(
        self,
        vector_dim: int,
        collection_name: Optional[str] = None,
        distance_metric: str = "cosine",
    ) -> None:
        """Create a new collection.

        Args:
            vector_dim: Dimensionality of vectors in this collection.
            collection_name: Collection name (defaults to configured collection).
            distance_metric: Distance metric (cosine, euclidean, dot_product).

        Raises:
            RuntimeError: If collection creation fails.
        """
        name = collection_name or self.collection_name

        if self.collection_exists(name):
            logger.info(f"Collection {name} already exists")
            return

        try:
            distance = Distance.COSINE
            if distance_metric == "euclidean":
                distance = Distance.EUCLID
            elif distance_metric == "dot_product":
                distance = Distance.DOT

            self.client.recreate_collection(
                collection_name=name,
                vectors_config=VectorParams(size=vector_dim, distance=distance),
            )
            logger.info(f"Created collection {name} with vector dim {vector_dim}")
        except Exception as e:
            raise RuntimeError(f"Failed to create collection {name}: {e}") from e

    def upsert_points(
        self,
        points: list[PointStruct],
        collection_name: Optional[str] = None,
    ) -> None:
        """Upsert points into the collection.

        Args:
            points: List of PointStruct objects to upsert.
            collection_name: Collection name (defaults to configured collection).

        Raises:
            RuntimeError: If upsert fails.
        """
        name = collection_name or self.collection_name

        if not points:
            logger.warning("No points to upsert")
            return

        try:
            self.client.upsert(
                collection_name=name,
                points=points,
            )
            logger.info(f"Upserted {len(points)} points to {name}")
        except Exception as e:
            raise RuntimeError(f"Failed to upsert points into {name}: {e}") from e

    def search(
        self,
        vector: list[float],
        collection_name: Optional[str] = None,
        limit: int = 10,
        score_threshold: Optional[float] = None,
    ) -> list[dict[str, Any]]:
        """Search for similar vectors in the collection.

        Args:
            vector: Query vector.
            collection_name: Collection name (defaults to configured collection).
            limit: Maximum number of results to return.
            score_threshold: Minimum similarity score threshold.

        Returns:
            List of search results with id, score, and payload.

        Raises:
            RuntimeError: If search fails.
        """
        name = collection_name or self.collection_name

        try:
            results = self.client.search(
                collection_name=name,
                query_vector=vector,
                limit=limit,
                score_threshold=score_threshold,
            )

            return [
                {
                    "id": result.id,
                    "score": result.score,
                    "payload": result.payload,
                }
                for result in results
            ]
        except Exception as e:
            raise RuntimeError(f"Search failed in {name}: {e}") from e

    def get_point(
        self,
        point_id: int | str,
        collection_name: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        """Retrieve a specific point by ID.

        Args:
            point_id: ID of the point to retrieve.
            collection_name: Collection name (defaults to configured collection).

        Returns:
            Point data with payload, or None if not found.

        Raises:
            RuntimeError: If retrieval fails.
        """
        name = collection_name or self.collection_name

        try:
            point = self.client.retrieve(
                collection_name=name,
                ids=[point_id],
            )
            if point:
                return {
                    "id": point[0].id,
                    "payload": point[0].payload,
                }
            return None
        except Exception as e:
            logger.debug(f"Failed to get point {point_id} from {name}: {e}")
            return None

    def delete_collection(self, collection_name: Optional[str] = None) -> None:
        """Delete a collection.

        Args:
            collection_name: Collection name (defaults to configured collection).

        Raises:
            RuntimeError: If deletion fails.
        """
        name = collection_name or self.collection_name

        try:
            self.client.delete_collection(name)
            logger.info(f"Deleted collection {name}")
        except Exception as e:
            raise RuntimeError(f"Failed to delete collection {name}: {e}") from e

    def health_check(self) -> bool:
        """Check if Qdrant is available and healthy.

        Returns:
            True if Qdrant is healthy, False otherwise.
        """
        try:
            self.client.get_collections()
            return True
        except Exception as e:
            logger.warning(f"Qdrant health check failed: {e}")
            return False
