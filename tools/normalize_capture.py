#!/usr/bin/env python3
"""Normalize USB capture binaries for diffing (strip SetTime timestamps)."""

from __future__ import annotations

import re
import sys
from pathlib import Path


def normalize(data: bytes) -> bytes:
    # BJL SetTime=YYYYMMDDHHmmss
    data = re.sub(
        rb"SetTime=\d{14}",
        b"SetTime=00000000000000",
        data,
    )
    # ESC [ K blocks may include variable length prefixes — keep structure
    return data


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <capture.bin>", file=sys.stderr)
        return 1

    src = Path(sys.argv[1])
    if not src.is_file():
        print(f"Error: {src} not found", file=sys.stderr)
        return 1

    raw = src.read_bytes()
    norm = normalize(raw)
    out = src.with_suffix(src.suffix + ".norm")
    out.write_bytes(norm)
    print(f"Wrote {out} ({len(norm)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
