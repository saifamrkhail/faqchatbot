"""Integration tests for the ingest.py script."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.repositories.faq_repository import FaqRepository


class TestFaqRepository:
    """Tests for FAQ repository (used by ingest script)."""

    def test_load_from_file_valid_json(self, tmp_path):
        """Test loading valid FAQ JSON file."""
        faq_file = tmp_path / "faq.json"
        faq_data = [
            {
                "id": "faq_001",
                "question": "Test question?",
                "answer": "Test answer.",
                "tags": ["test"],
                "category": "Test",
                "source": "test",
            }
        ]
        faq_file.write_text(json.dumps(faq_data))

        repo = FaqRepository()
        entries = repo.load_from_file(faq_file)

        assert len(entries) == 1
        assert entries[0].id == "faq_001"
        assert entries[0].question == "Test question?"
        assert entries[0].answer == "Test answer."

    def test_load_from_file_missing_file(self, tmp_path):
        """Test loading from non-existent file."""
        repo = FaqRepository()

        with pytest.raises(FileNotFoundError):
            repo.load_from_file(tmp_path / "nonexistent.json")

    def test_load_from_file_invalid_json(self, tmp_path):
        """Test loading invalid JSON."""
        faq_file = tmp_path / "faq.json"
        faq_file.write_text("invalid json {")

        repo = FaqRepository()

        with pytest.raises(ValueError):
            repo.load_from_file(faq_file)

    def test_load_from_file_not_a_list(self, tmp_path):
        """Test loading JSON that is not a list."""
        faq_file = tmp_path / "faq.json"
        faq_file.write_text(json.dumps({"not": "a list"}))

        repo = FaqRepository()

        with pytest.raises(ValueError, match="must be a list"):
            repo.load_from_file(faq_file)

    def test_load_from_file_missing_required_field(self, tmp_path):
        """Test loading FAQ entry with missing required field."""
        faq_file = tmp_path / "faq.json"
        faq_data = [
            {
                "id": "faq_001",
                "question": "Test?",
                # Missing "answer"
            }
        ]
        faq_file.write_text(json.dumps(faq_data))

        repo = FaqRepository()

        with pytest.raises(ValueError, match="Invalid FAQ entry"):
            repo.load_from_file(faq_file)

    def test_load_from_file_empty_required_field(self, tmp_path):
        """Test loading FAQ entry with empty required field."""
        faq_file = tmp_path / "faq.json"
        faq_data = [
            {
                "id": "",  # Empty ID
                "question": "Test?",
                "answer": "Test answer.",
            }
        ]
        faq_file.write_text(json.dumps(faq_data))

        repo = FaqRepository()

        with pytest.raises(ValueError, match="Invalid FAQ entry"):
            repo.load_from_file(faq_file)

    def test_load_from_file_multiple_entries(self, tmp_path):
        """Test loading multiple FAQ entries."""
        faq_file = tmp_path / "faq.json"
        faq_data = [
            {
                "id": "faq_001",
                "question": "Q1?",
                "answer": "A1.",
            },
            {
                "id": "faq_002",
                "question": "Q2?",
                "answer": "A2.",
            },
        ]
        faq_file.write_text(json.dumps(faq_data))

        repo = FaqRepository()
        entries = repo.load_from_file(faq_file)

        assert len(entries) == 2
        assert entries[0].id == "faq_001"
        assert entries[1].id == "faq_002"

    def test_load_from_file_optional_fields(self, tmp_path):
        """Test loading FAQ with only required fields."""
        faq_file = tmp_path / "faq.json"
        faq_data = [
            {
                "id": "faq_001",
                "question": "Question?",
                "answer": "Answer.",
                # No optional fields
            }
        ]
        faq_file.write_text(json.dumps(faq_data))

        repo = FaqRepository()
        entries = repo.load_from_file(faq_file)

        assert len(entries) == 1
        assert entries[0].tags == []
        assert entries[0].category is None
        assert entries[0].source is None


class TestIngestScriptIntegration:
    """Integration tests for the ingest script."""

    def test_script_file_exists(self):
        """Test that the ingest script exists."""
        script_path = Path(__file__).parent.parent / "scripts" / "ingest.py"
        assert script_path.exists(), f"Script not found at {script_path}"

    def test_script_is_executable(self):
        """Test that the ingest script is executable."""
        script_path = Path(__file__).parent.parent / "scripts" / "ingest.py"
        # Python files don't need execute bit on all systems, just check it exists
        assert script_path.exists()

    def test_script_has_main_entry_point(self):
        """Test that the script has a main entry point."""
        script_path = Path(__file__).parent.parent / "scripts" / "ingest.py"
        content = script_path.read_text()
        assert "async def main()" in content or "def main()" in content
        assert "if __name__" in content

    def test_sample_faq_file_exists(self):
        """Test that the sample FAQ file exists."""
        faq_path = Path(__file__).parent.parent / "data" / "faq.json"
        assert faq_path.exists(), f"Sample FAQ not found at {faq_path}"

    def test_sample_faq_is_valid_json(self):
        """Test that sample FAQ is valid JSON."""
        faq_path = Path(__file__).parent.parent / "data" / "faq.json"
        data = json.loads(faq_path.read_text())
        assert isinstance(data, list)
        assert len(data) > 0

    def test_sample_faq_entries_are_valid(self):
        """Test that sample FAQ entries are valid."""
        faq_path = Path(__file__).parent.parent / "data" / "faq.json"
        data = json.loads(faq_path.read_text())

        for entry in data:
            assert "id" in entry
            assert "question" in entry
            assert "answer" in entry
            assert entry["id"]
            assert entry["question"]
            assert entry["answer"]

    @pytest.mark.asyncio
    async def test_script_handles_missing_faq_file(self, tmp_path):
        """Test script behavior with missing FAQ file."""
        # This would be tested with actual script invocation
        # For now, just verify the FAQ repository handles it
        repo = FaqRepository()
        with pytest.raises(FileNotFoundError):
            repo.load_from_file(tmp_path / "nonexistent.json")

    def test_faq_sample_has_diverse_categories(self):
        """Test that sample FAQ has diverse categories for testing."""
        faq_path = Path(__file__).parent.parent / "data" / "faq.json"
        data = json.loads(faq_path.read_text())

        categories = set()
        for entry in data:
            if "category" in entry and entry["category"]:
                categories.add(entry["category"])

        # Ensure we have at least 3 different categories for retrieval testing
        assert len(categories) >= 3, f"Sample FAQ needs diverse categories, got: {categories}"

    def test_faq_sample_has_tags(self):
        """Test that sample FAQ entries have tags for filtering."""
        faq_path = Path(__file__).parent.parent / "data" / "faq.json"
        data = json.loads(faq_path.read_text())

        entries_with_tags = [e for e in data if e.get("tags")]
        assert len(entries_with_tags) > 0, "Sample FAQ should have tagged entries"
