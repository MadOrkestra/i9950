# macOS packaging notes

## Development install (unsigned)

```bash
make package
sudo installer -pkg build/i9950-printer-app.pkg -target /
```

Loads LaunchAgent `com.i9950.printer-app` to run `i9950-printer-app server` at login.

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
