"""Shared dossier chrome — hero plate, identity, media controls."""
from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Button, Input, Static

from ... import dossier_media as dmedia
from .profile_plate import ProfilePlate


class DossierChrome(Widget):
    """Always-visible plate + identity strip (+ optional media toolbar)."""

    DEFAULT_CSS = """
    DossierChrome {
        width: 54;
        min-width: 48;
        max-width: 60;
        height: auto;
        padding: 0 1 0 0;
    }
    DossierChrome #dossier-kind {
        color: #3aa060;
        height: 1;
        margin: 0 0 1 0;
    }
    DossierChrome #dossier-title {
        text-style: bold;
        color: #66ff99;
        height: auto;
        margin: 0 0 1 0;
    }
    DossierChrome #dossier-subtitle {
        color: #b8ffd0;
        height: auto;
        margin: 0 0 1 0;
    }
    DossierChrome #dossier-pic-status {
        color: #3aa060;
        height: auto;
        margin: 0 0 1 0;
    }
    DossierChrome #dossier-pic-row {
        height: 3;
        margin: 0 0 1 0;
    }
    DossierChrome #dossier-pic-row Input {
        width: 1fr;
        margin: 0 1 0 0;
    }
    DossierChrome #dossier-pic-row Button {
        margin: 0 1 0 0;
        min-width: 8;
        height: 3;
    }
    """

    def __init__(
        self,
        *,
        kind_label: str = "DOSSIER",
        title: str = "",
        subtitle: str = "",
        image_path: Path | str | None = None,
        read_only: bool = False,
        show_media_controls: bool = True,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self._kind_label = kind_label
        self._title = title
        self._subtitle = subtitle
        self._image_path = Path(image_path) if image_path else dmedia.DEFAULT_PLATE
        self.read_only = read_only
        self.show_media_controls = show_media_controls and not read_only

    def compose(self) -> ComposeResult:
        yield Static(self._kind_label, id="dossier-kind")
        yield Static(self._title or "—", id="dossier-title")
        yield Static(self._subtitle or "", id="dossier-subtitle")
        yield ProfilePlate(self._image_path, id="dossier-plate")
        yield Static(id="dossier-pic-status")
        if self.show_media_controls:
            with Horizontal(id="dossier-pic-row"):
                yield Input(placeholder="path to image…", id="dossier-pic-path")
                yield Button("Browse", id="btn-pic-browse")
                yield Button("Import", id="btn-pic-import")
                yield Button("Clear", id="btn-pic-clear")
                yield Button("Open", id="btn-pic-open")
        elif not self.read_only:
            pass
        else:
            yield Button("Open plate", id="btn-pic-open")

    def set_identity(self, *, title: str | None = None, subtitle: str | None = None) -> None:
        if title is not None:
            self._title = title
            try:
                self.query_one("#dossier-title", Static).update(title or "—")
            except Exception:
                pass
        if subtitle is not None:
            self._subtitle = subtitle
            try:
                self.query_one("#dossier-subtitle", Static).update(subtitle or "")
            except Exception:
                pass

    def set_plate_path(self, path: Path | str | None) -> None:
        p = Path(path) if path else dmedia.DEFAULT_PLATE
        if not p.is_file():
            p = dmedia.DEFAULT_PLATE
        self._image_path = p
        try:
            self.query_one("#dossier-plate", ProfilePlate).set_image_path(p)
        except Exception:
            pass

    def set_pic_status(self, text: str) -> None:
        try:
            self.query_one("#dossier-pic-status", Static).update(text)
        except Exception:
            pass

    def pic_path_value(self) -> str:
        try:
            return self.query_one("#dossier-pic-path", Input).value.strip()
        except Exception:
            return ""

    def set_pic_path_value(self, value: str) -> None:
        try:
            self.query_one("#dossier-pic-path", Input).value = value
        except Exception:
            pass


class DossierShell(Vertical):
    """Full-page shell: actions toolbar + chrome | scroll body."""

    DEFAULT_CSS = """
    DossierShell {
        height: 1fr;
        padding: 0 1;
    }
    DossierShell #dossier-toolbar {
        height: 3;
    }
    DossierShell #dossier-toolbar Button {
        margin: 0 1 0 0;
        min-width: 10;
        height: 3;
    }
    DossierShell #dossier-body {
        height: 1fr;
    }
    DossierShell #dossier-main {
        width: 1fr;
        height: 1fr;
        border: solid #2a8040;
        padding: 0 1;
    }
    """
