# Third-party dependencies

These libraries are **not committed** to git. Clone them here before building:

```bash
# PAPPL (Printer Application framework) — tag v1.4.8
git clone --depth 1 --branch v1.4.8 https://github.com/michaelrsweet/pappl.git pappl

# Gutenprint (libgutenprint Canon backend)
git clone --depth 1 https://github.com/koenkooi/gutenprint.git gutenprint
```

Then from the repo root:

```bash
make deps   # configure & build vendored libraries
make        # build i9950-printer-app
```

## Optional: git submodules

```bash
git submodule add https://github.com/michaelrsweet/pappl.git third_party/pappl
git submodule add https://github.com/koenkooi/gutenprint.git third_party/gutenprint
```

Pin PAPPL to tag `v1.4.8` in `.gitmodules` or after adding the submodule.
