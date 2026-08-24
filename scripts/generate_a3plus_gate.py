#!/usr/bin/env python3
"""T07 gate: 13×19 (A3+) color geometry fixture @ 600 dpi.

2400 dpi full-raster would exceed ~4 GB RAM; validate geometry at 600 dpi
first, then repeat at 2400 dpi once encoder maps GP photo modes.

Requires Pillow:
  build/.venv-fixtures/bin/python scripts/generate_a3plus_gate.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build"

WIDTH_IN = 13.0
HEIGHT_IN = 19.0
DPI = 600

MARGIN_MM = 5.0
FRAME_THICK = 8
CORNER_ARM = 240
CORNER_THICK = 10
CORNER_INSET_MM = 1.0
SCALE_MM = 30.0

SWATCH_MM = 18.0
GAP_MM = 6.0

ARIAL = Path("/System/Library/Fonts/Supplemental/Arial.ttf")
ARIAL_BOLD = Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf")

SWATCHES: list[tuple[str, tuple[int, int, int]]] = [
    ("Black", (0, 0, 0)),
    ("Cyan", (0, 255, 255)),
    ("Magenta", (255, 0, 255)),
    ("Yellow", (255, 255, 0)),
    ("Photo Cyan", (128, 255, 255)),
    ("Photo Magenta", (255, 128, 200)),
    ("Red", (255, 0, 0)),
    ("Green", (0, 180, 0)),
]


def pt_to_px(pt: float) -> int:
    return max(1, int(round(pt * DPI / 72.0)))


def mm_to_px(mm: float) -> int:
    return max(1, int(round(mm / 25.4 * DPI)))


def load_font(size_pt: float, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = ARIAL_BOLD if bold and ARIAL_BOLD.is_file() else ARIAL
    if not path.is_file():
        raise FileNotFoundError(f"Arial not found at {path}")
    return ImageFont.truetype(str(path), pt_to_px(size_pt))


def _patch_jfif_dpi(path: Path) -> None:
    data = bytearray(path.read_bytes())
    if data[:2] != b"\xff\xd8":
        return
    i = 2
    while i + 4 < len(data) and data[i] == 0xFF:
        marker = data[i + 1]
        if marker in (0xD9, 0xDA):
            break
        seglen = int.from_bytes(data[i + 2 : i + 4], "big")
        if marker == 0xE0 and data[i + 4 : i + 9] == b"JFIF\x00":
            data[i + 9] = 1
            data[i + 10 : i + 12] = DPI.to_bytes(2, "big")
            data[i + 12 : i + 14] = DPI.to_bytes(2, "big")
            path.write_bytes(data)
            return
        i += 2 + seglen


def write_jpeg(path: Path, img: Image.Image) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, "JPEG", quality=95, dpi=(DPI, DPI), subsampling=0)
    _patch_jfif_dpi(path)


def draw_corner_l(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    right: bool,
    bottom: bool,
    arm: int = CORNER_ARM,
    thick: int = CORNER_THICK,
) -> None:
    x1 = x + arm if not right else x - arm
    y1 = y + arm if not bottom else y - arm
    hx0, hx1 = min(x, x1), max(x, x1)
    hy0, hy1 = min(y, y1), max(y, y1)
    draw.rectangle([hx0, y, hx1, y + thick - 1], fill=(0, 0, 0))
    draw.rectangle([x, hy0, x + thick - 1, hy1], fill=(0, 0, 0))


def main() -> int:
    w = int(round(WIDTH_IN * DPI))
    h = int(round(HEIGHT_IN * DPI))
    margin = mm_to_px(MARGIN_MM)
    inset = mm_to_px(CORNER_INSET_MM)
    scale = mm_to_px(SCALE_MM)
    sw = mm_to_px(SWATCH_MM)
    gap = mm_to_px(GAP_MM)

    img = Image.new("RGB", (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    x0, y0 = margin, margin
    x1, y1 = w - margin - 1, h - margin - 1
    for t in range(FRAME_THICK):
        draw.rectangle([x0 + t, y0 + t, x1 - t, y1 - t], outline=(0, 0, 0))

    draw_corner_l(draw, x0 + inset, y0 + inset, False, False)
    draw_corner_l(draw, x1 - inset, y0 + inset, True, False)
    draw_corner_l(draw, x0 + inset, y1 - inset, False, True)
    draw_corner_l(draw, x1 - inset, y1 - inset, True, True)

    labels = load_font(11, bold=True)
    draw.text((x0 + inset + pt_to_px(4), y0 + inset + pt_to_px(4)), "TL", font=labels, fill=(0, 0, 0))
    draw.text((x1 - inset - pt_to_px(28), y0 + inset + pt_to_px(4)), "TR", font=labels, fill=(0, 0, 0))
    draw.text((x0 + inset + pt_to_px(4), y1 - inset - pt_to_px(18)), "BL", font=labels, fill=(0, 0, 0))
    draw.text((x1 - inset - pt_to_px(28), y1 - inset - pt_to_px(18)), "BR", font=labels, fill=(0, 0, 0))

    title = load_font(16, bold=True)
    body = load_font(11)
    draw.text(
        (x0 + scale + pt_to_px(8), y0 + pt_to_px(8)),
        "T07 13x19 GEOMETRY @ 600 dpi",
        font=title,
        fill=(0, 0, 0),
    )
    draw.text(
        (x0 + scale + pt_to_px(8), y0 + pt_to_px(26)),
        "Frame on 5 mm inset; swatches square; no right-edge clip",
        font=body,
        fill=(40, 40, 40),
    )

    # Scale probe
    sx, sy = x0 + inset, y0 + inset + scale + pt_to_px(12)
    draw.rectangle([sx, sy, sx + scale - 1, sy + scale - 1], outline=(0, 0, 0), width=4)
    draw.ellipse([sx, sy, sx + scale - 1, sy + scale - 1], outline=(0, 0, 0), width=4)

    # Swatch row
    row_y = y0 + (y1 - y0) // 2
    total_w = len(SWATCHES) * sw + (len(SWATCHES) - 1) * gap
    row_x = x0 + ((x1 - x0) - total_w) // 2
    cap = load_font(8)
    for i, (name, rgb) in enumerate(SWATCHES):
        x = row_x + i * (sw + gap)
        draw.rectangle([x, row_y, x + sw - 1, row_y + sw - 1], fill=rgb, outline=(0, 0, 0), width=2)
        tw = draw.textbbox((0, 0), name, font=cap)[2]
        draw.text((x + (sw - tw) // 2, row_y + sw + pt_to_px(2)), name, font=cap, fill=(0, 0, 0))

    out = BUILD / "t-a3plus-600.jpg"
    write_jpeg(out, img)
    print(f"{out} ({out.stat().st_size // 1024} KiB) {w}x{h} @ {DPI} dpi")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
