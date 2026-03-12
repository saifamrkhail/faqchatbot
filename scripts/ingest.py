"""Standalone FAQ ingestion entrypoint."""

from __future__ import annotations

import sys

from app.config import SettingsError, get_settings
from app.logging import configure_logging
from app.services import IngestionService, IngestionServiceError


def build_ingestion_message(processed_entries: int, upserted_points: int, vector_size: int) -> str:
    """Return a compact ingestion status line."""

    return (
        f"Ingested {processed_entries} FAQ entries | "
        f"upserted={upserted_points} | "
        f"vector_size={vector_size}"
    )


def main() -> int:
    """Run the standalone FAQ ingestion flow."""

    try:
        settings = get_settings()
    except SettingsError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1

    logger = configure_logging(settings)
    service = IngestionService.from_settings(settings)

    try:
        result = service.ingest()
    except IngestionServiceError as exc:
        logger.error("FAQ ingestion failed")
        print(f"Ingestion error: {exc}", file=sys.stderr)
        return 1

    logger.info(
        "FAQ ingestion completed",
        extra={
            "processed_entries": result.processed_entries,
            "upserted_points": result.upserted_points,
            "vector_size": result.vector_size,
            "collection_name": result.collection_name,
        },
    )
    print(
        build_ingestion_message(
            result.processed_entries,
            result.upserted_points,
            result.vector_size,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
