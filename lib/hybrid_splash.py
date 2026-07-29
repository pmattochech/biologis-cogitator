"""Hybrid boot splash: play SWF-derived GIF in a Tk window, then return to TUI."""
from __future__ import annotations

import os
import sys
from pathlib import Path

from .util import ROOT

BOOT_GIF = ROOT / "assets" / "cogitator-boot.gif"


def can_show_hybrid_splash() -> bool:
    if not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
        return False
    if not BOOT_GIF.is_file():
        return False
    try:
        import tkinter  # noqa: F401
        from PIL import Image, ImageTk, ImageSequence  # noqa: F401
    except ImportError:
        return False
    return True


def show_hybrid_splash(*, gif_path: Path | None = None) -> bool:
    """Play the cogitator boot GIF in a small window.

    Returns True if the splash ran (finished or skipped), False if unavailable.
    """
    path = gif_path or BOOT_GIF
    if not can_show_hybrid_splash() or not path.is_file():
        return False

    import tkinter as tk
    from PIL import Image, ImageSequence, ImageTk

    root = tk.Tk()
    root.title("Biologis Cogitator")
    root.configure(bg="#000000")
    root.resizable(False, False)

    # Load frames + durations (ms)
    frames: list[ImageTk.PhotoImage] = []
    durations: list[int] = []
    with Image.open(path) as im:
        for frame in ImageSequence.Iterator(im):
            rgb = frame.convert("RGBA")
            frames.append(ImageTk.PhotoImage(rgb, master=root))
            # PIL duration is ms; default 100
            durations.append(max(20, int(frame.info.get("duration") or 100)))

    if not frames:
        root.destroy()
        return False

    state = {"i": 0, "done": False}

    label = tk.Label(root, image=frames[0], bg="#000000", borderwidth=0, highlightthickness=0)
    label.pack()
    hint = tk.Label(
        root,
        text="skip: any key / click",
        fg="#1a8033",
        bg="#000000",
        font=("DejaVu Sans Mono", 9),
    )
    hint.pack(pady=(0, 6))

    def finish(_event: object | None = None) -> None:
        if state["done"]:
            return
        state["done"] = True
        try:
            root.destroy()
        except tk.TclError:
            pass

    def tick() -> None:
        if state["done"]:
            return
        i = state["i"]
        if i >= len(frames):
            finish()
            return
        label.configure(image=frames[i])
        # keep ref
        label.image = frames[i]
        delay = durations[i] if i < len(durations) else 100
        state["i"] = i + 1
        if state["i"] >= len(frames):
            # last frame already shown; duration includes glory hold
            root.after(delay, finish)
        else:
            root.after(delay, tick)

    root.bind("<Key>", finish)
    root.bind("<Button-1>", finish)
    root.protocol("WM_DELETE_WINDOW", finish)

    # Center on screen
    root.update_idletasks()
    w, h = root.winfo_width(), root.winfo_height()
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"+{(sw - w) // 2}+{(sh - h) // 2}")

    root.after(30, tick)
    try:
        root.mainloop()
    except tk.TclError:
        pass
    return True


def maybe_show_hybrid_splash() -> None:
    """Best-effort splash; never aborts launch on failure."""
    try:
        if show_hybrid_splash():
            return
    except Exception as exc:
        print(f"note: hybrid splash skipped ({exc})", file=sys.stderr)
