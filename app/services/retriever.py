"""Semantic FAQ retrieval service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from app.config import AppSettings
from app.domain import FAQEntry
from app.domain.retrieval_result import RetrievalResult
from app.infrastructure import (
    OllamaClient,
    OllamaClientError,
    QdrantClient,
    QdrantClientError,
)


class RetrieverError(RuntimeError):
    """Raised when retrieval fails."""


@dataclass(slots=True)
class Retriever:
    """Semantic FAQ retrieval from vector store."""

    ollama_client: OllamaClient
    qdrant_client: QdrantClient
    top_k: int
    score_threshold: float

    @classmethod
    def from_settings(cls, settings: AppSettings) -> "Retriever":
        """Build a fully wired retriever from application settings."""

        return cls(
            ollama_client=OllamaClient.from_settings(settings),
            qdrant_client=QdrantClient.from_settings(settings),
            top_k=settings.top_k,
            score_threshold=settings.score_threshold,
        )

    def retrieve(self, question: str) -> RetrievalResult:
        """Find the best FAQ match for a user question.

        Returns RetrievalResult with matched_entry=None if below threshold.
        """

        try:
            normalized_question = question.strip()
            if not normalized_question:
                raise RetrieverError("Question must not be empty")

            vector = self._embed_question(normalized_question)
            search_results = self._search_vector_store(vector)
            result = self._evaluate_threshold(search_results)

            return result
        except OllamaClientError as exc:
            raise RetrieverError(f"Failed to embed question: {exc}") from exc
        except QdrantClientError as exc:
            raise RetrieverError(f"Failed to search FAQ database: {exc}") from exc

    def _embed_question(self, question: str) -> list[float]:
        """Embed a user question for vector similarity search."""

        return self.ollama_client.embed_text(question)

    def _search_vector_store(
        self, vector: Sequence[float]
    ) -> list[tuple[FAQEntry, float]]:
        """Search Qdrant for semantically similar FAQ entries."""

        raw_results = self.qdrant_client.search(
            vector=vector, limit=self.top_k, with_payload=True
        )

        results: list[tuple[FAQEntry, float]] = []
        for raw_result in raw_results:
            if raw_result.payload is None:
                continue

            try:
                entry = FAQEntry.from_dict(raw_result.payload)
                results.append((entry, raw_result.score))
            except Exception as exc:
                raise RetrieverError(
                    f"Failed to parse FAQ entry from search result: {exc}"
                ) from exc

        return results

    def _evaluate_threshold(
        self, results: list[tuple[FAQEntry, float]]
    ) -> RetrievalResult:
        """Evaluate search results against threshold.

        Returns matched_entry=None if no results or score below threshold.
        """

        if not results:
            return RetrievalResult(
                matched_entry=None,
                score=0.0,
                top_k_results=results,
                retrieved=False,
            )

        best_entry, best_score = results[0]

        return RetrievalResult(
            matched_entry=best_entry if best_score >= self.score_threshold else None,
            score=best_score,
            top_k_results=results,
            retrieved=best_score >= self.score_threshold,
        )
