#!/usr/bin/env python
"""Standalone ingestion script for loading FAQ data into Qdrant."""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import get_settings
from app.logging import setup_logging
from app.domain.faq import FaqEntry
from app.repositories.faq_repository import FaqRepository
from app.infrastructure.ollama_client import OllamaClient
from app.infrastructure.qdrant_client import QdrantClient
from app.services.ingestion_service import IngestionService

logger = logging.getLogger(__name__)


async def main() -> int:
    """Main entry point for the ingestion script.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    parser = argparse.ArgumentParser(
        description="Ingest FAQ data into Qdrant vector database"
    )
    parser.add_argument(
        "--faq-file",
        type=str,
        default="data/faq.json",
        help="Path to FAQ JSON file (default: data/faq.json)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default=None,
        help="Override log level (DEBUG, INFO, WARNING, ERROR)",
    )

    args = parser.parse_args()

    # Load configuration
    try:
        settings = get_settings()
    except Exception as e:
        print(f"Failed to load settings: {e}", file=sys.stderr)
        return 1

    # Setup logging
    log_level = args.log_level or ("DEBUG" if args.verbose else settings.log_level)
    setup_logging(log_level=log_level)

    logger.info("FAQ Ingestion Script Started")
    logger.info(f"FAQ file: {args.faq_file}")
    logger.info(f"Ollama URL: {settings.ollama_base_url}")
    logger.info(f"Qdrant URL: {settings.qdrant_url}")
    logger.info(f"Collection: {settings.qdrant_collection_name}")

    try:
        # Load FAQ data
        logger.info("Loading FAQ entries...")
        faq_repo = FaqRepository()
        faq_entries = faq_repo.load_from_file(args.faq_file)
        logger.info(f"Loaded {len(faq_entries)} FAQ entries")

        if not faq_entries:
            logger.warning("No FAQ entries to ingest")
            return 0

        # Create service clients
        logger.info("Connecting to Ollama and Qdrant...")
        ollama = OllamaClient(settings)
        qdrant = QdrantClient(settings)

        # Health checks
        logger.info("Performing health checks...")
        ollama_healthy = await ollama.health_check()
        qdrant_healthy = qdrant.health_check()

        if not ollama_healthy:
            logger.error(f"Ollama is not healthy at {settings.ollama_base_url}")
            return 1

        if not qdrant_healthy:
            logger.error(f"Qdrant is not healthy at {settings.qdrant_url}")
            return 1

        logger.info("All services healthy")

        # Run ingestion
        logger.info("Starting FAQ ingestion...")
        ingestion_service = IngestionService(ollama, qdrant)
        result = await ingestion_service.ingest_faq_entries(faq_entries)

        # Print results
        print("")  # blank line for readability
        print("=" * 70)
        print(str(result))
        print("=" * 70)

        if result.errors:
            print("\nErrors encountered:")
            for error in result.errors:
                print(f"  - {error}")

        await ollama.close()

        if result.success:
            logger.info("Ingestion completed successfully")
            print("\n✓ Ingestion completed successfully")
            return 0
        else:
            logger.warning(f"Ingestion completed with {result.failed_entries} errors")
            print(f"\n✗ Ingestion completed with {result.failed_entries} errors")
            return 1

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 1

    except ValueError as e:
        logger.error(f"Invalid FAQ data: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 1

    except RuntimeError as e:
        logger.error(f"Runtime error: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 1

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
