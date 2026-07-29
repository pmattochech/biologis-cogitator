"""Rite of Registration — begin new mesh work (greenfield, biosphere, template)."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Input, Label, ListItem, ListView, Static

from ... import packs as packsmod
from ...wizard_session import WizardSession
from ..widgets.header import CogitatorHeader
from ..widgets.warn_log import WarnLog


class RegistrationScreen(Screen):
    """Chooser for how a registration rite begins."""

    BINDINGS = [("escape", "go_back", "Return")]

    def compose(self) -> ComposeResult:
        yield CogitatorHeader("RITE OF REGISTRATION")
        with VerticalScroll(id="main"):
            yield Static("RITE OF REGISTRATION — BEGIN", classes="title")
            yield Static(
                "Inscribe a new spine into the mesh, attach a biosphere to a known "
                "system, or invoke a pack as template litany. "
                "Species and biomes upon an existing body are registered under "
                "the Rite of Amendment.",
                classes="litany",
            )
            with Horizontal(classes="-toolbar"):
                yield Button(
                    "Register stellar system",
                    id="btn-system",
                    variant="primary",
                )
                yield Button(
                    "Register biosphere upon known system",
                    id="btn-biosphere",
                )
                yield Button(
                    "Invoke template litany",
                    id="btn-template",
                )
                yield Button("Return", id="btn-back")
            yield Label("System slug (stellar registration):")
            yield Input(value="new-system", id="slug-input")
            yield Label("Pack templates (invoke litany):")
            yield ListView(id="pack-list")
        yield WarnLog()

    def on_mount(self) -> None:
        self.query_one(WarnLog).boot()
        lv = self.query_one("#pack-list", ListView)
        for meta in packsmod.list_packs():
            title = meta.get("title") or meta.get("id")
            item = ListItem(Label(f"{meta.get('id')} — {title}"))
            item.pack_id = meta.get("id")  # type: ignore[attr-defined]
            lv.append(item)
        self._selected_pack: str | None = None

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        self._selected_pack = getattr(event.item, "pack_id", None)

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def _selected_pack_id(self) -> str | None:
        pack_id = getattr(self, "_selected_pack", None)
        if pack_id:
            return pack_id
        lv = self.query_one("#pack-list", ListView)
        if lv.highlighted_child is not None:
            return getattr(lv.highlighted_child, "pack_id", None)
        return None

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        warn = self.query_one(WarnLog)
        if bid == "btn-back":
            self.app.pop_screen()
            return
        if bid == "btn-system":
            slug = self.query_one("#slug-input", Input).value.strip() or "new-system"
            session: WizardSession = self.app.session  # type: ignore[attr-defined]
            session.start_greenfield_system(slug, mode="natural")
            warn.push(f"stellar registration '{slug}' initialized")
            from .system_flow import SystemFlowScreen

            self.app.push_screen(SystemFlowScreen())
            return
        if bid == "btn-biosphere":
            from .system_pick import SystemPickScreen

            self.app.push_screen(SystemPickScreen())
            return
        if bid == "btn-template":
            pack_id = self._selected_pack_id()
            if not pack_id:
                warn.push("select a pack template from the list first")
                return
            from .pack_pick import PackPickScreen

            warn.push(f"invoking template litany '{pack_id}'")
            self.app.push_screen(PackPickScreen(pack_id=pack_id))
            return
