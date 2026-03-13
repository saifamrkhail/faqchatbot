"""Textual application shell for the FAQ chatbot."""

from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header, Static

from app.ui.protocol import ChatResponse, ChatServiceProtocol, StubChatService
from app.ui.widgets import ChatInput, ChatLog, StatusIndicator


_CSS_PATH = Path(__file__).parent / "styles.tcss"


class FAQChatApp(App):
    """Terminal UI for the FAQ chatbot.

    Delegates all business logic to a ``ChatServiceProtocol`` implementation
    injected at construction time.
    """

    TITLE = "FAQ Chatbot"
    SUB_TITLE = "Stelle eine Frage"
    CSS_PATH = _CSS_PATH

    BINDINGS = [
        Binding("ctrl+q", "quit", "Beenden", show=True),
        Binding("ctrl+c", "quit", "Beenden", show=False),
    ]

    def __init__(
        self,
        chat_service: ChatServiceProtocol | None = None,
        *,
        title: str | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._chat_service: ChatServiceProtocol = chat_service or StubChatService()
        if title:
            self.title = title

    def compose(self) -> ComposeResult:
        yield Header()
        yield ChatLog(id="chat-log")
        yield StatusIndicator(id="status-indicator")
        yield ChatInput(id="input-area")
        yield Footer()

    def on_mount(self) -> None:
        chat_log = self.query_one("#chat-log", ChatLog)
        chat_log.mount(
            Static(
                "Willkommen! Stelle eine Frage zu unseren FAQ.",
                id="welcome",
            )
        )
        self.query_one("#input-area", ChatInput).focus_input()

    async def on_chat_input_submitted(self, event: ChatInput.Submitted) -> None:
        """Handle a user question submission."""

        question = event.question
        chat_log = self.query_one("#chat-log", ChatLog)
        status = self.query_one("#status-indicator", StatusIndicator)
        input_area = self.query_one("#input-area", ChatInput)

        # Remove the welcome message on first interaction.
        welcome = self.query("#welcome")
        for widget in welcome:
            await widget.remove()

        chat_log.append_message(question, role="user")

        input_area.disable()
        status.show_thinking()

        try:
            response: ChatResponse = await self._chat_service.ask(question)
            chat_log.append_message(response.answer, role="assistant")
        except Exception as exc:  # noqa: BLE001
            status.show_error(f"Fehler: {exc}")
        else:
            status.clear()
        finally:
            input_area.enable()
            input_area.focus_input()
