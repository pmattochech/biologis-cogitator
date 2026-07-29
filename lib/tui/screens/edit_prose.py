"""Free Magos / literary prose editor."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Static, TextArea

from ...wizard_session import WizardSession
from ..widgets.header import CogitatorHeader
from ..widgets.warn_log import WarnLog


class EditProseScreen(Screen):
    TRACK_DIRTY = True

    CSS = """
    #prose-main { height: 1fr; padding: 0 1; }
    #prose-toolbar { height: 3; }
    #prose-toolbar Button { margin: 0 1 0 0; min-width: 12; height: 3; }
    #prose-editor { height: 1fr; border: solid #2a8040; }
    """

    def __init__(self, *, kind: str = "magos", **kwargs) -> None:
        super().__init__(**kwargs)
        self.kind = kind if kind in ("magos", "literary") else "magos"

    def compose(self) -> ComposeResult:
        title = "MAGOS PROSE" if self.kind == "magos" else "LITERARY PROSE"
        yield CogitatorHeader(f"EDITOR / {title}")
        with Vertical(id="prose-main"):
            with Horizontal(id="prose-toolbar"):
                yield Button("Save override", id="btn-save", variant="primary")
                yield Button("Load generated", id="btn-gen")
                yield Button("Clear override", id="btn-clear")
                yield Button("Back", id="btn-back")
            yield Static(
                "Saved prose is stored in pack locks and preferred on Seal.",
                classes="litany",
            )
            yield TextArea("", id="prose-editor", show_line_numbers=False)
        yield WarnLog()

    def on_mount(self) -> None:
        self.query_one(WarnLog).boot()
        session = self._session()
        prose = ((session.body or {}).get("locks") or {}).get("prose") or {}
        existing = prose.get(self.kind)
        ta = self.query_one("#prose-editor", TextArea)
        if existing:
            ta.load_text(str(existing))
        else:
            ta.load_text(session.generated_prose_preview(self.kind))

    def _session(self) -> WizardSession:
        return self.app.session  # type: ignore[attr-defined]

    def flush_unsaved(self) -> str | None:
        ta = self.query_one("#prose-editor", TextArea)
        self._session().set_prose_override(self.kind, ta.text)
        return None

    def on_button_pressed(self, event: Button.Pressed) -> None:
        session = self._session()
        log = self.query_one(WarnLog)
        ta = self.query_one("#prose-editor", TextArea)
        if event.button.id == "btn-back":
            self.app.request_back()  # type: ignore[attr-defined]
            return
        if event.button.id == "btn-gen":
            ta.load_text(session.generated_prose_preview(self.kind))
            log.push("loaded generated template into editor (not saved yet)")
            return
        if event.button.id == "btn-clear":
            session.clear_prose_override(self.kind)
            ta.load_text(session.generated_prose_preview(self.kind))
            log.push(f"cleared {self.kind} override")
            return
        if event.button.id == "btn-save":
            session.set_prose_override(self.kind, ta.text)
            log.push(f"saved {self.kind} prose override on body locks")
