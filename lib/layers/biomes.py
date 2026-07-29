"""L4 Biomes — from locks or inferred from planet type / climate."""
from __future__ import annotations

from typing import Any

from ..rngutil import make_rng, pick
from ..util import ENUMS, load_yaml, warn


def _class_index() -> dict[str, dict]:
    from .. import custom_enums

    classes = custom_enums.merged_biome_classes()
    return {c["id"]: c for c in classes if c.get("id")}


def apply(world: dict[str, Any]) -> None:
    locks = world.get("locks") or {}
    spark = bool(world["meta"].get("spark"))
    rng = make_rng(world["meta"].get("seed"))
    idx = _class_index()
    stress = (world["layers"].get("chemistry_climate") or {}).get("immaterium_stress", "neutral")
    planet_type = (world["layers"].get("planet_type") or {}).get("planet_type", "")

    locked_biomes = locks.get("biomes") or []
    biomes: list[dict] = []
    body_slug = str((world.get("meta") or {}).get("slug") or "")
    used_ids: set[str] = set()

    if locked_biomes:
        for i, b in enumerate(locked_biomes):
            if isinstance(b, str):
                entry = _from_class(b, idx, i, body_slug=body_slug, used=used_ids)
            else:
                entry = _from_dict(b, idx, i, body_slug=body_slug, used=used_ids)
            biomes.append(entry)
    else:
        for class_id in _infer_classes(planet_type, stress, spark, rng):
            biomes.append(
                _from_class(
                    class_id, idx, len(biomes), body_slug=body_slug, used=used_ids
                )
            )

    # Stress gating: terminus forbids lush garden overlays
    if stress == "terminus":
        for b in biomes:
            if b["class"] in ("archival_garden", "jungle", "temperate_forest") and b["richness"] == "rich":
                warn(
                    world,
                    f"immaterium terminus: downgrading biome {b['id']} richness rich→sparse",
                )
                b["richness"] = "sparse"

    world["layers"]["biomes"] = biomes


def body_biome_prefix(body_slug: str) -> str:
    """Short body token for biome instance ids (aethelgard-prime → aethelgard)."""
    raw = str(body_slug or "").strip().replace("-", "_")
    if not raw:
        return ""
    parts = [p for p in raw.split("_") if p]
    drop = {
        "prime",
        "secundus",
        "tertius",
        "quartus",
        "i",
        "ii",
        "iii",
        "iv",
        "v",
        "vi",
        "vii",
        "viii",
        "ix",
        "x",
    }
    while len(parts) > 1 and parts[-1].lower() in drop:
        parts.pop()
    return "_".join(parts)


def unique_biome_instance_id(
    class_id: str,
    *,
    body_slug: str = "",
    used: set[str] | None = None,
    preferred: str | None = None,
) -> str:
    """Stable local biome slug — never `{class}_{list_index}` from total count.

    Prefer preferred id, else `{body}_{class}`, else class id; suffix _2+_ on clash.
    """
    taken = set(used or ())
    prefix = body_biome_prefix(body_slug)
    candidates: list[str] = []
    if preferred:
        candidates.append(str(preferred).strip())
    if prefix:
        candidates.append(f"{prefix}_{class_id}")
    candidates.append(class_id)
    for base in candidates:
        if not base:
            continue
        if base not in taken:
            return base
        n = 2
        while f"{base}_{n}" in taken:
            n += 1
        return f"{base}_{n}"
    return class_id or "biome"


def _from_class(
    class_id: str,
    idx: dict,
    i: int,
    *,
    body_slug: str = "",
    used: set[str] | None = None,
) -> dict:
    meta = idx.get(class_id) or {
        "id": class_id,
        "medium": "terrestrial",
        "overlay": False,
        "default_richness": "moderate",
    }
    bid = unique_biome_instance_id(class_id, body_slug=body_slug, used=used)
    if used is not None:
        used.add(bid)
    return {
        "id": bid,
        "class": class_id,
        "richness": meta.get("default_richness", "moderate"),
        "medium": meta.get("medium", "terrestrial"),
        "overlay": bool(meta.get("overlay")),
    }


def _from_dict(
    b: dict,
    idx: dict,
    i: int,
    *,
    body_slug: str = "",
    used: set[str] | None = None,
) -> dict:
    class_id = b.get("class") or b.get("id") or "barren_null"
    preferred = str(b["id"]) if b.get("id") else None
    base = _from_class(class_id, idx, i, body_slug=body_slug, used=None)
    base["id"] = unique_biome_instance_id(
        class_id,
        body_slug=body_slug,
        used=used,
        preferred=preferred,
    )
    if used is not None:
        used.add(base["id"])
    if b.get("richness"):
        base["richness"] = b["richness"]
    if b.get("medium"):
        base["medium"] = b["medium"]
    if "overlay" in b:
        base["overlay"] = bool(b["overlay"])
    if b.get("filing_id"):
        base["filing_id"] = b["filing_id"]
    return base


def _infer_classes(
    planet_type: str,
    stress: str,
    spark: bool,
    rng: Any,
) -> list[str]:
    mapping = {
        "forge_world": ["slag_industrial", "hive_stack", "barren_null"],
        "hive_world": ["hive_stack", "archival_garden"],
        "agri_world": ["monoculture_plain", "grassland"],
        "death_world": ["jungle", "swamp_wetland", "shoreline_intertidal"],
        "feral_world": ["temperate_forest", "grassland"],
        "ocean_world": ["oceanic_pelagic", "shoreline_intertidal", "oceanic_abyssal"],
        "ice_world": ["ice_cryogenic", "tundra"],
        "desert_world": ["desert"],
        "jungle_world": ["jungle"],
        "penal_world": ["penal_infrastructure", "barren_null"],
        "dead_world": ["barren_null", "dock_hull"],
        "mining_world": ["cave_subterranean", "slag_industrial"],
        "garden_world": ["temperate_forest", "grassland", "freshwater_river"],
        "industrial_world": ["slag_industrial", "hive_stack"],
    }
    classes = list(mapping.get(planet_type, ["grassland", "temperate_forest"]))
    if stress in ("extremis", "terminus") and "swamp_wetland" not in classes:
        classes.append("swamp_wetland")
    if spark and len(classes) > 1:
        # maybe drop one
        if rng.random() < 0.3:
            classes = classes[:-1]
    return classes
