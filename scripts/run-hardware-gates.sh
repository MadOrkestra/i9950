#!/usr/bin/env bash
# Print T04/T07 hardware gate fixtures (requires USB i9950 + running server).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
APP="${APP:-./build/i9950-printer-app}"
DEVICE="${DEVICE:-Canon i9950 (USB)}"

die() { echo "error: $*" >&2; exit 1; }

test -x "$APP" || die "build i9950-printer-app first (make all)"

if ! "$ROOT/build/i9950-tool" list 2>/dev/null | grep -q "04a9:1090"; then
  die "Canon i9950 (04A9:1090) not on USB"
fi

GATE="${1:-all}"

run_t04_600() {
  test -f build/t-photo-4x6-600.jpg || die "run: make fixtures-photo"
  echo "=== T04a: 4x6 borderless color @ 600 dpi (geometry probe) ==="
  "$APP" submit -d "$DEVICE" \
    -o media=na_index-4x6_4x6in \
    -o media-type=photographic-glossy \
    -o print-color-mode=color \
    -o printer-resolution=600dpi \
    -o media-left-margin=0 \
    -o media-right-margin=0 \
    -o media-top-margin=0 \
    -o media-bottom-margin=0 \
    build/t-photo-4x6-600.jpg
}

run_t04_2400() {
  test -f build/t-photo-4x6-2400.jpg || die "run: make fixtures-photo"
  echo "=== T04: 4x6 borderless color @ 2400 dpi (v1.0 criterion) ==="
  echo "Note: driver still encodes GP 600 dpi draft modes; 2400 raster is downscaled."
  "$APP" submit -d "$DEVICE" \
    -o media=na_index-4x6_4x6in \
    -o media-type=photographic-glossy \
    -o print-color-mode=color \
    -o printer-resolution=2400dpi \
    -o media-left-margin=0 \
    -o media-right-margin=0 \
    -o media-top-margin=0 \
    -o media-bottom-margin=0 \
    build/t-photo-4x6-2400.jpg
}

run_t07_600() {
  test -f build/t-a3plus-600.jpg || die "run: make fixtures-photo"
  echo "=== T07a: 13x19 color @ 600 dpi (geometry probe) ==="
  "$APP" submit -d "$DEVICE" \
    -o media=custom_max_13x19in \
    -o media-type=photographic-glossy \
    -o print-color-mode=color \
    -o printer-resolution=600dpi \
    build/t-a3plus-600.jpg
}

case "$GATE" in
  t04a) run_t04_600 ;;
  t04)  run_t04_2400 ;;
  t07a) run_t07_600 ;;
  all)
    run_t04_600
    run_t07_600
    echo
    echo "T04 @ 2400 dpi: ./scripts/run-hardware-gates.sh t04 (after T04a PASS)"
    ;;
  *)
    echo "Usage: $0 [t04a|t04|t07a|all]" >&2
    exit 1
    ;;
esac
