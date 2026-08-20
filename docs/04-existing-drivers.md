# Existing Drivers — Canon i9950

## Summary Table

| Driver | Platform | Status | Quality | Notes |
|--------|----------|--------|---------|-------|
| Canon official | macOS 10.5–10.6 | Discontinued | Excellent | Last update 2014 |
| Canon official | Windows XP–11 | Inbox/Update | Good | Via MS Update Catalog |
| Gutenprint | Linux/*BSD | EXPERIMENTAL | Variable | Known bugs on i9950 |
| Gutenprint | macOS | **Deprecated 2024** | N/A | No modern binaries |
| TurboPrint | Linux | Commercial | Excellent | Paid; reference only |
| PrintFab | macOS | Third-party | Good | Legacy printer support |

---

## Canon Official — macOS

| Version | OS Support | Download |
|---------|------------|----------|
| CUPS Driver 10.51.2.0 | OS X 10.5, 10.6 | [Canon Asia](https://asia.canon/en/support/0100219601?model=i9950) |
| Printer Driver 4.8.3 | OS X 10.2–10.5 | [Canon Asia](https://asia.canon/en/support/0900481701?model=i9950) |
| BJ Printer Driver 4.6 / 2.52 | Classic Mac OS / early OS X | Canon archives |

**Modern macOS (11+):** No official driver. Canon confirmed no plans for Catalina+ drivers for i9900/i9950 family.

**Workarounds reported:**
- Copy `/Library/Printers/Canon` from older OS X install ([Apple Discussions](https://discussions.apple.com/thread/5641607))
- Install on 10.8 VM, upgrade to 10.9+, copy driver files
- Use PrintFab third-party driver

**Source:** [Canon Community — Catalina](https://community.usa.canon.com/t5/Desktop-Inkjet-Printers/Canon-i9900-Printer-Not-Working-on-Mac-OS-Catalina-10-15/td-p/284677)

---

## Canon Official — Windows

| Component | OS | Notes |
|-----------|-----|-------|
| Inbox driver | Windows 7–11 | Via Windows Update / MS Catalog |
| Driver v1.75a | Windows XP | Standalone installer |
| Add-On Module 1.10 | Vista, 7 | Extends inbox driver features |

**Microsoft Update Catalog:** Search "Canon Inkjet i9950" — packages from 2006, still listed for Windows 10/11.

**Source:** [MS Update Catalog](https://www.catalog.update.microsoft.com/Search.aspx?q=i9950)

---

## Gutenprint (Open Source)

| Item | Detail |
|------|--------|
| Project | [gimp-print.sourceforge.io](https://gimp-print.sourceforge.io/) |
| GitHub mirror | [koenkooi/gutenprint](https://github.com/koenkooi/gutenprint) |
| Model IDs | `bjc-i9950`, `bjc-i9900` |
| Status | **EXPERIMENTAL** |
| PPD files | `stp-bjc-i9950.5.2.ppd.gz`, `stp-bjc-i9950.5.2.sim.ppd.gz` |
| macOS | Formally deprecated July 7, 2024 |

**Printer Application:** [OpenPrinting/gutenprint-printer-app](https://github.com/OpenPrinting/gutenprint-printer-app) — Linux/Snap only; not packaged for macOS.

**Relevance to this project:** We use Gutenprint's Canon backend (`libgutenprint`) as the protocol encoder, wrapped in our own PAPPL Printer Application for macOS.

---

## TurboPrint (Commercial Linux)

[TurboPrint i9950 page](https://www.turboprint.info/printer_Canon_i9950.html)

Features claimed:
- 600–4800 dpi print quality
- Borderless, CD printing
- Ink level display, nozzle test, head cleaning, alignment
- Color profiles for Canon and third-party papers
- Max size 32.89 × 58.42 cm (with Pro license)

Useful as a **feature parity reference** — not usable code (proprietary).

---

## Canon UFR II / cnrdrvcups-lb

Canon's modern Linux driver bundle (`cnrdrvcups-lb`) supports laser and newer inkjet models via UFR II, LIPSLX, CARPS2. **Does not include i9950.**

**Source:** [ArchWiki Canon cnrdrvcups-lb](https://wiki.archlinux.org/title/Canon_cnrdrvcups-lb_Driver)

---

## OpenPrinting Database

The i9950 is not prominently listed in the current OpenPrinting printer database with a dedicated entry. Community relies on Gutenprint PPD auto-detection.

**Source:** [OpenPrinting Canon list](https://openprinting.org/printers/manufacturer/Canon)

---

## Why a New macOS Driver Is Needed

1. Canon ended macOS support at 10.6 (2014)
2. Gutenprint deprecated macOS binaries (2024)
3. Apple's driverless/AirPrint model does not cover legacy USB inkjets
4. Existing Gutenprint i9950 support is EXPERIMENTAL with known bugs
5. PAPPL Printer Applications are Apple's endorsed replacement for kernel drivers

Our project fills this gap with a maintained, macOS-native Printer Application.
