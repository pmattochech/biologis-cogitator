#!/usr/bin/env python3
"""Compose a Mechanicus-style boot GIF from Aquila + crest stills.

Uses:
  assets/aquila-green.jpeg          (or aquila-vetorized / transparent aquila)
  assets/mechanicus-logo.jpg        (or images.steamusercontent.jpg)

Output:
  assets/cogitator-boot.gif

Default canvas matches a maximized 1080p window so the splash stays sharp.
Boot copy scrolls like a cogitator bring-up, with per-line timing so it can be read.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFont

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
OUT = ASSETS / "cogitator-boot.gif"

DEFAULT_SIZE = (1920, 1080)

# (line, hold_ms) — hold is how long the line stays before the next appears.
# Icons begin fading in on the frame after MACHINE SPIRIT — AWAKE.
BOOT_SCRIPT: list[tuple[str, int]] = [
    ("++ BIOLOGIS COGITATOR // MAGOS-CLASS ALTAR", 900),
    ("++++++++", 250),
    ("++ INITIALIZING MACHINE SPIRIT AWAKEN PROTOCOL", 1000),
    ("++ MACHINE SPIRIT - AWAKE", 700),
    ("+++++++++++++++++++++++++++++++++++++++++++++++", 350),
    ("++ RECITING LITANY OF IGNITION", 550),
    ("++++ 01001101 01000001 01000011 01001000 01001001 01001110 01000101", 450),
    ("++++ 01010011 01010000 01001001 01010010 01001001 01010100 00101110", 450),
    ("++ LITANY OF IGNITION RECITED", 650),
    ("++ INVOKE THE MOTIVE FORCE", 500),
    ("++ MOTIVE FORCE ANSWERS IN THE NOOSPHERE", 600),
    ("++ AUTHORISATION: MAGOS BIOLOGIS", 700),
    ("++ BY THE OMNISSIAH'S WILL - PROCEED", 700),
    ("++ GENE-VAULT UNSEALED IN HIS NAME", 600),
    ("++ COMPILING THE SPECIES MESH", 600),
    ("++ MOTIVE FORCE STABLE ACROSS ALL LOOMS", 650),
    ("++ RITE CHANNEL OPEN", 600),
    ("++ AWAITING THE MAGOS' COMMAND", 900),
]

AWAKE_LINE = "++ MACHINE SPIRIT - AWAKE"
ICON_FADE_STEPS = 5  # frames after awake until icons are fully present

GLORY_LINES = (
    "BY THE WILL OF THE MACHINE GOD",
    "GLORY TO THE OMNISSIAH",
)


def _find(*names: str) -> Path | None:
    for name in names:
        p = ASSETS / name
        if p.is_file():
            return p
    return None


def load_rgba(path: Path) -> Image.Image:
    im = Image.open(path)
    if im.mode != "RGBA":
        im = im.convert("RGBA")
    return im


def to_green_phosphor(im: Image.Image) -> Image.Image:
    """Force neon-green on black, keep alpha."""
    rgba = im.convert("RGBA")
    arr = np.asarray(rgba).astype(np.float32)
    rgb = arr[..., :3]
    a = arr[..., 3:4]
    lum = 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]
    if float(lum.mean()) > 127:
        lum = 255.0 - lum
    lum = np.clip((lum - 18.0) * 1.25, 0, 255)
    out = np.zeros_like(arr)
    out[..., 0] = lum * 0.25
    out[..., 1] = lum
    out[..., 2] = lum * 0.35
    out[..., 3] = np.where(lum > 12, np.maximum(a[..., 0], lum), 0)
    return Image.fromarray(out.astype(np.uint8), "RGBA")


def fit_on_canvas(
    im: Image.Image, box: tuple[int, int, int, int], size: tuple[int, int]
) -> Image.Image:
    x0, y0, x1, y1 = box
    bw, bh = x1 - x0, y1 - y0
    layer = im.copy()
    layer.thumbnail((bw, bh), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    x = x0 + (bw - layer.width) // 2
    y = y0 + (bh - layer.height) // 2
    canvas.alpha_composite(layer, (x, y))
    return canvas


def scanlines(base: Image.Image, strength: float = 0.22) -> Image.Image:
    arr = np.asarray(base.convert("RGBA")).astype(np.float32)
    arr[::2, :, :3] *= 1.0 - strength
    return Image.fromarray(arr.astype(np.uint8), "RGBA")


def _font_candidates(kind: str) -> list[str]:
    """Bold mono/sans paths that exist on typical Fedora / nerd-font installs."""
    if kind == "mono":
        return [
            "/usr/share/fonts/liberation-mono-fonts/LiberationMono-Bold.ttf",
            "/usr/share/fonts/google-noto/NotoSansMono-Bold.ttf",
            "/usr/share/fonts/adwaita-mono-fonts/AdwaitaMono-Bold.ttf",
            "/usr/share/fonts/nerd-fonts/DejaVuSansMono/DejaVuSansMNerdFont-Bold.ttf",
            "/usr/share/fonts/nerd-fonts/LiberationMono/LiterationMonoNerdFontMono-Bold.ttf",
            "/usr/share/fonts/nerd-fonts/UbuntuMono/UbuntuMonoNerdFontMono-Bold.ttf",
            "/usr/share/fonts/nerd-fonts/JetBrainsMono/JetBrainsMonoNerdFontMono-Bold.ttf",
            "/usr/share/fonts/dejavu-sans-fonts/DejaVuSansMono-Bold.ttf",
            "/usr/share/fonts/dejavu/DejaVuSansMono-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
            "/usr/share/fonts/TTF/DejaVuSansMono-Bold.ttf",
        ]
    return [
        "/usr/share/fonts/liberation-sans-fonts/LiberationSans-Bold.ttf",
        "/usr/share/fonts/google-noto/NotoSans-Bold.ttf",
        "/usr/share/fonts/nerd-fonts/DejaVuSans/DejaVuSansNerdFont-Bold.ttf",
        "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    ]


def _truetype(px: int, kind: str) -> ImageFont.FreeTypeFont:
    last_err: Exception | None = None
    for path in _font_candidates(kind):
        if not Path(path).is_file():
            continue
        try:
            return ImageFont.truetype(path, px)
        except OSError as exc:
            last_err = exc
            continue
    # Pillow 10+ default bitmap is tiny and ignores our spacing math — fail loud.
    raise SystemExit(
        f"No bold {kind} font found for boot GIF (need Liberation/Noto/DejaVu). "
        f"Last error: {last_err}"
    )


def _mono_font(px: int) -> ImageFont.FreeTypeFont:
    return _truetype(px, "mono")


def _sans_font(px: int) -> ImageFont.FreeTypeFont:
    return _truetype(px, "sans")


def _metrics(size: tuple[int, int]) -> tuple[int, int, int, ImageFont.FreeTypeFont]:
    """Bold mono log type — readable at maximize without dominating the frame."""
    font_px = 36
    font = _mono_font(font_px)
    # Line height from real glyph metrics so spacing cannot drift from font size.
    probe = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    bbox = probe.textbbox((0, 0), "Hg", font=font)
    glyph_h = max(1, bbox[3] - bbox[1])
    line_h = glyph_h + max(6, glyph_h // 10)
    margin = max(24, int(16 * size[0] / 640))
    return font_px, line_h, margin, font


def render_boot_log(
    lines: list[str],
    size: tuple[int, int],
    *,
    font: ImageFont.ImageFont,
    line_h: int,
    margin: int,
) -> Image.Image:
    """Draw accumulated boot lines; scroll up when they exceed the text area."""
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    # Leave room at bottom for glory / crest breathing room
    text_bottom = size[1] - max(120, int(90 * size[1] / 480))
    max_rows = max(8, (text_bottom - margin) // line_h)
    visible = lines[-max_rows:]
    y = margin
    for line in visible:
        # Bold face + light stroke for extra weight on phosphor green
        draw.text(
            (margin, y),
            line,
            fill=(90, 255, 130, 255),
            font=font,
            stroke_width=1,
            stroke_fill=(20, 90, 40, 255),
        )
        y += line_h
    return canvas


def glory_frame(base: Image.Image, size: tuple[int, int]) -> Image.Image:
    arr = (np.asarray(base.convert("RGB")).astype(np.float32) * 0.35).astype(np.uint8)
    im = Image.fromarray(arr, "RGB").convert("RGBA")
    draw = ImageDraw.Draw(im)
    font_px = max(28, int(22 * size[0] / 640))
    font = _sans_font(font_px)
    gap = max(12, font_px // 3)
    total_h = font_px * len(GLORY_LINES) + gap * (len(GLORY_LINES) - 1)
    y = (size[1] - total_h) // 2
    for text in GLORY_LINES:
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        draw.text(
            ((size[0] - tw) // 2, y),
            text,
            fill=(180, 255, 200, 255),
            font=font,
        )
        y += font_px + gap
    return scanlines(im, 0.2)


def composite(size: tuple[int, int], *layers: Image.Image | None) -> Image.Image:
    out = Image.new("RGBA", size, (0, 0, 0, 255))
    for layer in layers:
        if layer is not None:
            out = Image.alpha_composite(out, layer.convert("RGBA"))
    return out


def _awake_index() -> int:
    for i, (line, _) in enumerate(BOOT_SCRIPT):
        if line == AWAKE_LINE:
            return i
    return 3


def _icon_opacity_after_awake(step: int, awake_i: int, *, full: float = 1.0) -> float:
    """Icons begin loading on the frame after MACHINE SPIRIT — AWAKE."""
    start = awake_i + 1
    if step < start:
        return 0.0
    end = start + ICON_FADE_STEPS
    if step >= end:
        return full
    return full * (step - start + 1) / ICON_FADE_STEPS


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--width", type=int, default=DEFAULT_SIZE[0])
    ap.add_argument("--height", type=int, default=DEFAULT_SIZE[1])
    ap.add_argument("--glory-ms", type=int, default=3500)
    ap.add_argument("--colors", type=int, default=96)
    ap.add_argument(
        "--timing-scale",
        type=float,
        default=1.45,
        help="Multiply all line holds (default 1.45 ≈ readable Magos boot)",
    )
    args = ap.parse_args()
    size = (args.width, args.height)
    scale = max(0.4, args.timing_scale)
    awake_i = _awake_index()

    aquila_path = _find(
        "aquila-green.jpeg",
        "aquila-vetorized.jpeg",
        "527-5277156_imperial-aquila-png-transparent-png.png",
        "imperial-aquila.png",
    )
    crest_path = _find(
        "mechanicus-logo.jpg",
        "mechanicus-logo.png",
        "images.steamusercontent.jpg",
        "mechanicus-crest-centered.png",
    )
    if not aquila_path or not crest_path:
        raise SystemExit(
            "Need Aquila + Mechanicus images under assets/ "
            f"(aquila={aquila_path}, crest={crest_path})"
        )

    crest_dest = ASSETS / "mechanicus-logo.jpg"
    if crest_path.name != crest_dest.name and crest_path.suffix.lower() in {
        ".jpg",
        ".jpeg",
    }:
        Image.open(crest_path).convert("RGB").save(crest_dest, quality=95)

    aquila = to_green_phosphor(load_rgba(aquila_path))
    crest = to_green_phosphor(load_rgba(crest_path))

    top = max(40, int(20 * size[1] / 480))
    aquila_h = max(180, int(140 * size[1] / 480))
    side = max(80, int(40 * size[0] / 640))
    crest_side = max(280, int(180 * size[0] / 640))
    crest_top = aquila_h + max(10, int(8 * size[1] / 480))
    crest_bottom = size[1] - max(80, int(50 * size[1] / 480))

    aquila_full = fit_on_canvas(aquila, (side, top, size[0] - side, aquila_h), size)
    crest_full = fit_on_canvas(
        crest, (crest_side, crest_top, size[0] - crest_side, crest_bottom), size
    )

    _, line_h, margin, font = _metrics(size)

    frames: list[Image.Image] = []
    durations: list[int] = []
    accumulated: list[str] = []

    # Brief black breath before first line
    frames.append(scanlines(composite(size), 0.22).convert("RGB"))
    durations.append(int(400 * scale))

    for step, (line, hold_ms) in enumerate(BOOT_SCRIPT):
        accumulated.append(line)
        a_op = _icon_opacity_after_awake(step, awake_i, full=0.9)
        c_op = _icon_opacity_after_awake(step, awake_i, full=1.0)

        aquila_layer = None
        if a_op > 0.01:
            arr = np.asarray(aquila_full).astype(np.float32)
            arr[..., 3] *= a_op
            aquila_layer = Image.fromarray(arr.astype(np.uint8), "RGBA")

        crest_layer = None
        if c_op > 0.01:
            arr = np.asarray(crest_full).astype(np.float32)
            arr[..., 3] *= c_op * 0.75  # keep text readable over crest
            crest_layer = ImageEnhance.Brightness(
                Image.fromarray(arr.astype(np.uint8), "RGBA")
            ).enhance(0.9 + 0.1 * ((step % 2)))

        log = render_boot_log(
            accumulated, size, font=font, line_h=line_h, margin=margin
        )
        frame = composite(size, aquila_layer, crest_layer, log)
        frames.append(scanlines(frame, 0.2).convert("RGB"))
        durations.append(max(80, int(hold_ms * scale)))

    # Final stable frame with full log + icons, then glory
    final_log = render_boot_log(
        accumulated, size, font=font, line_h=line_h, margin=margin
    )
    final = composite(size, aquila_full, crest_full, final_log)
    frames.append(scanlines(final, 0.2).convert("RGB"))
    durations.append(int(800 * scale))

    glory = glory_frame(final, size)
    frames.append(glory.convert("RGB"))
    durations.append(int(args.glory_ms * scale))

    colors = max(32, min(256, args.colors))
    q = [
        im.convert("P", palette=Image.Palette.ADAPTIVE, colors=colors) for im in frames
    ]
    q[0].save(
        OUT,
        save_all=True,
        append_images=q[1:],
        duration=durations,
        loop=1,
        optimize=True,
        disposal=2,
    )
    total_s = sum(durations) / 1000.0
    print(f"Aquila: {aquila_path.name}")
    print(f"Crest:  {crest_path.name}")
    print(f"Size:   {size[0]}×{size[1]}")
    print(
        f"Wrote {OUT} ({OUT.stat().st_size / 1024:.0f} KiB, "
        f"{len(q)} frames, {total_s:.1f}s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
