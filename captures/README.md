# USB Capture Directory

Binary USB traffic captures for protocol validation. **Not committed to git** (see `.gitignore`).

## Expected Layout

```
captures/
├── README.md              ← this file
├── canon/                 ← captures from Canon/Windows reference driver
│   ├── nozzle-check.pcapng
│   ├── photo-2400-out.bin
│   └── ...
├── gutenprint/            ← captures from Linux Gutenprint
│   └── ...
└── ours/                  ← captures from i9950-printer-app (development)
    └── ...
```

## Capture Checklist

- [ ] `canon/nozzle-check` — nozzle test pattern
- [ ] `canon/text-600` — plain A4 text at 600 dpi
- [ ] `canon/photo-2400` — color photo A4 2400 dpi
- [ ] `canon/photo-4800` — color photo A4 4800 dpi
- [ ] `canon/borderless-4x6` — borderless 4×6
- [ ] `canon/a3plus-2400` — 13×19 at 2400 dpi
- [ ] `canon/head-clean` — maintenance cycle
- [ ] `gutenprint/photo-2400` — same settings as canon reference
- [ ] `ours/photo-2400` — our driver, same settings

## How to Capture

See [docs/06-reverse-engineering-guide.md](../docs/06-reverse-engineering-guide.md).

## Analysis Tools

```bash
# Normalize and diff two capture binaries
make -C .. normalize-capture CAP=canon/photo-2400-out.bin
make -C .. normalize-capture CAP=ours/photo-2400-out.bin
diff captures/canon/photo-2400-out.norm captures/ours/photo-2400-out.norm
```

## Status

**No printer connected yet.** Capture checklist items remain unchecked until a Canon i9950 is available on USB (`04A9:1090`). Tools and documentation are ready:

- `tools/extract_bulk_out.sh` — extract bulk OUT from pcapng (Windows VM capture)
- `tools/normalize_capture.py` — normalize SetTime for diffs
- `scripts/capture-helper.sh` — detect printer + print workflow
