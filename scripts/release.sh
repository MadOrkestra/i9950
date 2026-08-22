#!/usr/bin/env bash
# Build the macOS package and publish a complete GitHub Release (tag, notes, asset).
#
# Usage:
#   ./scripts/release.sh <version> [options]
#
# Options:
#   --dry-run      Validate and print notes; do not tag, push, or publish
#   --skip-build   Do not build locally; publish notes + tag and let CI attach the .pkg
#   --yes          Skip the interactive confirmation prompt
#   --no-push      Create the local tag (and optional local release draft) without pushing
#
# Prerequisites:
#   - CHANGELOG.md has a "## [X.Y.Z] - YYYY-MM-DD" section (see docs/10-release-process.md)
#   - Clean git working tree (Makefile VERSION may be updated by this script)
#   - gh authenticated (`gh auth status`)
#   - macOS + build deps when building (default)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

VERSION=""
DRY_RUN=0
SKIP_BUILD=0
ASSUME_YES=0
NO_PUSH=0

usage() {
  sed -n '2,17p' "$0" | sed 's/^# \{0,1\}//'
  exit "${1:-0}"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage 0 ;;
    --dry-run) DRY_RUN=1; shift ;;
    --skip-build) SKIP_BUILD=1; shift ;;
    --yes|-y) ASSUME_YES=1; shift ;;
    --no-push) NO_PUSH=1; shift ;;
    -*)
      echo "error: unknown option: $1" >&2
      usage 1
      ;;
    *)
      if [[ -n "$VERSION" ]]; then
        echo "error: unexpected argument: $1" >&2
        usage 1
      fi
      VERSION="$1"
      shift
      ;;
  esac
done

if [[ -z "$VERSION" ]]; then
  echo "error: version required (e.g. 0.1.0)" >&2
  usage 1
fi

if [[ ! "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+([.-][0-9A-Za-z.-]+)?$ ]]; then
  echo "error: version '${VERSION}' is not SemVer-like (expected MAJOR.MINOR.PATCH)" >&2
  exit 1
fi

TAG="v${VERSION}"
ASSET_NAME="i9950-printer-app-${VERSION}-macos.pkg"
ASSET_PATH="$ROOT/build/${ASSET_NAME}"
NOTES_FILE="$(mktemp)"
trap 'rm -f "$NOTES_FILE"' EXIT

die() { echo "error: $*" >&2; exit 1; }

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "missing required command: $1"
}

need_cmd git
need_cmd gh

echo "=== i9950 release ${VERSION} ==="

# --- Makefile VERSION --------------------------------------------------------
MAKE_VERSION="$(grep '^VERSION' Makefile | awk '{print $3}')"
if [[ "$MAKE_VERSION" != "$VERSION" ]]; then
  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "[dry-run] would update Makefile VERSION: ${MAKE_VERSION} → ${VERSION}"
  else
    echo "Updating Makefile VERSION: ${MAKE_VERSION} → ${VERSION}"
    if [[ "$(uname)" == Darwin ]]; then
      sed -i '' -E "s/^(VERSION[[:space:]]*\\?=[[:space:]]*).*/\\1${VERSION}/" Makefile
    else
      sed -i -E "s/^(VERSION[[:space:]]*\\?=[[:space:]]*).*/\\1${VERSION}/" Makefile
    fi
  fi
fi

# --- Changelog / notes -------------------------------------------------------
./scripts/generate-release-notes.sh "$VERSION" > "$NOTES_FILE"
echo
echo "----- release notes -----"
cat "$NOTES_FILE"
echo "-------------------------"
echo

# --- Working tree ------------------------------------------------------------
# Allow only Makefile as an unstaged/staged change from the VERSION bump.
dirty="$(git status --porcelain)"
if [[ -n "$dirty" ]]; then
  other="$(echo "$dirty" | awk '$2 != "Makefile" {print}')"
  if [[ -n "$other" ]]; then
    if [[ "$DRY_RUN" -eq 1 ]]; then
      echo "warning: working tree is dirty (ignored for --dry-run):" >&2
      echo "$other" >&2
    else
      echo "$dirty" >&2
      die "working tree is dirty; commit or stash changes before releasing"
    fi
  fi
fi

# --- Confirm -----------------------------------------------------------------
if [[ "$ASSUME_YES" -eq 0 && "$DRY_RUN" -eq 0 ]]; then
  read -r -p "Publish GitHub release ${TAG}? [y/N] " reply
  [[ "$reply" =~ ^[Yy]$ ]] || die "aborted"
fi

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "[dry-run] would tag ${TAG}, build/publish ${ASSET_NAME}, and push to origin"
  exit 0
fi

# --- Commit VERSION bump if needed -------------------------------------------
if ! git diff --quiet -- Makefile || ! git diff --cached --quiet -- Makefile; then
  git add Makefile
  git commit -m "chore: bump version to ${VERSION}"
  echo "Committed Makefile VERSION bump"
fi

# --- Build -------------------------------------------------------------------
if [[ "$SKIP_BUILD" -eq 0 ]]; then
  [[ "$(uname)" == Darwin ]] || die "building the .pkg requires macOS (use --skip-build to publish notes/tag only)"
  echo "Building package..."
  make package VERSION="$VERSION"
  cp "$ROOT/build/i9950-printer-app.pkg" "$ASSET_PATH"
  echo "Built ${ASSET_PATH}"
else
  echo "Skipping local build; CI will attach the .pkg after the tag is pushed"
fi

# --- Tag ---------------------------------------------------------------------
if git rev-parse "$TAG" >/dev/null 2>&1; then
  existing="$(git rev-list -n1 "$TAG")"
  head="$(git rev-list -n1 HEAD)"
  [[ "$existing" == "$head" ]] || die "tag ${TAG} already exists on a different commit"
  echo "Tag ${TAG} already points at HEAD"
else
  git tag -a "$TAG" -m "i9950 Printer Application ${VERSION}"
  echo "Created annotated tag ${TAG}"
fi

# --- Push --------------------------------------------------------------------
if [[ "$NO_PUSH" -eq 1 ]]; then
  echo "Skipping push (--no-push)"
else
  branch="$(git rev-parse --abbrev-ref HEAD)"
  [[ "$branch" != "HEAD" ]] || die "detached HEAD; check out a branch before releasing"
  echo "Pushing ${branch} and ${TAG} to origin..."
  git push origin "$branch"
  git push origin "$TAG"
fi

# --- GitHub Release ----------------------------------------------------------
publish_args=(
  "$TAG"
  --title "i9950 Printer Application ${VERSION}"
  --notes-file "$NOTES_FILE"
)

if [[ "$NO_PUSH" -eq 1 ]]; then
  publish_args+=(--draft --target "$(git rev-parse HEAD)")
fi

if [[ "$SKIP_BUILD" -eq 0 ]]; then
  publish_args+=("$ASSET_PATH")
fi

if gh release view "$TAG" >/dev/null 2>&1; then
  echo "Release ${TAG} already exists; updating notes and assets..."
  gh release edit "$TAG" --title "i9950 Printer Application ${VERSION}" --notes-file "$NOTES_FILE"
  if [[ "$SKIP_BUILD" -eq 0 ]]; then
    gh release upload "$TAG" "$ASSET_PATH" --clobber
  fi
else
  echo "Creating GitHub Release ${TAG}..."
  gh release create "${publish_args[@]}"
fi

url="$(gh release view "$TAG" --json url -q .url 2>/dev/null || true)"
echo
echo "=== release published ==="
echo "Tag:     ${TAG}"
[[ "$SKIP_BUILD" -eq 0 ]] && echo "Package: ${ASSET_NAME}"
[[ -n "$url" ]] && echo "URL:     ${url}"
if [[ "$SKIP_BUILD" -eq 1 && "$NO_PUSH" -eq 0 ]]; then
  echo "Watch CI package build: gh run watch"
fi
