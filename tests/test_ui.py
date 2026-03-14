"""Tests for Phase 8 – Terminal UI (Module 08)."""

from __future__ import annotations

import asyncio

import pytest

from app.domain import ChatResponse as DomainChatResponse
from app.ui.protocol import (
    ChatResponse,
    ChatServiceAdapter,
    ChatServiceProtocol,
    StubChatService,
)

try:
    import textual  # noqa: F401
except ModuleNotFoundError:
    textual = None


# ---------------------------------------------------------------------------
# ChatResponse tests
# ---------------------------------------------------------------------------

class TestChatResponse:
    def test_construct_with_defaults(self) -> None:
        resp = ChatResponse(answer="Hello")
        assert resp.answer == "Hello"
        assert resp.source_faq is None
        assert resp.is_fallback is False

    def test_construct_with_all_fields(self) -> None:
        resp = ChatResponse(answer="A", source_faq="faq-01", is_fallback=True)
        assert resp.answer == "A"
        assert resp.source_faq == "faq-01"
        assert resp.is_fallback is True

    def test_is_frozen(self) -> None:
        resp = ChatResponse(answer="X")
        with pytest.raises(AttributeError):
            resp.answer = "Y"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# StubChatService tests
# ---------------------------------------------------------------------------

class TestStubChatService:
    def test_satisfies_protocol(self) -> None:
        assert isinstance(StubChatService(), ChatServiceProtocol)

    @pytest.mark.asyncio
    async def test_ask_returns_chat_response(self) -> None:
        service = StubChatService()
        resp = await service.ask("What is this?")
        assert isinstance(resp, ChatResponse)
        assert resp.is_fallback is True
        assert resp.source_faq is None
        assert len(resp.answer) > 0


class TestChatServiceAdapter:
    def test_satisfies_protocol(self) -> None:
        class CoreService:
            def handle_question(self, question: str) -> DomainChatResponse:
                return DomainChatResponse(
                    question=question,
                    answer="Antwort",
                    is_fallback=False,
                    confidence=0.9,
                    source_faq_id="faq-01",
                    used_retrieval=True,
                )

        assert isinstance(ChatServiceAdapter(CoreService()), ChatServiceProtocol)

    @pytest.mark.asyncio
    async def test_maps_domain_response_to_ui_response(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        class CoreService:
            def handle_question(self, question: str) -> DomainChatResponse:
                return DomainChatResponse(
                    question=question,
                    answer="Antwort",
                    is_fallback=False,
                    confidence=0.9,
                    source_faq_id="faq-01",
                    used_retrieval=True,
                )

        async def run_inline(func, *args):
            return func(*args)

        monkeypatch.setattr("app.ui.protocol.asyncio.to_thread", run_inline)

        response = await ChatServiceAdapter(CoreService()).ask("Frage")

        assert response.answer == "Antwort"
        assert response.source_faq == "faq-01"
        assert response.is_fallback is False


# ---------------------------------------------------------------------------
# Widget unit tests (no full app mount required)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(textual is None, reason="textual is not installed")
class TestWidgetImports:
    """Verify all widgets can be imported without errors."""

    def test_import_message_bubble(self) -> None:
        from app.ui.widgets import MessageBubble
        assert MessageBubble is not None

    def test_import_chat_log(self) -> None:
        from app.ui.widgets import ChatLog
        assert ChatLog is not None

    def test_import_status_indicator(self) -> None:
        from app.ui.widgets import StatusIndicator
        assert StatusIndicator is not None

    def test_import_chat_input(self) -> None:
        from app.ui.widgets import ChatInput
        assert ChatInput is not None


# ---------------------------------------------------------------------------
# FAQChatApp integration tests (Textual pilot)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(textual is None, reason="textual is not installed")
class TestFAQChatApp:
    @pytest.mark.asyncio
    async def test_app_mounts_and_has_expected_widgets(self) -> None:
        from app.ui.chat_app import FAQChatApp
        from app.ui.widgets import ChatInput, ChatLog, StatusIndicator

        app = FAQChatApp()
        async with app.run_test() as pilot:
            assert app.query_one("#chat-log", ChatLog)
            assert app.query_one("#status-indicator", StatusIndicator)
            assert app.query_one("#input-area", ChatInput)

    @pytest.mark.asyncio
    async def test_welcome_message_displayed(self) -> None:
        from app.ui.chat_app import FAQChatApp

        app = FAQChatApp()
        async with app.run_test() as pilot:
            welcome = app.query_one("#welcome")
            assert "Willkommen" in welcome.render().plain

    @pytest.mark.asyncio
    async def test_submit_question_shows_response(self) -> None:
        from app.ui.chat_app import FAQChatApp
        from app.ui.widgets import ChatLog

        # Use a fast stub that returns immediately.
        class FastStub:
            async def ask(self, question: str) -> ChatResponse:
                return ChatResponse(answer="Test-Antwort", is_fallback=False)

        app = FAQChatApp(chat_service=FastStub())
        async with app.run_test() as pilot:
            # Type a question and submit.
            await pilot.click("#chat-input")
            await pilot.press("T", "e", "s", "t")
            await pilot.press("enter")
            await pilot.pause()

            chat_log = app.query_one("#chat-log", ChatLog)
            rendered = chat_log.render().plain if hasattr(chat_log.render(), 'plain') else str(chat_log.render())
            # Verify that both the user question and the answer appeared
            bubbles = chat_log.query("MessageBubble")
            assert len(bubbles) >= 2  # user message + assistant response

    @pytest.mark.asyncio
    async def test_empty_input_does_not_submit(self) -> None:
        from app.ui.chat_app import FAQChatApp
        from app.ui.widgets import ChatLog

        app = FAQChatApp()
        async with app.run_test() as pilot:
            # Press enter on empty input.
            await pilot.click("#chat-input")
            await pilot.press("enter")
            await pilot.pause()

            chat_log = app.query_one("#chat-log", ChatLog)
            bubbles = chat_log.query("MessageBubble")
            assert len(bubbles) == 0  # no message added

    @pytest.mark.asyncio
    async def test_custom_title_applied(self) -> None:
        from app.ui.chat_app import FAQChatApp

        app = FAQChatApp(title="MyBot")
        async with app.run_test() as pilot:
            assert app.title == "MyBot"

    @pytest.mark.asyncio
    async def test_error_handling_shows_status(self) -> None:
        from app.ui.chat_app import FAQChatApp
        from app.ui.widgets import StatusIndicator

        class FailingService:
            async def ask(self, question: str) -> ChatResponse:
                raise RuntimeError("Service unavailable")

        app = FAQChatApp(chat_service=FailingService())
        async with app.run_test() as pilot:
            await pilot.click("#chat-input")
            await pilot.press("H", "i")
            await pilot.press("enter")
            await pilot.pause()

            status = app.query_one("#status-indicator", StatusIndicator)
            assert status.has_class("error")
