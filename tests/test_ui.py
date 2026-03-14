"""Tests for Terminal UI (Module 08)."""

from __future__ import annotations

import asyncio
from io import StringIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domain import ChatResponse as DomainChatResponse
from app.ui.protocol import (
    ChatResponse,
    ChatServiceAdapter,
    ChatServiceProtocol,
    StubChatService,
)


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


# ---------------------------------------------------------------------------
# ChatServiceAdapter tests
# ---------------------------------------------------------------------------


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
# Chat loop tests
# ---------------------------------------------------------------------------


class TestRunChatLoop:
    def test_exits_on_eof(self) -> None:
        """Test that the loop exits cleanly when EOF is reached."""
        service = StubChatService()

        # Mock Console at the point where it's imported
        with patch("rich.console.Console") as mock_console_class:
            mock_console = MagicMock()
            mock_console_class.return_value = mock_console
            mock_console.input.side_effect = EOFError()

            from app.ui.chat_app import run_chat_loop

            # Should not raise an error
            run_chat_loop(service, title="test")

            # Verify the welcome message was printed
            assert mock_console.print.called

    def test_exits_on_keyboard_interrupt(self) -> None:
        """Test that the loop exits cleanly on Ctrl+C."""
        service = StubChatService()

        # Mock Console at the point where it's imported
        with patch("rich.console.Console") as mock_console_class:
            mock_console = MagicMock()
            mock_console_class.return_value = mock_console
            mock_console.input.side_effect = KeyboardInterrupt()

            from app.ui.chat_app import run_chat_loop

            # Should not raise an error
            run_chat_loop(service, title="test")

            # Verify the goodbye message was printed
            assert mock_console.print.called

    def test_skips_empty_questions(self) -> None:
        """Test that empty questions are skipped without calling the service."""
        service = AsyncMock(spec=ChatServiceProtocol)
        service.ask.return_value = ChatResponse(answer="Test")

        with patch("rich.console.Console") as mock_console_class:
            mock_console = MagicMock()
            mock_console_class.return_value = mock_console
            # Return empty string first (empty input), then EOFError to exit
            mock_console.input.side_effect = ["", EOFError()]

            from app.ui.chat_app import run_chat_loop

            run_chat_loop(service, title="test")

            # Verify the service was never called for the empty input
            service.ask.assert_not_called()

    def test_calls_service_with_valid_question(self) -> None:
        """Test that valid questions call the service."""
        service = AsyncMock(spec=ChatServiceProtocol)
        service.ask.return_value = ChatResponse(answer="Test Answer")

        with patch("rich.console.Console") as mock_console_class:
            mock_console = MagicMock()
            mock_console_class.return_value = mock_console
            # Ask a question, then exit
            mock_console.input.side_effect = ["Hello Bot?", EOFError()]

            from app.ui.chat_app import run_chat_loop

            run_chat_loop(service, title="test")

            # Verify the service was called with the question
            service.ask.assert_called_once_with("Hello Bot?")

    def test_prints_answer_on_success(self) -> None:
        """Test that successful answers are printed."""
        service = AsyncMock(spec=ChatServiceProtocol)
        service.ask.return_value = ChatResponse(answer="Test Answer")

        with patch("rich.console.Console") as mock_console_class:
            mock_console = MagicMock()
            mock_console_class.return_value = mock_console
            mock_console.input.side_effect = ["What?", EOFError()]

            from app.ui.chat_app import run_chat_loop

            run_chat_loop(service, title="test")

            # Verify the answer was printed
            calls = [str(call) for call in mock_console.print.call_args_list]
            answer_printed = any("Test Answer" in str(call) for call in calls)
            assert answer_printed

    def test_prints_error_on_service_exception(self) -> None:
        """Test that service exceptions are caught and printed."""
        service = AsyncMock(spec=ChatServiceProtocol)
        service.ask.side_effect = RuntimeError("Service error")

        with patch("rich.console.Console") as mock_console_class:
            mock_console = MagicMock()
            mock_console_class.return_value = mock_console
            mock_console.input.side_effect = ["Help!", EOFError()]

            from app.ui.chat_app import run_chat_loop

            run_chat_loop(service, title="test")

            # Verify the error was printed
            calls = [str(call) for call in mock_console.print.call_args_list]
            error_printed = any("Service error" in str(call) for call in calls)
            assert error_printed

    def test_custom_title(self) -> None:
        """Test that custom title is used."""
        service = StubChatService()

        with patch("rich.console.Console") as mock_console_class:
            mock_console = MagicMock()
            mock_console_class.return_value = mock_console
            mock_console.input.side_effect = EOFError()

            from app.ui.chat_app import run_chat_loop

            run_chat_loop(service, title="MyCustomBot")

            # Verify title was in the print calls
            calls = [str(call) for call in mock_console.print.call_args_list]
            title_printed = any("MyCustomBot" in str(call) for call in calls)
            assert title_printed

    def test_strips_whitespace_from_input(self) -> None:
        """Test that whitespace is stripped from user input."""
        service = AsyncMock(spec=ChatServiceProtocol)
        service.ask.return_value = ChatResponse(answer="OK")

        with patch("rich.console.Console") as mock_console_class:
            mock_console = MagicMock()
            mock_console_class.return_value = mock_console
            # Question with leading/trailing whitespace
            mock_console.input.side_effect = ["  question with spaces  ", EOFError()]

            from app.ui.chat_app import run_chat_loop

            run_chat_loop(service, title="test")

            # Verify the service was called with stripped input
            service.ask.assert_called_once_with("question with spaces")
