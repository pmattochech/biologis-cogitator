"""Body dossier — world plate + amend sections (create/edit surface)."""
from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Input, Select, Static

from ... import dossier_media as dmedia
from ... import packs as packsmod
from ...wizard_session import WizardSession
from ..widgets.dossier_chrome import DossierChrome
from ..widgets.header import CogitatorHeader
from ..widgets.warn_log import WarnLog


class BodyDossierScreen(Screen):
    """Body object page: hero plate always visible, sections to deepen the mesh."""

    TRACK_DIRTY = True

    CSS = """
    #bd-main { height: 1fr; padding: 0 1; }
    #bd-toolbar { height: 3; }
    #bd-toolbar Button { margin: 0 1 0 0; min-width: 10; height: 3; }
    #bd-body { height: 1fr; }
    #bd-main-col {
        width: 1fr;
        height: 1fr;
        border: solid #2a8040;
        padding: 0 1;
    }
    #bd-main-title {
        margin: 0 0 0 0;
        height: 1;
        color: #66ff99;
        text-style: bold;
    }
    #bd-hint {
        color: #3a9960;
        height: 1;
        margin: 0 0 1 0;
    }
    #bd-pack-label {
        height: 1;
        color: #40c070;
        margin: 0;
    }
    #bd-pack-select {
        height: 1 !important;
        min-height: 1 !important;
        max-height: 1 !important;
        margin: 0 0 0 0;
        width: 1fr;
    }
    #bd-pack-select > SelectCurrent {
        height: 1 !important;
        min-height: 1 !important;
        max-height: 1 !important;
        padding: 0 1;
    }
    #bd-pack-id {
        height: 1 !important;
        min-height: 1 !important;
        max-height: 1 !important;
        margin: 0 0 1 0;
        width: 1fr;
        padding: 0 1;
    }
    #bd-sections { height: 1fr; }
    #bd-sections Button {
        width: 1fr;
        height: 1;
        min-height: 1;
        max-height: 1;
        margin: 0 0 0 0;
        padding: 0 1;
        content-align: left middle;
        text-align: left;
    }
    """

    def __init__(self, *, read_only: bool = False, **kwargs) -> None:
        super().__init__(**kwargs)
        self.read_only = read_only
        self._pending_image: Path | None = None
        self._clear_image: bool = False

    def compose(self) -> ComposeResult:
        yield CogitatorHeader(
            "DOSSIER / BODY" + (" (read-only)" if self.read_only else "")
        )
        with Vertical(id="bd-main"):
            with Horizontal(id="bd-toolbar"):
                if not self.read_only:
                    yield Button("Save pack", id="btn-save", variant="primary")
                    yield Button("Seal results", id="btn-seal", variant="primary")
                yield Button("System dossier", id="btn-system")
                yield Button("Back", id="btn-back")
            with Horizontal(id="bd-body"):
                yield DossierChrome(
                    kind_label="BODY DOSSIER",
                    title="—",
                    subtitle="",
                    image_path=dmedia.DEFAULT_PLATE,
                    read_only=self.read_only,
                    id="bd-chrome",
                )
                with Vertical(id="bd-main-col"):
                    yield Static("World sections", id="bd-main-title")
                    yield Static(
                        "Plate stays visible while you open sections.",
                        id="bd-hint",
                        classes="litany",
                    )
                    if not self.read_only:
                        yield Static("Pack target", id="bd-pack-label")
                        yield Select(
                            [("…", "__init__")],
                            id="bd-pack-select",
                            allow_blank=False,
                            prompt="Existing pack",
                        )
                        yield Input(
                            placeholder="or new pack id…",
                            id="bd-pack-id",
                        )
                    with VerticalScroll(id="bd-sections"):
                        yield Button(
                            "Classification  —  planet / kind / notes",
                            id="btn-class",
                            disabled=self.read_only,
                        )
                        yield Button(
                            "Geology", id="btn-geo", disabled=self.read_only
                        )
                        yield Button(
                            "Climate / immaterium",
                            id="btn-chem",
                            disabled=self.read_only,
                        )
                        yield Button("Biomes", id="btn-biomes")
                        yield Button("Specimens", id="btn-specimens")
                        yield Button(
                            "Magos prose",
                            id="btn-magos",
                            disabled=self.read_only,
                        )
                        yield Button(
                            "Literary prose",
                            id="btn-lit",
                            disabled=self.read_only,
                        )
                        yield Button(
                            "Custom tags",
                            id="btn-tags",
                            disabled=self.read_only,
                        )
        yield WarnLog()

    def on_mount(self) -> None:
        self.query_one(WarnLog).boot()
        if not self.read_only:
            self._setup_pack_select()
        self._refresh()

    def on_screen_resume(self) -> None:
        self._refresh()

    def _session(self) -> WizardSession:
        return self.app.session  # type: ignore[attr-defined]

    def _chrome(self) -> DossierChrome:
        return self.query_one("#bd-chrome", DossierChrome)

    def _setup_pack_select(self) -> None:
        session = self._session()
        packs = packsmod.list_packs()
        opts = [(str(p.get("id")), str(p.get("id"))) for p in packs if p.get("id")]
        sel = self.query_one("#bd-pack-select", Select)
        typed = self.query_one("#bd-pack-id", Input)
        if opts:
            sel.set_options(opts)
            prefer = session.pack_id or opts[0][1]
            if any(v == prefer for _, v in opts):
                sel.value = prefer
            else:
                sel.value = opts[0][1]
            if session.pack_id and not any(v == session.pack_id for _, v in opts):
                typed.value = session.pack_id
            else:
                typed.value = ""
        else:
            sel.set_options([("(none yet — type a new id)", "")])
            if session.pack_id:
                typed.value = session.pack_id

    def _pack_id(self) -> str | None:
        if self.read_only:
            return self._session().pack_id
        typed = self.query_one("#bd-pack-id", Input).value.strip()
        if typed:
            return typed
        sel = self.query_one("#bd-pack-select", Select)
        if sel.value not in (Select.BLANK, "", None):
            return str(sel.value)
        return self._session().pack_id

    def flush_unsaved(self) -> str | None:
        if self.read_only:
            return None
        pack = self._pack_id()
        if not pack:
            return "set pack id to save"
        try:
            self._session().save_pack_lock(pack)
            self._apply_pending_image()
        except Exception as exc:
            return str(exc)
        return None

    def _slug(self) -> str:
        return str(
            ((self._session().body or {}).get("meta") or {}).get("slug") or ""
        )

    def _preview_image_path(self) -> Path:
        if self._clear_image:
            return dmedia.DEFAULT_PLATE
        if self._pending_image is not None and self._pending_image.is_file():
            return self._pending_image
        slug = self._slug()
        if slug:
            return dmedia.resolve_plate("body", body_slug=slug)
        return dmedia.DEFAULT_PLATE

    def _apply_pending_image(self) -> str | None:
        slug = self._slug()
        if not slug:
            return None
        if self._clear_image:
            removed = dmedia.clear_plate("body", body_slug=slug)
            self._clear_image = False
            self._pending_image = None
            return "cleared body plate" if removed else None
        if self._pending_image is not None:
            dmedia.write_plate("body", self._pending_image, body_slug=slug)
            self._pending_image = None
            return f"body plate → {dmedia.plate_path('body', body_slug=slug)}"
        return None

    def _refresh(self) -> None:
        session = self._session()
        body = session.body or {}
        meta = body.get("meta") or {}
        locks = body.get("locks") or {}
        pt = (body.get("layers") or {}).get("planet_type") or {}
        slug = str(meta.get("slug") or "—")
        sys_slug = str(meta.get("system_slug") or "—")
        specs = len(locks.get("specimens") or [])
        biomes = len((body.get("layers") or {}).get("biomes") or [])
        title = slug
        sub = (
            f"system `{sys_slug}` · "
            f"{pt.get('planet_type') or '—'} / {pt.get('body_kind') or '—'} · "
            f"biomes {biomes} · specimens {specs}"
        )
        try:
            chrome = self._chrome()
            chrome.set_identity(title=title, subtitle=sub)
            chrome.set_plate_path(self._preview_image_path())
            if self._clear_image:
                chrome.set_pic_status("status: will clear plate on Save/Seal")
            elif self._pending_image is not None:
                chrome.set_pic_status(f"status: staged ← {self._pending_image}")
            elif slug and slug != "—":
                chrome.set_pic_status(
                    f"status: {dmedia.plate_status_label('body', body_slug=slug)}"
                )
            else:
                chrome.set_pic_status("status: default placeholder")
        except Exception:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        session = self._session()
        log = self.query_one(WarnLog)
        bid = event.button.id
        if bid == "btn-back":
            self.app.request_back()  # type: ignore[attr-defined]
            return
        if bid == "btn-pic-browse":
            if self.read_only:
                return
            chosen = dmedia.browse_image_path()
            if chosen is None:
                log.push("browse cancelled")
                return
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
                session.mark_dirty()
                self._refresh()
                log.push("staged body plate (written on Save pack / Seal)")
            except Exception as exc:
                log.push(str(exc))
            return
        if bid == "btn-pic-clear":
            if self.read_only:
                return
            self._pending_image = None
            self._clear_image = True
            self._chrome().set_pic_path_value("")
            session.mark_dirty()
            self._refresh()
            return
        if bid == "btn-pic-open":
            try:
                dmedia.open_image_external(self._preview_image_path())
            except Exception as exc:
                log.push(str(exc))
            return
        if bid == "btn-system":
            from .system_dossier import SystemDossierScreen

            sys_slug = ((session.body or {}).get("meta") or {}).get("system_slug")
            if not sys_slug and session.system:
                sys_slug = ((session.system or {}).get("meta") or {}).get("slug")
            if not sys_slug:
                log.push("no system linked to this body")
                return
            self.app.push_screen(
                SystemDossierScreen(system_slug=str(sys_slug), read_only=self.read_only)
            )
            return
        if bid == "btn-save":
            if self.read_only:
                return
            pack = self._pack_id()
            if not pack:
                log.push("select or type a pack id first")
                return
            try:
                path = session.save_pack_lock(pack)
                note = self._apply_pending_image()
                log.push(f"saved pack lock → {path}")
                if note:
                    log.push(note)
            except Exception as exc:
                log.push(str(exc))
            self._setup_pack_select()
            self._refresh()
            return
        if bid == "btn-seal":
            if self.read_only:
                return
            if session.body is None:
                log.push("no body")
                return
            world = session.finalize()
            note = self._apply_pending_image()
            log.push(f"sealed cogitator-results/{world['meta']['slug']}/")
            if note:
                log.push(note)
            self._refresh()
            return
        if bid == "btn-class":
            from .edit_fields import EditFieldsScreen

            self.app.push_screen(EditFieldsScreen(section="classification"))
            return
        if bid == "btn-geo":
            from .edit_fields import EditFieldsScreen

            self.app.push_screen(EditFieldsScreen(section="geology"))
            return
        if bid == "btn-chem":
            from .edit_fields import EditFieldsScreen

            self.app.push_screen(EditFieldsScreen(section="climate"))
            return
        if bid == "btn-biomes":
            from .biome_dossier import BiomeIndexScreen

            self.app.push_screen(BiomeIndexScreen(read_only=self.read_only))
            return
        if bid == "btn-specimens":
            from .edit_specimens import EditSpecimensScreen

            self.app.push_screen(EditSpecimensScreen(read_only=self.read_only))
            return
        if bid == "btn-magos":
            if self.read_only:
                return
            from .edit_prose import EditProseScreen

            self.app.push_screen(EditProseScreen(kind="magos"))
            return
        if bid == "btn-lit":
            from .edit_prose import EditProseScreen

            self.app.push_screen(EditProseScreen(kind="literary"))
            return
        if bid == "btn-tags":
            from .edit_tags import EditTagsScreen

            self.app.push_screen(EditTagsScreen())
            return


# Back-compat alias for older imports / stack checks
EditHubScreen = BodyDossierScreen
