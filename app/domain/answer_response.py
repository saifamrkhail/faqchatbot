"""Answer generation domain models and responses."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AnswerResponse:
    """Result of answer generation from a question."""

    answer: str | None
    confidence: float
    source_faq_id: str | None
    is_fallback: bool
    used_retrieval: bool
