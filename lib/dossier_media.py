"""Shared dossier plate media — one hero image per object (gallery later)."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Literal

from .state import body_out_dir, system_out_dir
from .species_profile import species_dir
from .util import ROOT

# Fixed plate: landscape Mechanicus sensor frame (matches default art).
PLATE_WIDTH = 512
PLATE_HEIGHT = 288
PLATE_FORMAT = "PNG"
PLATE_FILE = "profile.png"

# Back-compat aliases used by species UI.
PROFILE_WIDTH = PLATE_WIDTH
PROFILE_HEIGHT = PLATE_HEIGHT
PROFILE_FORMAT = PLATE_FORMAT
PROFILE_FILE = PLATE_FILE

DEFAULT_PLATE = ROOT / "assets" / "default-profile.png"
DEFAULT_PROFILE = DEFAULT_PLATE

_PAD_RGBA = (8, 16, 8, 255)
_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tif", ".tiff"}

DossierKind = Literal["species", "body", "system", "biome"]


def _require_pillow():
    try:
        from PIL import Image  # noqa: F401
    except ImportError as exc:
        raise RuntimeError(
            "Pillow is required for dossier plates. Install with: pip install Pillow"
        ) from exc
    from PIL import Image

    return Image


def resize_to_plate(image) -> object:
    """Contain + centre letterbox into PLATE_WIDTH × PLATE_HEIGHT."""
    Image = _require_pillow()
    im = image.convert("RGBA")
    plate = Image.new("RGBA", (PLATE_WIDTH, PLATE_HEIGHT), _PAD_RGBA)
    fitted = im.copy()
    fitted.thumbnail((PLATE_WIDTH, PLATE_HEIGHT), Image.Resampling.LANCZOS)
    x = (PLATE_WIDTH - fitted.width) // 2
    y = (PLATE_HEIGHT - fitted.height) // 2
    plate.paste(fitted, (x, y), fitted)
    return plate


def validate_image_file(source: Path | str) -> Path:
    Image = _require_pillow()
    src = Path(source).expanduser().resolve()
    if not src.is_file():
        raise FileNotFoundError(f"image not found: {src}")
    with Image.open(src) as im:
        im.verify()
    with Image.open(src) as im:
        im.load()
    return src


def ingest_plate_image(source: Path | str, dest: Path) -> Path:
    Image = _require_pillow()
    src = Path(source).expanduser().resolve()
    if not src.is_file():
        raise FileNotFoundError(f"image not found: {src}")
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as im:
        plate = resize_to_plate(im)
        plate.save(dest, format=PLATE_FORMAT, optimize=True)
    return dest


def plate_path(
    kind: DossierKind,
    *,
    body_slug: str = "",
    species_id: str = "",
    system_slug: str = "",
    biome_id: str = "",
) -> Path:
    if kind == "species":
        return species_dir(body_slug, species_id) / PLATE_FILE
    if kind == "body":
        return body_out_dir(body_slug) / PLATE_FILE
    if kind == "system":
        return system_out_dir(system_slug) / PLATE_FILE
    if kind == "biome":
        return body_out_dir(body_slug) / "biomes" / biome_id / PLATE_FILE
    raise ValueError(f"unknown dossier kind: {kind}")


def has_custom_plate(
    kind: DossierKind,
    *,
    body_slug: str = "",
    species_id: str = "",
    system_slug: str = "",
    biome_id: str = "",
) -> bool:
    return plate_path(
        kind,
        body_slug=body_slug,
        species_id=species_id,
        system_slug=system_slug,
        biome_id=biome_id,
    ).is_file()


def resolve_plate(
    kind: DossierKind,
    *,
    body_slug: str = "",
    species_id: str = "",
    system_slug: str = "",
    biome_id: str = "",
) -> Path:
    custom = plate_path(
        kind,
        body_slug=body_slug,
        species_id=species_id,
        system_slug=system_slug,
        biome_id=biome_id,
    )
    if custom.is_file():
        return custom
    return DEFAULT_PLATE


def plate_status_label(
    kind: DossierKind,
    *,
    body_slug: str = "",
    species_id: str = "",
    system_slug: str = "",
    biome_id: str = "",
) -> str:
    dims = f"{PLATE_WIDTH}×{PLATE_HEIGHT} {PLATE_FORMAT}"
    if has_custom_plate(
        kind,
        body_slug=body_slug,
        species_id=species_id,
        system_slug=system_slug,
        biome_id=biome_id,
    ):
        return f"custom {PLATE_FILE} ({dims})"
    return f"default placeholder ({dims})"


def write_plate(
    kind: DossierKind,
    source: Path | str,
    *,
    body_slug: str = "",
    species_id: str = "",
    system_slug: str = "",
    biome_id: str = "",
) -> Path:
    dest = plate_path(
        kind,
        body_slug=body_slug,
        species_id=species_id,
        system_slug=system_slug,
        biome_id=biome_id,
    )
    return ingest_plate_image(source, dest)


def clear_plate(
    kind: DossierKind,
    *,
    body_slug: str = "",
    species_id: str = "",
    system_slug: str = "",
    biome_id: str = "",
) -> bool:
    path = plate_path(
        kind,
        body_slug=body_slug,
        species_id=species_id,
        system_slug=system_slug,
        biome_id=biome_id,
    )
    if path.is_file():
        path.unlink()
        return True
    return False


def open_image_external(path: Path | str) -> None:
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
        title="Dossier plate",
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


# --- species back-compat thin wrappers ---


def profile_image_path(body_slug: str, species_id: str) -> Path:
    return plate_path("species", body_slug=body_slug, species_id=species_id)


def has_custom_profile_image(body_slug: str, species_id: str) -> bool:
    return has_custom_plate("species", body_slug=body_slug, species_id=species_id)


def resolve_profile_image(body_slug: str, species_id: str) -> Path:
    return resolve_plate("species", body_slug=body_slug, species_id=species_id)


def profile_status_label(body_slug: str, species_id: str) -> str:
    return plate_status_label("species", body_slug=body_slug, species_id=species_id)


def write_profile_image(body_slug: str, species_id: str, source: Path | str) -> Path:
    return write_plate("species", source, body_slug=body_slug, species_id=species_id)


def clear_profile_image(body_slug: str, species_id: str) -> bool:
    return clear_plate("species", body_slug=body_slug, species_id=species_id)


def copy_profile_image(
    body_slug: str,
    from_species_id: str,
    to_species_id: str,
) -> bool:
    src = profile_image_path(body_slug, from_species_id)
    if not src.is_file():
        return False
    dest = profile_image_path(body_slug, to_species_id)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    return True


def ingest_profile_image(source: Path | str, dest: Path) -> Path:
    return ingest_plate_image(source, dest)


def resize_to_profile_plate(image) -> object:
    return resize_to_plate(image)
