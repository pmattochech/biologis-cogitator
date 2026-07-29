"""L5 Per-biome trophic niches — biome-born food webs."""
from __future__ import annotations

from typing import Any

from ..rngutil import make_rng, pick
from ..util import ENUMS, MATRICES, load_yaml, warn


def apply(world: dict[str, Any]) -> None:
    ladder = load_yaml(ENUMS / "trophic_slots.yaml")
    analogues = load_yaml(MATRICES / "niche_analogues.yaml")
    origins = load_yaml(ENUMS / "origin_subtypes.yaml")
    spark = bool(world["meta"].get("spark"))
    rng = make_rng(world["meta"].get("seed"))
    locks = world.get("locks") or {}
    specimens = list(locks.get("specimens") or [])

    by_biome: dict[str, list] = {}
    used_specimen_ids: set[str] = set()
    biomes = list(world["layers"].get("biomes") or [])
    biome_by_id = {b["id"]: b for b in biomes}

    for biome in biomes:
        slots_needed = list(
            (ladder.get("ladder_by_richness") or {}).get(biome.get("richness"), [])
        )
        if biome.get("richness") == "null":
            slots_needed = []

        biome_slots: list[dict] = []
        catalog = analogues.get(biome["class"]) or {}

        # Place locked specimens whose primary_biome matches this biome id or class
        for spec in specimens:
            primary = spec.get("primary_biome")
            if primary not in (biome["id"], biome["class"]):
                continue
            sid = spec.get("id") or spec.get("name")
            if sid in used_specimen_ids:
                continue
            slot_name = spec.get("trophic_slot") or "apex"
            if slot_name not in slots_needed and slots_needed:
                warn(
                    world,
                    f"specimen {sid} slot {slot_name} not in richness ladder "
                    f"for {biome['id']}; placing anyway (lock wins)",
                )
            entry = _slot_from_specimen(spec, biome, slot_name, link=False)
            biome_slots.append(entry)
            used_specimen_ids.add(sid)
            if slot_name in slots_needed:
                slots_needed = [s for s in slots_needed if s != slot_name]

        for slot_name in slots_needed:
            if any(s["slot"] == slot_name and s.get("locked") for s in biome_slots):
                continue
            options = list(catalog.get(slot_name) or [])
            if not options:
                continue
            analogue = pick(rng, options) if spark else options[0]
            origin, subtype = _default_origin(biome, slot_name, origins)
            biome_slots.append(
                {
                    "slot_id": f"{biome['id']}__{slot_name}",
                    "slot": slot_name,
                    "analogue": analogue,
                    "origin": origin,
                    "origin_subtype": subtype,
                    "range": "single",
                    "primary_biome": biome["id"],
                    "medium": biome["medium"],
                    "locked": False,
                    "name": None,
                    "link": False,
                }
            )

        by_biome[biome["id"]] = biome_slots

    # Secondary biome links (range: multi) — same specimen, not a second birth
    for spec in specimens:
        sid = spec.get("id") or spec.get("name")
        if sid not in used_specimen_ids:
            continue
        secondaries = list(spec.get("secondary_biomes") or [])
        if not secondaries and spec.get("range") != "multi":
            continue
        slot_name = spec.get("trophic_slot") or "apex"
        primary = spec.get("primary_biome")
        for sec_id in secondaries:
            biome = biome_by_id.get(sec_id)
            if biome is None:
                # allow class match
                biome = next((b for b in biomes if b["class"] == sec_id), None)
            if biome is None:
                warn(
                    world,
                    f"specimen {sid} secondary_biome {sec_id!r} matched no biome; link skipped",
                )
                continue
            slots = by_biome.setdefault(biome["id"], [])
            already = any(
                s.get("name") == (spec.get("name") or sid)
                or (s.get("dossier") and s.get("dossier") == spec.get("dossier"))
                or (
                    s.get("locked")
                    and s.get("slot") == slot_name
                    and s.get("primary_biome") == primary
                    and s.get("link")
                )
                for s in slots
            )
            # Also skip if full primary entry somehow here
            if any(
                s.get("locked")
                and not s.get("link")
                and (s.get("name") == (spec.get("name") or sid) or s.get("dossier") == spec.get("dossier"))
                for s in slots
            ):
                continue
            if already:
                continue
            link = _slot_from_specimen(spec, biome, slot_name, link=True)
            # Preserve true primary on link entries
            link["primary_biome"] = primary
            link["appearing_in"] = biome["id"]
            slots.append(link)
            # Remove generated filler occupying same slot if unlocked
            by_biome[biome["id"]] = [
                s
                for s in slots
                if not (s.get("slot") == slot_name and not s.get("locked") and s is not link)
            ] + ([link] if link not in by_biome[biome["id"]] else [])
            # rebuild cleanly
            cleaned = [
                s
                for s in by_biome[biome["id"]]
                if not (s.get("slot") == slot_name and not s.get("locked"))
            ]
            if link not in cleaned:
                cleaned.append(link)
            by_biome[biome["id"]] = cleaned

    for spec in specimens:
        sid = spec.get("id") or spec.get("name")
        if sid not in used_specimen_ids:
            warn(
                world,
                f"specimen {sid} primary_biome "
                f"{spec.get('primary_biome')!r} matched no generated biome; not placed",
            )

    world["layers"]["trophic"] = {"by_biome": by_biome}


def _default_origin(biome: dict, slot_name: str, origins: dict) -> tuple[str, str]:
    if biome.get("overlay"):
        origin = "exotic"
        if slot_name == "producer" and biome["class"] in ("monoculture_plain", "hydroponic"):
            subtype = "imperial_tithe" if biome["class"] == "monoculture_plain" else "deliberate_transplant"
        elif biome["class"] in ("dock_hull", "slag_industrial"):
            subtype = "voidborne"
        elif biome["class"] == "hive_stack":
            subtype = "feral_exotic"
        else:
            subtype = "deliberate_transplant"
        return origin, subtype
    return "native", "aboriginal"


def _slot_from_specimen(
    spec: dict,
    biome: dict,
    slot_name: str,
    *,
    link: bool = False,
) -> dict:
    primary = spec.get("primary_biome") or biome["id"]
    suffix = "link" if link else "primary"
    return {
        "slot_id": f"{biome['id']}__{slot_name}__{spec.get('id') or spec.get('name')}__{suffix}",
        "slot": slot_name,
        "analogue": spec.get("analogue") or spec.get("niche_analogue") or "locked_specimen",
        "origin": spec.get("origin", "native"),
        "origin_subtype": spec.get("origin_subtype", "aboriginal"),
        "range": spec.get("range", "single"),
        "primary_biome": primary,
        "secondary_biomes": list(spec.get("secondary_biomes") or []),
        "medium": biome["medium"],
        "locked": True,
        "link": link,
        "name": spec.get("name") or spec.get("id"),
        "dossier": spec.get("dossier"),
        "notes": spec.get("notes") or "",
    }
