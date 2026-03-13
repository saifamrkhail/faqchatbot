"""CLI entrypoint for the FAQ chatbot."""

from __future__ import annotations

import sys

from app.config import AppSettings, SettingsError, get_settings
from app.logging import configure_logging


def build_startup_message(settings: AppSettings) -> str:
    """Return a small status line for the current app baseline."""

    return (
        f"{settings.app_name} core services ready | "
        f"env={settings.environment} | "
        f"faq={settings.faq_data_path} | "
        f"qdrant={settings.qdrant_url} | "
        f"ollama={settings.ollama_base_url}"
    )


def _run_tui(settings: AppSettings) -> int:
    """Launch the Textual terminal UI."""

    from app.ui import FAQChatApp, StubChatService

    # Use StubChatService until Module 07 provides the real service.
    service = StubChatService()
    app = FAQChatApp(chat_service=service, title=settings.app_name)
    app.run()
    return 0


def main() -> int:
    """Start the chatbot application.

    Uses ``--tui`` flag or defaults to status-print mode.
    """

    try:
        settings = get_settings()
    except SettingsError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1

    logger = configure_logging(settings)

    tui_mode = "--tui" in sys.argv

    if tui_mode:
        logger.info("Launching Terminal UI")
        return _run_tui(settings)

    logger.info("Application core services initialized")
    print(build_startup_message(settings))
    return 0
