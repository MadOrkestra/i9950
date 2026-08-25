# Developer Guide — Build, Run, and Test

> **Doc version:** `1.0.0` · **Last updated:** 2026-08-25

How to build, run, and validate the Canon i9950 macOS Printer Application from source. For end-user install from a GitHub Release `.pkg`, see the root [README.md](../README.md).

## Requirements

- macOS 11+ (Ventura / Sonoma / Sequoia target)
- Xcode Command Line Tools
- Homebrew: `libusb`, `openssl@3`, `jpeg-turbo`, `libpng`, `gettext`, `libtool`, `autoconf`, `automake`

## Build

```bash
cd i9950
make deps    # builds vendored PAPPL + libgutenprint (first time only)
make         # produces build/i9950-printer-app and build/i9950-tool
make test    # unit tests (no printer needed)
```

## Run (development)

```bash
./build/i9950-printer-app server
```

Optional logging:

```bash
./build/i9950-printer-app server -o log-file=build/i9950-server.log -o log-level=debug
```

When running `server` on macOS, a **menu bar icon** (Lucide printer, template image for light/dark) opens configuration or quit. Disable with `I9950_NO_MENU_BAR=1`.

Add the printer in **System Settings → Printers** (should appear via IPP/Bonjour on localhost).

## Local package (unsigned)

To smoke-test the installer layout without a GitHub Release:

```bash
make package
sudo installer -pkg build/i9950-printer-app.pkg -target /
launchctl bootstrap gui/$(id -u) /Library/LaunchAgents/com.i9950.printer-app.plist
```

See [packaging/macos/INSTALL.md](../packaging/macos/INSTALL.md) for signing/notarization notes.

## Locked print paths

Do not change encoder Resolution/polarity without a new physical gate. Details:
[07-architecture-decision.md](07-architecture-decision.md#locked-print-paths-physical-gate).

### Black / greyscale only (`print-color-mode=monochrome`)

```bash
./build/i9950-printer-app submit -d "Canon i9950 (USB)" \
  -o media=iso_a4_210x297mm -o media-type=stationery \
  -o print-color-mode=monochrome -o printer-resolution=600dpi \
  build/t-printable-a4-600.png
```

Uses Gutenprint `600x600dpi_draftmono` + `PrintingMode=BW` + `InputImageType=Grayscale` (0=white). K ink only.

### Color (`print-color-mode=color`)

```bash
./build/i9950-printer-app submit -d "Canon i9950 (USB)" \
  -o media=iso_a4_210x297mm -o media-type=stationery \
  -o print-color-mode=color -o printer-resolution=600dpi \
  build/t-color-swatches-a4-600.jpg
```

Uses Gutenprint `600x600dpi_draft` (1-bit CMYK). Do **not** use medium `600x600dpi` (4-bit) — it stretches X and clips the right margin.

### Multi-page PDF (via CUPS — Preview, Pages, print dialog)

```bash
lp -d i9950dev \
  -o media=iso_a4_210x297mm -o media-type=stationery \
  -o print-color-mode=monochrome -o printer-resolution=600dpi \
  -o print-scaling=none \
  build/t-printable-a4-600.pdf
```

CUPS converts PDF → PWG raster @ 600 dpi, then sends to the printer app. Direct `i9950-printer-app submit … .pdf` is not supported.

Full test matrix and submit recipes: [09-test-results.md](09-test-results.md).

## Maintenance tool

```bash
# Without printer:
./build/i9950-tool --dry-run list
./build/i9950-tool --dry-run nozzle-check

# With printer connected:
./build/i9950-tool list
```

## When you connect a printer

1. Connect via USB 2.0 Hi-Speed
2. Verify: `system_profiler SPUSBDataType | grep -i 9950`
3. Run capture workflow: [06-reverse-engineering-guide.md](06-reverse-engineering-guide.md)
4. Print test page and update [09-test-results.md](09-test-results.md)

Hardware gate fixtures and run script:

```bash
make fixtures-photo
./scripts/run-hardware-gates.sh t04a   # 4×6 borderless geometry @ 600 dpi
```

## Cut a release

Versioning, changelog requirements, and GitHub Release packaging: [10-release-process.md](10-release-process.md). Changes: [CHANGELOG.md](../CHANGELOG.md).

```bash
./scripts/release.sh X.Y.Z          # build .pkg, tag, push, publish notes + asset
./scripts/release.sh X.Y.Z --dry-run
```

## Related documentation

| Doc | Topic |
|-----|-------|
| [07-architecture-decision.md](07-architecture-decision.md) | PAPPL + libgutenprint architecture |
| [08-feature-matrix.md](08-feature-matrix.md) | v1 target vs stretch goals |
| [09-test-results.md](09-test-results.md) | Hardware test matrix |
| [10-release-process.md](10-release-process.md) | Product SemVer and GitHub Releases |

---

## Version history

Document SemVer (`MAJOR.MINOR.PATCH`). See [11-documentation-standards.md](11-documentation-standards.md).

| Version | Date | Notes |
|---------|------|-------|
| 1.0.0 | 2026-08-25 | Build, dev run, locked paths, and release workflow (moved from root README) |
