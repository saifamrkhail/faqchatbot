"""Small Ollama HTTP client wrapper."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Mapping
from urllib import error, request

from app.config import AppSettings


class OllamaClientError(RuntimeError):
    """Raised when an Ollama request fails."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass(slots=True)
class OllamaClient:
    """Minimal client for Ollama embeddings and generation."""

    base_url: str
    generate_model: str
    embedding_model: str
    timeout_seconds: float

    @classmethod
    def from_settings(cls, settings: AppSettings) -> "OllamaClient":
        """Create an Ollama client from centralized settings."""

        return cls(
            base_url=settings.ollama_base_url,
            generate_model=settings.ollama_generate_model,
            embedding_model=settings.ollama_embedding_model,
            timeout_seconds=settings.ollama_timeout_seconds,
        )

    def embed_text(self, text: str) -> list[float]:
        """Return one embedding vector for the given text."""

        normalized_text = text.strip()
        if not normalized_text:
            raise OllamaClientError("Embedding text must not be empty")

        response = self._request_json(
            "POST",
            "/api/embed",
            {"model": self.embedding_model, "input": normalized_text},
        )

        if "embeddings" in response:
            embeddings = response["embeddings"]
            if not isinstance(embeddings, list) or not embeddings:
                raise OllamaClientError("Ollama returned an invalid embeddings payload")
            vector = embeddings[0]
        else:
            vector = response.get("embedding")

        return _normalize_vector(vector, "embedding")

    def generate(self, prompt: str) -> str:
        """Generate a non-streaming answer for the given prompt."""

        normalized_prompt = prompt.strip()
        if not normalized_prompt:
            raise OllamaClientError("Generation prompt must not be empty")

        response = self._request_json(
            "POST",
            "/api/generate",
            {
                "model": self.generate_model,
                "prompt": normalized_prompt,
                "stream": False,
            },
        )
        generated_text = response.get("response")
        if not isinstance(generated_text, str) or not generated_text.strip():
            raise OllamaClientError("Ollama returned an empty generation response")
        return generated_text.strip()

    def _request_json(
        self,
        method: str,
        path: str,
        payload: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        body = None
        headers = {"Accept": "application/json"}
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        http_request = request.Request(
            url=f"{self.base_url.rstrip('/')}/{path.lstrip('/')}",
            data=body,
            headers=headers,
            method=method,
        )

        try:
            with request.urlopen(http_request, timeout=self.timeout_seconds) as response:
                raw_response = response.read().decode("utf-8")
        except error.HTTPError as exc:
            raise OllamaClientError(
                _format_http_error("Ollama", exc),
                status_code=exc.code,
            ) from exc
        except error.URLError as exc:
            raise OllamaClientError(f"Could not reach Ollama: {exc.reason}") from exc
        except TimeoutError as exc:
            raise OllamaClientError("Ollama request timed out") from exc

        try:
            parsed = json.loads(raw_response)
        except json.JSONDecodeError as exc:
            raise OllamaClientError("Ollama returned invalid JSON") from exc

        if not isinstance(parsed, dict):
            raise OllamaClientError("Ollama returned an unexpected response payload")
        return parsed


def _normalize_vector(value: Any, field_name: str) -> list[float]:
    if not isinstance(value, list) or not value:
        raise OllamaClientError(f"Ollama returned an invalid {field_name} vector")

    vector: list[float] = []
    for item in value:
        if not isinstance(item, (int, float)):
            raise OllamaClientError(f"Ollama returned a non-numeric {field_name} value")
        vector.append(float(item))
    return vector


def _format_http_error(service_name: str, exc: error.HTTPError) -> str:
    try:
        body = exc.read().decode("utf-8")
    except Exception:
        body = ""

    detail = body.strip()
    if detail:
        try:
            parsed = json.loads(detail)
        except json.JSONDecodeError:
            pass
        else:
            if isinstance(parsed, dict) and isinstance(parsed.get("error"), str):
                detail = parsed["error"].strip()
        return f"{service_name} request failed with status {exc.code}: {detail}"

    return f"{service_name} request failed with status {exc.code}"
