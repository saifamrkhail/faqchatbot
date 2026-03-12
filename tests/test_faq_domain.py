from __future__ import annotations

import pytest

from app.domain import FAQEntry, FAQValidationError


def test_faq_entry_from_dict_validates_and_normalizes_fields() -> None:
    entry = FAQEntry.from_dict(
        {
            "id": " faq-1 ",
            "question": " Was ist neu? ",
            "answer": " Eintrag vorhanden. ",
            "tags": [" support ", "faq"],
            "category": " general ",
            "source": " fixture.json ",
        },
        record_index=1,
    )

    assert entry.id == "faq-1"
    assert entry.question == "Was ist neu?"
    assert entry.answer == "Eintrag vorhanden."
    assert entry.tags == ("support", "faq")
    assert entry.category == "general"
    assert entry.source == "fixture.json"
    assert entry.to_payload()["tags"] == ["support", "faq"]


def test_faq_entry_rejects_missing_required_fields() -> None:
    with pytest.raises(FAQValidationError, match="missing required field 'question'"):
        FAQEntry.from_dict({"id": "faq-1", "answer": "Hallo"}, record_index=2)


def test_faq_entry_rejects_invalid_tags() -> None:
    with pytest.raises(FAQValidationError, match="field 'tags'"):
        FAQEntry.from_dict(
            {
                "id": "faq-1",
                "question": "Frage",
                "answer": "Antwort",
                "tags": ["ok", ""],
            }
        )
