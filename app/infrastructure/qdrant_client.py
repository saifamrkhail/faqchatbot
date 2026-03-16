"""Small Qdrant HTTP client wrapper."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from typing import Any, Mapping, Sequence

import httpx

from app.config import AppSettings

DEFAULT_QDRANT_DISTANCE = "Cosine"


class QdrantClientError(RuntimeError):
    """Raised when a Qdrant request fails."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass(frozen=True, slots=True)
class QdrantPoint:
    """One Qdrant point for upsert operations."""

    id: str
    vector: tuple[float, ...]
    payload: dict[str, Any]

    def to_request_object(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "vector": list(self.vector),
            "payload": self.payload,
        }


@dataclass(frozen=True, slots=True)
class QdrantSearchResult:
    """One search result returned from Qdrant."""

    id: str
    score: float
    payload: dict[str, Any] | None


@dataclass(frozen=True, slots=True)
class QdrantCollectionConfig:
    """Collection vector configuration relevant for compatibility checks."""

    vector_size: int
    distance: str


@dataclass(slots=True)
class QdrantClient:
    """Thin Qdrant wrapper for collection checks, upserts, and similarity search."""

    base_url: str
    collection_name: str
    timeout_seconds: float
    _client: httpx.Client = field(init=False)

    def __post_init__(self) -> None:
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=self.timeout_seconds,
        )

    @classmethod
    def from_settings(cls, settings: AppSettings) -> "QdrantClient":
        """Create a Qdrant client from centralized settings."""

        return cls(
            base_url=settings.qdrant_url,
            collection_name=settings.qdrant_collection_name,
            timeout_seconds=settings.qdrant_timeout_seconds,
        )

    def ensure_collection(
        self,
        vector_size: int,
        *,
        distance: str = DEFAULT_QDRANT_DISTANCE,
    ) -> None:
        """Create the collection if needed, otherwise verify compatibility."""

        if vector_size < 1:
            raise QdrantClientError("Vector size must be >= 1")

        try:
            collection_info = self.get_collection_info()
        except QdrantClientError as exc:
            if exc.status_code != 404:
                raise
            self.create_collection(vector_size, distance=distance)
            return

        existing_config = _extract_vector_config(collection_info)
        if existing_config.vector_size != vector_size:
            raise QdrantClientError(
                "Configured Qdrant collection has vector size "
                f"{existing_config.vector_size}, expected {vector_size}"
            )
        if existing_config.distance.casefold() != distance.casefold():
            raise QdrantClientError(
                "Configured Qdrant collection uses distance "
                f"{existing_config.distance}, expected {distance}"
            )

    def get_collection_info(self) -> dict[str, Any]:
        """Return raw collection information from Qdrant."""

        return self._request_json("GET", f"/collections/{self.collection_name}")

    def create_collection(
        self,
        vector_size: int,
        *,
        distance: str = DEFAULT_QDRANT_DISTANCE,
    ) -> None:
        """Create a Qdrant collection for FAQ vectors."""

        self._request_json(
            "PUT",
            f"/collections/{self.collection_name}",
            {"vectors": {"size": vector_size, "distance": distance}},
        )

    def upsert_points(self, points: Sequence[QdrantPoint]) -> int:
        """Insert or update points in the configured collection."""

        if not points:
            return 0

        payload = {"points": [point.to_request_object() for point in points]}
        self._request_json(
            "PUT",
            f"/collections/{self.collection_name}/points?wait=true",
            payload,
        )
        return len(points)

    def search(
        self,
        vector: Sequence[float],
        *,
        limit: int,
        with_payload: bool = True,
    ) -> list[QdrantSearchResult]:
        """Search the configured collection for nearest neighbours."""

        if limit < 1:
            raise QdrantClientError("Search limit must be >= 1")

        query_vector = [float(item) for item in vector]
        if not query_vector:
            raise QdrantClientError("Search vector must not be empty")

        try:
            response = self._request_json(
                "POST",
                f"/collections/{self.collection_name}/points/query",
                {
                    "query": query_vector,
                    "limit": limit,
                    "with_payload": with_payload,
                },
            )
        except QdrantClientError as exc:
            if exc.status_code != 404:
                raise
            # Older Qdrant versions expose ``/points/search`` instead of ``/points/query``.
            response = self._request_json(
                "POST",
                f"/collections/{self.collection_name}/points/search",
                {
                    "vector": query_vector,
                    "limit": limit,
                    "with_payload": with_payload,
                },
            )

        raw_results = response.get("result")
        if not isinstance(raw_results, list):
            raise QdrantClientError("Qdrant returned an invalid search response")

        results: list[QdrantSearchResult] = []
        for raw_result in raw_results:
            if not isinstance(raw_result, Mapping):
                raise QdrantClientError("Qdrant returned an invalid search result")
            point_id = raw_result.get("id")
            score = raw_result.get("score")
            payload = raw_result.get("payload")
            if not isinstance(point_id, (str, int)):
                raise QdrantClientError("Qdrant search result is missing an id")
            if not isinstance(score, (int, float)):
                raise QdrantClientError("Qdrant search result is missing a score")
            if payload is not None and not isinstance(payload, dict):
                raise QdrantClientError("Qdrant search payload must be an object")
            results.append(
                QdrantSearchResult(
                    id=str(point_id),
                    score=float(score),
                    payload=payload,
                )
            )
        return results

    def _request_json(
        self,
        method: str,
        path: str,
        payload: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute one JSON request and translate transport failures."""
        try:
            response = self._client.request(
                method,
                path,
                json=payload,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise QdrantClientError(
                _format_http_error("Qdrant", exc.response),
                status_code=exc.response.status_code,
            ) from exc
        except httpx.TimeoutException as exc:
            raise QdrantClientError("Qdrant request timed out") from exc
        except httpx.RequestError as exc:
            raise QdrantClientError(f"Could not reach Qdrant: {exc}") from exc

        try:
            parsed = response.json()
        except ValueError as exc:
            raise QdrantClientError("Qdrant returned invalid JSON") from exc

        if not isinstance(parsed, dict):
            raise QdrantClientError("Qdrant returned an unexpected response payload")
        return parsed

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()


def _extract_vector_config(collection_info: Mapping[str, Any]) -> QdrantCollectionConfig:
    """Read vector size and distance from both named and unnamed Qdrant configs."""

    result = collection_info.get("result")
    if not isinstance(result, Mapping):
        raise QdrantClientError("Qdrant collection response is missing 'result'")

    config = result.get("config")
    if not isinstance(config, Mapping):
        raise QdrantClientError("Qdrant collection response is missing 'config'")

    params = config.get("params")
    if not isinstance(params, Mapping):
        raise QdrantClientError("Qdrant collection response is missing 'params'")

    vectors = params.get("vectors")
    if not isinstance(vectors, Mapping):
        raise QdrantClientError("Qdrant collection response is missing 'vectors'")

    vector_config = vectors
    size = vector_config.get("size")
    distance = vector_config.get("distance")
    if not isinstance(size, int) or not isinstance(distance, str):
        # Qdrant may also nest config under a single named vector key.
        if len(vectors) == 1:
            vector_config = next(iter(vectors.values()))
            if not isinstance(vector_config, Mapping):
                raise QdrantClientError("Qdrant collection vector config is invalid")
            size = vector_config.get("size")
            distance = vector_config.get("distance")

    if not isinstance(size, int):
        raise QdrantClientError("Qdrant collection response is missing vector size")
    if not isinstance(distance, str) or not distance.strip():
        raise QdrantClientError("Qdrant collection response is missing vector distance")
    return QdrantCollectionConfig(vector_size=size, distance=distance.strip())


def _format_http_error(service_name: str, response: httpx.Response) -> str:
    """Extract the most useful error detail from an HTTP response."""

    try:
        parsed = response.json()
    except ValueError:
        parsed = None

    detail = ""
    if isinstance(parsed, dict):
        status = parsed.get("status")
        if isinstance(status, Mapping) and isinstance(status.get("error"), str):
            detail = status["error"].strip()
        elif isinstance(parsed.get("error"), str):
            detail = parsed["error"].strip()
    elif response.text:
       detail = response.text.strip()

    if detail:
        return f"{service_name} request failed with status {response.status_code}: {detail}"

    return f"{service_name} request failed with status {response.status_code}"
