#!/usr/bin/env python3
"""T04 gate: 4×6 borderless color photo fixtures.

Full-bleed edge bars + corner ticks verify borderless geometry.
Generates 600 dpi (geometry probe) and 2400 dpi (v1.0 criterion) JPEGs.

Requires Pillow:
  build/.venv-fixtures/bin/python scripts/generate_photo_4x6_gate.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build"

WIDTH_IN = 4.0
HEIGHT_IN = 6.0  # portrait 4×6

ARIAL = Path("/System/Library/Fonts/Supplemental/Arial.ttf")
ARIAL_BOLD = Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf")

EDGE_MM = 3.0
CORNER_ARM_MM = 8.0

SWATCHES: list[tuple[str, tuple[int, int, int]]] = [
    ("K", (0, 0, 0)),
    ("C", (0, 255, 255)),
    ("M", (255, 0, 255)),
    ("Y", (255, 255, 0)),
    ("Pc", (128, 255, 255)),
    ("Pm", (255, 128, 200)),
    ("R", (255, 0, 0)),
    ("G", (0, 180, 0)),
]


def pt_to_px(pt: float, dpi: int) -> int:
    return max(1, int(round(pt * dpi / 72.0)))


def mm_to_px(mm: float, dpi: int) -> int:
    return max(1, int(round(mm / 25.4 * dpi)))


def load_font(size_pt: float, dpi: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = ARIAL_BOLD if bold and ARIAL_BOLD.is_file() else ARIAL
    if not path.is_file():
        raise FileNotFoundError(f"Arial not found at {path}")
    return ImageFont.truetype(str(path), pt_to_px(size_pt, dpi))


def _patch_jfif_dpi(path: Path, dpi: int) -> None:
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
            data[i + 10 : i + 12] = dpi.to_bytes(2, "big")
            data[i + 12 : i + 14] = dpi.to_bytes(2, "big")
            path.write_bytes(data)
            return
        i += 2 + seglen


def write_jpeg(path: Path, img: Image.Image, dpi: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, "JPEG", quality=95, dpi=(dpi, dpi), subsampling=0)
    _patch_jfif_dpi(path, dpi)


def draw_gate(dpi: int) -> Image.Image:
    w = int(round(WIDTH_IN * dpi))
    h = int(round(HEIGHT_IN * dpi))
    edge = mm_to_px(EDGE_MM, dpi)
    arm = mm_to_px(CORNER_ARM_MM, dpi)

    img = Image.new("RGB", (w, h), (245, 245, 245))
    draw = ImageDraw.Draw(img)

    # Full-bleed edge bars (borderless bleed check)
    draw.rectangle([0, 0, w - 1, edge - 1], fill=(220, 0, 0))
    draw.rectangle([0, h - edge, w - 1, h - 1], fill=(0, 180, 220))
    draw.rectangle([0, 0, edge - 1, h - 1], fill=(220, 0, 220))
    draw.rectangle([w - edge, 0, w - 1, h - 1], fill=(240, 220, 0))

    # Corner L-marks flush with sheet edges
    thick = max(2, dpi // 300)
    for x0, y0, hx, hy in (
        (0, 0, arm, thick),
        (0, 0, thick, arm),
        (w - arm, 0, w - 1, thick),
        (0, 0, w - 1, arm),
        (0, h - thick, arm, h - 1),
        (0, h - arm, thick, h - 1),
        (w - arm, h - thick, w - 1, h - 1),
        (w - thick, h - arm, w - 1, h - 1),
    ):
        draw.rectangle([x0, y0, hx, hy], fill=(0, 0, 0))

    title = load_font(14, dpi, bold=True)
    body = load_font(10, dpi)
    draw.text(
        (edge + pt_to_px(4, dpi), edge + pt_to_px(4, dpi)),
        f"T04 4x6 BORDERLESS @ {dpi} dpi",
        font=title,
        fill=(0, 0, 0),
    )
    draw.text(
        (edge + pt_to_px(4, dpi), edge + pt_to_px(22, dpi)),
        "Edge bars must reach paper edge; corners at bleed",
        font=body,
        fill=(40, 40, 40),
    )

    # Eight ink swatches (center band)
    sw = mm_to_px(10, dpi)
    gap = mm_to_px(2, dpi)
    total_w = len(SWATCHES) * sw + (len(SWATCHES) - 1) * gap
    sx = (w - total_w) // 2
    sy = h // 2 - sw // 2
    label = load_font(7, dpi)
    for i, (name, rgb) in enumerate(SWATCHES):
        x = sx + i * (sw + gap)
        draw.rectangle([x, sy, x + sw - 1, sy + sw - 1], fill=rgb, outline=(0, 0, 0), width=2)
        tw, th = draw.textbbox((0, 0), name, font=label)[2:]
        draw.text((x + (sw - tw) // 2, sy + sw + pt_to_px(2, dpi)), name, font=label, fill=(0, 0, 0))

    return img


def main() -> int:
    for dpi in (600, 2400):
        out = BUILD / f"t-photo-4x6-{dpi}.jpg"
        img = draw_gate(dpi)
        write_jpeg(out, img, dpi)
        print(f"{out} ({out.stat().st_size // 1024} KiB) {img.size[0]}x{img.size[1]} @ {dpi} dpi")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
