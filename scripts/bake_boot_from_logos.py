#!/usr/bin/env python3
"""Compose a Mechanicus-style boot GIF from Aquila + crest stills.

Uses:
  assets/aquila-green.jpeg          (or aquila-vetorized / transparent aquila)
  assets/mechanicus-logo.jpg        (or images.steamusercontent.jpg)

Output:
  assets/cogitator-boot.gif

Default canvas matches a maximized 1080p window so the splash stays sharp.
Lines type in character-by-character; icons ease in smoothly after Machine Spirit awake.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
OUT = ASSETS / "cogitator-boot.gif"

DEFAULT_SIZE = (1920, 1080)

# (line, hold_ms) — pause after the line finishes typing, before the next begins.
BOOT_SCRIPT: list[tuple[str, int]] = [
    ("++ BIOLOGIS COGITATOR // MAGOS-CLASS ALTAR", 700),
    ("++++++++", 200),
    ("++ INITIALIZING MACHINE SPIRIT AWAKEN PROTOCOL", 900),
    ("++ MACHINE SPIRIT - AWAKE", 500),
    ("+++++++++++++++++++++++++++++++++++++++++++++++", 280),
    ("++ RECITING LITANY OF IGNITION", 450),
    ("++++ 01001101 01000001 01000011 01001000 01001001 01001110 01000101", 350),
    ("++++ 01010011 01010000 01001001 01010010 01001001 01010100 00101110", 350),
    ("++ LITANY OF IGNITION RECITED", 500),
    ("++ INVOKE THE MOTIVE FORCE", 400),
    ("++ MOTIVE FORCE ANSWERS IN THE NOOSPHERE", 500),
    ("++ AUTHORISATION: MAGOS BIOLOGIS", 550),
    ("++ BY THE OMNISSIAH'S WILL - PROCEED", 550),
    ("++ GENE-VAULT UNSEALED IN HIS NAME", 450),
    ("++ COMPILING THE SPECIES MESH", 450),
    ("++ MOTIVE FORCE STABLE ACROSS ALL LOOMS", 500),
    ("++ RITE CHANNEL OPEN", 450),
    ("++ AWAITING THE MAGOS' COMMAND", 700),
]

AWAKE_LINE = "++ MACHINE SPIRIT - AWAKE"

# Smooth icon reveal (ms of wall-clock in the animation timeline).
ICON_FADE_MS = 1400
ICON_TICK_MS = 55

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


def scanlines(base: Image.Image, strength: float = 0.18) -> Image.Image:
    arr = np.asarray(base.convert("RGBA")).astype(np.float32)
    arr[::2, :, :3] *= 1.0 - strength
    return Image.fromarray(arr.astype(np.uint8), "RGBA")


def _font_candidates(kind: str) -> list[str]:
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
    raise SystemExit(
        f"No bold {kind} font found for boot GIF (need Liberation/Noto/DejaVu). "
        f"Last error: {last_err}"
    )


def _mono_font(px: int) -> ImageFont.FreeTypeFont:
    return _truetype(px, "mono")


def _sans_font(px: int) -> ImageFont.FreeTypeFont:
    return _truetype(px, "sans")


def _metrics(size: tuple[int, int]) -> tuple[int, int, int, ImageFont.FreeTypeFont]:
    font_px = 28
    font = _mono_font(font_px)
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
    cursor: bool = False,
) -> Image.Image:
    """Draw accumulated boot lines; scroll up when they exceed the text area."""
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    text_bottom = size[1] - max(120, int(90 * size[1] / 480))
    max_rows = max(8, (text_bottom - margin) // line_h)
    visible = lines[-max_rows:]
    y = margin
    for i, line in enumerate(visible):
        draw.text(
            (margin, y),
            line,
            fill=(90, 255, 130, 255),
            font=font,
            stroke_width=1,
            stroke_fill=(20, 90, 40, 255),
        )
        # Blinking block cursor on the active (last) line while typing.
        if cursor and i == len(visible) - 1:
            bbox = draw.textbbox((margin, y), line, font=font)
            cx = bbox[2] + 2
            draw.rectangle(
                [cx, y + 2, cx + max(8, line_h // 2), y + line_h - 4],
                fill=(90, 255, 130, 220),
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
    return scanlines(im, 0.18)


def composite(size: tuple[int, int], *layers: Image.Image | None) -> Image.Image:
    out = Image.new("RGBA", size, (0, 0, 0, 255))
    for layer in layers:
        if layer is not None:
            out = Image.alpha_composite(out, layer.convert("RGBA"))
    return out


def _smoothstep(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def _type_chunk_size(line: str) -> int:
    """Glyphs per typing frame — fewer frames, still reads as typed."""
    stripped = line.replace(" ", "")
    if stripped and set(stripped) <= {"+"}:
        return max(8, len(line) // 3)
    if line.startswith("++++ "):
        return 8
    # Aim for ~8 reveal steps on a typical status line.
    return max(3, (len(line) + 7) // 8)


def _with_alpha(layer: Image.Image, opacity: float) -> Image.Image | None:
    if opacity <= 0.01:
        return None
    if opacity >= 0.999:
        return layer
    arr = np.asarray(layer).astype(np.float32)
    arr[..., 3] *= opacity
    return Image.fromarray(arr.astype(np.uint8), "RGBA")


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
        help="Multiply holds / typing cadence (default 1.45)",
    )
    ap.add_argument(
        "--type-ms",
        type=int,
        default=32,
        help="Milliseconds per typing chunk (before timing-scale)",
    )
    args = ap.parse_args()
    size = (args.width, args.height)
    scale = max(0.4, args.timing_scale)
    type_ms = max(12, int(args.type_ms * scale))
    fade_ms = int(ICON_FADE_MS * scale)
    tick_ms = max(30, int(ICON_TICK_MS * min(scale, 1.2)))

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
    elapsed_ms = 0
    icon_fade_start: int | None = None

    def icon_opacity(at_ms: int) -> float:
        if icon_fade_start is None:
            return 0.0
        return _smoothstep((at_ms - icon_fade_start) / fade_ms)

    def push(
        lines: list[str],
        duration_ms: int,
        *,
        typing: bool = False,
        scan: float = 0.14,
    ) -> None:
        nonlocal elapsed_ms
        remaining = max(20, int(duration_ms))
        while remaining > 0:
            op = icon_opacity(elapsed_ms)
            # While icons are mid-fade, emit short ticks so the ease looks fluid.
            fading = icon_fade_start is not None and 0.0 < op < 0.999
            dt = min(remaining, tick_ms if fading else remaining)
            aquila_layer = _with_alpha(aquila_full, op * 0.9)
            crest_layer = _with_alpha(crest_full, op * 0.72)
            log = render_boot_log(
                lines,
                size,
                font=font,
                line_h=line_h,
                margin=margin,
                cursor=typing,
            )
            frame = composite(size, aquila_layer, crest_layer, log)
            frames.append(scanlines(frame, scan).convert("RGB"))
            durations.append(dt)
            elapsed_ms += dt
            remaining -= dt

    # Black breath
    push([], int(350 * scale), typing=False, scan=0.2)

    completed: list[str] = []
    for line, hold_ms in BOOT_SCRIPT:
        chunk = _type_chunk_size(line)
        for end in range(chunk, len(line) + chunk, chunk):
            partial = line[: min(end, len(line))]
            push(completed + [partial], type_ms, typing=True)
            if end >= len(line):
                break
        completed.append(line)
        if line == AWAKE_LINE:
            icon_fade_start = elapsed_ms
        push(completed, int(hold_ms * scale), typing=False)

    # Settle, then glory
    push(completed, int(700 * scale), typing=False, scan=0.16)
    final = composite(
        size,
        _with_alpha(aquila_full, 0.9),
        _with_alpha(crest_full, 0.72),
        render_boot_log(
            completed, size, font=font, line_h=line_h, margin=margin, cursor=False
        ),
    )
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
