"""Pick a body to edit from pack or sealed results."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Label, ListItem, ListView, Select, Static

from ... import out_archive as archive
from ... import packs as packsmod
from ...wizard_session import WizardSession
from ..widgets.header import CogitatorHeader
from ..widgets.warn_log import WarnLog


class EditPickScreen(Screen):
    CSS = """
    #edit-pick-main { height: 1fr; padding: 0 1; }
    #edit-pick-toolbar { height: 3; }
    #edit-pick-toolbar Button { margin: 0 1 0 0; min-width: 12; height: 3; }
    #slug-list { height: 1fr; border: solid #2a8040; }
    """

    def compose(self) -> ComposeResult:
        yield CogitatorHeader("RITE OF AMENDMENT")
        with Vertical(id="edit-pick-main"):
            with Horizontal(id="edit-pick-toolbar"):
                yield Button("From pack", id="btn-mode-pack", variant="primary")
                yield Button("From results", id="btn-mode-results")
                yield Button("Open editor", id="btn-open", variant="primary")
                yield Button("Back", id="btn-back")
            yield Static(
                "Select a body to amend. New biomes and species upon it are "
                "registered within this rite.",
                classes="litany",
            )
            yield Label("Pack:")
            yield Select([], id="pack-select", allow_blank=True, prompt="Pack")
            yield Label("Bodies:")
            yield ListView(id="slug-list")
        yield WarnLog()

    def on_mount(self) -> None:
        self.query_one(WarnLog).boot()
        self._mode = "pack"
        self._selected: str | None = None
        packs = packsmod.list_packs()
        opts = [(p.get("id"), p.get("id")) for p in packs if p.get("id")]
        sel = self.query_one("#pack-select", Select)
        if opts:
            sel.set_options(opts)
            session: WizardSession = self.app.session  # type: ignore[attr-defined]
            prefer = session.pack_id or opts[0][0]
            if prefer in [o[0] for o in opts]:
                sel.value = prefer
            else:
                sel.value = opts[0][0]
            self._reload()
        else:
            sel.set_options([("(none)", None)])

    def _reload(self) -> None:
        lv = self.query_one("#slug-list", ListView)
        lv.clear()
        self._selected = None
        if self._mode == "results":
            slugs = archive.list_out_bodies()
        else:
            sel = self.query_one("#pack-select", Select)
            pack_id = None if sel.value is Select.BLANK else str(sel.value)
            if not pack_id or pack_id == "(none)":
                return
            slugs = packsmod.list_body_slugs(pack_id)
        for slug in slugs:
            item = ListItem(Label(slug))
            item.body_slug = slug  # type: ignore[attr-defined]
            lv.append(item)
        self.query_one(WarnLog).push(f"{self._mode}: {len(slugs)} bodies")

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "pack-select" and self._mode == "pack":
            self._reload()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        self._selected = getattr(event.item, "body_slug", None)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-back":
            self.app.request_back()  # type: ignore[attr-defined]
            return
        if event.button.id == "btn-mode-pack":
            self._mode = "pack"
            self._reload()
            return
        if event.button.id == "btn-mode-results":
            self._mode = "results"
            self._reload()
            return
        if event.button.id == "btn-open":
            slug = self._selected
            if not slug:
                lv = self.query_one("#slug-list", ListView)
                if lv.highlighted_child is not None:
                    slug = getattr(lv.highlighted_child, "body_slug", None)
            if not slug:
                self.query_one(WarnLog).push("select a body slug")
                return
            session: WizardSession = self.app.session  # type: ignore[attr-defined]
            pack_id = None
            if self._mode == "pack":
                sel = self.query_one("#pack-select", Select)
                pack_id = None if sel.value is Select.BLANK else str(sel.value)
            try:
                session.load_body_for_edit(
                    slug, pack_id=pack_id, from_results=(self._mode == "results")
                )
            except Exception as exc:
                self.query_one(WarnLog).push(str(exc))
                return
            from .edit_hub import EditHubScreen

            self.app.push_screen(EditHubScreen())
