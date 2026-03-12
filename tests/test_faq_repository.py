from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.config import AppSettings
from app.repositories import FAQRepository, FAQRepositoryError


def test_repository_loads_real_faq_dataset() -> None:
    repository = FAQRepository(Path("data/faq.json"))

    entries = repository.list_entries()

    assert len(entries) == 10
    assert entries[0].id == "faq-01-services-overview"
    assert repository.get_by_id("faq-10-pricing") is not None
    assert entries[0].source == "data/faq.txt"
    assert "Cloud-Lösungen" in entries[0].answer


def test_repository_rejects_invalid_json_array(tmp_path: Path) -> None:
    data_file = tmp_path / "faq.json"
    data_file.write_text(json.dumps({"items": []}), encoding="utf-8")

    repository = FAQRepository(data_file)

    with pytest.raises(FAQRepositoryError, match="JSON array"):
        repository.list_entries()


def test_repository_wraps_validation_errors(tmp_path: Path) -> None:
    data_file = tmp_path / "faq.json"
    data_file.write_text(json.dumps([{"id": "faq-1", "answer": "Antwort"}]), encoding="utf-8")

    repository = FAQRepository(data_file)

    with pytest.raises(FAQRepositoryError, match="missing required field 'question'"):
        repository.list_entries()


def test_repository_raises_for_missing_file(tmp_path: Path) -> None:
    repository = FAQRepository(tmp_path / "missing.json")

    with pytest.raises(FAQRepositoryError, match="not found"):
        repository.list_entries()


def test_repository_rejects_duplicate_ids(tmp_path: Path) -> None:
    data_file = tmp_path / "faq.json"
    data_file.write_text(
        json.dumps(
            [
                {"id": "faq-1", "question": "Frage 1", "answer": "Antwort 1"},
                {"id": "faq-1", "question": "Frage 2", "answer": "Antwort 2"},
            ]
        ),
        encoding="utf-8",
    )

    repository = FAQRepository(data_file)

    with pytest.raises(FAQRepositoryError, match="duplicate id 'faq-1'"):
        repository.list_entries()


def test_repository_from_settings_resolves_relative_paths_from_project_root(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)

    repository = FAQRepository.from_settings(AppSettings(faq_data_path="data/faq.json"))

    entries = repository.list_entries()

    assert len(entries) == 10
