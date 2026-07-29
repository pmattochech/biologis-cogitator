"""Play the Mechanicus SWF splash via Adobe Flash Player (Flatpak) or Ruffle."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

BOOT_SWF = Path(__file__).resolve().parent.parent / "assets" / "cogitator-boot.swf"
# Finite play time — the SWF loops; we stop the player then open the app.
DEFAULT_MAX_SECONDS = 22.0


def _flash_flatpak_cmd(swf: Path) -> list[str] | None:
    if not shutil.which("flatpak"):
        return None
    try:
        r = subprocess.run(
            ["flatpak", "info", "com.adobe.Flash-Player-Projector"],
            capture_output=True,
            timeout=5,
            check=False,
        )
    except Exception:
        return None
    if r.returncode != 0:
        return None
    # Grant home read so the projector can open the SWF from the repo path
    return [
        "flatpak",
        "run",
        "--filesystem=home:ro",
        "com.adobe.Flash-Player-Projector",
        str(swf.resolve()),
    ]


def _ruffle_cmd(swf: Path) -> list[str] | None:
    ruffle = shutil.which("ruffle")
    if not ruffle:
        return None
    return [ruffle, str(swf.resolve())]


def can_play_swf() -> bool:
    if not BOOT_SWF.is_file():
        return False
    if not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
        return False
    return _flash_flatpak_cmd(BOOT_SWF) is not None or _ruffle_cmd(BOOT_SWF) is not None


def play_swf_splash(
    *,
    swf: Path | None = None,
    max_seconds: float = DEFAULT_MAX_SECONDS,
) -> bool:
    """Open the SWF in Flash/Ruffle, wait until it exits or max_seconds.

    Returns True if a player was launched.
    """
    path = swf or BOOT_SWF
    if not path.is_file():
        return False
    if not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
        return False

    cmd = _flash_flatpak_cmd(path) or _ruffle_cmd(path)
    if not cmd:
        print(
            "note: no SWF player found (install Flatpak "
            "'com.adobe.Flash-Player-Projector' or ruffle)",
            file=sys.stderr,
        )
        return False

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError as exc:
        print(f"note: failed to start SWF player ({exc})", file=sys.stderr)
        return False

    deadline = time.monotonic() + max(1.0, max_seconds)
    try:
        while time.monotonic() < deadline:
            if proc.poll() is not None:
                return True
            time.sleep(0.2)
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()
    return True
