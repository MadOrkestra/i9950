# Canon i9950 macOS Printer Application

Modern macOS printer driver for the Canon Bubble Jet **i9950** (USB `04A9:1090`), built as a [PAPPL](https://github.com/michaelrsweet/pappl) Printer Application with Gutenprint's `bjc-i9950` encoder.

## Status

| Component | Status |
|-----------|--------|
| Research docs | Complete — see [docs/](docs/) |
| Driver source | Builds; locked mono + color draft paths |
| USB capture baselines | Partial — live USB print jobs exercised |
| Physical print validation | Mono + color gates PASS; CUPS PDF 2/10-page + color PDF (Jobs 58–60); package smoke PASS |

The driver is designed to work without a kernel extension. When you connect the printer, macOS should discover it via Bonjour after starting the Printer Application.

## Locked print paths

Do not change encoder Resolution/polarity without a new physical gate. Details:
[docs/07-architecture-decision.md](docs/07-architecture-decision.md#locked-print-paths-physical-gate).

**Black / greyscale only** (`print-color-mode=monochrome`):

```bash
./build/i9950-printer-app server -o log-file=build/i9950-server.log -o log-level=debug
./build/i9950-printer-app submit -d "Canon i9950 (USB)" \
  -o media=iso_a4_210x297mm -o media-type=stationery \
  -o print-color-mode=monochrome -o printer-resolution=600dpi \
  build/t-printable-a4-600.png
```

Uses Gutenprint `600x600dpi_draftmono` + `PrintingMode=BW` + `InputImageType=Grayscale` (0=white). K ink only.

**Color** (`print-color-mode=color`):

```bash
./build/i9950-printer-app submit -d "Canon i9950 (USB)" \
  -o media=iso_a4_210x297mm -o media-type=stationery \
  -o print-color-mode=color -o printer-resolution=600dpi \
  build/t-color-swatches-a4-600.jpg
```

Uses Gutenprint `600x600dpi_draft` (1-bit CMYK). Do **not** use medium `600x600dpi` (4-bit) — it stretches X and clips the right margin.

**Multi-page PDF** (via CUPS — Preview, Pages, print dialog):

```bash
lp -d i9950dev \
  -o media=iso_a4_210x297mm -o media-type=stationery \
  -o print-color-mode=monochrome -o printer-resolution=600dpi \
  -o print-scaling=none \
  build/t-printable-a4-600.pdf
```

CUPS converts PDF → PWG raster @ 600 dpi, then sends to the printer app. Direct `i9950-printer-app submit … .pdf` is not supported.

## Requirements

- macOS 11+ (Ventura/Sonoma/Sequoia target)
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

Then add the printer in **System Settings → Printers** (should appear via IPP/Bonjour on localhost).

## Install (unsigned dev package)

```bash
make package
sudo installer -pkg build/i9950-printer-app.pkg -target /
launchctl load ~/Library/LaunchAgents/com.i9950.printer-app.plist
```

## Maintenance tool

```bash
# Without printer:
./build/i9950-tool --dry-run list
./build/i9950-tool --dry-run nozzle-check

# With printer connected:
./build/i9950-tool list
```

## When you get the printer

1. Connect via USB 2.0 Hi-Speed
2. Verify: `system_profiler SPUSBDataType | grep -i 9950`
3. Run capture workflow: [docs/06-reverse-engineering-guide.md](docs/06-reverse-engineering-guide.md)
4. Print test page and update [docs/09-test-results.md](docs/09-test-results.md)

## Releases

Versioning, changelog requirements, and GitHub Release contents: [docs/10-release-process.md](docs/10-release-process.md). Changes: [CHANGELOG.md](CHANGELOG.md).

```bash
./scripts/release.sh X.Y.Z          # build .pkg, tag, push, publish notes + asset
./scripts/release.sh X.Y.Z --dry-run
```

## License

GPL-2.0-or-later (required by libgutenprint linkage). See [docs/07-architecture-decision.md](docs/07-architecture-decision.md).
