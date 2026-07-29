"""Pick an existing system for biosphere-only path."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Label, ListItem, ListView, Select, Static

from ... import packs as packsmod
from ...wizard_session import WizardSession
from ..widgets.header import CogitatorHeader
from ..widgets.warn_log import WarnLog


class SystemPickScreen(Screen):
    """Load system from results/ or from a pack, then jump to BodyFlow."""

    def compose(self) -> ComposeResult:
        yield CogitatorHeader("BIOSPHERE ONLY / SELECT SYSTEM")
        with VerticalScroll(id="main"):
            yield Static("ATTACH TO EXISTING SYSTEM", classes="title")
            yield Static(
                "Skip stellar rite. Load a system from sealed results or a pack, then shape the biosphere.",
                classes="litany",
            )
            yield Label("Systems in results:")
            yield ListView(id="out-sys-list")
            yield Label("Or pack + pack system:")
            yield Select([], id="pack-select")
            yield ListView(id="pack-sys-list")
            with Horizontal(classes="-toolbar"):
                yield Button("Load from results", id="btn-out", variant="primary")
                yield Button("Load from pack", id="btn-pack")
                yield Button("Back", id="btn-back")
        yield WarnLog()

    def on_mount(self) -> None:
        self.query_one(WarnLog).boot()
        self._selected_out: str | None = None
        self._selected_pack_sys: str | None = None
        lv = self.query_one("#out-sys-list", ListView)
        for slug in WizardSession.list_out_systems():
            item = ListItem(Label(slug))
            item.sys_slug = slug  # type: ignore[attr-defined]
            lv.append(item)
        packs = packsmod.list_packs()
        sel = self.query_one("#pack-select", Select)
        opts = [(p.get("id"), p.get("id")) for p in packs if p.get("id")]
        sel.set_options(opts)
        if opts:
            sel.value = opts[0][0]
            self._reload_pack_systems(str(opts[0][0]))

    def _reload_pack_systems(self, pack_id: str) -> None:
        lv = self.query_one("#pack-sys-list", ListView)
        lv.clear()
        for slug in packsmod.list_system_slugs(pack_id):
            item = ListItem(Label(slug))
            item.sys_slug = slug  # type: ignore[attr-defined]
            lv.append(item)

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "pack-select" and event.value is not Select.BLANK:
            self._reload_pack_systems(str(event.value))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        slug = getattr(event.item, "sys_slug", None)
        if event.list_view.id == "out-sys-list":
            self._selected_out = slug
        elif event.list_view.id == "pack-sys-list":
            self._selected_pack_sys = slug

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        item = event.item
        if item is None:
            return
        slug = getattr(item, "sys_slug", None)
        if not slug:
            return
        # Track whichever list currently holds highlight
        try:
            if event.list_view.id == "out-sys-list":
                self._selected_out = slug
            elif event.list_view.id == "pack-sys-list":
                self._selected_pack_sys = slug
        except Exception:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        session: WizardSession = self.app.session  # type: ignore[attr-defined]
        log = self.query_one(WarnLog)
        if event.button.id == "btn-back":
            self.app.request_back()  # type: ignore[attr-defined]
            return
        if event.button.id == "btn-out":
            slug = self._selected_out
            if not slug:
                lv = self.query_one("#out-sys-list", ListView)
                if lv.highlighted_child is not None:
                    slug = getattr(lv.highlighted_child, "sys_slug", None)
            if not slug:
                log.push("select a system from results/")
                return
            try:
                system = session.load_system_from_out(slug)
            except FileNotFoundError as exc:
                log.push(str(exc))
                return
            slots = (system.get("layers") or {}).get("body_slots") or (
                system.get("locks") or {}
            ).get("bodies") or []
            log.push(
                f"loaded system '{slug}' from results/ "
                f"({len(slots)} body slot(s)) — continuing to body rite"
            )
            from .body_flow import BodyFlowScreen

            self.app.push_screen(BodyFlowScreen())
            return
        if event.button.id == "btn-pack":
            pack_sel = self.query_one("#pack-select", Select)
            pack_id = str(pack_sel.value) if pack_sel.value is not Select.BLANK else None
            slug = self._selected_pack_sys
            if not slug:
                lv = self.query_one("#pack-sys-list", ListView)
                if lv.highlighted_child is not None:
                    slug = getattr(lv.highlighted_child, "sys_slug", None)
            if not pack_id or not slug:
                log.push("select pack and system")
                return
            system = session.load_pack_system(slug, pack_id)
            slots = (system.get("layers") or {}).get("body_slots") or (
                system.get("locks") or {}
            ).get("bodies") or []
            log.push(
                f"loaded system '{slug}' from pack '{pack_id}' "
                f"({len(slots)} body slot(s)) — continuing to body rite"
            )
            from .body_flow import BodyFlowScreen

            self.app.push_screen(BodyFlowScreen())
