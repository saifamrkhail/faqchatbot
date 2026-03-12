"""Ollama client for embeddings and text generation."""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

import aiohttp

from app.config import AppSettings

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for Ollama API (embeddings and generation)."""

    def __init__(self, settings: AppSettings) -> None:
        """Initialize the Ollama client.

        Args:
            settings: Application settings containing Ollama base URL and model names.
        """
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.embedding_model = settings.ollama_embedding_model
        self.generation_model = settings.ollama_generate_model
        self._session: Optional[aiohttp.ClientSession] = None
        self._embedding_dim: Optional[int] = None

    async def close(self) -> None:
        """Close the HTTP session."""
        if self._session:
            await self._session.close()

    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create the HTTP session."""
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self._session

    async def embed_text(self, text: str, model: Optional[str] = None) -> list[float]:
        """Generate embedding for a text string.

        Args:
            text: Text to embed.
            model: Model name (defaults to embedding model from config).

        Returns:
            List of floats representing the embedding vector.

        Raises:
            RuntimeError: If Ollama is unavailable or request fails.
        """
        model = model or self.embedding_model

        if not text or not text.strip():
            raise ValueError("Text must not be empty")

        try:
            session = await self.get_session()
            url = f"{self.base_url}/api/embed"

            async with session.post(
                url,
                json={"model": model, "input": text},
                timeout=aiohttp.ClientTimeout(total=60),
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(
                        f"Ollama embed failed (status {response.status}): {error_text}"
                    )

                data = await response.json()
                embeddings = data.get("embeddings", [[]])[0]

                if not embeddings:
                    raise RuntimeError("Ollama returned empty embedding")

                # Cache embedding dimension
                if self._embedding_dim is None:
                    self._embedding_dim = len(embeddings)

                return embeddings

        except asyncio.TimeoutError as e:
            raise RuntimeError(f"Ollama request timeout: {e}") from e
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Ollama connection error: {e}") from e

    async def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings from the configured model.

        Returns:
            Number of dimensions in the embedding vector.

        Raises:
            RuntimeError: If dimension cannot be determined.
        """
        if self._embedding_dim is not None:
            return self._embedding_dim

        try:
            # Embed a simple test string to determine dimensions
            test_embedding = await self.embed_text("test")
            self._embedding_dim = len(test_embedding)
            return self._embedding_dim
        except RuntimeError as e:
            raise RuntimeError(f"Cannot determine embedding dimension: {e}") from e

    async def generate_text(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.3,
    ) -> str:
        """Generate text using Ollama.

        Args:
            prompt: Prompt for text generation.
            model: Model name (defaults to generation model from config).
            temperature: Sampling temperature (0.0 to 1.0).

        Returns:
            Generated text response.

        Raises:
            RuntimeError: If Ollama is unavailable or request fails.
        """
        model = model or self.generation_model

        if not prompt or not prompt.strip():
            raise ValueError("Prompt must not be empty")

        try:
            session = await self.get_session()
            url = f"{self.base_url}/api/generate"

            async with session.post(
                url,
                json={
                    "model": model,
                    "prompt": prompt,
                    "temperature": temperature,
                    "stream": False,
                },
                timeout=aiohttp.ClientTimeout(total=120),
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(
                        f"Ollama generate failed (status {response.status}): {error_text}"
                    )

                data = await response.json()
                return data.get("response", "").strip()

        except asyncio.TimeoutError as e:
            raise RuntimeError(f"Ollama request timeout: {e}") from e
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Ollama connection error: {e}") from e

    async def health_check(self) -> bool:
        """Check if Ollama is available and healthy.

        Returns:
            True if Ollama is healthy, False otherwise.
        """
        try:
            session = await self.get_session()
            url = f"{self.base_url}/"

            async with session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=5),
            ) as response:
                return response.status == 200
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")
            return False
