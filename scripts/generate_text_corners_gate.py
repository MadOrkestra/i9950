#!/usr/bin/env python3
"""Generate white-bg text+corner gate fixtures: 600 dpi JPG/PNG + 2-page PDF.

White = 0xFF / no PDF fills. Ink only on black text and corner marks.
"""

from __future__ import annotations

import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build"

# A4 @ 600 dpi
DPI = 600
W = 4960  # round(210/25.4*600)
H = 7016  # round(297/25.4*600)
MARGIN = 72  # 0.12 in from page edge for corner marks

# 5x7 bitmap font (uppercase + digits + few punct), bits MSB left
_FONT = {
    " ": 0x00000000000000,
    "-": 0x0000000F800000,
    ":": 0x000C00000C0000,
    "0": 0x1E33333F33331E,
    "1": 0x0C1C0C0C0C0C1E,
    "2": 0x1E33060C18303F,
    "3": 0x1E330E0333331E,
    "4": 0x060E1E363F0606,
    "5": 0x3F303E0333331E,
    "6": 0x0E18303E33331E,
    "7": 0x3F03060C181818,
    "8": 0x1E33331E33331E,
    "9": 0x1E33331F030C18,
    "A": 0x1E33333F333333,
    "B": 0x3E33333E33333E,
    "C": 0x1E33303030331E,
    "D": 0x3C36333333363C,
    "E": 0x3F30303E30303F,
    "F": 0x3F30303E303030,
    "G": 0x1E33303337331E,
    "H": 0x3333333F333333,
    "I": 0x1E0C0C0C0C0C1E,
    "J": 0x0F03030333331E,
    "K": 0x33363C383C3633,
    "L": 0x3030303030303F,
    "M": 0x63337F6B636363,
    "N": 0x33333B3F373333,
    "O": 0x1E33333333331E,
    "P": 0x3E33333E303030,
    "Q": 0x1E3333333B1E03,
    "R": 0x3E33333E3C3633,
    "S": 0x1E33301E03331E,
    "T": 0x3F0C0C0C0C0C0C,
    "U": 0x3333333333331E,
    "V": 0x33333333331E0C,
    "W": 0x6363636B7F3363,
    "X": 0x33331E0C1E3333,
    "Y": 0x3333331E0C0C0C,
    "Z": 0x3F03060C18303F,
}


def _glyph(ch: str) -> int:
    return _FONT.get(ch.upper(), _FONT[" "])


def put_pixel(buf: bytearray, x: int, y: int, v: int = 0) -> None:
    if 0 <= x < W and 0 <= y < H:
        buf[y * W + x] = v


def hline(buf: bytearray, y: int, x0: int, x1: int, v: int = 0, thick: int = 1) -> None:
    for t in range(thick):
        yy = y + t
        if 0 <= yy < H:
            for x in range(max(0, x0), min(W, x1 + 1)):
                buf[yy * W + x] = v


def vline(buf: bytearray, x: int, y0: int, y1: int, v: int = 0, thick: int = 1) -> None:
    for t in range(thick):
        xx = x + t
        if 0 <= xx < W:
            for y in range(max(0, y0), min(H, y1 + 1)):
                buf[y * W + xx] = v


def draw_char(buf: bytearray, x: int, y: int, ch: str, scale: int = 4) -> None:
    bits = _glyph(ch)
    for row in range(7):
        # Glyph rows are packed in bits 4..0 of each byte (not 7..3).
        row_bits = (bits >> (48 - row * 8)) & 0xFF
        for col in range(5):
            if row_bits & (0x10 >> col):
                for dy in range(scale):
                    for dx in range(scale):
                        put_pixel(buf, x + col * scale + dx, y + row * scale + dy, 0)


def draw_text(buf: bytearray, x: int, y: int, text: str, scale: int = 4) -> None:
    cx = x
    for ch in text:
        draw_char(buf, cx, y, ch, scale)
        cx += 6 * scale


def corner_mark(buf: bytearray, x: int, y: int, right: bool, bottom: bool, arm: int = 180, thick: int = 6) -> None:
    """L-shaped mark with corner at (x,y), arms toward page center."""
    x1 = x + arm if not right else x - arm
    y1 = y + arm if not bottom else y - arm
    hline(buf, y if not bottom else y - thick + 1, min(x, x1), max(x, x1), 0, thick)
    vline(buf, x if not right else x - thick + 1, min(y, y1), max(y, y1), 0, thick)


def render_page(page_label: str) -> bytearray:
    buf = bytearray(b"\xff") * (W * H)
    # Outer rectangle via corner marks near edges
    corner_mark(buf, MARGIN, MARGIN, False, False)
    corner_mark(buf, W - 1 - MARGIN, MARGIN, True, False)
    corner_mark(buf, MARGIN, H - 1 - MARGIN, False, True)
    corner_mark(buf, W - 1 - MARGIN, H - 1 - MARGIN, True, True)

    # Full thin rectangle connecting corners (scale check)
    x0, y0 = MARGIN, MARGIN
    x1, y1 = W - 1 - MARGIN, H - 1 - MARGIN
    hline(buf, y0, x0, x1, 0, 2)
    hline(buf, y1 - 1, x0, x1, 0, 2)
    vline(buf, x0, y0, y1, 0, 2)
    vline(buf, x1 - 1, y0, y1, 0, 2)

    scale = 5
    lines = [
        "CANON I9950 TEXTONLY MONO TEST",
        "CORNER MARKERS ARE THE SCALE CHECK",
        "TL TR BL BR MUST SIT NEAR PAGE EDGES",
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
        "0123456789",
        "JOB TAG: TTEXT-CORNERS-A4-600",
        "PRINT-COLOR-MODE: MONOCHROME",
        page_label,
    ]
    ty = MARGIN + 220
    tx = MARGIN + 80
    for line in lines:
        draw_text(buf, tx, ty, line, scale)
        ty += 7 * scale + 28

    # Corner labels
    ls = 4
    draw_text(buf, MARGIN + 20, MARGIN + 20, "TL", ls)
    draw_text(buf, W - MARGIN - 6 * ls * 2 - 20, MARGIN + 20, "TR", ls)
    draw_text(buf, MARGIN + 20, H - MARGIN - 7 * ls - 20, "BL", ls)
    draw_text(buf, W - MARGIN - 6 * ls * 2 - 20, H - MARGIN - 7 * ls - 20, "BR", ls)
    return buf


def write_png(path: Path, buf: bytearray) -> None:
    """Grayscale PNG with pHYs = 600 dpi for PAPPL."""
    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ppm = int(round(DPI / 0.0254))  # pixels per meter
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 0, 0, 0, 0)  # 8-bit gray
    raw = bytearray()
    for y in range(H):
        raw.append(0)  # filter None
        raw.extend(buf[y * W : (y + 1) * W])
    phys = struct.pack(">IIB", ppm, ppm, 1)  # 1 = meter
    png = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"pHYs", phys)
        + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + chunk(b"IEND", b"")
    )
    path.write_bytes(png)


def write_jpeg_jfif(path: Path, buf: bytearray) -> None:
    """Minimal grayscale baseline JPEG with JFIF dens_unit=1 dens=600.

    Uses a trivial 1-byte-per-block approach via Pillow if present; else
    writes PPM and invokes `cjpeg`/`magick`, else embeds raw JFIF via sips
    then patches density.
    """
    try:
        from PIL import Image  # type: ignore

        img = Image.frombytes("L", (W, H), bytes(buf))
        img.save(path, "JPEG", quality=95, dpi=(DPI, DPI), subsampling=0)
        return
    except Exception:
        pass

    ppm = path.with_suffix(".ppm")
    ppm.write_bytes(f"P5\n{W} {H}\n255\n".encode() + buf)
    import subprocess

    for cmd in (
        ["cjpeg", "-grayscale", "-quality", "95", "-dpi", str(DPI), "-outfile", str(path), str(ppm)],
        ["magick", str(ppm), "-density", str(DPI), "-units", "PixelsPerInch", "-quality", "95", str(path)],
    ):
        try:
            subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            ppm.unlink(missing_ok=True)
            _patch_jfif_dpi(path)
            return
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue

    subprocess.check_call(
        ["sips", "-s", "format", "jpeg", str(ppm), "--out", str(path)],
        stdout=subprocess.DEVNULL,
    )
    ppm.unlink(missing_ok=True)
    _patch_jfif_dpi(path)


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
            data[i + 9] = 1  # units = dpi
            data[i + 10 : i + 12] = (DPI).to_bytes(2, "big")
            data[i + 12 : i + 14] = (DPI).to_bytes(2, "big")
            path.write_bytes(data)
            return
        i += 2 + seglen


def write_pdf_2page(path: Path) -> None:
    """Vector A4 2-page PDF: white (no fill), text + corner marks + rectangle."""
    pages_content: list[bytes] = []
    for p in (1, 2):
        # PDF coords: origin bottom-left. Margin 36pt (~0.5in).
        m = 36
        # Corner arm length in points
        arm = 18
        lines = [
            "CANON I9950 TEXTONLY MONO TEST",
            "CORNER MARKERS ARE THE SCALE CHECK",
            "TL TR BL BR MUST SIT NEAR PAGE EDGES",
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
            "0123456789",
            "JOB TAG: TTEXT-CORNERS-A4-600",
            "PRINT-COLOR-MODE: MONOCHROME",
            f"PAGE {p} OF 2",
        ]
        text_ops = []
        y = 842 - m - 48
        for line in lines:
            safe = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            text_ops.append(f"BT /F1 11 Tf {m + 24:.0f} {y:.0f} Td ({safe}) Tj ET")
            y -= 16

        # Rectangle + L corners
        content = (
            "0.8 w\n"
            f"{m} {m} {595 - 2 * m} {842 - 2 * m} re S\n"
            # TL
            f"{m} {842 - m} m {m + arm} {842 - m} l S\n"
            f"{m} {842 - m} m {m} {842 - m - arm} l S\n"
            # TR
            f"{595 - m} {842 - m} m {595 - m - arm} {842 - m} l S\n"
            f"{595 - m} {842 - m} m {595 - m} {842 - m - arm} l S\n"
            # BL
            f"{m} {m} m {m + arm} {m} l S\n"
            f"{m} {m} m {m} {m + arm} l S\n"
            # BR
            f"{595 - m} {m} m {595 - m - arm} {m} l S\n"
            f"{595 - m} {m} m {595 - m} {m + arm} l S\n"
            f"BT /F1 9 Tf {m + 4} {842 - m - 12} Td (TL) Tj ET\n"
            f"BT /F1 9 Tf {595 - m - 18} {842 - m - 12} Td (TR) Tj ET\n"
            f"BT /F1 9 Tf {m + 4} {m + 4} Td (BL) Tj ET\n"
            f"BT /F1 9 Tf {595 - m - 18} {m + 4} Td (BR) Tj ET\n"
            + "\n".join(text_ops)
            + "\n"
        ).encode()
        pages_content.append(content)

    objs: list[bytes] = []
    objs.append(b"<< /Type /Catalog /Pages 2 0 R >>\n")
    objs.append(b"<< /Type /Pages /Kids [3 0 R 4 0 R] /Count 2 >>\n")
    # page objs 3,4; content 5,6; font 7
    objs.append(
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
        b"/Contents 5 0 R /Resources << /Font << /F1 7 0 R >> >> >>\n"
    )
    objs.append(
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
        b"/Contents 6 0 R /Resources << /Font << /F1 7 0 R >> >> >>\n"
    )
    for c in pages_content:
        objs.append(f"<< /Length {len(c)} >>\nstream\n".encode() + c + b"endstream\n")
    objs.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\n")

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


def main() -> int:
    BUILD.mkdir(parents=True, exist_ok=True)
    page1 = render_page("PAGE 1 OF 1 JPG")
    jpg = BUILD / "t-text-a4-mono-600.jpg"
    png = BUILD / "t-text-a4-mono-600.png"
    pdf = BUILD / "t-text-a4-mono-2page.pdf"

    write_png(png, page1)
    write_jpeg_jfif(jpg, page1)
    write_pdf_2page(pdf)

    # Verify JPEG JFIF dens
    raw = jpg.read_bytes()
    jfif = raw.find(b"JFIF\x00")
    dens = None
    if jfif >= 0:
        dens = (raw[jfif + 5], int.from_bytes(raw[jfif + 6 : jfif + 8], "big"))
    print(f"{jpg} ({jpg.stat().st_size} bytes) JFIF dens={dens}")
    print(f"{png} ({png.stat().st_size} bytes) pHYs 600dpi")
    print(f"{pdf} ({pdf.stat().st_size} bytes) 2 pages")
    # Sample corners must be white
    assert page1[0] == 255 and page1[W // 2 + (H // 2) * W] == 255
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
