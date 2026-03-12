from __future__ import annotations

from app.cli import build_startup_message, main
from app.config import AppSettings, SettingsError


def test_build_startup_message_contains_key_runtime_targets() -> None:
    message = build_startup_message(AppSettings())

    assert "faqchatbot scaffold ready" in message
    assert "qdrant=http://localhost:6333" in message
    assert "ollama=http://localhost:11434" in message


def test_main_returns_error_code_for_invalid_configuration(monkeypatch) -> None:
    def raise_settings_error() -> AppSettings:
        raise SettingsError("boom")

    monkeypatch.setattr("app.cli.get_settings", raise_settings_error)

    assert main() == 1
