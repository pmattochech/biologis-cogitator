"""Biome dossiers — habitat plate per biome instance on a body."""
from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Label, ListItem, ListView, Static

from ... import dossier_media as dmedia
from ...wizard_session import WizardSession
from ..widgets.dossier_chrome import DossierChrome
from ..widgets.header import CogitatorHeader
from ..widgets.profile_plate import ProfilePlate
from ..widgets.warn_log import WarnLog


class BiomeIndexScreen(Screen):
    """List biomes on the current body; open each as a dossier page."""

    TRACK_DIRTY = False

    CSS = """
    #bi-main { height: 1fr; padding: 0 1; }
    #bi-toolbar { height: 3; }
    #bi-toolbar Button { margin: 0 1 0 0; min-width: 10; height: 3; }
    #bi-list { height: 10; border: solid #2a8040; }
    #bi-detail {
        height: 1fr;
        border: solid #2a8040;
        padding: 0 1;
        color: #b8ffd0;
    }
    #bi-hint { height: auto; color: #3aa060; margin: 0 0 1 0; }
    """

    def __init__(self, *, read_only: bool = False, **kwargs) -> None:
        super().__init__(**kwargs)
        self.read_only = read_only
        self._selected_id: str | None = None

    def compose(self) -> ComposeResult:
        yield CogitatorHeader("DOSSIER / BIOMES")
        with Vertical(id="bi-main"):
            with Horizontal(id="bi-toolbar"):
                yield Button("Open dossier", id="btn-open", variant="primary")
                if not self.read_only:
                    yield Button("Register / roll", id="btn-flow")
                yield Button("Back", id="btn-back")
            yield Static(
                "Each biome has its own dossier page with a habitat plate.",
                id="bi-hint",
                classes="litany",
            )
            yield Label("Biomes on body")
            yield ListView(id="bi-list")
            yield Label("Preview")
            with VerticalScroll(id="bi-detail"):
                yield ProfilePlate(dmedia.DEFAULT_PLATE, id="bi-preview")
                yield Static("(select a biome)", id="bi-ro")
        yield WarnLog()

    def on_mount(self) -> None:
        self.query_one(WarnLog).boot()
        self._reload()

    def on_screen_resume(self) -> None:
        self._reload()

    def _session(self) -> WizardSession:
        return self.app.session  # type: ignore[attr-defined]

    def _body_slug(self) -> str:
        return str(
            ((self._session().body or {}).get("meta") or {}).get("slug") or ""
        )

    def _biomes(self) -> list[dict]:
        body = self._session().body or {}
        locks = body.get("locks") or {}
        layers = body.get("layers") or {}
        return list(locks.get("biomes") or layers.get("biomes") or [])

    def _reload(self) -> None:
        lv = self.query_one("#bi-list", ListView)
        lv.clear()
        keep = self._selected_id
        for b in self._biomes():
            bid = str(b.get("id") or "")
            klass = str(b.get("class") or "")
            rich = str(b.get("richness") or "")
            label = f"{bid} — {klass}"
            if rich:
                label += f" [{rich}]"
            item = ListItem(Label(label))
            item.biome_id = bid  # type: ignore[attr-defined]
            lv.append(item)
        if keep:
            self._selected_id = keep
            self._show(keep)
        else:
            self.query_one("#bi-ro", Static).update("(select a biome)")

    def _show(self, biome_id: str) -> None:
        slug = self._body_slug()
        try:
            self.query_one("#bi-preview", ProfilePlate).set_image_path(
                dmedia.resolve_plate("biome", body_slug=slug, biome_id=biome_id)
                if slug
                else dmedia.DEFAULT_PLATE
            )
        except Exception:
            pass
        match = next((b for b in self._biomes() if str(b.get("id")) == biome_id), None)
        if not match:
            self.query_one("#bi-ro", Static).update(f"(unknown biome {biome_id})")
            return
        lines = [
            f"id: `{match.get('id')}`",
            f"class: `{match.get('class')}`",
            f"richness: `{match.get('richness')}`",
            f"medium: `{match.get('medium')}`",
            f"filing: `{match.get('filing_id') or match.get('entry_id') or '—'}`",
        ]
        self.query_one("#bi-ro", Static).update("\n".join(lines))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        bid = getattr(event.item, "biome_id", None)
        if not bid:
            return
        self._selected_id = str(bid)
        self._show(self._selected_id)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        log = self.query_one(WarnLog)
        bid = event.button.id
        if bid == "btn-back":
            if len(self.app.screen_stack) > 1:
                self.app.pop_screen()
            return
        if bid == "btn-flow":
            from .biome_flow import BiomeFlowScreen

            self.app.push_screen(BiomeFlowScreen())
            return
        if bid == "btn-open":
            if not self._selected_id:
                log.push("select a biome first")
                return
            self.app.push_screen(
                BiomeDossierScreen(
                    biome_id=self._selected_id,
                    read_only=self.read_only,
                )
            )
            return


class BiomeDossierScreen(Screen):
    TRACK_DIRTY = False

    CSS = """
    #bmd-main { height: 1fr; padding: 0 1; }
    #bmd-toolbar { height: 3; }
    #bmd-toolbar Button { margin: 0 1 0 0; min-width: 10; height: 3; }
    #bmd-body { height: 1fr; }
    #bmd-panel {
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
        biome_id: str,
        read_only: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.biome_id = biome_id
        self.read_only = read_only
        self._pending_image: Path | None = None
        self._clear_image: bool = False

    def compose(self) -> ComposeResult:
        yield CogitatorHeader(
            "DOSSIER / BIOME" + (" (read-only)" if self.read_only else "")
        )
        with Vertical(id="bmd-main"):
            with Horizontal(id="bmd-toolbar"):
                if not self.read_only:
                    yield Button("Save plate", id="btn-save-plate", variant="primary")
                yield Button("Back", id="btn-back")
            with Horizontal(id="bmd-body"):
                yield DossierChrome(
                    kind_label="BIOME DOSSIER",
                    title=self.biome_id,
                    subtitle="",
                    image_path=dmedia.DEFAULT_PLATE,
                    read_only=self.read_only,
                    id="bmd-chrome",
                )
                with VerticalScroll(id="bmd-panel"):
                    yield Static(id="bmd-summary")
        yield WarnLog()

    def on_mount(self) -> None:
        self.query_one(WarnLog).boot()
        self._refresh()

    def _session(self) -> WizardSession:
        return self.app.session  # type: ignore[attr-defined]

    def _chrome(self) -> DossierChrome:
        return self.query_one("#bmd-chrome", DossierChrome)

    def _body_slug(self) -> str:
        return str(
            ((self._session().body or {}).get("meta") or {}).get("slug") or ""
        )

    def _biome(self) -> dict | None:
        body = self._session().body or {}
        locks = body.get("locks") or {}
        layers = body.get("layers") or {}
        for b in list(locks.get("biomes") or layers.get("biomes") or []):
            if str(b.get("id") or "") == self.biome_id:
                return b
        return None

    def _preview_image_path(self) -> Path:
        if self._clear_image:
            return dmedia.DEFAULT_PLATE
        if self._pending_image is not None and self._pending_image.is_file():
            return self._pending_image
        slug = self._body_slug()
        if slug and self.biome_id:
            return dmedia.resolve_plate(
                "biome", body_slug=slug, biome_id=self.biome_id
            )
        return dmedia.DEFAULT_PLATE

    def _refresh(self) -> None:
        b = self._biome() or {}
        klass = str(b.get("class") or "—")
        rich = str(b.get("richness") or "—")
        medium = str(b.get("medium") or "—")
        lines = [
            f"Biome id: `{self.biome_id}`",
            f"Class: `{klass}`",
            f"Richness: `{rich}`",
            f"Medium: `{medium}`",
            f"Filing: `{b.get('filing_id') or b.get('entry_id') or '—'}`",
            "",
            "Habitat plate is optional visualization for this biome.",
            "Class/richness registration still uses Biomes → Register / roll.",
        ]
        try:
            self.query_one("#bmd-summary", Static).update("\n".join(lines))
            chrome = self._chrome()
            chrome.set_identity(
                title=self.biome_id,
                subtitle=f"class `{klass}` · richness `{rich}` · `{medium}`",
            )
            chrome.set_plate_path(self._preview_image_path())
            slug = self._body_slug()
            if self._pending_image is not None:
                chrome.set_pic_status(f"status: staged ← {self._pending_image}")
            elif self._clear_image:
                chrome.set_pic_status("status: will clear on Save plate")
            elif slug:
                chrome.set_pic_status(
                    "status: "
                    + dmedia.plate_status_label(
                        "biome", body_slug=slug, biome_id=self.biome_id
                    )
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
            slug = self._body_slug()
            if not slug:
                log.push("body slug required — seal or save body first")
                return
            if self._clear_image:
                dmedia.clear_plate(
                    "biome", body_slug=slug, biome_id=self.biome_id
                )
                self._clear_image = False
                log.push("cleared biome plate")
            elif self._pending_image is not None:
                dmedia.write_plate(
                    "biome",
                    self._pending_image,
                    body_slug=slug,
                    biome_id=self.biome_id,
                )
                self._pending_image = None
                log.push(
                    "saved biome plate → "
                    + str(
                        dmedia.plate_path(
                            "biome", body_slug=slug, biome_id=self.biome_id
                        )
                    )
                )
            else:
                log.push("nothing staged")
            self._refresh()
            return
