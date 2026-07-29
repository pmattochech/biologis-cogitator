"""Archive — browse and read sealed packs under cogitator-results/."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Label, ListItem, ListView, Select, Static, TextArea

from ... import out_archive as archive
from ..widgets.header import CogitatorHeader
from ..widgets.warn_log import WarnLog


def _is_select_blank(value: object) -> bool:
    if value is None:
        return True
    if value is Select.BLANK:
        return True
    # Textual may surface the sentinel as its repr string
    return str(value) in {"Select.BLANK", "Select.NULL"}


class OutArchiveScreen(Screen):
    """Read-only viewer for cogitator-results/<body>/ and …/systems/<slug>/."""

    CSS = """
    #archive-main {
        height: 1fr;
        padding: 0 1;
    }
    #archive-toolbar {
        height: 3;
        dock: top;
        align: left middle;
    }
    #archive-toolbar Button {
        margin: 0 1 0 0;
        min-width: 12;
        width: auto;
        height: 3;
    }
    #archive-body {
        height: 1fr;
    }
    #archive-sidebar {
        width: 32;
        min-width: 24;
        max-width: 40;
        height: 1fr;
        padding: 0 1 0 0;
    }
    /* Section headers only — never style ListItem children from here */
    #archive-sidebar > Label {
        margin: 1 0 0 0;
        height: 1;
        color: #40c070;
    }
    #slug-list {
        height: 1fr;
        min-height: 8;
        border: solid #2a8040;
        background: #081008;
        color: #b8ffd0;
    }
    #slug-list > ListItem {
        height: 1;
        min-height: 1;
        max-height: 1;
        padding: 0 1;
        width: 1fr;
        color: #b8ffd0;
        background: transparent;
        overflow: hidden hidden;
    }
    #slug-list > ListItem > .slug-row {
        height: 1;
        width: 1fr;
        margin: 0 !important;
        padding: 0;
        color: #b8ffd0;
        background: transparent;
    }
    #slug-list > ListItem.-hovered {
        background: #143020;
    }
    #slug-list > ListItem.-highlight {
        background: #1a5040 !important;
        color: #e8ffe8 !important;
        text-style: bold;
    }
    #slug-list > ListItem.-highlight > .slug-row {
        color: #e8ffe8 !important;
        margin: 0 !important;
    }
    #slug-list:focus > ListItem.-highlight {
        background: #248050 !important;
        color: #ffffff !important;
    }
    #slug-list:focus > ListItem.-highlight > .slug-row {
        color: #ffffff !important;
    }
    #file-select {
        height: 3;
        margin-top: 1;
    }
    #viewer-path {
        height: 1;
        margin: 0 0 0 1;
        color: #3a9960;
    }
    #viewer {
        height: 1fr;
        border: solid #2a8040;
        background: #081008;
        color: #b8ffd0;
        margin-left: 1;
    }
    """

    def __init__(
        self,
        *,
        kind: archive.Kind | None = None,
        slug: str | None = None,
        filename: str | None = None,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self._focus_kind = kind
        self._focus_slug = slug
        self._focus_filename = filename
        self._kind: archive.Kind = kind or "body"
        self._slug: str | None = slug
        self._filename: str | None = filename
        self._suppress_select = False

    def compose(self) -> ComposeResult:
        yield CogitatorHeader("RITE OF CONSULTATION")
        with Vertical(id="archive-main"):
            with Horizontal(id="archive-toolbar"):
                yield Button("Bodies", id="btn-bodies", variant="primary")
                yield Button("Systems", id="btn-systems")
                yield Button("Reload", id="btn-reload")
                yield Button("Back", id="btn-back")
            yield Static(
                "Scroll the right pane for biomes & species (past geology / climate).",
                classes="litany",
            )
            with Horizontal(id="archive-body"):
                with Vertical(id="archive-sidebar"):
                    yield Label("Slugs")
                    yield ListView(id="slug-list")
                    yield Label("Artifact")
                    yield Select(
                        [("magos.md", "magos.md")],
                        id="file-select",
                        allow_blank=False,
                        prompt="Artifact",
                    )
                with Vertical():
                    yield Static(id="viewer-path")
                    yield TextArea(
                        "(select a slug)",
                        id="viewer",
                        read_only=True,
                        show_line_numbers=False,
                    )
        yield WarnLog()

    def on_mount(self) -> None:
        self.query_one(WarnLog).boot()
        if self._focus_kind:
            self._kind = self._focus_kind
        self._reload_slugs(select_slug=self._focus_slug)
        if self._focus_slug:
            self._slug = self._focus_slug
            self._fill_files(
                prefer=self._focus_filename
                or ("magos.md" if self._kind == "body" else "system.json")
            )
            self._show_current()

    def _set_viewer(self, text: str) -> None:
        ta = self.query_one("#viewer", TextArea)
        ta.load_text(text)
        ta.scroll_home(animate=False)

    def _reload_slugs(self, *, select_slug: str | None = None) -> None:
        lv = self.query_one("#slug-list", ListView)
        lv.clear()
        slugs = (
            archive.list_out_bodies()
            if self._kind == "body"
            else archive.list_out_systems()
        )
        highlight_idx = 0
        for i, slug in enumerate(slugs):
            item = ListItem(Static(slug, classes="slug-row"))
            item.out_slug = slug  # type: ignore[attr-defined]
            lv.append(item)
            if select_slug and slug == select_slug:
                highlight_idx = i
        if slugs:
            self._slug = select_slug if select_slug in slugs else slugs[highlight_idx]
            lv.index = highlight_idx if select_slug in slugs else 0
            if select_slug is None or select_slug not in slugs:
                self._slug = slugs[0]
                lv.index = 0
            self._fill_files(
                prefer=(
                    "magos.md"
                    if self._kind == "body"
                    else "system.json"
                )
            )
            self._show_current()
        else:
            self._slug = None
            self._filename = None
            self._set_select_options([])
            self.query_one("#viewer-path", Static).update("")
            self._set_viewer(f"(no {self._kind} packs in results/)")
        self.query_one(WarnLog).push(f"archive: {len(slugs)} {self._kind} pack(s)")

    def _set_select_options(self, files: list[str], prefer: str | None = None) -> None:
        sel = self.query_one("#file-select", Select)
        self._suppress_select = True
        try:
            if not files:
                # keep a harmless placeholder so Select never goes empty
                sel.set_options([("(none)", "(none)")])
                sel.value = "(none)"
                self._filename = None
                return
            sel.set_options([(f, f) for f in files])
            pick = prefer if prefer in files else files[0]
            sel.value = pick
            self._filename = pick
        finally:
            self._suppress_select = False

    def _fill_files(self, prefer: str | None = None) -> None:
        if not self._slug:
            self._set_select_options([])
            return
        files = archive.list_artifacts(self._kind, self._slug)
        self._set_select_options(files, prefer=prefer)

    def _show_current(self) -> None:
        log = self.query_one(WarnLog)
        path_label = self.query_one("#viewer-path", Static)
        if not self._slug or not self._filename or self._filename == "(none)":
            path_label.update("")
            self._set_viewer("(nothing selected)")
            return
        try:
            text = archive.read_out_artifact(self._kind, self._slug, self._filename)
        except (FileNotFoundError, ValueError) as exc:
            path_label.update("")
            self._set_viewer(str(exc))
            log.push(str(exc))
            return
        if len(text) > 200_000:
            text = text[:200_000] + "\n\n… [truncated for cogitator display]"
        path_label.update(
            f"/ {self._kind}/{self._slug}/{self._filename}  ({len(text.splitlines())} lines)"
        )
        self._set_viewer(text)
        log.push(f"reading {self._kind}/{self._slug}/{self._filename}")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.list_view.id != "slug-list":
            return
        slug = getattr(event.item, "out_slug", None)
        if not slug:
            return
        self._slug = slug
        default = "magos.md" if self._kind == "body" else "system.json"
        self._fill_files(prefer=default)
        self._show_current()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id != "file-select":
            return
        if self._suppress_select:
            return
        if _is_select_blank(event.value):
            return
        value = str(event.value)
        if value == "(none)":
            return
        self._filename = value
        self._show_current()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-back":
            self.app.request_back()  # type: ignore[attr-defined]
            return
        if event.button.id == "btn-bodies":
            self._kind = "body"
            self._reload_slugs()
            return
        if event.button.id == "btn-systems":
            self._kind = "system"
            self._reload_slugs()
            return
        if event.button.id == "btn-reload":
            self._reload_slugs(select_slug=self._slug)
            return
