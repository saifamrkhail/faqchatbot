from __future__ import annotations

import pytest

from app.config import clear_settings_cache


@pytest.fixture(autouse=True)
def reset_settings_cache() -> None:
    clear_settings_cache()
    yield
    clear_settings_cache()
