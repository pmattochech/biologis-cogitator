"""Filing IDs: body AAAA, biome AAAA-BBB, species AAAA-BBB-NNN[-AA].

Universal registry lives in user config (not the install git tree), so
auto-update is not blocked by registry writes. Seeded once from
data/enums/filing_ids.csv.
"""
from __future__ import annotations

import csv
import re
import shutil
from pathlib import Path
from typing import Any, Iterator

from .state import body_out_dir
from .util import ENUMS

# Species: AETH-SHR-001 ; variant: AETH-SHR-001-AA
ENTRY_ID_RE = re.compile(r"^[A-Z]{4}-[A-Z]{3}-[0-9]{3}(?:-[A-Z]{2})?$")
ENTRY_ID_PARSE = re.compile(
    r"^(?P<planet>[A-Z]{4})-(?P<biome>[A-Z]{3})-(?P<serial>[0-9]{3})"
    r"(?:-(?P<variant>[A-Z]{2}))?$"
)
BODY_ID_RE = re.compile(r"^[A-Z]{4}$")
BIOME_FILING_RE = re.compile(r"^[A-Z]{4}-[A-Z]{3}$")

# Non-planetary origins — fixed BBB codes; never write biome rows to the CSV.
SPECIAL_ORIGIN_ABBREVS: dict[str, str] = {
    "void": "VOD",
    "warp": "WRP",
    "outer_space": "OSP",
}
SPECIAL_ORIGIN_IDS = frozenset(SPECIAL_ORIGIN_ABBREVS)

BUNDLED_REGISTRY_PATH = ENUMS / "filing_ids.csv"
# Back-compat name: prefer registry_path() for the writable file.
REGISTRY_PATH = BUNDLED_REGISTRY_PATH
CSV_FIELDS = ("kind", "filing_id", "slug", "parent_filing_id", "label")


# --- CSV registry -----------------------------------------------------------


def registry_path() -> Path:
    """Writable filing registry under XDG/AppData config (not the git checkout)."""
    from . import config as app_config

    return app_config.config_dir() / "filing_ids.csv"


def _ensure_user_registry() -> Path:
    """Return user registry path, seeding from bundled CSV on first use."""
    path = registry_path()
    if path.is_file():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    if BUNDLED_REGISTRY_PATH.is_file():
        shutil.copy2(BUNDLED_REGISTRY_PATH, path)
    else:
        path.write_text(
            "kind,filing_id,slug,parent_filing_id,label\n",
            encoding="utf-8",
        )
    return path


def _empty_rows() -> list[dict[str, str]]:
    return []


def load_registry() -> list[dict[str, str]]:
    path = _ensure_user_registry()
    if not path.is_file():
        return _empty_rows()
    with path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        rows: list[dict[str, str]] = []
        for raw in reader:
            if not raw:
                continue
            row = {
                "kind": str(raw.get("kind") or "").strip().lower(),
                "filing_id": str(raw.get("filing_id") or "").strip().upper(),
                "slug": str(raw.get("slug") or "").strip(),
                "parent_filing_id": str(raw.get("parent_filing_id") or "")
                .strip()
                .upper(),
                "label": str(raw.get("label") or "").strip(),
            }
            if row["kind"] and row["filing_id"]:
                rows.append(row)
        return rows


def save_registry(rows: list[dict[str, str]]) -> None:
    path = _ensure_user_registry()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS, lineterminator="\n")
        writer.writeheader()
        for row in sorted(
            rows,
            key=lambda r: (r.get("kind") or "", r.get("filing_id") or "", r.get("slug") or ""),
        ):
            writer.writerow(
                {
                    "kind": row.get("kind") or "",
                    "filing_id": row.get("filing_id") or "",
                    "slug": row.get("slug") or "",
                    "parent_filing_id": row.get("parent_filing_id") or "",
                    "label": row.get("label") or "",
                }
            )


def find_rows(
    *,
    kind: str | None = None,
    filing_id: str | None = None,
    slug: str | None = None,
    parent_filing_id: str | None = None,
    rows: list[dict[str, str]] | None = None,
) -> list[dict[str, str]]:
    data = rows if rows is not None else load_registry()
    out: list[dict[str, str]] = []
    for row in data:
        if kind is not None and row["kind"] != kind.lower():
            continue
        if filing_id is not None and row["filing_id"] != filing_id.upper():
            continue
        if slug is not None and row["slug"] != slug:
            continue
        if parent_filing_id is not None and row["parent_filing_id"] != parent_filing_id.upper():
            continue
        out.append(row)
    return out


def filing_id_taken(filing_id: str, rows: list[dict[str, str]] | None = None) -> bool:
    fid = filing_id.upper()
    return any(r["filing_id"] == fid for r in (rows if rows is not None else load_registry()))


def body_filing_id(body_slug: str, rows: list[dict[str, str]] | None = None) -> str | None:
    found = find_rows(kind="body", slug=body_slug, rows=rows)
    return found[0]["filing_id"] if found else None


def biome_filing_id(
    biome_slug: str,
    *,
    parent_filing_id: str | None = None,
    rows: list[dict[str, str]] | None = None,
) -> str | None:
    found = find_rows(kind="biome", slug=biome_slug, rows=rows)
    if parent_filing_id:
        parent = parent_filing_id.upper()
        found = [r for r in found if r["parent_filing_id"] == parent]
    return found[0]["filing_id"] if found else None


def biome_abbrev_from_filing(biome_filing: str) -> str | None:
    """AETH-SHR → SHR."""
    parts = normalize_entry_id(biome_filing).split("-")
    if len(parts) >= 2 and len(parts[1]) == 3:
        return parts[1]
    return None


# --- code generation --------------------------------------------------------


def _alpha_only(text: str) -> str:
    return "".join(c for c in text.upper() if c.isalpha())


def _candidate_body_codes(slug: str) -> Iterator[str]:
    token = _alpha_only(slug.replace("-", " ").split()[0] if slug else "BODY")
    if not token:
        token = "BODY"
    base = (token + "XXXX")[:4]
    yield base
    for i in range(26):
        yield base[:3] + chr(65 + i)
    for a in range(26):
        for b in range(26):
            yield base[:2] + chr(65 + a) + chr(65 + b)
    for a in range(26):
        for b in range(26):
            for c in range(26):
                yield base[0] + chr(65 + a) + chr(65 + b) + chr(65 + c)


def _candidate_biome_codes(class_or_id: str) -> Iterator[str]:
    raw = class_or_id.replace("-", "_")
    token = raw.split("_")[0] if raw else "BIO"
    letters = _alpha_only(token)
    cons = "".join(c for c in letters if c not in "AEIOU")
    vowels = "".join(c for c in letters if c in "AEIOU")
    seeds = [
        (cons + vowels + "XXX")[:3],
        (letters + "XXX")[:3],
        (cons + "XXX")[:3],
    ]
    seen: set[str] = set()
    for s in seeds:
        code = (s + "XXX")[:3]
        if code not in seen:
            seen.add(code)
            yield code
    base = (letters + "XXX")[:3]
    for i in range(26):
        yield base[:2] + chr(65 + i)
    for a in range(26):
        for b in range(26):
            yield base[0] + chr(65 + a) + chr(65 + b)
    for a in range(26):
        for b in range(26):
            for c in range(26):
                yield chr(65 + a) + chr(65 + b) + chr(65 + c)


def allocate_body_filing_id(
    body_slug: str,
    *,
    label: str = "",
    rows: list[dict[str, str]] | None = None,
) -> str:
    """Return existing body AAAA or allocate+register a new unique one."""
    data = list(rows) if rows is not None else load_registry()
    existing = body_filing_id(body_slug, data)
    if existing:
        return existing
    used = {r["filing_id"] for r in data if r["kind"] == "body"}
    for code in _candidate_body_codes(body_slug):
        if not BODY_ID_RE.match(code):
            continue
        if code in used:
            continue
        data.append(
            {
                "kind": "body",
                "filing_id": code,
                "slug": body_slug,
                "parent_filing_id": "",
                "label": label or body_slug.replace("-", " ").title(),
            }
        )
        save_registry(data)
        return code
    raise ValueError(f"no free body filing id for {body_slug!r}")


def allocate_biome_filing_id(
    biome_slug: str,
    *,
    body_slug: str,
    class_id: str = "",
    label: str = "",
    rows: list[dict[str, str]] | None = None,
) -> str:
    """Return existing AAAA-BBB for biome under body, or allocate+register."""
    if str(biome_slug or "").strip() in SPECIAL_ORIGIN_IDS:
        raise ValueError(
            f"{biome_slug!r} is a special origin place — use allocate_base_id, "
            "do not register it as a planetary biome"
        )
    data = list(rows) if rows is not None else load_registry()
    body_id = allocate_body_filing_id(body_slug, rows=data)
    # reload after possible body write
    data = load_registry()
    existing = biome_filing_id(biome_slug, parent_filing_id=body_id, rows=data)
    if existing:
        return existing
    used_bbb = {
        biome_abbrev_from_filing(r["filing_id"]) or ""
        for r in data
        if r["kind"] == "biome" and r["parent_filing_id"] == body_id
    }
    seed = class_id or biome_slug
    for bbb in _candidate_biome_codes(seed):
        if len(bbb) != 3:
            continue
        if bbb in used_bbb:
            continue
        fid = f"{body_id}-{bbb}"
        if filing_id_taken(fid, data):
            continue
        data.append(
            {
                "kind": "biome",
                "filing_id": fid,
                "slug": biome_slug,
                "parent_filing_id": body_id,
                "label": label or biome_slug.replace("_", " "),
            }
        )
        save_registry(data)
        return fid
    raise ValueError(f"no free biome filing id for {biome_slug!r} under {body_slug!r}")


def ensure_world_filing_ids(world: dict[str, Any]) -> str:
    """Ensure body + biomes have filing_id fields and CSV rows. Returns body AAAA."""
    meta = world.setdefault("meta", {})
    locks = world.setdefault("locks", {})
    slug = str(meta.get("slug") or "").strip()
    if not slug:
        raise ValueError("world meta.slug required for filing ids")
    body_id = allocate_body_filing_id(slug)
    meta["filing_id"] = body_id
    locks["filing_id"] = body_id

    biomes = list(locks.get("biomes") or (world.get("layers") or {}).get("biomes") or [])
    updated: list[dict[str, Any]] = []
    for b in biomes:
        entry = dict(b)
        bid = str(entry.get("id") or "").strip()
        if not bid:
            updated.append(entry)
            continue
        fid = allocate_biome_filing_id(
            bid,
            body_slug=slug,
            class_id=str(entry.get("class") or ""),
            label=str(entry.get("class") or bid),
        )
        entry["filing_id"] = fid
        updated.append(entry)
    if updated:
        locks["biomes"] = updated
        layers = world.setdefault("layers", {})
        if layers.get("biomes") is not None:
            layers["biomes"] = copy_biomes_with_filing(layers.get("biomes") or [], updated)
    return body_id


def copy_biomes_with_filing(
    layer_biomes: list[dict[str, Any]],
    lock_biomes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_id = {str(b.get("id")): b for b in lock_biomes}
    out: list[dict[str, Any]] = []
    for b in layer_biomes:
        entry = dict(b)
        match = by_id.get(str(entry.get("id")))
        if match and match.get("filing_id"):
            entry["filing_id"] = match["filing_id"]
        out.append(entry)
    return out


# --- species Entry ID -------------------------------------------------------


def is_valid_entry_id(entry_id: str) -> bool:
    return bool(ENTRY_ID_RE.match(str(entry_id or "").strip()))


def parse_entry_id(entry_id: str) -> dict[str, str] | None:
    m = ENTRY_ID_PARSE.match(str(entry_id or "").strip())
    if not m:
        return None
    out = {
        "planet": m.group("planet"),
        "biome": m.group("biome"),
        "serial": m.group("serial"),
        "prefix": f"{m.group('planet')}-{m.group('biome')}",
        "base_id": f"{m.group('planet')}-{m.group('biome')}-{m.group('serial')}",
    }
    variant = m.group("variant")
    if variant:
        out["variant"] = variant
    return out


def validate_entry_id(entry_id: str) -> list[str]:
    eid = str(entry_id or "").strip()
    if not eid:
        return ["Entry ID required (AAAA-BBB-NNN or AAAA-BBB-NNN-AA)"]
    if not is_valid_entry_id(eid):
        return [
            "Entry ID must match AAAA-BBB-NNN or AAAA-BBB-NNN-AA "
            "(4 letters, 3 letters, 3 digits, optional 2-letter variant)"
        ]
    return []


def list_entry_ids_on_disk(body_slug: str) -> list[str]:
    root = body_out_dir(body_slug) / "species"
    if not root.is_dir():
        return []
    return sorted(p.name for p in root.iterdir() if p.is_dir())


def used_serials_for_prefix(
    body_slug: str,
    prefix: str,
    *,
    reserved_ids: list[str] | None = None,
) -> set[int]:
    used: set[int] = set()
    candidates = list(list_entry_ids_on_disk(body_slug))
    if reserved_ids:
        candidates.extend(reserved_ids)
    for eid in candidates:
        parsed = parse_entry_id(str(eid or "").strip().upper())
        if not parsed:
            continue
        if parsed["prefix"] != prefix:
            continue
        used.add(int(parsed["serial"]))
    return used


def next_serial(
    body_slug: str,
    prefix: str,
    *,
    reserved_ids: list[str] | None = None,
) -> int:
    used = used_serials_for_prefix(body_slug, prefix, reserved_ids=reserved_ids)
    n = 1
    while n in used:
        n += 1
        if n > 999:
            raise ValueError(f"no free serial left for {prefix}")
    return n


def format_entry_id(planet: str, biome: str, serial: int, variant: str | None = None) -> str:
    base = f"{planet.upper()}-{biome.upper()}-{serial:03d}"
    if variant:
        return f"{base}-{variant.upper()}"
    return base


def allocate_base_id(
    body_slug: str,
    *,
    biome_id: str,
    reserved_ids: list[str] | None = None,
) -> str:
    """Allocate next AAAA-BBB-NNN using CSV body/biome filing ids.

    Special origins (void / warp / outer_space) use fixed BBB codes and do
    **not** register biome rows in filing_ids.csv.
    """
    body_id = allocate_body_filing_id(body_slug)
    origin = str(biome_id or "").strip()
    if origin in SPECIAL_ORIGIN_ABBREVS:
        bbb = SPECIAL_ORIGIN_ABBREVS[origin]
    else:
        biome_fid = allocate_biome_filing_id(origin, body_slug=body_slug)
        bbb = biome_abbrev_from_filing(biome_fid)
        if not bbb:
            raise ValueError(f"invalid biome filing id {biome_fid!r}")
    prefix = f"{body_id}-{bbb}"
    serial = next_serial(body_slug, prefix, reserved_ids=reserved_ids)
    return format_entry_id(body_id, bbb, serial)


def validate_variant_parent(body_slug: str, entry_id: str) -> list[str]:
    parsed = parse_entry_id(entry_id)
    if not parsed or "variant" not in parsed:
        return []
    base = parsed["base_id"]
    base_dir = body_out_dir(body_slug) / "species" / base
    if base_dir.is_dir():
        return []
    return [f"variant {entry_id}: base {base} not on disk yet (will save variant folder only)"]


def suggest_entry_id(
    body_slug: str | None,
    biome_id: str | None,
    *,
    reserved_ids: list[str] | None = None,
) -> str:
    if not body_slug or not biome_id:
        return ""
    try:
        return allocate_base_id(
            body_slug, biome_id=biome_id, reserved_ids=reserved_ids
        )
    except ValueError:
        return ""


def normalize_entry_id(entry_id: str) -> str:
    return str(entry_id or "").strip().upper()


def _next_variant_letters(used: set[str]) -> str:
    for first in range(26):
        for second in range(26):
            suffix = chr(65 + first) + chr(65 + second)
            if suffix not in used:
                return suffix
    raise ValueError("no free variant suffix left (AA–ZZ exhausted)")


def used_variants_for_base(
    body_slug: str,
    base_id: str,
    *,
    reserved_ids: list[str] | None = None,
) -> set[str]:
    base = normalize_entry_id(base_id)
    used: set[str] = set()
    candidates = list(list_entry_ids_on_disk(body_slug))
    if reserved_ids:
        candidates.extend(reserved_ids)
    for eid in candidates:
        parsed = parse_entry_id(normalize_entry_id(str(eid or "")))
        if not parsed:
            continue
        if parsed["base_id"] != base:
            continue
        if "variant" in parsed:
            used.add(parsed["variant"])
    return used


def allocate_variant_id(
    body_slug: str,
    parent_entry_id: str,
    *,
    reserved_ids: list[str] | None = None,
) -> str:
    parsed = parse_entry_id(normalize_entry_id(parent_entry_id))
    if not parsed:
        raise ValueError(
            f"parent Entry ID invalid: {parent_entry_id!r} "
            "(need AAAA-BBB-NNN or AAAA-BBB-NNN-AA)"
        )
    base = parsed["base_id"]
    used = used_variants_for_base(body_slug, base, reserved_ids=reserved_ids)
    return f"{base}-{_next_variant_letters(used)}"


# Back-compat aliases for older call sites
def load_abbreviations() -> dict[str, Any]:
    """Deprecated shape: planets/biomes maps derived from CSV."""
    rows = load_registry()
    planets = {r["slug"]: r["filing_id"] for r in rows if r["kind"] == "body"}
    biomes = {
        r["slug"]: (biome_abbrev_from_filing(r["filing_id"]) or "")
        for r in rows
        if r["kind"] == "biome"
    }
    return {"planets": planets, "biomes": biomes}


def planet_abbrev(body_slug: str, abbrevs: dict[str, Any] | None = None) -> str | None:
    if abbrevs is not None:
        raw = (abbrevs.get("planets") or {}).get(body_slug)
        return str(raw).strip().upper() if raw else None
    return body_filing_id(body_slug)


def biome_abbrev(biome_id: str, abbrevs: dict[str, Any] | None = None) -> str | None:
    if abbrevs is not None:
        raw = (abbrevs.get("biomes") or {}).get(biome_id)
        return str(raw).strip().upper() if raw else None
    fid = biome_filing_id(biome_id)
    return biome_abbrev_from_filing(fid) if fid else None
