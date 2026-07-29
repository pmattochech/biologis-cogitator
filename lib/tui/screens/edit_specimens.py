"""Specimen list — read-only dossier view; New / Edit / Add subspecies."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Label, ListItem, ListView, Static

from ... import species_profile as speciesmod
from ...wizard_session import WizardSession
from ..widgets.header import CogitatorHeader
from ..widgets.warn_log import WarnLog
from . import species_form as form


class EditSpecimensScreen(Screen):
    # Read-only: do not mark session dirty from this screen
    TRACK_DIRTY = False

    CSS = """
    #spec-main { height: 1fr; padding: 0 1; }
    #spec-toolbar { height: 3; }
    #spec-toolbar Button { margin: 0 1 0 0; min-width: 10; height: 3; }
    #spec-list { height: 8; border: solid #2a8040; }
    #spec-detail {
        height: 1fr;
        border: solid #2a8040;
        padding: 0 1;
        color: #b8ffd0;
    }
    #spec-hint { height: auto; color: #3aa060; margin: 0 0 1 0; }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._selected_id: str | None = None

    def compose(self) -> ComposeResult:
        yield CogitatorHeader("EDITOR / SPECIMENS")
        with Vertical(id="spec-main"):
            with Horizontal(id="spec-toolbar"):
                yield Button("New", id="btn-new", variant="primary")
                yield Button("Edit", id="btn-edit")
                yield Button("Add subspecies", id="btn-subspecies")
                yield Button("Remove", id="btn-remove")
                yield Button("Back", id="btn-back")
            yield Static(
                "Select a specimen, then Edit. New asks for primary biome first "
                "(Entry ID is generated; disk write only on Save).",
                id="spec-hint",
                classes="litany",
            )
            yield Label("Specimens")
            yield ListView(id="spec-list")
            yield Label("Profile (read-only)")
            with VerticalScroll(id="spec-detail"):
                yield Static("(select a specimen)", id="spec-ro")
            yield Static(id="biome-hint", classes="litany")
        yield WarnLog()

    def on_mount(self) -> None:
        self.query_one(WarnLog).boot()
        biomes = ", ".join(b.get("id", "") for b in self._session().current_biomes())
        self.query_one("#biome-hint", Static).update(
            f"Biome ids on body: {biomes or '(none)'}"
        )
        self._reload_list()

    def _session(self) -> WizardSession:
        return self.app.session  # type: ignore[attr-defined]

    def flush_unsaved(self) -> str | None:
        return None

    def _reserved_ids(self) -> list[str]:
        return [str(s.get("id") or "") for s in self._session().current_specimens()]

    def _reload_list(self) -> None:
        lv = self.query_one("#spec-list", ListView)
        lv.clear()
        session = self._session()
        keep = self._selected_id
        for spec in session.current_specimens():
            sid = str(spec.get("id") or "")
            prof = session.get_species_profile(sid) if sid else None
            name = (
                speciesmod.display_name(prof)
                if prof
                else str(spec.get("name") or sid)
            )
            slot = spec.get("trophic_slot") or ""
            label = f"{sid} — {name}"
            if slot:
                label += f" [{slot}]"
            item = ListItem(Label(label))
            item.spec_id = sid  # type: ignore[attr-defined]
            lv.append(item)
        if keep:
            self._selected_id = keep
            self._show_detail(keep)
        else:
            self.query_one("#spec-ro", Static).update("(select a specimen)")

    def _show_detail(self, sid: str) -> None:
        session = self._session()
        profile = session.get_species_profile(sid)
        if not profile:
            self.query_one("#spec-ro", Static).update(
                f"(no profile for {sid} — use Edit to create)"
            )
            return
        text = form.format_profile_readonly(
            profile, trophic_slots=session.trophic_slots()
        )
        self.query_one("#spec-ro", Static).update(text)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        sid = getattr(event.item, "spec_id", None)
        if not sid:
            return
        self._selected_id = str(sid)
        self._show_detail(self._selected_id)

    def _open_editor(
        self,
        *,
        species_id: str | None = None,
        create: bool = False,
        profile: dict | None = None,
    ) -> None:
        from .edit_species_profile import EditSpeciesProfileScreen

        self.app.push_screen(
            EditSpeciesProfileScreen(
                species_id=species_id,
                create=create,
                profile=profile,
            )
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        session = self._session()
        log = self.query_one(WarnLog)
        if event.button.id == "btn-back":
            # Read-only screen: pop without dirty trap
            if len(self.app.screen_stack) > 1:
                self.app.pop_screen()
            return
        if event.button.id == "btn-new":
            from .species_wizard import NewSpeciesBiomeScreen

            self.app.push_screen(NewSpeciesBiomeScreen())
            return
        if event.button.id == "btn-edit":
            sid = self._selected_id
            if not sid:
                log.push("select a specimen from the list first")
                return
            self._open_editor(species_id=sid, create=False)
            return
        if event.button.id == "btn-subspecies":
            sid = self._selected_id
            if not sid:
                log.push("select a parent specimen first")
                return
            parent = session.get_species_profile(sid)
            if not parent:
                log.push(f"no profile to clone for {sid}")
                return
            try:
                new_id = speciesmod.suggest_variant_id_for_session(
                    session.body_slug(),
                    sid,
                    reserved_ids=self._reserved_ids(),
                )
            except Exception as exc:
                log.push(str(exc))
                return
            if not new_id:
                log.push("could not allocate subspecies Entry ID")
                return
            clone = speciesmod.clone_profile_as_variant(parent, new_id)
            self._open_editor(species_id=new_id, create=True, profile=clone)
            return
        if event.button.id == "btn-remove":
            sid = self._selected_id
            if not sid:
                log.push("select a specimen first")
                return
            session.remove_specimen(sid)
            self._selected_id = None
            log.push(f"removed pack lock {sid} (disk archive not deleted)")
            self._reload_list()
            return

    def on_screen_resume(self) -> None:
        biomes = ", ".join(b.get("id", "") for b in self._session().current_biomes())
        self.query_one("#biome-hint", Static).update(
            f"Biome ids on body: {biomes or '(none)'}"
        )
        self._reload_list()
