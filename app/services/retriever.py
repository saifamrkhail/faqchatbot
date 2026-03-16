"""Semantic FAQ retrieval service."""

from __future__ import annotations

from dataclasses import dataclass
import logging
import re
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


logger = logging.getLogger(__name__)

_LEXICAL_STOPWORDS = {
    "a",
    "ab",
    "all",
    "am",
    "an",
    "and",
    "are",
    "auf",
    "aus",
    "beim",
    "bei",
    "bieten",
    "das",
    "dem",
    "den",
    "der",
    "des",
    "die",
    "do",
    "ein",
    "eine",
    "einem",
    "einen",
    "einer",
    "eines",
    "es",
    "fuer",
    "für",
    "habt",
    "haben",
    "help",
    "how",
    "ich",
    "ihr",
    "ihre",
    "ihren",
    "ihnen",
    "im",
    "in",
    "ist",
    "it",
    "kann",
    "können",
    "könnt",
    "mit",
    "my",
    "of",
    "or",
    "the",
    "to",
    "und",
    "ungefähr",
    "ungefaehr",
    "uns",
    "von",
    "was",
    "welche",
    "wie",
    "wir",
    "you",
    "zu",
    "zur",
}
_MAX_LEXICAL_BONUS = 0.18
_QUERY_REWRITE_MIN_LEXICAL_TERMS = 2
_QUERY_REWRITE_MIN_SUPPORT = 2
_QUERY_REWRITE_HIGH_CONFIDENCE_MARGIN = 0.12


@dataclass(frozen=True, slots=True)
class _RetrievalTrial:
    query: str
    result: RetrievalResult


@dataclass(slots=True)
class _RewriteCandidate:
    entry: FAQEntry
    best_result: RetrievalResult
    best_score: float
    seen_queries: set[str]


@dataclass(slots=True)
class Retriever:
    """Embed a question, search Qdrant, rerank, and optionally rewrite borderline queries."""

    ollama_client: OllamaClient
    qdrant_client: QdrantClient
    top_k: int
    score_threshold: float
    query_rewrite_enabled: bool = True
    query_rewrite_borderline_min_score: float = 0.35
    query_rewrite_max_variants: int = 3
    query_rewrite_temperature: float = 0.0
    query_rewrite_max_tokens: int = 96

    @classmethod
    def from_settings(cls, settings: AppSettings) -> "Retriever":
        """Build a fully wired retriever from application settings."""

        return cls(
            ollama_client=OllamaClient.from_settings(settings),
            qdrant_client=QdrantClient.from_settings(settings),
            top_k=settings.top_k,
            score_threshold=settings.score_threshold,
            query_rewrite_enabled=settings.query_rewrite_enabled,
            query_rewrite_borderline_min_score=(
                settings.query_rewrite_borderline_min_score
            ),
            query_rewrite_max_variants=settings.query_rewrite_max_variants,
            query_rewrite_temperature=settings.query_rewrite_temperature,
            query_rewrite_max_tokens=settings.query_rewrite_max_tokens,
        )

    def retrieve(self, question: str) -> RetrievalResult:
        """Find the best FAQ match for a user question."""

        try:
            normalized_question = question.strip()
            if not normalized_question:
                raise RetrieverError("Question must not be empty")
            primary_result = self._retrieve_once(normalized_question)
        except OllamaClientError as exc:
            raise RetrieverError(f"Failed to embed question: {exc}") from exc
        except QdrantClientError as exc:
            raise RetrieverError(f"Failed to search FAQ database: {exc}") from exc

        if not self._should_attempt_query_rewrite(normalized_question, primary_result):
            return primary_result

        return self._retrieve_with_query_rewrite(
            normalized_question,
            primary_result,
        )

    def _retrieve_once(self, question: str) -> RetrievalResult:
        """Run one retrieval pass before any optional query rewrites."""

        vector = self._embed_question(question)
        search_results = self._search_vector_store(vector)
        reranked_results = self._rerank_results(question, search_results)
        return self._evaluate_threshold(reranked_results)

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

    def _rerank_results(
        self,
        question: str,
        results: list[tuple[FAQEntry, float]],
    ) -> list[tuple[FAQEntry, float]]:
        """Blend semantic similarity with a capped lexical overlap bonus."""

        if not results:
            return results

        query_terms = _extract_lexical_terms(question)
        reranked: list[tuple[FAQEntry, float]] = []
        for entry, semantic_score in results:
            lexical_bonus = _compute_lexical_bonus(query_terms, entry)
            reranked.append((entry, min(1.0, semantic_score + lexical_bonus)))

        reranked.sort(key=lambda item: item[1], reverse=True)
        return reranked

    def _should_attempt_query_rewrite(
        self,
        question: str,
        result: RetrievalResult,
    ) -> bool:
        if not self.query_rewrite_enabled or result.retrieved:
            return False
        if not result.top_k_results:
            return False

        best_score = result.top_k_results[0][1]
        if best_score < self.query_rewrite_borderline_min_score:
            return False
        if best_score >= self.score_threshold:
            return False

        return len(_extract_lexical_terms(question)) >= _QUERY_REWRITE_MIN_LEXICAL_TERMS

    def _retrieve_with_query_rewrite(
        self,
        question: str,
        primary_result: RetrievalResult,
    ) -> RetrievalResult:
        try:
            rewrites = self._rewrite_question(question)
        except OllamaClientError as exc:
            logger.warning(
                "Borderline retrieval rewrite skipped because rewrite generation failed. "
                "Question: %r, Error: %s",
                question,
                exc,
            )
            return primary_result

        if not rewrites:
            return primary_result

        logger.info(
            "Borderline retrieval score %.3f for %r. Trying %d rewrite candidate(s).",
            primary_result.score,
            question,
            len(rewrites),
        )

        trials = [_RetrievalTrial(query=question, result=primary_result)]
        for rewrite in rewrites:
            try:
                trials.append(
                    _RetrievalTrial(
                        query=rewrite,
                        result=self._retrieve_once(rewrite),
                    )
                )
            except (OllamaClientError, QdrantClientError, RetrieverError) as exc:
                logger.warning(
                    "Query rewrite candidate failed and will be ignored. "
                    "Original question: %r, Rewrite: %r, Error: %s",
                    question,
                    rewrite,
                    exc,
                )

        promoted_result = self._select_rewrite_candidate(primary_result, trials)
        if promoted_result is None:
            return primary_result

        logger.info(
            "Query rewrite promoted retrieval for %r from %.3f to %.3f.",
            question,
            primary_result.score,
            promoted_result.score,
        )
        return promoted_result

    def _rewrite_question(self, question: str) -> list[str]:
        prompt = _build_query_rewrite_prompt(
            question,
            max_variants=self.query_rewrite_max_variants,
        )
        generation = self.ollama_client.generate_response(
            prompt,
            think=False,
            temperature=self.query_rewrite_temperature,
            max_tokens=self.query_rewrite_max_tokens,
        )
        return _parse_query_rewrites(
            question,
            generation.response,
            max_variants=self.query_rewrite_max_variants,
        )

    def _select_rewrite_candidate(
        self,
        primary_result: RetrievalResult,
        trials: list[_RetrievalTrial],
    ) -> RetrievalResult | None:
        primary_best_id = (
            primary_result.top_k_results[0][0].id if primary_result.top_k_results else None
        )
        candidates: dict[str, _RewriteCandidate] = {}

        for trial in trials:
            if not trial.result.top_k_results:
                continue

            entry, score = trial.result.top_k_results[0]
            candidate = candidates.get(entry.id)
            if candidate is None:
                candidates[entry.id] = _RewriteCandidate(
                    entry=entry,
                    best_result=trial.result,
                    best_score=score,
                    seen_queries={trial.query},
                )
                continue

            candidate.seen_queries.add(trial.query)
            if score > candidate.best_score:
                candidate.entry = entry
                candidate.best_result = trial.result
                candidate.best_score = score

        accepted_candidates = [
            candidate
            for candidate in candidates.values()
            if candidate.best_score >= self.score_threshold
            and (
                candidate.entry.id == primary_best_id
                or len(candidate.seen_queries) >= _QUERY_REWRITE_MIN_SUPPORT
                or candidate.best_score
                >= min(1.0, self.score_threshold + _QUERY_REWRITE_HIGH_CONFIDENCE_MARGIN)
            )
        ]
        if not accepted_candidates:
            return None

        accepted_candidates.sort(
            key=lambda candidate: (
                candidate.best_score,
                len(candidate.seen_queries),
                candidate.entry.id == primary_best_id,
            ),
            reverse=True,
        )
        return accepted_candidates[0].best_result

    def _evaluate_threshold(
        self, results: list[tuple[FAQEntry, float]]
    ) -> RetrievalResult:
        """Decide whether the top result is strong enough to trust."""

        if not results:
            return RetrievalResult(
                matched_entry=None,
                score=0.0,
                top_k_results=results,
                retrieved=False,
            )

        # Only the top hit decides whether generation may use FAQ context.
        best_entry, best_score = results[0]

        return RetrievalResult(
            matched_entry=best_entry if best_score >= self.score_threshold else None,
            score=best_score,
            top_k_results=results,
            retrieved=best_score >= self.score_threshold,
        )


def _compute_lexical_bonus(query_terms: set[str], entry: FAQEntry) -> float:
    """Reward direct term overlap without overwhelming the semantic score."""

    if not query_terms:
        return 0.0

    entry_terms = _extract_lexical_terms(
        " ".join(
            part
            for part in (
                entry.question,
                entry.answer,
                entry.category or "",
                " ".join(entry.tags),
            )
            if part
        )
    )
    overlap = query_terms & entry_terms
    if not overlap:
        return 0.0

    overlap_ratio = len(overlap) / len(query_terms)
    bonus = min(_MAX_LEXICAL_BONUS, overlap_ratio * _MAX_LEXICAL_BONUS)
    if any(term.isdigit() for term in overlap):
        bonus = min(_MAX_LEXICAL_BONUS, bonus + 0.03)
    return bonus


def _extract_lexical_terms(text: str) -> set[str]:
    """Extract coarse lexical terms used for reranking and rewrite gating."""

    normalized = text.casefold().replace("/", " ")
    return {
        term
        for term in re.findall(r"[A-Za-z0-9À-ÿ]{2,}", normalized)
        if term not in _LEXICAL_STOPWORDS
    }


def _build_query_rewrite_prompt(question: str, *, max_variants: int) -> str:
    """Build the prompt that asks the model for retrieval-friendly rewrites."""

    return (
        "Du formulierst Suchanfragen fuer einen FAQ-Retriever um.\n"
        "Ziel: dieselbe Kundenfrage mit alternativen Suchbegriffen auffindbar machen.\n\n"
        "Regeln:\n"
        f"- Erzeuge hoechstens {max_variants} kurze Umformulierungen.\n"
        "- Behalte die urspruengliche Bedeutung exakt bei.\n"
        "- Fuege keine neuen Fakten, Produkte oder Annahmen hinzu.\n"
        "- Antworte nur mit den Umformulierungen, jeweils eine pro Zeile, ohne Nummerierung.\n"
        "- Wenn keine sinnvolle Umformulierung moeglich ist, gib keine leere Floskel aus.\n\n"
        f"Kundenfrage: {question}\n\n"
        "Umformulierungen:"
    )


def _parse_query_rewrites(
    original_question: str,
    response: str,
    *,
    max_variants: int,
) -> list[str]:
    """Parse and deduplicate rewrite candidates from the model response."""

    normalized_original = _normalize_query_text(original_question)
    seen: set[str] = {normalized_original}
    rewrites: list[str] = []

    raw_lines = [line for line in response.splitlines() if line.strip()]
    if len(raw_lines) == 1 and ";" in raw_lines[0]:
        raw_lines = [part for part in raw_lines[0].split(";") if part.strip()]

    for raw_line in raw_lines:
        cleaned = re.sub(r"^\s*(?:[-*]|\d+[.)])\s*", "", raw_line).strip()
        cleaned = cleaned.strip("\"'` ")
        normalized = _normalize_query_text(cleaned)
        if not normalized:
            continue
        if normalized in seen:
            continue
        if normalized in {
            "umformulierungen",
            "keine",
            "keine umformulierung moeglich",
        }:
            continue
        seen.add(normalized)
        rewrites.append(cleaned)
        if len(rewrites) >= max_variants:
            break

    return rewrites


def _normalize_query_text(value: str) -> str:
    """Normalize rewrite candidates for stable equality checks."""

    return " ".join(value.casefold().split())
