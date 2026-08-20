/*
 * Canon i9950 maintenance utility (USB via libusb).
 *
 * Requires a connected printer (VID 04A9, PID 1090).
 * Without hardware, use --dry-run to inspect commands.
 *
 * Copyright (C) 2026 i9950 driver project
 * SPDX-License-Identifier: GPL-2.0-or-later
 */

#include <libusb-1.0/libusb.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CANON_VID 0x04a9
#define I9950_PID 0x1090

static const unsigned char bjl_init[] =
  "BJLSTART\nControlMode=Common\nSetTime=00000000000000\nBJLEND\n";

static int
find_i9950(libusb_device ***list_out)
{
  libusb_device **list;
  ssize_t         count;
  libusb_device **matches = NULL;
  size_t          n = 0, cap = 0;
  int             i;

  count = libusb_get_device_list(NULL, &list);
  if (count < 0)
    return (int)count;

  for (i = 0; i < count; i++)
  {
    struct libusb_device_descriptor desc;

    if (libusb_get_device_descriptor(list[i], &desc) != 0)
      continue;
    if (desc.idVendor == CANON_VID && desc.idProduct == I9950_PID)
    {
      if (n >= cap)
      {
        cap = cap ? cap * 2 : 4;
        matches = realloc(matches, cap * sizeof(*matches));
      }
      matches[n++] = list[i];
    }
  }

  libusb_free_device_list(list, 1);
  *list_out = matches;
  return (int)n;
}

static void
usage(const char *prog)
{
  printf("Usage: %s [--dry-run] <command>\n\n", prog);
  printf("Commands:\n");
  printf("  list         List matching USB devices\n");
  printf("  nozzle-check Send nozzle check (experimental)\n");
  printf("  head-clean   Send head cleaning (experimental)\n");
  printf("\nNo printer connected? Use --dry-run to print bytes only.\n");
}

int
main(int argc, char *argv[])
{
  const char *cmd;
  int         dry_run = 0;
  int         i;

  if (argc < 2)
  {
    usage(argv[0]);
    return 1;
  }

  for (i = 1; i < argc; i++)
  {
    if (!strcmp(argv[i], "--dry-run"))
      dry_run = 1;
  }

  cmd = argv[argc - 1];

  if (!strcmp(cmd, "list"))
  {
    libusb_device **matches;
    int             n;

    if (libusb_init(NULL) != 0)
    {
      fprintf(stderr, "libusb_init failed\n");
      return 1;
    }

    n = find_i9950(&matches);
    if (n <= 0)
    {
      printf("No Canon i9950 (04A9:1090) found on USB.\n");
      libusb_exit(NULL);
      return 0;
    }

    printf("Found %d device(s):\n", n);
    for (i = 0; i < n; i++)
    {
      struct libusb_device_descriptor desc;

      libusb_get_device_descriptor(matches[i], &desc);
      printf("  Bus %03u Device %03u  ID %04x:%04x\n",
             libusb_get_bus_number(matches[i]),
             libusb_get_device_address(matches[i]),
             desc.idVendor, desc.idProduct);
    }

    free(matches);
    libusb_exit(NULL);
    return 0;
  }

  if (dry_run)
  {
    printf("[dry-run] Would send BJL init (%zu bytes)\n", sizeof(bjl_init) - 1);
    if (!strcmp(cmd, "nozzle-check") || !strcmp(cmd, "head-clean"))
      printf("[dry-run] Maintenance command '%s' not yet reverse-engineered.\n", cmd);
    return 0;
  }

  fprintf(stderr, "No printer actions without hardware. Connect i9950 or use --dry-run.\n");
  return 1;
}
