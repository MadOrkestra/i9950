# Canon i9950 Driver Research Documentation

> **Doc version:** `1.2.0` · **Last updated:** 2026-08-25

Research and reference material for developing a modern macOS USB printer driver for the Canon Bubble Jet i9950.

## Documents

| File | Description |
|------|-------------|
| [01-printer-overview.md](01-printer-overview.md) | Hardware specs, variants, ink, paper, interfaces |
| [02-usb-identification.md](02-usb-identification.md) | USB VID/PID, device class, endpoint identification |
| [03-protocol-notes.md](03-protocol-notes.md) | BJL/ESC command structure and job lifecycle |
| [04-existing-drivers.md](04-existing-drivers.md) | Canon, Gutenprint, TurboPrint, Windows inbox drivers |
| [05-community-issues.md](05-community-issues.md) | Known bugs, workarounds, forum reports |
| [06-reverse-engineering-guide.md](06-reverse-engineering-guide.md) | USB capture methodology and analysis workflow |
| [07-architecture-decision.md](07-architecture-decision.md) | PAPPL + libgutenprint architecture; **locked mono/color print paths** |
| [08-feature-matrix.md](08-feature-matrix.md) | Canon original vs v1 target vs stretch goals |
| [09-test-results.md](09-test-results.md) | Test matrix results (updated during development) |
| [10-release-process.md](10-release-process.md) | Product SemVer, changelog, and GitHub Release packaging |
| [11-documentation-standards.md](11-documentation-standards.md) | Doc SemVer rules, header + version-history template |
| [12-developer-guide.md](12-developer-guide.md) | Build from source, dev run, locked paths, hardware tests |
| [sources/bibliography.md](sources/bibliography.md) | Full source list with URLs and access dates |

## Related Project Directories

```
i9950/
├── docs/           ← you are here
├── captures/       ← USB traffic captures (gitignored binaries)
├── src/            ← driver source code
├── ppd/            ← printer capability definitions
├── test/           ← test images and baselines
└── packaging/      ← macOS install scripts
```

## How to Use This Research

1. Read **01** and **02** for hardware and USB identification basics.
2. Read **04** and **05** before choosing implementation strategy.
3. Use **06** when capturing USB traffic with a connected printer.
4. Use **03** to interpret capture data and validate encoder output.
5. Refer to **07** and **08** during implementation planning.
6. Follow **11** for SemVer and version history on every doc (new or updated).
7. Use **10** when cutting a software release (`CHANGELOG.md` + GitHub).
8. Use **12** to build from source or run hardware validation gates.

## Key Facts (Quick Reference)

- **Model:** K10238 (i9900 / i9950 / PIXUS 9900i)
- **USB ID:** `04A9:1090` (Canon, Inc.)
- **Protocol:** Canon BJC extended mode (BJL + ESC binary commands)
- **Target:** macOS CUPS Printer Application (PAPPL-based)
- **Foundation:** Gutenprint `bjc-i9950` backend (EXPERIMENTAL status)

---

## Version history

Document SemVer (`MAJOR.MINOR.PATCH`). See [11-documentation-standards.md](11-documentation-standards.md).

| Version | Date | Notes |
|---------|------|-------|
| 1.2.0 | 2026-08-25 | Index `12-developer-guide.md`; build/dev content moved from root README |
| 1.1.1 | 2026-08-24 | Note locked mono/color paths on ADR 07 |
| 1.1.0 | 2026-08-22 | Index `11-documentation-standards.md`; how-to steps for doc SemVer |
| 1.0.0 | 2026-08-22 | Index of research docs; linked documentation standards and SemVer convention |
