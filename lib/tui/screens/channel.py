"""Build channel — pick which origin branch/tag auto-update tracks."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Input, Select, Static

from ... import update as updatemod
from ..widgets.header import CogitatorHeader
from ..widgets.warn_log import WarnLog


def _is_select_blank(value: object) -> bool:
    if value is None:
        return True
    if value is Select.BLANK:
        return True
    return str(value) in {"Select.BLANK", "Select.NULL"}


class ChannelScreen(Screen):
    """Choose origin branch for auto-update / testing before master."""

    TRACK_DIRTY = False

    CSS = """
    #ch-main { height: 1fr; padding: 0 1; }
    #ch-toolbar { height: 3; }
    #ch-toolbar Button { margin: 0 1 0 0; min-width: 12; height: 3; }
    #ch-status { height: auto; color: #3aa060; margin: 0 0 1 0; }
    #ch-select { height: 3; margin: 0 0 1 0; }
    #ch-manual { height: 3; margin: 0 0 1 0; }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._branches: list[str] = []
        self._suppress = False

    def compose(self) -> ComposeResult:
        yield CogitatorHeader("VEIL CHANNEL / BUILD REF")
        with Vertical(id="ch-main"):
            with Horizontal(id="ch-toolbar"):
                yield Button("Apply", id="btn-apply", variant="primary")
                yield Button("Refresh list", id="btn-refresh")
                yield Button("Back", id="btn-back")
            yield Static(
                "Pick an origin branch to test before merging to master. "
                "BIOLOGIS_REF (env) overrides the saved channel when set. "
                "After Apply, Terminate and reopen to load the new build.",
                classes="litany",
            )
            yield Static(id="ch-status")
            yield Static("Remote branches", classes="title")
            yield Select(
                [(updatemod.DEFAULT_REF, updatemod.DEFAULT_REF)],
                id="ch-select",
                allow_blank=False,
                prompt="Branch",
            )
            yield Static("Or type a branch / tag", classes="title")
            yield Input(
                placeholder="e.g. cursor/species-profile-picture or master",
                id="ch-manual",
            )
        yield WarnLog()

    def on_mount(self) -> None:
        self.query_one(WarnLog).boot()
        self._refresh_status()
        self._reload_branches()

    def _refresh_status(self) -> None:
        ref = updatemod.update_ref()
        src = updatemod.ref_source()
        src_label = {
            "env": "BIOLOGIS_REF (environment — overrides config)",
            "config": "config.yaml git_ref",
            "default": "default (master)",
        }.get(src, src)
        local = updatemod.local_head()
        short = (local or "?")[:7]
        self.query_one("#ch-status", Static).update(
            f"active channel: {ref}\n"
            f"source: {src_label}\n"
            f"local HEAD: {short}"
        )
        try:
            self.query_one("#ch-manual", Input).value = ref
        except Exception:
            pass

    def _reload_branches(self) -> None:
        log = self.query_one(WarnLog)
        log.push("listing origin branches…")
        self._branches = updatemod.list_remote_branches()
        current = updatemod.update_ref()
        opts = self._branches or [updatemod.DEFAULT_REF]
        if current not in opts:
            opts = [current, *opts]
        sel = self.query_one("#ch-select", Select)
        self._suppress = True
        try:
            sel.set_options([(b, b) for b in opts])
            sel.value = current if current in opts else opts[0]
        finally:
            self._suppress = False
        if self._branches:
            log.push(f"{len(self._branches)} remote branch(es)")
        else:
            log.push("no remote branches listed (offline or no origin)")

    def _chosen_ref(self) -> str:
        manual = self.query_one("#ch-manual", Input).value.strip()
        if manual:
            return manual
        sel = self.query_one("#ch-select", Select)
        if not _is_select_blank(sel.value):
            return str(sel.value).strip()
        return updatemod.update_ref()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id != "ch-select" or self._suppress:
            return
        if _is_select_blank(event.value):
            return
        self.query_one("#ch-manual", Input).value = str(event.value)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        log = self.query_one(WarnLog)
        bid = event.button.id
        if bid == "btn-back":
            if len(self.app.screen_stack) > 1:
                self.app.pop_screen()
            return
        if bid == "btn-refresh":
            self._reload_branches()
            self._refresh_status()
            return
        if bid != "btn-apply":
            return
        raw = self._chosen_ref()
        try:
            status = updatemod.switch_to_ref(raw, apply_now=True)
        except ValueError as exc:
            log.push(str(exc))
            return
        self._refresh_status()
        log.push(status.message)
        if status.error:
            log.push(status.error)
        if status.applied:
            log.push("session still runs old code until Terminate + reopen")
