#!/usr/bin/env python3
"""Color-swatch gate: mono printable baseline + 20×20 mm ink squares.

Baseline matches scripts/generate_printable_gate.py (5 mm frame, corner
L-marks + TL/TR/BL/BR, multi-size Arial pt text). Then adds eight 20×20 mm
RGB swatches for the i9950 ink set.

Requires Pillow:
  build/.venv-fixtures/bin/python scripts/generate_color_swatches_gate.py
"""

from __future__ import annotations

import struct
import zlib
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build"

DPI = 600
W = 4960
H = 7016

MARGIN_MM = 5.0
MARGIN = int(round(MARGIN_MM / 25.4 * DPI))  # 118 px
FRAME_THICK = 8
CORNER_INSET_MM = 1.0
CORNER_INSET = int(round(CORNER_INSET_MM / 25.4 * DPI))  # 24 px
CORNER_ARM = 180
CORNER_THICK = 10

SQUARE_MM = 20.0
SQUARE = int(round(SQUARE_MM / 25.4 * DPI))  # 472 px
GAP_MM = 8.0
GAP = int(round(GAP_MM / 25.4 * DPI))

SCALE_MM = 30.0
SCALE = int(round(SCALE_MM / 25.4 * DPI))  # 709 px

ARIAL = Path("/System/Library/Fonts/Supplemental/Arial.ttf")
ARIAL_BOLD = Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf")

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# (label, RGB) — i9950 / pappl supply set
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


def load_font(size_pt: float, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = ARIAL_BOLD if bold and ARIAL_BOLD.is_file() else ARIAL
    if not path.is_file():
        raise FileNotFoundError(f"Arial not found at {path}")
    return ImageFont.truetype(str(path), pt_to_px(size_pt))


def draw_scale_check(
    draw: ImageDraw.ImageDraw, x: int, y: int, ink: tuple[int, int, int] = BLACK
) -> None:
    """Axis-aligned square with a perfect inscribed circle — X/Y scale probe."""
    x1, y1 = x + SCALE - 1, y + SCALE - 1
    draw.rectangle([x, y, x1, y1], outline=ink, width=4)
    draw.ellipse([x, y, x1, y1], outline=ink, width=4)
    mid_x = x + SCALE // 2
    mid_y = y + SCALE // 2
    draw.line([mid_x, y, mid_x, y1], fill=ink, width=2)
    draw.line([x, mid_y, x1, mid_y], fill=ink, width=2)
    font = load_font(9, bold=True)
    draw.text((x, y1 + pt_to_px(2)), f"SCALE {SCALE_MM:.0f}mm sq+circle", font=font, fill=ink)


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
    hy = y if not bottom else y - thick + 1
    draw.rectangle([hx0, hy, hx1, hy + thick - 1], fill=BLACK)
    vx = x if not right else x - thick + 1
    vy0, vy1 = min(y, y1), max(y, y1)
    draw.rectangle([vx, vy0, vx + thick - 1, vy1], fill=BLACK)


def render_page(page_num: int = 1, page_count: int = 1) -> Image.Image:
    """Mono printable baseline (RGB black) + color swatches below the type."""
    img = Image.new("RGB", (W, H), WHITE)
    draw = ImageDraw.Draw(img)

    x0, y0 = MARGIN, MARGIN
    x1, y1 = W - 1 - MARGIN, H - 1 - MARGIN
    # Keep the full stroke inside the 5 mm margin: Pillow centers outlines on
    # the path (half the width would otherwise sit in the clipped margin),
    # plus 1 mm safety for right-edge registration clip seen on color prints.
    safe = int(round(1.0 / 25.4 * DPI))  # 24 px
    o = FRAME_THICK // 2
    draw.rectangle(
        [x0 + safe + o, y0 + safe + o, x1 - safe - o, y1 - safe - o],
        outline=BLACK,
        width=FRAME_THICK,
    )

    cx0 = MARGIN + safe + FRAME_THICK + CORNER_INSET
    cy0 = MARGIN + safe + FRAME_THICK + CORNER_INSET
    cx1 = (W - 1 - MARGIN - safe - FRAME_THICK) - CORNER_INSET
    cy1 = (H - 1 - MARGIN - safe - FRAME_THICK) - CORNER_INSET

    draw_corner_l(draw, cx0, cy0, False, False)
    draw_corner_l(draw, cx1, cy0, True, False)
    draw_corner_l(draw, cx0, cy1, False, True)
    draw_corner_l(draw, cx1, cy1, True, True)

    label_font = load_font(10, bold=True)
    pad = 14
    draw.text((cx0 + CORNER_THICK + pad, cy0 + CORNER_THICK + pad), "TL", font=label_font, fill=BLACK)
    tr_bbox = draw.textbbox((0, 0), "TR", font=label_font)
    tr_w = tr_bbox[2] - tr_bbox[0]
    draw.text((cx1 - CORNER_THICK - pad - tr_w, cy0 + CORNER_THICK + pad), "TR", font=label_font, fill=BLACK)
    bl_bbox = draw.textbbox((0, 0), "BL", font=label_font)
    bl_h = bl_bbox[3] - bl_bbox[1]
    draw.text((cx0 + CORNER_THICK + pad, cy1 - CORNER_THICK - pad - bl_h), "BL", font=label_font, fill=BLACK)
    br_bbox = draw.textbbox((0, 0), "BR", font=label_font)
    br_w = br_bbox[2] - br_bbox[0]
    br_h = br_bbox[3] - br_bbox[1]
    draw.text((cx1 - CORNER_THICK - pad - br_w, cy1 - CORNER_THICK - pad - br_h), "BR", font=label_font, fill=BLACK)

    page_label = f"PAGE {page_num} OF {page_count}"
    lines = [
        (18, True, "T-COLOR-SWATCHES-A4-600"),
        (14, True, page_label),
        (12, False, "Printable frame = driver 5 mm margin"),
        (12, False, "Corner L-marks 1 mm inside frame"),
        (11, False, "ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
        (11, False, "abcdefghijklmnopqrstuvwxyz"),
        (11, False, "0123456789"),
        (8, False, "8 pt: The quick brown fox jumps over the lazy dog"),
        (10, False, "10 pt: Sharpness check"),
        (14, False, "14 pt: Large"),
        (18, True, "18 pt"),
        (24, True, "24 pt"),
        (12, True, f"Color squares {SQUARE_MM:.0f}x{SQUARE_MM:.0f} mm (8 inks, RGB approx)"),
    ]
    tx = cx0 + CORNER_ARM + 40
    ty = cy0 + CORNER_ARM + 40
    for size_pt, bold, text in lines:
        font = load_font(size_pt, bold=bold)
        draw.text((tx, ty), text, font=font, fill=BLACK)
        bbox = draw.textbbox((tx, ty), text, font=font)
        ty = bbox[3] + max(pt_to_px(2), pt_to_px(size_pt) // 4)

    # Aspect probe on the right (same as mono fixture)
    sx = cx1 - CORNER_ARM - SCALE - 20
    sy = cy0 + CORNER_ARM + 40
    draw_scale_check(draw, sx, sy, ink=BLACK)

    # Color swatches below type block
    ty += pt_to_px(6)
    cols = 4
    label_h = pt_to_px(14)
    cell_w = SQUARE + GAP
    cell_h = SQUARE + label_h + GAP
    swatch_label = load_font(9, bold=True)
    for i, (name, rgb) in enumerate(SWATCHES):
        col = i % cols
        row = i // cols
        x = tx + col * cell_w
        y = ty + row * cell_h
        # Keep inside frame
        assert x + SQUARE < cx1 - 10, f"swatch {name} overflows right"
        assert y + SQUARE + label_h < cy1 - CORNER_ARM - 40, f"swatch {name} overflows bottom"
        draw.rectangle(
            [x, y, x + SQUARE - 1, y + SQUARE - 1],
            fill=rgb,
            outline=BLACK,
            width=2,
        )
        draw.text((x, y + SQUARE + pt_to_px(2)), name, font=swatch_label, fill=BLACK)

    foot = load_font(10, bold=True)
    fb = draw.textbbox((0, 0), page_label, font=foot)
    fw, fh = fb[2] - fb[0], fb[3] - fb[1]
    draw.text(((W - fw) // 2, cy1 - CORNER_ARM - fh - 20), page_label, font=foot, fill=BLACK)

    return img


def write_png(path: Path, img: Image.Image) -> None:
    assert img.mode == "RGB" and img.size == (W, H)
    raw_rgb = img.tobytes()

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ppm = int(round(DPI / 0.0254))
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    raw = bytearray()
    row_bytes = W * 3
    for y in range(H):
        raw.append(0)
        raw.extend(raw_rgb[y * row_bytes : (y + 1) * row_bytes])
    phys = struct.pack(">IIB", ppm, ppm, 1)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"pHYs", phys)
        + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + chunk(b"IEND", b"")
    )


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
            data[i + 10 : i + 12] = (DPI).to_bytes(2, "big")
            data[i + 12 : i + 14] = (DPI).to_bytes(2, "big")
            path.write_bytes(data)
            return
        i += 2 + seglen


def write_jpeg(path: Path, img: Image.Image) -> None:
    img.save(path, "JPEG", quality=95, dpi=(DPI, DPI), subsampling=0)
    _patch_jfif_dpi(path)


def write_pdf(path: Path, img: Image.Image) -> None:
    """Single-page A4 PDF embedding RGB raster (CUPS color PDF gate)."""
    assert img.mode == "RGB" and img.size == (W, H)
    pw, ph = 595.27, 841.89
    compressed = zlib.compress(img.tobytes(), 9)
    content = f"q\n{pw:.2f} 0 0 {ph:.2f} 0 0 cm\n/Im0 Do\nQ\n".encode()
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>\n",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>\n",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595.27 841.89] "
        b"/Contents 4 0 R /Resources << /XObject << /Im0 5 0 R >> >> >>\n",
        f"<< /Length {len(content)} >>\nstream\n".encode() + content + b"endstream\n",
        (
            f"<< /Type /XObject /Subtype /Image /Width {W} /Height {H} "
            f"/ColorSpace /DeviceRGB /BitsPerComponent 8 "
            f"/Filter /FlateDecode /Length {len(compressed)} >>\n"
            f"stream\n"
        ).encode()
        + compressed
        + b"\nendstream\n",
    ]
    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offs = [0]
    for i, body in enumerate(objs, 1):
        offs.append(len(out))
        out += f"{i} 0 obj\n".encode() + body + b"endobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n".encode()
    out += b"0000000000 65535 f \n"
    for off in offs[1:]:
        out += f"{off:010d} 00000 n \n".encode()
    out += (
        f"trailer << /Size {len(objs) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref}\n%%EOF\n"
    ).encode()
    path.write_bytes(out)


def self_check(img: Image.Image) -> None:
    assert MARGIN == 118
    assert SQUARE == 472
    px = img.load()
    assert px[0, 0] == WHITE
    safe = int(round(1.0 / 25.4 * DPI))
    o = FRAME_THICK // 2
    assert px[MARGIN + safe + o, MARGIN + safe + o] == BLACK, "frame corner must be black"
    assert px[W // 2, MARGIN + safe + o] == BLACK, "frame top center must be black"
    assert px[MARGIN - 1, H // 2] == WHITE, "outside left margin must be white"
    assert px[W - MARGIN, H // 2] == WHITE, "outside right margin must be white"
    cx = MARGIN + safe + FRAME_THICK + CORNER_INSET
    cy = MARGIN + safe + FRAME_THICK + CORNER_INSET
    assert px[cx, cy] == BLACK, "corner mark must be black"
    # Cyan swatch exists somewhere (pure-ish cyan)
    found_cyan = False
    for y in range(H // 3, H - MARGIN):
        for x in range(MARGIN, W - MARGIN):
            r, g, b = px[x, y]
            if r < 40 and g > 200 and b > 200:
                found_cyan = True
                break
        if found_cyan:
            break
    assert found_cyan, "cyan swatch not found"


def main() -> int:
    if not ARIAL.is_file():
        raise SystemExit(f"Arial not found: {ARIAL}")

    BUILD.mkdir(parents=True, exist_ok=True)
    page = render_page(1, 1)
    self_check(page)

    png = BUILD / "t-color-swatches-a4-600.png"
    jpg = BUILD / "t-color-swatches-a4-600.jpg"
    pdf = BUILD / "t-color-swatches-a4-600.pdf"
    write_png(png, page)
    write_jpeg(jpg, page)
    write_pdf(pdf, page)

    print(f"MARGIN={MARGIN}px frame+corners+type baseline; SQUARE={SQUARE}px ({SQUARE_MM}mm)")
    print(f"swatches={len(SWATCHES)}: " + ", ".join(n for n, _ in SWATCHES))
    print(f"{png} ({png.stat().st_size} bytes)")
    print(f"{jpg} ({jpg.stat().st_size} bytes)")
    print(f"{pdf} ({pdf.stat().st_size} bytes)")
    print("self-check OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
