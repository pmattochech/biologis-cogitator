"""Boot screen — choose Registration, Amendment, or Consultation."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Static

from ..widgets.header import CogitatorHeader
from ..widgets.warn_log import WarnLog


class BootScreen(Screen):
    """Root rite chooser — three doors, then Abort."""

    BINDINGS = [("q", "request_terminate", "Terminate")]

    def compose(self) -> ComposeResult:
        yield CogitatorHeader("AWAITING RITE SELECTION")
        with VerticalScroll(id="main"):
            yield Static("CASUS BIOGENESIS — CHOOSE YOUR RITE", classes="title")
            yield Static(
                "Three rites stand before the Magos Biologis. "
                "Register new mesh work, amend what already exists, "
                "or consult the sealed archive.",
                classes="litany",
            )
            with Horizontal(classes="-toolbar rite-doors"):
                yield Button(
                    "Rite of Registration",
                    id="btn-registration",
                    variant="primary",
                    classes="rite-door",
                )
                yield Button(
                    "Rite of Amendment",
                    id="btn-amendment",
                    classes="rite-door",
                )
                yield Button(
                    "Rite of Consultation",
                    id="btn-consultation",
                    classes="rite-door",
                )
        yield WarnLog()

    def on_mount(self) -> None:
        self.query_one(WarnLog).boot()

    def action_request_terminate(self) -> None:
        self.app.request_terminate()  # type: ignore[attr-defined]

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "btn-registration":
            from .registration import RegistrationScreen

            self.app.push_screen(RegistrationScreen())
            return
        if bid == "btn-amendment":
            from .edit_pick import EditPickScreen

            self.app.push_screen(EditPickScreen())
            return
        if bid == "btn-consultation":
            from .out_archive import OutArchiveScreen

            self.app.push_screen(OutArchiveScreen())
            return
