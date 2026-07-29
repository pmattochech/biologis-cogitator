"""Pick a system (and later body) from a loaded pack."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Label, ListItem, ListView, Static

from ... import packs as packsmod
from ...wizard_session import WizardSession
from ..widgets.header import CogitatorHeader
from ..widgets.warn_log import WarnLog


class PackPickScreen(Screen):
    def __init__(self, pack_id: str) -> None:
        super().__init__()
        self.pack_id = pack_id

    def compose(self) -> ComposeResult:
        yield CogitatorHeader(f"PACK / {self.pack_id}")
        with VerticalScroll(id="main"):
            try:
                meta = packsmod.load_pack_meta(self.pack_id)
                desc = (meta.get("description") or "").strip()
            except FileNotFoundError:
                desc = ""
            yield Static(f"Pack: {self.pack_id}", classes="title")
            if desc:
                yield Static(desc, classes="litany")
            yield Label("Systems in pack — select then Load system:")
            yield ListView(id="sys-list")
            with Horizontal(classes="-toolbar"):
                yield Button("Load system (pinned)", id="btn-load", variant="primary")
                yield Button("Back", id="btn-back")
        yield WarnLog()

    def on_mount(self) -> None:
        self.query_one(WarnLog).boot()
        self._selected_sys: str | None = None
        lv = self.query_one("#sys-list", ListView)
        for slug in packsmod.list_system_slugs(self.pack_id):
            item = ListItem(Label(slug))
            item.sys_slug = slug  # type: ignore[attr-defined]
            lv.append(item)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        self._selected_sys = getattr(event.item, "sys_slug", None)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-back":
            self.app.request_back()  # type: ignore[attr-defined]
            return
        if event.button.id == "btn-load":
            slug = getattr(self, "_selected_sys", None)
            if not slug:
                lv = self.query_one("#sys-list", ListView)
                if lv.highlighted_child is not None:
                    slug = getattr(lv.highlighted_child, "sys_slug", None)
            if not slug:
                self.query_one(WarnLog).push("select a system")
                return
            session: WizardSession = self.app.session  # type: ignore[attr-defined]
            session.load_pack_system(slug, self.pack_id)
            self.query_one(WarnLog).push(f"loaded system '{slug}' from pack '{self.pack_id}'")
            from .system_flow import SystemFlowScreen

            self.app.push_screen(SystemFlowScreen())
