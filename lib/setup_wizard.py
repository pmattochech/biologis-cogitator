"""First-run / reconfigure: pick results + out dirs (GUI or CLI)."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

from . import config as app_config
from . import util


def _copy_bundled_seals(dest: Path) -> int:
    src = app_config.BUNDLED_RESULTS
    if not src.is_dir():
        return 0
    dest.mkdir(parents=True, exist_ok=True)
    copied = 0
    for child in src.iterdir():
        target = dest / child.name
        if child.is_dir():
            shutil.copytree(child, target, dirs_exist_ok=True)
        else:
            shutil.copy2(child, target)
        copied += 1
    return copied


def apply_setup(results_dir: Path, out_dir: Path, *, copy_seals: bool = False) -> Path:
    results_dir = results_dir.expanduser().resolve()
    out_dir = out_dir.expanduser().resolve()
    results_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    if copy_seals:
        _copy_bundled_seals(results_dir)
    path = app_config.save_config(
        {
            "results_dir": str(results_dir),
            "out_dir": str(out_dir),
            "setup_complete": True,
        }
    )
    util.apply_config()
    return path


def run_cli_setup() -> int:
    default_results, default_out = app_config.default_suggestions()
    print("Biologis Cogitator — setup")
    print("Choose where sealed results and scratch files are stored.\n")
    results_s = input(f"Results directory [{default_results}]: ").strip()
    out_s = input(f"Scratch (out) directory [{default_out}]: ").strip()
    results = Path(results_s) if results_s else default_results
    out = Path(out_s) if out_s else default_out
    copy = input("Copy bundled Castra Vetera seals into results? [Y/n]: ").strip().lower()
    copy_seals = copy not in ("n", "no")
    path = apply_setup(results, out, copy_seals=copy_seals)
    print(f"Saved config: {path}")
    print(f"  results: {results.expanduser().resolve()}")
    print(f"  out:     {out.expanduser().resolve()}")
    return 0


def run_gui_setup() -> int:
    try:
        import tkinter as tk
        from tkinter import filedialog, messagebox, ttk
    except ImportError:
        print(
            "tkinter is not available. Install it (Fedora: sudo dnf install python3-tkinter)\n"
            "Falling back to terminal prompts.\n",
            file=sys.stderr,
        )
        return run_cli_setup()

    default_results, default_out = app_config.default_suggestions()
    result: dict[str, object] = {"ok": False}

    root = tk.Tk()
    root.title("Biologis Cogitator — Setup")
    root.minsize(520, 240)
    root.resizable(True, False)

    frame = ttk.Frame(root, padding=16)
    frame.grid(row=0, column=0, sticky="nsew")
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    frame.columnconfigure(1, weight=1)

    ttk.Label(
        frame,
        text="Choose folders for sealed results and scratch working files.",
        wraplength=480,
    ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 12))

    results_var = tk.StringVar(value=str(default_results))
    out_var = tk.StringVar(value=str(default_out))
    copy_var = tk.BooleanVar(value=True)

    def browse_results() -> None:
        chosen = filedialog.askdirectory(
            title="Results directory",
            initialdir=results_var.get() or str(Path.home()),
            mustexist=False,
        )
        if chosen:
            results_var.set(chosen)

    def browse_out() -> None:
        chosen = filedialog.askdirectory(
            title="Scratch (out) directory",
            initialdir=out_var.get() or str(Path.home()),
            mustexist=False,
        )
        if chosen:
            out_var.set(chosen)

    ttk.Label(frame, text="Results:").grid(row=1, column=0, sticky="w", pady=4)
    ttk.Entry(frame, textvariable=results_var).grid(row=1, column=1, sticky="ew", padx=8, pady=4)
    ttk.Button(frame, text="Browse…", command=browse_results).grid(row=1, column=2, pady=4)

    ttk.Label(frame, text="Scratch:").grid(row=2, column=0, sticky="w", pady=4)
    ttk.Entry(frame, textvariable=out_var).grid(row=2, column=1, sticky="ew", padx=8, pady=4)
    ttk.Button(frame, text="Browse…", command=browse_out).grid(row=2, column=2, pady=4)

    ttk.Checkbutton(
        frame,
        text="Copy bundled Castra Vetera seals into results",
        variable=copy_var,
    ).grid(row=3, column=0, columnspan=3, sticky="w", pady=(8, 12))

    def on_save() -> None:
        results = Path(results_var.get().strip() or str(default_results))
        out = Path(out_var.get().strip() or str(default_out))
        try:
            path = apply_setup(results, out, copy_seals=bool(copy_var.get()))
        except OSError as exc:
            messagebox.showerror("Setup failed", str(exc))
            return
        result["ok"] = True
        messagebox.showinfo(
            "Setup complete",
            f"Config saved:\n{path}\n\nResults: {results.resolve()}\nScratch: {out.resolve()}",
        )
        root.destroy()

    def on_cancel() -> None:
        root.destroy()

    btns = ttk.Frame(frame)
    btns.grid(row=4, column=0, columnspan=3, sticky="e")
    ttk.Button(btns, text="Cancel", command=on_cancel).pack(side="right", padx=(8, 0))
    ttk.Button(btns, text="Save & continue", command=on_save).pack(side="right")

    root.mainloop()
    return 0 if result.get("ok") else 1


def run_setup(*, prefer_gui: bool | None = None) -> int:
    """Run setup. Prefer GUI when DISPLAY is set unless prefer_gui=False."""
    import os

    if prefer_gui is None:
        prefer_gui = bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
    if prefer_gui:
        return run_gui_setup()
    return run_cli_setup()
