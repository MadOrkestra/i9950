# macOS packaging notes

## End-user install (GitHub Release)

Download `i9950-printer-app-X.Y.Z-macos.pkg` from [GitHub Releases](https://github.com/MadOrkestra/i9950/releases). Install steps are in the root [README.md](../../README.md).

## Local build install (unsigned)

For developers building from source, see [docs/12-developer-guide.md](../../docs/12-developer-guide.md).

## GitHub releases

Tagged releases (`vX.Y.Z`) publish `i9950-printer-app-X.Y.Z-macos.pkg` via [scripts/release.sh](../../scripts/release.sh) on macOS. Release pages include SemVer metadata, changelog changes/improvements, and install steps. Author those details in [CHANGELOG.md](../../CHANGELOG.md); process is documented in [docs/10-release-process.md](../../docs/10-release-process.md).

## Distribution

Production releases require:

1. Apple Developer ID Application certificate
2. `codesign` on binaries
3. `notarytool` notarization
4. Staple notarization ticket to `.pkg`

## No printer yet

The package installs software only. Physical printing validation happens after connecting the Canon i9950 via USB.
