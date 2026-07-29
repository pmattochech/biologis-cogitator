"""Pack-local custom tags + promote to global enums."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Input, Label, ListItem, ListView, Select, Static

from ... import custom_enums
from ...wizard_session import WizardSession
from ..widgets.header import CogitatorHeader
from ..widgets.warn_log import WarnLog


class EditTagsScreen(Screen):
    TRACK_DIRTY = True

    CSS = """
    #tags-main { height: 1fr; padding: 0 1; }
    #tags-toolbar { height: 3; }
    #tags-toolbar Button { margin: 0 1 0 0; min-width: 10; height: 3; }
    #custom-list { height: 10; border: solid #8a6a20; }
    """

    def compose(self) -> ComposeResult:
        yield CogitatorHeader("EDITOR / CUSTOM TAGS")
        with Vertical(id="tags-main"):
            with Horizontal(id="tags-toolbar"):
                yield Button("Add biome class", id="btn-add-biome", variant="primary")
                yield Button("Add planet type", id="btn-add-pt")
                yield Button("Promote selected", id="btn-promote")
                yield Button("Back", id="btn-back")
            yield Static(id="pack-hint", classes="litany")
            yield Label("Pack-local biome classes / planet types")
            yield ListView(id="custom-list")
            with VerticalScroll():
                yield Label("New biome class id")
                yield Input(id="biome-id")
                yield Label("medium")
                yield Select(
                    [
                        ("terrestrial", "terrestrial"),
                        ("marine", "marine"),
                        ("freshwater", "freshwater"),
                        ("aerial", "aerial"),
                        ("subterranean", "subterranean"),
                        ("industrial_void", "industrial_void"),
                    ],
                    id="biome-medium",
                    allow_blank=False,
                )
                yield Label("default_richness")
                yield Select(
                    [(r, r) for r in ("null", "barren", "sparse", "moderate", "rich")],
                    id="biome-rich",
                    allow_blank=False,
                )
                yield Label("New planet_type id")
                yield Input(id="planet-type-id")
        yield WarnLog()

    def on_mount(self) -> None:
        self.query_one(WarnLog).boot()
        self.query_one("#biome-medium", Select).value = "terrestrial"
        self.query_one("#biome-rich", Select).value = "moderate"
        self._selected_kind: str | None = None
        self._selected_id: str | None = None
        self._reload()

    def _session(self) -> WizardSession:
        return self.app.session  # type: ignore[attr-defined]

    def _pack(self) -> str | None:
        return self._session().pack_id

    def _reload(self) -> None:
        pack = self._pack()
        self.query_one("#pack-hint", Static).update(
            f"Active pack: {pack or '(none — set pack on Edit hub before adding tags)'}"
        )
        lv = self.query_one("#custom-list", ListView)
        lv.clear()
        if not pack:
            return
        data = custom_enums.load_custom_enums(pack)
        for c in data.get("biome_classes") or []:
            cid = c.get("id")
            item = ListItem(Label(f"biome_class: {cid}"))
            item.tag_kind = "biome_class"  # type: ignore[attr-defined]
            item.tag_id = cid  # type: ignore[attr-defined]
            lv.append(item)
        for p in data.get("planet_types") or []:
            item = ListItem(Label(f"planet_type: {p}"))
            item.tag_kind = "planet_type"  # type: ignore[attr-defined]
            item.tag_id = p  # type: ignore[attr-defined]
            lv.append(item)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        self._selected_kind = getattr(event.item, "tag_kind", None)
        self._selected_id = getattr(event.item, "tag_id", None)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        log = self.query_one(WarnLog)
        pack = self._pack()
        if event.button.id == "btn-back":
            self.app.request_back()  # type: ignore[attr-defined]
            return
        if not pack and event.button.id != "btn-back":
            log.push("set pack_id on Edit hub / load from pack first")
            return
        if event.button.id == "btn-add-biome":
            cid = self.query_one("#biome-id", Input).value.strip()
            if not cid:
                log.push("biome id required")
                return
            custom_enums.add_custom_biome_class(
                {
                    "id": cid,
                    "medium": str(self.query_one("#biome-medium", Select).value),
                    "overlay": False,
                    "default_richness": str(self.query_one("#biome-rich", Select).value),
                    "note": "pack-local",
                },
                pack,
            )
            log.push(f"added pack biome class {cid}")
            self._reload()
            return
        if event.button.id == "btn-add-pt":
            pt = self.query_one("#planet-type-id", Input).value.strip()
            if not pt:
                log.push("planet_type required")
                return
            custom_enums.add_custom_planet_type(pt, pack)
            log.push(f"added pack planet_type {pt}")
            self._reload()
            return
        if event.button.id == "btn-promote":
            if not self._selected_kind or not self._selected_id:
                log.push("select a pack-local tag first")
                return
            try:
                if self._selected_kind == "biome_class":
                    custom_enums.promote_biome_class(self._selected_id, pack)
                else:
                    custom_enums.promote_planet_type(self._selected_id, pack)
                log.push(f"promoted {self._selected_kind} {self._selected_id} → global enums")
                self._reload()
            except Exception as exc:
                log.push(str(exc))
