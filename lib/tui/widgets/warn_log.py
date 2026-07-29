from __future__ import annotations

from textual.widgets import RichLog


class WarnLog(RichLog):
    """Scrolling warning / override log."""

    def __init__(self) -> None:
        super().__init__(id="warn-log", highlight=False, markup=True)

    def boot(self) -> None:
        self.write("[dim]# WARNINGS / OVERRIDES — empty is blessed[/dim]")

    def push(self, msg: str) -> None:
        self.write(f"[yellow]>[/yellow] {msg}")
