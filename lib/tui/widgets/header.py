"""Persistent cogitator header: title + Menu / Reload / Terminate."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Button, Static


class CogitatorHeader(Horizontal):
    DEFAULT_CSS = """
    CogitatorHeader {
        dock: top;
        height: 5;
        background: #0a1810;
        border: heavy #2a8040;
        padding: 0 1;
    }
    CogitatorHeader #header-title {
        width: 1fr;
        height: 100%;
        color: #66ff99;
        text-style: bold;
        content-align: left middle;
    }
    CogitatorHeader #header-actions {
        width: auto;
        height: 100%;
        align: right middle;
    }
    CogitatorHeader #header-actions Button {
        min-width: 12;
        width: auto;
        height: 3;
        margin: 0 0 0 1;
    }
    """

    def __init__(self, subtitle: str = "VEIL LINK STABLE") -> None:
        super().__init__()
        self._subtitle = subtitle

    def compose(self) -> ComposeResult:
        yield Static(
            f"MAGOS BIOLOGIS / COGITATOR-BIOGEN  |  {self._subtitle}",
            id="header-title",
        )
        with Horizontal(id="header-actions"):
            yield Button("Menu", id="hdr-menu")
            yield Button("Reload", id="hdr-reload")
            yield Button("Terminate", id="hdr-terminate")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        app = self.app
        bid = event.button.id
        if bid == "hdr-menu":
            event.stop()
            getattr(app, "request_menu")()
        elif bid == "hdr-reload":
            event.stop()
            getattr(app, "request_reload")()
        elif bid == "hdr-terminate":
            event.stop()
            getattr(app, "request_terminate")()
