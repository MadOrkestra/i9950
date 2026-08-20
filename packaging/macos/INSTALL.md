# macOS packaging notes

## Development install (unsigned)

```bash
make package
sudo installer -pkg build/i9950-printer-app.pkg -target /
```

Loads LaunchAgent `com.i9950.printer-app` to run `i9950-printer-app serve` at login.

## Distribution

Production releases require:

1. Apple Developer ID Application certificate
2. `codesign` on binaries
3. `notarytool` notarization
4. Staple notarization ticket to `.pkg`

## No printer yet

The package installs software only. Physical printing validation happens after connecting the Canon i9950 via USB.
