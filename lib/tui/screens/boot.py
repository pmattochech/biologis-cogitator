"""Boot screen — greenfield or load pack."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Input, Label, ListItem, ListView, Static

from ... import packs as packsmod
from ...wizard_session import WizardSession
from ..widgets.header import CogitatorHeader
from ..widgets.warn_log import WarnLog


class BootScreen(Screen):
    BINDINGS = [("q", "request_terminate", "Terminate")]

    def compose(self) -> ComposeResult:
        yield CogitatorHeader("AWAITING RITE SELECTION")
        with VerticalScroll(id="main"):
            yield Static("CASUS BIOGENESIS — INITIATE", classes="title")
            yield Static(
                "The Emperor dictates, we comply. Greenfield, biosphere-only, load pack, edit body, or browse results.",
                classes="litany",
            )
            with Horizontal(classes="-toolbar"):
                yield Button("New system (greenfield)", id="btn-green", variant="primary")
                yield Button("Biosphere only", id="btn-bio")
                yield Button("Load pack", id="btn-pack")
                yield Button("Edit body", id="btn-edit")
                yield Button("Browse results", id="btn-archive")
                yield Button("Abort", id="btn-abort")
            yield Label("System slug (greenfield):")
            yield Input(value="new-system", id="slug-input")
            yield Label("Packs available:")
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

    def action_request_terminate(self) -> None:
        self.app.request_terminate()  # type: ignore[attr-defined]

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-abort":
            self.app.request_terminate()  # type: ignore[attr-defined]
            return
        if event.button.id == "btn-green":
            slug = self.query_one("#slug-input", Input).value.strip() or "new-system"
            session: WizardSession = self.app.session  # type: ignore[attr-defined]
            session.start_greenfield_system(slug, mode="natural")
            self.query_one(WarnLog).push(f"greenfield system '{slug}' initialized")
            from .system_flow import SystemFlowScreen

            self.app.push_screen(SystemFlowScreen())
            return
        if event.button.id == "btn-bio":
            from .system_pick import SystemPickScreen

            self.app.push_screen(SystemPickScreen())
            return
        if event.button.id == "btn-archive":
            from .out_archive import OutArchiveScreen

            self.app.push_screen(OutArchiveScreen())
            return
        if event.button.id == "btn-edit":
            from .edit_pick import EditPickScreen

            self.app.push_screen(EditPickScreen())
            return
        if event.button.id == "btn-pack":
            pack_id = getattr(self, "_selected_pack", None)
            if not pack_id:
                # fallback: highlighted index
                lv = self.query_one("#pack-list", ListView)
                if lv.highlighted_child is not None:
                    pack_id = getattr(lv.highlighted_child, "pack_id", None)
            if not pack_id:
                self.query_one(WarnLog).push("select a pack from the list first")
                return
            from .pack_pick import PackPickScreen

            self.app.push_screen(PackPickScreen(pack_id=pack_id))
