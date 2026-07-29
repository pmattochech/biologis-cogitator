"""L-1 stellar / system generation."""
from __future__ import annotations

from typing import Any

from ..rngutil import make_rng, pick, weighted_choice
from ..util import ENUMS, MATRICES, load_yaml, warn


def _load_star_enums() -> dict:
    return load_yaml(ENUMS / "star_classes.yaml")


def _load_sparks() -> dict:
    return load_yaml(MATRICES / "stellar_sparks.yaml")


def generate_system(
    state: dict[str, Any],
    *,
    mode: str = "natural",
    existing: bool = False,
) -> dict[str, Any]:
    """Fill SystemState layers. If existing/pinned, load from locks without rolling."""
    locks = state.get("locks") or {}
    spark = bool(state["meta"].get("spark"))
    rng = make_rng(state["meta"].get("seed"))

    system_mode = locks.get("system_mode") or mode
    state["layers"]["system_mode"] = system_mode

    if existing or locks.get("star"):
        _apply_pinned(state, locks)
        return state

    if system_mode == "engineered_mesh":
        _apply_engineered(state, locks, rng, spark)
        return state

    _roll_natural(state, locks, rng, spark)
    return state


def _apply_pinned(state: dict[str, Any], locks: dict[str, Any]) -> None:
    if locks.get("star"):
        state["layers"]["star"] = dict(locks["star"])
    if locks.get("orbit_bands"):
        state["layers"]["orbit_bands"] = dict(locks["orbit_bands"])
    else:
        state["layers"]["orbit_bands"] = _default_orbit_bands()
    if locks.get("companions") is not None:
        state["layers"]["companions"] = locks["companions"]
    else:
        state["layers"]["companions"] = {"type": "none"}
    if locks.get("formations") is not None:
        state["layers"]["formations"] = list(locks["formations"])
    else:
        state["layers"]["formations"] = []
    if locks.get("bodies"):
        state["layers"]["body_slots"] = [
            {"slug": b, "band": "habitable", "kind": "rocky"} if isinstance(b, str) else b
            for b in locks["bodies"]
        ]
    state["layers"]["pinned"] = True


def _apply_engineered(
    state: dict[str, Any],
    locks: dict[str, Any],
    rng: Any,
    spark: bool,
) -> None:
    star = locks.get("star") or {
        "spectral": "G",
        "size_band": "dwarf",
        "note": "engineered_mesh — stellar context pinned or symbolic",
    }
    state["layers"]["star"] = dict(star)
    state["layers"]["orbit_bands"] = locks.get("orbit_bands") or _default_orbit_bands()
    state["layers"]["companions"] = locks.get("companions") or {"type": "none"}
    state["layers"]["formations"] = list(locks.get("formations") or [])
    bodies = locks.get("bodies") or []
    state["layers"]["body_slots"] = [
        {"slug": b, "band": "habitable", "kind": "engineered"} if isinstance(b, str) else b
        for b in bodies
    ]
    if spark and not bodies:
        warn(state, "engineered_mesh with --spark but no locked bodies; body_slots empty")
    state["layers"]["pinned"] = False
    state["layers"]["system_mode"] = "engineered_mesh"


def _roll_natural(
    state: dict[str, Any],
    locks: dict[str, Any],
    rng: Any,
    spark: bool,
) -> None:
    enums = _load_star_enums()
    sparks = _load_sparks()

    if spark:
        spectral = weighted_choice(
            rng,
            enums["spectral"],
            [sparks["spectral_weights"].get(s, 1) for s in enums["spectral"]],
        )
        size_band = weighted_choice(
            rng,
            enums["size_bands"],
            [sparks["size_weights"].get(s, 1) for s in enums["size_bands"]],
        )
    else:
        spectral = "G"
        size_band = "dwarf"

    state["layers"]["star"] = {
        "spectral": spectral,
        "size_band": size_band,
        "label": f"{spectral}-{size_band}",
    }

    bands = _default_orbit_bands()
    # Soft occupancy suggestions
    body_slots: list[dict] = []
    for band_name, band in bands.items():
        lo, hi = band["typical_count"]
        if spark:
            count = rng.randint(lo, hi)
        else:
            count = lo if band_name != "habitable" else max(lo, 1)
        kinds = band["typical_body_kinds"]
        for i in range(count):
            kind = pick(rng, kinds) if spark else kinds[0]
            body_slots.append(
                {
                    "slug": f"{state['meta']['slug']}-{band_name}-{i+1}",
                    "band": band_name,
                    "kind": kind,
                    "suggested": True,
                }
            )
            # Soft: unusual combo warning example
            if band_name == "ice" and kind == "greenhouse":
                warn(
                    state,
                    f"soft orbit suggestion unusual: greenhouse in ice band "
                    f"({state['meta']['slug']}-{band_name}-{i+1})",
                )

    state["layers"]["orbit_bands"] = bands
    state["layers"]["body_slots"] = body_slots

    if spark:
        formations = list(sparks.get("formations") or [])
        n = rng.randint(0, 2)
        state["layers"]["formations"] = (
            [pick(rng, formations) for _ in range(n)] if formations else []
        )
        companion_roll = rng.random()
        if companion_roll < 0.15:
            state["layers"]["companions"] = {"type": "binary_star"}
        elif companion_roll < 0.35:
            state["layers"]["companions"] = {"type": "distant_companion"}
        else:
            state["layers"]["companions"] = {"type": "none"}
    else:
        state["layers"]["formations"] = list(locks.get("formations") or [])
        state["layers"]["companions"] = locks.get("companions") or {"type": "none"}

    state["layers"]["pinned"] = False


def _default_orbit_bands() -> dict:
    enums = _load_star_enums()
    return dict(enums.get("orbit_bands") or {})
