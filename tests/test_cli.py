from __future__ import annotations

from app.cli import _build_tui_service, build_startup_message, main
from app.config import AppSettings, SettingsError
from app.ui import StubChatService


def test_build_startup_message_contains_key_runtime_targets() -> None:
    message = build_startup_message(AppSettings())

    assert "faqchatbot core services ready" in message
    assert "faq=data/faq.json" in message
    assert "qdrant=http://localhost:6333" in message
    assert "ollama=http://localhost:11434" in message


def test_main_returns_error_code_for_invalid_configuration(monkeypatch) -> None:
    def raise_settings_error() -> AppSettings:
        raise SettingsError("boom")

    monkeypatch.setattr("app.cli.get_settings", raise_settings_error)

    assert main() == 1


def test_build_tui_service_uses_real_chat_service_by_default(monkeypatch) -> None:
    sentinel_service = object()

    class FakeAdapter:
        def __init__(self, chat_service: object) -> None:
            self.chat_service = chat_service

    monkeypatch.setattr("app.ui.protocol.ChatServiceAdapter", FakeAdapter)
    monkeypatch.setattr(
        "app.cli.ChatService.from_settings",
        lambda settings: sentinel_service,
    )

    service = _build_tui_service(AppSettings())

    assert isinstance(service, FakeAdapter)
    assert service.chat_service is sentinel_service


def test_build_tui_service_can_fall_back_to_stub() -> None:
    service = _build_tui_service(AppSettings(use_stub_ui_service=True))

    assert isinstance(service, StubChatService)
