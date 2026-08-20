#!/usr/bin/env bash
# Extract bulk OUT payloads from a pcapng file using tshark (if available).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CAP="${1:-}"

if [[ -z "$CAP" ]]; then
  echo "Usage: $0 <capture.pcapng> [output.bin]" >&2
  exit 1
fi

OUT="${2:-${CAP%.pcapng}-out.bin}"

if ! command -v tshark >/dev/null 2>&1; then
  echo "tshark not found. Install Wireshark: brew install --cask wireshark" >&2
  exit 1
fi

# Canon i9950 bulk OUT transfers
tshark -r "$CAP" \
  -Y "usb.idVendor == 0x04a9 && usb.idProduct == 0x1090 && usb.endpoint_address.direction == 0 && usb.transfer_type == 3" \
  -T fields -e usb.capdata \
  2>/dev/null | while read -r line; do
    if [[ -n "$line" && "$line" != "(null)" ]]; then
      echo "$line" | xxd -r -p
    fi
  done > "$OUT"

echo "Extracted bulk OUT data to $OUT ($(wc -c < "$OUT") bytes)"
