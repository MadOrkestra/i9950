#!/usr/bin/env python3
"""Generate low-ink black-only diagnostic fixtures for i9950 hardware tests.

Design goals
------------
- Exercise the full printable area (edges, corners, center, diagonals).
- Cover geometry types the driver/printer must handle: borders, hairlines,
  circles, diagonals, text, and small halftone/raster patches.
- Keep page coverage tiny (target well under 5%). Never flood with solid ink.

Outputs (under build/):
  t-diag-a4-mono.jpg          Single-page area/geometry diagnostic
  t05-a4-mono-sparse.jpg      Alias used by the test matrix
  t08-2page-mono-sparse.pdf   2-page flush smoke (vector outlines)
  t08-10page-mono-sparse.pdf  10-page flush (vector outlines)
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build"

# A4 @ 150 dpi — enough for geometry checks; PAPPL scales up.
W, H = 1240, 1754
MARGIN = 48  # ~8 mm


def _set(buf: bytearray, w: int, x: int, y: int, v: int = 0) -> None:
    if 0 <= x < w and 0 <= y < (len(buf) // w):
        buf[y * w + x] = v


def hline(buf: bytearray, w: int, y: int, x0: int, x1: int, v: int = 0) -> None:
    if not (0 <= y < len(buf) // w):
        return
    if x0 > x1:
        x0, x1 = x1, x0
    row = y * w
    for x in range(max(0, x0), min(w, x1 + 1)):
        buf[row + x] = v


def vline(buf: bytearray, w: int, x: int, y0: int, y1: int, v: int = 0) -> None:
    h = len(buf) // w
    if not (0 <= x < w):
        return
    if y0 > y1:
        y0, y1 = y1, y0
    for y in range(max(0, y0), min(h, y1 + 1)):
        buf[y * w + x] = v


def rect(buf: bytearray, w: int, x0: int, y0: int, x1: int, y1: int, v: int = 0) -> None:
    hline(buf, w, y0, x0, x1, v)
    hline(buf, w, y1, x0, x1, v)
    vline(buf, w, x0, y0, y1, v)
    vline(buf, w, x1, y0, y1, v)


def circle(buf: bytearray, w: int, cx: int, cy: int, r: int, v: int = 0) -> None:
    x, y, d = r, 0, 1 - r
    while x >= y:
        for px, py in (
            (cx + x, cy + y),
            (cx + y, cy + x),
            (cx - y, cy + x),
            (cx - x, cy + y),
            (cx - x, cy - y),
            (cx - y, cy - x),
            (cx + y, cy - x),
            (cx + x, cy - y),
        ):
            _set(buf, w, px, py, v)
        y += 1
        if d < 0:
            d += 2 * y + 1
        else:
            x -= 1
            d += 2 * (y - x) + 1


def line(buf: bytearray, w: int, x0: int, y0: int, x1: int, y1: int, v: int = 0) -> None:
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    x, y = x0, y0
    while True:
        _set(buf, w, x, y, v)
        if x == x1 and y == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x += sx
        if e2 <= dx:
            err += dx
            y += sy


def checker(
    buf: bytearray,
    w: int,
    x0: int,
    y0: int,
    bw: int,
    bh: int,
    cell: int,
    duty: int,
) -> None:
    """Small halftone patch. duty=1 -> ~50%, duty=2 -> ~25%."""
    for y in range(y0, y0 + bh):
        for x in range(x0, x0 + bw):
            cx = (x - x0) // cell
            cy = (y - y0) // cell
            if (cx + cy) % (duty + 1) == 0:
                _set(buf, w, x, y, 0)


# Minimal 5x7 glyphs for labels (A-Z, 0-9, space, hyphen, percent, slash).
_FONT: dict[str, list[int]] = {
    " ": [0, 0, 0, 0, 0],
    "-": [0, 0, 0x1F, 0, 0],
    "/": [0x02, 0x04, 0x08, 0x10, 0x20],
    "%": [0x19, 0x1A, 0x04, 0x0B, 0x13],
    "0": [0x1F, 0x11, 0x11, 0x11, 0x1F],
    "1": [0, 0x11, 0x1F, 0x01, 0],
    "2": [0x17, 0x15, 0x15, 0x15, 0x1D],
    "3": [0x11, 0x15, 0x15, 0x15, 0x1F],
    "4": [0x1C, 0x04, 0x04, 0x04, 0x1F],
    "5": [0x1D, 0x15, 0x15, 0x15, 0x17],
    "6": [0x1F, 0x15, 0x15, 0x15, 0x17],
    "7": [0x10, 0x10, 0x10, 0x10, 0x1F],
    "8": [0x1F, 0x15, 0x15, 0x15, 0x1F],
    "9": [0x1D, 0x15, 0x15, 0x15, 0x1F],
    "A": [0x0F, 0x14, 0x14, 0x14, 0x0F],
    "B": [0x1F, 0x15, 0x15, 0x15, 0x0A],
    "C": [0x0E, 0x11, 0x11, 0x11, 0x0A],
    "D": [0x1F, 0x11, 0x11, 0x11, 0x0E],
    "E": [0x1F, 0x15, 0x15, 0x15, 0x11],
    "F": [0x1F, 0x14, 0x14, 0x14, 0x10],
    "G": [0x0E, 0x11, 0x15, 0x15, 0x07],
    "H": [0x1F, 0x04, 0x04, 0x04, 0x1F],
    "I": [0x11, 0x11, 0x1F, 0x11, 0x11],
    "J": [0x02, 0x01, 0x01, 0x01, 0x1E],
    "K": [0x1F, 0x04, 0x0A, 0x11, 0x11],
    "L": [0x1F, 0x01, 0x01, 0x01, 0x01],
    "M": [0x1F, 0x08, 0x04, 0x08, 0x1F],
    "N": [0x1F, 0x08, 0x04, 0x02, 0x1F],
    "O": [0x0E, 0x11, 0x11, 0x11, 0x0E],
    "P": [0x1F, 0x14, 0x14, 0x14, 0x08],
    "R": [0x1F, 0x14, 0x16, 0x15, 0x09],
    "S": [0x09, 0x15, 0x15, 0x15, 0x12],
    "T": [0x10, 0x10, 0x1F, 0x10, 0x10],
    "U": [0x1E, 0x01, 0x01, 0x01, 0x1E],
    "V": [0x1C, 0x02, 0x01, 0x02, 0x1C],
    "W": [0x1F, 0x02, 0x04, 0x02, 0x1F],
    "X": [0x11, 0x0A, 0x04, 0x0A, 0x11],
    "Y": [0x18, 0x04, 0x03, 0x04, 0x18],
    "Z": [0x13, 0x15, 0x15, 0x15, 0x19],
}


def text(buf: bytearray, w: int, x: int, y: int, s: str) -> None:
    cx = x
    for ch in s.upper():
        cols = _FONT.get(ch, [0x1F, 0x11, 0x11, 0x11, 0x1F])
        for dx, bits in enumerate(cols):
            for dy in range(7):
                if bits & (1 << (6 - dy)):
                    _set(buf, w, cx + dx, y + dy, 0)
                    _set(buf, w, cx + dx, y + dy + 1, 0)
        cx += 6


def build_diagnostic(w: int = W, h: int = H) -> bytearray:
    buf = bytearray(b"\xff" * (w * h))
    x0, y0, x1, y1 = MARGIN, MARGIN, w - MARGIN - 1, h - MARGIN - 1

    # Outer printable-area border
    rect(buf, w, x0, y0, x1, y1, 0)

    # Corner L-marks
    mark = 36
    for cx, cy, sx, sy in (
        (x0 + 8, y0 + 8, 1, 1),
        (x1 - 8, y0 + 8, -1, 1),
        (x0 + 8, y1 - 8, 1, -1),
        (x1 - 8, y1 - 8, -1, -1),
    ):
        hline(buf, w, cy, cx, cx + sx * mark, 0)
        vline(buf, w, cx, cy, cy + sy * mark, 0)

    # Sparse ~2 inch ruling grid (hairlines only — covers area without flooding)
    step = 300
    for x in range(x0 + step, x1, step):
        vline(buf, w, x, y0, y1, 0)
    for y in range(y0 + step, y1, step):
        hline(buf, w, y, x0, x1, 0)

    # Full-area diagonals
    line(buf, w, x0, y0, x1, y1, 0)
    line(buf, w, x1, y0, x0, y1, 0)

    # Concentric circle outlines at center
    cx, cy = w // 2, h // 2
    for r in (60, 120, 200):
        circle(buf, w, cx, cy, r, 0)
    hline(buf, w, cy, cx - 20, cx + 20, 0)
    vline(buf, w, cx, cy - 20, cy + 20, 0)

    # Line-weight samples (outline strokes, not fills)
    ly = y0 + 70
    lx = x0 + 80
    for thickness, dx in ((1, 0), (2, 90), (4, 180), (8, 280)):
        for t in range(thickness):
            hline(buf, w, ly + t, lx + dx, lx + dx + 70, 0)
        text(buf, w, lx + dx, ly + 14, f"{thickness}PX")

    # Tiny raster patches only (never full-page)
    checker(buf, w, x0 + 80, y1 - 140, 90, 50, cell=4, duty=1)
    text(buf, w, x0 + 80, y1 - 155, "50% RASTER")
    checker(buf, w, x0 + 200, y1 - 140, 90, 50, cell=4, duty=2)
    text(buf, w, x0 + 200, y1 - 155, "25% RASTER")
    checker(buf, w, x0 + 320, y1 - 140, 90, 50, cell=2, duty=1)
    text(buf, w, x0 + 320, y1 - 155, "FINE")

    # Thin K ramp strip (8 px tall)
    ramp_y0 = y1 - 70
    ramp_x0, ramp_x1 = x0 + 80, x1 - 80
    for y in range(ramp_y0, ramp_y0 + 8):
        for x in range(ramp_x0, ramp_x1):
            v = int(255 * (x - ramp_x0) / max(1, ramp_x1 - ramp_x0))
            _set(buf, w, x, y, v)
    text(buf, w, ramp_x0, ramp_y0 - 14, "K RAMP")

    text(buf, w, x0 + 80, y0 + 20, "I9950 MONO AREA DIAG - LOW INK")
    text(buf, w, x0 + 80, y0 + 36, "BORDER GRID CIRCLES DIAGONALS RASTERS")

    black = sum(1 for b in buf if b < 250)
    print(f"diagnostic coverage ≈ {100.0 * black / len(buf):.2f}% inked pixels")
    return buf


def write_jpeg(path: Path, buf: bytearray, w: int, h: int) -> Path:
    ppm = path.with_suffix(".ppm")
    ppm.write_bytes(f"P5\n{w} {h}\n255\n".encode() + buf)
    subprocess.check_call(
        ["sips", "-s", "format", "jpeg", str(ppm), "--out", str(path)],
        stdout=subprocess.DEVNULL,
    )
    ppm.unlink(missing_ok=True)
    return path


def write_sparse_mono_pdf(path: Path, labels: list[str]) -> Path:
    """N-page A4 PDF: border + diagonals + circle + label (no fills)."""
    objs: list[bytes] = []

    def add(body: bytes) -> int:
        objs.append(body)
        return len(objs)

    add(b"<< /Type /Catalog /Pages 2 0 R >>\n")
    n = len(labels)
    kids = " ".join(f"{3 + i} 0 R" for i in range(n))
    add(f"<< /Type /Pages /Kids [{kids}] /Count {n} >>\n".encode())
    content_start = 3 + n
    font_id = content_start + n
    for i in range(n):
        add(
            (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
                f"/Contents {content_start + i} 0 R "
                f"/Resources << /Font << /F1 {font_id} 0 R >> >> >>\n"
            ).encode()
        )
    for i, label in enumerate(labels):
        safe = label.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        # PDF "arc" is not in base PDF — use four Bezier approx for a circle.
        # Center 297,421 r=80. Cubic approx kappa = 0.55228475 * r.
        k = 44.18
        content = (
            "0.5 w\n"
            "36 36 523 770 re S\n"
            "36 36 m 559 806 l S\n"
            "559 36 m 36 806 l S\n"
            f"377 421 m 377 {421 + k:.2f} 341.18 {421 + 80} 297 {421 + 80} c\n"
            f"252.82 {421 + 80} 217 {421 + k:.2f} 217 421 c\n"
            f"217 {421 - k:.2f} 252.82 {421 - 80} 297 {421 - 80} c\n"
            f"341.18 {421 - 80} 377 {421 - k:.2f} 377 421 c S\n"
            f"BT /F1 11 Tf 50 {780 - i * 12} Td ({safe}) Tj ET\n"
        ).encode()
        add(f"<< /Length {len(content)} >>\nstream\n".encode() + content + b"endstream\n")
    add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\n")

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
    return path


def main() -> int:
    BUILD.mkdir(parents=True, exist_ok=True)

    # Remove earlier wasteful solid/color fixtures from the default set.
    for waste in (
        BUILD / "t05-letter-600-color.jpg",
        BUILD / "t05-letter-600-color.ppm",
        BUILD / "t08-10page.pdf",
    ):
        if waste.exists():
            print(f"note: leaving {waste.name} in place but do not print it")

    diag = build_diagnostic()
    primary = write_jpeg(BUILD / "t-diag-a4-mono.jpg", diag, W, H)
    alias = BUILD / "t05-a4-mono-sparse.jpg"
    alias.write_bytes(primary.read_bytes())

    files = [
        primary,
        alias,
        write_sparse_mono_pdf(
            BUILD / "t08-2page-mono-sparse.pdf",
            [
                "T08 p1/2 mono sparse flush check",
                "T08 p2/2 mono sparse last page must finish",
            ],
        ),
        write_sparse_mono_pdf(
            BUILD / "t08-10page-mono-sparse.pdf",
            [f"T08 p{i}/10 mono sparse" for i in range(1, 11)],
        ),
    ]
    for p in files:
        print(f"{p} ({p.stat().st_size} bytes)")
    print(
        "Ink policy: black/K only; outlines + tiny rasters; no full-page fills. "
        "Submit with print-color-mode=monochrome."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
