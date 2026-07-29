"""L7 Dual render: Magos dossier + literary ecology brief."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from . import species_profile as speciesmod
from .state import body_out_dir


def render_all(
    world: dict[str, Any],
    *,
    species_profiles: dict[str, dict[str, Any]] | None = None,
) -> None:
    slug = world["meta"]["slug"]
    out = body_out_dir(slug)
    out.mkdir(parents=True, exist_ok=True)
    profiles = species_profiles
    if profiles is None:
        profiles = speciesmod.load_all_profiles(slug)
    elif profiles:
        speciesmod.write_profiles_for_body(slug, profiles)
    magos = out / "magos.md"
    literary = out / "literary.md"
    magos.write_text(_magos(world, profiles), encoding="utf-8")
    literary.write_text(_literary(world, profiles), encoding="utf-8")
    world["render"] = {
        "magos_path": str(Path("cogitator-results") / slug / "magos.md"),
        "literary_path": str(Path("cogitator-results") / slug / "literary.md"),
        "species_dir": str(Path("cogitator-results") / slug / "species"),
    }


def _prose_override(world: dict[str, Any], kind: str) -> str | None:
    prose = (world.get("locks") or {}).get("prose") or {}
    text = prose.get(kind)
    if text is None:
        return None
    text = str(text).strip()
    return text if text else None


def _magos(
    world: dict[str, Any],
    profiles: dict[str, dict[str, Any]] | None = None,
) -> str:
    override = _prose_override(world, "magos")
    if override is not None:
        return override if override.endswith("\n") else override + "\n"
    meta = world["meta"]
    locks = world.get("locks") or {}
    layers = world.get("layers") or {}
    pt = layers.get("planet_type") or {}
    geo = layers.get("geology") or {}
    chem = layers.get("chemistry_climate") or {}
    if profiles is None:
        profiles = speciesmod.load_all_profiles(str(meta.get("slug") or ""))
    lines = [
        f"# Magos Biologis Dossier — {meta['slug']}",
        "",
        f"**System:** {meta.get('system_slug') or '—'}",
        f"**Seed:** {meta.get('seed')}",
        f"**Spark:** {meta.get('spark')}",
        f"**Generated:** {meta.get('generated_at')}",
        "",
        "## Classification",
        "",
        f"- **Body kind:** `{pt.get('body_kind')}`",
        f"- **Planet type (Administratum):** `{pt.get('planet_type')}`",
        f"- **Local notes:** {pt.get('local_notes') or locks.get('local_notes') or '—'}",
        "",
        "## Geology",
        "",
        f"- Gravity: {geo.get('gravity_g')} g",
        f"- Crust: {geo.get('crust')}",
        f"- Volcanism: {geo.get('volcanism')}",
        f"- Connectivity: {geo.get('connectivity')}",
        f"- Tidal lock: {geo.get('tidal_lock')}",
        f"- Hydrosphere: {geo.get('hydrosphere_pct')}%",
        f"- Insolation hint: {geo.get('insolation_hint')}",
        f"- Topology: {geo.get('topology') or '—'}",
        "",
        "## Chemistry & climate",
        "",
        f"- Atmosphere: {chem.get('atmosphere')}",
        f"- Water: {chem.get('water')}",
        f"- Solvent: {chem.get('solvent')}",
        f"- Cryosphere: {chem.get('cryosphere')}",
        f"- Climate belts: {', '.join(chem.get('climate_belts') or [])}",
        f"- **Immaterium stress:** `{chem.get('immaterium_stress')}`",
        f"- Stress reading: {chem.get('immaterium_description')}",
        f"- Flavor tags: {', '.join(chem.get('immaterium_flavor_tags') or []) or '—'}",
        "",
        "## Biomes",
        "",
    ]
    for b in layers.get("biomes") or []:
        lines.append(
            f"- `{b['id']}` — class `{b['class']}`, richness `{b['richness']}`, "
            f"medium `{b['medium']}`, overlay={b.get('overlay')}"
        )
    lines += ["", "## Trophic webs (per biome)", ""]
    trophic = (layers.get("trophic") or {}).get("by_biome") or {}
    bauplan = (layers.get("bauplan") or {}).get("by_slot") or {}
    for biome_id, slots in trophic.items():
        lines.append(f"### {biome_id}")
        lines.append("")
        if not slots:
            lines.append("- (empty web)")
            lines.append("")
            continue
        for s in slots:
            bp = bauplan.get(s["slot_id"]) or {}
            name = s.get("name") or s.get("analogue") or s["slot"]
            link_note = " [range link]" if s.get("link") else ""
            lines.append(
                f"- **{s['slot']}** — {name}{link_note} | Origin: `{s['origin']}` / "
                f"`{s['origin_subtype']}` | analogue: `{s.get('analogue')}`"
            )
            if bp.get("dossier"):
                lines.append(f"  - Locked dossier: `{bp['dossier']}` (bauplan not rewritten)")
            elif not bp.get("locked"):
                lines.append(
                    f"  - Bauplan: locomotion `{bp.get('locomotion')}`, "
                    f"respiration `{bp.get('respiration')}`, "
                    f"size `{bp.get('size_class')}` (ceiling `{bp.get('size_ceiling')}`)"
                )
        lines.append("")

    lines += speciesmod.magos_species_section(profiles or {})

    risks = locks.get("risks") or []
    lines += ["## Biological risks (locked)", ""]
    if risks:
        for r in risks:
            lines.append(f"- {r}")
    else:
        lines.append("- (none locked)")

    warnings = world.get("warnings") or []
    lines += ["", "## Warnings / contradictions", ""]
    if warnings:
        for w in warnings:
            lines.append(f"- {w}")
    else:
        lines.append("- (none)")
    lines.append("")
    return "\n".join(lines)


def _literary(
    world: dict[str, Any],
    profiles: dict[str, dict[str, Any]] | None = None,
) -> str:
    override = _prose_override(world, "literary")
    if override is not None:
        return override if override.endswith("\n") else override + "\n"
    meta = world["meta"]
    layers = world.get("layers") or {}
    locks = world.get("locks") or {}
    chem = layers.get("chemistry_climate") or {}
    geo = layers.get("geology") or {}
    pt = layers.get("planet_type") or {}
    if profiles is None:
        profiles = speciesmod.load_all_profiles(str(meta.get("slug") or ""))
    stress = chem.get("immaterium_stress", "neutral")

    stress_line = {
        "neutral": "The veil lies quiet here; weather answers only to star and stone.",
        "minoris": "Sometimes the wind carries an omen that instruments refuse to name.",
        "majoris": "Seasons fray at the edges; living things learn shapes the Magos call wrong.",
        "extremis": "Storm-shadow is weather. The ecology has learned to breathe beside the Wound.",
        "terminus": "Nothing soft survives long. What endures does so under a sky that hates maps.",
    }.get(stress, "")

    lines = [
        f"# Ecology Brief — {meta['slug']}",
        "",
        locks.get("topology")
        or geo.get("topology")
        or f"A {pt.get('planet_type', 'world').replace('_', ' ')} under Administratum filing.",
        "",
        stress_line,
        "",
    ]

    trophic = (layers.get("trophic") or {}).get("by_biome") or {}
    for biome in layers.get("biomes") or []:
        lines.append(f"## {biome['class'].replace('_', ' ').title()}")
        lines.append("")
        slots = trophic.get(biome["id"]) or []
        if not slots:
            lines.append("Life here is rumor, residue, or absent.")
            lines.append("")
            continue
        # Prefer named / apex / producer sentences
        for s in slots:
            name = s.get("name") or s.get("analogue", "an unnamed form")
            origin = s["origin"]
            subtype = s["origin_subtype"]
            link = " (range presence)" if s.get("link") else ""
            if origin == "native" and subtype == "neo_endemic":
                provenance = (
                    "native now — neo-endemic, born of colonizer stock that learned this world"
                )
            elif origin == "native":
                provenance = f"native ({subtype.replace('_', ' ')})"
            else:
                provenance = f"exotic ({subtype.replace('_', ' ')})"
            lines.append(
                f"In the {biome['class'].replace('_', ' ')}, the {s['slot'].replace('_', ' ')} "
                f"niche is held by {name}{link} — {provenance}."
            )
        lines.append("")

    lines += speciesmod.literary_species_paragraphs(profiles or {})

    if locks.get("notes") or locks.get("local_notes"):
        lines.append("## Filed note")
        lines.append("")
        lines.append(locks.get("notes") or locks.get("local_notes"))
        lines.append("")

    return "\n".join(lines)
