from __future__ import annotations

from app.services import IngestionResult, IngestionServiceError
from scripts.ingest import build_ingestion_message, main


def test_build_ingestion_message_contains_key_metrics() -> None:
    message = build_ingestion_message(10, 10, 768)

    assert "Ingested 10 FAQ entries" in message
    assert "upserted=10" in message
    assert "vector_size=768" in message


def test_ingest_main_returns_error_code_for_ingestion_failure(monkeypatch) -> None:
    class FakeLogger:
        def info(self, *args, **kwargs) -> None:
            return None

        def error(self, *args, **kwargs) -> None:
            return None

    class FakeService:
        def ingest(self) -> IngestionResult:
            raise IngestionServiceError("boom")

    monkeypatch.setattr("scripts.ingest.get_settings", lambda: object())
    monkeypatch.setattr("scripts.ingest.configure_logging", lambda settings: FakeLogger())
    monkeypatch.setattr("scripts.ingest.IngestionService.from_settings", lambda settings: FakeService())

    assert main() == 1


def test_ingest_main_returns_success_for_completed_ingestion(monkeypatch) -> None:
    class FakeLogger:
        def info(self, *args, **kwargs) -> None:
            return None

        def error(self, *args, **kwargs) -> None:
            return None

    class FakeService:
        def ingest(self) -> IngestionResult:
            return IngestionResult(
                processed_entries=10,
                upserted_points=10,
                vector_size=768,
                collection_name="faq_entries",
            )

    monkeypatch.setattr("scripts.ingest.get_settings", lambda: object())
    monkeypatch.setattr("scripts.ingest.configure_logging", lambda settings: FakeLogger())
    monkeypatch.setattr("scripts.ingest.IngestionService.from_settings", lambda settings: FakeService())

    assert main() == 0
