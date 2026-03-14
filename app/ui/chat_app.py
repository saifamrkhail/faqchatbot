"""Simple terminal chat loop."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.ui.protocol import ChatServiceProtocol


def run_chat_loop(chat_service: ChatServiceProtocol, *, title: str = "faqchatbot") -> None:
    """Run an interactive terminal chat loop.

    Args:
        chat_service: The chat service implementation to use.
        title: Application title displayed in the header.
    """
    from rich.console import Console
    from rich.rule import Rule

    console = Console()
    console.print(Rule(f"[bold]{title}[/bold]  —  Ctrl+C oder 'exit' zum Beenden"))
    console.print()
    console.print("[dim]Willkommen! Stelle eine Frage zu unseren FAQ.[/dim]")
    console.print()

    while True:
        try:
            question = input("Sie: ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Tschüss![/dim]")
            break

        if not question:
            continue

        if question.lower() in {"exit", "quit", "bye"}:
            console.print("[dim]Tschüss![/dim]")
            break

        console.print("[dim]...[/dim]")

        try:
            response = chat_service.ask(question)
            console.print(f"[bold green]Bot:[/bold green] {response.answer}")
        except Exception as exc:  # noqa: BLE001
            console.print(f"[bold red]Fehler:[/bold red] {exc}")

        console.print()
