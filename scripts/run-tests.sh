#!/usr/bin/env bash
# Run automated checks that do not require a connected printer.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "=== i9950 driver automated tests (no hardware) ==="

make test
make -C . all

test -x build/i9950-printer-app
test -x build/i9950-tool

./build/i9950-tool --dry-run list || true
./build/i9950-tool --dry-run nozzle-check

if system_profiler SPUSBDataType 2>/dev/null | grep -qi "9950"; then
  echo "[INFO] Printer detected — run physical test matrix manually."
else
  echo "[SKIP] No Canon i9950 on USB — physical print tests deferred."
fi

echo "=== automated tests passed ==="
