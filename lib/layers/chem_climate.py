"""L3 Chemistry + climate + immaterium stress."""
from __future__ import annotations

from typing import Any

from ..rngutil import make_rng, pick
from ..util import ENUMS, load_yaml, warn


def apply(world: dict[str, Any], system: dict[str, Any] | None = None) -> None:
    locks = world.get("locks") or {}
    spark = bool(world["meta"].get("spark"))
    rng = make_rng(world["meta"].get("seed"))
    chem_lock = locks.get("chemistry_climate") or {}
    grades = load_yaml(ENUMS / "immaterium_stress.yaml")
    grade_list = list(grades.get("grades") or ["neutral"])
    default_grade = grades.get("default") or "neutral"

    atmosphere = chem_lock.get("atmosphere", locks.get("atmosphere"))
    if atmosphere is None:
        atmosphere = (
            pick(rng, ["thin", "breathable", "dense", "toxic", "corrosive"])
            if spark
            else "breathable"
        )

    water = chem_lock.get("water", locks.get("water"))
    if water is None:
        water = True if (world["layers"].get("geology") or {}).get("hydrosphere_pct", 50) >= 20 else False

    solvent = chem_lock.get("solvent", "water")
    cryosphere = chem_lock.get("cryosphere", locks.get("cryosphere"))
    if cryosphere is None:
        cryosphere = pick(rng, ["cold", "cool", "moderate", "warm", "hot"]) if spark else "moderate"

    climate_belts = chem_lock.get("climate_belts")
    if climate_belts is None:
        climate_belts = ["equatorial", "temperate", "polar"] if water else ["arid"]

    stress = chem_lock.get("immaterium_stress", locks.get("immaterium_stress"))
    if stress is None:
        if spark:
            # Never auto terminus
            stress = pick(rng, ["neutral", "neutral", "neutral", "minoris", "majoris"])
        else:
            stress = default_grade
    if stress not in grade_list:
        warn(world, f"unknown immaterium_stress {stress!r}; coercing to neutral")
        stress = "neutral"
    if stress == "terminus" and not (
        locks.get("immaterium_stress") == "terminus"
        or chem_lock.get("immaterium_stress") == "terminus"
    ):
        warn(world, "immaterium_stress terminus without lock; downgrading to extremis")
        stress = "extremis"

    flavor_tags = list(chem_lock.get("immaterium_flavor_tags") or locks.get("immaterium_flavor_tags") or [])

    world["layers"]["chemistry_climate"] = {
        "atmosphere": atmosphere,
        "water": bool(water),
        "solvent": solvent,
        "cryosphere": cryosphere,
        "climate_belts": climate_belts,
        "immaterium_stress": stress,
        "immaterium_flavor_tags": flavor_tags,
        "immaterium_description": (grades.get("descriptions") or {}).get(stress, ""),
    }
