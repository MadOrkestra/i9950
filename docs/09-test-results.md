# Test Results — Canon i9950 macOS Driver

> **Doc version:** `1.0.0` · **Last updated:** 2026-08-22

## Test Environment

| Field | Value |
|-------|-------|
| Driver version | 0.1.0-dev |
| Printer | Canon i9950, serial `40f6f2` |
| Connection | USB 2.0 Hi-Speed (`04A9:1090`) |
| Host | macOS Sequoia 15.7.9 arm64 |
| Last updated | 2026-08-22 |

> Automated build tests pass without hardware. Physical matrix started 2026-08-22.

## Ink-efficient hardware policy

Use **black (K) only** until the USB/encode/flush path is proven. Regenerate fixtures with:

```bash
python3 scripts/generate-ink-efficient-tests.py
```

**Do not print solid full-page fills or color swatches for routine validation.**

### Primary area diagnostic (`build/t-diag-a4-mono.jpg`)

One sparse A4 mono page (~2–3% inked pixels) that still checks the printable area:

| Element | What it validates |
|---------|-------------------|
| 1 px outer border + corner L-marks | Margins / clipping / edge nozzles |
| ~2" ruling grid (hairlines) | Straight horizontals & verticals across the page |
| Full-page diagonals | Skew / weave across the whole plane |
| Concentric circle outlines + crosshair | Curves / centering |
| 1/2/4/8 px stroke samples | Line weight / rasterization |
| Tiny 50% / 25% / fine checker patches | Halftone/raster (small only) |
| Thin K ramp strip (8 px tall) | Grayscale response without flooding |

Aliases: `build/t05-a4-mono-sparse.jpg` (same file).

| Priority | Asset | Purpose | Ink |
|----------|-------|---------|-----|
| 1 | `build/t-diag-a4-mono.jpg` | Area + geometry path | Very low |
| 2 | `build/t08-2page-mono-sparse.pdf` | Last-page flush smoke | Very low |
| 3 | `build/t08-10page-mono-sparse.pdf` | Full multi-page flush (only if #2 passes) | Low |
| Later | Color / photo / glossy | T04/T06 quality | High — defer |

Always submit with `-o print-color-mode=monochrome` (or CUPS `print-color-mode=monochrome`).
Wasteful color fixtures (if present) live under `build/archive-wasteful/` — do not print them.

## Automated Checks (No Printer Required)

| Check | Command | Result | Notes |
|-------|---------|--------|-------|
| Build | `make all` | **PASS** | arm64, macOS Sequoia |
| Unit test | `make test` | **PASS** | Job terminator bytes |
| Binary | `build/i9950-printer-app --version` | **PASS** | prints `0.1.0` |
| USB list | `build/i9950-tool list` | **PASS** | reports `04a9:1090` when connected |
| Dry-run | `build/i9950-tool --dry-run nozzle-check` | **PASS** | no hardware needed |

## Test Matrix (Requires Printer)

| ID | Test | macOS Version | Result | Notes |
|----|------|---------------|--------|-------|
| T01 | USB detection (04A9:1090) | Sequoia 15.7.9 | PASS | `system_profiler` + `i9950-tool list`; IEEE1284 `MDL:i9950` |
| T02 | Bonjour discovery | Sequoia 15.7.9 | PASS | `_ipp._tcp` name `Canon i9950 (USB)`; `ipp://tiny.local:8501/ipp/print/Canon_i9950_(USB)`; web UI :8501 |
| T03 | Nozzle check pattern | — | BLOCKED | |
| T04 | 4×6 borderless photo 2400dpi | — | BLOCKED | |
| T05 | A4 letter 600dpi plain | Sequoia 15.7.9 | PASS* | Job 4 completed (old color swatch). *Software PASS only. |
| T05b | Sparse mono area diag JPG | Sequoia 15.7.9 | PENDING visual | Job 6 FAIL (pre-fix). Job **24** completed post-Grayscale fix (~72s, 1 impression). Expect white + thin black geometry full-page — confirm visually. |
| T05c | Text-only A4 mono 600dpi | Sequoia 15.7.9 | PASS | Job 22: readable mono (scale ambiguous). Job 23: corner-marker fixture — TL/TR/BL/BR near page edges; scale + mono **PASS** (user confirmed). Root fix: Black→`InputImageType=Grayscale`. |
| T06 | A4 photo 4800dpi glossy | — | BLOCKED | Defer (color/photo ink) |
| T07 | A3+ 13×19 2400dpi | — | BLOCKED | Defer (paper + ink) |
| T08 | Multi-page PDF flush | Sequoia 15.7.9 | PENDING visual | Job 21: 2 impressions but wrong artwork (pre-fix). Job **26** via CUPS `i9950dev` completed with **2 impressions** post-fix (~3 min). Direct PAPPL PDF submit aborts (`application/pdf` unsupported). Confirm both pages match sparse mono artwork. |
| T09 | Grayscale document | Sequoia 15.7.9 | PASS* | Job 5 completed mono. Prefer sparse fixtures; confirm visually next. |
| T10 | Sleep/wake reconnect | — | BLOCKED | |
| T11–T13 | Ventura/Sonoma/Sequoia | Sequoia build OK | PARTIAL | Build verified on Sequoia only |

| Date | Issue | Fix | Verified |
|------|-------|-----|----------|
| 2026-08-22 | Server SIGSEGV on first print: `stp_init` never called; no Gutenprint XML | Set `STP_DATA_PATH`, call `stp_init()` | Job 2+ no longer crash |
| 2026-08-22 | `stp_verify` failed: full-page image vs hardware margins | Size job to Gutenprint imageable area; named `PageSize` | Job 3 reached `stp_print` |
| 2026-08-22 | `stp_print` abort (status 2) | Set `InputImageType=RGB`; do not abort on row `byte_limit` | T05 job 4 completed |
| 2026-08-22 | Sparse mono diag + 2-page PDF: jobs complete but print ≠ source; grey flood, banding, magenta cast | Open: compare Gutenprint mono path vs nozzle check; CUPS PDF→PWG at huge sGray size | Photos in Cursor assets; T05b FAIL visual, T08 PARTIAL |
| 2026-08-22 | Mono A4 looked ~half/⅓ page + grey garbage | Mono raster is 1 byte/px but encoder forced `InputImageType=RGB` (3 bytes/px). Map CUPS spaces correctly | Job 23 visual PASS (corner markers, scale) |
| 2026-08-22 | Sparse mono printed as **near-solid black** (ink flood) | PAPPL `CUPS_CSPACE_K` is 0=white; encoder used `Grayscale` (0=black) → inverted. Switch K/W→`Whitescale`; abort mono pages >8% ink unless `I9950_ALLOW_HIGH_INK=1` | Fix built; awaiting sparse retest |

## How to Record Results

1. Run test from matrix
2. Update Result column: PASS / FAIL / SKIP
3. Add notes and screenshots to `test/expected/` if visual
4. Log regressions in table above

---

## Version history

Document SemVer (`MAJOR.MINOR.PATCH`). See [11-documentation-standards.md](11-documentation-standards.md).

| Version | Date | Notes |
|---------|------|-------|
| 1.0.0 | 2026-08-22 | Initial test matrix and early automated/no-hardware results |
