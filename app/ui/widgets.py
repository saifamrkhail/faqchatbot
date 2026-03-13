"""Custom Textual widgets for the FAQ chatbot UI."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, ScrollableContainer
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button, Input, Static


class MessageBubble(Static):
    """Displays a single chat message with a role indicator."""

    DEFAULT_CSS = ""

    def __init__(
        self,
        content: str,
        *,
        role: str = "user",
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._content = content
        self._role = role

    def compose(self) -> ComposeResult:
        prefix = "🧑 Du" if self._role == "user" else "🤖 Antwort"
        yield Static(f"**{prefix}**", classes="message-role")
        yield Static(self._content, classes="message-text")

    def on_mount(self) -> None:
        self.add_class(f"message-{self._role}")


class ChatLog(ScrollableContainer):
    """Vertically scrolling container for chat messages."""

    def append_message(self, content: str, *, role: str = "user") -> None:
        """Add a message and scroll to the bottom."""

        bubble = MessageBubble(content, role=role)
        self.mount(bubble)
        bubble.scroll_visible()


class StatusIndicator(Static):
    """Shows transient status text such as 'Thinking...' or errors."""

    def show_thinking(self) -> None:
        self.update("⏳ Einen Moment bitte …")
        self.add_class("visible")

    def show_error(self, message: str) -> None:
        self.update(f"⚠ {message}")
        self.add_class("visible")
        self.add_class("error")

    def clear(self) -> None:
        self.update("")
        self.remove_class("visible")
        self.remove_class("error")


class ChatInput(Widget):
    """Input bar with a send button that fires a custom message."""

    class Submitted(Message):
        """Fired when the user submits a question."""

        def __init__(self, question: str) -> None:
            super().__init__()
            self.question = question

    def compose(self) -> ComposeResult:
        with Horizontal(id="input-row"):
            yield Input(
                placeholder="Stelle eine Frage …",
                id="chat-input",
            )
            yield Button("Senden", id="send-btn", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "send-btn":
            self._submit()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._submit()

    def _submit(self) -> None:
        input_widget = self.query_one("#chat-input", Input)
        question = input_widget.value.strip()
        if not question:
            return
        input_widget.value = ""
        self.post_message(self.Submitted(question))

    def focus_input(self) -> None:
        """Move focus to the text input."""
        self.query_one("#chat-input", Input).focus()

    def disable(self) -> None:
        self.query_one("#chat-input", Input).disabled = True
        self.query_one("#send-btn", Button).disabled = True

    def enable(self) -> None:
        self.query_one("#chat-input", Input).disabled = False
        self.query_one("#send-btn", Button).disabled = False
