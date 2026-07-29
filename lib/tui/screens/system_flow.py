"""L-1 system flow — mode, star roll/pick/skip."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Label, Select, Static

from ...wizard_session import WizardSession
from ..widgets.header import CogitatorHeader
from ..widgets.warn_log import WarnLog


class SystemFlowScreen(Screen):
    TRACK_DIRTY = True

    def compose(self) -> ComposeResult:
        yield CogitatorHeader("LAYER L-1 / STELLAR RITE")
        with VerticalScroll(id="main"):
            yield Static("SYSTEM PARAMETERS", classes="title")
            yield Static(id="sys-summary", classes="panel")
            yield Label("System mode:")
            yield Select(
                [("natural", "natural"), ("engineered_mesh", "engineered_mesh")],
                id="mode-select",
                value="natural",
            )
            yield Label("Star spectral / size (for Pick):")
            with Horizontal():
                yield Select([], id="spectral-select")
                yield Select([], id="size-select")
            with Horizontal(classes="-toolbar"):
                yield Button("Roll star", id="btn-roll")
                yield Button("Pick star", id="btn-pick", variant="primary")
                yield Button("Skip star", id="btn-skip")
            with Horizontal(classes="-toolbar"):
                yield Button("Apply mode", id="btn-mode")
                yield Button("Continue to body →", id="btn-next", variant="primary")
                yield Button("Back", id="btn-back")
        yield WarnLog()

    def on_mount(self) -> None:
        log = self.query_one(WarnLog)
        log.boot()
        session: WizardSession = self.app.session  # type: ignore[attr-defined]
        spec = self.query_one("#spectral-select", Select)
        size = self.query_one("#size-select", Select)
        spec.set_options([(s, s) for s in session.star_spectrals()])
        size.set_options([(s, s) for s in session.star_sizes()])
        if session.star_spectrals():
            spec.value = session.star_spectrals()[0]
        if session.star_sizes():
            size.value = session.star_sizes()[0]
        mode = (session.system or {}).get("layers", {}).get("system_mode") or "natural"
        self.query_one("#mode-select", Select).value = mode
        self._refresh_summary()
        for w in session.warnings[-5:]:
            log.push(w)

    def _session(self) -> WizardSession:
        return self.app.session  # type: ignore[attr-defined]

    def _refresh_summary(self) -> None:
        s = self._session().system or {}
        layers = s.get("layers") or {}
        star = layers.get("star") or {}
        text = (
            f"Slug: {s.get('meta', {}).get('slug')}\n"
            f"Mode: {layers.get('system_mode')}\n"
            f"Star: {star.get('label') or star}\n"
            f"Body slots: {len(layers.get('body_slots') or [])}\n"
            f"Formations: {layers.get('formations')}"
        )
        self.query_one("#sys-summary", Static).update(text)

    def _flush_warns(self) -> None:
        log = self.query_one(WarnLog)
        session = self._session()
        # show latest system warnings
        for w in (session.system or {}).get("warnings") or []:
            if w not in session.warnings:
                session.warnings.append(w)
        if session.system and session.system.get("warnings"):
            log.push(session.system["warnings"][-1])

    def on_button_pressed(self, event: Button.Pressed) -> None:
        session = self._session()
        log = self.query_one(WarnLog)
        if event.button.id == "btn-back":
            self.app.request_back()  # type: ignore[attr-defined]
            return
        if event.button.id == "btn-mode":
            mode = str(self.query_one("#mode-select", Select).value)
            session.set_system_mode(mode)
            log.push(f"system_mode → {mode} ({session.provenance.get('system_mode')})")
            self._refresh_summary()
            return
        if event.button.id == "btn-roll":
            star = session.roll_system_star()
            log.push(f"rolled star {star.get('label')} ({session.provenance.get('star')})")
            self._flush_warns()
            self._refresh_summary()
            return
        if event.button.id == "btn-pick":
            spectral = str(self.query_one("#spectral-select", Select).value)
            size_band = str(self.query_one("#size-select", Select).value)
            star = session.pick_system_star(spectral, size_band)
            log.push(f"picked star {star.get('label')} ({session.provenance.get('star')})")
            self._flush_warns()
            self._refresh_summary()
            return
        if event.button.id == "btn-skip":
            star = session.skip_system_star()
            log.push(f"skipped star keep {star.get('label')}")
            self._refresh_summary()
            return
        if event.button.id == "btn-next":
            session.save_system_out()
            from .body_flow import BodyFlowScreen

            self.app.push_screen(BodyFlowScreen())
