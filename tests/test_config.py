from __future__ import annotations

import pytest

from app.config import AppSettings, SettingsError, get_settings


def test_app_settings_uses_defaults_when_env_is_empty() -> None:
    settings = AppSettings.from_env({})

    assert settings.app_name == "faqchatbot"
    assert settings.environment == "development"
    assert settings.top_k == 3
    assert settings.score_threshold == pytest.approx(0.70)
    assert settings.debug is False


def test_app_settings_reads_environment_overrides() -> None:
    settings = AppSettings.from_env(
        {
            "FAQ_CHATBOT_ENVIRONMENT": "test",
            "FAQ_CHATBOT_LOG_LEVEL": "debug",
            "FAQ_CHATBOT_DEBUG": "true",
            "FAQ_CHATBOT_TOP_K": "5",
            "FAQ_CHATBOT_SCORE_THRESHOLD": "0.85",
            "FAQ_CHATBOT_QDRANT_COLLECTION_NAME": "faq_test",
        }
    )

    assert settings.environment == "test"
    assert settings.log_level == "DEBUG"
    assert settings.debug is True
    assert settings.top_k == 5
    assert settings.score_threshold == pytest.approx(0.85)
    assert settings.qdrant_collection_name == "faq_test"


def test_app_settings_rejects_invalid_threshold() -> None:
    with pytest.raises(SettingsError, match="SCORE_THRESHOLD"):
        AppSettings.from_env({"FAQ_CHATBOT_SCORE_THRESHOLD": "1.5"})


def test_get_settings_reads_process_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FAQ_CHATBOT_ENVIRONMENT", "test")

    settings = get_settings()

    assert settings.environment == "test"
