#!/usr/bin/env python3
"""Generate printable-area gate fixtures: A4 @ 600 dpi, mono, white bg.

Frame sits exactly on the driver's 5 mm margins (i9950 left_right/bottom_top=500).
Black stroked rectangle; corner L-marks 1 mm inside the frame with TL/TR/BL/BR
labels; multi-size Arial text. No full-page fill.

Requires Pillow:
  build/.venv-fixtures/bin/python scripts/generate_printable_gate.py
"""

from __future__ import annotations

import struct
import zlib
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build"

DPI = 600
W = 4960  # round(210/25.4*600)
H = 7016  # round(297/25.4*600)

MARGIN_MM = 5.0
MARGIN = int(round(MARGIN_MM / 25.4 * DPI))  # 118 px
FRAME_THICK = 8
CORNER_INSET_MM = 1.0
CORNER_INSET = int(round(CORNER_INSET_MM / 25.4 * DPI))  # 24 px
CORNER_ARM = 180
CORNER_THICK = 10

ARIAL = Path("/System/Library/Fonts/Supplemental/Arial.ttf")
ARIAL_BOLD = Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf")


def pt_to_px(pt: float) -> int:
    """Convert typographic points to pixels at fixture DPI (1 pt = 1/72 in)."""
    return max(1, int(round(pt * DPI / 72.0)))


def load_font(size_pt: float, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = ARIAL_BOLD if bold and ARIAL_BOLD.is_file() else ARIAL
    if not path.is_file():
        raise FileNotFoundError(f"Arial not found at {path}")
    return ImageFont.truetype(str(path), pt_to_px(size_pt))


def draw_corner_l(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    right: bool,
    bottom: bool,
    arm: int = CORNER_ARM,
    thick: int = CORNER_THICK,
) -> None:
    """L-mark with outer corner at (x,y), arms toward page center."""
    x1 = x + arm if not right else x - arm
    y1 = y + arm if not bottom else y - arm
    hx0, hx1 = min(x, x1), max(x, x1)
    hy = y if not bottom else y - thick + 1
    draw.rectangle([hx0, hy, hx1, hy + thick - 1], fill=0)
    vx = x if not right else x - thick + 1
    vy0, vy1 = min(y, y1), max(y, y1)
    draw.rectangle([vx, vy0, vx + thick - 1, vy1], fill=0)


def render_page(page_num: int = 1, page_count: int = 1) -> Image.Image:
    img = Image.new("L", (W, H), 255)
    draw = ImageDraw.Draw(img)

    x0, y0 = MARGIN, MARGIN
    x1, y1 = W - 1 - MARGIN, H - 1 - MARGIN
    draw.rectangle([x0, y0, x1, y1], outline=0, width=FRAME_THICK)

    # Corner marks 1 mm inside the inner edge of the frame
    cx0 = MARGIN + FRAME_THICK + CORNER_INSET
    cy0 = MARGIN + FRAME_THICK + CORNER_INSET
    cx1 = (W - 1 - MARGIN - FRAME_THICK) - CORNER_INSET
    cy1 = (H - 1 - MARGIN - FRAME_THICK) - CORNER_INSET

    draw_corner_l(draw, cx0, cy0, False, False)
    draw_corner_l(draw, cx1, cy0, True, False)
    draw_corner_l(draw, cx0, cy1, False, True)
    draw_corner_l(draw, cx1, cy1, True, True)

    label_font = load_font(10, bold=True)
    pad = 14
    draw.text((cx0 + CORNER_THICK + pad, cy0 + CORNER_THICK + pad), "TL", font=label_font, fill=0)
    tr_bbox = draw.textbbox((0, 0), "TR", font=label_font)
    tr_w = tr_bbox[2] - tr_bbox[0]
    draw.text((cx1 - CORNER_THICK - pad - tr_w, cy0 + CORNER_THICK + pad), "TR", font=label_font, fill=0)
    bl_bbox = draw.textbbox((0, 0), "BL", font=label_font)
    bl_h = bl_bbox[3] - bl_bbox[1]
    draw.text((cx0 + CORNER_THICK + pad, cy1 - CORNER_THICK - pad - bl_h), "BL", font=label_font, fill=0)
    br_bbox = draw.textbbox((0, 0), "BR", font=label_font)
    br_w = br_bbox[2] - br_bbox[0]
    br_h = br_bbox[3] - br_bbox[1]
    draw.text((cx1 - CORNER_THICK - pad - br_w, cy1 - CORNER_THICK - pad - br_h), "BR", font=label_font, fill=0)

    page_label = f"PAGE {page_num} OF {page_count}"
    # All sizes are typographic points (1 pt = 1/72 in), converted at DPI.
    lines = [
        (18, True, "T-PRINTABLE-A4-600"),
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
    ]
    tx = cx0 + CORNER_ARM + 40
    ty = cy0 + CORNER_ARM + 40
    for size_pt, bold, text in lines:
        font = load_font(size_pt, bold=bold)
        draw.text((tx, ty), text, font=font, fill=0)
        bbox = draw.textbbox((tx, ty), text, font=font)
        ty = bbox[3] + max(pt_to_px(2), pt_to_px(size_pt) // 4)

    # Bottom-center page indicator (clear even if body text is clipped)
    foot = load_font(10, bold=True)
    fb = draw.textbbox((0, 0), page_label, font=foot)
    fw, fh = fb[2] - fb[0], fb[3] - fb[1]
    draw.text(((W - fw) // 2, cy1 - CORNER_ARM - fh - 20), page_label, font=foot, fill=0)

    return img


def write_png(path: Path, img: Image.Image) -> None:
    buf = img.tobytes()
    assert img.mode == "L" and img.size == (W, H)

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ppm = int(round(DPI / 0.0254))
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 0, 0, 0, 0)
    raw = bytearray()
    for y in range(H):
        raw.append(0)
        raw.extend(buf[y * W : (y + 1) * W])
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


def write_pdf_pages(path: Path, pages: list[Image.Image]) -> None:
    """Multi-page A4 PDF embedding grayscale rasters (same look as PNG)."""
    assert pages, "need at least one page"
    for img in pages:
        assert img.mode == "L" and img.size == (W, H)

    pw, ph = 595.27, 841.89
    n = len(pages)
    # Object layout:
    # 1 Catalog, 2 Pages, then per page: Page, Contents, Image  => 3n + 2 objs
    kids = " ".join(f"{3 + 3 * i} 0 R" for i in range(n))
    objs: list[bytes] = [
        b"<< /Type /Catalog /Pages 2 0 R >>\n",
        f"<< /Type /Pages /Kids [{kids}] /Count {n} >>\n".encode(),
    ]

    for i, img in enumerate(pages):
        compressed = zlib.compress(img.tobytes(), 9)
        page_obj = 3 + 3 * i
        contents_obj = page_obj + 1
        image_obj = page_obj + 2
        im_name = f"Im{i}"
        content = f"q\n{pw:.2f} 0 0 {ph:.2f} 0 0 cm\n/{im_name} Do\nQ\n".encode()
        objs.append(
            (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {pw} {ph}] "
                f"/Contents {contents_obj} 0 R "
                f"/Resources << /XObject << /{im_name} {image_obj} 0 R >> >> >>\n"
            ).encode()
        )
        objs.append(
            f"<< /Length {len(content)} >>\nstream\n".encode() + content + b"endstream\n"
        )
        objs.append(
            (
                f"<< /Type /XObject /Subtype /Image /Width {W} /Height {H} "
                f"/ColorSpace /DeviceGray /BitsPerComponent 8 "
                f"/Filter /FlateDecode /Length {len(compressed)} >>\n"
                f"stream\n"
            ).encode()
            + compressed
            + b"\nendstream\n"
        )

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
    assert MARGIN == 118, f"expected 5mm inset 118px, got {MARGIN}"
    assert CORNER_INSET == 24, f"expected 1mm inset 24px, got {CORNER_INSET}"
    px = img.load()
    assert px[0, 0] == 255, "page TL must be white"
    assert px[W - 1, 0] == 255, "page TR must be white"
    assert px[0, H - 1] == 255, "page BL must be white"
    assert px[W - 1, H - 1] == 255, "page BR must be white"
    assert px[MARGIN, MARGIN] == 0, "frame corner must be black"
    assert px[W // 2, MARGIN] == 0, "frame top center must be black"
    cx = MARGIN + FRAME_THICK + CORNER_INSET
    cy = MARGIN + FRAME_THICK + CORNER_INSET
    assert px[cx, cy] == 0, f"corner mark at ({cx},{cy}) must be black"
    assert px[W // 2, H // 2] == 255, "page center must be white"


def main() -> int:
    if not ARIAL.is_file():
        raise SystemExit(f"Arial not found: {ARIAL}")

    BUILD.mkdir(parents=True, exist_ok=True)
    page1 = render_page(1, 2)
    page2 = render_page(2, 2)
    self_check(page1)
    self_check(page2)

    png = BUILD / "t-printable-a4-600.png"
    jpg = BUILD / "t-printable-a4-600.jpg"
    pdf = BUILD / "t-printable-a4-600.pdf"

    # PNG/JPG: page 1. Also emit p1/p2 PNGs (PAPPL has no PDF input).
    # PDF: both pages with PAGE N OF 2 indicators.
    write_png(png, page1)
    write_jpeg(jpg, page1)
    write_png(BUILD / "t-printable-a4-600-p1.png", page1)
    write_png(BUILD / "t-printable-a4-600-p2.png", page2)
    write_pdf_pages(pdf, [page1, page2])

    raw = jpg.read_bytes()
    jfif = raw.find(b"JFIF\x00")
    dens = None
    if jfif >= 0:
        dens = (raw[jfif + 5], int.from_bytes(raw[jfif + 6 : jfif + 8], "big"))

    print(f"MARGIN={MARGIN}px ({MARGIN_MM}mm) CORNER_INSET={CORNER_INSET}px ({CORNER_INSET_MM}mm)")
    print(f"page={W}x{H} @ {DPI}dpi font={ARIAL.name}")
    print(f"{png} ({png.stat().st_size} bytes) pHYs 600dpi (page 1)")
    print(f"{jpg} ({jpg.stat().st_size} bytes) JFIF dens={dens} (page 1)")
    print(f"{pdf} ({pdf.stat().st_size} bytes) 2 pages (raster)")
    print("self-check OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
