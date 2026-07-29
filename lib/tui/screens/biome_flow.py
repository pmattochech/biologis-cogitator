"""Explicit biomes step — add instances, register new classes, roll / skip."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Input, Label, ListItem, ListView, Select, Static

from ... import custom_enums
from ...wizard_session import WizardSession
from ..widgets.header import CogitatorHeader
from ..widgets.warn_log import WarnLog


class BiomeFlowScreen(Screen):
    TRACK_DIRTY = True

    CSS = """
    #class-row { height: 3; }
    #new-class-row { height: 3; }
    """

    def compose(self) -> ComposeResult:
        yield CogitatorHeader("LAYER L4 / BIOMES")
        with VerticalScroll(id="main"):
            yield Static("BIOSPHERE — BIOME RITE", classes="title")
            yield Static(
                "Add biomes onto this body (auto filing id AAAA-BBB). "
                "Register a new class if the dropdown does not have it yet.",
                classes="litany",
            )
            yield Static(id="biome-summary", classes="panel")
            yield Label("Current biomes on this body:")
            yield ListView(id="biome-list")
            yield Label("Add existing class / richness:")
            with Horizontal(id="class-row"):
                yield Select([], id="class-select")
                yield Select([], id="rich-select")
            with Horizontal(classes="-toolbar"):
                yield Button("Add biome", id="btn-add", variant="primary")
                yield Button("Remove selected", id="btn-remove")
            yield Label("Register new biome class:")
            yield Input(placeholder="class id e.g. needle_estuary", id="new-class-id")
            with Horizontal(id="new-class-row"):
                yield Select(
                    [
                        ("terrestrial", "terrestrial"),
                        ("marine", "marine"),
                        ("freshwater", "freshwater"),
                        ("aerial", "aerial"),
                        ("subterranean", "subterranean"),
                        ("industrial_void", "industrial_void"),
                    ],
                    id="new-medium",
                    allow_blank=False,
                )
                yield Select(
                    [(r, r) for r in ("null", "barren", "sparse", "moderate", "rich")],
                    id="new-rich",
                    allow_blank=False,
                )
            with Horizontal(classes="-toolbar"):
                yield Button("Register class", id="btn-register")
                yield Button("Register + add to body", id="btn-register-add", variant="primary")
            with Horizontal(classes="-toolbar"):
                yield Button("Roll biomes", id="btn-roll")
                yield Button("Skip biomes", id="btn-skip")
            with Horizontal(classes="-toolbar"):
                yield Button("Continue →", id="btn-next", variant="primary")
                yield Button("Back", id="btn-back")
        yield WarnLog()

    def on_mount(self) -> None:
        log = self.query_one(WarnLog)
        log.boot()
        self._selected_biome: str | None = None
        self.query_one("#new-medium", Select).value = "terrestrial"
        self.query_one("#new-rich", Select).value = "moderate"
        self._reload_class_select()
        self._refresh()

    def _session(self) -> WizardSession:
        return self.app.session  # type: ignore[attr-defined]

    def _reload_class_select(self, *, prefer: str | None = None) -> None:
        session = self._session()
        classes = session.list_biome_classes()
        sel = self.query_one("#class-select", Select)
        sel.set_options([(c, c) for c in classes] or [("—", "")])
        pick = prefer if prefer in classes else (classes[0] if classes else None)
        if pick:
            sel.value = pick
        rich = session.list_richness()
        rsel = self.query_one("#rich-select", Select)
        rsel.set_options([(r, r) for r in rich])
        if "moderate" in rich:
            rsel.value = "moderate"

    def _refresh(self) -> None:
        session = self._session()
        biomes = session.current_biomes()
        text = (
            f"Body: {(session.body or {}).get('meta', {}).get('slug')} "
            f"[{(session.body or {}).get('meta', {}).get('filing_id') or '—'}]\n"
            f"Provenance: {session.provenance.get('biomes', '—')}\n"
            f"Count: {len(biomes)}"
        )
        self.query_one("#biome-summary", Static).update(text)
        lv = self.query_one("#biome-list", ListView)
        lv.clear()
        for b in biomes:
            fid = b.get("filing_id") or ""
            label = (
                f"{fid + ' · ' if fid else ''}{b.get('id')} — "
                f"{b.get('class')} ({b.get('richness')})"
            )
            item = ListItem(Label(label))
            item.biome_id = b.get("id")  # type: ignore[attr-defined]
            lv.append(item)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        self._selected_biome = getattr(event.item, "biome_id", None)

    def _register_class(self) -> str:
        session = self._session()
        cid = self.query_one("#new-class-id", Input).value.strip()
        if not cid:
            raise ValueError("enter a new class id first")
        medium = str(self.query_one("#new-medium", Select).value)
        rich = str(self.query_one("#new-rich", Select).value)
        entry = custom_enums.register_biome_class(
            cid,
            medium=medium,
            default_richness=rich,
            pack_id=session.pack_id,
        )
        return str(entry.get("id") or cid)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        session = self._session()
        log = self.query_one(WarnLog)
        if event.button.id == "btn-back":
            self.app.request_back()  # type: ignore[attr-defined]
            return
        if event.button.id in ("btn-register", "btn-register-add"):
            try:
                cid = self._register_class()
            except Exception as exc:
                log.push(str(exc))
                return
            where = f"pack '{session.pack_id}'" if session.pack_id else "global enums"
            log.push(f"registered biome class '{cid}' → {where}")
            self._reload_class_select(prefer=cid)
            if event.button.id == "btn-register-add":
                if session.body is None:
                    log.push("init a body first to add the biome instance")
                    return
                rich = str(self.query_one("#new-rich", Select).value)
                entry = session.add_biome(cid, rich)
                log.push(
                    f"added {entry.get('filing_id') or entry.get('id')} "
                    f"({session.provenance.get('biomes')})"
                )
                self._refresh()
            return
        if session.body is None:
            log.push("no body — go back and init")
            return
        if event.button.id == "btn-add":
            class_id = str(self.query_one("#class-select", Select).value)
            if not class_id or class_id == "—":
                log.push("select a class or register a new one")
                return
            richness = str(self.query_one("#rich-select", Select).value)
            entry = session.add_biome(class_id, richness)
            log.push(
                f"added {entry.get('filing_id') or entry.get('id')} "
                f"({session.provenance.get('biomes')})"
            )
            self._refresh()
            return
        if event.button.id == "btn-remove":
            biome_id = self._selected_biome
            if not biome_id:
                lv = self.query_one("#biome-list", ListView)
                if lv.highlighted_child is not None:
                    biome_id = getattr(lv.highlighted_child, "biome_id", None)
            if not biome_id:
                log.push("select a biome to remove")
                return
            session.remove_biome(biome_id)
            log.push(f"removed biome {biome_id}")
            self._refresh()
            return
        if event.button.id == "btn-roll":
            biomes = session.roll_biomes()
            log.push(f"rolled {len(biomes)} biomes ({session.provenance.get('biomes')})")
            self._refresh()
            return
        if event.button.id == "btn-skip":
            session.skip_biomes()
            log.push(f"skipped biomes — keep {len(session.current_biomes())}")
            self._refresh()
            return
        if event.button.id == "btn-next":
            from .edit_hub import EditHubScreen
            from .review import ReviewScreen

            if any(isinstance(s, EditHubScreen) for s in self.app.screen_stack):
                self.app.pop_screen()
            else:
                self.app.push_screen(ReviewScreen())
