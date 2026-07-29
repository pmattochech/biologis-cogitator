"""L2 Geology."""
from __future__ import annotations

from typing import Any

from ..rngutil import make_rng, pick
from ..util import warn


def apply(world: dict[str, Any], system: dict[str, Any] | None = None) -> None:
    locks = world.get("locks") or {}
    spark = bool(world["meta"].get("spark"))
    rng = make_rng(world["meta"].get("seed"))
    geo_lock = locks.get("geology") or {}

    gravity = geo_lock.get("gravity_g", locks.get("gravity_g"))
    if gravity is None:
        gravity = pick(rng, [0.8, 1.0, 1.1, 1.2]) if spark else 1.0

    crust = geo_lock.get("crust", locks.get("crust"))
    if crust is None:
        crust = pick(rng, ["rocky", "hollow_industrial", "icy", "adamantium_ribbed"]) if spark else "rocky"

    volcanism = geo_lock.get("volcanism", locks.get("volcanism"))
    if volcanism is None:
        volcanism = pick(rng, ["inert", "low", "moderate", "high"]) if spark else "moderate"

    connectivity = geo_lock.get("connectivity", locks.get("connectivity"))
    if connectivity is None:
        connectivity = (
            pick(rng, ["pangaea", "semi_pangaea", "isoterra", "semi_archipelago", "archipelago"])
            if spark
            else "isoterra"
        )

    tidal_lock = geo_lock.get("tidal_lock", locks.get("tidal_lock"))
    if tidal_lock is None:
        tidal_lock = False

    hydrosphere_pct = geo_lock.get("hydrosphere_pct")
    if hydrosphere_pct is None:
        hydrosphere_pct = pick(rng, [10, 30, 50, 70, 90]) if spark else 50

    # Insolation hint from system star
    insolation = "standard"
    if system:
        star = (system.get("layers") or {}).get("star") or {}
        label = star.get("label") or f"{star.get('spectral', 'G')}-{star.get('size_band', 'dwarf')}"
        if star.get("spectral") == "M":
            insolation = "dim"
        elif star.get("spectral") == "F" or star.get("size_band") == "giant":
            insolation = "bright"
        insolation = f"{insolation} ({label})"

    world["layers"]["geology"] = {
        "gravity_g": gravity,
        "crust": crust,
        "volcanism": volcanism,
        "connectivity": connectivity,
        "tidal_lock": bool(tidal_lock),
        "hydrosphere_pct": hydrosphere_pct,
        "insolation_hint": insolation,
        "topology": locks.get("topology") or "",
    }

    # Soft unusual warning
    if tidal_lock and connectivity == "archipelago" and spark:
        warn(world, "soft geology note: tidal lock + archipelago is unusual but allowed")
