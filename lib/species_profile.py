"""Named species profiles under cogitator-results/<body>/species/<id>/."""
from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from . import profile_schema as qschema
from . import entry_id as entryid
from .state import body_out_dir
from .util import dump_yaml, load_yaml

PROFILE_FILE = "profile.yaml"
LEGACY_PROFILE_FILE = "questionnaire.yaml"
MIDJOURNEY_FILE = "midjourney.md"
REMINDERS_FILE = "filing-reminders.md"

MIN_ORIGIN = frozenset({"native", "exotic"})


def species_root(body_slug: str) -> Path:
    return body_out_dir(body_slug) / "species"


def species_dir(body_slug: str, species_id: str) -> Path:
    return species_root(body_slug) / species_id


def empty_profile(
    species_id: str = "",
    *,
    working_common_name: str = "",
    world_biome: str = "",
    trophic_slot: str = "apex",
) -> dict[str, Any]:
    return qschema.empty_profile_from_schema(
        species_id=species_id,
        working_common_name=working_common_name,
        world_biome=world_biome,
        trophic_slot=trophic_slot,
    )


def display_name(profile: dict[str, Any]) -> str:
    answers = profile.get("answers") or {}
    a = answers.get("A") or {}
    f = answers.get("F") or {}
    # Vernacular / working first, then formal Magos registry (A, then legacy F)
    w = str(profile.get("working_common_name") or "").strip()
    if w:
        return w
    for src in (a, f):
        for key in ("vernacular", "common_name", "formal_name", "high_gothic"):
            val = str(src.get(key) or "").strip()
            if val:
                return val
    return str(profile.get("id") or "unnamed")


def validate_minimum(profile: dict[str, Any]) -> list[str]:
    errors = list(qschema.validate_minimum(profile))
    sid = entryid.normalize_entry_id(str(profile.get("id") or ""))
    for err in entryid.validate_entry_id(sid):
        if err not in errors:
            errors.append(err)
    return errors


def suggest_id_for_session(
    body_slug: str | None,
    world_biome: str | None,
    *,
    reserved_ids: list[str] | None = None,
) -> str:
    return entryid.suggest_entry_id(
        body_slug, world_biome, reserved_ids=reserved_ids
    )


def suggest_variant_id_for_session(
    body_slug: str | None,
    parent_entry_id: str,
    *,
    reserved_ids: list[str] | None = None,
) -> str:
    if not body_slug:
        return ""
    try:
        return entryid.allocate_variant_id(
            body_slug, parent_entry_id, reserved_ids=reserved_ids
        )
    except ValueError:
        return ""


def clone_profile_as_variant(
    profile: dict[str, Any],
    new_entry_id: str,
) -> dict[str, Any]:
    """Deep copy for subspecies filing — same answers, new Entry ID only."""
    out = copy.deepcopy(profile)
    sid = entryid.normalize_entry_id(new_entry_id)
    out["id"] = sid
    out["magos_scaffold_id"] = sid
    return out


def migrate_profile_stores(profile: dict[str, Any]) -> dict[str, Any]:
    """Move legacy limb/morphology into B; naming into v5 (formal + vernacular working)."""
    out = dict(profile)
    answers = dict(out.get("answers") or {})
    a = dict(answers.get("A") or {})
    b = dict(answers.get("B") or {})
    c = dict(answers.get("C") or {})
    f = dict(answers.get("F") or {})

    def _pull(dst_key: str, *sources: tuple[dict[str, Any], str]) -> None:
        if str(b.get(dst_key) or "").strip():
            return
        for src, key in sources:
            val = src.get(key)
            if val is not None and str(val).strip() != "":
                b[dst_key] = val
                return

    _pull("eyes", (a, "eyes"), (c, "eyes"))
    _pull(
        "jaw_disposition",
        (b, "jaw_disposition"),
        (b, "jaw_bones"),
        (a, "jaw_bones"),
        (c, "jaw_bones"),
    )
    _pull("skull_seams", (b, "skull_seams"), (a, "skull_seams"))
    _pull("limb_disposition", (a, "limbs_fins"), (b, "limbs_fins"), (c, "limbs_fins"))
    _pull(
        "ancestral_limb_count",
        (c, "ancestral_limb_count"),
        (a, "ancestral_limb_count"),
    )
    _pull(
        "limb_mode",
        (c, "fin_limb_mode"),
        (b, "fin_limb_mode"),
        (a, "fin_limb_mode"),
    )
    _pull(
        "limb_mode_other",
        (c, "fin_limb_other"),
        (b, "fin_limb_other"),
        (a, "fin_limb_other"),
    )
    mode = str(b.get("limb_mode") or "").strip().upper()
    other = str(b.get("limb_mode_other") or "").strip()
    if mode == "D" and other and "flipper" not in other.lower() and "whale" not in other.lower():
        b["limb_mode"] = "K"
        if not str(b.get("limb_mode_other") or "").strip():
            b["limb_mode_other"] = other

    for dead in ("eyes", "limbs_fins", "jaw_bones", "ancestral_limb_count",
                 "fin_limb_mode", "fin_limb_other"):
        a.pop(dead, None)
    for dead in (
        "ancestral_limb_count",
        "fin_limb_mode",
        "fin_limb_other",
        "eyes",
        "limbs_fins",
        "jaw_bones",
        "phylum",
        "genetic_class",
    ):
        if dead != "origin":
            c.pop(dead, None)

    if not str(a.get("formal_name") or "").strip():
        for src in (f, a):
            for key in ("formal_name", "high_gothic"):
                hg = str(src.get(key) or "").strip()
                if hg:
                    a["formal_name"] = hg
                    break
            if str(a.get("formal_name") or "").strip():
                break
    if not str(a.get("confusions") or "").strip():
        conf = str(f.get("confusions") or "").strip()
        if conf:
            a["confusions"] = conf
    if not str(out.get("working_common_name") or "").strip():
        vern = str(f.get("vernacular") or f.get("common_name") or "").strip()
        if vern:
            out["working_common_name"] = vern

    answers["A"] = a
    answers["B"] = b
    answers["C"] = c
    answers["F"] = f
    out["answers"] = answers
    return out


def _origin_from_profile(profile: dict[str, Any]) -> str:
    answers = profile.get("answers") or {}
    a = answers.get("A") or {}
    c = answers.get("C") or {}
    origin = str(c.get("origin") or a.get("origin") or "native").strip().lower()
    return origin if origin in MIN_ORIGIN else "native"


def profile_to_specimen_lock(profile: dict[str, Any]) -> dict[str, Any]:
    answers = profile.get("answers") or {}
    origin = _origin_from_profile(profile)
    secondary = list(profile.get("secondary_biomes") or [])
    rng = str(profile.get("range") or "single").strip() or "single"
    if secondary and rng == "single":
        rng = "multi"
    spec: dict[str, Any] = {
        "id": str(profile.get("id") or "").strip(),
        "name": display_name(profile),
        "primary_biome": str(profile.get("world_biome") or "").strip(),
        "secondary_biomes": secondary,
        "range": rng,
        "trophic_slot": str(profile.get("trophic_slot") or "apex").strip() or "apex",
        "origin": origin,
        "origin_subtype": str(profile.get("origin_subtype") or "aboriginal").strip()
        or "aboriginal",
        "notes": str(profile.get("notes") or "").strip(),
    }
    analogue = str(profile.get("analogue") or "").strip()
    if analogue:
        spec["analogue"] = analogue
    dossier = str(profile.get("dossier") or "").strip()
    g_path = str((answers.get("G") or {}).get("dossier_path") or "").strip()
    if dossier:
        spec["dossier"] = dossier
    elif g_path:
        spec["dossier"] = g_path
    return {k: v for k, v in spec.items() if v is not None and v != []}


def specimen_lock_to_profile_seed(spec: dict[str, Any]) -> dict[str, Any]:
    sid = str(spec.get("id") or "").strip()
    profile = empty_profile(
        sid,
        working_common_name=str(spec.get("name") or ""),
        world_biome=str(spec.get("primary_biome") or ""),
        trophic_slot=str(spec.get("trophic_slot") or "apex"),
    )
    profile["secondary_biomes"] = list(spec.get("secondary_biomes") or [])
    profile["range"] = str(spec.get("range") or "single")
    profile["origin_subtype"] = str(spec.get("origin_subtype") or "aboriginal")
    profile["analogue"] = str(spec.get("analogue") or "")
    profile["dossier"] = str(spec.get("dossier") or "")
    profile["notes"] = str(spec.get("notes") or "")
    origin = str(spec.get("origin") or "").strip().lower()
    if origin in MIN_ORIGIN:
        qschema.set_store(profile, "answers.C.origin", origin)
    name = str(spec.get("name") or "").strip()
    if name:
        # Seed as vernacular working label; formal registry filled later
        profile["working_common_name"] = name
    if profile["dossier"]:
        qschema.set_store(profile, "answers.G.dossier_path", profile["dossier"])
    return profile


def _store_text(profile: dict[str, Any], store: str) -> str:
    val = qschema.get_store(profile, store)
    if isinstance(val, bool):
        return "yes" if val else ""
    return str(val or "").strip()


def build_midjourney_prompt(profile: dict[str, Any]) -> str:
    schema = qschema.load_schema()
    roles = schema.get("roles") or {}
    name = display_name(profile)
    bits = ["Warhammer 40k xenos fauna concept art", name]
    for store in roles.get("midjourney_bits") or []:
        text = _store_text(profile, store)
        if not text:
            continue
        if store.endswith(".eyes"):
            bits.append(f"eyes:{text}")
        elif store.endswith(".origin"):
            bits.append(f"origin:{text}")
        else:
            bits.append(text)
    bits.append("grimdark, detailed creature design, full body, cinematic lighting")
    prompt = ", ".join(x for x in bits if x)
    lines = [
        f"# Midjourney — {profile.get('id') or name}",
        "",
        "## Prompt",
        "",
        prompt,
        "",
    ]
    excludes = []
    for store in roles.get("midjourney_excludes") or []:
        t = _store_text(profile, store)
        if t:
            excludes.append(t)
    if excludes:
        lines += ["## Hard excludes", "", "; ".join(excludes), ""]
    confusions = []
    for store in roles.get("naming_confusions") or []:
        t = _store_text(profile, store)
        if t:
            confusions.append(t)
    if confusions:
        lines += ["## Naming confusions to avoid", "", "; ".join(confusions), ""]
    return "\n".join(lines)


def build_filing_reminders(profile: dict[str, Any]) -> str:
    g = (profile.get("answers") or {}).get("G") or {}
    lines = [
        f"# Filing reminders — {profile.get('id')}",
        "",
        "Cogitator does **not** write `external/lore/`. Use these as a manual checklist.",
        "",
        f"- Suggested dossier path: `{g.get('dossier_path') or '(unset)'}`",
        f"- Update `fauna-flora-named-specimens.md`: {'yes' if g.get('update_named_specimens') else 'no'}",
        f"- Update bestiary `INDEX.md`: {'yes' if g.get('update_index') else 'no'}",
        f"- Cross-link geography / Magos food web: {'yes' if g.get('cross_link_geography') else 'no'}",
        "",
        f"(Schema: templates/{qschema.SCHEMA_PATH.name})",
        "",
    ]
    return "\n".join(lines)


def save_species_profile(body_slug: str, profile: dict[str, Any]) -> Path:
    profile = dict(profile)
    sid = entryid.normalize_entry_id(str(profile.get("id") or ""))
    profile["id"] = sid
    profile["magos_scaffold_id"] = sid  # legacy alias; UI label is Entry ID
    errors = validate_minimum(profile)
    if errors:
        raise ValueError("; ".join(errors))
    sch = qschema.load_schema()
    profile["schema_id"] = sch.get("id")
    profile["schema_version"] = sch.get("version")
    d = species_dir(body_slug, sid)
    d.mkdir(parents=True, exist_ok=True)
    dump_yaml(d / PROFILE_FILE, profile)
    legacy = d / LEGACY_PROFILE_FILE
    if legacy.is_file():
        legacy.unlink()
    (d / MIDJOURNEY_FILE).write_text(build_midjourney_prompt(profile), encoding="utf-8")
    (d / REMINDERS_FILE).write_text(build_filing_reminders(profile), encoding="utf-8")
    return d


def _profile_yaml_path(body_slug: str, species_id: str) -> Path | None:
    d = species_dir(body_slug, species_id)
    for name in (PROFILE_FILE, LEGACY_PROFILE_FILE):
        path = d / name
        if path.is_file():
            return path
    return None


def load_species_profile(body_slug: str, species_id: str) -> dict[str, Any] | None:
    path = _profile_yaml_path(body_slug, species_id)
    if path is None:
        return None
    data = load_yaml(path)
    if not isinstance(data, dict):
        return None
    return migrate_profile_stores(data)


def list_species_ids(body_slug: str) -> list[str]:
    root = species_root(body_slug)
    if not root.is_dir():
        return []
    ids: list[str] = []
    for p in sorted(root.iterdir()):
        if not p.is_dir():
            continue
        if (p / PROFILE_FILE).is_file() or (p / LEGACY_PROFILE_FILE).is_file():
            ids.append(p.name)
    return ids


def load_all_profiles(body_slug: str) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for sid in list_species_ids(body_slug):
        prof = load_species_profile(body_slug, sid)
        if prof:
            out[sid] = prof
    return out


def write_profiles_for_body(body_slug: str, profiles: dict[str, dict[str, Any]]) -> list[str]:
    written: list[str] = []
    for sid, prof in profiles.items():
        p = dict(prof)
        p["id"] = sid
        save_species_profile(body_slug, p)
        written.append(sid)
    return written


def magos_species_section(profiles: dict[str, dict[str, Any]]) -> list[str]:
    if not profiles:
        return []
    lines = ["## Named species profiles", ""]
    for sid in sorted(profiles):
        p = migrate_profile_stores(profiles[sid])
        answers = p.get("answers") or {}
        a, b, c, d, e, f = (
            answers.get("A") or {},
            answers.get("B") or {},
            answers.get("C") or {},
            answers.get("D") or {},
            answers.get("E") or {},
            answers.get("F") or {},
        )
        origin = c.get("origin") or a.get("origin")
        phylum = a.get("phylum")
        gclass = a.get("genetic_class")
        eyes = b.get("eyes") or a.get("eyes")
        limbs = (
            b.get("limb_disposition")
            or b.get("limbs_fins")
            or a.get("limbs_fins")
        )
        jaw = (
            b.get("jaw_disposition")
            or b.get("jaw_bones")
            or a.get("jaw_bones")
        )
        jaw_mode = b.get("jaw_mode") or ""
        jaw_other = b.get("jaw_mode_other") or ""
        skull = b.get("skull_seams") or ""
        anc = b.get("ancestral_limb_count") or c.get("ancestral_limb_count")
        mode = b.get("limb_mode") or b.get("fin_limb_mode") or c.get("fin_limb_mode")
        mode_other = (
            b.get("limb_mode_other")
            or b.get("fin_limb_other")
            or c.get("fin_limb_other")
        )

        lines.append(f"### {display_name(p)} (`{sid}`)")
        lines.append("")
        lines.append(
            f"- **Filing:** biome `{p.get('world_biome') or '—'}`, "
            f"slot `{p.get('trophic_slot') or '—'}`"
        )
        tax = ", ".join(
            x
            for x in (
                f"phylum {phylum}" if phylum else "",
                f"class {gclass}" if gclass else "",
            )
            if x
        )
        if tax:
            lines.append(f"- **Taxonomy:** {tax}")
        lines.append(f"- **Bodyshape:** {b.get('bodyshape') or '—'}")
        if b.get("size_min") or b.get("size_max"):
            lines.append(
                f"- **Size:** {b.get('size_min') or '—'} → {b.get('size_max') or '—'}"
            )
        if b.get("dimorphism"):
            lines.append(f"- **Dimorphism:** {b.get('dimorphism')}")
        if eyes:
            lines.append(f"- **Eyes:** {eyes}")
        if limbs:
            lines.append(f"- **Limb disposition:** {limbs}")
        if anc or mode:
            lines.append(
                f"- **Ancestral limbs / mode:** {anc or '—'} / "
                f"{mode or '—'} {mode_other or ''}".rstrip()
            )
        if jaw:
            lines.append(f"- **Jaw disposition:** {jaw}")
        if jaw_mode:
            lines.append(
                f"- **Jaw / bite mode:** {jaw_mode} {jaw_other}".rstrip()
            )
        if skull:
            lines.append(f"- **Skull seams / weak points:** {skull}")
        lines.append(f"- **Origin:** `{origin or '—'}`")
        if d.get("diet"):
            lines.append(f"- **Diet:** {d.get('diet')}")
        if d.get("lifespan"):
            lines.append(f"- **Lifespan:** {d.get('lifespan')}")
        if d.get("predators"):
            lines.append(f"- **Predators:** {d.get('predators')}")
        if d.get("temperament"):
            lines.append(f"- **Temperament:** {d.get('temperament')}")
        if e.get("skin_armor_color"):
            lines.append(f"- **Appearance:** {e.get('skin_armor_color')}")
        if e.get("iconic_wrong"):
            lines.append(f"- **Iconic / wrong silhouette:** {e.get('iconic_wrong')}")
        names = []
        formal = a.get("formal_name") or f.get("formal_name") or f.get("high_gothic")
        if formal:
            names.append(f"formal `{formal}`")
        vern = str(p.get("working_common_name") or f.get("vernacular") or "").strip()
        if vern:
            names.append(f"vernacular `{vern}`")
        if names:
            lines.append(f"- **Names:** {'; '.join(names)}")
        conf = a.get("confusions") or f.get("confusions")
        if conf:
            lines.append(f"- **Avoid confusing with:** {conf}")
        g = answers.get("G") or {}
        if g.get("dossier_path"):
            lines.append(
                f"- **Filing reminder (manual):** dossier path `{g.get('dossier_path')}`"
            )
        lines.append(
            f"- **Artifacts:** `species/{sid}/{PROFILE_FILE}`, "
            f"`species/{sid}/{MIDJOURNEY_FILE}`"
        )
        lines.append("")
    return lines


def literary_species_paragraphs(profiles: dict[str, dict[str, Any]]) -> list[str]:
    if not profiles:
        return []
    lines = ["## Named forms", ""]
    for sid in sorted(profiles):
        p = migrate_profile_stores(profiles[sid])
        answers = p.get("answers") or {}
        b = answers.get("B") or {}
        d = answers.get("D") or {}
        e = answers.get("E") or {}
        c = answers.get("C") or {}
        a = answers.get("A") or {}
        name = display_name(p)
        shape = str(b.get("bodyshape") or "an unnamed shape").strip()
        origin = str(c.get("origin") or a.get("origin") or "unknown").strip()
        diet = str(d.get("diet") or "").strip()
        temper = str(d.get("temperament") or "").strip()
        look = str(e.get("skin_armor_color") or e.get("iconic_wrong") or "").strip()
        bits = [f"The {name} ({shape}) is filed as {origin} to this world."]
        if diet:
            bits.append(f"It feeds on {diet}.")
        if temper:
            bits.append(f"Temperament: {temper}.")
        if look:
            bits.append(look if look.endswith(".") else look + ".")
        lines.append(" ".join(bits))
        lines.append("")
    return lines
