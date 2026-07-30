"""Inline profile-picture plate for Textual (textual-image + fallback)."""
from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static

from ... import species_media as media

# Probe terminal graphics *before* CogitatorApp.run() — see ensure_image_support().
_IMAGE_CLS: type | None = None
_PROBED = False


def ensure_image_support() -> bool:
    """Import textual-image renderable before the app starts (required for TGP/Sixel)."""
    global _IMAGE_CLS, _PROBED
    if _PROBED:
        return _IMAGE_CLS is not None
    _PROBED = True
    try:
        import textual_image.renderable  # noqa: F401
        from textual_image.widget import Image

        _IMAGE_CLS = Image
        return True
    except Exception:
        _IMAGE_CLS = None
        return False


def image_support_available() -> bool:
    if not _PROBED:
        ensure_image_support()
    return _IMAGE_CLS is not None


class ProfilePlate(Widget):
    """Fixed-height dossier plate; uses textual-image when installed."""

    DEFAULT_CSS = """
    ProfilePlate {
        height: 14;
        width: 52;
        min-width: 40;
        max-width: 64;
        margin: 0 0 1 0;
        border: solid #2a8040;
        background: #081008;
        overflow: hidden hidden;
    }
    ProfilePlate #plate-image {
        width: 1fr;
        height: 1fr;
    }
    ProfilePlate #plate-fallback {
        width: 1fr;
        height: 1fr;
        color: #3aa060;
        padding: 0 1;
    }
    """

    def __init__(
        self,
        image_path: Path | str | None = None,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self._path = Path(image_path) if image_path else media.DEFAULT_PROFILE

    def compose(self) -> ComposeResult:
        ensure_image_support()
        path = self._path if self._path.is_file() else media.DEFAULT_PROFILE
        if _IMAGE_CLS is not None:
            yield _IMAGE_CLS(str(path), id="plate-image")
        else:
            yield Static(
                "inline preview needs textual-image\n"
                f"(pip install textual-image)\n{path}",
                id="plate-fallback",
            )

    def set_image_path(self, path: Path | str | None) -> None:
        """Swap the displayed image (custom plate, staged file, or default)."""
        p = Path(path) if path else media.DEFAULT_PROFILE
        if not p.is_file():
            p = media.DEFAULT_PROFILE
        self._path = p
        if _IMAGE_CLS is not None:
            try:
                img = self.query_one("#plate-image", _IMAGE_CLS)
                img.image = str(p)
                return
            except Exception:
                pass
        try:
            self.query_one("#plate-fallback", Static).update(
                "inline preview needs textual-image\n"
                f"(pip install textual-image)\n{p}"
            )
        except Exception:
            pass
