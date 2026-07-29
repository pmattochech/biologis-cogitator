"""L6 Bauplan — constrained by parent biome medium."""
from __future__ import annotations

from typing import Any

from ..rngutil import make_rng, pick
from ..util import MATRICES, load_yaml, warn


def apply(world: dict[str, Any]) -> None:
    traits = load_yaml(MATRICES / "bauplan_traits.yaml")
    media = traits.get("media") or {}
    size_bias = traits.get("slot_size_bias") or {}
    spark = bool(world["meta"].get("spark"))
    rng = make_rng(world["meta"].get("seed"))

    biome_by_id = {b["id"]: b for b in world["layers"].get("biomes") or []}
    by_slot: dict[str, dict] = {}

    for biome_id, slots in (world["layers"].get("trophic") or {}).get("by_biome", {}).items():
        biome = biome_by_id.get(biome_id) or {}
        medium = biome.get("medium") or "terrestrial"
        medium_traits = media.get(medium) or media.get("terrestrial") or {}

        for slot in slots:
            slot_id = slot["slot_id"]
            if slot.get("locked") and slot.get("dossier"):
                # Link only — do not rewrite locked dossiers
                by_slot[slot_id] = {
                    "slot_id": slot_id,
                    "origin": slot["origin"],
                    "origin_subtype": slot["origin_subtype"],
                    "medium": medium,
                    "locked": True,
                    "dossier": slot.get("dossier"),
                    "name": slot.get("name"),
                    "note": "bauplan deferred to locked dossier — not rewritten",
                }
                continue

            locomotion_opts = medium_traits.get("locomotion") or ["cursorial"]
            if isinstance(locomotion_opts, str):
                locomotion_opts = [locomotion_opts]
            locomotion = pick(rng, locomotion_opts) if spark else locomotion_opts[0]

            respiration = medium_traits.get("respiration")
            if isinstance(respiration, list):
                respiration = pick(rng, respiration) if spark else respiration[0]

            size = size_bias.get(slot["slot"], "medium")
            ceiling = medium_traits.get("size_ceiling", "large")

            # Enforce medium match
            if slot.get("medium") and slot["medium"] != medium:
                warn(
                    world,
                    f"bauplan medium mismatch on {slot_id}: "
                    f"slot {slot['medium']} vs biome {medium}; keeping biome medium",
                )

            by_slot[slot_id] = {
                "slot_id": slot_id,
                "name": slot.get("name"),
                "analogue": slot.get("analogue"),
                "origin": slot["origin"],
                "origin_subtype": slot["origin_subtype"],
                "medium": medium,
                "locomotion": locomotion,
                "respiration": respiration,
                "size_class": size,
                "size_ceiling": ceiling,
                "trophic_slot": slot["slot"],
                "primary_biome": biome_id,
                "locked": False,
            }

    world["layers"]["bauplan"] = {"by_slot": by_slot}
