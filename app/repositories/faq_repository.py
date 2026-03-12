"""FAQ repository for loading and managing FAQ entries."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Sequence

from app.domain.faq import FaqEntry

logger = logging.getLogger(__name__)


class FaqRepository:
    """Repository for loading FAQ entries from JSON files."""

    def __init__(self) -> None:
        """Initialize the FAQ repository."""

    def load_from_file(self, file_path: str | Path) -> list[FaqEntry]:
        """Load FAQ entries from a JSON file.

        Args:
            file_path: Path to the JSON file containing FAQ entries.

        Returns:
            List of validated FaqEntry objects.

        Raises:
            FileNotFoundError: If the FAQ file does not exist.
            ValueError: If the FAQ data is invalid or malformed.
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"FAQ file not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            raise ValueError("FAQ data must be a list of entries")

        entries: list[FaqEntry] = []
        for idx, item in enumerate(data):
            try:
                entry = self._parse_entry(item)
                entry.validate()
                entries.append(entry)
            except (TypeError, ValueError) as e:
                logger.warning(f"Failed to parse FAQ entry at index {idx}: {e}")
                raise ValueError(f"Invalid FAQ entry at index {idx}: {e}") from e

        logger.info(f"Loaded {len(entries)} FAQ entries from {path}")
        return entries

    @staticmethod
    def _parse_entry(data: dict) -> FaqEntry:
        """Parse a single FAQ entry from a dictionary.

        Args:
            data: Dictionary containing FAQ entry data.

        Returns:
            FaqEntry object.

        Raises:
            TypeError: If required fields are missing.
            ValueError: If field types are incorrect.
        """
        try:
            return FaqEntry(
                id=str(data["id"]),
                question=str(data["question"]),
                answer=str(data["answer"]),
                tags=data.get("tags", []) or [],
                category=data.get("category"),
                source=data.get("source"),
            )
        except KeyError as e:
            raise TypeError(f"Missing required field: {e}") from e
        except (TypeError, ValueError) as e:
            raise ValueError(f"Invalid field value: {e}") from e
