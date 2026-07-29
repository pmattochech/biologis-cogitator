"""Species dossier media — profile picture plate (gallery later)."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from .species_profile import species_dir
from .util import ROOT

# Fixed plate: landscape Mechanicus sensor frame (matches default art).
PROFILE_WIDTH = 512
PROFILE_HEIGHT = 288
PROFILE_FORMAT = "PNG"
PROFILE_FILE = "profile.png"
PROFILE_MIME = "image/png"

DEFAULT_PROFILE = ROOT / "assets" / "default-profile.png"

# Letterbox / pad colour (near-black green, matches TUI chrome).
_PAD_RGBA = (8, 16, 8, 255)

_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tif", ".tiff"}


def profile_image_path(body_slug: str, species_id: str) -> Path:
    """On-disk custom profile plate path (may not exist)."""
    return species_dir(body_slug, species_id) / PROFILE_FILE


def has_custom_profile_image(body_slug: str, species_id: str) -> bool:
    return profile_image_path(body_slug, species_id).is_file()


def resolve_profile_image(body_slug: str, species_id: str) -> Path:
    """Custom plate if present, else shipped default placeholder."""
    custom = profile_image_path(body_slug, species_id)
    if custom.is_file():
        return custom
    return DEFAULT_PROFILE


def profile_status_label(body_slug: str, species_id: str) -> str:
    if not species_id:
        return f"default placeholder ({PROFILE_WIDTH}×{PROFILE_HEIGHT} {PROFILE_FORMAT})"
    if has_custom_profile_image(body_slug, species_id):
        return (
            f"custom {PROFILE_FILE} "
            f"({PROFILE_WIDTH}×{PROFILE_HEIGHT} {PROFILE_FORMAT})"
        )
    return f"default placeholder ({PROFILE_WIDTH}×{PROFILE_HEIGHT} {PROFILE_FORMAT})"


def _require_pillow():
    try:
        from PIL import Image  # noqa: F401
    except ImportError as exc:
        raise RuntimeError(
            "Pillow is required for profile pictures. "
            "Install with: pip install Pillow"
        ) from exc
    from PIL import Image

    return Image


def resize_to_profile_plate(image) -> object:
    """
    Fit any image into PROFILE_WIDTH × PROFILE_HEIGHT PNG plate.

    Contain + centre letterbox (no stretch, no crop of content).
    """
    Image = _require_pillow()
    im = image.convert("RGBA")
    plate = Image.new("RGBA", (PROFILE_WIDTH, PROFILE_HEIGHT), _PAD_RGBA)
    fitted = im.copy()
    fitted.thumbnail((PROFILE_WIDTH, PROFILE_HEIGHT), Image.Resampling.LANCZOS)
    x = (PROFILE_WIDTH - fitted.width) // 2
    y = (PROFILE_HEIGHT - fitted.height) // 2
    plate.paste(fitted, (x, y), fitted)
    return plate


def validate_image_file(source: Path | str) -> Path:
    """Ensure path exists and Pillow can decode it. Returns resolved path."""
    Image = _require_pillow()
    src = Path(source).expanduser().resolve()
    if not src.is_file():
        raise FileNotFoundError(f"image not found: {src}")
    with Image.open(src) as im:
        im.verify()
    # verify() can leave the file handle in a bad state; reopen briefly
    with Image.open(src) as im:
        im.load()
    return src


def ingest_profile_image(source: Path | str, dest: Path) -> Path:
    """Load source image, resize to plate, write PNG to dest. Returns dest."""
    Image = _require_pillow()
    src = Path(source).expanduser().resolve()
    if not src.is_file():
        raise FileNotFoundError(f"image not found: {src}")
    if src.suffix.lower() not in _IMAGE_SUFFIXES and src.suffix:
        # Still try open — Pillow may support it
        pass
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as im:
        plate = resize_to_profile_plate(im)
        plate.save(dest, format=PROFILE_FORMAT, optimize=True)
    return dest


def write_profile_image(body_slug: str, species_id: str, source: Path | str) -> Path:
    """Ingest and store custom profile plate for a species."""
    if not body_slug or not species_id:
        raise ValueError("body slug and species id required for profile image")
    dest = profile_image_path(body_slug, species_id)
    return ingest_profile_image(source, dest)


def clear_profile_image(body_slug: str, species_id: str) -> bool:
    """Remove custom plate if present. Returns True if a file was removed."""
    path = profile_image_path(body_slug, species_id)
    if path.is_file():
        path.unlink()
        return True
    return False


def copy_profile_image(
    body_slug: str,
    from_species_id: str,
    to_species_id: str,
) -> bool:
    """Copy custom plate between species dirs. Returns True if copied."""
    src = profile_image_path(body_slug, from_species_id)
    if not src.is_file():
        return False
    dest = profile_image_path(body_slug, to_species_id)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    return True


def open_image_external(path: Path | str) -> None:
    """Open an image with the OS default viewer."""
    import os

    p = Path(path).expanduser().resolve()
    if not p.is_file():
        raise FileNotFoundError(f"image not found: {p}")
    if sys.platform == "win32":
        os.startfile(str(p))  # type: ignore[attr-defined]
        return
    if sys.platform == "darwin":
        subprocess.Popen(["open", str(p)], shell=False)  # noqa: S603
        return
    subprocess.Popen(["xdg-open", str(p)], shell=False)  # noqa: S603


def browse_image_path() -> Path | None:
    """Native file dialog for an image path (tkinter). None if cancelled/unavailable."""
    try:
        import tkinter as tk
        from tkinter import filedialog
    except ImportError:
        return None
    root = tk.Tk()
    root.withdraw()
    try:
        root.attributes("-topmost", True)
    except Exception:
        pass
    chosen = filedialog.askopenfilename(
        title="Profile picture",
        filetypes=[
            ("Images", "*.png *.jpg *.jpeg *.webp *.gif *.bmp *.tif *.tiff"),
            ("PNG", "*.png"),
            ("All files", "*.*"),
        ],
    )
    try:
        root.destroy()
    except Exception:
        pass
    if not chosen:
        return None
    return Path(chosen)
