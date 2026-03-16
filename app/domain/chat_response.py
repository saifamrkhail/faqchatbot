"""Chat application domain models and responses."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ChatResponse:
    """Response to a user question passed through the chat pipeline.

    Combines retrieval and generation results into a single, UI-ready response.
    """

    question: str             # Original user question (normalized)
    answer: str               # Generated answer or fallback message
    is_fallback: bool         # True if no FAQ was retrieved
    confidence: float         # Retrieval score 0.0-1.0
    source_faq_id: str | None # FAQ entry used, None if fallback
    used_retrieval: bool      # True if answer came from FAQ
    thinking: str | None = None # Optional model thinking trace
