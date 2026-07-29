"""Paths and YAML helpers for biologis-cogitator."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
ENUMS = DATA / "enums"
MATRICES = DATA / "matrices"
PACKS = DATA / "packs"
# Sealed finals (Archive / Write seal). Scratch working copies stay under out/.
# Overridden by XDG config when setup has run — see apply_config().
RESULTS = ROOT / "cogitator-results"
OUT = ROOT / "out"  # scratch / working only — not finals
TEMPLATES = ROOT / "templates"
# Legacy paths (pre-pack layout); kept only for compatibility shim
LOCKS_BODIES = DATA / "locks" / "bodies"
LOCKS_SYSTEMS = DATA / "locks" / "systems"


def apply_config() -> None:
    """Load user results/out dirs from XDG config into module globals."""
    global RESULTS, OUT
    from . import config as app_config

    cfg = app_config.load_config()
    if not cfg:
        return
    results = cfg.get("results_dir")
    out = cfg.get("out_dir")
    if results:
        RESULTS = Path(results).expanduser()
    if out:
        OUT = Path(out).expanduser()


apply_config()

# Active pack for lock resolution (set by CLI / wizard)
_active_pack: str | None = None


def set_active_pack(pack_id: str | None) -> None:
    global _active_pack
    _active_pack = pack_id


def get_active_pack() -> str | None:
    return _active_pack


def load_yaml(path: Path) -> Any:
    try:
        import yaml
    except ImportError as exc:
        raise SystemExit(
            "PyYAML is required. Install with: pip install -r requirements.txt"
        ) from exc
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def dump_yaml(path: Path, data: Any) -> None:
    import yaml

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(data, fh, sort_keys=False, allow_unicode=True)


def dump_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def warn(state: dict, message: str) -> None:
    state.setdefault("warnings", []).append(message)
