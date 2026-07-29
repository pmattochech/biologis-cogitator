"""Pack store: list/load/export scenario packs (CV is one pack, not the core)."""
from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Any

from .util import PACKS, dump_yaml, load_yaml, warn


def pack_dir(pack_id: str) -> Path:
    return PACKS / pack_id


def list_packs() -> list[dict[str, Any]]:
    PACKS.mkdir(parents=True, exist_ok=True)
    out: list[dict[str, Any]] = []
    for path in sorted(PACKS.iterdir()):
        if not path.is_dir():
            continue
        meta_path = path / "pack.yaml"
        if meta_path.is_file():
            meta = load_yaml(meta_path)
            meta.setdefault("id", path.name)
            out.append(meta)
        else:
            out.append({"id": path.name, "title": path.name, "description": ""})
    return out


def load_pack_meta(pack_id: str) -> dict[str, Any]:
    path = pack_dir(pack_id) / "pack.yaml"
    if not path.is_file():
        raise FileNotFoundError(f"Pack not found: {pack_id} ({path})")
    meta = load_yaml(path)
    meta.setdefault("id", pack_id)
    return meta


def systems_dir(pack_id: str) -> Path:
    return pack_dir(pack_id) / "systems"


def bodies_dir(pack_id: str) -> Path:
    return pack_dir(pack_id) / "bodies"


def list_system_slugs(pack_id: str) -> list[str]:
    d = systems_dir(pack_id)
    if not d.is_dir():
        return []
    return sorted(p.stem for p in d.glob("*.yaml"))


def list_body_slugs(pack_id: str) -> list[str]:
    d = bodies_dir(pack_id)
    if not d.is_dir():
        return []
    return sorted(p.stem for p in d.glob("*.yaml"))


def slugify_pack_id(name: str) -> str:
    s = name.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-") or "pack"


def export_pack(
    pack_id: str,
    *,
    title: str | None = None,
    description: str | None = None,
    system: dict[str, Any] | None = None,
    body: dict[str, Any] | None = None,
    systems: list[dict[str, Any]] | None = None,
    bodies: list[dict[str, Any]] | None = None,
) -> Path:
    """Write/update a pack from session state (system + body dicts).

    Existing pack.yaml title/description are kept unless new values are passed.
    Body/system YAML files are upserted; other pack members are left intact.
    """
    pack_id = slugify_pack_id(pack_id)
    root = pack_dir(pack_id)
    systems_path = root / "systems"
    bodies_path = root / "bodies"
    systems_path.mkdir(parents=True, exist_ok=True)
    bodies_path.mkdir(parents=True, exist_ok=True)

    sys_list = list(systems or [])
    if system:
        sys_list.append(system)
    body_list = list(bodies or [])
    if body:
        body_list.append(body)

    written_systems: list[str] = []
    for s in sys_list:
        slug = (s.get("meta") or {}).get("slug") or s.get("slug")
        if not slug:
            continue
        yaml_body = _system_to_lock(s)
        dump_yaml(systems_path / f"{slug}.yaml", yaml_body)
        written_systems.append(slug)

    written_bodies: list[str] = []
    for w in body_list:
        slug = (w.get("meta") or {}).get("slug") or w.get("slug")
        if not slug:
            continue
        yaml_body = _world_to_lock(w)
        dump_yaml(bodies_path / f"{slug}.yaml", yaml_body)
        written_bodies.append(slug)

    # Merge with existing pack.yaml system list if present
    meta_path = root / "pack.yaml"
    existing_systems: list[str] = []
    old_title = pack_id
    old_desc = ""
    if meta_path.is_file():
        old = load_yaml(meta_path)
        existing_systems = list(old.get("systems") or [])
        old_title = str(old.get("title") or pack_id)
        old_desc = str(old.get("description") or "")
    all_systems = sorted(
        set(existing_systems) | set(written_systems) | set(list_system_slugs(pack_id))
    )

    dump_yaml(
        meta_path,
        {
            "id": pack_id,
            "title": title if title is not None else old_title,
            "description": description if description is not None else old_desc,
            "systems": all_systems,
        },
    )
    return root


def _system_to_lock(system: dict[str, Any]) -> dict[str, Any]:
    locks = dict(system.get("locks") or {})
    layers = system.get("layers") or {}
    out: dict[str, Any] = {}
    out["system_mode"] = layers.get("system_mode") or locks.get("system_mode") or "natural"
    if layers.get("star") or locks.get("star"):
        out["star"] = layers.get("star") or locks.get("star")
    if layers.get("formations") is not None or locks.get("formations") is not None:
        out["formations"] = layers.get("formations") if layers.get("formations") is not None else locks.get("formations")
    if layers.get("companions") is not None or locks.get("companions") is not None:
        out["companions"] = layers.get("companions") if layers.get("companions") is not None else locks.get("companions")
    if layers.get("orbit_bands") or locks.get("orbit_bands"):
        out["orbit_bands"] = layers.get("orbit_bands") or locks.get("orbit_bands")
    slots = layers.get("body_slots") or locks.get("bodies") or []
    if slots:
        out["bodies"] = slots
    if locks.get("notes"):
        out["notes"] = locks["notes"]
    return out


def _world_to_lock(world: dict[str, Any]) -> dict[str, Any]:
    locks = dict(world.get("locks") or {})
    layers = world.get("layers") or {}
    out: dict[str, Any] = {}
    if world["meta"].get("system_slug"):
        out["system_slug"] = world["meta"]["system_slug"]
    out["stellar"] = locks.get("stellar") or "pinned"
    if locks.get("filing_id") or (world.get("meta") or {}).get("filing_id"):
        out["filing_id"] = locks.get("filing_id") or world["meta"].get("filing_id")
    pt = layers.get("planet_type") or {}
    if pt.get("planet_type") or locks.get("planet_type"):
        out["planet_type"] = pt.get("planet_type") or locks.get("planet_type")
    if pt.get("body_kind") or locks.get("body_kind"):
        out["body_kind"] = pt.get("body_kind") or locks.get("body_kind")
    for key in (
        "topology",
        "local_notes",
        "notes",
        "immaterium_stress",
        "risks",
        "specimens",
        "sources",
    ):
        if locks.get(key) is not None:
            out[key] = locks[key]
    if locks.get("prose"):
        out["prose"] = dict(locks["prose"])
    if layers.get("biomes"):
        out["biomes"] = layers["biomes"]
    elif locks.get("biomes"):
        out["biomes"] = locks["biomes"]
    if layers.get("geology"):
        out["geology"] = {
            k: v
            for k, v in (layers["geology"] or {}).items()
            if k
            in (
                "gravity_g",
                "crust",
                "volcanism",
                "connectivity",
                "tidal_lock",
                "hydrosphere_pct",
                "topology",
            )
        }
    elif locks.get("geology"):
        out["geology"] = locks["geology"]
    if layers.get("chemistry_climate"):
        chem = layers["chemistry_climate"] or {}
        out["chemistry_climate"] = {
            k: chem[k]
            for k in (
                "atmosphere",
                "water",
                "solvent",
                "cryosphere",
                "climate_belts",
                "immaterium_stress",
                "immaterium_flavor_tags",
            )
            if k in chem
        }
    elif locks.get("chemistry_climate"):
        out["chemistry_climate"] = locks["chemistry_climate"]
    return out


def write_body_lock(
    world: dict[str, Any],
    pack_id: str,
    *,
    merge_sources: bool = True,
) -> Path:
    """Write/update a single body YAML lock under a pack."""
    slug = (world.get("meta") or {}).get("slug")
    if not slug:
        raise ValueError("world meta.slug required")
    root = bodies_dir(pack_id)
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{slug}.yaml"
    yaml_body = _world_to_lock(world)
    if merge_sources and path.is_file():
        old = load_yaml(path)
        # preserve sources list from disk if session has none
        if not yaml_body.get("sources") and old.get("sources"):
            yaml_body["sources"] = old["sources"]
    dump_yaml(path, yaml_body)
    # ensure pack.yaml lists system if known
    meta_path = pack_dir(pack_id) / "pack.yaml"
    if meta_path.is_file():
        meta = load_yaml(meta_path)
    else:
        meta = {"id": pack_id, "title": pack_id, "description": "", "systems": []}
    sys_slug = yaml_body.get("system_slug")
    if sys_slug:
        systems = list(meta.get("systems") or [])
        if sys_slug not in systems:
            systems.append(sys_slug)
            meta["systems"] = sorted(systems)
            dump_yaml(meta_path, meta)
    return path


def note_override(state: dict[str, Any], field: str, locked: Any, user: Any) -> None:
    warn(state, f"override: {field} lock={locked!r} user={user!r}")
