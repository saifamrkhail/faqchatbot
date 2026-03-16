"""Repository for loading FAQ entries from JSON."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from app.config import AppSettings, resolve_project_path
from app.domain.faq import FAQEntry, FAQValidationError


class FAQRepositoryError(RuntimeError):
    """Raised when FAQ data cannot be loaded from disk."""


@dataclass(slots=True)
class FAQRepository:
    """Disk boundary that turns ``faq.json`` into validated domain objects."""

    data_path: Path

    @classmethod
    def from_settings(cls, settings: AppSettings) -> "FAQRepository":
        """Create a repository using the configured FAQ data path."""

        return cls(data_path=resolve_project_path(settings.faq_data_path))

    def list_entries(self) -> list[FAQEntry]:
        """Load, validate, and de-duplicate every configured FAQ entry."""

        payload = self._load_json()
        if not isinstance(payload, list):
            raise FAQRepositoryError("FAQ data file must contain a JSON array")

        entries: list[FAQEntry] = []
        seen_entry_ids: set[str] = set()
        for index, raw_entry in enumerate(payload, start=1):
            try:
                entry = FAQEntry.from_dict(raw_entry, record_index=index)
            except FAQValidationError as exc:
                raise FAQRepositoryError(str(exc)) from exc
            if entry.id in seen_entry_ids:
                # Duplicate ids would make retrieval and source attribution ambiguous.
                raise FAQRepositoryError(
                    f"FAQ record {index} uses duplicate id '{entry.id}'"
                )
            seen_entry_ids.add(entry.id)
            entries.append(entry)
        return entries

    def get_by_id(self, entry_id: str) -> FAQEntry | None:
        """Return one FAQ entry by id, or None if it does not exist."""

        normalized_id = entry_id.strip()
        if not normalized_id:
            raise FAQRepositoryError("FAQ entry id must not be empty")

        for entry in self.list_entries():
            if entry.id == normalized_id:
                return entry
        return None

    def _load_json(self) -> Any:
        """Read and parse the raw JSON payload while translating IO errors."""

        try:
            raw_text = self.data_path.read_text(encoding="utf-8")
        except FileNotFoundError as exc:
            raise FAQRepositoryError(
                f"FAQ data file not found: {self.data_path}"
            ) from exc
        except OSError as exc:
            raise FAQRepositoryError(
                f"FAQ data file could not be read: {self.data_path}"
            ) from exc

        try:
            return json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise FAQRepositoryError(
                f"FAQ data file contains invalid JSON: {self.data_path}"
            ) from exc
