"""Structured field editors for classification / geology / climate."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Input, Label, Select, Static

from ...wizard_session import WizardSession
from ..widgets.header import CogitatorHeader
from ..widgets.warn_log import WarnLog


class EditFieldsScreen(Screen):
    TRACK_DIRTY = True

    CSS = """
    #fields-main { height: 1fr; padding: 0 1; }
    #fields-toolbar { height: 3; }
    #fields-toolbar Button { margin: 0 1 0 0; min-width: 12; height: 3; }
    """

    def __init__(self, *, section: str = "classification", **kwargs) -> None:
        super().__init__(**kwargs)
        self.section = section

    def compose(self) -> ComposeResult:
        yield CogitatorHeader(f"EDITOR / {self.section.upper()}")
        with Vertical(id="fields-main"):
            with Horizontal(id="fields-toolbar"):
                yield Button("Apply", id="btn-apply", variant="primary")
                yield Button("Back", id="btn-back")
            with VerticalScroll():
                yield Static(id="hint", classes="litany")
                if self.section == "classification":
                    yield Label("Planet type")
                    yield Select([("civilised_world", "civilised_world")], id="planet-type", allow_blank=False)
                    yield Label("Body kind")
                    yield Select([("planet", "planet")], id="body-kind", allow_blank=False)
                    yield Label("Local notes")
                    yield Input(id="local-notes")
                    yield Label("Topology")
                    yield Input(id="topology")
                elif self.section == "geology":
                    yield Label("gravity_g")
                    yield Input(id="gravity_g")
                    yield Label("crust")
                    yield Input(id="crust")
                    yield Label("volcanism")
                    yield Input(id="volcanism")
                    yield Label("connectivity")
                    yield Input(id="connectivity")
                    yield Label("hydrosphere_pct")
                    yield Input(id="hydrosphere_pct")
                    yield Label("tidal_lock (true/false)")
                    yield Input(id="tidal_lock")
                else:
                    yield Label("immaterium_stress")
                    yield Select([("neutral", "neutral")], id="immaterium", allow_blank=False)
                    yield Label("atmosphere")
                    yield Input(id="atmosphere")
                    yield Label("cryosphere")
                    yield Input(id="cryosphere")
                    yield Label("climate_belts (comma-separated)")
                    yield Input(id="climate_belts")
                    yield Label("flavor tags (comma-separated)")
                    yield Input(id="flavor_tags")
        yield WarnLog()

    def on_mount(self) -> None:
        self.query_one(WarnLog).boot()
        session = self._session()
        body = session.body or {}
        layers = body.get("layers") or {}
        locks = body.get("locks") or {}
        if self.section == "classification":
            self.query_one("#hint", Static).update("Administratum class + body kind + notes.")
            pts = [(p, p) for p in session.planet_types()]
            bks = [(k, k) for k in session.body_kinds()]
            self.query_one("#planet-type", Select).set_options(pts or [("civilised_world", "civilised_world")])
            self.query_one("#body-kind", Select).set_options(bks or [("planet", "planet")])
            pt = layers.get("planet_type") or {}
            cur_pt = pt.get("planet_type") or locks.get("planet_type")
            cur_bk = pt.get("body_kind") or locks.get("body_kind") or "planet"
            if cur_pt:
                self.query_one("#planet-type", Select).value = cur_pt
            if cur_bk:
                self.query_one("#body-kind", Select).value = cur_bk
            self.query_one("#local-notes", Input).value = str(
                locks.get("local_notes") or pt.get("local_notes") or ""
            )
            self.query_one("#topology", Input).value = str(
                locks.get("topology") or (layers.get("geology") or {}).get("topology") or ""
            )
        elif self.section == "geology":
            self.query_one("#hint", Static).update("Geology locks (rebuild layers on Apply).")
            geo = layers.get("geology") or locks.get("geology") or {}
            for key in ("gravity_g", "crust", "volcanism", "connectivity", "hydrosphere_pct"):
                self.query_one(f"#{key}", Input).value = str(geo.get(key, locks.get(key, "")))
            self.query_one("#tidal_lock", Input).value = str(geo.get("tidal_lock", False)).lower()
        else:
            self.query_one("#hint", Static).update("Climate + immaterium stress.")
            grades = [(g, g) for g in session.immaterium_grades()]
            self.query_one("#immaterium", Select).set_options(grades)
            chem = layers.get("chemistry_climate") or locks.get("chemistry_climate") or {}
            grade = chem.get("immaterium_stress") or locks.get("immaterium_stress") or "neutral"
            self.query_one("#immaterium", Select).value = grade
            self.query_one("#atmosphere", Input).value = str(chem.get("atmosphere") or "")
            self.query_one("#cryosphere", Input).value = str(chem.get("cryosphere") or "")
            self.query_one("#climate_belts", Input).value = ", ".join(chem.get("climate_belts") or [])
            self.query_one("#flavor_tags", Input).value = ", ".join(
                chem.get("immaterium_flavor_tags") or []
            )

    def _session(self) -> WizardSession:
        return self.app.session  # type: ignore[attr-defined]

    def flush_unsaved(self) -> str | None:
        """Apply field form into session (same as Apply)."""
        try:
            self._apply_fields()
        except Exception as exc:
            return str(exc)
        return None

    def _apply_fields(self) -> None:
        session = self._session()
        if self.section == "classification":
            pt = str(self.query_one("#planet-type", Select).value)
            bk = str(self.query_one("#body-kind", Select).value)
            notes = self.query_one("#local-notes", Input).value
            topo = self.query_one("#topology", Input).value
            session.pick_planet_type(pt, bk)
            session.update_lock_fields({"local_notes": notes, "topology": topo})
        elif self.section == "geology":
            fields: dict = {}
            g = self.query_one("#gravity_g", Input).value.strip()
            if g:
                fields["gravity_g"] = float(g)
            for key in ("crust", "volcanism", "connectivity"):
                v = self.query_one(f"#{key}", Input).value.strip()
                if v:
                    fields[key] = v
            h = self.query_one("#hydrosphere_pct", Input).value.strip()
            if h:
                fields["hydrosphere_pct"] = float(h)
            tl = self.query_one("#tidal_lock", Input).value.strip().lower()
            fields["tidal_lock"] = tl in ("1", "true", "yes", "y")
            session.update_geology_lock(fields)
        else:
            fields = {
                "immaterium_stress": str(self.query_one("#immaterium", Select).value),
                "atmosphere": self.query_one("#atmosphere", Input).value.strip(),
                "cryosphere": self.query_one("#cryosphere", Input).value.strip(),
                "climate_belts": [
                    x.strip()
                    for x in self.query_one("#climate_belts", Input).value.split(",")
                    if x.strip()
                ],
                "immaterium_flavor_tags": [
                    x.strip()
                    for x in self.query_one("#flavor_tags", Input).value.split(",")
                    if x.strip()
                ],
            }
            session.update_chem_lock(fields)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-back":
            self.app.request_back()  # type: ignore[attr-defined]
            return
        if event.button.id != "btn-apply":
            return
        log = self.query_one(WarnLog)
        try:
            self._apply_fields()
            log.push("fields applied — layers rebuilt")
        except Exception as exc:
            log.push(str(exc))
