"""CLI entrypoint for the project scaffold."""

from __future__ import annotations

import sys

from app.config import AppSettings, SettingsError, get_settings
from app.logging import configure_logging


def build_startup_message(settings: AppSettings) -> str:
    """Return a small status line for the scaffolded app."""

    return (
        f"{settings.app_name} scaffold ready | "
        f"env={settings.environment} | "
        f"qdrant={settings.qdrant_url} | "
        f"ollama={settings.ollama_base_url}"
    )


def main() -> int:
    """Start the current scaffold and validate configuration eagerly."""

    try:
        settings = get_settings()
    except SettingsError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1

    logger = configure_logging(settings)
    logger.info("Application scaffold initialized")
    print(build_startup_message(settings))
    return 0
