/*
 * macOS menu bar status item for i9950-printer-app.
 *
 * Copyright (C) 2026 i9950 driver project
 * SPDX-License-Identifier: GPL-2.0-or-later
 */

#ifndef I9950_STATUS_BAR_H
#define I9950_STATUS_BAR_H

#include <stdbool.h>

#ifdef __APPLE__

/* Resolve Lucide printer template PNG (installed or build tree). */
const char *i9950_menu_icon_path(void);

/* True when running `server` and menu bar is not disabled. */
bool i9950_status_bar_wanted(int argc, char *argv[]);

/* Install NSStatusItem before papplMainloop (same thread / run loop). */
void i9950_status_bar_init(const char *icon_path, int web_port);

#else

static inline const char *i9950_menu_icon_path(void) { return NULL; }
static inline bool i9950_status_bar_wanted(int argc, char *argv[]) {
  (void)argc; (void)argv;
  return false;
}
static inline void i9950_status_bar_init(const char *icon_path, int web_port) {
  (void)icon_path; (void)web_port;
}

#endif

#endif /* I9950_STATUS_BAR_H */
