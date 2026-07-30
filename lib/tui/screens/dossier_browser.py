"""Consultation — browse sealed dossiers (read-only object pages)."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Label, ListItem, ListView, Static

from ... import out_archive as archive
from ...wizard_session import WizardSession
from ..widgets.header import CogitatorHeader
from ..widgets.warn_log import WarnLog


class DossierBrowserScreen(Screen):
    """Index of sealed bodies/systems → open read-only dossiers."""

    TRACK_DIRTY = False

    CSS = """
    #db-main { height: 1fr; padding: 0 1; }
    #db-toolbar { height: 3; }
    #db-toolbar Button { margin: 0 1 0 0; min-width: 12; height: 3; }
    #db-list { height: 1fr; border: solid #2a8040; }
    #db-hint { height: auto; color: #3aa060; margin: 0 0 1 0; }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._kind: str = "body"  # body | system
        self._selected: str | None = None

    def compose(self) -> ComposeResult:
        yield CogitatorHeader("RITE OF CONSULTATION / DOSSIERS")
        with Vertical(id="db-main"):
            with Horizontal(id="db-toolbar"):
                yield Button("Bodies", id="btn-bodies", variant="primary")
                yield Button("Systems", id="btn-systems")
                yield Button("Open dossier", id="btn-open", variant="primary")
                yield Button("Back", id="btn-back")
            yield Static(
                "Read-only body and system dossiers with plate + lore. "
                "Amendment is still used for editing.",
                id="db-hint",
                classes="litany",
            )
            yield Label("Sealed packs")
            yield ListView(id="db-list")
        yield WarnLog()

    def on_mount(self) -> None:
        self.query_one(WarnLog).boot()
        self._reload()

    def _reload(self) -> None:
        lv = self.query_one("#db-list", ListView)
        lv.clear()
        self._selected = None
        if self._kind == "body":
            slugs = archive.list_out_bodies()
        else:
            slugs = archive.list_out_systems()
        for slug in slugs:
            item = ListItem(Static(slug, classes="slug-row"))
            item.out_slug = slug  # type: ignore[attr-defined]
            lv.append(item)
        self.query_one(WarnLog).push(f"{self._kind}: {len(slugs)} sealed")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        self._selected = getattr(event.item, "out_slug", None)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        log = self.query_one(WarnLog)
        bid = event.button.id
        if bid == "btn-back":
            self.app.request_back()  # type: ignore[attr-defined]
            return
        if bid == "btn-bodies":
            self._kind = "body"
            self._reload()
            return
        if bid == "btn-systems":
            self._kind = "system"
            self._reload()
            return
        if bid != "btn-open":
            return
        slug = self._selected
        if not slug:
            lv = self.query_one("#db-list", ListView)
            if lv.highlighted_child is not None:
                slug = getattr(lv.highlighted_child, "out_slug", None)
        if not slug:
            log.push("select a slug first")
            return
        session: WizardSession = self.app.session  # type: ignore[attr-defined]
        if self._kind == "body":
            try:
                session.load_body_for_edit(slug, from_results=True)
            except Exception as exc:
                log.push(str(exc))
                return
            from .body_dossier import BodyDossierScreen

            self.app.push_screen(BodyDossierScreen(read_only=True))
            return
        from .system_dossier import SystemDossierScreen

        self.app.push_screen(
            SystemDossierScreen(system_slug=slug, read_only=True)
        )
