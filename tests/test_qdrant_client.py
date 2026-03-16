from __future__ import annotations

import pytest

from app.config import AppSettings
from app.infrastructure import (
    QdrantClient,
    QdrantClientError,
    QdrantPoint,
)


def test_qdrant_client_from_settings_uses_central_configuration() -> None:
    settings = AppSettings(
        qdrant_url="http://qdrant.local",
        qdrant_collection_name="faq_test",
        qdrant_timeout_seconds=18.0,
    )

    client = QdrantClient.from_settings(settings)

    assert client.base_url == "http://qdrant.local"
    assert client.collection_name == "faq_test"
    assert client.timeout_seconds == pytest.approx(18.0)


def test_ensure_collection_creates_missing_collection(monkeypatch: pytest.MonkeyPatch) -> None:
    client = QdrantClient(
        base_url="http://qdrant.local",
        collection_name="faq_entries",
        timeout_seconds=30.0,
    )
    created: dict[str, object] = {}

    def fake_get_collection_info(self) -> dict[str, object]:
        raise QdrantClientError("missing", status_code=404)

    def fake_create_collection(self, vector_size: int, *, distance: str) -> None:
        created["vector_size"] = vector_size
        created["distance"] = distance

    monkeypatch.setattr(QdrantClient, "get_collection_info", fake_get_collection_info)
    monkeypatch.setattr(QdrantClient, "create_collection", fake_create_collection)

    client.ensure_collection(3)

    assert created == {"vector_size": 3, "distance": "Cosine"}


def test_ensure_collection_rejects_mismatched_vector_size(monkeypatch: pytest.MonkeyPatch) -> None:
    client = QdrantClient(
        base_url="http://qdrant.local",
        collection_name="faq_entries",
        timeout_seconds=30.0,
    )

    monkeypatch.setattr(
        QdrantClient,
        "get_collection_info",
        lambda self: {
            "result": {
                "config": {"params": {"vectors": {"size": 5, "distance": "Cosine"}}}
            }
        },
    )

    with pytest.raises(QdrantClientError, match="vector size 5"):
        client.ensure_collection(3)


def test_ensure_collection_rejects_mismatched_distance(monkeypatch: pytest.MonkeyPatch) -> None:
    client = QdrantClient(
        base_url="http://qdrant.local",
        collection_name="faq_entries",
        timeout_seconds=30.0,
    )

    monkeypatch.setattr(
        QdrantClient,
        "get_collection_info",
        lambda self: {
            "result": {
                "config": {"params": {"vectors": {"size": 3, "distance": "Dot"}}}
            }
        },
    )

    with pytest.raises(QdrantClientError, match="distance Dot"):
        client.ensure_collection(3, distance="Cosine")


def test_upsert_points_sends_all_points(monkeypatch: pytest.MonkeyPatch) -> None:
    client = QdrantClient(
        base_url="http://qdrant.local",
        collection_name="faq_entries",
        timeout_seconds=30.0,
    )
    recorded: dict[str, object] = {}

    import httpx
    def fake_request(
        self, method: str, path: str, **kwargs: object
    ) -> httpx.Response:
        recorded["method"] = method
        recorded["path"] = path
        recorded["payload"] = kwargs.get("json")
        return httpx.Response(200, json={"status": "ok"}, request=httpx.Request(method, path))

    monkeypatch.setattr("httpx.Client.request", fake_request)

    point = QdrantPoint(id="faq-1", vector=(0.1, 0.2), payload={"question": "Hi"})
    upserted = client.upsert_points([point])

    assert upserted == 1
    assert recorded == {
        "method": "PUT",
        "path": "/collections/faq_entries/points?wait=true",
        "payload": {
            "points": [
                {
                    "id": "faq-1",
                    "vector": [0.1, 0.2],
                    "payload": {"question": "Hi"},
                }
            ]
        },
    }


def test_search_falls_back_to_legacy_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    client = QdrantClient(
        base_url="http://qdrant.local",
        collection_name="faq_entries",
        timeout_seconds=30.0,
    )
    paths: list[str] = []

    def fake_request(
        self, method: str, path: str, payload: dict[str, object]
    ) -> dict[str, object]:
        paths.append(path)
        if path.endswith("/points/query"):
            raise QdrantClientError("missing", status_code=404)
        return {
            "result": [
                {
                    "id": "faq-1",
                    "score": 0.91,
                    "payload": {"question": "Welche Dienstleistungen?"},
                }
            ]
        }

    monkeypatch.setattr(QdrantClient, "_request_json", fake_request)

    results = client.search([0.1, 0.2], limit=1)

    assert [result.id for result in results] == ["faq-1"]
    assert paths == [
        "/collections/faq_entries/points/query",
        "/collections/faq_entries/points/search",
    ]


def test_search_supports_query_endpoint_points_wrapper(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = QdrantClient(
        base_url="http://qdrant.local",
        collection_name="faq_entries",
        timeout_seconds=30.0,
    )

    def fake_request(
        self, method: str, path: str, payload: dict[str, object]
    ) -> dict[str, object]:
        assert path == "/collections/faq_entries/points/query"
        return {
            "result": {
                "points": [
                    {
                        "id": "faq-1",
                        "score": 0.91,
                        "payload": {"question": "Welche Dienstleistungen?"},
                    }
                ]
            }
        }

    monkeypatch.setattr(QdrantClient, "_request_json", fake_request)

    results = client.search([0.1, 0.2], limit=1)

    assert [result.id for result in results] == ["faq-1"]
    assert results[0].score == pytest.approx(0.91)


def test_search_supports_missing_payload_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    client = QdrantClient(
        base_url="http://qdrant.local",
        collection_name="faq_entries",
        timeout_seconds=30.0,
    )

    def fake_request(
        self, method: str, path: str, payload: dict[str, object]
    ) -> dict[str, object]:
        return {"result": [{"id": "faq-1", "score": 0.81, "payload": None}]}

    monkeypatch.setattr(QdrantClient, "_request_json", fake_request)

    results = client.search([0.1, 0.2], limit=1, with_payload=False)

    assert len(results) == 1
    assert results[0].payload is None
