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

# Keys written by setup — always refreshed when present in save payload.
_PATH_KEYS = ("results_dir", "out_dir", "setup_complete")


def config_dir() -> Path:
    """User config directory: %APPDATA% on Windows, XDG elsewhere."""
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA") or (Path.home() / "AppData" / "Roaming"))
        return base / APP_NAME
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
    """Merge into existing config and write.

    Preserves keys such as ``git_ref`` when setup only updates paths.
    """
    import yaml

    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(load_config())
    payload.update(data)
    # Normalize path fields when present
    if "results_dir" in payload and payload["results_dir"]:
        payload["results_dir"] = str(
            Path(str(payload["results_dir"])).expanduser().resolve()
        )
    if "out_dir" in payload and payload["out_dir"]:
        payload["out_dir"] = str(Path(str(payload["out_dir"])).expanduser().resolve())
    if "setup_complete" in payload:
        payload["setup_complete"] = bool(payload["setup_complete"])
    if "git_ref" in payload:
        ref = str(payload.get("git_ref") or "").strip()
        if ref:
            payload["git_ref"] = ref
        else:
            payload.pop("git_ref", None)
    with path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(payload, fh, sort_keys=False, allow_unicode=True)
    return path


def get_git_ref() -> str | None:
    """Configured update branch/tag, or None if unset."""
    ref = str(load_config().get("git_ref") or "").strip()
    return ref or None


def set_git_ref(ref: str) -> Path:
    """Persist preferred origin branch/tag for auto-update / channel switch."""
    cfg = load_config()
    cfg["git_ref"] = str(ref).strip()
    return save_config(cfg)


def default_suggestions() -> tuple[Path, Path]:
    return DEFAULT_RESULTS, DEFAULT_OUT
