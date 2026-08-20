/*
 * libgutenprint Canon BJC encoder wrapper for Canon i9950.
 *
 * Copyright (C) 2026 i9950 driver project
 * SPDX-License-Identifier: GPL-2.0-or-later
 */

#ifndef I9950_GP_ENCODER_H
#define I9950_GP_ENCODER_H

#include <pappl/device.h>
#include <pappl/job.h>
#include <pappl/printer.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct i9950_gp_job_s i9950_gp_job_t;

i9950_gp_job_t *i9950_gp_job_create(pappl_job_t *job, pappl_device_t *device);
void            i9950_gp_job_destroy(i9950_gp_job_t *gp);

int  i9950_gp_begin_page(i9950_gp_job_t *gp, pappl_pr_options_t *options);
int  i9950_gp_write_line(i9950_gp_job_t *gp, unsigned y, const unsigned char *line);
int  i9950_gp_end_page(i9950_gp_job_t *gp);
int  i9950_gp_end_job(i9950_gp_job_t *gp);

#ifdef __cplusplus
}
#endif

#endif /* !I9950_GP_ENCODER_H */
