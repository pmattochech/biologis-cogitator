"""Modal: unsaved changes — Save / Don't save / Cancel."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static


class ConfirmDirtyScreen(ModalScreen[str]):
    """Return 'save' | 'discard' | 'cancel'."""

    CSS = """
    ConfirmDirtyScreen {
        align: center middle;
    }
    #dirty-box {
        width: 72;
        height: auto;
        border: heavy #40c070;
        background: #0a1810;
        padding: 1 2;
    }
    #dirty-box Static {
        height: auto;
        margin-bottom: 1;
        color: #b8ffd0;
    }
    #dirty-actions {
        height: 3;
        align: center middle;
    }
    #dirty-actions Button {
        margin: 0 1;
        min-width: 14;
    }
    """

    def __init__(self, *, message: str | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self._message = message or (
            "Unsaved changes detected. Save before continuing?"
        )

    def compose(self) -> ComposeResult:
        with Vertical(id="dirty-box"):
            yield Static("WARNING / UNSAVED CHANGES", classes="title")
            yield Static(self._message)
            with Horizontal(id="dirty-actions"):
                yield Button("Save", id="btn-save", variant="primary")
                yield Button("Don't save", id="btn-discard")
                yield Button("Cancel", id="btn-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-save":
            self.dismiss("save")
        elif event.button.id == "btn-discard":
            self.dismiss("discard")
        else:
            self.dismiss("cancel")
