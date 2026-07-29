"""User config for biologis-cogitator (XDG)."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

APP_NAME = "biologis-cogitator"
ROOT = Path(__file__).resolve().parent.parent
BUNDLED_RESULTS = ROOT / "cogitator-results"

DEFAULT_RESULTS = Path.home() / "BiologisCogitator" / "results"
DEFAULT_OUT = Path.home() / "BiologisCogitator" / "out"


def config_dir() -> Path:
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / APP_NAME


def config_path() -> Path:
    return config_dir() / "config.yaml"


def is_configured() -> bool:
    cfg = load_config()
    return bool(cfg.get("setup_complete")) and bool(cfg.get("results_dir")) and bool(cfg.get("out_dir"))


def load_config() -> dict[str, Any]:
    path = config_path()
    if not path.is_file():
        return {}
    try:
        import yaml
    except ImportError:
        return {}
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return data if isinstance(data, dict) else {}


def save_config(data: dict[str, Any]) -> Path:
    import yaml

    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "results_dir": str(Path(data["results_dir"]).expanduser().resolve()),
        "out_dir": str(Path(data["out_dir"]).expanduser().resolve()),
        "setup_complete": bool(data.get("setup_complete", True)),
    }
    with path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(payload, fh, sort_keys=False, allow_unicode=True)
    return path


def default_suggestions() -> tuple[Path, Path]:
    return DEFAULT_RESULTS, DEFAULT_OUT
