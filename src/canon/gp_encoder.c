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

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define I9950_DRIVER_NAME "bjc-i9950"

#ifndef I9950_GUTENPRINT_XMLDIR
#define I9950_GUTENPRINT_XMLDIR ""
#endif

static int
i9950_gp_ensure_init(void)
{
  static int ready = 0;

  if (ready)
    return 0;

  if (!getenv("STP_DATA_PATH"))
    setenv("STP_DATA_PATH", I9950_GUTENPRINT_XMLDIR, 0);

  if (stp_init() != 0)
    return -1;

  if (!stp_get_printer_by_driver(I9950_DRIVER_NAME) &&
      !stp_get_printer_by_driver("bjc-i9900"))
    return -1;

  ready = 1;
  return 0;
}

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
  int                 mono;            /* 1-byte mono page */
  int                 zero_is_white;   /* PAPPL K/W: 0=white; sGray: 0=black */
};

static void
gp_write(void *data, const char *buf, size_t bytes)
{
  pappl_device_t *device = (pappl_device_t *)data;

  if (device && bytes > 0)
    papplDeviceWrite(device, buf, bytes);
}

static void
gp_err(void *data, const char *buf, size_t bytes)
{
  (void)data;

  if (buf && bytes > 0)
    fwrite(buf, 1, bytes, stderr);
}

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
  i9950_gp_job_t *gp = (i9950_gp_job_t *)image->rep;

  return gp ? (int)gp->width : 0;
}

static int
raster_height(stp_image_t *image)
{
  i9950_gp_job_t *gp = (i9950_gp_job_t *)image->rep;

  return gp ? (int)gp->height : 0;
}

static stp_image_status_t
raster_get_row(stp_image_t *image, unsigned char *data, size_t byte_limit, int row)
{
  i9950_gp_job_t      *gp = (i9950_gp_job_t *)image->rep;
  const unsigned char *src;

  if (!gp || row < 0 || !data)
    return STP_IMAGE_STATUS_ABORT;

  if ((unsigned)row >= gp->height)
    return STP_IMAGE_STATUS_ABORT;

  src = gp->rows + ((size_t)row * gp->row_bytes);
  memcpy(data, src, byte_limit < gp->row_bytes ? byte_limit : gp->row_bytes);
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
  int                 media_w, media_h, left, right, bottom, top;

  (void)h;

  printer = stp_get_printer_by_driver(I9950_DRIVER_NAME);
  if (!printer)
    printer = stp_get_printer_by_driver("bjc-i9900");

  stp_set_driver(gp->vars, I9950_DRIVER_NAME);
  if (printer)
    stp_set_printer_defaults(gp->vars, printer);

  stp_set_string_parameter(gp->vars, "JobMode", "Page");

  /* i9950/i9900 Gutenprint modes are all 600 dpi; names are not "600x600". */
  if (options->print_quality == IPP_QUALITY_DRAFT)
    snprintf(resbuf, sizeof(resbuf), "600x600dpi_draft");
  else if (options->print_quality == IPP_QUALITY_HIGH)
    snprintf(resbuf, sizeof(resbuf), "600x600dpi_high2");
  else
    snprintf(resbuf, sizeof(resbuf), "600x600dpi");
  stp_set_string_parameter(gp->vars, "Resolution", resbuf);

  if (options->media.type[0])
  {
    if (!strcmp(options->media.type, "photographic-glossy"))
      stp_set_string_parameter(gp->vars, "MediaType", "GlossyPaper");
    else if (!strcmp(options->media.type, "photographic-matte"))
      stp_set_string_parameter(gp->vars, "MediaType", "PhotopaperMatte");
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

  stp_get_media_size(gp->vars, &media_w, &media_h);
  if (media_w > 0)
    stp_set_page_width(gp->vars, media_w);
  if (media_h > 0)
    stp_set_page_height(gp->vars, media_h);

  stp_get_imageable_area(gp->vars, &left, &right, &bottom, &top);
  if (right > left && bottom > top)
  {
    stp_set_width(gp->vars, right - left);
    stp_set_height(gp->vars, bottom - top);
    stp_set_left(gp->vars, left);
    stp_set_top(gp->vars, top);
  }

  /*
   * InputImageType must match bytes/pixel AND polarity.
   * PAPPL mono JPEG/PNG writes CUPS_CSPACE_K with 0=white (it inverts
   * photographic gray with ~pixel). That is Gutenprint Whitescale, not
   * Grayscale (0=black). Using Grayscale floods the page with black ink.
   */
  gp->mono = 0;
  gp->zero_is_white = 0;
  switch (options->header.cupsColorSpace)
  {
    case CUPS_CSPACE_W : /* DeviceGray, 0=white */
    case CUPS_CSPACE_K : /* PAPPL Black, 0=white (amount of ink inverted) */
      stp_set_string_parameter(gp->vars, "PrintingMode", "BW");
      stp_set_string_parameter(gp->vars, "InputImageType", "Whitescale");
      gp->mono = 1;
      gp->zero_is_white = 1;
      break;
    case CUPS_CSPACE_SW: /* sGray, 0=black */
      stp_set_string_parameter(gp->vars, "PrintingMode", "BW");
      stp_set_string_parameter(gp->vars, "InputImageType", "Grayscale");
      gp->mono = 1;
      gp->zero_is_white = 0;
      break;
    case CUPS_CSPACE_CMYK :
      stp_set_string_parameter(gp->vars, "PrintingMode", "Color");
      stp_set_string_parameter(gp->vars, "InputImageType", "CMYK");
      break;
    case CUPS_CSPACE_KCMY :
      stp_set_string_parameter(gp->vars, "PrintingMode", "Color");
      stp_set_string_parameter(gp->vars, "InputImageType", "KCMY");
      break;
    default :
      stp_set_string_parameter(gp->vars, "PrintingMode", "Color");
      stp_set_string_parameter(gp->vars, "InputImageType", "RGB");
      break;
  }

  /* PAPPL often reports 0 margins; borderless is only valid on photo media. */
  if (options->media.type[0] &&
      !strncmp(options->media.type, "photographic-", 13) &&
      options->media.bottom_margin == 0 &&
      options->media.top_margin == 0 &&
      options->media.left_margin == 0 &&
      options->media.right_margin == 0)
    stp_set_boolean_parameter(gp->vars, "Borderless", 1);
  else
    stp_set_boolean_parameter(gp->vars, "Borderless", 0);

}

i9950_gp_job_t *
i9950_gp_job_create(pappl_job_t *job, pappl_device_t *device)
{
  i9950_gp_job_t *gp;

  if (i9950_gp_ensure_init() != 0)
  {
    papplLogJob(job, PAPPL_LOGLEVEL_ERROR,
                "Gutenprint init failed (set STP_DATA_PATH to gutenprint XML).");
    return NULL;
  }

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
  stp_set_errfunc(gp->vars, gp_err);
  stp_set_outdata(gp->vars, device);
  stp_set_errdata(gp->vars, job);

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

  /*
   * Ink-safety gate: sparse mono fixtures are <<5% inked. A polarity bug
   * turns that into ~95%+ black. Refuse to print unless overridden.
   */
  if (gp->mono && gp->rows && gp->width && gp->height &&
      !getenv("I9950_ALLOW_HIGH_INK"))
  {
    size_t i, n = (size_t)gp->width * (size_t)gp->height;
    size_t ink = 0;
    const unsigned char *p = gp->rows;

    for (i = 0; i < n; i++)
    {
      if (gp->zero_is_white)
      {
        if (p[i] > 64)
          ink++;
      }
      else if (p[i] < 192)
        ink++;
    }

    papplLogJob(gp->job, PAPPL_LOGLEVEL_INFO,
                "Mono ink estimate: %.2f%% (%zu / %zu pixels).",
                100.0 * (double)ink / (double)n, ink, n);

    if (ink * 100 > n * 8) /* >8% inked */
    {
      papplLogJob(gp->job, PAPPL_LOGLEVEL_ERROR,
                  "Aborting page: mono ink coverage %.1f%% exceeds 8%% safety "
                  "limit (refuses full-page black floods). Set I9950_ALLOW_HIGH_INK=1 "
                  "to override.",
                  100.0 * (double)ink / (double)n);
      gp->page_open = 0;
      return -1;
    }
  }

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
