#!/usr/bin/env bash
# USB capture helper — verifies printer presence and documents capture steps.
set -euo pipefail

VID="04a9"
PID="1090"

echo "=== Canon i9950 USB Capture Helper ==="
echo

if system_profiler SPUSBDataType 2>/dev/null | grep -qi "9950\|04a9:1090\|i9950"; then
  echo "[OK] Canon i9950 appears connected (system_profiler)"
  PRINTER_PRESENT=1
else
  echo "[INFO] No i9950 detected yet — capture steps below are for when hardware arrives."
  PRINTER_PRESENT=0
fi

echo
echo "Recommended capture workflow:"
echo "  1. Use Windows VM with USB passthrough + Wireshark/USBPcap"
echo "  2. Or Linux VM with usbmon + lsusb -d ${VID}:${PID}"
echo "  3. Save to captures/canon/<scenario>.pcapng"
echo "  4. Extract: ./tools/extract_bulk_out.sh captures/canon/photo-2400.pcapng"
echo "  5. Normalize: python3 tools/normalize_capture.py captures/canon/photo-2400-out.bin"
echo
echo "See docs/06-reverse-engineering-guide.md for full instructions."
