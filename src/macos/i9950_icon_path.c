/*
 * Locate menu-bar icon PNG on macOS.
 *
 * Copyright (C) 2026 i9950 driver project
 * SPDX-License-Identifier: GPL-2.0-or-later
 */

#ifdef __APPLE__

#include "i9950_status_bar.h"

#include <mach-o/dyld.h>
#include <stdint.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <libgen.h>

const char *
i9950_menu_icon_path(void)
{
  static char path[PATH_MAX];
  const char *env;

  env = getenv("I9950_ICON_PATH");
  if (env && env[0] && access(env, R_OK) == 0)
    return env;

  if (access("/usr/local/share/i9950/lucide-printer-template.png", R_OK) == 0)
    return "/usr/local/share/i9950/lucide-printer-template.png";

  env = getenv("I9950_BUILD_DIR");
  if (env && env[0])
  {
    snprintf(path, sizeof(path), "%s/share/i9950/lucide-printer-template.png", env);
    if (access(path, R_OK) == 0)
      return path;
  }

  {
    char exe[PATH_MAX];
    uint32_t size = (uint32_t)sizeof(exe);

    if (_NSGetExecutablePath(exe, &size) == 0)
    {
      char *dir = dirname(exe);

      snprintf(path, sizeof(path),
               "%s/share/i9950/lucide-printer-template.png", dir);
      if (access(path, R_OK) == 0)
        return path;

      snprintf(path, sizeof(path),
               "%s/../share/i9950/lucide-printer-template.png", dir);
      if (access(path, R_OK) == 0)
        return path;
    }
  }

  return (NULL);
}

#endif /* __APPLE__ */
