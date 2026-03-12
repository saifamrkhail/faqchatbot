from __future__ import annotations

import logging

from app.config import AppSettings
from app.logging import configure_logging


def test_configure_logging_sets_the_root_log_level() -> None:
    logger = configure_logging(AppSettings(log_level="DEBUG"))

    assert logging.getLogger().level == logging.DEBUG
    assert logger.name == "faqchatbot"
