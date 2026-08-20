/*
 * USB job completion helpers for Canon i9950.
 *
 * Copyright (C) 2026 i9950 driver project
 * SPDX-License-Identifier: GPL-2.0-or-later
 */

#ifndef I9950_USB_FLUSH_H
#define I9950_USB_FLUSH_H

#include <pappl/device.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Send Canon job terminator and flush USB buffers (fixes stuck last page). */
int i9950_usb_finish_job(pappl_device_t *device);

#ifdef __cplusplus
}
#endif

#endif /* !I9950_USB_FLUSH_H */
