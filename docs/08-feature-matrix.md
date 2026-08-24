# Feature Matrix — Canon i9950 Driver

> **Doc version:** `1.2.0` · **Last updated:** 2026-08-24

## Current MVP (hardware-proven)

As of 2026-08-24, the driver reliably prints **A4 @ 600 dpi on plain paper** with locked encoder paths ([07-architecture-decision.md](07-architecture-decision.md)):

| Mode | Gutenprint resolution | Status |
|------|----------------------|--------|
| Mono / greyscale / K-only | `600x600dpi_draftmono` | **PASS** (Job 38, 53) |
| Color | `600x600dpi_draft` (1-bit CMYK) | **PASS** geometry (Job 52, 54); lighter ink than medium/photo modes |

Full 8-ink multilevel color (`600x600dpi` C6 inkset) is **not** MVP — it breaks aspect ratio on i9950 hardware.

## Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Target for v1 |
| 🔶 | Stretch / v1.1 |
| ❌ | Out of scope |
| 📋 | Canon original had it |

## Comparison Table

| Feature | Canon Original | Gutenprint | TurboPrint | **Our v1 Target** |
|---------|---------------|------------|------------|-------------------|
| USB printing | 📋 ✅ | ✅ (buggy) | ✅ | ✅ |
| FireWire | 📋 ✅ | ✅ | ✅ | ❌ |
| 600 dpi | 📋 ✅ | ✅ | ✅ | ✅ |
| 1200 dpi | 📋 ✅ | ✅ | ✅ | ✅ |
| 2400 dpi | 📋 ✅ | ✅ | ✅ | ✅ |
| 4800 dpi | 📋 ✅ | ✅ | ✅ | ✅ |
| 8-ink color | 📋 ✅ | ✅ | ✅ | ✅ |
| A4 / Letter | 📋 ✅ | ✅ | ✅ | ✅ |
| A3 / 11×17 | 📋 ✅ | ✅ | ✅ | ✅ |
| A3+ / 13×19 | 📋 ✅ | ✅ | ✅ | ✅ |
| Borderless | 📋 ✅ | ✅ | ✅ | ✅ |
| Photo paper modes | 📋 ✅ | ✅ | ✅ | ✅ |
| Matte / glossy profiles | 📋 ✅ | ✅ | ✅ | 🔶 |
| ColorSync / ICC | 📋 ✅ | ✅ | ✅ | 🔶 |
| Grayscale | 📋 ✅ | ✅ | ✅ | ✅ |
| CD/DVD printing | 📋 ✅ | ✅ | ✅ | ❌ |
| Duplex | — | — | — | ❌ (no hardware) |
| Ink level display | 📋 ✅ | 🔶 | ✅ | 🔶 v1.1 |
| Nozzle check | 📋 ✅ | 🔶 | ✅ | 🔶 v1.1 |
| Head cleaning | 📋 ✅ | 🔶 | ✅ | 🔶 v1.1 |
| Head alignment | 📋 ✅ | 🔶 | ✅ | 🔶 v1.1 |
| PictBridge | 📋 ✅ | — | — | ❌ |
| macOS 11+ | ❌ | ❌ | ❌ | ✅ |
| macOS 10.6 | 📋 ✅ | ✅ (old) | — | ❌ |

## v1 Priority Breakdown

### P0 — Must Have (MVP)

- [x] Single-page USB print without hang
- [x] 600 dpi **mono** on A4 plain paper (K-only, white background)
- [x] 600 dpi **color** on A4 plain paper (draft 1-bit CMYK; correct geometry)
- [x] Recognizable color output (swatches; not full photo quality)
- [x] Job completes; printer returns to ready
- [x] Bonjour discovery on macOS

### P1 — Full Parity (v1.0)

- [ ] Resolutions: 600 only today; 1200, 2400, 4800 dpi deferred ([i9950_driver.c](../src/pappl/i9950_driver.c) advertises 600 until encoder maps GP modes)
- [ ] Paper sizes through 13×19 / A3+ (listed in driver; only A4 gated on hardware)
- [ ] Borderless printing (flag set; not validated)
- [ ] Media type selection on hardware (plain PASS; photo glossy/matte not gated)
- [x] Multi-page documents with **printable gate** artwork (T08 PASS — Jobs 55/56; T13 PASS — Job 58 PDF via CUPS)
- [ ] Full multilevel 8-ink color without geometry stretch

### P2 — Maintenance (v1.1)

- [ ] `i9950-tool nozzle-check`
- [ ] `i9950-tool head-clean`
- [ ] `i9950-tool ink-levels`
- [ ] `i9950-tool align`

### Out of Scope

- CD/DVD printing (per project requirements)
- FireWire interface
- PictBridge / direct camera print
- Windows / Linux builds (macOS primary; PAPPL is portable if needed later)

## IPP Attributes to Expose

**Shipped today** (see [i9950_driver.c](../src/pappl/i9950_driver.c)):

```
media-supported: na_letter_8.5x11in, iso_a4_210x297mm, iso_a3_297x420mm, ...
media-type-supported: stationery, photographic-glossy, photographic-matte, stationery-letterhead
pwg-raster-document-resolution-supported: 600dpi
print-color-mode-supported: monochrome, color
borderless-supported: true (per paper size; not hardware-validated)
sides-supported: one-sided
document-format-supported: image/pwg-raster (PDF via CUPS filter chain, not direct IPP)
```

**v1.0 target** (partial):

```
pwg-raster-document-resolution-supported: 600dpi, 1200dpi, 2400dpi, 4800dpi
application/pdf on IPP (optional; CUPS PDF→PWG path PASS — T13–T15 Jobs 58–60)
```

## Success Criteria (v1.0 Release)

1. Install `.pkg` on macOS Ventura, Sonoma, or Sequoia — **PASS** (T16, system install confirmed)
2. Printer auto-discovered when USB connected
3. Print 4×6 borderless photo at 2400 dpi — correct colors, full bleed
4. Print 10-page PDF — all pages complete, no power cycle needed — **PASS** (T14 Job 59, user confirmed)
5. Print 13×19 at 2400 dpi — full page, no truncation

See [09-test-results.md](09-test-results.md) for test execution status.

---

## Version history

Document SemVer (`MAJOR.MINOR.PATCH`). See [11-documentation-standards.md](11-documentation-standards.md).

| Version | Date | Notes |
|---------|------|-------|
| 1.2.0 | 2026-08-24 | CUPS PDF→PWG multi-page path PASS (T13 Job 58) |
| 1.1.0 | 2026-08-24 | MVP reality: draft mono/color at 600 dpi; P1 resolutions/multilevel color open |
| 1.0.0 | 2026-08-22 | Initial feature matrix (Canon vs v1 target vs stretch) |
