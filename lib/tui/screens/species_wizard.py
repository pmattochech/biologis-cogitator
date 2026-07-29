"""New species — pick primary origin place, then open profile with allocated Entry ID."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Select, Static

from ... import species_profile as speciesmod
from ...wizard_session import WizardSession
from ..widgets.header import CogitatorHeader
from ..widgets.warn_log import WarnLog


class NewSpeciesBiomeScreen(Screen):
    """Gate: choose origin place on the current body, then open the profile."""

    TRACK_DIRTY = False

    CSS = """
    #new-main { height: 1fr; padding: 0 1; }
    #new-toolbar { height: 3; }
    #new-toolbar Button { margin: 0 1 0 0; min-width: 10; height: 3; }
    #new-hint { height: auto; color: #3aa060; margin: 1 0; }
    #new-preview { height: auto; color: #b8ffd0; margin: 1 0; border: solid #2a8040; padding: 1; }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._biome_id: str = ""

    def compose(self) -> ComposeResult:
        yield CogitatorHeader("EDITOR / NEW SPECIES")
        with Vertical(id="new-main"):
            with Horizontal(id="new-toolbar"):
                yield Button("Continue", id="btn-continue", variant="primary")
                yield Button("Cancel", id="btn-cancel")
            yield Static(
                "World is the body already open. Pick the origin place — "
                "registered biomes on this body, or void / warp / outer_space "
                "when there is no planetary surface. "
                "Entry ID is allocated next (file created only when you Save).",
                id="new-hint",
                classes="litany",
            )
            yield Static("Origin place")
            yield Select([("(none)", "")], id="new-biome", allow_blank=False)
            yield Static("Entry ID preview: —", id="new-preview")
        yield WarnLog()

    def on_mount(self) -> None:
        self.query_one(WarnLog).boot()
        session = self._session()
        biomes = session.current_biomes()
        opts = speciesmod.origin_place_options(biomes)
        sel = self.query_one("#new-biome", Select)
        if not opts:
            sel.set_options(list(speciesmod.SPECIAL_ORIGIN_PLACES))
            opts = list(speciesmod.SPECIAL_ORIGIN_PLACES)
        sel.set_options(opts)
        sel.value = opts[0][1]
        self._biome_id = opts[0][1]
        if not biomes:
            self.query_one(WarnLog).push(
                "no planetary biomes on this body — use void / warp / outer_space"
            )
        self._refresh_preview()

    def _session(self) -> WizardSession:
        return self.app.session  # type: ignore[attr-defined]

    def _reserved_ids(self) -> list[str]:
        return [str(s.get("id") or "") for s in self._session().current_specimens()]

    def _refresh_preview(self) -> None:
        session = self._session()
        sid = speciesmod.suggest_id_for_session(
            session.body_slug(),
            self._biome_id,
            reserved_ids=self._reserved_ids(),
        )
        slug = session.body_slug() or "(no body)"
        text = (
            f"Body: {slug}\n"
            f"Origin place: {self._biome_id or '—'}\n"
            f"Entry ID preview: {sid or '(register body in data/enums/filing_ids.csv)'}"
        )
        self.query_one("#new-preview", Static).update(text)

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id != "new-biome":
            return
        val = event.value
        # Select.BLANK is falsy on current Textual — treat blank carefully
        if val is None or (isinstance(val, str) and not val.strip()):
            self._biome_id = ""
        elif val is getattr(Select, "BLANK", object()) or val is getattr(
            Select, "NULL", object()
        ):
            self._biome_id = ""
        else:
            self._biome_id = str(val)
        self._refresh_preview()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        log = self.query_one(WarnLog)
        if event.button.id == "btn-cancel":
            if len(self.app.screen_stack) > 1:
                self.app.pop_screen()
            return
        if event.button.id != "btn-continue":
            return
        session = self._session()
        if not self._biome_id:
            log.push("select an origin place")
            return
        allowed = {
            v for _, v in speciesmod.origin_place_options(session.current_biomes())
        }
        if self._biome_id not in allowed:
            log.push(f"origin place {self._biome_id!r} is not allowed on this body")
            return
        sid = speciesmod.suggest_id_for_session(
            session.body_slug(),
            self._biome_id,
            reserved_ids=self._reserved_ids(),
        )
        if not sid:
            log.push(
                "cannot allocate Entry ID — check data/enums/filing_ids.csv / body filing_id"
            )
            return
        profile = speciesmod.empty_profile(sid, world_biome=self._biome_id)
        from .edit_species_profile import EditSpeciesProfileScreen

        # Replace this gate with the profile (no disk write yet)
        self.app.pop_screen()
        self.app.push_screen(
            EditSpeciesProfileScreen(
                species_id=sid,
                create=True,
                profile=profile,
            )
        )


# Back-compat alias for older hub buttons
SpeciesWizardScreen = NewSpeciesBiomeScreen
