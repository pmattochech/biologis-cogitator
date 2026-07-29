#!/usr/bin/python3
"""Biologis Cogitator — GTK window with embedded VTE (Textual host)."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Vte", "2.91")
gi.require_version("Gdk", "3.0")
gi.require_version("GdkPixbuf", "2.0")

from gi.repository import Gdk, GdkPixbuf, GLib, Gtk, Pango, Vte  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
BG_PATH = ROOT / "assets" / "window-bg.png"
BOOT_GIF = ROOT / "assets" / "cogitator-boot.gif"
ICON_PATH = ROOT / "assets" / "app-icon.png"
TITLE = "Biologis Cogitator"


def _rgba(r: float, g: float, b: float, a: float = 1.0) -> Gdk.RGBA:
    c = Gdk.RGBA()
    c.red, c.green, c.blue, c.alpha = r, g, b, a
    return c


def _load_gif_meta(path: Path) -> tuple[object, list[int], int]:
    """Open GIF for sequential playback; return (pil_image, durations_ms, n_frames).

    Frames are decoded on demand so a long typewriter splash stays memory-light.
    """
    from PIL import Image

    im = Image.open(path)
    n = int(getattr(im, "n_frames", 1) or 1)
    durations: list[int] = []
    for i in range(n):
        im.seek(i)
        durations.append(max(20, int(im.info.get("duration") or 100)))
    im.seek(0)
    return im, durations, n


def _pil_frame_to_pixbuf(im: object, index: int) -> GdkPixbuf.Pixbuf:
    from PIL import Image

    assert isinstance(im, Image.Image)
    im.seek(index)
    rgba = im.convert("RGBA")
    data = rgba.tobytes()
    w, h = rgba.size
    pix = GdkPixbuf.Pixbuf.new_from_data(
        data,
        GdkPixbuf.Colorspace.RGB,
        True,
        8,
        w,
        h,
        w * 4,
    )
    return pix.copy()


def _scale_pixbuf(
    pix: GdkPixbuf.Pixbuf, max_w: int, max_h: int
) -> GdkPixbuf.Pixbuf:
    """Scale pixbuf to fit inside max_w x max_h, keeping aspect ratio."""
    if max_w < 2 or max_h < 2:
        return pix
    pw, ph = pix.get_width(), pix.get_height()
    scale = min(max_w / pw, max_h / ph)
    tw = max(1, int(pw * scale))
    th = max(1, int(ph * scale))
    return pix.scale_simple(tw, th, GdkPixbuf.InterpType.BILINEAR)


def _find_app_python() -> str:
    candidates: list[str] = []
    if os.environ.get("BIOLOGIS_PYTHON"):
        candidates.append(os.environ["BIOLOGIS_PYTHON"])
    which = GLib.find_program_in_path("python3")
    if which:
        candidates.append(which)
    candidates.extend(
        [
            str(Path.home() / "miniconda3" / "bin" / "python3"),
            str(Path.home() / "anaconda3" / "bin" / "python3"),
            "/usr/bin/python3",
        ]
    )
    seen: set[str] = set()
    for py in candidates:
        if not py or py in seen or not Path(py).is_file():
            continue
        seen.add(py)
        try:
            r = subprocess.run(
                [py, "-c", "import textual, yaml"],
                capture_output=True,
                timeout=8,
                check=False,
            )
            if r.returncode == 0:
                return py
        except Exception:
            continue
    return "/usr/bin/python3"


class CogitatorWindow(Gtk.Window):
    def __init__(self, argv: list[str], *, play_splash: bool = True) -> None:
        super().__init__(title=TITLE)
        # Keep taskbar grouping with packaging/biologis-cogitator.desktop
        # (StartupWMClass=biologis-cogitator).
        try:
            self.set_wmclass("biologis-cogitator", "biologis-cogitator")
        except Exception:
            pass
        self.set_default_size(1180, 780)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.maximize()
        self.set_icon_name("biologis-cogitator")
        if ICON_PATH.is_file():
            try:
                self.set_icon_from_file(str(ICON_PATH))
            except GLib.Error:
                pass
        self.connect("destroy", Gtk.main_quit)
        self._argv = argv
        self._child_exited = False
        self._splash_done = False
        self._spawned = False
        self._splash_timeout_id = 0
        self._splash_pil = None
        self._splash_durations: list[int] = []
        self._splash_n_frames = 0
        self._splash_frame_i = 0
        self._splash_tick_id = 0
        self._splash_pix: GdkPixbuf.Pixbuf | None = None

        self._overlay = Gtk.Overlay()
        self.add(self._overlay)

        bg = Gtk.Image()
        if BG_PATH.is_file():
            try:
                pix = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                    str(BG_PATH), 1600, 1000, True
                )
                bg.set_from_pixbuf(pix)
            except GLib.Error:
                pass
        bg.set_halign(Gtk.Align.FILL)
        bg.set_valign(Gtk.Align.FILL)
        self._overlay.add(bg)

        self._term_frame = Gtk.Frame()
        self._term_frame.set_shadow_type(Gtk.ShadowType.NONE)
        self._term_frame.set_margin_top(16)
        self._term_frame.set_margin_bottom(16)
        self._term_frame.set_margin_start(16)
        self._term_frame.set_margin_end(16)
        self._term_frame.set_halign(Gtk.Align.FILL)
        self._term_frame.set_valign(Gtk.Align.FILL)
        self._term_frame.set_hexpand(True)
        self._term_frame.set_vexpand(True)
        css = Gtk.CssProvider()
        css.load_from_data(
            b"""
            frame {
              background-color: rgba(0, 8, 4, 0.82);
              border: 1px solid #2a8040;
            }
            """
        )
        self._term_frame.get_style_context().add_provider(
            css, Gtk.STYLE_PROVIDER_PRIORITY_USER
        )

        self.term = Vte.Terminal()
        self._style_terminal()
        self.term.set_mouse_autohide(True)
        self.term.set_hexpand(True)
        self.term.set_vexpand(True)
        self.term.connect("child-exited", self._on_child_exited)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_hexpand(True)
        scrolled.set_vexpand(True)
        scrolled.add(self.term)
        self._term_frame.add(scrolled)
        self._overlay.add_overlay(self._term_frame)

        self._splash_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self._splash_box.set_halign(Gtk.Align.FILL)
        self._splash_box.set_valign(Gtk.Align.FILL)
        self._splash_box.set_hexpand(True)
        self._splash_box.set_vexpand(True)

        splash_css = Gtk.CssProvider()
        splash_css.load_from_data(
            b"""
            box.splash {
              background-color: rgba(0, 0, 0, 1.0);
            }
            label.splash-hint {
              color: #1a8033;
              font-family: monospace;
              font-size: 11px;
            }
            """
        )
        self._splash_box.get_style_context().add_class("splash")
        self._splash_box.get_style_context().add_provider(
            splash_css, Gtk.STYLE_PROVIDER_PRIORITY_USER
        )

        self._splash_image = Gtk.Image()
        self._splash_image.set_halign(Gtk.Align.CENTER)
        self._splash_image.set_valign(Gtk.Align.CENTER)
        self._splash_image.set_hexpand(True)
        self._splash_image.set_vexpand(True)
        self._splash_box.pack_start(self._splash_image, True, True, 0)
        hint = Gtk.Label(label="skip: any key / click")
        hint.get_style_context().add_class("splash-hint")
        hint.get_style_context().add_provider(splash_css, Gtk.STYLE_PROVIDER_PRIORITY_USER)
        self._splash_box.pack_start(hint, False, False, 8)
        self._overlay.add_overlay(self._splash_box)

        self.connect("key-press-event", self._on_key)
        self.connect("size-allocate", self._on_size_allocate)
        self._splash_box.connect("button-press-event", self._on_splash_click)
        self._splash_box.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)

        self.show_all()

        # Splash covers the terminal; keep the terminal mapped so Overlay
        # allocates it at maximize size (hiding it causes a tiny leftover frame).
        if play_splash and BOOT_GIF.is_file():
            self._splash_box.show_all()
            try:
                self._overlay.reorder_overlay(self._splash_box, -1)
            except (AttributeError, TypeError):
                pass
            self._start_splash()
        else:
            self._splash_box.hide()
            self._finish_splash()

    def _start_splash(self) -> None:
        try:
            self._splash_pil, self._splash_durations, self._splash_n_frames = (
                _load_gif_meta(BOOT_GIF)
            )
        except Exception as exc:
            print(f"note: boot GIF failed ({exc}); skipping splash", file=sys.stderr)
            self._finish_splash()
            return
        if self._splash_n_frames < 1:
            self._finish_splash()
            return

        self._splash_frame_i = 0
        self._show_splash_frame()
        delay = self._splash_durations[0]
        self._splash_tick_id = GLib.timeout_add(delay, self._on_splash_tick)

    def _on_splash_tick(self) -> bool:
        if self._splash_done:
            self._splash_tick_id = 0
            return False
        self._splash_frame_i += 1
        if self._splash_frame_i >= self._splash_n_frames:
            self._splash_tick_id = 0
            self._finish_splash()
            return False
        self._show_splash_frame()
        delay = self._splash_durations[self._splash_frame_i]
        self._splash_tick_id = GLib.timeout_add(delay, self._on_splash_tick)
        return False  # we re-armed manually with next delay

    def _show_splash_frame(self) -> None:
        if self._splash_pil is None or self._splash_done:
            return
        try:
            self._splash_pix = _pil_frame_to_pixbuf(
                self._splash_pil, self._splash_frame_i
            )
        except Exception as exc:
            print(f"note: splash frame decode failed ({exc})", file=sys.stderr)
            self._finish_splash()
            return
        alloc = self._splash_image.get_allocation()
        max_w = max(alloc.width, self.get_allocated_width() - 24)
        max_h = max(alloc.height, self.get_allocated_height() - 48)
        if max_w < 32 or max_h < 32:
            max_w = max(self.get_allocated_width() - 24, 640)
            max_h = max(self.get_allocated_height() - 48, 480)
        scaled = _scale_pixbuf(self._splash_pix, max_w, max_h)
        self._splash_image.set_from_pixbuf(scaled)

    def _on_size_allocate(self, _widget: Gtk.Widget, _alloc: Gdk.Rectangle) -> None:
        if not self._splash_done and self._splash_pix is not None:
            alloc = self._splash_image.get_allocation()
            max_w = max(alloc.width, self.get_allocated_width() - 24)
            max_h = max(alloc.height, self.get_allocated_height() - 48)
            if max_w >= 32 and max_h >= 32:
                scaled = _scale_pixbuf(self._splash_pix, max_w, max_h)
                self._splash_image.set_from_pixbuf(scaled)

    def _on_splash_timeout(self) -> bool:
        self._finish_splash()
        return False

    def _on_key(self, _widget: Gtk.Widget, _event: Gdk.EventKey) -> bool:
        if not self._splash_done:
            self._finish_splash()
            return True
        return False

    def _on_splash_click(self, _widget: Gtk.Widget, _event: Gdk.EventButton) -> bool:
        if not self._splash_done:
            self._finish_splash()
            return True
        return False

    def _finish_splash(self) -> None:
        if self._splash_done:
            return
        self._splash_done = True
        if self._splash_timeout_id:
            GLib.source_remove(self._splash_timeout_id)
            self._splash_timeout_id = 0
        if self._splash_tick_id:
            GLib.source_remove(self._splash_tick_id)
            self._splash_tick_id = 0
        self._splash_box.hide()
        self._term_frame.show_all()
        self.term.grab_focus()
        if self._splash_pil is not None:
            try:
                self._splash_pil.close()
            except Exception:
                pass
            self._splash_pil = None
        self._splash_pix = None
        # Defer spawn + resize nudge until after this event finishes so VTE
        # sees the final maximized allocation (not the pre-show stub size).
        GLib.idle_add(self._after_splash_layout)

    def _after_splash_layout(self) -> bool:
        self._overlay.queue_resize()
        self._term_frame.queue_resize()
        self.term.queue_resize()
        # 1px resize nudge: VTE sometimes keeps stale cols/rows until configure.
        try:
            width, height = self.get_size()
            if width > 64 and height > 64:
                was_max = self.is_maximized()
                self.resize(max(64, width - 1), max(64, height - 1))

                def _restore() -> bool:
                    self.resize(width, height)
                    if was_max:
                        self.maximize()
                    self.term.queue_resize()
                    self.term.grab_focus()
                    return False

                GLib.idle_add(_restore)
        except Exception:
            pass
        if not self._spawned:
            self._spawned = True
            self._spawn(self._argv)
        return False

    def _style_terminal(self) -> None:
        term = self.term
        fg = _rgba(0.4, 1.0, 0.55)
        bg = _rgba(0.0, 0.03, 0.015, 0.88)
        bold = _rgba(0.72, 1.0, 0.82)
        cursor = _rgba(0.4, 0.85, 0.5)
        term.set_colors(fg, bg, None)
        term.set_color_bold(bold)
        term.set_color_cursor(cursor)
        term.set_color_cursor_foreground(bg)
        try:
            term.set_clear_background(False)  # type: ignore[attr-defined]
        except AttributeError:
            pass
        term.set_font(Pango.FontDescription("DejaVu Sans Mono 12"))
        term.set_scrollback_lines(4000)
        term.set_cursor_blink_mode(Vte.CursorBlinkMode.ON)
        term.set_audible_bell(False)

    def _spawn(self, argv: list[str]) -> None:
        py = _find_app_python()
        cmd = [py, str(ROOT / "bin" / "cli.py"), "wizard", "--no-splash", *argv]

        env = [e for e in GLib.get_environ() if not e.startswith("BIOLOGIS_WINDOW=")]
        env.append("BIOLOGIS_WINDOW=1")
        env.append("TERM=xterm-256color")
        py_bin = str(Path(py).parent)
        path = os.environ.get("PATH", "")
        if py_bin not in path.split(":"):
            env = [e for e in env if not e.startswith("PATH=")]
            env.append(f"PATH={py_bin}:{path}")

        def _on_spawn(
            terminal: Vte.Terminal,
            pid: int,
            error: GLib.Error | None,
            *_user_data: object,
        ) -> None:
            if error is not None:
                self._fail(
                    f"Failed to spawn cogitator:\n{error.message}\n\ncmd: {' '.join(cmd)}"
                )

        self.term.spawn_async(
            Vte.PtyFlags.DEFAULT,
            str(ROOT),
            cmd,
            env,
            GLib.SpawnFlags.DEFAULT,
            None,
            None,
            -1,
            None,
            _on_spawn,
            None,
        )

    def _fail(self, message: str) -> None:
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.CLOSE,
            text=message,
        )
        dialog.run()
        dialog.destroy()
        Gtk.main_quit()

    def _on_child_exited(self, _term: Vte.Terminal, _status: int) -> None:
        if self._child_exited:
            return
        self._child_exited = True
        GLib.idle_add(self.destroy)


def main(argv: list[str] | None = None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    if argv and argv[0] == "wizard":
        argv = argv[1:]

    # Must run before any Gtk.Window so the shell can match StartupWMClass.
    GLib.set_prgname("biologis-cogitator")
    Gdk.set_program_class("biologis-cogitator")

    play_splash = True
    cleaned: list[str] = []
    for a in argv:
        if a == "--no-splash":
            play_splash = False
        elif a == "--splash":
            play_splash = True
        else:
            cleaned.append(a)

    # Real splash = GIF composed from Aquila + Mechanicus stills (see scripts/bake_boot_from_logos.py).
    # SWF/Flash path abandoned.
    CogitatorWindow(cleaned, play_splash=play_splash)
    Gtk.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
