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

        try:
            if hasattr(chat_service, "ask_streaming"):
                print("Bot: ", end="", flush=True)
                for token in chat_service.ask_streaming(question):
                    print(token, end="", flush=True)
                print("\n")
            else:
                print("...")
                response = chat_service.ask(question)
                if response.thinking:
                    print("Qwen denkt:")
                    print(response.thinking)
                    print()
                print(f"Bot: {response.answer}\n")
        except Exception as exc:  # noqa: BLE001
            print(f"\nFehler: {exc}\n")
