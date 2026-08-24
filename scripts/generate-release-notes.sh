#!/usr/bin/env bash
# Generate GitHub Release notes from CHANGELOG.md + version metadata.
# Usage: generate-release-notes.sh <version>
# Writes markdown to stdout. Exits non-zero if the changelog section is missing.
set -euo pipefail

VERSION="${1:?usage: $0 <version>}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CHANGELOG="$ROOT/CHANGELOG.md"

if [[ ! -f "$CHANGELOG" ]]; then
  echo "error: missing $CHANGELOG" >&2
  exit 1
fi

# Extract "## [X.Y.Z] ..." through the line before the next "## [" heading.
NOTES="$(awk -v ver="$VERSION" '
  $0 ~ "^## \\[" ver "\\]" {found=1; print; next}
  found && $0 ~ /^## \[/ {exit}
  found {print}
' "$CHANGELOG")"

if [[ -z "$NOTES" ]]; then
  echo "error: no CHANGELOG.md section for version ${VERSION}" >&2
  echo "Add a '## [${VERSION}] - YYYY-MM-DD' heading before tagging. See docs/10-release-process.md." >&2
  exit 1
fi

PKG="i9950-printer-app-${VERSION}-macos.pkg"
REPO="${GITHUB_SERVER_URL:-https://github.com}/${GITHUB_REPOSITORY:-MadOrkestra/i9950}"

cat <<EOF
## Version

| | |
|--|--|
| **Version** | \`${VERSION}\` |
| **Git tag** | \`v${VERSION}\` |
| **Scheme** | [Semantic Versioning](https://semver.org/) (\`MAJOR.MINOR.PATCH\`) |
| **Changelog** | [CHANGELOG.md](${REPO}/blob/v${VERSION}/CHANGELOG.md) |

## Changes

${NOTES}

## macOS package

| | |
|--|--|
| **Asset** | \`${PKG}\` |
| **Signing** | Unsigned development package (Gatekeeper may warn) |

### Install

\`\`\`bash
sudo installer -pkg ${PKG} -target /
launchctl bootstrap gui/$(id -u) /Library/LaunchAgents/com.i9950.printer-app.plist
\`\`\`

Production distribution still requires Developer ID signing and notarization. See \`packaging/macos/INSTALL.md\` and \`docs/10-release-process.md\`.
EOF
