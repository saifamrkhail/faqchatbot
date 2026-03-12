"""FAQ domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True, slots=True)
class FaqEntry:
    """Represents a single FAQ entry."""

    id: str
    question: str
    answer: str
    tags: list[str] = field(default_factory=list)
    category: Optional[str] = None
    source: Optional[str] = None

    def validate(self) -> None:
        """Validate FAQ entry data."""
        if not self.id or not self.id.strip():
            raise ValueError("FAQ id must not be empty")
        if not self.question or not self.question.strip():
            raise ValueError("FAQ question must not be empty")
        if not self.answer or not self.answer.strip():
            raise ValueError("FAQ answer must not be empty")
