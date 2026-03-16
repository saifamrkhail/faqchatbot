from __future__ import annotations

import pytest

from pathlib import Path

from app.config import AppSettings, PROJECT_ROOT, SettingsError, get_settings, resolve_project_path


def test_app_settings_uses_defaults_when_env_is_empty() -> None:
    settings = AppSettings.from_env({})

    assert settings.app_name == "faqchatbot"
    assert settings.environment == "development"
    assert settings.faq_data_path == "data/faq.json"
    assert settings.ollama_timeout_seconds == pytest.approx(120.0)
    assert settings.ollama_generate_temperature == pytest.approx(0.1)
    assert settings.ollama_generate_max_tokens == 512
    assert settings.ollama_enable_thinking is False
    assert settings.qdrant_timeout_seconds == pytest.approx(30.0)
    assert settings.top_k == 3
    assert settings.score_threshold == pytest.approx(0.50)
    assert settings.max_question_chars == 500
    assert settings.use_stub_ui_service is False
    assert settings.query_rewrite_enabled is True
    assert settings.query_rewrite_borderline_min_score == pytest.approx(0.35)
    assert settings.query_rewrite_max_variants == 3
    assert settings.query_rewrite_temperature == pytest.approx(0.0)
    assert settings.query_rewrite_max_tokens == 96
    assert settings.debug is False


def test_app_settings_reads_environment_overrides() -> None:
    settings = AppSettings.from_env(
        {
            "FAQ_CHATBOT_ENVIRONMENT": "test",
            "FAQ_CHATBOT_LOG_LEVEL": "debug",
            "FAQ_CHATBOT_DEBUG": "true",
            "FAQ_CHATBOT_FAQ_DATA_PATH": "fixtures/faq.json",
            "FAQ_CHATBOT_TOP_K": "5",
            "FAQ_CHATBOT_SCORE_THRESHOLD": "0.85",
            "FAQ_CHATBOT_OLLAMA_TIMEOUT_SECONDS": "45",
            "FAQ_CHATBOT_OLLAMA_GENERATE_TEMPERATURE": "0.2",
            "FAQ_CHATBOT_OLLAMA_GENERATE_MAX_TOKENS": "512",
            "FAQ_CHATBOT_OLLAMA_ENABLE_THINKING": "false",
            "FAQ_CHATBOT_QDRANT_COLLECTION_NAME": "faq_test",
            "FAQ_CHATBOT_QDRANT_TIMEOUT_SECONDS": "15",
            "FAQ_CHATBOT_MAX_QUESTION_CHARS": "300",
            "FAQ_CHATBOT_USE_STUB_UI_SERVICE": "true",
            "FAQ_CHATBOT_QUERY_REWRITE_ENABLED": "false",
            "FAQ_CHATBOT_QUERY_REWRITE_BORDERLINE_MIN_SCORE": "0.40",
            "FAQ_CHATBOT_QUERY_REWRITE_MAX_VARIANTS": "2",
            "FAQ_CHATBOT_QUERY_REWRITE_TEMPERATURE": "0.05",
            "FAQ_CHATBOT_QUERY_REWRITE_MAX_TOKENS": "64",
        }
    )

    assert settings.environment == "test"
    assert settings.log_level == "DEBUG"
    assert settings.debug is True
    assert settings.faq_data_path == "fixtures/faq.json"
    assert settings.ollama_timeout_seconds == pytest.approx(45.0)
    assert settings.ollama_generate_temperature == pytest.approx(0.2)
    assert settings.ollama_generate_max_tokens == 512
    assert settings.ollama_enable_thinking is False
    assert settings.top_k == 5
    assert settings.score_threshold == pytest.approx(0.85)
    assert settings.qdrant_collection_name == "faq_test"
    assert settings.qdrant_timeout_seconds == pytest.approx(15.0)
    assert settings.max_question_chars == 300
    assert settings.use_stub_ui_service is True
    assert settings.query_rewrite_enabled is False
    assert settings.query_rewrite_borderline_min_score == pytest.approx(0.40)
    assert settings.query_rewrite_max_variants == 2
    assert settings.query_rewrite_temperature == pytest.approx(0.05)
    assert settings.query_rewrite_max_tokens == 64


def test_app_settings_rejects_invalid_threshold() -> None:
    with pytest.raises(SettingsError, match="SCORE_THRESHOLD"):
        AppSettings.from_env({"FAQ_CHATBOT_SCORE_THRESHOLD": "1.5"})


def test_app_settings_rejects_invalid_timeouts() -> None:
    with pytest.raises(SettingsError, match="OLLAMA_TIMEOUT_SECONDS"):
        AppSettings.from_env({"FAQ_CHATBOT_OLLAMA_TIMEOUT_SECONDS": "0"})

    with pytest.raises(SettingsError, match="QDRANT_TIMEOUT_SECONDS"):
        AppSettings.from_env({"FAQ_CHATBOT_QDRANT_TIMEOUT_SECONDS": "301"})


def test_app_settings_rejects_invalid_generation_configuration() -> None:
    with pytest.raises(SettingsError, match="OLLAMA_GENERATE_TEMPERATURE"):
        AppSettings.from_env({"FAQ_CHATBOT_OLLAMA_GENERATE_TEMPERATURE": "3"})

    with pytest.raises(SettingsError, match="OLLAMA_GENERATE_MAX_TOKENS"):
        AppSettings.from_env({"FAQ_CHATBOT_OLLAMA_GENERATE_MAX_TOKENS": "0"})

    with pytest.raises(SettingsError, match="MAX_QUESTION_CHARS"):
        AppSettings.from_env({"FAQ_CHATBOT_MAX_QUESTION_CHARS": "0"})

    with pytest.raises(SettingsError, match="QUERY_REWRITE_TEMPERATURE"):
        AppSettings.from_env({"FAQ_CHATBOT_QUERY_REWRITE_TEMPERATURE": "3"})

    with pytest.raises(SettingsError, match="QUERY_REWRITE_MAX_TOKENS"):
        AppSettings.from_env({"FAQ_CHATBOT_QUERY_REWRITE_MAX_TOKENS": "0"})

    with pytest.raises(SettingsError, match="QUERY_REWRITE_MAX_VARIANTS"):
        AppSettings.from_env({"FAQ_CHATBOT_QUERY_REWRITE_MAX_VARIANTS": "0"})

    with pytest.raises(
        SettingsError,
        match="QUERY_REWRITE_BORDERLINE_MIN_SCORE must be <= SCORE_THRESHOLD",
    ):
        AppSettings.from_env(
            {
                "FAQ_CHATBOT_SCORE_THRESHOLD": "0.50",
                "FAQ_CHATBOT_QUERY_REWRITE_BORDERLINE_MIN_SCORE": "0.60",
            }
        )


def test_get_settings_reads_process_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FAQ_CHATBOT_ENVIRONMENT", "test")

    settings = get_settings()

    assert settings.environment == "test"


def test_resolve_project_path_uses_project_root_for_relative_paths() -> None:
    resolved = resolve_project_path("data/faq.json")

    assert resolved == (PROJECT_ROOT / "data/faq.json").resolve()


def test_resolve_project_path_preserves_absolute_paths(tmp_path: Path) -> None:
    absolute_path = tmp_path / "faq.json"

    assert resolve_project_path(absolute_path) == absolute_path
