"""Small Ollama HTTP client wrapper."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from typing import Any, Mapping

import httpx

from app.config import AppSettings


class OllamaClientError(RuntimeError):
    """Raised when an Ollama request fails."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass(slots=True)
class OllamaClient:
    """Thin Ollama wrapper so higher layers never deal with raw HTTP shapes."""

    base_url: str
    generate_model: str
    embedding_model: str
    timeout_seconds: float
    generate_temperature: float
    generate_max_tokens: int
    _client: httpx.Client = field(init=False)

    def __post_init__(self) -> None:
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=self.timeout_seconds,
        )

    @classmethod
    def from_settings(cls, settings: AppSettings) -> "OllamaClient":
        """Create an Ollama client from centralized settings."""

        return cls(
            base_url=settings.ollama_base_url,
            generate_model=settings.ollama_generate_model,
            embedding_model=settings.ollama_embedding_model,
            timeout_seconds=settings.ollama_timeout_seconds,
            generate_temperature=settings.ollama_generate_temperature,
            generate_max_tokens=settings.ollama_generate_max_tokens,
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

        # Ollama has returned both ``embedding`` and ``embeddings`` payload shapes.
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
                "options": {
                    "temperature": self.generate_temperature,
                    "num_predict": self.generate_max_tokens,
                },
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
        """Execute one JSON request and translate transport failures."""

        try:
            response = self._client.request(
                method,
                path,
                json=payload,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise OllamaClientError(
                _format_http_error("Ollama", exc.response),
                status_code=exc.response.status_code,
            ) from exc
        except httpx.TimeoutException as exc:
            raise OllamaClientError("Ollama request timed out") from exc
        except httpx.RequestError as exc:
            raise OllamaClientError(f"Could not reach Ollama: {exc}") from exc

        try:
            parsed = response.json()
        except ValueError as exc:
            raise OllamaClientError("Ollama returned invalid JSON") from exc

        if not isinstance(parsed, dict):
            raise OllamaClientError("Ollama returned an unexpected response payload")
        return parsed

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()


def _normalize_vector(value: Any, field_name: str) -> list[float]:
    """Validate numeric vectors before the rest of the app consumes them."""

    if not isinstance(value, list) or not value:
        raise OllamaClientError(f"Ollama returned an invalid {field_name} vector")

    vector: list[float] = []
    for item in value:
        if not isinstance(item, (int, float)):
            raise OllamaClientError(f"Ollama returned a non-numeric {field_name} value")
        vector.append(float(item))
    return vector


def _format_http_error(service_name: str, response: httpx.Response) -> str:
    """Extract the most useful error detail from an HTTP response."""

    try:
        parsed = response.json()
    except ValueError:
        parsed = None

    detail = ""
    if isinstance(parsed, dict) and isinstance(parsed.get("error"), str):
        detail = parsed["error"].strip()
    elif response.text:
       detail = response.text.strip()

    if detail:
        return f"{service_name} request failed with status {response.status_code}: {detail}"

    return f"{service_name} request failed with status {response.status_code}"
