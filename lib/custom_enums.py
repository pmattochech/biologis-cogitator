"""Pack-local custom enums + promote-to-global."""
from __future__ import annotations

from typing import Any

from .util import ENUMS, PACKS, dump_yaml, get_active_pack, load_yaml

CUSTOM_KEYS = (
    "biome_classes",
    "planet_types",
    "body_kinds",
    "immaterium_flavor_tags",
    "origin_subtypes",
)


def custom_enums_path(pack_id: str | None = None) -> Any:
    pid = pack_id or get_active_pack()
    if not pid:
        raise ValueError("no active pack for custom enums")
    return PACKS / pid / "custom_enums.yaml"


def load_custom_enums(pack_id: str | None = None) -> dict[str, Any]:
    pid = pack_id or get_active_pack()
    if not pid:
        return {}
    path = PACKS / pid / "custom_enums.yaml"
    if not path.is_file():
        return {
            "biome_classes": [],
            "planet_types": [],
            "body_kinds": [],
            "immaterium_flavor_tags": [],
            "origin_subtypes": {"native": [], "exotic": []},
        }
    data = load_yaml(path) or {}
    data.setdefault("biome_classes", [])
    data.setdefault("planet_types", [])
    data.setdefault("body_kinds", [])
    data.setdefault("immaterium_flavor_tags", [])
    data.setdefault("origin_subtypes", {"native": [], "exotic": []})
    return data


def save_custom_enums(data: dict[str, Any], pack_id: str | None = None) -> Any:
    path = custom_enums_path(pack_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    dump_yaml(path, data)
    return path


def merged_biome_classes(pack_id: str | None = None) -> list[dict[str, Any]]:
    global_data = load_yaml(ENUMS / "biome_classes.yaml")
    classes = list(global_data.get("classes") or [])
    seen = {c.get("id") for c in classes if c.get("id")}
    custom = load_custom_enums(pack_id)
    for c in custom.get("biome_classes") or []:
        cid = c.get("id")
        if cid and cid not in seen:
            entry = dict(c)
            entry["_custom"] = True
            classes.append(entry)
            seen.add(cid)
    return classes


def merged_planet_types(pack_id: str | None = None) -> list[str]:
    global_pts = list(load_yaml(ENUMS / "planet_types.yaml").get("planet_types") or [])
    custom = load_custom_enums(pack_id)
    out = list(global_pts)
    for p in custom.get("planet_types") or []:
        if p not in out:
            out.append(p)
    return out


def merged_body_kinds(pack_id: str | None = None) -> list[str]:
    global_k = list(load_yaml(ENUMS / "planet_types.yaml").get("body_kinds") or [])
    custom = load_custom_enums(pack_id)
    out = list(global_k)
    for k in custom.get("body_kinds") or []:
        if k not in out:
            out.append(k)
    return out


def add_custom_biome_class(
    entry: dict[str, Any],
    pack_id: str | None = None,
) -> dict[str, Any]:
    data = load_custom_enums(pack_id)
    classes = list(data.get("biome_classes") or [])
    cid = entry.get("id")
    if not cid:
        raise ValueError("biome class needs id")
    classes = [c for c in classes if c.get("id") != cid]
    classes.append(entry)
    data["biome_classes"] = classes
    save_custom_enums(data, pack_id)
    return entry


def register_biome_class(
    class_id: str,
    *,
    medium: str = "terrestrial",
    default_richness: str = "moderate",
    overlay: bool = False,
    pack_id: str | None = None,
) -> dict[str, Any]:
    """Register a new biome class (pack custom_enums if pack set, else global YAML)."""
    cid = class_id.strip().replace(" ", "_").lower()
    if not cid:
        raise ValueError("biome class id required")
    # Already known?
    for existing in merged_biome_classes(pack_id):
        if existing.get("id") == cid:
            return dict(existing)
    entry = {
        "id": cid,
        "medium": medium,
        "overlay": bool(overlay),
        "default_richness": default_richness,
    }
    pid = pack_id or get_active_pack()
    if pid:
        return add_custom_biome_class(entry, pid)
    # No pack — write into global biome_classes.yaml
    global_path = ENUMS / "biome_classes.yaml"
    g = load_yaml(global_path) if global_path.is_file() else {"classes": []}
    classes = list(g.get("classes") or [])
    classes.append(entry)
    g["classes"] = classes
    dump_yaml(global_path, g)
    return entry


def add_custom_planet_type(value: str, pack_id: str | None = None) -> str:
    data = load_custom_enums(pack_id)
    pts = list(data.get("planet_types") or [])
    if value not in pts:
        pts.append(value)
    data["planet_types"] = pts
    save_custom_enums(data, pack_id)
    return value


def add_custom_flavor_tag(value: str, pack_id: str | None = None) -> str:
    data = load_custom_enums(pack_id)
    tags = list(data.get("immaterium_flavor_tags") or [])
    if value not in tags:
        tags.append(value)
    data["immaterium_flavor_tags"] = tags
    save_custom_enums(data, pack_id)
    return value


def promote_biome_class(class_id: str, pack_id: str | None = None) -> None:
    """Move a pack-local biome class into global biome_classes.yaml."""
    data = load_custom_enums(pack_id)
    classes = list(data.get("biome_classes") or [])
    match = next((c for c in classes if c.get("id") == class_id), None)
    if not match:
        raise FileNotFoundError(f"custom biome class not found: {class_id}")
    global_path = ENUMS / "biome_classes.yaml"
    g = load_yaml(global_path)
    g_classes = list(g.get("classes") or [])
    if any(c.get("id") == class_id for c in g_classes):
        # already global — just remove from pack
        pass
    else:
        clean = {k: v for k, v in match.items() if not str(k).startswith("_")}
        g_classes.append(clean)
        g["classes"] = g_classes
        dump_yaml(global_path, g)
    data["biome_classes"] = [c for c in classes if c.get("id") != class_id]
    save_custom_enums(data, pack_id)


def promote_planet_type(value: str, pack_id: str | None = None) -> None:
    data = load_custom_enums(pack_id)
    pts = list(data.get("planet_types") or [])
    if value not in pts:
        raise FileNotFoundError(f"custom planet_type not found: {value}")
    global_path = ENUMS / "planet_types.yaml"
    g = load_yaml(global_path)
    g_pts = list(g.get("planet_types") or [])
    if value not in g_pts:
        g_pts.append(value)
        g["planet_types"] = g_pts
        dump_yaml(global_path, g)
    data["planet_types"] = [p for p in pts if p != value]
    save_custom_enums(data, pack_id)
