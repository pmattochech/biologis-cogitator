"""Load species profile schema from YAML (edit file → restart / re-open screen)."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .util import TEMPLATES, load_yaml

SCHEMA_PATH = TEMPLATES / "species-generation-profile.yaml"

_cache: dict[str, Any] | None = None
_cache_mtime: float | None = None


def schema_path() -> Path:
    return SCHEMA_PATH


def load_schema(*, force: bool = False) -> dict[str, Any]:
    """Load profile schema; reloads when the YAML file changes on disk."""
    global _cache, _cache_mtime
    path = SCHEMA_PATH
    if not path.is_file():
        raise FileNotFoundError(
            f"profile schema missing: {path} — restore templates/species-generation-profile.yaml"
        )
    mtime = path.stat().st_mtime
    if not force and _cache is not None and _cache_mtime == mtime:
        return _cache
    data = load_yaml(path)
    if not isinstance(data, dict) or not data.get("steps"):
        raise ValueError(f"invalid profile schema: {path}")
    _cache = data
    _cache_mtime = mtime
    return data


def clear_schema_cache() -> None:
    global _cache, _cache_mtime
    _cache = None
    _cache_mtime = None


def steps(schema: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    sch = schema or load_schema()
    return list(sch.get("steps") or [])


def all_fields(schema: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for step in steps(schema):
        for field in step.get("fields") or []:
            out.append(field)
    return out


def widget_id(field: dict[str, Any]) -> str:
    """Stable DOM id for a field."""
    store = str(field.get("store") or field.get("id") or "field")
    return "qf-" + store.replace(".", "-")


def get_store(profile: dict[str, Any], store: str) -> Any:
    parts = store.split(".")
    cur: Any = profile
    for p in parts:
        if p == "profile":
            continue
        if p == "answers":
            cur = profile.setdefault("answers", {})
            continue
        if not isinstance(cur, dict):
            return None
        cur = cur.get(p)
    if store.startswith("profile."):
        key = store.split(".", 1)[1]
        return profile.get(key)
    return cur


def set_store(profile: dict[str, Any], store: str, value: Any) -> None:
    if store.startswith("profile."):
        key = store.split(".", 1)[1]
        profile[key] = value
        if key == "id":
            profile["magos_scaffold_id"] = value
        return
    if store.startswith("answers."):
        parts = store.split(".")
        # answers.SECTION.key
        answers = profile.setdefault("answers", {})
        if len(parts) != 3:
            raise ValueError(f"bad answers store path: {store}")
        section = answers.setdefault(parts[1], {})
        section[parts[2]] = value
        return
    raise ValueError(f"unknown store path: {store}")


def empty_profile_from_schema(
    schema: dict[str, Any] | None = None,
    *,
    species_id: str = "",
    working_common_name: str = "",
    world_biome: str = "",
    trophic_slot: str = "apex",
) -> dict[str, Any]:
    sch = schema or load_schema()
    profile: dict[str, Any] = {
        "id": species_id.strip(),
        "magos_scaffold_id": species_id.strip(),
        "working_common_name": working_common_name,
        "world_biome": world_biome,
        "trophic_slot": trophic_slot,
        "secondary_biomes": [],
        "range": "single",
        "origin_subtype": "aboriginal",
        "analogue": "",
        "dossier": "",
        "notes": "",
        "answers": {},
        "schema_id": sch.get("id"),
        "schema_version": sch.get("version"),
    }
    for field in all_fields(sch):
        store = str(field.get("store") or "")
        if not store:
            continue
        default = field.get("default", "" if field.get("type") != "yes_no" else False)
        if field.get("type") == "comma_list":
            default = default if isinstance(default, list) else []
        if field.get("type") == "yes_no":
            default = bool(default)
        # Don't clobber meta seeds already set
        existing = get_store(profile, store)
        if existing not in (None, "", [], False) and store.startswith("profile."):
            continue
        if store in (
            "profile.id",
            "profile.working_common_name",
            "profile.world_biome",
            "profile.trophic_slot",
        ):
            continue
        set_store(profile, store, default if default is not None else "")
    # re-apply seeds
    if species_id:
        set_store(profile, "profile.id", species_id.strip())
    if working_common_name:
        set_store(profile, "profile.working_common_name", working_common_name)
    if world_biome:
        set_store(profile, "profile.world_biome", world_biome)
    if trophic_slot:
        set_store(profile, "profile.trophic_slot", trophic_slot)
    return profile


def validate_minimum(
    profile: dict[str, Any], schema: dict[str, Any] | None = None
) -> list[str]:
    sch = schema or load_schema()
    errors: list[str] = []
    minimum = sch.get("minimum") or {}
    for req in minimum.get("required") or []:
        store = str(req.get("store") or "")
        label = str(req.get("label") or store)
        val = get_store(profile, store)
        if val is None or str(val).strip() == "":
            errors.append(f"{label} required")
    for group in minimum.get("any_of") or []:
        stores = list(group.get("stores") or [])
        label = str(group.get("label") or "one of required fields")
        ok = False
        for store in stores:
            val = get_store(profile, store)
            if val is not None and str(val).strip() != "":
                ok = True
                break
        if not ok:
            errors.append(label)
    return errors


def option_pairs(field: dict[str, Any], profile: dict[str, Any] | None = None) -> list[tuple[str, str]]:
    """Return (label, value) pairs for a select field, honoring depends_on."""
    depends = field.get("depends_on")
    options = field.get("options")
    if depends and field.get("options_by"):
        dep_val = ""
        if profile is not None:
            raw = get_store(profile, str(depends))
            dep_val = str(raw or "").strip()
        options = (field.get("options_by") or {}).get(dep_val) or []
    pairs: list[tuple[str, str]] = []
    for opt in options or []:
        if isinstance(opt, dict):
            val = str(opt.get("value") or "")
            label = str(opt.get("label") or val)
            if val:
                pairs.append((label, val))
        else:
            s = str(opt)
            pairs.append((s, s))
    return pairs


def resolve_option_label(field: dict[str, Any], value: str, profile: dict[str, Any] | None = None) -> str:
    for label, val in option_pairs(field, profile):
        if val == value:
            return label
    return value


def min_gate_hint(schema: dict[str, Any] | None = None) -> str:
    sch = schema or load_schema()
    bits = [str(r.get("label") or r.get("store")) for r in (sch.get("minimum") or {}).get("required") or []]
    for g in (sch.get("minimum") or {}).get("any_of") or []:
        bits.append(str(g.get("label") or "any-of group"))
    path = SCHEMA_PATH.name
    return (
        f"Minimum: {'; '.join(bits)}. Schema: templates/{path} "
        "(edit YAML → re-open species screen / restart)."
    )


def field_by_store(store: str, schema: dict[str, Any] | None = None) -> dict[str, Any] | None:
    for field in all_fields(schema):
        if field.get("store") == store:
            return field
    return None
