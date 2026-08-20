/*
 * PAPPL driver callbacks for Canon i9950.
 *
 * Copyright (C) 2026 i9950 driver project
 * SPDX-License-Identifier: GPL-2.0-or-later
 */

#ifndef I9950_DRIVER_H
#define I9950_DRIVER_H

#include <pappl/pappl.h>

#ifdef __cplusplus
extern "C" {
#endif

const char *i9950_autoadd(const char *device_info,
                          const char *device_uri,
                          const char *device_id,
                          void       *data);

bool i9950_driver_callback(pappl_system_t *system,
                           const char *driver_name,
                           const char *device_uri,
                           const char *device_id,
                           pappl_pr_driver_data_t *driver_data,
                           ipp_t **driver_attrs,
                           void *data);

bool i9950_rstartjob(pappl_job_t *job, pappl_pr_options_t *options,
                     pappl_device_t *device);
bool i9950_rstartpage(pappl_job_t *job, pappl_pr_options_t *options,
                      pappl_device_t *device, unsigned page);
bool i9950_rwriteline(pappl_job_t *job, pappl_pr_options_t *options,
                      pappl_device_t *device, unsigned y,
                      const unsigned char *line);
bool i9950_rendpage(pappl_job_t *job, pappl_pr_options_t *options,
                    pappl_device_t *device, unsigned page);
bool i9950_rendjob(pappl_job_t *job, pappl_pr_options_t *options,
                   pappl_device_t *device);
bool i9950_status(pappl_printer_t *printer);

int               i9950_driver_count(void);
pappl_pr_driver_t *i9950_drivers_list(void);

#ifdef __cplusplus
}
#endif

#endif /* !I9950_DRIVER_H */
