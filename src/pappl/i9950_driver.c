/*
 * PAPPL driver callbacks for Canon i9950.
 *
 * Copyright (C) 2026 i9950 driver project
 * SPDX-License-Identifier: GPL-2.0-or-later
 */

#include "i9950_driver.h"
#include "../canon/gp_encoder.h"

#include <pappl/pappl.h>
#include <pappl/base-private.h>

#include <string.h>

#define I9950_VID "04A9"
#define I9950_PID "1090"

static const char * const i9950_media[] =
{
  "na_letter_8.5x11in",
  "iso_a4_210x297mm",
  "iso_a3_297x420mm",
  "na_ledger_11x17in",
  "na_index-4x6_4x6in",
  "na_5x7_5x7in",
  "custom_max_13x19in",
  "custom_min_3x5in"
};

static pappl_pr_driver_t i9950_drivers[] =
{
  { "canon_i9950", "Canon i9950 Photo Printer" }
};

const char *i9950_autoadd(const char *device_info,
              const char *device_uri,
              const char *device_id,
              void       *data)
{
  (void)data;

  if (device_uri)
  {
    if (strstr(device_uri, "04A9") && strstr(device_uri, "1090"))
      return ("canon_i9950");
    if (strstr(device_uri, "i9950") || strstr(device_uri, "i9900"))
      return ("canon_i9950");
  }

  if (device_info &&
      (strstr(device_info, "i9950") || strstr(device_info, "i9900")))
    return ("canon_i9950");

  if (device_id)
  {
    if (strstr(device_id, "i9950") || strstr(device_id, "i9900"))
      return ("canon_i9950");
    if (strstr(device_id, I9950_VID) && strstr(device_id, I9950_PID))
      return ("canon_i9950");
  }

  return (NULL);
}

bool
i9950_driver_callback(pappl_system_t         *system,
               const char             *driver_name,
               const char             *device_uri,
               const char             *device_id,
               pappl_pr_driver_data_t *driver_data,
               ipp_t                  **driver_attrs,
               void                   *data)
{
  int i;

  (void)device_uri;
  (void)device_id;
  (void)data;

  if (!driver_name || !driver_data || strcmp(driver_name, "canon_i9950"))
    return (false);

  papplLog(system, PAPPL_LOGLEVEL_INFO,
           "Loading Canon i9950 driver (Gutenprint bjc-i9950 backend).");

  driver_data->printfile_cb  = NULL;
  driver_data->rendjob_cb    = i9950_rendjob;
  driver_data->rendpage_cb   = i9950_rendpage;
  driver_data->rstartjob_cb  = i9950_rstartjob;
  driver_data->rstartpage_cb = i9950_rstartpage;
  driver_data->rwriteline_cb = i9950_rwriteline;
  driver_data->status_cb     = i9950_status;

  driver_data->format          = "image/pwg-raster";
  driver_data->orient_default  = IPP_ORIENT_PORTRAIT;
  driver_data->quality_default = IPP_QUALITY_NORMAL;
  driver_data->kind            = PAPPL_KIND_PHOTO | PAPPL_KIND_DOCUMENT;
  driver_data->borderless      = true;
  driver_data->has_supplies    = true;

  driver_data->color_supported = PAPPL_COLOR_MODE_AUTO |
                                 PAPPL_COLOR_MODE_COLOR |
                                 PAPPL_COLOR_MODE_MONOCHROME;
  driver_data->color_default   = PAPPL_COLOR_MODE_COLOR;

  /*
   * Gutenprint bjc-i9950 modes are all native 600 dpi. Advertising 1200/2400
   * makes CUPS PDF filters send huge rasters that we still encode as 600 dpi
   * modes — that mismatch greys sparse mono pages. Re-enable higher DPI only
   * when the encoder maps them to real GP modes / downsamples correctly.
   */
  driver_data->num_resolution = 1;
  driver_data->x_resolution[0] = 600;
  driver_data->y_resolution[0] = 600;
  driver_data->x_default = 600;
  driver_data->y_default = 600;

  driver_data->raster_types = PAPPL_PWG_RASTER_TYPE_BLACK_8 |
                              PAPPL_PWG_RASTER_TYPE_SRGB_8;

  driver_data->num_media = (int)(sizeof(i9950_media) / sizeof(i9950_media[0]));
  memcpy((void *)driver_data->media, i9950_media, sizeof(i9950_media));

  driver_data->num_type = 4;
  driver_data->type[0]  = "stationery";
  driver_data->type[1]  = "photographic-glossy";
  driver_data->type[2]  = "photographic-matte";
  driver_data->type[3]  = "stationery-letterhead";

  driver_data->num_source = 1;
  driver_data->source[0]  = "auto";

  driver_data->left_right = 500; /* 5mm */
  driver_data->bottom_top = 500; /* 5mm */
  driver_data->ppm        = 12;
  driver_data->ppm_color  = 12;

  papplCopyString(driver_data->make_and_model,
                  "Canon i9950",
                  sizeof(driver_data->make_and_model));

  papplCopyString(driver_data->media_default.size_name,
                  "iso_a4_210x297mm",
                  sizeof(driver_data->media_default.size_name));
  papplCopyString(driver_data->media_default.type,
                  "stationery",
                  sizeof(driver_data->media_default.type));
  papplCopyString(driver_data->media_default.source,
                  "auto",
                  sizeof(driver_data->media_default.source));

  for (i = 0; i < driver_data->num_media; i ++)
  {
    pwg_media_t *pwg = pwgMediaForPWG(driver_data->media[i]);

    if (!pwg)
      continue;

    papplCopyString(driver_data->media_ready[i].size_name,
                    driver_data->media[i],
                    sizeof(driver_data->media_ready[i].size_name));
    papplCopyString(driver_data->media_ready[i].type,
                    "stationery",
                    sizeof(driver_data->media_ready[i].type));
    papplCopyString(driver_data->media_ready[i].source,
                    "auto",
                    sizeof(driver_data->media_ready[i].source));
    driver_data->media_ready[i].size_width  = pwg->width;
    driver_data->media_ready[i].size_length = pwg->length;
    driver_data->media_ready[i].left_margin = driver_data->left_right;
    driver_data->media_ready[i].right_margin = driver_data->left_right;
    driver_data->media_ready[i].top_margin = driver_data->bottom_top;
    driver_data->media_ready[i].bottom_margin = driver_data->bottom_top;
  }

  if (driver_attrs)
    *driver_attrs = NULL;

  return (true);
}

bool
i9950_rstartjob(pappl_job_t        *job,
                pappl_pr_options_t *options,
                pappl_device_t     *device)
{
  i9950_gp_job_t *gp;

  (void)options;

  gp = i9950_gp_job_create(job, device);
  if (!gp)
    return (false);

  papplJobSetData(job, gp);
  return (true);
}

bool
i9950_rstartpage(pappl_job_t        *job,
                 pappl_pr_options_t *options,
                 pappl_device_t     *device,
                 unsigned            page)
{
  i9950_gp_job_t *gp = (i9950_gp_job_t *)papplJobGetData(job);

  (void)device;
  (void)page;

  if (!gp || i9950_gp_begin_page(gp, options) != 0)
    return (false);

  return (true);
}

bool
i9950_rwriteline(pappl_job_t        *job,
                 pappl_pr_options_t *options,
                 pappl_device_t     *device,
                 unsigned            y,
                 const unsigned char *line)
{
  i9950_gp_job_t *gp = (i9950_gp_job_t *)papplJobGetData(job);

  (void)options;
  (void)device;

  if (!gp || i9950_gp_write_line(gp, y, line) != 0)
    return (false);

  return (true);
}

bool
i9950_rendpage(pappl_job_t        *job,
               pappl_pr_options_t *options,
               pappl_device_t     *device,
               unsigned            page)
{
  i9950_gp_job_t *gp = (i9950_gp_job_t *)papplJobGetData(job);

  (void)options;
  (void)device;
  (void)page;

  if (!gp || i9950_gp_end_page(gp) != 0)
    return (false);

  return (true);
}

bool
i9950_rendjob(pappl_job_t        *job,
              pappl_pr_options_t *options,
              pappl_device_t     *device)
{
  i9950_gp_job_t *gp = (i9950_gp_job_t *)papplJobGetData(job);

  (void)options;
  (void)device;

  if (gp)
  {
    i9950_gp_end_job(gp);
    i9950_gp_job_destroy(gp);
    papplJobSetData(job, NULL);
  }

  return (true);
}

bool
i9950_status(pappl_printer_t *printer)
{
  static pappl_supply_t supplies[8] =
  {
    { PAPPL_SUPPLY_COLOR_BLACK,         "Black",         true, 100, PAPPL_SUPPLY_TYPE_INK },
    { PAPPL_SUPPLY_COLOR_CYAN,          "Cyan",          true, 100, PAPPL_SUPPLY_TYPE_INK },
    { PAPPL_SUPPLY_COLOR_MAGENTA,       "Magenta",       true, 100, PAPPL_SUPPLY_TYPE_INK },
    { PAPPL_SUPPLY_COLOR_YELLOW,        "Yellow",        true, 100, PAPPL_SUPPLY_TYPE_INK },
    { PAPPL_SUPPLY_COLOR_LIGHT_CYAN,    "Photo Cyan",    true, 100, PAPPL_SUPPLY_TYPE_INK },
    { PAPPL_SUPPLY_COLOR_LIGHT_MAGENTA, "Photo Magenta", true, 100, PAPPL_SUPPLY_TYPE_INK },
    { PAPPL_SUPPLY_COLOR_NO_COLOR,      "Red",           true, 100, PAPPL_SUPPLY_TYPE_INK },
    { PAPPL_SUPPLY_COLOR_NO_COLOR,      "Green",         true, 100, PAPPL_SUPPLY_TYPE_INK }
  };

  (void)printer;

  if (papplPrinterGetSupplies(printer, 0, NULL) == 0)
    papplPrinterSetSupplies(printer, 8, supplies);

  return (true);
}

int
i9950_driver_count(void)
{
  return ((int)(sizeof(i9950_drivers) / sizeof(i9950_drivers[0])));
}

pappl_pr_driver_t *
i9950_drivers_list(void)
{
  return (i9950_drivers);
}
