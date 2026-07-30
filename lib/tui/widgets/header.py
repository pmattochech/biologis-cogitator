"""Persistent cogitator header: status banner + title + Menu / Reload / Terminate."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Static


class CogitatorHeader(Vertical):
    DEFAULT_CSS = """
    CogitatorHeader {
        dock: top;
        height: auto;
        background: #0a1810;
        border: heavy #2a8040;
        padding: 0;
    }
    CogitatorHeader #update-banner {
        display: none;
        width: 1fr;
        height: 1;
        max-height: 1;
        min-height: 1;
        padding: 0 1;
        text-style: bold;
        overflow: hidden hidden;
    }
    CogitatorHeader #update-banner.-show {
        display: block;
    }
    CogitatorHeader #update-banner.-update {
        background: #3a2010;
        color: #ffd080;
        border-bottom: solid #c07020;
    }
    CogitatorHeader #update-banner.-current {
        background: #0a2818;
        color: #b8ffd0;
        border-bottom: solid #2a8040;
    }
    CogitatorHeader #header-bar {
        height: 3;
        width: 1fr;
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
        min-width: 10;
        width: auto;
        height: 3;
        margin: 0 0 0 1;
    }
    """

    def __init__(self, subtitle: str = "VEIL LINK STABLE") -> None:
        super().__init__()
        self._subtitle = subtitle

    def compose(self) -> ComposeResult:
        yield Static("", id="update-banner")
        with Horizontal(id="header-bar"):
            yield Static(
                f"MAGOS BIOLOGIS / COGITATOR-BIOGEN  |  {self._subtitle}",
                id="header-title",
            )
            with Horizontal(id="header-actions"):
                yield Button("Menu", id="hdr-menu")
                yield Button("Reload", id="hdr-reload")
                yield Button("Terminate", id="hdr-terminate")

    def show_status_banner(self, text: str, *, kind: str = "update") -> None:
        """kind: 'update' (amber) or 'current' (green)."""
        banner = self.query_one("#update-banner", Static)
        banner.update(text)
        banner.remove_class("-update", "-current")
        banner.add_class("-show", f"-{kind}" if kind in {"update", "current"} else "-update")

    def show_update_notice(self, text: str) -> None:
        self.show_status_banner(text, kind="update")

    def show_current_notice(self, text: str) -> None:
        self.show_status_banner(text, kind="current")

    def hide_update_notice(self) -> None:
        banner = self.query_one("#update-banner", Static)
        banner.remove_class("-show", "-update", "-current")
        banner.update("")

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
