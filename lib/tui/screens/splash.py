"""Startup splash — play SWF timeline as braille frames in the TTY."""
from __future__ import annotations

import json
from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.timer import Timer
from textual.widgets import Static

from ...util import ROOT

ANIM_DIR = ROOT / "assets" / "splash-anim"
ANIM_FRAMES = ANIM_DIR / "frames.jsonl"
ANIM_META = ANIM_DIR / "meta.json"
CREST_FALLBACK = ROOT / "assets" / "mechanicus-crest.txt"

BOOT_LINES = (
    "++ BIOLOGIS COGITATOR // MAGOS-CLASS ALTAR",
    "++++++++",
    "++ INITIALIZING MACHINE SPIRIT AWAKEN PROTOCOL",
    "++ MACHINE SPIRIT - AWAKE",
    "+++++++++++++++++++++++++++++++++++++++++++++++",
    "++ RECITING LITANY OF IGNITION",
    "++++ 01001101 01000001 01000011 01001000 01001001 01001110 01000101",
    "++++ 01010011 01010000 01001001 01010010 01001001 01010100 00101110",
    "++ LITANY OF IGNITION RECITED",
    "++ INVOKE THE MOTIVE FORCE",
    "++ MOTIVE FORCE ANSWERS IN THE NOOSPHERE",
    "++ AUTHORISATION: MAGOS BIOLOGIS",
    "++ BY THE OMNISSIAH'S WILL - PROCEED",
    "++ GENE-VAULT UNSEALED IN HIS NAME",
    "++ COMPILING THE SPECIES MESH",
    "++ MOTIVE FORCE STABLE ACROSS ALL LOOMS",
    "++ RITE CHANNEL OPEN",
    "++ AWAITING THE MAGOS' COMMAND",
)

LINE_INTERVAL = 0.45
GLORY_HOLD = 3.0
DEFAULT_FPS = 10.0


def load_anim_frames() -> tuple[list[str], float]:
    """Return (frames, fps). Empty frames → caller uses static fallback."""
    fps = DEFAULT_FPS
    if ANIM_META.is_file():
        try:
            meta = json.loads(ANIM_META.read_text(encoding="utf-8"))
            fps = float(meta.get("fps") or DEFAULT_FPS)
        except (json.JSONDecodeError, TypeError, ValueError):
            pass
    frames: list[str] = []
    if ANIM_FRAMES.is_file():
        with ANIM_FRAMES.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    frames.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return frames, fps


def load_static_crest() -> str:
    if CREST_FALLBACK.is_file():
        return CREST_FALLBACK.read_text(encoding="utf-8").rstrip("\n")
    return "(splash animation missing — bake with scripts/bake_splash_anim.py)"


class SplashScreen(Screen):
    """Play cogitator SWF frames in-terminal, then hand off to BootScreen."""

    BINDINGS = [
        Binding("escape", "skip", "Skip", show=False),
        Binding("enter", "skip", "Skip", show=False),
        Binding("space", "skip", "Skip", show=False),
        Binding("q", "skip", "Skip", show=False),
    ]

    CSS = """
    SplashScreen {
        background: #000000;
        align: center middle;
    }

    #splash-root {
        width: 100%;
        height: 100%;
        align: center middle;
        background: #000000;
        padding: 0 1;
        overflow-y: auto;
    }

    #splash-log {
        width: 90;
        height: auto;
        color: #33ff66;
        text-style: bold;
        text-align: left;
        margin: 0 0 1 0;
    }

    #splash-anim {
        width: 90;
        height: auto;
        color: #66ff99;
        text-align: center;
        margin: 0 0 1 0;
    }

    #splash-glory {
        width: 90;
        height: auto;
        color: #b8ffd0;
        text-style: bold;
        text-align: center;
        margin-top: 1;
    }

    #splash-hint {
        width: 90;
        height: auto;
        color: #1a8033;
        text-align: center;
        margin-top: 1;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._frames, self._fps = load_anim_frames()
        self._frame_i = 0
        self._line_i = 0
        self._log_lines: list[str] = []
        self._done = False
        self._anim_done = False
        self._lines_done = False
        self._anim_timer: Timer | None = None
        self._line_timer: Timer | None = None
        self._hold_timer: Timer | None = None

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="splash-root"):
            yield Static("", id="splash-log")
            yield Static("", id="splash-anim")
            yield Static("", id="splash-glory")
            yield Static("skip: any key", id="splash-hint")

    def on_mount(self) -> None:
        anim = self.query_one("#splash-anim", Static)
        if self._frames:
            anim.update(self._frames[0])
            interval = 1.0 / max(1.0, self._fps)
            self._anim_timer = self.set_interval(interval, self._tick_anim)
        else:
            anim.update(load_static_crest())
            self._anim_done = True
        self._line_timer = self.set_interval(LINE_INTERVAL, self._tick_line)

    def _tick_anim(self) -> None:
        if self._done or self._anim_done:
            return
        self._frame_i += 1
        if self._frame_i >= len(self._frames):
            self._anim_done = True
            if self._anim_timer is not None:
                self._anim_timer.stop()
                self._anim_timer = None
            self._maybe_finish()
            return
        self.query_one("#splash-anim", Static).update(self._frames[self._frame_i])

    def _tick_line(self) -> None:
        if self._done or self._lines_done:
            return
        if self._line_i >= len(BOOT_LINES):
            self._lines_done = True
            if self._line_timer is not None:
                self._line_timer.stop()
                self._line_timer = None
            self._maybe_finish()
            return
        line = BOOT_LINES[self._line_i]
        self._line_i += 1
        self._log_lines.append(line)
        self.query_one("#splash-log", Static).update("\n".join(self._log_lines))

    def _maybe_finish(self) -> None:
        if self._done or not (self._anim_done and self._lines_done):
            return
        glory = self.query_one("#splash-glory", Static)
        glory.update("BY THE WILL OF THE MACHINE GOD\nGLORY TO THE OMNISSIAH")
        if self._hold_timer is None:
            self._hold_timer = self.set_timer(GLORY_HOLD, self._go_boot)

    def _go_boot(self) -> None:
        if self._done:
            return
        self._done = True
        for t in (self._anim_timer, self._line_timer, self._hold_timer):
            if t is not None:
                t.stop()
        self._anim_timer = self._line_timer = self._hold_timer = None
        from .boot import BootScreen

        self.app.switch_screen(BootScreen())

    def action_skip(self) -> None:
        self._go_boot()

    def on_key(self, event) -> None:  # type: ignore[no-untyped-def]
        if not self._done:
            event.stop()
            self._go_boot()
