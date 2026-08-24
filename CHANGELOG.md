# Changelog

All notable changes to the Canon i9950 macOS Printer Application are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
(`MAJOR.MINOR.PATCH`). See [docs/10-release-process.md](docs/10-release-process.md).

## [Unreleased]

### Added

- GitHub Actions workflow to build and publish the macOS `.pkg` on `v*` tags
- `scripts/release.sh` for end-to-end release (build, tag, push, notes + asset on GitHub)
- Document SemVer + version-history template for all `docs/` files ([docs/11-documentation-standards.md](docs/11-documentation-standards.md))
- Printable-area and color-swatch gate fixtures (`scripts/generate_printable_gate.py`, `scripts/generate_color_swatches_gate.py`)

### Changed

- `packaging/macos/build-pkg.sh` honors `VERSION` from the environment (tag-driven releases)
- **Locked mono path:** `600x600dpi_draftmono` + `PrintingMode=BW` + `InputImageType=Grayscale` (Job 38 PASS) — see [docs/07-architecture-decision.md](docs/07-architecture-decision.md)
- **Locked color path:** `600x600dpi_draft` (1-bit CMYK / IP8500), not medium `600x600dpi` 4-bit (Job 52 PASS)

### Fixed

- Mono polarity: do not use Whitescale with Canon K (Job 37 invert); normalize 0=white → Grayscale
- Color geometry stretch / right-edge clip from multilevel medium mode; use draft 1-bit color mode

### Verified (Phase 1–2)

- Multi-page mono printable gate: Jobs 55/56 (PAGE 1/2 + PAGE 2/2), last-page flush OK
- CUPS → IPP single page: Job 57 via `lp -d i9950dev`
- CUPS PDF → IPP 2-page: Job 58 via `lp -d i9950dev` + `t-printable-a4-600.pdf`

## [0.1.0] - 2026-08-22

### Added

- PAPPL-based Printer Application (`i9950-printer-app`) with Gutenprint `bjc-i9950` encoder
- USB flush helper for Canon bulk-OUT job completion
- Maintenance CLI (`i9950-tool`) with dry-run support
- Unsigned macOS installer package (`make package`)
- Research docs, feature matrix, and automated tests that run without hardware

### Known limitations

- Physical print validation blocked until an i9950 is connected
- Package is unsigned; Gatekeeper may require an override until Developer ID signing and notarization are added
