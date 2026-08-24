/*
 * Canon i9950 Printer Application (PAPPL).
 *
 * Copyright (C) 2026 i9950 driver project
 * SPDX-License-Identifier: GPL-2.0-or-later
 */

#include "pappl/i9950_driver.h"

#include <pappl/pappl.h>
#include <stdlib.h>

#ifdef __APPLE__
# include "macos/i9950_status_bar.h"
#endif

#ifndef I9950_VERSION
#define I9950_VERSION "0.0.0-dev"
#endif

static bool
i9950_callback(pappl_system_t         *system,
               const char             *driver_name,
               const char             *device_uri,
               const char             *device_id,
               pappl_pr_driver_data_t *driver_data,
               ipp_t                  **driver_attrs,
               void                   *data)
{
  return i9950_driver_callback(system, driver_name, device_uri, device_id,
                               driver_data, driver_attrs, data);
}

int
main(int argc, char *argv[])
{
#ifdef __APPLE__
  if (i9950_status_bar_wanted(argc, argv))
  {
    setenv("I9950_CUSTOM_MENU_BAR", "1", 1);
    i9950_status_bar_init(i9950_menu_icon_path(), 0);
  }
#endif

  return papplMainloop(argc, argv,
                       I9950_VERSION,
                       "Copyright (C) 2026 i9950 driver project. "
                       "Provided under GPL-2.0-or-later.",
                       i9950_driver_count(),
                       i9950_drivers_list(),
                       i9950_autoadd,
                       i9950_callback,
                       NULL, NULL, NULL, NULL, NULL);
}
