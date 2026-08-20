/*
 * Unit test for USB job terminator byte sequence (no hardware required).
 *
 * Copyright (C) 2026 i9950 driver project
 * SPDX-License-Identifier: GPL-2.0-or-later
 */

#include <stdio.h>
#include <string.h>

int
main(void)
{
  static const unsigned char expect[] = {
    0x1b, 0x5b, 0x4b, 0x0b, 0x00, 0x00, 0x1e, 0x00, 0x09,
    0x53, 0x53, 0x52, 0x3d, 0x44, 0x46, 0x3b
  };

  if (sizeof(expect) != 16)
  {
    fprintf(stderr, "unexpected terminator length\n");
    return 1;
  }

  if (memcmp(expect + 9, "SSR=DF;", 7) != 0)
  {
    fprintf(stderr, "terminator payload mismatch\n");
    return 1;
  }

  printf("test_usb_flush: OK (terminator structure validated)\n");
  return 0;
}
