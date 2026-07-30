"""System dossier — heraldry plate + star/orbit summary."""
from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Static

from ... import dossier_media as dmedia
from ... import state as statemod
from ...wizard_session import WizardSession
from ..widgets.dossier_chrome import DossierChrome
from ..widgets.header import CogitatorHeader
from ..widgets.warn_log import WarnLog


class SystemDossierScreen(Screen):
    TRACK_DIRTY = False

    CSS = """
    #sysd-main { height: 1fr; padding: 0 1; }
    #sysd-toolbar { height: 3; }
    #sysd-toolbar Button { margin: 0 1 0 0; min-width: 10; height: 3; }
    #sysd-body { height: 1fr; }
    #sysd-panel {
        width: 1fr;
        height: 1fr;
        border: solid #2a8040;
        padding: 0 1;
        color: #b8ffd0;
    }
    """

    def __init__(
        self,
        *,
        system_slug: str | None = None,
        read_only: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.system_slug = system_slug
        self.read_only = read_only
        self._pending_image: Path | None = None
        self._clear_image: bool = False
        self._system: dict | None = None

    def compose(self) -> ComposeResult:
        yield CogitatorHeader(
            "DOSSIER / SYSTEM" + (" (read-only)" if self.read_only else "")
        )
        with Vertical(id="sysd-main"):
            with Horizontal(id="sysd-toolbar"):
                if not self.read_only:
                    yield Button("Save plate", id="btn-save-plate", variant="primary")
                    yield Button("Edit star (wizard)", id="btn-edit-flow")
                yield Button("Back", id="btn-back")
            with Horizontal(id="sysd-body"):
                yield DossierChrome(
                    kind_label="SYSTEM DOSSIER",
                    title=self.system_slug or "—",
                    subtitle="",
                    image_path=dmedia.DEFAULT_PLATE,
                    read_only=self.read_only,
                    id="sysd-chrome",
                )
                with VerticalScroll(id="sysd-panel"):
                    yield Static(id="sysd-summary")
        yield WarnLog()

    def on_mount(self) -> None:
        self.query_one(WarnLog).boot()
        self._load()
        self._refresh()

    def _session(self) -> WizardSession:
        return self.app.session  # type: ignore[attr-defined]

    def _chrome(self) -> DossierChrome:
        return self.query_one("#sysd-chrome", DossierChrome)

    def _load(self) -> None:
        session = self._session()
        slug = self.system_slug
        if not slug and session.system:
            slug = str(((session.system or {}).get("meta") or {}).get("slug") or "")
            self.system_slug = slug
        data = None
        if session.system and (
            ((session.system or {}).get("meta") or {}).get("slug") == slug
        ):
            data = session.system
        if data is None and slug:
            try:
                data = statemod.load_system(slug)
            except Exception:
                data = None
        self._system = data

    def _preview_image_path(self) -> Path:
        if self._clear_image:
            return dmedia.DEFAULT_PLATE
        if self._pending_image is not None and self._pending_image.is_file():
            return self._pending_image
        slug = self.system_slug or ""
        if slug:
            return dmedia.resolve_plate("system", system_slug=slug)
        return dmedia.DEFAULT_PLATE

    def _refresh(self) -> None:
        sysd = self._system or {}
        meta = sysd.get("meta") or {}
        slug = str(meta.get("slug") or self.system_slug or "—")
        mode = str(sysd.get("system_mode") or meta.get("system_mode") or "—")
        star = sysd.get("star") or {}
        spectral = star.get("spectral") or star.get("class") or "—"
        size = star.get("size_band") or star.get("size") or "—"
        lines = [
            f"Slug: `{slug}`",
            f"Mode: `{mode}`",
            f"Star: spectral `{spectral}` · size `{size}`",
            "",
            "Plate is optional heraldry for this system.",
            "Deep star edits still use the Registration system wizard for now.",
        ]
        try:
            self.query_one("#sysd-summary", Static).update("\n".join(lines))
            chrome = self._chrome()
            chrome.set_identity(
                title=slug,
                subtitle=f"mode `{mode}` · star `{spectral}` / `{size}`",
            )
            chrome.set_plate_path(self._preview_image_path())
            if self._pending_image is not None:
                chrome.set_pic_status(f"status: staged ← {self._pending_image}")
            elif self._clear_image:
                chrome.set_pic_status("status: will clear on Save plate")
            elif slug and slug != "—":
                chrome.set_pic_status(
                    f"status: {dmedia.plate_status_label('system', system_slug=slug)}"
                )
            else:
                chrome.set_pic_status("status: default placeholder")
        except Exception:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        log = self.query_one(WarnLog)
        bid = event.button.id
        if bid == "btn-back":
            if len(self.app.screen_stack) > 1:
                self.app.pop_screen()
            return
        if bid == "btn-pic-browse":
            if self.read_only:
                return
            chosen = dmedia.browse_image_path()
            if chosen:
                self._chrome().set_pic_path_value(str(chosen))
            return
        if bid == "btn-pic-import":
            if self.read_only:
                return
            raw = self._chrome().pic_path_value()
            if not raw:
                log.push("set an image path first")
                return
            try:
                self._pending_image = dmedia.validate_image_file(raw)
                self._clear_image = False
                self._refresh()
                log.push("staged system plate")
            except Exception as exc:
                log.push(str(exc))
            return
        if bid == "btn-pic-clear":
            if self.read_only:
                return
            self._pending_image = None
            self._clear_image = True
            self._refresh()
            return
        if bid == "btn-pic-open":
            try:
                dmedia.open_image_external(self._preview_image_path())
            except Exception as exc:
                log.push(str(exc))
            return
        if bid == "btn-save-plate":
            if self.read_only:
                return
            slug = self.system_slug or ""
            if not slug:
                log.push("no system slug")
                return
            # Ensure sealed/system dir exists so plate can land
            try:
                d = statemod.system_out_dir(slug)
                d.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass
            if self._clear_image:
                dmedia.clear_plate("system", system_slug=slug)
                self._clear_image = False
                log.push("cleared system plate")
            elif self._pending_image is not None:
                dmedia.write_plate("system", self._pending_image, system_slug=slug)
                self._pending_image = None
                log.push(f"saved system plate → {dmedia.plate_path('system', system_slug=slug)}")
            else:
                log.push("nothing staged")
            self._refresh()
            return
        if bid == "btn-edit-flow":
            if self.read_only:
                return
            from .system_flow import SystemFlowScreen

            self.app.push_screen(SystemFlowScreen())
            return
