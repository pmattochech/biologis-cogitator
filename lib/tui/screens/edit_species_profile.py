"""Species dossier — create/edit page with always-visible plate."""
from __future__ import annotations

import copy
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Input, Static

from ... import dossier_media as dmedia
from ... import profile_schema as qschema
from ... import species_profile as speciesmod
from ...wizard_session import WizardSession
from ..widgets.dossier_chrome import DossierChrome
from ..widgets.header import CogitatorHeader
from ..widgets.warn_log import WarnLog
from . import species_form as form


class EditSpeciesProfileScreen(Screen):
    """Species dossier page (create and edit share this surface)."""

    TRACK_DIRTY = True

    CSS = """
    #sp-main { height: 1fr; padding: 0 1; }
    #sp-toolbar { height: 3; }
    #sp-toolbar Button { margin: 0 1 0 0; min-width: 10; height: 3; }
    #sp-min-hint { height: auto; color: #3aa060; margin: 0 0 1 0; }
    #sp-body { height: 1fr; }
    #sp-scroll {
        width: 1fr;
        height: 1fr;
        border: solid #2a8040;
        padding: 0 1;
    }
    #sp-scroll Label { margin-top: 1; }
    #sp-scroll SelectionList.biome-multi {
        height: auto;
        max-height: 12;
        margin: 0 0 1 0;
        border: solid #2a8040;
    }
    """

    def __init__(
        self,
        *,
        species_id: str | None = None,
        create: bool = False,
        profile: dict | None = None,
        read_only: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.species_id = species_id
        self.create = create
        self.read_only = read_only
        self._seed_profile = copy.deepcopy(profile) if profile else None
        self._schema: dict = {}
        self._profile: dict = {}
        self._pending_image: Path | None = None
        self._clear_image: bool = False

    def compose(self) -> ComposeResult:
        self._schema = qschema.load_schema(force=True)
        title = "NEW SPECIES" if self.create else (
            "SPECIES DOSSIER" if self.read_only else "EDIT SPECIES"
        )
        yield CogitatorHeader(f"DOSSIER / {title}")
        with Vertical(id="sp-main"):
            with Horizontal(id="sp-toolbar"):
                if not self.read_only:
                    yield Button("Save", id="btn-save", variant="primary")
                    yield Button("Add subspecies", id="btn-subspecies")
                    yield Button("Reload schema", id="btn-reload")
                yield Button("Back", id="btn-back")
            if not self.read_only:
                yield Static(form.min_gate_hint(), id="sp-min-hint", classes="litany")
            with Horizontal(id="sp-body"):
                yield DossierChrome(
                    kind_label="SPECIES DOSSIER",
                    title=self.species_id or "—",
                    subtitle="plate + filing identity",
                    image_path=dmedia.DEFAULT_PLATE,
                    read_only=self.read_only,
                    id="sp-chrome",
                )
                with VerticalScroll(id="sp-scroll"):
                    if self.read_only:
                        yield Static(id="sp-readonly", classes="litany")
                    else:
                        biomes = self._body_biomes_safe()
                        biome_opts = speciesmod.origin_place_options(biomes)
                        secondary_opts = speciesmod.secondary_biome_options(biomes)
                        for step in qschema.steps(self._schema):
                            yield Static(
                                f"— {step.get('title') or step.get('id')} —",
                                classes="title",
                            )
                            yield from form.yield_step_fields(
                                step,
                                trophic_slots=self._trophic_slots_safe(),
                                biome_options=biome_opts,
                                secondary_biome_options=secondary_opts,
                            )
        yield WarnLog()

    def _body_biomes_safe(self) -> list[dict]:
        try:
            return list(self._session().current_biomes() or [])
        except Exception:
            return []

    def _biome_option_pairs(self) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
        biomes = self._body_biomes_safe()
        return (
            speciesmod.origin_place_options(biomes),
            speciesmod.secondary_biome_options(biomes),
        )

    def _trophic_slots_safe(self) -> list[str]:
        try:
            return self._session().trophic_slots()
        except Exception:
            return ["apex"]

    def _lock_entry_id_widget(self) -> None:
        if self.read_only:
            return
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
        if not self.read_only:
            biome_opts, secondary_opts = self._biome_option_pairs()
            form.apply_profile_to_widgets(
                self,
                self._profile,
                self._schema,
                trophic_slots=session.trophic_slots(),
                biome_options=biome_opts,
                secondary_biome_options=secondary_opts,
            )
            form.refresh_dependent_selects(self, self._profile, self._schema)
            self._lock_entry_id_widget()
        else:
            text = form.format_profile_readonly(
                self._profile,
                trophic_slots=session.trophic_slots(),
                body_slug=session.body_slug(),
            )
            try:
                self.query_one("#sp-readonly", Static).update(text)
            except Exception:
                pass
        self._refresh_identity()
        self._refresh_pic_status()

    def _session(self) -> WizardSession:
        return self.app.session  # type: ignore[attr-defined]

    def _chrome(self) -> DossierChrome:
        return self.query_one("#sp-chrome", DossierChrome)

    def _refresh_identity(self) -> None:
        name = speciesmod.display_name(self._profile) if self._profile else "—"
        sid = str(self.species_id or (self._profile or {}).get("id") or "—")
        slot = str((self._profile or {}).get("trophic_slot") or "").strip()
        sub = f"Entry ID `{sid}`"
        if slot:
            sub += f" · slot `{slot}`"
        if self.create:
            sub += " · unsaved"
        try:
            self._chrome().set_identity(title=name, subtitle=sub)
        except Exception:
            pass

    def _preview_image_path(self) -> Path:
        if self._clear_image:
            return dmedia.DEFAULT_PLATE
        if self._pending_image is not None and self._pending_image.is_file():
            return self._pending_image
        slug = self._session().body_slug() or ""
        sid = str(self.species_id or (self._profile or {}).get("id") or "")
        if slug and sid:
            return dmedia.resolve_plate("species", body_slug=slug, species_id=sid)
        return dmedia.DEFAULT_PLATE

    def _refresh_pic_status(self) -> None:
        try:
            chrome = self._chrome()
        except Exception:
            return
        slug = self._session().body_slug() or ""
        sid = str(self.species_id or (self._profile or {}).get("id") or "")
        chrome.set_plate_path(self._preview_image_path())
        if self._clear_image:
            chrome.set_pic_status("status: will clear plate on Save → default")
            return
        if self._pending_image is not None:
            chrome.set_pic_status(f"status: staged for Save ← {self._pending_image}")
            return
        if slug and sid:
            chrome.set_pic_status(
                f"status: {dmedia.plate_status_label('species', body_slug=slug, species_id=sid)}"
            )
        else:
            chrome.set_pic_status(
                f"status: default ({dmedia.PLATE_WIDTH}×{dmedia.PLATE_HEIGHT} {dmedia.PLATE_FORMAT})"
            )

    def _apply_pending_image(self, sid: str) -> str | None:
        slug = self._session().body_slug() or ""
        if not slug or not sid:
            return None
        if self._clear_image:
            removed = dmedia.clear_plate("species", body_slug=slug, species_id=sid)
            self._clear_image = False
            self._pending_image = None
            return "cleared profile plate" if removed else "plate already default"
        if self._pending_image is not None:
            dmedia.write_plate(
                "species", self._pending_image, body_slug=slug, species_id=sid
            )
            path = self._pending_image
            self._pending_image = None
            return f"plate → {dmedia.plate_path('species', body_slug=slug, species_id=sid)} (from {path})"
        return None

    def flush_unsaved(self) -> str | None:
        if self.read_only:
            return None
        _, secondary_opts = self._biome_option_pairs()
        profile = form.collect_profile_from_widgets(
            self,
            self._schema,
            base=self._profile,
            secondary_biome_options=secondary_opts,
        )
        if self.species_id and not str(profile.get("id") or "").strip():
            profile["id"] = self.species_id
        errors = speciesmod.validate_minimum(
            profile, body_biomes=self._body_biomes_safe()
        )
        if errors:
            return "; ".join(errors)
        try:
            self._session().save_species_profile(profile)
            self._profile = profile
            self.species_id = profile["id"]
            self.create = False
            self._apply_pending_image(self.species_id)
            self._refresh_identity()
            self._refresh_pic_status()
            self._session().clear_dirty()
        except Exception as exc:
            return str(exc)
        return None

    def on_select_changed(self, event) -> None:  # type: ignore[no-untyped-def]
        if self.read_only:
            return
        form.on_select_changed_refresh(
            self,
            event.select.id or "",
            lambda: self._profile,
            self._schema,
        )
        self._refresh_identity()

    def on_input_changed(self, event) -> None:  # type: ignore[no-untyped-def]
        if self.read_only:
            return
        # Live identity from vernacula / names as user types
        try:
            self._profile = self._collect()
            self._refresh_identity()
        except Exception:
            pass

    def _collect(self) -> dict:
        _, secondary_opts = self._biome_option_pairs()
        profile = form.collect_profile_from_widgets(
            self,
            self._schema,
            base=self._profile,
            secondary_biome_options=secondary_opts,
        )
        if self.species_id:
            profile["id"] = self.species_id
            profile["magos_scaffold_id"] = self.species_id
        return profile

    def on_button_pressed(self, event: Button.Pressed) -> None:
        log = self.query_one(WarnLog)
        bid = event.button.id
        if bid == "btn-back":
            self.app.request_back()  # type: ignore[attr-defined]
            return
        if bid == "btn-pic-browse":
            if self.read_only:
                return
            chosen = dmedia.browse_image_path()
            if chosen is None:
                log.push("browse cancelled (or tkinter unavailable — paste a path)")
                return
            self._chrome().set_pic_path_value(str(chosen))
            log.push(f"path set ← {chosen}")
            return
        if bid == "btn-pic-import":
            if self.read_only:
                return
            raw = self._chrome().pic_path_value()
            if not raw:
                log.push("set an image path first (Browse or type)")
                return
            try:
                src = dmedia.validate_image_file(raw)
            except Exception as exc:
                log.push(f"cannot read image: {exc}")
                return
            self._pending_image = src
            self._clear_image = False
            self._session().mark_dirty()
            self._refresh_pic_status()
            log.push(
                f"staged plate import ({dmedia.PLATE_WIDTH}×"
                f"{dmedia.PLATE_HEIGHT} {dmedia.PLATE_FORMAT} on Save)"
            )
            return
        if bid == "btn-pic-clear":
            if self.read_only:
                return
            self._pending_image = None
            self._clear_image = True
            self._chrome().set_pic_path_value("")
            self._session().mark_dirty()
            self._refresh_pic_status()
            log.push("staged clear of plate (applies on Save)")
            return
        if bid == "btn-pic-open":
            try:
                dmedia.open_image_external(self._preview_image_path())
                log.push("opened plate in system viewer")
            except Exception as exc:
                log.push(str(exc))
            return
        if bid == "btn-subspecies":
            if self.read_only:
                return
            session = self._session()
            parent = self._collect()
            sid = str(parent.get("id") or self.species_id or "").strip()
            if not sid:
                log.push("save or set Entry ID before adding subspecies")
                return
            reserved = [str(s.get("id") or "") for s in session.current_specimens()]
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
        if bid == "btn-reload":
            if self.read_only:
                return
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
        if bid != "btn-save" or self.read_only:
            return
        session = self._session()
        profile = self._collect()
        errors = speciesmod.validate_minimum(
            profile, body_biomes=self._body_biomes_safe()
        )
        form.show_min_errors(self, errors)
        if errors:
            log.push("minimum gate failed: " + "; ".join(errors))
            return
        try:
            path = session.save_species_profile(profile)
            self._profile = profile
            self.species_id = profile["id"]
            self.create = False
            pic_note = self._apply_pending_image(self.species_id)
            self._refresh_identity()
            self._refresh_pic_status()
            session.clear_dirty()
            log.push(f"saved species dossier → {path}")
            if pic_note:
                log.push(pic_note)
        except Exception as exc:
            log.push(str(exc))
