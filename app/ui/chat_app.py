"""Terminal chat loop."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.ui.protocol import ChatServiceProtocol

_SEP = "─" * 60


def run_chat_loop(chat_service: ChatServiceProtocol, *, title: str = "faqchatbot") -> None:
    print(f"\n{_SEP}")
    print(f"  {title}  |  'exit' oder Ctrl+C zum Beenden")
    print(_SEP)
    print("Willkommen! Stelle eine Frage zu unseren FAQ.\n")

    while True:
        try:
            question = input("Sie: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nTschüss!")
            break

        if not question:
            continue

        if question.lower() in {"exit", "quit", "bye"}:
            print("Tschüss!")
            break

        print("...")

        try:
            response = chat_service.ask(question)
            print(f"Bot: {response.answer}\n")
        except Exception as exc:  # noqa: BLE001
            print(f"Fehler: {exc}\n")
