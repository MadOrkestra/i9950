#!/usr/bin/env python3
"""Render Lucide printer icon as macOS menu-bar template PNG.

Black strokes on transparent background @ 36×36 px (18 pt @2x).
Output: build/share/i9950/lucide-printer-template.png
Also refreshes: assets/icons/lucide-printer-template.png
"""

from __future__ import annotations

import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SVG = ROOT / "assets/icons/lucide-printer.svg"
BUNDLED = ROOT / "assets/icons/lucide-printer-template.png"
OUT = ROOT / "build/share/i9950/lucide-printer-template.png"
SIZE = 36


def write_png(path: Path, width: int, height: int, rgba: bytes) -> None:
    def chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    raw = bytearray()
    row = width * 4
    for y in range(height):
        raw.append(0)
        raw.extend(rgba[y * row : (y + 1) * row])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + chunk(b"IEND", b"")
    )


def _plot(buf: bytearray, w: int, h: int, x: int, y: int) -> None:
    if 0 <= x < w and 0 <= y < h:
        i = (y * w + x) * 4
        buf[i : i + 4] = b"\x00\x00\x00\xff"


def _thick(buf: bytearray, w: int, h: int, x: int, y: int, t: int) -> None:
    for dy in range(-t, t + 1):
        for dx in range(-t, t + 1):
            if dx * dx + dy * dy <= t * t + t:
                _plot(buf, w, h, x + dx, y + dy)


def _line(buf: bytearray, w: int, h: int, x0: int, y0: int, x1: int, y1: int, t: int) -> None:
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    x, y = x0, y0
    while True:
        _thick(buf, w, h, x, y, t)
        if x == x1 and y == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x += sx
        if e2 <= dx:
            err += dx
            y += sy


def _rect(buf: bytearray, w: int, h: int, x0: int, y0: int, x1: int, y1: int, t: int) -> None:
    _line(buf, w, h, x0, y0, x1, y0, t)
    _line(buf, w, h, x1, y0, x1, y1, t)
    _line(buf, w, h, x1, y1, x0, y1, t)
    _line(buf, w, h, x0, y1, x0, y0, t)


def render_lucide_printer() -> bytes:
    """Lucide 'printer' paths scaled from 24×24 → 36×36."""
    w = h = SIZE
    buf = bytearray(w * h * 4)
    s = SIZE / 24.0
    t = max(1, int(round(1.1 * s)))  # ~2 px stroke at 36

    def p(x: float, y: float) -> tuple[int, int]:
        return (int(round(x * s)), int(round(y * s)))

    # Paper tray: M6 9 V3 h10 v6  → open bottom rectangle
    x0, y0 = p(6, 3)
    x1, y1 = p(17, 9)
    _line(buf, w, h, x0, y0, x1, y0, t)
    _line(buf, w, h, x0, y0, x0, y1, t)
    _line(buf, w, h, x1, y0, x1, y1, t)

    # Body top + sides: y≈11..16, x=2..22
    bx0, by = p(2, 11)
    bx1, by2 = p(22, 16)
    _line(buf, w, h, bx0, by, bx1, by, t)
    _line(buf, w, h, bx0, by, bx0, by2, t)
    _line(buf, w, h, bx1, by, bx1, by2, t)
    _line(buf, w, h, bx0, by2, bx1, by2, t)

    # Output tray: rect 6,14 12×8
    ox0, oy0 = p(6, 14)
    ox1, oy1 = p(17, 21)
    _rect(buf, w, h, ox0, oy0, ox1, oy1, t)

    return bytes(buf)


def main() -> int:
    if not SVG.is_file():
        raise SystemExit(f"missing {SVG}")
    rgba = render_lucide_printer()
    write_png(OUT, SIZE, SIZE, rgba)
    write_png(BUNDLED, SIZE, SIZE, rgba)
    print(f"{OUT} ({OUT.stat().st_size} bytes) lucide template")
    print(f"{BUNDLED} ({BUNDLED.stat().st_size} bytes) lucide template")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
