"""Tests for Terminal UI (Module 08)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

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

    def test_ask_returns_chat_response(self) -> None:
        service = StubChatService()
        with patch("app.ui.protocol.time.sleep"):
            resp = service.ask("What is this?")
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

    def test_maps_domain_response_to_ui_response(self) -> None:
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

        response = ChatServiceAdapter(CoreService()).ask("Frage")

        assert response.answer == "Antwort"
        assert response.source_faq == "faq-01"
        assert response.is_fallback is False


# ---------------------------------------------------------------------------
# Chat loop tests
# ---------------------------------------------------------------------------


class TestRunChatLoop:
    def test_exits_on_eof(self) -> None:
        service = StubChatService()

        with patch("builtins.input", side_effect=EOFError()):
            with patch("rich.console.Console") as mock_console_class:
                mock_console = MagicMock()
                mock_console_class.return_value = mock_console

                from app.ui.chat_app import run_chat_loop

                run_chat_loop(service, title="test")
                assert mock_console.print.called

    def test_exits_on_keyboard_interrupt(self) -> None:
        service = StubChatService()

        with patch("builtins.input", side_effect=KeyboardInterrupt()):
            with patch("rich.console.Console") as mock_console_class:
                mock_console = MagicMock()
                mock_console_class.return_value = mock_console

                from app.ui.chat_app import run_chat_loop

                run_chat_loop(service, title="test")
                assert mock_console.print.called

    def test_exits_on_exit_command(self) -> None:
        service = MagicMock(spec=ChatServiceProtocol)

        with patch("builtins.input", side_effect=["exit"]):
            with patch("rich.console.Console") as mock_console_class:
                mock_console_class.return_value = MagicMock()

                from app.ui.chat_app import run_chat_loop

                run_chat_loop(service, title="test")
                service.ask.assert_not_called()

    def test_skips_empty_questions(self) -> None:
        service = MagicMock(spec=ChatServiceProtocol)
        service.ask.return_value = ChatResponse(answer="Test")

        with patch("builtins.input", side_effect=["", EOFError()]):
            with patch("rich.console.Console") as mock_console_class:
                mock_console_class.return_value = MagicMock()

                from app.ui.chat_app import run_chat_loop

                run_chat_loop(service, title="test")
                service.ask.assert_not_called()

    def test_calls_service_with_valid_question(self) -> None:
        service = MagicMock(spec=ChatServiceProtocol)
        service.ask.return_value = ChatResponse(answer="Test Answer")

        with patch("builtins.input", side_effect=["Hello Bot?", EOFError()]):
            with patch("rich.console.Console") as mock_console_class:
                mock_console_class.return_value = MagicMock()

                from app.ui.chat_app import run_chat_loop

                run_chat_loop(service, title="test")
                service.ask.assert_called_once_with("Hello Bot?")

    def test_prints_answer_on_success(self) -> None:
        service = MagicMock(spec=ChatServiceProtocol)
        service.ask.return_value = ChatResponse(answer="Test Answer")

        with patch("builtins.input", side_effect=["What?", EOFError()]):
            with patch("rich.console.Console") as mock_console_class:
                mock_console = MagicMock()
                mock_console_class.return_value = mock_console

                from app.ui.chat_app import run_chat_loop

                run_chat_loop(service, title="test")

                calls = [str(c) for c in mock_console.print.call_args_list]
                assert any("Test Answer" in c for c in calls)

    def test_prints_error_on_service_exception(self) -> None:
        service = MagicMock(spec=ChatServiceProtocol)
        service.ask.side_effect = RuntimeError("Service error")

        with patch("builtins.input", side_effect=["Help!", EOFError()]):
            with patch("rich.console.Console") as mock_console_class:
                mock_console = MagicMock()
                mock_console_class.return_value = mock_console

                from app.ui.chat_app import run_chat_loop

                run_chat_loop(service, title="test")

                calls = [str(c) for c in mock_console.print.call_args_list]
                assert any("Service error" in c for c in calls)

    def test_custom_title(self) -> None:
        service = MagicMock(spec=ChatServiceProtocol)

        with patch("builtins.input", side_effect=EOFError()):
            with patch("rich.console.Console") as mock_console_class:
                mock_console = MagicMock()
                mock_console_class.return_value = mock_console

                from app.ui.chat_app import run_chat_loop

                run_chat_loop(service, title="MyCustomBot")

                calls = [str(c) for c in mock_console.print.call_args_list]
                assert any("MyCustomBot" in c for c in calls)

    def test_strips_whitespace_from_input(self) -> None:
        service = MagicMock(spec=ChatServiceProtocol)
        service.ask.return_value = ChatResponse(answer="OK")

        with patch("builtins.input", side_effect=["  spaced question  ", EOFError()]):
            with patch("rich.console.Console") as mock_console_class:
                mock_console_class.return_value = MagicMock()

                from app.ui.chat_app import run_chat_loop

                run_chat_loop(service, title="test")
                service.ask.assert_called_once_with("spaced question")
