# Canon i9950 macOS Printer Application

> **Work in progress** — This project is under active development. Releases are experimental and not ready for general use. Expect breaking changes, incomplete features, and limited hardware validation.

Modern macOS printer driver for the Canon Bubble Jet **i9950** (USB `04A9:1090`).

The driver runs as a userspace Printer Application — no kernel extension required. Connect the printer via USB, install the package, and print from any macOS app through the standard print dialog.

## Disclaimer

This is an **independent, community-driven project**. It is **not affiliated with, endorsed by, or supported by Canon Inc.**

- Software is provided **as-is**, without warranty of any kind.
- Use at your own risk. Test on non-critical jobs before relying on it for important prints.
- The installer package is **unsigned** and has **not** been notarized by Apple.
- Hardware validation is **limited** (see [Known limitations](#known-limitations)). Higher resolutions, photo media, borderless printing, and large paper sizes are not fully verified.
- Bug reports and contributions are welcome; see [docs/12-developer-guide.md](docs/12-developer-guide.md) for building from source.

## Requirements

- macOS 11 or later (Ventura, Sonoma, or Sequoia)
- Canon i9950 connected via USB 2.0 Hi-Speed

## Install

1. Download the latest **`i9950-printer-app-X.Y.Z-macos.pkg`** from [GitHub Releases](https://github.com/MadOrkestra/i9950/releases).
2. Install the package:

```bash
sudo installer -pkg i9950-printer-app-X.Y.Z-macos.pkg -target /
launchctl bootstrap gui/$(id -u) /Library/LaunchAgents/com.i9950.printer-app.plist
```

Replace `X.Y.Z` with the release version (for example `0.2.1`).

3. Connect the i9950 via USB.
4. Open **System Settings → Printers & Scanners** and add **Canon i9950 (USB)** when it appears (IPP/Bonjour on localhost).

The Printer Application starts at login and shows a menu bar icon for configuration or quit.

## Print

Use the normal macOS print dialog from Preview, Pages, Safari, or any app. Supported today:

- A4 plain paper @ 600 dpi
- Monochrome and color
- Multi-page PDF (via macOS CUPS)

## Known limitations

- Package is **unsigned** — Gatekeeper may warn; allow in **System Settings → Privacy & Security** if prompted.
- Validated on **A4 plain @ 600 dpi** only; higher resolutions, borderless, photo media, and large paper sizes are listed but not fully validated yet.
- Color uses draft 1-bit CMYK (lighter ink than photo modes).

See [CHANGELOG.md](CHANGELOG.md) for version history and [docs/08-feature-matrix.md](docs/08-feature-matrix.md) for the full capability roadmap.

## Documentation

| Doc | Description |
|-----|-------------|
| [docs/README.md](docs/README.md) | Research and reference index |
| [docs/12-developer-guide.md](docs/12-developer-guide.md) | Build from source, dev run, hardware tests |
| [docs/10-release-process.md](docs/10-release-process.md) | Versioning and release workflow |

## License

GPL-2.0-or-later (required by libgutenprint linkage). See [docs/07-architecture-decision.md](docs/07-architecture-decision.md).
