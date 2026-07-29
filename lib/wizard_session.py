"""WizardSession — guided roll/pick/skip/override over pipeline layers."""
from __future__ import annotations

import copy
from typing import Any

from . import locks as lockmod
from . import packs as packsmod
from . import pipeline
from . import propose_export
from . import entry_id as entryid
from . import species_profile as speciesmod
from . import state as statemod
from .layers import biomes as biomes_layer
from .layers import stellar
from .rngutil import make_rng, pick
from .util import ENUMS, load_yaml, set_active_pack, warn


Provenance = str  # rolled | picked | skipped | locked | overridden


class WizardSession:
    def __init__(
        self,
        *,
        seed: int | None = None,
        pack_id: str | None = None,
    ) -> None:
        self.seed = seed if seed is not None else 42
        self.pack_id = pack_id
        self.system: dict[str, Any] | None = None
        self.body: dict[str, Any] | None = None
        self.species_profiles: dict[str, dict[str, Any]] = {}
        self.provenance: dict[str, Provenance] = {}
        self.warnings: list[str] = []
        self._dirty: bool = False
        # Last editor load target for Reload
        self.edit_resume: dict[str, Any] | None = None
        self._rng = make_rng(self.seed)
        if pack_id:
            set_active_pack(pack_id)

    def mark_dirty(self) -> None:
        self._dirty = True

    def clear_dirty(self) -> None:
        self._dirty = False

    def is_dirty(self) -> bool:
        return bool(self._dirty)

    def reset(self, *, keep_seed: bool = True, pack_id: str | None = None) -> None:
        """Clear system/body for a fresh rite; used when returning to boot menu."""
        seed = self.seed if keep_seed else 42
        self.__init__(seed=seed, pack_id=pack_id)

    def note(self, msg: str) -> None:
        self.warnings.append(msg)
        if self.system is not None:
            warn(self.system, msg)
        if self.body is not None:
            warn(self.body, msg)

    def set_provenance(self, field: str, how: Provenance) -> None:
        self.provenance[field] = how

    # --- system ---

    def start_greenfield_system(self, slug: str, mode: str = "natural") -> dict[str, Any]:
        self.pack_id = None
        set_active_pack(None)
        self.system = statemod.new_system_state(slug, seed=self.seed, spark=True)
        self.system["locks"]["system_mode"] = mode
        stellar.generate_system(self.system, mode=mode, existing=False)
        self.set_provenance("system", "rolled")
        return self.system

    def load_pack_system(self, slug: str, pack_id: str | None = None) -> dict[str, Any]:
        pack = pack_id or self.pack_id
        if pack:
            set_active_pack(pack)
            self.pack_id = pack
        self.system = pipeline.generate_system(
            slug, seed=self.seed, spark=False, existing=True, pack=pack
        )
        self.set_provenance("system", "locked")
        return self.system

    def load_system_from_out(self, slug: str) -> dict[str, Any]:
        """Load a previously generated system from cogitator-results/systems/<slug>/."""
        self.system = statemod.load_system(slug)
        self.set_provenance("system", "locked")
        return self.system

    @staticmethod
    def list_out_systems() -> list[str]:
        from . import out_archive as archive

        return archive.list_out_systems()

    def roll_system_star(self) -> dict[str, Any]:
        assert self.system is not None
        enums = load_yaml(ENUMS / "star_classes.yaml")
        spectral = pick(self._rng, enums["spectral"])
        size_band = pick(self._rng, enums["size_bands"])
        star = {
            "spectral": spectral,
            "size_band": size_band,
            "label": f"{spectral}-{size_band}",
        }
        locked = (self.system.get("locks") or {}).get("star")
        if locked and locked != star:
            lockmod.override_field(self.system, "star", locked, star)
            self.set_provenance("star", "overridden")
        else:
            self.set_provenance("star", "rolled")
        self.system["layers"]["star"] = star
        return star

    def pick_system_star(self, spectral: str, size_band: str) -> dict[str, Any]:
        assert self.system is not None
        star = {
            "spectral": spectral,
            "size_band": size_band,
            "label": f"{spectral}-{size_band}",
        }
        locked = (self.system.get("locks") or {}).get("star")
        if locked and (
            locked.get("spectral") != spectral or locked.get("size_band") != size_band
        ):
            lockmod.override_field(self.system, "star", locked, star)
            self.set_provenance("star", "overridden")
        else:
            self.set_provenance("star", "picked")
        self.system["layers"]["star"] = star
        return star

    def skip_system_star(self) -> dict[str, Any]:
        assert self.system is not None
        star = self.system["layers"].get("star") or {
            "spectral": "G",
            "size_band": "dwarf",
            "label": "G-dwarf",
        }
        self.system["layers"]["star"] = star
        self.set_provenance("star", "skipped")
        return star

    def set_system_mode(self, mode: str, *, how: Provenance = "picked") -> None:
        assert self.system is not None
        locked = (self.system.get("locks") or {}).get("system_mode")
        if locked and locked != mode:
            lockmod.override_field(self.system, "system_mode", locked, mode)
            how = "overridden"
        self.system["layers"]["system_mode"] = mode
        self.system["locks"]["system_mode"] = mode
        self.set_provenance("system_mode", how)

    def save_system_out(self) -> str:
        assert self.system is not None
        path = statemod.save_system(self.system)
        pipeline._write_system_md(self.system)
        return str(path)

    # --- body ---

    def start_body(self, slug: str, *, use_lock: bool = True) -> dict[str, Any]:
        assert self.system is not None
        system_slug = self.system["meta"]["slug"]
        self.body = statemod.new_world_state(
            slug, system_slug=system_slug, seed=self.seed, spark=True
        )
        if use_lock:
            try:
                lock = lockmod.load_body_lock(slug, pack=self.pack_id)
                lockmod.apply_body_lock(self.body, lock)
                self.set_provenance("body_lock", "locked")
            except FileNotFoundError:
                self.note(f"no body lock for {slug}; greenfield body")
                self.set_provenance("body_lock", "skipped")
        pipeline.run_body_layers(self.body, self.system)
        from . import entry_id as entryid

        entryid.ensure_world_filing_ids(self.body)
        return self.body

    def reroll_body_layers(self) -> None:
        assert self.body is not None
        self.body["meta"]["spark"] = True
        locks = copy.deepcopy(self.body.get("locks") or {})
        system_slug = self.body["meta"].get("system_slug")
        slug = self.body["meta"]["slug"]
        seed = self.body["meta"].get("seed")
        self.body = statemod.new_world_state(
            slug, system_slug=system_slug, seed=seed, spark=True
        )
        self.body["locks"] = locks
        pipeline.run_body_layers(self.body, self.system)
        self.set_provenance("body_layers", "rolled")

    def pick_planet_type(self, planet_type: str, body_kind: str = "planet") -> None:
        assert self.body is not None
        locked = (self.body.get("locks") or {}).get("planet_type")
        if locked and locked != planet_type:
            lockmod.override_field(self.body, "planet_type", locked, planet_type)
            self.set_provenance("planet_type", "overridden")
        else:
            self.set_provenance("planet_type", "picked")
        self.body["locks"]["planet_type"] = planet_type
        self.body["locks"]["body_kind"] = body_kind
        pipeline.run_body_layers(self.body, self.system)
        self.mark_dirty()

    def pick_immaterium(self, grade: str) -> None:
        assert self.body is not None
        locked = (self.body.get("locks") or {}).get("immaterium_stress")
        chem = (self.body.get("locks") or {}).get("chemistry_climate") or {}
        locked = locked or chem.get("immaterium_stress")
        if locked and locked != grade:
            lockmod.override_field(self.body, "immaterium_stress", locked, grade)
            self.set_provenance("immaterium_stress", "overridden")
        else:
            self.set_provenance("immaterium_stress", "picked")
        self.body["locks"]["immaterium_stress"] = grade
        self.body.setdefault("locks", {}).setdefault("chemistry_climate", {})[
            "immaterium_stress"
        ] = grade
        pipeline.run_body_layers(self.body, self.system)
        self.mark_dirty()

    # --- biomes ---

    def list_biome_classes(self) -> list[str]:
        from . import custom_enums

        return [c["id"] for c in custom_enums.merged_biome_classes(self.pack_id) if c.get("id")]

    def list_richness(self) -> list[str]:
        return ["null", "barren", "sparse", "moderate", "rich"]

    def current_biomes(self) -> list[dict[str, Any]]:
        if not self.body:
            return []
        return list((self.body.get("layers") or {}).get("biomes") or [])

    def _sync_biome_locks_and_rebuild(self, biomes: list[dict[str, Any]]) -> None:
        assert self.body is not None
        locked = (self.body.get("locks") or {}).get("biomes")
        if locked and locked != biomes:
            lockmod.override_field(self.body, "biomes", locked, biomes)
            self.set_provenance("biomes", "overridden")
        self.body.setdefault("locks", {})["biomes"] = copy.deepcopy(biomes)
        pipeline.run_body_layers(self.body, self.system)
        self.mark_dirty()

    def add_biome(
        self,
        class_id: str,
        richness: str = "moderate",
        *,
        instance_id: str | None = None,
    ) -> dict[str, Any]:
        assert self.body is not None
        from . import custom_enums
        from .layers import biomes as biomes_layer

        biomes = copy.deepcopy(self.current_biomes())
        meta = next(
            (
                c
                for c in custom_enums.merged_biome_classes(self.pack_id)
                if c.get("id") == class_id
            ),
            {},
        )
        slug = str((self.body.get("meta") or {}).get("slug") or "")
        used = {str(b.get("id") or "") for b in biomes}
        entry = {
            "id": biomes_layer.unique_biome_instance_id(
                class_id,
                body_slug=slug,
                used=used,
                preferred=instance_id,
            ),
            "class": class_id,
            "richness": richness or meta.get("default_richness", "moderate"),
            "medium": meta.get("medium", "terrestrial"),
            "overlay": bool(meta.get("overlay")),
        }
        from . import entry_id as entryid

        entry["filing_id"] = entryid.allocate_biome_filing_id(
            str(entry["id"]),
            body_slug=slug,
            class_id=class_id,
            label=class_id,
        )
        biomes.append(entry)
        if self.provenance.get("biomes") != "overridden":
            self.set_provenance("biomes", "picked")
        self._sync_biome_locks_and_rebuild(biomes)
        return entry

    def remove_biome(self, biome_id: str) -> None:
        assert self.body is not None
        biomes = [b for b in self.current_biomes() if b.get("id") != biome_id]
        if self.provenance.get("biomes") != "overridden":
            self.set_provenance("biomes", "picked")
        self._sync_biome_locks_and_rebuild(biomes)

    def roll_biomes(self) -> list[dict[str, Any]]:
        """Clear lock biomes and spark-infer a new set via layer."""
        assert self.body is not None
        locks = self.body.setdefault("locks", {})
        old = locks.get("biomes")
        if "biomes" in locks:
            del locks["biomes"]
        self.body["meta"]["spark"] = True
        pipeline.run_body_layers(self.body, self.system)
        self.body["layers"]["biomes"] = []
        biomes_layer.apply(self.body)
        new_biomes = copy.deepcopy(self.body["layers"]["biomes"])
        if old and old != new_biomes:
            lockmod.override_field(self.body, "biomes", old, new_biomes)
            self.set_provenance("biomes", "overridden")
        else:
            self.set_provenance("biomes", "rolled")
        locks["biomes"] = copy.deepcopy(new_biomes)
        from . import entry_id as entryid

        entryid.ensure_world_filing_ids(self.body)
        pipeline.run_body_layers(self.body, self.system)
        self.mark_dirty()
        return self.current_biomes()

    def skip_biomes(self) -> list[dict[str, Any]]:
        """Keep current biomes unchanged."""
        assert self.body is not None
        self.set_provenance("biomes", "skipped")
        return self.current_biomes()

    def finalize(self) -> dict[str, Any]:
        """Seal body: sync species profiles → specimen locks → trophic → Magos/literary."""
        assert self.body is not None
        from . import entry_id as entryid
        from .layers import trophic

        entryid.ensure_world_filing_ids(self.body)
        if self.system is not None:
            self.save_system_out()

        # Merge disk profiles with session so Seal always sees every created/edited form.
        slug = self.body_slug()
        merged: dict[str, dict[str, Any]] = {}
        if slug:
            merged.update(speciesmod.load_all_profiles(slug))
        merged.update(copy.deepcopy(self.species_profiles))
        self.species_profiles = merged

        # Named profiles drive thin locks (name/notes/biomes) before webs rebuild.
        for sid, prof in merged.items():
            self.upsert_specimen(speciesmod.profile_to_specimen_lock(prof))
        trophic.apply(self.body)

        world = pipeline.finalize_body(
            self.body, species_profiles=merged or None
        )
        self.clear_dirty()
        return world

    def save_pack_lock(self, pack_id: str | None = None) -> str:
        """Write current body (and system if present) into pack YAML locks."""
        pid = pack_id or self.pack_id
        if not pid:
            raise ValueError("pack_id required to save lock")
        if self.body is None:
            raise ValueError("no body to save")
        from . import entry_id as entryid

        entryid.ensure_world_filing_ids(self.body)
        set_active_pack(pid)
        self.pack_id = pid
        path = packsmod.write_body_lock(self.body, pid)
        if self.system is not None:
            packsmod.export_pack(
                pid,
                title=pid,
                description="",
                system=self.system,
                body=None,
            )
        self.set_provenance("pack_lock", "picked")
        self.clear_dirty()
        return str(path)

    def set_prose_override(self, kind: str, text: str) -> None:
        assert self.body is not None
        if kind not in ("magos", "literary"):
            raise ValueError("kind must be magos or literary")
        prose = dict((self.body.get("locks") or {}).get("prose") or {})
        prose[kind] = text
        self.body.setdefault("locks", {})["prose"] = prose
        self.set_provenance(f"prose_{kind}", "picked")
        self.mark_dirty()

    def clear_prose_override(self, kind: str) -> None:
        assert self.body is not None
        prose = dict((self.body.get("locks") or {}).get("prose") or {})
        if kind in prose:
            del prose[kind]
        if prose:
            self.body.setdefault("locks", {})["prose"] = prose
        else:
            self.body.setdefault("locks", {}).pop("prose", None)
        self.set_provenance(f"prose_{kind}", "skipped")
        self.mark_dirty()

    def generated_prose_preview(self, kind: str) -> str:
        """Return what L7 would generate without override."""
        assert self.body is not None
        from . import render as rendermod

        body = copy.deepcopy(self.body)
        body.setdefault("locks", {}).pop("prose", None)
        profiles = self.species_profiles or speciesmod.load_all_profiles(
            str((body.get("meta") or {}).get("slug") or "")
        )
        if kind == "magos":
            return rendermod._magos(body, profiles)
        return rendermod._literary(body, profiles)

    def load_body_for_edit(
        self,
        slug: str,
        *,
        pack_id: str | None = None,
        from_results: bool = False,
    ) -> dict[str, Any]:
        """Load a body for the Editor hub (pack regenerate or sealed state)."""
        pack = pack_id or self.pack_id
        if pack:
            set_active_pack(pack)
            self.pack_id = pack
        if from_results:
            self.body = statemod.load_world(slug)
            sys_slug = self.body["meta"].get("system_slug")
            if sys_slug:
                try:
                    self.system = statemod.load_system(sys_slug)
                except FileNotFoundError:
                    if pack:
                        try:
                            self.system = self.load_pack_system(sys_slug, pack)
                        except Exception:
                            self.system = None
            self.set_provenance("edit", "locked")
            self.reload_species_profiles()
            from . import entry_id as entryid

            entryid.ensure_world_filing_ids(self.body)
            self.edit_resume = {
                "slug": slug,
                "pack_id": self.pack_id,
                "from_results": True,
            }
            self.clear_dirty()
            return self.body
        # From pack: need system then body layers
        lock = lockmod.load_body_lock(slug, pack=pack)
        sys_slug = lock.get("system_slug")
        if sys_slug:
            try:
                self.load_pack_system(sys_slug, pack)
            except Exception:
                try:
                    self.load_system_from_out(sys_slug)
                except FileNotFoundError:
                    self.system = None
        if self.system is None:
            # minimal placeholder system
            self.system = statemod.new_system_state(
                sys_slug or "unknown-system", seed=self.seed, spark=False
            )
        body = self.start_body(slug, use_lock=True)
        self.reload_species_profiles()
        self.edit_resume = {
            "slug": slug,
            "pack_id": self.pack_id,
            "from_results": False,
        }
        self.clear_dirty()
        return body

    def update_lock_fields(self, updates: dict[str, Any]) -> None:
        """Patch body locks and rebuild layers."""
        assert self.body is not None
        locks = self.body.setdefault("locks", {})
        for k, v in updates.items():
            locks[k] = v
        pipeline.run_body_layers(self.body, self.system)
        self.set_provenance("lock_fields", "picked")
        self.mark_dirty()

    def update_geology_lock(self, fields: dict[str, Any]) -> None:
        assert self.body is not None
        geo = dict((self.body.get("locks") or {}).get("geology") or {})
        geo.update(fields)
        self.body.setdefault("locks", {})["geology"] = geo
        for k, v in fields.items():
            if k in ("gravity_g", "topology", "connectivity", "volcanism", "crust", "tidal_lock"):
                self.body["locks"][k] = v
        pipeline.run_body_layers(self.body, self.system)
        self.set_provenance("geology", "picked")
        self.mark_dirty()

    def update_chem_lock(self, fields: dict[str, Any]) -> None:
        assert self.body is not None
        chem = dict((self.body.get("locks") or {}).get("chemistry_climate") or {})
        chem.update(fields)
        self.body.setdefault("locks", {})["chemistry_climate"] = chem
        if "immaterium_stress" in fields:
            self.body["locks"]["immaterium_stress"] = fields["immaterium_stress"]
        pipeline.run_body_layers(self.body, self.system)
        self.set_provenance("chemistry_climate", "picked")
        self.mark_dirty()

    def current_specimens(self) -> list[dict[str, Any]]:
        if not self.body:
            return []
        return list((self.body.get("locks") or {}).get("specimens") or [])

    def set_specimens(self, specimens: list[dict[str, Any]]) -> None:
        assert self.body is not None
        self.body.setdefault("locks", {})["specimens"] = copy.deepcopy(specimens)
        pipeline.run_body_layers(self.body, self.system)
        self.set_provenance("specimens", "picked")
        self.mark_dirty()

    def upsert_specimen(self, spec: dict[str, Any]) -> None:
        specs = copy.deepcopy(self.current_specimens())
        sid = spec.get("id")
        if not sid:
            raise ValueError("specimen needs id")
        specs = [s for s in specs if s.get("id") != sid]
        specs.append(spec)
        self.set_specimens(specs)

    def remove_specimen(self, specimen_id: str) -> None:
        specs = [s for s in self.current_specimens() if s.get("id") != specimen_id]
        self.set_specimens(specs)
        self.species_profiles.pop(specimen_id, None)

    def body_slug(self) -> str | None:
        if not self.body:
            return None
        return str((self.body.get("meta") or {}).get("slug") or "") or None

    def reload_species_profiles(self) -> None:
        slug = self.body_slug()
        self.species_profiles = {}
        if not slug:
            return
        self.species_profiles = speciesmod.load_all_profiles(slug)
        # Seed thin locks that lack a profile yet (edit existing specimen)
        for spec in self.current_specimens():
            sid = str(spec.get("id") or "")
            if sid and sid not in self.species_profiles:
                # keep memory empty until user opens profile; do not invent
                continue

    def get_species_profile(self, species_id: str) -> dict[str, Any] | None:
        if species_id in self.species_profiles:
            return copy.deepcopy(self.species_profiles[species_id])
        slug = self.body_slug()
        if slug:
            loaded = speciesmod.load_species_profile(slug, species_id)
            if loaded:
                self.species_profiles[species_id] = copy.deepcopy(loaded)
                return copy.deepcopy(loaded)
        spec = next(
            (s for s in self.current_specimens() if s.get("id") == species_id), None
        )
        if spec:
            return speciesmod.specimen_lock_to_profile_seed(spec)
        return None

    def save_species_profile(self, profile: dict[str, Any]) -> str:
        """Validate minimum, write planet/species/<id>/, upsert thin pack lock."""
        assert self.body is not None
        slug = self.body_slug()
        if not slug:
            raise ValueError("body slug required")
        errors = speciesmod.validate_minimum(
            profile, body_biomes=self.current_biomes()
        )
        if errors:
            raise ValueError("; ".join(errors))
        profile = copy.deepcopy(profile)
        sid = entryid.normalize_entry_id(str(profile.get("id") or ""))
        profile["id"] = sid
        profile["magos_scaffold_id"] = sid
        path = speciesmod.save_species_profile(
            slug, profile, body_biomes=self.current_biomes()
        )
        self.species_profiles[sid] = copy.deepcopy(profile)
        self.upsert_specimen(speciesmod.profile_to_specimen_lock(profile))
        self.set_provenance(f"species:{sid}", "picked")
        return str(path)

    def save_as_pack(
        self,
        pack_id: str,
        *,
        title: str | None = None,
        description: str | None = None,
    ) -> str:
        root = packsmod.export_pack(
            pack_id,
            title=title,
            description=description,
            system=self.system,
            body=self.body,
        )
        self.pack_id = packsmod.slugify_pack_id(pack_id)
        set_active_pack(self.pack_id)
        return str(root)

    def propose_export_text(self) -> str:
        assert self.body is not None
        return propose_export.format_report(self.body)

    def planet_types(self) -> list[str]:
        from . import custom_enums

        return custom_enums.merged_planet_types(self.pack_id)

    def body_kinds(self) -> list[str]:
        from . import custom_enums

        return custom_enums.merged_body_kinds(self.pack_id)

    def immaterium_grades(self) -> list[str]:
        return list(load_yaml(ENUMS / "immaterium_stress.yaml").get("grades") or [])

    def star_spectrals(self) -> list[str]:
        return list(load_yaml(ENUMS / "star_classes.yaml").get("spectral") or [])

    def star_sizes(self) -> list[str]:
        return list(load_yaml(ENUMS / "star_classes.yaml").get("size_bands") or [])

    def star_spectral_options(self) -> list[tuple[str, str]]:
        """Select options: (label_with_gloss, value)."""
        data = load_yaml(ENUMS / "star_classes.yaml")
        gloss = dict(data.get("spectral_gloss") or {})
        out: list[tuple[str, str]] = []
        for s in data.get("spectral") or []:
            g = gloss.get(s)
            out.append((f"{s} — {g}" if g else str(s), str(s)))
        return out

    def star_size_options(self) -> list[tuple[str, str]]:
        data = load_yaml(ENUMS / "star_classes.yaml")
        gloss = dict(data.get("size_band_gloss") or {})
        out: list[tuple[str, str]] = []
        for s in data.get("size_bands") or []:
            g = gloss.get(s)
            out.append((f"{s} — {g}" if g else str(s), str(s)))
        return out

    def star_lexicon_text(self, spectral: str | None = None, size_band: str | None = None) -> str:
        """Short Magos panel for the stellar rite."""
        data = load_yaml(ENUMS / "star_classes.yaml")
        sg = dict(data.get("spectral_gloss") or {})
        zg = dict(data.get("size_band_gloss") or {})
        lines = [
            "STAR LEXICON (L-1) — fiction-grade, not HR-diagram physics.",
            "Letters are Harvard spectral classes (temperature), not English words.",
            "Classic hot→cool ladder: O B A F G K M — this altar exposes M K G F only.",
            "Label = {spectral}-{size_band}  (e.g. G-dwarf ≈ Sol-like main sequence).",
            "",
            "Spectral (cool → warmer):",
        ]
        for s in data.get("spectral") or []:
            mark = "►" if s == spectral else " "
            lines.append(f"  {mark} {s} — {sg.get(s, '')}")
        lines.append("")
        lines.append("Size band (how big / evolved / bright):")
        for s in data.get("size_bands") or []:
            mark = "►" if s == size_band else " "
            lines.append(f"  {mark} {s} — {zg.get(s, '')}")
        if spectral and size_band:
            lines.append("")
            lines.append(f"Current pick → {spectral}-{size_band}")
        return "\n".join(lines)

    def trophic_slots(self) -> list[str]:
        return list(load_yaml(ENUMS / "trophic_slots.yaml").get("slot_order") or [])

    def origin_subtypes(self) -> dict[str, list[str]]:
        return dict(load_yaml(ENUMS / "origin_subtypes.yaml") or {})
