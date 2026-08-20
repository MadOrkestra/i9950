# IPP / driver capabilities reference

The Canon i9950 Printer Application exposes capabilities via PAPPL IPP attributes
(see `src/pappl/i9950_driver.c`):

- Driver: `canon_i9950`
- Gutenprint backend: `bjc-i9950`
- Resolutions: 600, 1200, 2400, 4800 × 2400 dpi
- Media: Letter, A4, A3, 11×17, 4×6, 5×7, 13×19
- Types: stationery, photographic-glossy, photographic-matte
- Borderless: supported
- Color: color + monochrome

Classic PPD files are not required on modern macOS; the Printer Application
registers via Bonjour/IPP.
