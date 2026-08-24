#!/usr/bin/env bash
# Build a local macOS installer package (unsigned — for development).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PKGROOT="$ROOT/build/pkgroot"
PKG="$ROOT/build/i9950-printer-app.pkg"
VERSION="${VERSION:-$(grep '^VERSION' "$ROOT/Makefile" | awk '{print $3}')}"
VERSION="${VERSION:-0.1.0}"

cd "$ROOT"
make clean all VERSION="$VERSION"

rm -rf "$PKGROOT"
mkdir -p "$PKGROOT/usr/local/bin"
mkdir -p "$PKGROOT/usr/local/share/i9950"
mkdir -p "$PKGROOT/Library/LaunchAgents"

install -m 755 "$ROOT/build/i9950-printer-app" "$PKGROOT/usr/local/bin/"
install -m 755 "$ROOT/build/i9950-tool" "$PKGROOT/usr/local/bin/"
install -m 644 "$ROOT/build/share/i9950/lucide-printer-template.png" \
  "$PKGROOT/usr/local/share/i9950/"
install -m 644 "$ROOT/packaging/macos/com.i9950.printer-app.plist" \
  "$PKGROOT/Library/LaunchAgents/"

pkgbuild --root "$PKGROOT" \
  --identifier com.i9950.printer-app \
  --version "${VERSION:-0.1.0}" \
  --install-location / \
  "$PKG"

echo "Built unsigned package: $PKG"
echo "Install: sudo installer -pkg $PKG -target /"
echo "Note: Code signing/notarization required for distribution outside this machine."
