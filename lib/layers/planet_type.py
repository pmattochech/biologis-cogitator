"""L1 Imperial planet type."""
from __future__ import annotations

from typing import Any

from ..rngutil import make_rng, pick
from ..util import ENUMS, load_yaml, warn


def apply(world: dict[str, Any], system: dict[str, Any] | None = None) -> None:
    enums = load_yaml(ENUMS / "planet_types.yaml")
    types = list(enums.get("planet_types") or [])
    kinds = list(enums.get("body_kinds") or [])
    locks = world.get("locks") or {}
    spark = bool(world["meta"].get("spark"))
    rng = make_rng(world["meta"].get("seed"))

    body_kind = locks.get("body_kind") or "planet"
    if body_kind not in kinds:
        warn(world, f"unknown body_kind {body_kind!r}; coercing to planet")
        body_kind = "planet"

    locked_type = locks.get("planet_type")
    if locked_type:
        if locked_type not in types:
            warn(
                world,
                f"lock planet_type {locked_type!r} not in Imperial enum; keeping anyway",
            )
        planet_type = locked_type
    elif spark:
        # Soft bias from orbit band if system present
        band = None
        if system:
            for slot in system.get("layers", {}).get("body_slots") or []:
                if slot.get("slug") == world["meta"]["slug"]:
                    band = slot.get("band")
                    break
        biased = _band_bias(band, types)
        planet_type = pick(rng, biased)
    else:
        planet_type = "civilised_world"

    world["layers"]["planet_type"] = {
        "planet_type": planet_type,
        "body_kind": body_kind,
        "local_notes": locks.get("local_notes") or locks.get("notes") or "",
    }


def _band_bias(band: str | None, types: list[str]) -> list[str]:
    if band == "inner":
        prefer = ["desert_world", "dead_world", "mining_world", "forge_world"]
    elif band == "habitable":
        prefer = [
            "civilised_world",
            "agri_world",
            "hive_world",
            "death_world",
            "feral_world",
            "garden_world",
            "ocean_world",
        ]
    elif band == "outer":
        prefer = ["ice_world", "mining_world", "dead_world", "penal_world"]
    elif band == "ice":
        prefer = ["ice_world", "dead_world", "quarantine_world"]
    else:
        return types
    return [t for t in prefer if t in types] or types
