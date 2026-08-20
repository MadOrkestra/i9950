# USB Identification — Canon i9950

## Vendor and Product IDs

| Field | Value |
|-------|-------|
| **Vendor ID (VID)** | `0x04A9` |
| **Product ID (PID)** | `0x1090` |
| **Manufacturer** | Canon, Inc. |
| **Product string** | Canon i9950 (typical) |
| **Windows HW ID** | `USB\VID_04A9&PID_1090` |

**Sources:** [drivers.eu Windows 7](https://drivers.eu/DeviceId/USB%5CVID_04A9%26PID_1090/Windows%207), [drivers.eu macOS](https://drivers.eu/DeviceId/USB%5CVID_04A9%26PID_1090/Mac%20OS%20X)

## Device Class

The i9950 enumerates as a **standard USB Printer Class** device:

- **Interface class:** `0x07` (Printer)
- **No custom kernel driver required** on macOS, Linux, or Windows
- Communication uses USB **bulk transfers** for print data

Unlike Canon SELPHY dye-sublimation printers, the i9950 does **not** require Gutenprint's proprietary `gutenprint52+usb` backend or special handshaking for basic printing.

## Detection on macOS

```bash
# List USB devices
system_profiler SPUSBDataType | grep -A5 -i "9950"

# Alternative (if ioreg available)
ioreg -p IOUSB -l | grep -i "9950"
```

Expected appearance: Canon device with vendor ID 04a9 and product ID 1090.

## Detection on Linux

```bash
lsusb -d 04a9:1090
# Example output:
# Bus 001 Device 005: ID 04a9:1090 Canon, Inc. i9950
```

## CUPS Device URI

When connected via USB, CUPS typically discovers:

```
usb://Canon/i9950?serial=<serial>
```

Or generically:

```
usb://Canon/Canon%20i9950
```

**Important:** Do not use the legacy Gutenprint `canon://` backend URI. Use standard `usb://` URIs with the Printer Application or CUPS usb backend.

## USB Ports on the Printer

The i9950 has **two USB ports**:

1. **USB 2.0 Hi-Speed** — recommended for PC connection (480 Mbps)
2. **USB 2.0 Full Speed** — alternate port (12 Mbps)

Use a certified USB 2.0 Hi-Speed cable, preferably ≤3 meters.

**Source:** [Canon QSG PDF](https://www2.canon.com.hk/myContent/Product_Tab/ColorBubbleJetPrinter/desktopprinter/i9950/i9900_i9950_qsg_eng.pdf)

## Wireshark / Capture Filters

When analyzing USB traffic:

```
usb.idVendor == 0x04a9 && usb.idProduct == 0x1090
```

Bulk transfer data only:

```
usb.idVendor == 0x04a9 && usb.idProduct == 0x1090 && usb.transfer_type == 3
```

Printer class interface:

```
usb.bInterfaceClass == 0x07
```

## Related Canon USB IDs (Not i9950)

Do not confuse with other Canon printers. The i9950 PID is specifically **1090**. Other Bubble Jet models use different PIDs.

## Driver Binding on macOS

Modern macOS (Ventura+) has no inbox driver for this device. When plugged in:

1. System may recognize it as a generic USB printer class device
2. No functional driver is installed automatically
3. Our Printer Application will claim the device via PAPPL USB support and expose it as an IPP Everywhere printer on localhost
