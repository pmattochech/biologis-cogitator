"""Editor hub — sectioned edit of body locks, specimens, prose, tags."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Input, Label, Select, Static

from ... import packs as packsmod
from ...wizard_session import WizardSession
from ..features import CONSULTATION_ENABLED
from ..widgets.header import CogitatorHeader
from ..widgets.warn_log import WarnLog


class EditHubScreen(Screen):
    TRACK_DIRTY = True

    CSS = """
    #edit-hub {
        height: 1fr;
        padding: 0 1;
    }
    #edit-hub-body {
        height: 1fr;
    }
    #edit-side {
        width: 42;
        min-width: 34;
        max-width: 48;
        height: 1fr;
        padding: 0 1 0 0;
        border-right: solid #2a8040;
    }
    #edit-status {
        height: auto;
        max-height: 14;
        border: solid #2a8040;
        background: #081008;
        color: #b8ffd0;
        padding: 1;
        margin: 0 0 1 0;
    }
    #edit-side > Label {
        margin: 1 0 0 0;
        height: 1;
        color: #40c070;
    }
    #edit-side .side-hint {
        color: #3a9960;
        height: auto;
        margin: 0 0 1 0;
    }
    #edit-side #pack-select,
    #edit-side #pack-id {
        width: 1fr;
        margin: 0 0 1 0;
    }
    #edit-actions {
        height: auto;
        margin-top: 1;
    }
    #edit-actions Button {
        width: 1fr;
        min-width: 12;
        height: 3;
        margin: 0 0 1 0;
    }
    #edit-main {
        width: 1fr;
        height: 1fr;
        padding: 0 0 0 1;
    }
    #edit-main-title {
        margin: 0 0 1 0;
        color: #66ff99;
        text-style: bold;
    }
    #edit-main-hint {
        color: #3a9960;
        height: auto;
        margin: 0 0 1 0;
    }
    #edit-sections {
        height: 1fr;
    }
    #edit-sections Button {
        width: 1fr;
        height: 4;
        min-height: 3;
        margin: 0 0 1 0;
        content-align: left middle;
        text-align: left;
    }
    """

    def compose(self) -> ComposeResult:
        yield CogitatorHeader("EDITOR / BODY")
        with Vertical(id="edit-hub"):
            with Horizontal(id="edit-hub-body"):
                with Vertical(id="edit-side"):
                    yield Static(id="edit-status")
                    yield Label("Pack target")
                    yield Static(
                        "Existing pack to write locks into (dropdown).",
                        classes="side-hint",
                    )
                    yield Select(
                        [("…", "__init__")],
                        id="pack-select",
                        allow_blank=False,
                        prompt="Existing pack",
                    )
                    yield Label("New pack id")
                    yield Static(
                        "Optional — type a new id to create/save under that name.",
                        classes="side-hint",
                    )
                    yield Input(placeholder="e.g. my-mesh-export", id="pack-id")
                    with Vertical(id="edit-actions"):
                        yield Button("Save pack", id="btn-save", variant="primary")
                        yield Button("Seal results", id="btn-seal", variant="primary")
                        yield Button(
                            "Archive"
                            if CONSULTATION_ENABLED
                            else "Archive (offline)",
                            id="btn-archive",
                            disabled=not CONSULTATION_ENABLED,
                        )
                        yield Button("Back", id="btn-back")
                with Vertical(id="edit-main"):
                    yield Static("Amend sections", id="edit-main-title")
                    yield Static(
                        "Open a dossier layer to edit. Biomes and species are "
                        "registered from here.",
                        id="edit-main-hint",
                        classes="litany",
                    )
                    with VerticalScroll(id="edit-sections"):
                        yield Button(
                            "Classification  —  planet / kind / notes",
                            id="btn-class",
                        )
                        yield Button("Geology", id="btn-geo")
                        yield Button("Climate / immaterium", id="btn-chem")
                        yield Button("Biomes", id="btn-biomes")
                        yield Button("Specimens", id="btn-specimens")
                        yield Button("Magos prose", id="btn-magos")
                        yield Button("Literary prose", id="btn-lit")
                        yield Button("Custom tags", id="btn-tags")
        yield WarnLog()

    def on_mount(self) -> None:
        self.query_one(WarnLog).boot()
        self._setup_pack_select()
        self._refresh()

    def _session(self) -> WizardSession:
        return self.app.session  # type: ignore[attr-defined]

    def _setup_pack_select(self) -> None:
        session = self._session()
        packs = packsmod.list_packs()
        opts = [(str(p.get("id")), str(p.get("id"))) for p in packs if p.get("id")]
        sel = self.query_one("#pack-select", Select)
        typed = self.query_one("#pack-id", Input)
        if opts:
            sel.set_options(opts)
            prefer = session.pack_id or opts[0][1]
            if any(v == prefer for _, v in opts):
                sel.value = prefer
            else:
                sel.value = opts[0][1]
            # Keep typed field empty unless user is inventing a new id
            # (prefill with current pack only when it is not in the dropdown).
            if session.pack_id and not any(v == session.pack_id for _, v in opts):
                typed.value = session.pack_id
            else:
                typed.value = ""
                typed.placeholder = f"or new id (current: {sel.value})"
        else:
            sel.set_options([("(none yet — type a new id)", "")])
            if session.pack_id:
                typed.value = session.pack_id

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id != "pack-select":
            return
        if event.value in (Select.BLANK, "", None):
            return
        # Selecting an existing pack clears a typed override so Save uses the dropdown.
        typed = self.query_one("#pack-id", Input)
        if not typed.value.strip():
            typed.placeholder = f"or new id (current: {event.value})"

    def _pack_id(self) -> str | None:
        typed = self.query_one("#pack-id", Input).value.strip()
        if typed:
            return typed
        sel = self.query_one("#pack-select", Select)
        if sel.value not in (Select.BLANK, "", None):
            return str(sel.value)
        return self._session().pack_id

    def flush_unsaved(self) -> str | None:
        pack = self._pack_id()
        if not pack:
            return "set pack id to save"
        try:
            self._session().save_pack_lock(pack)
        except Exception as exc:
            return str(exc)
        return None

    def _refresh(self) -> None:
        session = self._session()
        body = session.body or {}
        meta = body.get("meta") or {}
        locks = body.get("locks") or {}
        pt = (body.get("layers") or {}).get("planet_type") or {}
        specs = len(locks.get("specimens") or [])
        biomes = len((body.get("layers") or {}).get("biomes") or [])
        prose = locks.get("prose") or {}
        profiles = len(session.species_profiles)
        text = (
            f"BODY\n"
            f"  {meta.get('slug') or '—'}\n"
            f"SYSTEM\n"
            f"  {meta.get('system_slug') or '—'}\n"
            f"ACTIVE PACK\n"
            f"  {session.pack_id or '(none)'}\n"
            f"PLANET\n"
            f"  {pt.get('planet_type') or '—'} / {pt.get('body_kind') or '—'}\n"
            f"COUNTS\n"
            f"  biomes {biomes} · specimens {specs}\n"
            f"  species profiles {profiles}\n"
            f"PROSE\n"
            f"  magos={'yes' if prose.get('magos') else 'no'}  "
            f"literary={'yes' if prose.get('literary') else 'no'}"
        )
        self.query_one("#edit-status", Static).update(text)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        session = self._session()
        log = self.query_one(WarnLog)
        if event.button.id == "btn-back":
            self.app.request_back()  # type: ignore[attr-defined]
            return
        if event.button.id == "btn-archive":
            if not CONSULTATION_ENABLED:
                log.push(
                    "Archive offline — dossier redesign pending. "
                    "Stay in Amendment to inspect biomes and species."
                )
                return
            slug = ((session.body or {}).get("meta") or {}).get("slug")
            from .out_archive import OutArchiveScreen

            self.app.push_screen(
                OutArchiveScreen(kind="body", slug=slug, filename="magos.md")
                if slug
                else OutArchiveScreen()
            )
            return
        if event.button.id == "btn-save":
            pack = self._pack_id()
            if not pack:
                log.push("select or type a pack id first")
                return
            try:
                path = session.save_pack_lock(pack)
                log.push(f"saved pack lock → {path}")
            except Exception as exc:
                log.push(str(exc))
            self._setup_pack_select()
            self._refresh()
            return
        if event.button.id == "btn-seal":
            if session.body is None:
                log.push("no body")
                return
            world = session.finalize()
            log.push(f"sealed cogitator-results/{world['meta']['slug']}/")
            self._refresh()
            return
        if event.button.id == "btn-class":
            from .edit_fields import EditFieldsScreen

            self.app.push_screen(EditFieldsScreen(section="classification"))
            return
        if event.button.id == "btn-geo":
            from .edit_fields import EditFieldsScreen

            self.app.push_screen(EditFieldsScreen(section="geology"))
            return
        if event.button.id == "btn-chem":
            from .edit_fields import EditFieldsScreen

            self.app.push_screen(EditFieldsScreen(section="climate"))
            return
        if event.button.id == "btn-biomes":
            from .biome_flow import BiomeFlowScreen

            self.app.push_screen(BiomeFlowScreen())
            return
        if event.button.id == "btn-specimens":
            from .edit_specimens import EditSpecimensScreen

            self.app.push_screen(EditSpecimensScreen())
            return
        if event.button.id == "btn-magos":
            from .edit_prose import EditProseScreen

            self.app.push_screen(EditProseScreen(kind="magos"))
            return
        if event.button.id == "btn-lit":
            from .edit_prose import EditProseScreen

            self.app.push_screen(EditProseScreen(kind="literary"))
            return
        if event.button.id == "btn-tags":
            from .edit_tags import EditTagsScreen

            self.app.push_screen(EditTagsScreen())
            return

    def on_screen_resume(self) -> None:
        self._refresh()
