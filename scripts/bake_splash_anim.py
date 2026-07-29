#!/usr/bin/env python3
"""Bake SWF timeline PNG frames → braille pack for in-terminal splash video.

Requires FFDec export first:
  java -jar ffdec-cli.jar -export frame,sprite,image \\
    assets/swf-export assets/cogitator-boot.swf

Then:
  python3 scripts/bake_splash_anim.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
FRAMES_DIR = ASSETS / "swf-export" / "frames"
OUT_DIR = ASSETS / "splash-anim"

N_FRAMES = 60
COLS = 74
MAX_ROWS = 28
FPS = 10.0


def to_mask(im: Image.Image) -> Image.Image:
    arr = np.asarray(im.convert("RGBA"))
    lit = (arr[..., 1] > 35) | (arr[..., 0] > 50) | (arr[..., 2] > 50)
    out = np.zeros(arr.shape[:2], dtype=np.uint8)
    out[lit] = 255
    return Image.fromarray(out, "L")


def to_braille(mask: Image.Image, cols: int = COLS) -> str:
    px_w = cols * 2
    px_h = int(round(mask.height * (px_w / max(1, mask.width))))
    if px_h % 4:
        px_h += 4 - (px_h % 4)
    if px_h // 4 > MAX_ROWS:
        px_h = MAX_ROWS * 4
        px_w = int(round(mask.width * (px_h / max(1, mask.height))))
        if px_w % 2:
            px_w += 1
    img = mask.resize((px_w, px_h), Image.Resampling.BOX)
    ink = np.asarray(img) > 127
    dots = [
        (0, 0, 0x01),
        (1, 0, 0x08),
        (0, 1, 0x02),
        (1, 1, 0x10),
        (0, 2, 0x04),
        (1, 2, 0x20),
        (0, 3, 0x40),
        (1, 3, 0x80),
    ]
    lines: list[str] = []
    for by in range(0, px_h, 4):
        row: list[str] = []
        for bx in range(0, px_w, 2):
            val = 0
            for dx, dy, bit in dots:
                if by + dy < ink.shape[0] and bx + dx < ink.shape[1] and ink[by + dy, bx + dx]:
                    val |= bit
            row.append(chr(0x2800 + val) if val else " ")
        lines.append("".join(row).rstrip())
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines)


def main() -> int:
    pngs = sorted(FRAMES_DIR.glob("*.png"), key=lambda p: int(p.stem))
    if not pngs:
        print(f"No frames in {FRAMES_DIR} — export SWF with FFDec first.", file=sys.stderr)
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    idxs = np.linspace(0, len(pngs) - 1, N_FRAMES).astype(int)
    seen: set[int] = set()
    uniq: list[int] = []
    for i in idxs:
        ii = int(i)
        if ii not in seen:
            seen.add(ii)
            uniq.append(ii)

    frames: list[str] = []
    source_indices: list[int] = []
    for k, i in enumerate(uniq):
        art = to_braille(to_mask(Image.open(pngs[i])))
        frames.append(art)
        source_indices.append(int(pngs[i].stem))
        if k % 15 == 0:
            print(f"  {k + 1}/{len(uniq)} ← frame {pngs[i].stem}")

    meta = {
        "source": "assets/cogitator-boot.swf",
        "fps": FPS,
        "frame_count": len(frames),
        "source_indices": source_indices,
    }
    (OUT_DIR / "meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    with (OUT_DIR / "frames.jsonl").open("w", encoding="utf-8") as fh:
        for art in frames:
            fh.write(json.dumps(art, ensure_ascii=False) + "\n")

    (ASSETS / "mechanicus-crest.txt").write_text(frames[-1] + "\n", encoding="utf-8")
    (ASSETS / "mechanicus-crest.half.txt").write_text(frames[-1] + "\n", encoding="utf-8")
    size = (OUT_DIR / "frames.jsonl").stat().st_size
    print(f"Wrote {len(frames)} frames @ {FPS} fps → {OUT_DIR} ({size / 1024:.1f} KiB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
