"""Boot screen — Registration, Amendment, or Consultation (dossiers)."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Static

from ..features import CONSULTATION_ENABLED
from ..widgets.header import CogitatorHeader
from ..widgets.warn_log import WarnLog


class BootScreen(Screen):
    """Root rite chooser — three doors when Consultation is enabled."""

    BINDINGS = [("q", "request_terminate", "Terminate")]

    def compose(self) -> ComposeResult:
        yield CogitatorHeader("AWAITING RITE SELECTION")
        with VerticalScroll(id="main"):
            yield Static("CASUS BIOGENESIS — CHOOSE YOUR RITE", classes="title")
            yield Static(
                "Three rites stand before the Magos Biologis. "
                "Register new mesh work, amend what already exists, "
                "or consult sealed dossiers (read-only object pages).",
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
                    "Rite of Consultation"
                    if CONSULTATION_ENABLED
                    else "Consultation (offline)",
                    id="btn-consultation",
                    classes="rite-door",
                    disabled=not CONSULTATION_ENABLED,
                )
            with Horizontal(classes="-toolbar"):
                yield Button("Build channel", id="btn-channel")
            yield Static(id="boot-channel", classes="litany")
        yield WarnLog()

    def on_mount(self) -> None:
        self.query_one(WarnLog).boot()
        self._show_channel_hint()

    def _show_channel_hint(self) -> None:
        try:
            from ... import update as updatemod

            ref = updatemod.update_ref()
            src = updatemod.ref_source()
            self.query_one("#boot-channel", Static).update(
                f"Build channel: {ref} ({src})"
            )
        except Exception:
            pass

    def on_screen_resume(self) -> None:
        self._show_channel_hint()

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
            log = self.query_one(WarnLog)
            if not CONSULTATION_ENABLED:
                log.push(
                    "Consultation offline. Use Rite of Amendment to inspect work."
                )
                return
            from .dossier_browser import DossierBrowserScreen

            self.app.push_screen(DossierBrowserScreen())
            return
        if bid == "btn-channel":
            from .channel import ChannelScreen

            self.app.push_screen(ChannelScreen())
            return
