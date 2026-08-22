# Feature Matrix — Canon i9950 Driver

> **Doc version:** `1.0.0` · **Last updated:** 2026-08-22

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
- [x] 600 dpi color on A4 plain paper
- [x] Recognizable color output (8-ink)
- [x] Job completes; printer returns to ready
- [x] Bonjour discovery on macOS

### P1 — Full Parity (v1.0)

- [ ] Resolutions: 600, 1200, 2400, 4800 dpi
- [ ] Paper sizes through 13×19 / A3+
- [ ] Borderless printing
- [ ] Media type selection (plain, photo glossy, matte, HR)
- [x] Multi-page documents (2-page mono PDF completed / flushed; 10-page still deferred)

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

Derived from Gutenprint PPD and Canon original driver:

```
media-supported: na_letter_8.5x11in, iso_a4_210x297mm, iso_a3_297x420mm, ...
media-type-supported: stationery, photographic-glossy, photographic-matte, ...
pwg-raster-document-resolution-supported: 600dpi, 1200dpi, 2400dpi, 4800dpi
print-color-mode-supported: monochrome, color
borderless-supported: true (per paper size)
sides-supported: one-sided
```

## Success Criteria (v1.0 Release)

1. Install `.pkg` on macOS Ventura, Sonoma, or Sequoia
2. Printer auto-discovered when USB connected
3. Print 4×6 borderless photo at 2400 dpi — correct colors, full bleed
4. Print 10-page PDF — all pages complete, no power cycle needed
5. Print 13×19 at 2400 dpi — full page, no truncation

See [09-test-results.md](09-test-results.md) for test execution status.

---

## Version history

Document SemVer (`MAJOR.MINOR.PATCH`). See [11-documentation-standards.md](11-documentation-standards.md).

| Version | Date | Notes |
|---------|------|-------|
| 1.0.0 | 2026-08-22 | Initial feature matrix (Canon vs v1 target vs stretch) |
