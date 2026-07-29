"""Propose external lore / filing paths (dry-run only — never writes)."""
from __future__ import annotations

from typing import Any


EXPORT_BESTIARY = "external/lore/bestiary"


def propose(world: dict[str, Any]) -> list[str]:
    slug = world["meta"]["slug"]
    system = world["meta"].get("system_slug") or "unknown-system"
    paths = [
        f"{EXPORT_BESTIARY}/generated/{slug}.md  (new Magos+literary merge candidate)",
        f"{EXPORT_BESTIARY}/fauna-flora-named-specimens.md  (append rows for new named slots)",
    ]
    # Guess matrix by system name conventions
    sys_l = system.lower()
    if "bastion" in sys_l or "noviomagus" in sys_l or "central" in sys_l:
        paths.append(
            f"{EXPORT_BESTIARY}/biogeographic-matrix-central-bastion.md  "
            f"(update/expand ### section for {slug})"
        )
    elif "crucible" in sys_l or "aethelgard" in sys_l or "incus" in sys_l:
        paths.append(
            f"{EXPORT_BESTIARY}/biogeographic-matrix-crucible.md  "
            f"(update/expand ### section for {slug})"
        )
    elif "threshold" in sys_l or "vigil" in sys_l or "tempest" in sys_l:
        paths.append(
            f"{EXPORT_BESTIARY}/biogeographic-matrix-threshold.md  "
            f"(update/expand ### section for {slug})"
        )
    else:
        paths.append(
            f"{EXPORT_BESTIARY}/biogeographic-matrix-<system>.md  "
            f"(choose matrix for system {system})"
        )

    for slots in (world.get("layers", {}).get("trophic") or {}).get("by_biome", {}).values():
        for s in slots:
            if s.get("locked") and s.get("dossier"):
                paths.append(f"{s['dossier']}  (already locked — do not overwrite)")

    # de-dupe preserve order
    seen: set[str] = set()
    out: list[str] = []
    for p in paths:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def format_report(world: dict[str, Any]) -> str:
    lines = [
        f"Export propose (dry-run) for body `{world['meta']['slug']}`",
        "No files will be written under external/lore/.",
        "",
        "Suggested targets:",
    ]
    for p in propose(world):
        lines.append(f"  - {p}")
    lines.append("")
    return "\n".join(lines)
