# Test Results — Canon i9950 macOS Driver

## Test Environment

| Field | Value |
|-------|-------|
| Driver version | 0.1.0-dev |
| Printer | **Not connected** |
| Connection | N/A |
| Last updated | 2026-08-20 |

> Physical tests require a Canon i9950 on USB (`04A9:1090`). Automated build tests pass without hardware.

## Automated Checks (No Printer Required)

| Check | Command | Result | Notes |
|-------|---------|--------|-------|
| Build | `make all` | **PASS** | arm64, macOS Sequoia |
| Unit test | `make test` | **PASS** | Job terminator bytes |
| Binary | `build/i9950-printer-app --version` | **PASS** | prints `0.1.0` |
| USB list | `build/i9950-tool list` | **PASS** | correctly reports no device |
| Dry-run | `build/i9950-tool --dry-run nozzle-check` | **PASS** | no hardware needed |

## Test Matrix (Requires Printer)

| ID | Test | macOS Version | Result | Notes |
|----|------|---------------|--------|-------|
| T01 | USB detection (04A9:1090) | — | BLOCKED | No printer connected |
| T02 | Bonjour discovery | — | BLOCKED | Run `i9950-printer-app serve` after connect |
| T03 | Nozzle check pattern | — | BLOCKED | |
| T04 | 4×6 borderless photo 2400dpi | — | BLOCKED | |
| T05 | A4 letter 600dpi plain | — | BLOCKED | MVP baseline |
| T06 | A4 photo 4800dpi glossy | — | BLOCKED | |
| T07 | A3+ 13×19 2400dpi | — | BLOCKED | |
| T08 | 10-page PDF | — | BLOCKED | Validates last-page flush fix |
| T09 | Grayscale document | — | BLOCKED | |
| T10 | Sleep/wake reconnect | — | BLOCKED | |
| T11–T13 | Ventura/Sonoma/Sequoia | Sequoia build OK | PARTIAL | Build verified on Sequoia only |

| Date | Issue | Fix | Verified |
|------|-------|-----|----------|
| — | — | — | — |

## How to Record Results

1. Run test from matrix
2. Update Result column: PASS / FAIL / SKIP
3. Add notes and screenshots to `test/expected/` if visual
4. Log regressions in table above
