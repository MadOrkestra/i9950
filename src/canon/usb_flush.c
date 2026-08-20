/*
 * USB job completion — ensures Canon BJL jobs finalize correctly.
 *
 * Addresses Gutenprint legacy canon:// backend flush bug where the last
 * page of a job hangs because bulk OUT data is not fully delivered before
 * close(). See docs/05-community-issues.md.
 *
 * Copyright (C) 2026 i9950 driver project
 * SPDX-License-Identifier: GPL-2.0-or-later
 */

#include "usb_flush.h"

#include <string.h>

/* Observed job-end pattern from Canon BJL protocol (snorp.dev, Gutenprint). */
static const unsigned char i9950_job_end[] = {
  0x1b, 0x5b, 0x4b, 0x0b, 0x00, 0x00, 0x1e, 0x00, 0x09,
  0x53, 0x53, 0x52, 0x3d, 0x44, 0x46, 0x3b
};

int
i9950_usb_finish_job(pappl_device_t *device)
{
  if (!device)
    return -1;

  if (papplDeviceWrite(device, i9950_job_end, sizeof(i9950_job_end)) < 0)
    return -1;

  papplDeviceFlush(device);
  return 0;
}
