"""Full species profile editor — fields come from schema YAML."""
from __future__ import annotations

import copy
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Input, Static

from ... import profile_schema as qschema
from ... import species_media as media
from ... import species_profile as speciesmod
from ...wizard_session import WizardSession
from ..widgets.header import CogitatorHeader
from ..widgets.profile_plate import ProfilePlate
from ..widgets.warn_log import WarnLog
from . import species_form as form


class EditSpeciesProfileScreen(Screen):
    TRACK_DIRTY = True

    CSS = """
    #sp-main { height: 1fr; padding: 0 1; }
    #sp-toolbar { height: 3; }
    #sp-toolbar Button { margin: 0 1 0 0; min-width: 10; height: 3; }
    #sp-min-hint { height: auto; color: #3aa060; margin: 0 0 1 0; }
    #sp-scroll { height: 1fr; }
    #sp-scroll Label { margin-top: 1; }
    #sp-scroll SelectionList.biome-multi {
        height: auto;
        max-height: 12;
        margin: 0 0 1 0;
        border: solid #2a8040;
    }
    #sp-pic-status { height: auto; color: #3aa060; margin: 0 0 1 0; }
    #sp-pic-row { height: 3; margin: 0 0 1 0; }
    #sp-pic-row Input { width: 1fr; margin: 0 1 0 0; }
    #sp-pic-row Button { margin: 0 1 0 0; min-width: 8; height: 3; }
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
        # Staged until Save: ingest source path, or clear custom plate.
        self._pending_image: Path | None = None
        self._clear_image: bool = False

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
                yield Static("— Profile picture —", classes="title")
                yield Static(
                    f"Optional. Plate is always {media.PROFILE_WIDTH}×"
                    f"{media.PROFILE_HEIGHT} {media.PROFILE_FORMAT} "
                    f"(contain + letterbox). Missing → default cog placeholder. "
                    f"Preview renders in-pane below.",
                    id="sp-pic-hint",
                    classes="litany",
                )
                yield ProfilePlate(media.DEFAULT_PROFILE, id="sp-pic-preview")
                yield Static(id="sp-pic-status")
                with Horizontal(id="sp-pic-row"):
                    yield Input(placeholder="path to image…", id="sp-pic-path")
                    yield Button("Browse", id="btn-pic-browse")
                    yield Button("Import", id="btn-pic-import")
                    yield Button("Clear", id="btn-pic-clear")
                    yield Button("Open", id="btn-pic-open")
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
        self._refresh_pic_status()

    def _session(self) -> WizardSession:
        return self.app.session  # type: ignore[attr-defined]

    def _preview_image_path(self) -> Path:
        if self._clear_image:
            return media.DEFAULT_PROFILE
        if self._pending_image is not None and self._pending_image.is_file():
            return self._pending_image
        slug = self._session().body_slug() or ""
        sid = str(self.species_id or (self._profile or {}).get("id") or "")
        if slug and sid:
            return media.resolve_profile_image(slug, sid)
        return media.DEFAULT_PROFILE

    def _refresh_pic_status(self) -> None:
        try:
            status = self.query_one("#sp-pic-status", Static)
        except Exception:
            return
        slug = self._session().body_slug() or ""
        sid = str(self.species_id or (self._profile or {}).get("id") or "")
        try:
            self.query_one("#sp-pic-preview", ProfilePlate).set_image_path(
                self._preview_image_path()
            )
        except Exception:
            pass
        if self._clear_image:
            status.update(
                "status: will clear custom plate on Save → default placeholder"
            )
            return
        if self._pending_image is not None:
            status.update(f"status: staged for Save ← {self._pending_image}")
            return
        if slug and sid:
            status.update(f"status: {media.profile_status_label(slug, sid)}")
        else:
            status.update(
                f"status: default placeholder "
                f"({media.PROFILE_WIDTH}×{media.PROFILE_HEIGHT} {media.PROFILE_FORMAT})"
            )
    def _apply_pending_image(self, sid: str) -> str | None:
        """Write/clear staged profile plate. Returns warn log line or None."""
        slug = self._session().body_slug() or ""
        if not slug or not sid:
            return None
        if self._clear_image:
            removed = media.clear_profile_image(slug, sid)
            self._clear_image = False
            self._pending_image = None
            return "cleared profile picture" if removed else "profile picture already default"
        if self._pending_image is not None:
            media.write_profile_image(slug, sid, self._pending_image)
            path = self._pending_image
            self._pending_image = None
            return f"profile picture → {media.profile_image_path(slug, sid)} (from {path})"
        return None

    def flush_unsaved(self) -> str | None:
        _, secondary_opts = self._biome_option_pairs()
        profile = form.collect_profile_from_widgets(
            self,
            self._schema,
            base=self._profile,
            secondary_biome_options=secondary_opts,
        )
        # Keep locked Entry ID from profile if widget disabled/empty
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
            self._refresh_pic_status()
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
            chosen = media.browse_image_path()
            if chosen is None:
                log.push("browse cancelled (or tkinter unavailable — paste a path)")
                return
            self.query_one("#sp-pic-path", Input).value = str(chosen)
            log.push(f"path set ← {chosen}")
            return
        if bid == "btn-pic-import":
            raw = self.query_one("#sp-pic-path", Input).value.strip()
            if not raw:
                log.push("set an image path first (Browse or type)")
                return
            try:
                # Validate decode now; write on Save.
                src = media.validate_image_file(raw)
            except Exception as exc:
                log.push(f"cannot read image: {exc}")
                return
            self._pending_image = src
            self._clear_image = False
            self._session().mark_dirty()
            self._refresh_pic_status()
            log.push(
                f"staged profile import ({media.PROFILE_WIDTH}×"
                f"{media.PROFILE_HEIGHT} {media.PROFILE_FORMAT} on Save)"
            )
            return
        if bid == "btn-pic-clear":
            self._pending_image = None
            self._clear_image = True
            self.query_one("#sp-pic-path", Input).value = ""
            self._session().mark_dirty()
            self._refresh_pic_status()
            log.push("staged clear of custom profile picture (applies on Save)")
            return
        if bid == "btn-pic-open":
            slug = self._session().body_slug() or ""
            sid = str(self.species_id or (self._profile or {}).get("id") or "")
            try:
                if self._pending_image is not None and self._pending_image.is_file():
                    media.open_image_external(self._pending_image)
                elif slug and sid and not self._clear_image:
                    media.open_image_external(media.resolve_profile_image(slug, sid))
                else:
                    media.open_image_external(media.DEFAULT_PROFILE)
                log.push("opened profile image in system viewer")
            except Exception as exc:
                log.push(str(exc))
            return
        if bid == "btn-subspecies":
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
        if bid == "btn-reload":
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
        if bid != "btn-save":
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
            self._refresh_pic_status()
            session.clear_dirty()
            log.push(f"saved species → {path}")
            if pic_note:
                log.push(pic_note)
        except Exception as exc:
            log.push(str(exc))
