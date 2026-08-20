/*
 * Gutenprint-backed Canon i9950 raster encoder.
 *
 * Copyright (C) 2026 i9950 driver project
 * SPDX-License-Identifier: GPL-2.0-or-later
 */

#include "gp_encoder.h"
#include "usb_flush.h"

#include <gutenprint/gutenprint.h>
#include <pappl/log.h>
#include <pappl/base-private.h>

#include <stdlib.h>
#include <string.h>

#define I9950_DRIVER_NAME "bjc-i9950"

struct i9950_gp_job_s
{
  pappl_job_t        *job;
  pappl_device_t     *device;
  stp_vars_t         *vars;
  stp_image_t         image;
  unsigned char      *rows;
  size_t              row_bytes;
  unsigned            width;
  unsigned            height;
  unsigned            current_row;
  int                 page_open;
};

static void
gp_write(void *data, const char *buf, size_t bytes)
{
  pappl_device_t *device = (pappl_device_t *)data;

  if (device && bytes > 0)
    papplDeviceWrite(device, buf, bytes);
}

typedef struct
{
  i9950_gp_job_t *gp;
} raster_image_priv_t;

static void
raster_init(stp_image_t *image)
{
  (void)image;
}

static void
raster_reset(stp_image_t *image)
{
  (void)image;
}

static int
raster_width(stp_image_t *image)
{
  raster_image_priv_t *priv = (raster_image_priv_t *)image->rep;

  return priv ? (int)priv->gp->width : 0;
}

static int
raster_height(stp_image_t *image)
{
  raster_image_priv_t *priv = (raster_image_priv_t *)image->rep;

  return priv ? (int)priv->gp->height : 0;
}

static stp_image_status_t
raster_get_row(stp_image_t *image, unsigned char *data, size_t byte_limit, int row)
{
  raster_image_priv_t *priv = (raster_image_priv_t *)image->rep;
  i9950_gp_job_t      *gp;
  const unsigned char *src;

  if (!priv || row < 0 || !data)
    return STP_IMAGE_STATUS_ABORT;

  gp = priv->gp;
  if ((unsigned)row >= gp->height || byte_limit < gp->row_bytes)
    return STP_IMAGE_STATUS_ABORT;

  src = gp->rows + ((size_t)row * gp->row_bytes);
  memcpy(data, src, gp->row_bytes);
  return STP_IMAGE_STATUS_OK;
}

static const char *
raster_appname(stp_image_t *image)
{
  (void)image;
  return "i9950-printer-app";
}

static void
raster_conclude(stp_image_t *image)
{
  (void)image;
}

static const char *
map_ipp_media_to_pagesize(const char *ipp_name)
{
  if (!ipp_name || !ipp_name[0])
    return NULL;

  if (!strcmp(ipp_name, "na_letter_8.5x11in"))
    return "Letter";
  if (!strcmp(ipp_name, "iso_a4_210x297mm"))
    return "A4";
  if (!strcmp(ipp_name, "iso_a3_297x420mm"))
    return "A3";
  if (!strcmp(ipp_name, "na_ledger_11x17in"))
    return "11x17";
  if (!strcmp(ipp_name, "na_legal_8.5x14in"))
    return "Legal";
  if (!strcmp(ipp_name, "na_index-4x6_4x6in"))
    return "4x6";
  if (!strcmp(ipp_name, "na_5x7_5x7in"))
    return "5x7";
  if (!strcmp(ipp_name, "custom_max_13x19in"))
    return "13x19";

  return NULL;
}

static void
apply_pappl_options(i9950_gp_job_t *gp, pappl_pr_options_t *options)
{
  const stp_printer_t *printer;
  cups_page_header_t  *h = &options->header;
  char                resbuf[32];
  int                 xres = h->cupsWidth ? (int)h->HWResolution[0] : 600;
  int                 yres = h->cupsHeight ? (int)h->HWResolution[1] : 600;
  double              pw, ph;

  printer = stp_get_printer_by_driver(I9950_DRIVER_NAME);
  if (!printer)
    printer = stp_get_printer_by_driver("bjc-i9900");

  stp_set_driver(gp->vars, I9950_DRIVER_NAME);
  if (printer)
    stp_set_printer_defaults(gp->vars, printer);

  stp_set_string_parameter(gp->vars, "JobMode", "Page");

  snprintf(resbuf, sizeof(resbuf), "%dx%d", xres, yres);
  stp_set_string_parameter(gp->vars, "Resolution", resbuf);

  pw = h->cupsWidth * 72.0 / xres;
  ph = h->cupsHeight * 72.0 / yres;
  stp_set_page_width(gp->vars, pw);
  stp_set_page_height(gp->vars, ph);
  stp_set_width(gp->vars, (int)pw);
  stp_set_height(gp->vars, (int)ph);

  if (options->media.type[0])
  {
    if (!strcmp(options->media.type, "photographic-glossy"))
      stp_set_string_parameter(gp->vars, "MediaType", "GlossyFilm");
    else if (!strcmp(options->media.type, "photographic-matte"))
      stp_set_string_parameter(gp->vars, "MediaType", "Matte");
    else if (!strcmp(options->media.type, "stationery"))
      stp_set_string_parameter(gp->vars, "MediaType", "Plain");
    else
      stp_set_string_parameter(gp->vars, "MediaType", "Plain");
  }

  if (options->media.size_name[0])
  {
    const char          *pagesize = map_ipp_media_to_pagesize(options->media.size_name);
    const stp_papersize_t *ps;

    if (pagesize && (ps = stp_get_papersize_by_name(pagesize)) != NULL)
      stp_set_string_parameter(gp->vars, "PageSize", ps->name);
  }

  if (options->header.cupsColorSpace == CUPS_CSPACE_K ||
      options->header.cupsColorSpace == CUPS_CSPACE_W ||
      options->header.cupsColorSpace == CUPS_CSPACE_SW)
    stp_set_string_parameter(gp->vars, "PrintingMode", "Gray");
  else
    stp_set_string_parameter(gp->vars, "PrintingMode", "Color");

  if (options->media.bottom_margin == 0 &&
      options->media.top_margin == 0 &&
      options->media.left_margin == 0 &&
      options->media.right_margin == 0)
    stp_set_boolean_parameter(gp->vars, "Borderless", 1);

}

i9950_gp_job_t *
i9950_gp_job_create(pappl_job_t *job, pappl_device_t *device)
{
  i9950_gp_job_t *gp;

  gp = calloc(1, sizeof(*gp));
  if (!gp)
    return NULL;

  gp->job = job;
  gp->device = device;
  gp->vars = stp_vars_create();
  if (!gp->vars)
  {
    free(gp);
    return NULL;
  }

  stp_set_outfunc(gp->vars, gp_write);
  stp_set_errfunc(gp->vars, gp_write);
  stp_set_outdata(gp->vars, device);
  stp_set_errdata(gp->vars, device);

  gp->image.init = raster_init;
  gp->image.reset = raster_reset;
  gp->image.width = raster_width;
  gp->image.height = raster_height;
  gp->image.get_row = raster_get_row;
  gp->image.get_appname = raster_appname;
  gp->image.conclude = raster_conclude;

  return gp;
}

void
i9950_gp_job_destroy(i9950_gp_job_t *gp)
{
  if (!gp)
    return;

  free(gp->rows);
  if (gp->vars)
    stp_vars_destroy(gp->vars);
  free(gp);
}

int
i9950_gp_begin_page(i9950_gp_job_t *gp, pappl_pr_options_t *options)
{
  cups_page_header_t *h;

  if (!gp || !options)
    return -1;

  h = &options->header;
  gp->width = h->cupsWidth;
  gp->height = h->cupsHeight;
  gp->row_bytes = h->cupsBytesPerLine;
  gp->current_row = 0;

  free(gp->rows);
  gp->rows = calloc(gp->height, gp->row_bytes);
  if (!gp->rows)
    return -1;

  apply_pappl_options(gp, options);

  gp->image.rep = gp;
  gp->page_open = 1;

  return 0;
}

int
i9950_gp_write_line(i9950_gp_job_t *gp, unsigned y, const unsigned char *line)
{
  unsigned char *dest;

  if (!gp || !gp->page_open || !line || y >= gp->height)
    return -1;

  dest = gp->rows + ((size_t)y * gp->row_bytes);
  memcpy(dest, line, gp->row_bytes);
  if (y >= gp->current_row)
    gp->current_row = y + 1;

  return 0;
}

int
i9950_gp_end_page(i9950_gp_job_t *gp)
{
  int status;

  if (!gp || !gp->page_open)
    return -1;

  if (stp_verify(gp->vars) != 1)
  {
    papplLogJob(gp->job, PAPPL_LOGLEVEL_ERROR,
                "Gutenprint parameter verification failed for i9950 page.");
    gp->page_open = 0;
    return -1;
  }

  status = stp_print(gp->vars, &gp->image);
  gp->page_open = 0;

  if (status != 1)
  {
    papplLogJob(gp->job, PAPPL_LOGLEVEL_ERROR,
                "Gutenprint stp_print failed (status=%d).", status);
    return -1;
  }

  papplDeviceFlush(gp->device);
  return 0;
}

int
i9950_gp_end_job(i9950_gp_job_t *gp)
{
  if (!gp)
    return -1;

  i9950_usb_finish_job(gp->device);
  return 0;
}
