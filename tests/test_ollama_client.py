from __future__ import annotations

from urllib import error

import pytest

from app.config import AppSettings
from app.infrastructure import OllamaClient, OllamaClientError


def test_ollama_client_from_settings_uses_central_configuration() -> None:
    settings = AppSettings(
        ollama_base_url="http://ollama.local",
        ollama_generate_model="llama-test",
        ollama_embedding_model="embed-test",
        ollama_timeout_seconds=12.5,
    )

    client = OllamaClient.from_settings(settings)

    assert client.base_url == "http://ollama.local"
    assert client.generate_model == "llama-test"
    assert client.embedding_model == "embed-test"
    assert client.timeout_seconds == pytest.approx(12.5)


def test_embed_text_builds_expected_request_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    client = OllamaClient(
        base_url="http://ollama.local",
        generate_model="gen",
        embedding_model="embed",
        timeout_seconds=30.0,
    )
    recorded: dict[str, object] = {}

    def fake_request(
        self, method: str, path: str, payload: dict[str, object]
    ) -> dict[str, object]:
        recorded["method"] = method
        recorded["path"] = path
        recorded["payload"] = payload
        return {"embeddings": [[0.1, 0.2, 0.3]]}

    monkeypatch.setattr(OllamaClient, "_request_json", fake_request)

    vector = client.embed_text(" Hallo ")

    assert vector == [0.1, 0.2, 0.3]
    assert recorded == {
        "method": "POST",
        "path": "/api/embed",
        "payload": {"model": "embed", "input": "Hallo"},
    }


def test_generate_builds_expected_request_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    client = OllamaClient(
        base_url="http://ollama.local",
        generate_model="gen",
        embedding_model="embed",
        timeout_seconds=30.0,
    )
    recorded: dict[str, object] = {}

    def fake_request(
        self, method: str, path: str, payload: dict[str, object]
    ) -> dict[str, object]:
        recorded["method"] = method
        recorded["path"] = path
        recorded["payload"] = payload
        return {"response": " Kurze Antwort. "}

    monkeypatch.setattr(OllamaClient, "_request_json", fake_request)

    response = client.generate(" Bitte antworten ")

    assert response == "Kurze Antwort."
    assert recorded == {
        "method": "POST",
        "path": "/api/generate",
        "payload": {"model": "gen", "prompt": "Bitte antworten", "stream": False},
    }


def test_request_json_wraps_transport_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    client = OllamaClient(
        base_url="http://ollama.local",
        generate_model="gen",
        embedding_model="embed",
        timeout_seconds=30.0,
    )

    def raise_url_error(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise error.URLError("connection refused")

    monkeypatch.setattr("urllib.request.urlopen", raise_url_error)

    with pytest.raises(OllamaClientError, match="Could not reach Ollama"):
        client._request_json("GET", "/api/version")
