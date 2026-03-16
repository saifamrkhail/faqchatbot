"""Small Ollama HTTP client wrapper."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Iterator, Mapping

import httpx

from app.config import AppSettings


class OllamaClientError(RuntimeError):
    """Raised when an Ollama request fails."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass(frozen=True, slots=True)
class OllamaGenerationResult:
    """Structured response returned from Ollama generation requests."""

    response: str
    thinking: str | None = None
    done_reason: str | None = None


@dataclass(slots=True)
class OllamaClient:
    """Minimal client for Ollama embeddings and generation."""

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

        result = self.generate_response(prompt)
        generated_text = result.response
        if not generated_text:
            raise OllamaClientError("Ollama returned an empty generation response")
        return generated_text

    def generate_response(
        self,
        prompt: str,
        *,
        think: bool | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> OllamaGenerationResult:
        """Generate a non-streaming response with optional thinking output."""

        normalized_prompt = prompt.strip()
        if not normalized_prompt:
            raise OllamaClientError("Generation prompt must not be empty")

        payload: dict[str, Any] = {
            "model": self.generate_model,
            "prompt": normalized_prompt,
            "stream": False,
            "options": {
                "temperature": (
                    self.generate_temperature
                    if temperature is None
                    else temperature
                ),
                "num_predict": (
                    self.generate_max_tokens
                    if max_tokens is None
                    else max_tokens
                ),
            },
        }
        if think is not None:
            payload["think"] = think

        response = self._request_json("POST", "/api/generate", payload)

        generated_text = response.get("response")
        thinking_text = response.get("thinking")
        done_reason = response.get("done_reason")

        if not isinstance(generated_text, str):
            raise OllamaClientError("Ollama returned an invalid generation response")
        if thinking_text is not None and not isinstance(thinking_text, str):
            raise OllamaClientError("Ollama returned an invalid thinking response")
        if done_reason is not None and not isinstance(done_reason, str):
            raise OllamaClientError("Ollama returned an invalid done reason")

        normalized_thinking = thinking_text.strip() or None if thinking_text else None
        normalized_done_reason = done_reason.strip() or None if done_reason else None

        return OllamaGenerationResult(
            response=generated_text.strip(),
            thinking=normalized_thinking,
            done_reason=normalized_done_reason,
        )

    def generate_streaming(
        self,
        prompt: str,
        *,
        think: bool | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> Iterator[str]:
        """Generate a streaming response, yielding text tokens as they arrive."""

        normalized_prompt = prompt.strip()
        if not normalized_prompt:
            raise OllamaClientError("Generation prompt must not be empty")

        payload: dict[str, Any] = {
            "model": self.generate_model,
            "prompt": normalized_prompt,
            "stream": True,
            "options": {
                "temperature": (
                    self.generate_temperature if temperature is None else temperature
                ),
                "num_predict": (
                    self.generate_max_tokens if max_tokens is None else max_tokens
                ),
            },
        }
        if think is not None:
            payload["think"] = think

        try:
            with self._client.stream("POST", "/api/generate", json=payload) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                    except ValueError:
                        continue
                    token = chunk.get("response", "")
                    if token:
                        yield token
                    if chunk.get("done", False):
                        break
        except httpx.HTTPStatusError as exc:
            raise OllamaClientError(
                _format_http_error("Ollama", exc.response),
                status_code=exc.response.status_code,
            ) from exc
        except httpx.TimeoutException as exc:
            raise OllamaClientError("Ollama request timed out") from exc
        except httpx.RequestError as exc:
            raise OllamaClientError(f"Could not reach Ollama: {exc}") from exc

    def _request_json(
        self,
        method: str,
        path: str,
        payload: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute JSON request and handle httpx exceptions."""

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
    if not isinstance(value, list) or not value:
        raise OllamaClientError(f"Ollama returned an invalid {field_name} vector")

    vector: list[float] = []
    for item in value:
        if not isinstance(item, (int, float)):
            raise OllamaClientError(f"Ollama returned a non-numeric {field_name} value")
        vector.append(float(item))
    return vector


def _format_http_error(service_name: str, response: httpx.Response) -> str:
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
