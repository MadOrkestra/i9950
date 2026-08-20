# Canon i9950 macOS Printer Application

Modern macOS printer driver for the Canon Bubble Jet **i9950** (USB `04A9:1090`), built as a [PAPPL](https://github.com/michaelrsweet/pappl) Printer Application with Gutenprint's `bjc-i9950` encoder.

## Status

| Component | Status |
|-----------|--------|
| Research docs | Complete — see [docs/](docs/) |
| Driver source | Complete — builds without printer |
| USB capture baselines | **Blocked** — no printer connected yet |
| Physical print validation | **Blocked** — connect i9950 via USB |

The driver is designed to work without a kernel extension. When you connect the printer, macOS should discover it via Bonjour after starting the Printer Application.

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
./build/i9950-printer-app serve
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

## License

GPL-2.0-or-later (required by libgutenprint linkage). See [docs/07-architecture-decision.md](docs/07-architecture-decision.md).
