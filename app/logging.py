"""Logging configuration helpers."""

from __future__ import annotations

import logging

from app.config import AppSettings, get_settings

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def configure_logging(settings: AppSettings | None = None) -> logging.Logger:
    """Configure root logging and return the application logger."""

    resolved_settings = settings or get_settings()
    level = getattr(logging, resolved_settings.log_level, logging.INFO)

    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        datefmt=DATE_FORMAT,
        force=True,
    )
    logging.captureWarnings(True)

    logger = logging.getLogger(resolved_settings.app_name)
    logger.debug("Logging configured", extra={"environment": resolved_settings.environment})
    return logger
