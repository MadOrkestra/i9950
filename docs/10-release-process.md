# Release Process — Versioning, Changelog, and GitHub Releases

> **Doc version:** `1.1.0` · **Last updated:** 2026-08-22

How this project versions builds, records changes, and publishes the macOS driver package on GitHub.

## Versioning

We use **Semantic Versioning** (`MAJOR.MINOR.PATCH`):

| Component | When to bump |
|-----------|----------------|
| **MAJOR** | Incompatible changes (install layout, IPP/driver identity, breaking CLI flags) |
| **MINOR** | New capabilities in a compatible way (media modes, maintenance commands, better encoding) |
| **PATCH** | Bug fixes and small improvements that do not change the public contract |

Rules:

1. The release version is the tag **without** the leading `v` (tag `v0.2.0` → version `0.2.0`).
2. `VERSION` in the root [Makefile](../Makefile) must match the release version before you tag.
3. The same version is embedded in binaries (`-DI9950_VERSION`) and in the `.pkg` metadata.
4. Pre-releases use a suffix on the tag only when needed (e.g. `v0.2.0-rc.1`); prefer shipping `Unreleased` notes into a normal `MAJOR.MINOR.PATCH` when ready.

**Document** SemVer (each file under `docs/`) is separate from this product scheme. See [11-documentation-standards.md](11-documentation-standards.md).

## Changelog (source of truth for release notes)

[CHANGELOG.md](../CHANGELOG.md) is the **only** place release-page change detail is authored.

### Required sections per release

Each released version must have a heading:

```markdown
## [X.Y.Z] - YYYY-MM-DD
```

Under that heading, use Keep a Changelog categories as applicable:

| Section | Use for |
|---------|---------|
| **Added** | New features, commands, package contents |
| **Changed** | Behavior or defaults that stay compatible |
| **Fixed** | Bug fixes |
| **Removed** | Removed APIs, options, or install paths |
| **Security** | Security-related fixes |
| **Known limitations** | Hardware blockers, unsigned package caveats, incomplete validation |

Keep an **`## [Unreleased]`** section at the top. Move its bullets into the new `## [X.Y.Z]` block when cutting a release (do not leave the same items in both places).

### What belongs in the changelog

- User-visible improvements and fixes
- Packaging / install changes
- Notable dependency pins (e.g. PAPPL tag) when they affect builds or behavior

Omit routine internal refactors unless they change behavior or risk.

## GitHub Release page content

[scripts/release.sh](../scripts/release.sh) builds the package locally on macOS, then publishes a GitHub Release via `gh`. Release notes come from [scripts/generate-release-notes.sh](../scripts/generate-release-notes.sh).

Every release page includes:

1. **Version** — SemVer and git tag
2. **Changes** — the matching `CHANGELOG.md` section (added / changed / fixed / …)
3. **Install** — `installer` + LaunchAgent load commands for the attached `.pkg`
4. **Signing status** — unsigned vs notarized expectations (see [packaging/macos/INSTALL.md](../packaging/macos/INSTALL.md))

If the changelog has no `## [X.Y.Z]` section, the release script **fails**. Add the section before tagging.

## Cut a release (preferred)

Author the changelog section first, then run:

```bash
./scripts/release.sh X.Y.Z
```

That script:

1. Ensures `Makefile` `VERSION` matches `X.Y.Z` (commits the bump if needed)
2. Validates `CHANGELOG.md` and prints the GitHub Release notes
3. Builds `build/i9950-printer-app-X.Y.Z-macos.pkg` (macOS)
4. Creates annotated tag `vX.Y.Z`
5. Pushes the branch and tag to `origin`
6. Publishes the GitHub Release with notes + `.pkg` via `gh`

Useful flags: `--dry-run`, `--yes`, `--no-push`.

### Manual checklist (without the script)

1. Move items from `## [Unreleased]` into a new `## [X.Y.Z] - YYYY-MM-DD` in `CHANGELOG.md`.
2. Set `VERSION ?= X.Y.Z` in the Makefile.
3. Commit on the release branch/main.
4. Tag and push:

   ```bash
   git tag -a vX.Y.Z -m "i9950 Printer Application X.Y.Z"
   git push origin vX.Y.Z
   ```

5. Confirm the GitHub Release page shows changelog + install notes and the `.pkg` asset is attached.
6. Smoke-install the attached `.pkg` on a clean macOS host when practical; update [09-test-results.md](09-test-results.md) if results change.

## Related files

| Path | Role |
|------|------|
| [CHANGELOG.md](../CHANGELOG.md) | Human-authored changes and improvements |
| [Makefile](../Makefile) `VERSION` | Default / documented project version |
| [packaging/macos/build-pkg.sh](../packaging/macos/build-pkg.sh) | Builds the `.pkg`; respects `VERSION` |
| [scripts/generate-release-notes.sh](../scripts/generate-release-notes.sh) | Builds the GitHub Release markdown body |
| [scripts/release.sh](../scripts/release.sh) | End-to-end: validate, build, tag, push, publish |
| [11-documentation-standards.md](11-documentation-standards.md) | Doc SemVer + version-history template (not product SemVer) |

---

## Version history

Document SemVer (`MAJOR.MINOR.PATCH`). See [11-documentation-standards.md](11-documentation-standards.md).

| Version | Date | Notes |
|---------|------|-------|
| 1.1.0 | 2026-08-22 | Clarify product vs document SemVer; link documentation standards |
| 1.0.0 | 2026-08-22 | Initial release process: product SemVer, changelog, GitHub Releases |
