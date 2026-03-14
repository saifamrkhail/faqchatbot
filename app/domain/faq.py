"""FAQ domain models and validation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


class FAQValidationError(ValueError):
    """Raised when FAQ source data is invalid."""


@dataclass(frozen=True, slots=True)
class FAQEntry:
    """Validated FAQ entry consumed by the application."""

    id: str
    question: str
    answer: str
    tags: tuple[str, ...] = ()
    category: str | None = None
    source: str | None = None

    @classmethod
    def from_dict(
        cls,
        raw: Mapping[str, Any],
        *,
        record_index: int | None = None,
    ) -> "FAQEntry":
        """Build a validated FAQ entry from a raw mapping."""

        if not isinstance(raw, Mapping):
            raise FAQValidationError(f"{_record_label(record_index)} must be an object")

        entry_id = _require_string(raw, "id", record_index=record_index)
        question = _require_string(raw, "question", record_index=record_index)
        answer = _require_string(raw, "answer", record_index=record_index)
        tags = _normalize_tags(raw.get("tags"), record_index=record_index)
        category = _normalize_optional_string(
            raw.get("category"), "category", record_index=record_index
        )
        source = _normalize_optional_string(
            raw.get("source"), "source", record_index=record_index
        )
        return cls(
            id=entry_id,
            question=question,
            answer=answer,
            tags=tags,
            category=category,
            source=source,
        )

    def to_payload(self) -> dict[str, Any]:
        """Return a JSON-serializable payload for persistence layers."""

        payload: dict[str, Any] = {
            "id": self.id,
            "question": self.question,
            "answer": self.answer,
            "tags": list(self.tags),
        }
        if self.category is not None:
            payload["category"] = self.category
        if self.source is not None:
            payload["source"] = self.source
        return payload


def _require_string(
    raw: Mapping[str, Any],
    field_name: str,
    *,
    record_index: int | None,
) -> str:
    if field_name not in raw:
        raise FAQValidationError(
            f"{_record_label(record_index)} is missing required field '{field_name}'"
        )

    value = raw[field_name]
    if not isinstance(value, str):
        raise FAQValidationError(
            f"{_record_label(record_index)} field '{field_name}' must be a string"
        )

    stripped = value.strip()
    if not stripped:
        raise FAQValidationError(
            f"{_record_label(record_index)} field '{field_name}' must not be empty"
        )
    return stripped


def _normalize_optional_string(
    value: Any,
    field_name: str,
    *,
    record_index: int | None,
) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise FAQValidationError(
            f"{_record_label(record_index)} field '{field_name}' must be a string"
        )
    stripped = value.strip()
    if not stripped:
        raise FAQValidationError(
            f"{_record_label(record_index)} field '{field_name}' must not be empty"
        )
    return stripped


def _normalize_tags(value: Any, *, record_index: int | None) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise FAQValidationError(
            f"{_record_label(record_index)} field 'tags' must be a list of strings"
        )

    normalized_tags: list[str] = []
    for tag in value:
        if not isinstance(tag, str):
            raise FAQValidationError(
                f"{_record_label(record_index)} field 'tags' must contain only strings"
            )
        stripped = tag.strip()
        if not stripped:
            raise FAQValidationError(
                f"{_record_label(record_index)} field 'tags' must not contain empty values"
            )
        normalized_tags.append(stripped)
    return tuple(normalized_tags)


def _record_label(record_index: int | None) -> str:
    if record_index is None:
        return "FAQ record"
    return f"FAQ record {record_index}"
