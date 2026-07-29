"""Body flow — choose slug, roll layers, pick planet type / immaterium."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Input, Label, ListItem, ListView, Select, Static

from ... import out_archive as archive
from ... import packs as packsmod
from ... import state as statemod
from ...wizard_session import WizardSession
from ..widgets.header import CogitatorHeader
from ..widgets.warn_log import WarnLog


class BodyFlowScreen(Screen):
    TRACK_DIRTY = True

    CSS = """
    #body-list { height: 10; max-height: 12; }
    #ptype-row { height: 3; }
    #stress-row { height: 3; margin-bottom: 1; }
    #sys-attach { height: auto; }
    """

    def compose(self) -> ComposeResult:
        yield CogitatorHeader("LAYERS L1–L6 / BIOSPHERE RITE")
        with VerticalScroll(id="main"):
            yield Static("BODY SELECTION", classes="title")
            yield Static(id="sys-attach", classes="panel")
            yield Label("Body slug (create or listed body):")
            yield Input(value="new-world", id="body-slug")
            yield Label("Bodies for this system (slots / sealed / pack):")
            yield ListView(id="body-list")
            with Horizontal(classes="-toolbar"):
                yield Button("Init body", id="btn-init", variant="primary")
                yield Button("Use listed body", id="btn-listed")
            yield Static(id="body-summary", classes="panel")
            yield Label("Planet type / body kind:")
            with Horizontal(id="ptype-row"):
                yield Select([], id="ptype-select")
                yield Select([], id="bkind-select")
            yield Label("Immaterium stress:")
            with Horizontal(id="stress-row"):
                yield Select([], id="stress-select")
            with Horizontal(classes="-toolbar"):
                yield Button("Pick planet type", id="btn-ptype")
                yield Button("Pick stress", id="btn-stress")
                yield Button("Reroll layers", id="btn-reroll")
            with Horizontal(classes="-toolbar"):
                yield Button("Continue to biomes →", id="btn-next", variant="primary")
                yield Button("Back", id="btn-back")
        yield WarnLog()

    def on_mount(self) -> None:
        log = self.query_one(WarnLog)
        log.boot()
        session = self._session()
        self.query_one("#ptype-select", Select).set_options(
            [(t, t) for t in session.planet_types()]
        )
        self.query_one("#bkind-select", Select).set_options(
            [(t, t) for t in session.body_kinds()]
        )
        self.query_one("#stress-select", Select).set_options(
            [(t, t) for t in session.immaterium_grades()]
        )
        if session.planet_types():
            self.query_one("#ptype-select", Select).value = session.planet_types()[0]
        if session.body_kinds():
            self.query_one("#bkind-select", Select).value = "planet"
        if session.immaterium_grades():
            self.query_one("#stress-select", Select).value = "neutral"

        self._selected_body: str | None = None
        self._refresh_system_panel()
        self._reload_body_list()
        self._refresh()
        if session.system is None:
            log.push("no system attached — go back and load a system first")
        else:
            slug = (session.system.get("meta") or {}).get("slug")
            log.push(f"system attached: {slug}")

    def _session(self) -> WizardSession:
        return self.app.session  # type: ignore[attr-defined]

    def _system_slug(self) -> str | None:
        sys = self._session().system
        if not sys:
            return None
        return str((sys.get("meta") or {}).get("slug") or "") or None

    def _candidate_body_slugs(self) -> list[tuple[str, str]]:
        """Return (slug, source_tag) for the body list."""
        session = self._session()
        sys_slug = self._system_slug()
        seen: set[str] = set()
        out: list[tuple[str, str]] = []

        def _add(slug: str, tag: str) -> None:
            s = str(slug or "").strip()
            if not s or s in seen:
                return
            seen.add(s)
            out.append((s, tag))

        # 1) System body slots / locked bodies
        if session.system:
            layers = session.system.get("layers") or {}
            locks = session.system.get("locks") or {}
            for slot in layers.get("body_slots") or locks.get("bodies") or []:
                if isinstance(slot, dict):
                    _add(str(slot.get("slug") or ""), "slot")
                else:
                    _add(str(slot), "slot")

        # 2) Sealed results bodies belonging to this system
        if sys_slug:
            for body_slug in archive.list_out_bodies():
                try:
                    world = statemod.load_world(body_slug)
                except Exception:
                    continue
                if (world.get("meta") or {}).get("system_slug") == sys_slug:
                    _add(body_slug, "sealed")

        # 3) Pack body locks (if a pack is active)
        if session.pack_id:
            for body_slug in packsmod.list_body_slugs(session.pack_id):
                _add(body_slug, "pack")

        return out

    def _refresh_system_panel(self) -> None:
        session = self._session()
        sys = session.system
        panel = self.query_one("#sys-attach", Static)
        if not sys:
            panel.update(
                "No system attached.\n"
                "Biosphere-only: go Back and Load a system from results/pack first."
            )
            return
        meta = sys.get("meta") or {}
        layers = sys.get("layers") or {}
        star = layers.get("star") or (sys.get("locks") or {}).get("star") or {}
        if isinstance(star, dict):
            star_label = star.get("label") or f"{star.get('spectral')}-{star.get('size_band')}"
        else:
            star_label = str(star)
        slots = layers.get("body_slots") or (sys.get("locks") or {}).get("bodies") or []
        panel.update(
            f"Attached system: {meta.get('slug')}\n"
            f"Mode: {layers.get('system_mode') or (sys.get('locks') or {}).get('system_mode')}\n"
            f"Star: {star_label}\n"
            f"Body slots: {len(slots)}  |  Pack: {session.pack_id or '(none — using slots/sealed)'}"
        )

    def _reload_body_list(self) -> None:
        lv = self.query_one("#body-list", ListView)
        lv.clear()
        candidates = self._candidate_body_slugs()
        for slug, tag in candidates:
            item = ListItem(Label(f"{slug}  [{tag}]"))
            item.body_slug = slug  # type: ignore[attr-defined]
            lv.append(item)
        if candidates:
            self.query_one("#body-slug", Input).value = candidates[0][0]
            self._selected_body = candidates[0][0]
            try:
                lv.index = 0
            except Exception:
                pass

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        slug = getattr(event.item, "body_slug", None)
        if slug:
            self._selected_body = str(slug)
            self.query_one("#body-slug", Input).value = str(slug)

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        item = event.item
        if item is None:
            return
        slug = getattr(item, "body_slug", None)
        if slug:
            self._selected_body = str(slug)

    def _refresh(self) -> None:
        body = self._session().body
        if not body:
            self.query_one("#body-summary", Static).update(
                "No body initialized yet — pick a listed body or type a slug, then Init / Use listed."
            )
            return
        layers = body.get("layers") or {}
        pt = layers.get("planet_type") or {}
        chem = layers.get("chemistry_climate") or {}
        biomes = layers.get("biomes") or []
        text = (
            f"Slug: {body['meta']['slug']}\n"
            f"Filing ID: {body.get('meta', {}).get('filing_id') or (body.get('locks') or {}).get('filing_id') or '—'}\n"
            f"Planet type: {pt.get('planet_type')} ({pt.get('body_kind')})\n"
            f"Immaterium: {chem.get('immaterium_stress')}\n"
            f"Biomes: {len(biomes)} — {[b.get('id') for b in biomes]}\n"
            f"Warnings: {len(body.get('warnings') or [])}"
        )
        self.query_one("#body-summary", Static).update(text)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        session = self._session()
        log = self.query_one(WarnLog)
        if event.button.id == "btn-back":
            self.app.request_back()  # type: ignore[attr-defined]
            return
        if session.system is None and event.button.id in (
            "btn-init",
            "btn-listed",
            "btn-ptype",
            "btn-stress",
            "btn-reroll",
            "btn-next",
        ):
            log.push("no system attached — load a system first (Biosphere only / pack)")
            return
        if event.button.id == "btn-listed":
            slug = getattr(self, "_selected_body", None)
            if not slug:
                lv = self.query_one("#body-list", ListView)
                if lv.highlighted_child is not None:
                    slug = getattr(lv.highlighted_child, "body_slug", None)
            if not slug:
                log.push("select a body from the list")
                return
            self.query_one("#body-slug", Input).value = slug
            session.start_body(slug, use_lock=True)
            log.push(f"initialized body '{slug}'")
            for w in (session.body or {}).get("warnings") or []:
                log.push(w)
            self._refresh()
            return
        if event.button.id == "btn-init":
            slug = self.query_one("#body-slug", Input).value.strip() or "new-world"
            session.start_body(slug, use_lock=True)
            log.push(f"initialized body '{slug}'")
            for w in (session.body or {}).get("warnings") or []:
                log.push(w)
            self._refresh()
            return
        if session.body is None:
            log.push("initialize a body first")
            return
        if event.button.id == "btn-ptype":
            ptype = str(self.query_one("#ptype-select", Select).value)
            bkind = str(self.query_one("#bkind-select", Select).value)
            session.pick_planet_type(ptype, bkind)
            log.push(
                f"planet_type → {ptype}/{bkind} ({session.provenance.get('planet_type')})"
            )
            for w in session.body.get("warnings") or []:
                if w.startswith("override:"):
                    log.push(w)
            self._refresh()
            return
        if event.button.id == "btn-stress":
            grade = str(self.query_one("#stress-select", Select).value)
            session.pick_immaterium(grade)
            log.push(
                f"immaterium_stress → {grade} ({session.provenance.get('immaterium_stress')})"
            )
            self._refresh()
            return
        if event.button.id == "btn-reroll":
            session.reroll_body_layers()
            log.push("rerolled body layers (spark)")
            self._refresh()
            return
        if event.button.id == "btn-next":
            if session.body is None:
                log.push("initialize a body first (Init body / Use listed body)")
                return
            from .biome_flow import BiomeFlowScreen

            self.app.push_screen(BiomeFlowScreen())
