"""Editor hub — sectioned edit of body locks, specimens, prose, tags."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Input, Select, Static

from ... import packs as packsmod
from ...wizard_session import WizardSession
from ..widgets.header import CogitatorHeader
from ..widgets.warn_log import WarnLog


class EditHubScreen(Screen):
    TRACK_DIRTY = True

    CSS = """
    #edit-hub { height: 1fr; padding: 0 1; }
    #edit-hub-toolbar { height: 3; }
    #edit-hub-toolbar Button { margin: 0 1 0 0; min-width: 10; height: 3; }
    #edit-sections { height: 1fr; }
    #edit-sections Button { width: 100%; margin: 0 0 1 0; height: 3; }
    #edit-status { height: auto; border: solid #8a6a20; padding: 1; margin-top: 1; }
    """

    def compose(self) -> ComposeResult:
        yield CogitatorHeader("EDITOR / BODY")
        with Vertical(id="edit-hub"):
            with Horizontal(id="edit-hub-toolbar"):
                yield Button("Save pack", id="btn-save", variant="primary")
                yield Button("Seal results", id="btn-seal", variant="primary")
                yield Button("Archive", id="btn-archive")
                yield Button("Back", id="btn-back")
            yield Static(id="edit-status", classes="panel")
            yield Select([("…", "__init__")], id="pack-select", allow_blank=False)
            yield Input(placeholder="or type new pack id", id="pack-id")
            with VerticalScroll(id="edit-sections"):
                yield Button("Classification (planet / kind / notes)", id="btn-class")
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
        if opts:
            sel.set_options(opts)
            prefer = session.pack_id or opts[0][1]
            if any(v == prefer for _, v in opts):
                sel.value = prefer
            else:
                sel.value = opts[0][1]
            self.query_one("#pack-id", Input).value = str(sel.value)
        else:
            sel.set_options([("(none yet)", "")])
            if session.pack_id:
                self.query_one("#pack-id", Input).value = session.pack_id

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id != "pack-select":
            return
        if event.value in (Select.BLANK, "", None):
            return
        self.query_one("#pack-id", Input).value = str(event.value)

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
            f"Body: {meta.get('slug')}  system={meta.get('system_slug')}\n"
            f"Pack: {session.pack_id or '(none)'}\n"
            f"Planet: {pt.get('planet_type')} / {pt.get('body_kind')}\n"
            f"Biomes: {biomes}  Specimens: {specs}  Species profiles: {profiles}\n"
            f"Prose overrides: magos={'yes' if prose.get('magos') else 'no'} "
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
