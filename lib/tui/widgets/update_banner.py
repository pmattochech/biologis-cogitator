"""Docket update notice (legacy helper — prefer CogitatorHeader.show_update_notice)."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static


class UpdateBanner(Widget):
    """Upper-app notice when a newer git revision is available on the remote."""

    DEFAULT_CSS = """
    UpdateBanner {
        dock: top;
        width: 1fr;
        height: auto;
        display: none;
        background: #3a2010;
        color: #ffd080;
        border: heavy #c07020;
        padding: 0 1;
        text-style: bold;
    }
    UpdateBanner.-show {
        display: block;
        height: auto;
        min-height: 3;
        max-height: 5;
    }
    UpdateBanner #update-banner-text {
        width: 1fr;
        height: auto;
        color: #ffd080;
        text-style: bold;
        padding: 1 0;
    }
    """

    visible_notice = reactive(False, layout=True)

    def compose(self) -> ComposeResult:
        yield Static("", id="update-banner-text")

    def show_update(self, text: str) -> None:
        self.query_one("#update-banner-text", Static).update(text)
        self.visible_notice = True
        self.add_class("-show")

    def hide_update(self) -> None:
        self.visible_notice = False
        self.remove_class("-show")
        try:
            self.query_one("#update-banner-text", Static).update("")
        except Exception:
            pass
