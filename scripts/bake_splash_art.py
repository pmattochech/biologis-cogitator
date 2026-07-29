#!/usr/bin/env python3
"""Bake splash braille art from FFDec SWF export (SkullandCog + Aquila crop).

Prereq (once):
  java -jar ffdec-cli.jar -export frame,sprite,image,shape \\
    assets/swf-export assets/cogitator-boot.swf
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
SPRITE = (
    ASSETS
    / "swf-export"
    / "sprites"
    / "DefineSprite_158__40kGuide_fla.SkullandCog_52"
    / "1.png"
)
FRAME = ASSETS / "swf-export" / "frames" / "287.png"


def to_mask(im: Image.Image) -> Image.Image:
    arr = np.asarray(im.convert("RGBA"))
    lit = (arr[..., 0] > 40) | (arr[..., 1] > 40) | (arr[..., 2] > 40)
    out = np.zeros(arr.shape[:2], dtype=np.uint8)
    out[lit] = 255
    return Image.fromarray(out, "L")


def crop_content(mask: Image.Image, pad: int = 4) -> Image.Image:
    a = np.asarray(mask)
    ys, xs = np.where(a > 0)
    if len(xs) == 0:
        return mask
    box = (
        max(0, int(xs.min()) - pad),
        max(0, int(ys.min()) - pad),
        min(mask.width, int(xs.max()) + pad + 1),
        min(mask.height, int(ys.max()) + pad + 1),
    )
    return mask.crop(box)


def to_braille(mask: Image.Image, cols: int) -> str:
    px_w = cols * 2
    px_h = int(round(mask.height * (px_w / max(1, mask.width))))
    if px_h % 4:
        px_h += 4 - (px_h % 4)
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
                if ink[by + dy, bx + dx]:
                    val |= bit
            row.append(chr(0x2800 + val) if val else " ")
        lines.append("".join(row).rstrip())
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines)


def main() -> int:
    if not SPRITE.is_file() or not FRAME.is_file():
        print(
            "Missing SWF export. Run FFDec export into assets/swf-export first.",
            file=sys.stderr,
        )
        return 1

    crest_mask = crop_content(to_mask(Image.open(SPRITE)))
    crest_mask.save(ASSETS / "mechanicus-crest-source.png")
    crest = to_braille(crest_mask, cols=44)
    (ASSETS / "mechanicus-crest.txt").write_text(crest + "\n", encoding="utf-8")
    (ASSETS / "mechanicus-crest.half.txt").write_text(crest + "\n", encoding="utf-8")

    fr = Image.open(FRAME).convert("RGBA")
    w, h = fr.size
    aq = crop_content(to_mask(fr.crop((int(w * 0.62), 0, w, int(h * 0.28)))), pad=2)
    aq.save(ASSETS / "imperial-aquila-bw.png")
    aquila = to_braille(aq, cols=56)
    (ASSETS / "imperial-aquila.txt").write_text(aquila + "\n", encoding="utf-8")

    print(f"Wrote crest ({crest.count(chr(10))+1} lines) + aquila ({aquila.count(chr(10))+1} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
