"""Retrieval domain models and results."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from app.domain.faq import FAQEntry


@dataclass(frozen=True, slots=True)
class RetrievalResult:
    """Outcome of a single FAQ retrieval operation."""

    matched_entry: FAQEntry | None
    score: float
    top_k_results: Sequence[tuple[FAQEntry, float]]
    retrieved: bool
