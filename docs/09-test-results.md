# Test Results — Canon i9950 macOS Driver

> **Doc version:** `1.5.0` · **Last updated:** 2026-08-24

## Test Environment

| Field | Value |
|-------|-------|
| Driver version | 0.2.1 |
| Printer | Canon i9950, serial `40f6f2` |
| Connection | USB 2.0 Hi-Speed (`04A9:1090`) |
| Host | macOS Sequoia 15.7.9 arm64 |
| Last updated | 2026-08-24 |

> Automated build tests pass without hardware. Physical matrix started 2026-08-22.

## Locked submit paths (do not regress)

See [07-architecture-decision.md](07-architecture-decision.md#locked-print-paths-physical-gate) for full parameter tables.

### Mono / black / greyscale

```bash
./build/i9950-printer-app submit -d "Canon i9950 (USB)" \
  -o media=iso_a4_210x297mm -o media-type=stationery \
  -o print-color-mode=monochrome -o printer-resolution=600dpi \
  build/t-printable-a4-600.png
```

Encoder must use `600x600dpi_draftmono` + `PrintingMode=BW` + `InputImageType=Grayscale` (0=white). **PASS:** Job 38 (PNG), Job 39 (JPG), **53** (regression 2026-08-24).

### Color

```bash
./build/i9950-printer-app submit -d "Canon i9950 (USB)" \
  -o media=iso_a4_210x297mm -o media-type=stationery \
  -o print-color-mode=color -o printer-resolution=600dpi \
  build/t-color-swatches-a4-600.jpg
```

Encoder must use `600x600dpi_draft` (1-bit CMYK / IP8500). **Not** `600x600dpi` medium (4-bit). **PASS:** Job 52, **54** (regression 2026-08-24).

### Multi-page mono (printable gate)

```bash
./build/i9950-printer-app submit -d "Canon i9950 (USB)" \
  -o media=iso_a4_210x297mm -o media-type=stationery \
  -o print-color-mode=monochrome -o printer-resolution=600dpi \
  build/t-printable-a4-600-p1.png

./build/i9950-printer-app submit -d "Canon i9950 (USB)" \
  -o media=iso_a4_210x297mm -o media-type=stationery \
  -o print-color-mode=monochrome -o printer-resolution=600dpi \
  build/t-printable-a4-600-p2.png
```

Each page shows `PAGE N OF 2`. For CLI submit use `p1.png` + `p2.png` (T08). For PDF use the CUPS path below (T13).

### PDF via CUPS (macOS apps — proper multi-page path)

PAPPL accepts `image/pwg-raster` only. macOS **CUPS** converts `application/pdf` → PWG raster at 600 dpi, then forwards to the IPP printer app. This is the supported PDF workflow for Preview, Pages, and the print dialog.

```bash
lp -d i9950dev \
  -o media=iso_a4_210x297mm \
  -o media-type=stationery \
  -o print-color-mode=monochrome \
  -o printer-resolution=600dpi \
  -o print-scaling=none \
  build/t-printable-a4-600.pdf
```

**PASS:** Job **58** (`i9950dev-70`), `job-impressions-completed=2`; user confirmed both pages correct (2026-08-24).

**10-page stress (T14):**

```bash
lp -d i9950dev \
  -o media=iso_a4_210x297mm \
  -o media-type=stationery \
  -o print-color-mode=monochrome \
  -o printer-resolution=600dpi \
  -o print-scaling=none \
  build/t08-10page-mono-sparse.pdf
```

Fixture: vector sparse mono PDF (`scripts/generate-ink-efficient-tests.py`). **PASS:** Job **59** (`i9950dev-71`), `job-impressions-completed=10`; user confirmed all 10 sheets correct (2026-08-24).

**Color PDF (T15):**

```bash
lp -d i9950dev \
  -o media=iso_a4_210x297mm \
  -o media-type=stationery \
  -o print-color-mode=color \
  -o printer-resolution=600dpi \
  -o print-scaling=none \
  build/t-color-swatches-a4-600.pdf
```

Fixture: `scripts/generate_color_swatches_gate.py` (also `.png`/`.jpg`). **PASS:** Job **60** (`i9950dev-72`), `600x600dpi_draft`, `mono=0`; user confirmed swatches + frame correct (2026-08-24).

Direct `./build/i9950-printer-app submit … .pdf` still fails (`application/pdf` unsupported).

### CUPS queue smoke (single-page raster)

```bash
lp -d i9950dev \
  -o media=iso_a4_210x297mm \
  -o print-color-mode=monochrome \
  -o printer-resolution=600dpi \
  build/t-printable-a4-600.png
```

Queue `i9950dev` → `ipp://127.0.0.1:8501/ipp/print/Canon_i9950_(USB)` (installed LaunchAgent default). Dev server may use another port (e.g. 8502) — update with:

```bash
lpadmin -p i9950dev -v 'ipp://127.0.0.1:8501/ipp/print/Canon_i9950_(USB)'
```

## Ink-efficient hardware policy

Prefer **monochrome** for routine validation (K only). Color swatches are for the color geometry gate only.

Regenerate fixtures:

```bash
build/.venv-fixtures/bin/python scripts/generate_printable_gate.py
build/.venv-fixtures/bin/python scripts/generate_color_swatches_gate.py
python3 scripts/generate-ink-efficient-tests.py   # 10-page sparse PDF
make fixtures-photo   # T04/T07 gates (4×6 + 13×19)
```

### T04 — 4×6 borderless photo (v1.0 criterion #3)

```bash
make fixtures-photo
./scripts/run-hardware-gates.sh t04a   # 600 dpi geometry probe first
./scripts/run-hardware-gates.sh t04    # 2400 dpi after T04a PASS
```

Visual checks: edge color bars reach paper edge; corner L-marks at bleed; eight ink swatches recognizable.

**Note:** Encoder still uses locked `600x600dpi_draft` GP mode; 2400 dpi jobs send a larger raster until photo-resolution mapping lands.

### T07 — 13×19 @ 2400 dpi (v1.0 criterion #5)

```bash
make fixtures-photo
./scripts/run-hardware-gates.sh t07a   # 600 dpi geometry (requires 13×19 glossy loaded)
```

Visual checks: 5 mm frame complete; swatches square; TL/TR/BL/BR near corners. Full T07 @ 2400 dpi blocked on encoder GP photo modes (13×19 @ 2400 raster ~4 GB).

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
| 1 | `build/t-printable-a4-600.png` | Locked mono geometry + polarity gate | Low |
| 2 | `build/t-color-swatches-a4-600.jpg` | Locked color geometry gate | Medium |
| 3 | `build/t-printable-a4-600-p1.png` + `p2.png` | Multi-page mono flush via CLI (T08) | Low |
| 4 | `build/t-printable-a4-600.pdf` | Multi-page mono via CUPS PDF path (T13) | Low |
| 5 | `build/t08-10page-mono-sparse.pdf` | 10-page mono flush via CUPS (T14) | Very low |
| 6 | `build/t-color-swatches-a4-600.pdf` | Color swatches via CUPS PDF (T15) | Medium |
| 7 | `build/t08-2page-mono-sparse.pdf` | Legacy sparse 2-page (superseded) | Very low |
| 8 | `build/t-photo-4x6-600.jpg` | T04a borderless 4×6 geometry @ 600 dpi | Medium |
| 9 | `build/t-photo-4x6-2400.jpg` | T04 borderless 4×6 @ 2400 dpi (v1.0 #3) | High |
| 10 | `build/t-a3plus-600.jpg` | T07a 13×19 geometry @ 600 dpi | Medium |
| Later | Photo / glossy / high multilevel modes | T04/T06/T07 @ 2400 | High — encoder GP mode map open |

Always submit mono with `-o print-color-mode=monochrome`. Color with `-o print-color-mode=color`.

## Automated Checks (No Printer Required)

| Check | Command | Result | Notes |
|-------|---------|--------|-------|
| Build | `make all` | **PASS** | arm64, macOS Sequoia |
| Unit test | `make test` | **PASS** | Job terminator bytes |
| Binary | `build/i9950-printer-app --version` | **PASS** | prints `0.2.1` |
| USB list | `build/i9950-tool list` | **PASS** | reports `04a9:1090` when connected |
| Dry-run | `build/i9950-tool --dry-run nozzle-check` | **PASS** | no hardware needed |

## Test Matrix (Requires Printer)

| ID | Test | macOS Version | Result | Notes |
|----|------|---------------|--------|-------|
| T01 | USB detection (04A9:1090) | Sequoia 15.7.9 | PASS | `system_profiler` + `i9950-tool list`; IEEE1284 `MDL:i9950` |
| T02 | Bonjour discovery | Sequoia 15.7.9 | PASS | `_ipp._tcp` name `Canon i9950 (USB)`; `ipp://tiny.local:8501/ipp/print/Canon_i9950_(USB)`; web UI :8501 |
| T03 | Nozzle check pattern | — | BLOCKED | |
| T04 | 4×6 borderless photo 2400dpi | — | **READY** | Fixtures + `run-hardware-gates.sh`; T04a @ 600 dpi first |
| T05 | A4 letter 600dpi plain | Sequoia 15.7.9 | PASS* | Job 4 completed (old color swatch). *Software PASS only. |
| T05b | Sparse mono area diag JPG | Sequoia 15.7.9 | PENDING visual | Job 6 FAIL (pre-fix). Job **24** completed post-Grayscale fix (~72s, 1 impression). Expect white + thin black geometry full-page — confirm visually. |
| T05c | Text-only A4 mono 600dpi | Sequoia 15.7.9 | PASS | Job 22: readable mono (scale ambiguous). Job 23: corner-marker fixture — TL/TR/BL/BR near page edges; scale + mono **PASS** (user confirmed). Root fix: Black→`InputImageType=Grayscale`. |
| T05d | Printable-area mono gate | Sequoia 15.7.9 | PASS | Job **38** PNG / **39** JPG / **53** regression: `t-printable-a4-600` — white bg, frame, corners. Locked: `draftmono` + BW + Grayscale polarity. |
| T05e | Color swatches geometry gate | Sequoia 15.7.9 | PASS | Job **52** / **54** JPG: `t-color-swatches-a4-600` — squares square, frame complete. Locked: `600x600dpi_draft` (1-bit CMYK). Jobs 43–51 FAIL on medium `600x600dpi` (4-bit stretch). |
| T05f | Regression gate (mono + color) | Sequoia 15.7.9 | PASS | Job **53** mono + **54** color same session after doc lock — both completed, locked resolutions in log. |
| T06 | A4 photo 4800dpi glossy | — | BLOCKED | Defer (color/photo ink) |
| T07 | A3+ 13×19 2400dpi | — | **READY** | T07a @ 600 dpi fixture `t-a3plus-600.jpg`; 2400 dpi encoder map open |
| T08 | Multi-page mono flush (printable gate) | Sequoia 15.7.9 | **PASS** | Jobs **55** (PAGE 1 OF 2) + **56** (PAGE 2 OF 2) via CLI submit; user confirmed both pages printed correctly. Last-page flush OK. |
| T12 | CUPS → IPP smoke (single page) | Sequoia 15.7.9 | **PASS** | Job **57**: `lp -d i9950dev` mono `t-printable-a4-600.png` (CUPS request `i9950dev-69`) completed. |
| T13 | CUPS PDF → IPP (2-page printable gate) | Sequoia 15.7.9 | **PASS** | Job **58**: `lp -d i9950dev` + `print-scaling=none` on `t-printable-a4-600.pdf` (`i9950dev-70`); `job-impressions-completed=2`; user confirmed both pages correct. |
| T14 | CUPS PDF → IPP (10-page stress) | Sequoia 15.7.9 | **PASS** | Job **59**: `t08-10page-mono-sparse.pdf` (`i9950dev-71`); `job-impressions-completed=10`; user confirmed all 10 sheets. v1.0 criterion #4 met. |
| T15 | CUPS color PDF → IPP | Sequoia 15.7.9 | **PASS** | Job **60**: `t-color-swatches-a4-600.pdf` + `print-color-mode=color` (`i9950dev-72`); user confirmed swatches + frame on paper. |
| T16 | Package + LaunchAgent smoke | Sequoia 15.7.9 | **PASS** | `make package` OK; `sudo installer -pkg build/i9950-printer-app.pkg -target /` installed `/usr/local/bin/i9950-printer-app` + `/Library/LaunchAgents/com.i9950.printer-app.plist` (`server` subcommand). LaunchAgent running from system plist; dev smoke plist removed. USB `04a9:1090` detected. |
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
| 2026-08-23 | Mono printable gate: white + frame | `draftmono` + BW + normalize to Grayscale (not Whitescale) | Job 38/39 PASS |
| 2026-08-24 | Color swatches: X stretch, right frame missing | Medium `600x600dpi` is 4-bit C6; use 1-bit `600x600dpi_draft` (IP8500) like mono | Job 52/54 PASS |
| 2026-08-24 | Phase 1: doc sync + multipage/CUPS gates | Feature matrix MVP section; T05f/T08/T12 | T08/T12 PASS (Jobs 55–57) |
| 2026-08-24 | CUPS PDF path for 2-page printable gate | Document CUPS PDF→PWG workflow; `-o print-scaling=none` | T13 PASS (Job 58); user confirmed both pages |
| 2026-08-24 | 10-page + color PDF + package smoke | T14/T15/T16; plist `serve`→`server`; color PDF fixture | T14/T15 PASS (Jobs 59/60); T16 system `sudo installer` confirmed |

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
| 1.5.0 | 2026-08-24 | T04/T07 gate fixtures + hardware run script; status READY |
| 1.4.2 | 2026-08-24 | T16 PASS: system `sudo installer` confirmed |
| 1.4.1 | 2026-08-24 | T14/T15 visual PASS confirmed (Jobs 59/60) |
| 1.4.0 | 2026-08-24 | T14/T15 CUPS PDF gates; package smoke; color PDF fixture |
| 1.3.0 | 2026-08-24 | T13 PASS: CUPS PDF 2-page path (Job 58); locked PDF submit recipe |
| 1.2.0 | 2026-08-24 | Phase 1: Jobs 53/54 regression, multipage/CUPS submit recipes, T08/T12 |
| 1.1.0 | 2026-08-24 | Locked mono (Job 38) and color draft (Job 52) submit paths; T05d/T05e |
| 1.0.0 | 2026-08-22 | Initial test matrix and early automated/no-hardware results |
