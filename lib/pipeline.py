"""Pipeline orchestration: system (L-1) and body (L0–L7)."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from . import locks as lockmod
from . import state as statemod
from .layers import (
    bauplan,
    biomes,
    chem_climate,
    geology,
    planet_type,
    stellar,
    trophic,
)
from . import render
from .util import set_active_pack, warn


LAYER_CONTRACTS = [
    ("L-1", "Stellar / system", "Star, orbit bands, companions, formations, body slots"),
    ("L0", "Hardlock ingest", "Curated YAML locks into WorldState.locks"),
    ("L1", "Imperial planet type", "Administratum planet_type + body_kind"),
    ("L2", "Geology", "Gravity, crust, volcanism, connectivity, hydrosphere"),
    ("L3", "Chemistry + climate", "Atmosphere, water, cryosphere, immaterium_stress"),
    ("L4", "Biomes", "Biome list with richness, medium, overlay"),
    ("L5", "Trophic niches", "Per-biome food webs, origin + origin_subtype"),
    ("L6", "Bauplan", "Body plan constrained by biome medium"),
    ("L7", "Dual render", "Magos dossier + literary brief + state.json"),
]


def generate_system(
    slug: str,
    *,
    seed: int | None = None,
    spark: bool = False,
    mode: str = "natural",
    existing: bool = False,
    pack: str | None = None,
) -> dict[str, Any]:
    if pack:
        set_active_pack(pack)
    system = statemod.new_system_state(slug, seed=seed, spark=spark)
    lock = lockmod.load_system_lock(slug, pack=pack)
    if lock:
        lockmod.apply_system_lock(system, lock)
        # If lock exists and user asked existing, or lock has star/bodies, treat as pin
        if existing or lock.get("star") or lock.get("system_mode") == "engineered_mesh":
            existing = True
            if lock.get("system_mode"):
                mode = lock["system_mode"]
    elif existing:
        warn(system, f"--existing but no lock file for {slug}; generating empty pin shell")

    stellar.generate_system(system, mode=mode, existing=existing)
    path = statemod.save_system(system)
    # also write short markdown summary
    _write_system_md(system)
    system["_saved"] = str(path)
    return system


def generate_body(
    slug: str,
    *,
    seed: int | None = None,
    spark: bool = False,
    from_lock: Path | None = None,
    system_slug: str | None = None,
    existing_system: str | None = None,
    pack: str | None = None,
) -> dict[str, Any]:
    if pack:
        set_active_pack(pack)
    # Resolve system: existing pin/load, or require prior generate-system
    resolved_system_slug = existing_system or system_slug
    system_state: dict[str, Any] | None = None

    # L0 lock first (may declare system_slug)
    try:
        body_lock = lockmod.load_body_lock(slug, from_lock, pack=pack)
    except FileNotFoundError:
        body_lock = None

    if body_lock and body_lock.get("system_slug") and not resolved_system_slug:
        resolved_system_slug = body_lock["system_slug"]

    if existing_system:
        # Pin/load system; skip L-1 rolls
        lock = lockmod.load_system_lock(existing_system, pack=pack)
        system_state = statemod.new_system_state(
            existing_system, seed=seed, spark=False
        )
        if lock:
            lockmod.apply_system_lock(system_state, lock)
        stellar.generate_system(system_state, mode=lock.get("system_mode", "natural") if lock else "natural", existing=True)
        statemod.save_system(system_state)
        _write_system_md(system_state)
        resolved_system_slug = existing_system
    elif resolved_system_slug:
        try:
            system_state = statemod.load_system(resolved_system_slug)
        except FileNotFoundError:
            # Auto-load from system lock as pinned
            lock = lockmod.load_system_lock(resolved_system_slug, pack=pack)
            if not lock:
                raise FileNotFoundError(
                    f"System '{resolved_system_slug}' not found in cogitator-results/ and no system lock. "

                    f"Run: ./run generate-system {resolved_system_slug} "
                    f"or pass --existing-system {resolved_system_slug}"
                    + (f" --pack {pack}" if pack else "")
                )
            system_state = generate_system(
                resolved_system_slug,
                seed=seed,
                spark=False,
                mode=lock.get("system_mode") or "natural",
                existing=True,
                pack=pack,
            )
    else:
        raise ValueError(
            "Body generation requires a system. Pass --system <slug>, "
            "--existing-system <slug>, or set system_slug in the body lock."
        )

    world = statemod.new_world_state(
        slug,
        system_slug=resolved_system_slug,
        seed=seed,
        spark=spark,
    )

    if body_lock:
        lockmod.apply_body_lock(world, body_lock)
        if world["locks"].get("stellar") in ("pinned", "skip"):
            # already using existing system
            pass
    else:
        warn(world, f"no body lock for {slug}; generating from planet_type inference only")

    # L1–L6
    planet_type.apply(world, system_state)
    geology.apply(world, system_state)
    chem_climate.apply(world, system_state)
    biomes.apply(world)
    trophic.apply(world)
    bauplan.apply(world)

    # L7
    render.render_all(world)
    statemod.save_world(world)
    return world


def run_body_layers(world: dict[str, Any], system_state: dict[str, Any] | None) -> None:
    """Re-run L1–L6 on an existing WorldState (wizard use)."""
    planet_type.apply(world, system_state)
    geology.apply(world, system_state)
    chem_climate.apply(world, system_state)
    biomes.apply(world)
    trophic.apply(world)
    bauplan.apply(world)


def finalize_body(
    world: dict[str, Any],
    *,
    species_profiles: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    render.render_all(world, species_profiles=species_profiles)
    statemod.save_world(world)
    return world


def _write_system_md(system: dict[str, Any]) -> None:
    slug = system["meta"]["slug"]
    layers = system.get("layers") or {}
    star = layers.get("star") or {}
    lines = [
        f"# System: {slug}",
        "",
        f"- Mode: {layers.get('system_mode', system.get('locks', {}).get('system_mode', 'natural'))}",
        f"- Star: {star.get('label') or star}",
        f"- Companions: {layers.get('companions')}",
        f"- Formations: {layers.get('formations')}",
        f"- Body slots: {len(layers.get('body_slots') or [])}",
        "",
        "## Warnings",
        "",
    ]
    for w in system.get("warnings") or []:
        lines.append(f"- {w}")
    if not system.get("warnings"):
        lines.append("- (none)")
    path = statemod.system_out_dir(slug) / "system.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
