"""Browse and read sealed packs under cogitator-results/ (bodies + systems)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from .util import RESULTS

Kind = Literal["body", "system"]

BODY_ARTIFACTS = ("magos.md", "literary.md", "state.json")
SYSTEM_ARTIFACTS = ("system.json", "system.md")


def list_out_bodies() -> list[str]:
    """Body slugs with at least one known artifact under cogitator-results/<slug>/."""
    if not RESULTS.is_dir():
        return []
    slugs: list[str] = []
    for p in RESULTS.iterdir():
        if not p.is_dir() or p.name == "systems":
            continue
        if any((p / name).is_file() for name in BODY_ARTIFACTS):
            slugs.append(p.name)
    return sorted(slugs)


def list_out_systems() -> list[str]:
    """System slugs under cogitator-results/systems/."""
    root = RESULTS / "systems"
    if not root.is_dir():
        return []
    slugs: list[str] = []
    for p in root.iterdir():
        if not p.is_dir():
            continue
        if any((p / name).is_file() for name in SYSTEM_ARTIFACTS):
            slugs.append(p.name)
    return sorted(slugs)


def out_dir(kind: Kind, slug: str) -> Path:
    if kind == "body":
        return RESULTS / slug
    return RESULTS / "systems" / slug


def list_species_artifacts(slug: str) -> list[str]:
    """Relative paths under body: species/<id>/<file>."""
    root = out_dir("body", slug) / "species"
    if not root.is_dir():
        return []
    found: list[str] = []
    for sid_dir in sorted(root.iterdir()):
        if not sid_dir.is_dir():
            continue
        for name in (
            "profile.yaml",
            "questionnaire.yaml",  # legacy
            "midjourney.md",
            "filing-reminders.md",
        ):
            if (sid_dir / name).is_file():
                found.append(f"species/{sid_dir.name}/{name}")
    return found


def list_artifacts(kind: Kind, slug: str) -> list[str]:
    """Filenames present for this slug (known set + species profiles for bodies)."""
    names = BODY_ARTIFACTS if kind == "body" else SYSTEM_ARTIFACTS
    d = out_dir(kind, slug)
    found = [n for n in names if (d / n).is_file()]
    if kind == "body":
        found.extend(list_species_artifacts(slug))
    return found


def artifact_path(kind: Kind, slug: str, filename: str) -> Path:
    if kind == "body" and filename.startswith("species/"):
        path = out_dir(kind, slug) / filename
        # stay under body dir
        if not str(path.resolve()).startswith(str(out_dir(kind, slug).resolve())):
            raise ValueError(f"path escape: {filename}")
        return path
    allowed = BODY_ARTIFACTS if kind == "body" else SYSTEM_ARTIFACTS
    if filename not in allowed:
        raise ValueError(f"unknown artifact '{filename}' for {kind}")
    return out_dir(kind, slug) / filename


def read_out_artifact(kind: Kind, slug: str, filename: str) -> str:
    """
    Return text for display. JSON is pretty-printed.
    Raises FileNotFoundError if missing.
    """
    path = artifact_path(kind, slug, filename)
    if not path.is_file():
        raise FileNotFoundError(f"no {kind} artifact {slug}/{filename}")
    raw = path.read_text(encoding="utf-8")
    if filename.endswith(".json"):
        try:
            data = json.loads(raw)
            return json.dumps(data, indent=2, ensure_ascii=False) + "\n"
        except json.JSONDecodeError:
            return raw
    return raw
