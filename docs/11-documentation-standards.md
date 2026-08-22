# Documentation Standards — SemVer and Version History

> **Doc version:** `1.0.0` · **Last updated:** 2026-08-22

Conventions for every Markdown file under [`docs/`](.). **Software** SemVer (`Makefile` / GitHub Releases) is separate; see [10-release-process.md](10-release-process.md). This document covers **document** SemVer only.

## Why document versions

Docs drift. A SemVer on each file and a history table at the end make it obvious what changed, when, and whether a reader should re-read after a bump.

## Document SemVer rules

Use `MAJOR.MINOR.PATCH` on the **document**, independent of the driver release version:

| Component | Bump when |
|-----------|-----------|
| **MAJOR** | Structure or guidance changes that invalidate prior reading (removed sections, reversed recommendations, renumbered meaning) |
| **MINOR** | New sections, substantial facts, new procedures, or expanded matrices |
| **PATCH** | Typos, wording clarifications, link fixes, formatting, metadata-only edits |

Rules:

1. Every `docs/**/*.md` file (including this one and `sources/`) carries a SemVer and a version history.
2. The version in the header **must** match the latest row in the version history table.
3. `Last updated` is the date of the latest history row (`YYYY-MM-DD`).
4. Do not leave “Unreleased” in a doc history — bump and date when you merge the change.
5. Driver releases do **not** automatically bump every doc. Only bump docs you actually change.

## Required template (new and existing files)

Apply this shape to **new** docs and retrofit **existing** docs the same way.

```markdown
# Document Title

> **Doc version:** `1.0.0` · **Last updated:** YYYY-MM-DD

One-line purpose (optional).

## First section

…

---

## Version history

Document SemVer (`MAJOR.MINOR.PATCH`). See [11-documentation-standards.md](11-documentation-standards.md).

| Version | Date | Notes |
|---------|------|-------|
| 1.0.0 | YYYY-MM-DD | Initial document |
```

### Header line

Place the blockquote **immediately under the H1 title** (before any other content):

```markdown
> **Doc version:** `X.Y.Z` · **Last updated:** YYYY-MM-DD
```

### Version history section

Place **at the end** of the file, after a horizontal rule:

- Heading must be exactly `## Version history`
- Intro line points at this standards doc (adjust relative path from `sources/` to `../11-documentation-standards.md`)
- Table columns: `Version` | `Date` | `Notes`
- Newest version at the **top** of the table (same order as Keep a Changelog)

### Notes column

Write for a future reader: what changed and why it matters. Prefer concrete phrases (“Added USB endpoint table”) over “Updates”.

## Checklist for editing a doc

1. Make the content change.
2. Decide MAJOR / MINOR / PATCH using the table above.
3. Add a new top row to **Version history**.
4. Update the header `Doc version` and `Last updated` to match.
5. If the file is new, start at `1.0.0` and add it to [README.md](README.md).

## Checklist for adding a new doc

1. Copy the template above.
2. Choose the next numeric prefix if it is a top-level research doc (`12-…`), or place under `sources/` / a subfolder as appropriate.
3. Start at **Doc version `1.0.0`**.
4. Link it from [README.md](README.md).
5. Keep software release notes in [CHANGELOG.md](../CHANGELOG.md) — doc history does not replace the product changelog.

## Relationship to product releases

| Artifact | Version scheme | Source of truth |
|----------|----------------|-----------------|
| Driver / `.pkg` | Product SemVer | `Makefile` `VERSION`, [CHANGELOG.md](../CHANGELOG.md) |
| Each `docs/*.md` file | Document SemVer | Header + **Version history** in that file |
| This standards doc | Document SemVer | Same template as every other doc |

A product `v0.2.0` release may leave most docs at `1.0.0` if only code changed. When release process docs change, bump [10-release-process.md](10-release-process.md) only.

## Examples

**Patch** — fix a broken URL in the bibliography → `1.0.0` → `1.0.1`.

**Minor** — add a new capture workflow section to the RE guide → `1.0.0` → `1.1.0`.

**Major** — replace the recommended architecture with a different stack → `1.x` → `2.0.0`, with a history note that prior architecture guidance is obsolete.

---

## Version history

Document SemVer (`MAJOR.MINOR.PATCH`). See [11-documentation-standards.md](11-documentation-standards.md).

| Version | Date | Notes |
|---------|------|-------|
| 1.0.0 | 2026-08-22 | Initial documentation standards: SemVer rules, required header, end-of-file version history template |
