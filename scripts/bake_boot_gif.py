#!/usr/bin/env python3
"""Build assets/cogitator-boot.gif from stills in assets/boot-stills/.

Drop ordered images (PNG/JPG/WebP), e.g.:
  assets/boot-stills/001.png
  assets/boot-stills/002.png
  ...

Then:
  python3 scripts/bake_boot_gif.py
  python3 scripts/bake_boot_gif.py --ms 120          # ms per frame
  python3 scripts/bake_boot_gif.py --glory-ms 3000   # hold final + Omnissiah line
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
STILLS = ROOT / "assets" / "boot-stills"
OUT = ROOT / "assets" / "cogitator-boot.gif"
SIZE = (640, 480)
EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}


def list_stills() -> list[Path]:
    files = [
        p
        for p in STILLS.iterdir()
        if p.is_file() and p.suffix.lower() in EXTS and not p.name.startswith(".")
    ]
    return sorted(files, key=lambda p: p.name.lower())


def load_frame(path: Path) -> Image.Image:
    im = Image.open(path).convert("RGB")
    # letterbox into SIZE on black
    im.thumbnail(SIZE, Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", SIZE, (0, 0, 0))
    x = (SIZE[0] - im.width) // 2
    y = (SIZE[1] - im.height) // 2
    canvas.paste(im, (x, y))
    return canvas


def add_glory(frame: Image.Image, text: str = "GLORY TO THE OMNISSIAH") -> Image.Image:
    glory = Image.fromarray((np.asarray(frame).astype(np.float32) * 0.35).astype(np.uint8))
    draw = ImageDraw.Draw(glory)
    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf", 28
        )
    except OSError:
        try:
            font = ImageFont.truetype("/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf", 28)
        except OSError:
            font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(
        ((SIZE[0] - tw) // 2, SIZE[1] - th - 40),
        text,
        fill=(102, 255, 153),
        font=font,
    )
    return glory


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ms", type=int, default=150, help="Milliseconds per still")
    ap.add_argument(
        "--glory-ms",
        type=int,
        default=3000,
        help="Hold final Omnissiah frame (0 to disable)",
    )
    ap.add_argument("--no-glory", action="store_true", help="Do not append glory frame")
    args = ap.parse_args()

    stills = list_stills()
    if not stills:
        print(
            f"No images in {STILLS}/\n"
            "Add ordered stills (001.png, 002.png, …) then re-run.",
            file=sys.stderr,
        )
        return 1

    print(f"Found {len(stills)} stills in {STILLS}")
    images: list[Image.Image] = []
    for i, path in enumerate(stills):
        frame = load_frame(path)
        images.append(frame.convert("P", palette=Image.Palette.ADAPTIVE, colors=128))
        print(f"  {i + 1:3d}/{len(stills)}  {path.name}")

    durations = [max(20, args.ms)] * len(images)

    if not args.no_glory and args.glory_ms > 0:
        glory = add_glory(load_frame(stills[-1]))
        images.append(glory.convert("P", palette=Image.Palette.ADAPTIVE, colors=128))
        durations.append(args.glory_ms)

    images[0].save(
        OUT,
        save_all=True,
        append_images=images[1:],
        duration=durations,
        loop=1,
        optimize=True,
        disposal=2,
    )
    print(f"Wrote {OUT} ({OUT.stat().st_size / 1024:.0f} KiB, {len(images)} frames)")
    print("Launch biologis-cogitator to play it in the GTK window splash.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
