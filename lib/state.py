"""SystemState and WorldState constructors / I/O."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .util import RESULTS, dump_json, load_json


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def new_system_state(
    slug: str,
    *,
    seed: int | None = None,
    spark: bool = False,
) -> dict[str, Any]:
    return {
        "meta": {
            "slug": slug,
            "seed": seed,
            "spark": spark,
            "generated_at": utc_now(),
        },
        "locks": {},
        "layers": {
            "star": {},
            "orbit_bands": {},
            "companions": {},
            "formations": [],
            "body_slots": [],
        },
        "warnings": [],
    }


def new_world_state(
    slug: str,
    *,
    system_slug: str | None = None,
    seed: int | None = None,
    spark: bool = False,
) -> dict[str, Any]:
    return {
        "meta": {
            "slug": slug,
            "system_slug": system_slug,
            "seed": seed,
            "spark": spark,
            "generated_at": utc_now(),
        },
        "locks": {
            "sources": [],
            "topology": "",
            "planet_type": None,
            "body_kind": "planet",
            "biomes": [],
            "specimens": [],
            "risks": [],
            "notes": "",
            "stellar": "generate",
            "local_notes": "",
        },
        "layers": {
            "planet_type": {},
            "geology": {},
            "chemistry_climate": {},
            "biomes": [],
            "trophic": {"by_biome": {}},
            "bauplan": {"by_slot": {}},
        },
        "warnings": [],
        "render": {"magos_path": None, "literary_path": None},
    }


def system_out_dir(slug: str) -> Path:
    """Sealed system pack under cogitator-results/systems/<slug>/."""
    return RESULTS / "systems" / slug


def body_out_dir(slug: str) -> Path:
    """Sealed body pack under cogitator-results/<slug>/."""
    return RESULTS / slug


def save_system(state: dict[str, Any]) -> Path:
    slug = state["meta"]["slug"]
    path = system_out_dir(slug) / "system.json"
    dump_json(path, state)
    return path


def load_system(slug: str) -> dict[str, Any]:
    path = system_out_dir(slug) / "system.json"
    if not path.is_file():
        raise FileNotFoundError(f"No system pack at {path}")
    return load_json(path)


def save_world(state: dict[str, Any]) -> Path:
    slug = state["meta"]["slug"]
    path = body_out_dir(slug) / "state.json"
    dump_json(path, state)
    return path


def load_world(slug: str) -> dict[str, Any]:
    path = body_out_dir(slug) / "state.json"
    if not path.is_file():
        raise FileNotFoundError(f"No body pack at {path}")
    return load_json(path)
