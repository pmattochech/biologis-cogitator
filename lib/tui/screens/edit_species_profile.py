"""Full species profile editor — fields come from schema YAML."""
from __future__ import annotations

import copy

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Input, Static

from ... import profile_schema as qschema
from ... import species_profile as speciesmod
from ...wizard_session import WizardSession
from ..widgets.header import CogitatorHeader
from ..widgets.warn_log import WarnLog
from . import species_form as form


class EditSpeciesProfileScreen(Screen):
    TRACK_DIRTY = True

    CSS = """
    #sp-main { height: 1fr; padding: 0 1; }
    #sp-toolbar { height: 3; }
    #sp-toolbar Button { margin: 0 1 0 0; min-width: 10; height: 3; }
    #sp-min-hint { height: auto; color: #c9a227; margin: 0 0 1 0; }
    #sp-scroll { height: 1fr; }
    #sp-scroll Label { margin-top: 1; }
    """

    def __init__(
        self,
        *,
        species_id: str | None = None,
        create: bool = False,
        profile: dict | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.species_id = species_id
        self.create = create
        self._seed_profile = copy.deepcopy(profile) if profile else None
        self._schema: dict = {}
        self._profile: dict = {}

    def compose(self) -> ComposeResult:
        self._schema = qschema.load_schema(force=True)
        title = "NEW SPECIES" if self.create else "EDIT SPECIES"
        yield CogitatorHeader(f"EDITOR / {title}")
        with Vertical(id="sp-main"):
            with Horizontal(id="sp-toolbar"):
                yield Button("Save", id="btn-save", variant="primary")
                yield Button("Add subspecies", id="btn-subspecies")
                yield Button("Reload schema", id="btn-reload")
                yield Button("Back", id="btn-back")
            yield Static(form.min_gate_hint(), id="sp-min-hint", classes="litany")
            with VerticalScroll(id="sp-scroll"):
                for step in qschema.steps(self._schema):
                    yield Static(
                        f"— {step.get('title') or step.get('id')} —",
                        classes="title",
                    )
                    yield from form.yield_step_fields(
                        step, trophic_slots=self._trophic_slots_safe()
                    )
        yield WarnLog()

    def _trophic_slots_safe(self) -> list[str]:
        try:
            return self._session().trophic_slots()
        except Exception:
            return ["apex"]

    def _lock_entry_id_widget(self) -> None:
        """Entry ID is allocated by New / Add subspecies — not free-typed."""
        try:
            field = qschema.field_by_store("profile.id", self._schema)
            if not field:
                return
            wid = qschema.widget_id(field)
            self.query_one(f"#{wid}", Input).disabled = True
        except Exception:
            pass

    def on_mount(self) -> None:
        self.query_one(WarnLog).boot()
        session = self._session()
        if self._seed_profile is not None:
            self._profile = copy.deepcopy(self._seed_profile)
            self.species_id = str(self._profile.get("id") or self.species_id or "")
        elif self.species_id and not self.create:
            loaded = session.get_species_profile(self.species_id)
            self._profile = loaded or speciesmod.empty_profile(self.species_id)
        elif self.create and self.species_id:
            self._profile = speciesmod.empty_profile(self.species_id)
        else:
            self._profile = speciesmod.empty_profile()
        form.apply_profile_to_widgets(
            self,
            self._profile,
            self._schema,
            trophic_slots=session.trophic_slots(),
        )
        form.refresh_dependent_selects(self, self._profile, self._schema)
        self._lock_entry_id_widget()

    def _session(self) -> WizardSession:
        return self.app.session  # type: ignore[attr-defined]

    def flush_unsaved(self) -> str | None:
        profile = form.collect_profile_from_widgets(
            self, self._schema, base=self._profile
        )
        # Keep locked Entry ID from profile if widget disabled/empty
        if self.species_id and not str(profile.get("id") or "").strip():
            profile["id"] = self.species_id
        errors = speciesmod.validate_minimum(profile)
        if errors:
            return "; ".join(errors)
        try:
            self._session().save_species_profile(profile)
            self._profile = profile
            self.species_id = profile["id"]
            self.create = False
            self._session().clear_dirty()
        except Exception as exc:
            return str(exc)
        return None

    def on_select_changed(self, event) -> None:  # type: ignore[no-untyped-def]
        form.on_select_changed_refresh(
            self,
            event.select.id or "",
            lambda: self._profile,
            self._schema,
        )

    def _collect(self) -> dict:
        profile = form.collect_profile_from_widgets(
            self, self._schema, base=self._profile
        )
        if self.species_id:
            profile["id"] = self.species_id
            profile["magos_scaffold_id"] = self.species_id
        return profile

    def on_button_pressed(self, event: Button.Pressed) -> None:
        log = self.query_one(WarnLog)
        if event.button.id == "btn-back":
            self.app.request_back()  # type: ignore[attr-defined]
            return
        if event.button.id == "btn-subspecies":
            # Prefill clone in memory only — disk write on Save of the new screen
            session = self._session()
            parent = self._collect()
            sid = str(parent.get("id") or self.species_id or "").strip()
            if not sid:
                log.push("save or set Entry ID before adding subspecies")
                return
            reserved = [str(s.get("id") or "") for s in session.current_specimens()]
            # Also reserve current unsaved id
            if sid not in reserved:
                reserved.append(sid)
            new_id = speciesmod.suggest_variant_id_for_session(
                session.body_slug(), sid, reserved_ids=reserved
            )
            if not new_id:
                log.push("could not allocate subspecies Entry ID")
                return
            clone = speciesmod.clone_profile_as_variant(parent, new_id)
            self.app.push_screen(
                EditSpeciesProfileScreen(
                    species_id=new_id,
                    create=True,
                    profile=clone,
                )
            )
            return
        if event.button.id == "btn-reload":
            self._profile = self._collect()
            self.app.pop_screen()
            self.app.push_screen(
                EditSpeciesProfileScreen(
                    species_id=self.species_id
                    or str(self._profile.get("id") or "")
                    or None,
                    create=self.create,
                    profile=self._profile,
                )
            )
            log.push(f"reloaded schema v{qschema.load_schema().get('version')}")
            return
        if event.button.id != "btn-save":
            return
        session = self._session()
        profile = self._collect()
        errors = speciesmod.validate_minimum(profile)
        form.show_min_errors(self, errors)
        if errors:
            log.push("minimum gate failed: " + "; ".join(errors))
            return
        try:
            path = session.save_species_profile(profile)
            self._profile = profile
            self.species_id = profile["id"]
            self.create = False
            session.clear_dirty()
            log.push(f"saved species → {path}")
        except Exception as exc:
            log.push(str(exc))
