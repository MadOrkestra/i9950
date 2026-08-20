# Community Issues and Workarounds

## Issue 1: Incomplete Last Page / Job Hang

**Symptoms:**
- Print stops partway through the last page
- CUPS shows "Rendering completed" while printer is still mid-page
- Printer stuck until USB disconnect or power cycle
- Affects multi-page jobs; single pages may work

**Reports:**
- [openSUSE Forums — half page / lock up](https://forums.opensuse.org/t/printer-only-prints-half-a-page/137952)
- User workaround: add blank page at end of documents

**Root cause (Gutenprint project):**
Legacy CUPS `canon://` and `epson://` backends fail to flush all USB bulk data on certain OS/kernel versions. The backend believes data was sent, but `close()` on non-blocking file descriptors leaves data in kernel buffers.

**Fix for our driver:**
- Never use `canon://` backend
- Use PAPPL USB path with synchronous bulk writes
- Explicit flush after all raster data
- Send verified job terminator (`SSR=DF;`)
- Keep job state `processing` until USB OUT queue is drained

**Source:** [Gutenprint NEWS](https://github.com/koenkooi/gutenprint/blob/master/NEWS)

---

## Issue 2: Garbage Output with i9950/i9900 Gutenprint PPD

**Symptoms:**
- Using Gutenprint i9950 or i9900 driver produces scrambled/wrong output
- BJC-8500 driver works but at reduced resolution (600×600)

**Report:**
- [30 Days of Linux — Canon i9900 on Ubuntu](https://my30daysoflinux.blogspot.com/2016/02/canon-i9900-printer-working-ubuntu-1404.html)
- Two weeks of testing; i9900-named driver "does NOT WORK"
- BJC8500 driver selected as workaround

**Possible causes:**
- Wrong model_id or channel order in encoder
- Incorrect ESC `(l` / `(P` command lengths
- 8-ink weaving parameters mismatch
- Network printing vs direct USB (user tested via network)

**Fix for our driver:**
- Validate encoder output against USB captures
- Compare i9950 vs i9900 Gutenprint definitions
- Test direct USB before network relay

---

## Issue 3: macOS Driver Installation Failures

**Symptoms:**
- Canon driver installer refuses to run on macOS 10.9+
- Quality/Borderless options greyed out after partial install

**Reports:**
- [Apple Discussions — 10.9 i9950](https://discussions.apple.com/thread/5641607)
- [SuperUser — i950 spoof attempt](https://superuser.com/questions/1795261/unable-to-spoof-macos-level-in-order-to-install-printer-driver-for-canon-i950)

**Workaround:**
Copy `/Library/Printers/Canon` from older OS X installation; repair driver when prompted.

**Our approach:** Bypass Canon installer entirely with PAPPL Printer Application.

---

## Issue 4: Gutenprint macOS Deprecation

**Date:** July 7, 2024

Gutenprint formally deprecated macOS support. No further macOS binaries will be produced. No active macOS maintainer for 3+ years.

**Impact:** Linux Gutenprint remains available; macOS users have no maintained open-source path.

**Source:** [Gutenprint macOS FAQ](https://gimp-print.sourceforge.io/p_FAQ_OS_X.php)

---

## Issue 5: PDF Printing Freezes

**Symptoms:**
- PDF print jobs lock up mid-page
- Test pages via CUPS localhost:631 also fail
- USB disconnect required to recover

**Report:** Same openSUSE thread; user on Gutenprint 5.2.14 and 5.3.3.

**Note:** May overlap with Issue 1 (backend flush) or separate raster size/timeout issue.

---

## Issue 6: Print Head / Maintenance (Hardware)

Not driver bugs, but frequently discussed alongside driver problems:

- Clogged nozzles (cyan/yellow common)
- Purge unit not cleaning properly
- Ink level shown empty despite full cartridges (likely head failure)
- Print head QY6-0055-000 replacement (~$100+)

**Source:** [PrinterKnowledge i9900/i9950 thread](https://www.printerknowledge.com/threads/canon-i9900-in-usa-or-i9950.7870/)

---

## Workarounds Summary

| Problem | Workaround | Our Fix |
|---------|------------|---------|
| Last page hang | Add blank page; power cycle | Proper USB flush + job end |
| Bad Gutenprint output | Use BJC-8500 driver | Fix i9950 encoder params |
| No macOS driver | VM with old OS X; PrintFab | PAPPL Printer Application |
| No Linux official driver | Gutenprint / TurboPrint | N/A (macOS target) |

---

## Bug Report Channels (Reference)

- Gutenprint bugs: https://sourceforge.net/bugs/?group_id=1537
- Gutenprint forums: https://sourceforge.net/forum/?group_id=1537

When our driver encounters Gutenprint backend bugs, consider upstream patches to Gutenprint canon definitions.
