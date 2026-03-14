"""Tests for Terminal UI (Module 08)."""

from __future__ import annotations

from unittest.mock import MagicMock, call, patch

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
    def _make_service(self, answer: str = "Antwort") -> MagicMock:
        service = MagicMock(spec=ChatServiceProtocol)
        service.ask.return_value = ChatResponse(answer=answer)
        return service

    def test_exits_on_eof(self) -> None:
        service = self._make_service()
        with patch("builtins.input", side_effect=EOFError()), \
             patch("builtins.print") as mock_print:
            from app.ui.chat_app import run_chat_loop
            run_chat_loop(service, title="test")
        assert mock_print.called

    def test_exits_on_keyboard_interrupt(self) -> None:
        service = self._make_service()
        with patch("builtins.input", side_effect=KeyboardInterrupt()), \
             patch("builtins.print") as mock_print:
            from app.ui.chat_app import run_chat_loop
            run_chat_loop(service, title="test")
        assert mock_print.called

    def test_exits_on_exit_command(self) -> None:
        service = self._make_service()
        with patch("builtins.input", side_effect=["exit"]), \
             patch("builtins.print"):
            from app.ui.chat_app import run_chat_loop
            run_chat_loop(service, title="test")
        service.ask.assert_not_called()

    def test_skips_empty_questions(self) -> None:
        service = self._make_service()
        with patch("builtins.input", side_effect=["", "  ", EOFError()]), \
             patch("builtins.print"):
            from app.ui.chat_app import run_chat_loop
            run_chat_loop(service, title="test")
        service.ask.assert_not_called()

    def test_calls_service_with_valid_question(self) -> None:
        service = self._make_service()
        with patch("builtins.input", side_effect=["Was kostet Support?", EOFError()]), \
             patch("builtins.print"):
            from app.ui.chat_app import run_chat_loop
            run_chat_loop(service, title="test")
        service.ask.assert_called_once_with("Was kostet Support?")

    def test_prints_answer(self) -> None:
        service = self._make_service(answer="Ja, wir bieten Support an.")
        with patch("builtins.input", side_effect=["Frage?", EOFError()]), \
             patch("builtins.print") as mock_print:
            from app.ui.chat_app import run_chat_loop
            run_chat_loop(service, title="test")
        printed = " ".join(str(c) for c in mock_print.call_args_list)
        assert "Ja, wir bieten Support an." in printed

    def test_prints_error_on_service_exception(self) -> None:
        service = MagicMock(spec=ChatServiceProtocol)
        service.ask.side_effect = RuntimeError("Verbindung fehlgeschlagen")
        with patch("builtins.input", side_effect=["Hilfe!", EOFError()]), \
             patch("builtins.print") as mock_print:
            from app.ui.chat_app import run_chat_loop
            run_chat_loop(service, title="test")
        printed = " ".join(str(c) for c in mock_print.call_args_list)
        assert "Verbindung fehlgeschlagen" in printed

    def test_title_in_header(self) -> None:
        service = self._make_service()
        with patch("builtins.input", side_effect=EOFError()), \
             patch("builtins.print") as mock_print:
            from app.ui.chat_app import run_chat_loop
            run_chat_loop(service, title="MeinBot")
        printed = " ".join(str(c) for c in mock_print.call_args_list)
        assert "MeinBot" in printed

    def test_strips_whitespace_from_input(self) -> None:
        service = self._make_service()
        with patch("builtins.input", side_effect=["  Frage mit Spaces  ", EOFError()]), \
             patch("builtins.print"):
            from app.ui.chat_app import run_chat_loop
            run_chat_loop(service, title="test")
        service.ask.assert_called_once_with("Frage mit Spaces")
