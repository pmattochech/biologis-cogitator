"""L0 hardlock ingest — pack-aware (CV is an optional pack)."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .util import (
    LOCKS_BODIES,
    LOCKS_SYSTEMS,
    PACKS,
    get_active_pack,
    load_yaml,
    warn,
)


def _pack_bodies(pack_id: str) -> Path:
    return PACKS / pack_id / "bodies"


def _pack_systems(pack_id: str) -> Path:
    return PACKS / pack_id / "systems"


def body_lock_path(
    slug: str,
    override: Path | None = None,
    pack: str | None = None,
) -> Path:
    if override is not None:
        return override
    pack_id = pack or get_active_pack()
    if pack_id:
        return _pack_bodies(pack_id) / f"{slug}.yaml"
    # Legacy fallback
    return LOCKS_BODIES / f"{slug}.yaml"


def system_lock_path(slug: str, pack: str | None = None) -> Path:
    pack_id = pack or get_active_pack()
    if pack_id:
        return _pack_systems(pack_id) / f"{slug}.yaml"
    return LOCKS_SYSTEMS / f"{slug}.yaml"


def _resolve_body_path(slug: str, override: Path | None, pack: str | None) -> Path:
    if override is not None:
        return override
    pack_id = pack or get_active_pack()
    candidates: list[Path] = []
    if pack_id:
        candidates.append(_pack_bodies(pack_id) / f"{slug}.yaml")
    # Search all packs if no pack / miss
    if PACKS.is_dir():
        for p in sorted(PACKS.iterdir()):
            cand = p / "bodies" / f"{slug}.yaml"
            if cand not in candidates:
                candidates.append(cand)
    if LOCKS_BODIES.is_dir():
        candidates.append(LOCKS_BODIES / f"{slug}.yaml")
    for c in candidates:
        if c.is_file():
            return c
    # Prefer active pack path for error message
    return body_lock_path(slug, override, pack)


def _resolve_system_path(slug: str, pack: str | None) -> Path | None:
    pack_id = pack or get_active_pack()
    candidates: list[Path] = []
    if pack_id:
        candidates.append(_pack_systems(pack_id) / f"{slug}.yaml")
    if PACKS.is_dir():
        for p in sorted(PACKS.iterdir()):
            cand = p / "systems" / f"{slug}.yaml"
            if cand not in candidates:
                candidates.append(cand)
    if LOCKS_SYSTEMS.is_dir():
        candidates.append(LOCKS_SYSTEMS / f"{slug}.yaml")
    for c in candidates:
        if c.is_file():
            return c
    return None


def load_body_lock(
    slug: str,
    override: Path | None = None,
    pack: str | None = None,
) -> dict[str, Any]:
    path = _resolve_body_path(slug, override, pack)
    if not path.is_file():
        raise FileNotFoundError(f"Body lock not found: {path}")
    data = load_yaml(path)
    data["_path"] = str(path)
    return data


def load_system_lock(slug: str, pack: str | None = None) -> dict[str, Any] | None:
    path = _resolve_system_path(slug, pack)
    if path is None:
        return None
    data = load_yaml(path)
    data["_path"] = str(path)
    return data


def apply_body_lock(world: dict[str, Any], lock: dict[str, Any]) -> None:
    """Merge lock fields into world.locks; locks win over empty generated fields."""
    wl = world["locks"]
    sources = list(wl.get("sources") or [])
    if lock.get("_path"):
        sources.append(lock["_path"])
    for src in lock.get("sources") or []:
        if src not in sources:
            sources.append(src)
    wl["sources"] = sources

    for key in (
        "topology",
        "planet_type",
        "body_kind",
        "notes",
        "local_notes",
        "stellar",
        "system_slug",
        "filing_id",
        "immaterium_stress",
        "gravity_g",
        "atmosphere",
        "water",
        "cryosphere",
        "connectivity",
        "volcanism",
        "crust",
        "tidal_lock",
    ):
        if key in lock and lock[key] is not None:
            wl[key] = lock[key]
    if lock.get("filing_id"):
        world.setdefault("meta", {})["filing_id"] = lock["filing_id"]

    if lock.get("biomes"):
        wl["biomes"] = list(lock["biomes"])
    if lock.get("specimens"):
        wl["specimens"] = list(lock["specimens"])
    if lock.get("risks"):
        wl["risks"] = list(lock["risks"])
    if lock.get("geology"):
        wl["geology"] = dict(lock["geology"])
    if lock.get("chemistry_climate"):
        wl["chemistry_climate"] = dict(lock["chemistry_climate"])
    if lock.get("prose"):
        wl["prose"] = dict(lock["prose"])

    if lock.get("system_slug") and not world["meta"].get("system_slug"):
        world["meta"]["system_slug"] = lock["system_slug"]


def apply_system_lock(system: dict[str, Any], lock: dict[str, Any]) -> None:
    sl = system.setdefault("locks", {})
    for key in (
        "system_mode",
        "star",
        "bodies",
        "formations",
        "notes",
        "companions",
        "orbit_bands",
    ):
        if key in lock and lock[key] is not None:
            sl[key] = lock[key]
    if lock.get("_path"):
        system.setdefault("warnings", [])
        sl["sources"] = [lock["_path"]]


def pin_field(world: dict[str, Any], layer_key: str, field: str, value: Any) -> None:
    """Record that a generated value lost to a lock."""
    warn(
        world,
        f"lock wins: layers.{layer_key}.{field} kept lock value {value!r}",
    )


def override_field(
    state: dict[str, Any],
    field: str,
    locked: Any,
    user: Any,
) -> None:
    """User overrode a lock — keep user value, record warning."""
    warn(state, f"override: {field} lock={locked!r} user={user!r}")
