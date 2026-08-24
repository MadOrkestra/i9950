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
/* Match driver left_right/bottom_top and fixture MARGIN_MM (5 mm). */
#define I9950_MARGIN_HMM 500

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
  if (byte_limit > gp->row_bytes)
  {
    /* Pad unread bytes as white for current polarity. */
    memset(data, gp->zero_is_white ? 0 : 255, byte_limit);
    memcpy(data, src, gp->row_bytes);
  }
  else
    memcpy(data, src, byte_limit);
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

  printer = stp_get_printer_by_driver(I9950_DRIVER_NAME);
  if (!printer)
    printer = stp_get_printer_by_driver("bjc-i9900");

  stp_set_driver(gp->vars, I9950_DRIVER_NAME);
  if (printer)
    stp_set_printer_defaults(gp->vars, printer);

  stp_set_string_parameter(gp->vars, "JobMode", "Page");

  /*
   * i9950/i9900 Gutenprint modes are all native 600 dpi. Resolution names
   * below are locked by physical prints — see mono and color LOCKED blocks.
   */
  gp->mono = 0;
  gp->zero_is_white = 0;
  switch (options->header.cupsColorSpace)
  {
    case CUPS_CSPACE_W :
    case CUPS_CSPACE_K :
    case CUPS_CSPACE_SW:
      gp->mono = 1;
      break;
    default :
      break;
  }

  if (gp->mono)
  {
    /*
     * LOCKED (Job 38 PASS — t-printable-a4-600.png; Job 39 JPG):
     * Black / greyscale-only path. Submit with print-color-mode=monochrome.
     *
     * Resolution: 600x600dpi_draftmono (or _draftmono2 for draft quality).
     *   INKSET 11_K2 = 1-bit K, MODE_FLAG_IP8500 — K cartridge only.
     * PrintingMode=BW, InkSet=Black, InkType=Gray — prevents Color/CMY
     *   wash on white paper.
     * ImageType=LineArt + ColorCorrection=Threshold — sparse text/line art.
     * Polarity (end_page): normalize to 0=white / 255=ink, then always
     *   InputImageType=Grayscale. Never Whitescale (Job 37 inverted).
     *
     * Do NOT send mono through Color / 600x600dpi CMYK modes.
     */
    if (options->print_quality == IPP_QUALITY_DRAFT)
      snprintf(resbuf, sizeof(resbuf), "600x600dpi_draftmono2");
    else
      snprintf(resbuf, sizeof(resbuf), "600x600dpi_draftmono");
    stp_set_string_parameter(gp->vars, "Resolution", resbuf);
    stp_set_string_parameter(gp->vars, "PrintingMode", "BW");
    stp_set_string_parameter(gp->vars, "InkSet", "Black");
    stp_set_string_parameter(gp->vars, "InkType", "Gray");
    stp_set_string_parameter(gp->vars, "ImageType", "LineArt");
    stp_set_string_parameter(gp->vars, "ColorCorrection", "Threshold");
  }
  else
  {
    /*
     * LOCKED (Job 52 PASS — t-color-swatches-a4-600.jpg):
     * Color must use 1-bit IP8500 draft modes, not medium/high multilevel.
     *
     * Failed: "600x600dpi" (INKSET 11_C6M6Y6K6_c = 4-bit) → squares stretch
     * sideways, right frame clips (Jobs 43–51). Adding MODE_FLAG_IP8500 alone
     * did not help — bit packing still mismatched mono draftmono (1-bit K).
     *
     * Works: "600x600dpi_draft" / "_draft2" (INKSET 11_C2M2Y2K2 = 1-bit CMYK,
     * MODE_FLAG_IP8500) — same ESC (t) / bit-depth family as draftmono.
     * Do NOT switch color back to 600x600dpi / high2 / PRO without a new
     * physical geometry gate.
     */
    if (options->print_quality == IPP_QUALITY_DRAFT)
      snprintf(resbuf, sizeof(resbuf), "600x600dpi_draft2");
    else
      snprintf(resbuf, sizeof(resbuf), "600x600dpi_draft");
    stp_set_string_parameter(gp->vars, "Resolution", resbuf);
  }

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

  /*
   * Color: set final PrintingMode/InputImageType before geometry so
   * stp_get_imageable_area() sees the same state as stp_print().
   */
  if (!gp->mono)
  {
    switch (options->header.cupsColorSpace)
    {
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
  }

  /*
   * One geometry for mono/color and PNG/JPG/PDF rasters.
   *
   * Fixtures are drawn for the driver 5 mm printable inset. PAPPL often
   * hands us 0 margins, so Gutenprint's ~3.5 mm imageable box was used
   * instead — that clips the right frame and, when filled independently
   * in X/Y, turns squares into rectangles. Always enforce ≥5 mm and fit
   * the raster with a single scale factor.
   */
  stp_get_imageable_area(gp->vars, &left, &right, &bottom, &top);
  if (right > left && bottom > top)
  {
    int xdpi = h->HWResolution[0] ? (int)h->HWResolution[0] : 600;
    int ydpi = h->HWResolution[1] ? (int)h->HWResolution[1] : 600;
    int raster_w_pt = (int)((h->cupsWidth * 72.0) / xdpi + 0.5);
    int raster_h_pt = (int)((h->cupsHeight * 72.0) / ydpi + 0.5);
    int img_w, img_h;
    int ml_hmm = options->media.left_margin > 0 ? (int)options->media.left_margin
                                                 : I9950_MARGIN_HMM;
    int mr_hmm = options->media.right_margin > 0 ? (int)options->media.right_margin
                                                  : I9950_MARGIN_HMM;
    int mt_hmm = options->media.top_margin > 0 ? (int)options->media.top_margin
                                                : I9950_MARGIN_HMM;
    int mb_hmm = options->media.bottom_margin > 0 ? (int)options->media.bottom_margin
                                                   : I9950_MARGIN_HMM;
    /* hundredths of a millimetre → points */
    int pappl_l = (int)((ml_hmm * 72.0) / 2540.0 + 0.5);
    int pappl_r = (int)((mr_hmm * 72.0) / 2540.0 + 0.5);
    int pappl_t = (int)((mt_hmm * 72.0) / 2540.0 + 0.5);
    int pappl_b = (int)((mb_hmm * 72.0) / 2540.0 + 0.5);
    int cons_l = left;
    int cons_r = right;
    int cons_t = top;
    int cons_b = bottom;
    int print_w, print_h, print_l, print_t;
    double sx, sy, s;

    if (pappl_l > cons_l)
      cons_l = pappl_l;
    if (media_w - pappl_r < cons_r)
      cons_r = media_w - pappl_r;
    if (pappl_t > cons_t)
      cons_t = pappl_t;
    if (media_h - pappl_b < cons_b)
      cons_b = media_h - pappl_b;

    if (cons_r > cons_l && cons_b > cons_t)
    {
      left = cons_l;
      right = cons_r;
      top = cons_t;
      bottom = cons_b;
    }
    img_w = right - left;
    img_h = bottom - top;

    sx = (double)img_w / (double)raster_w_pt;
    sy = (double)img_h / (double)raster_h_pt;
    s = (sx < sy) ? sx : sy;
    if (s > 1.0)
      s = 1.0;

    print_w = (int)(raster_w_pt * s + 0.5);
    print_h = (int)(raster_h_pt * s + 0.5);
    if (print_w < 1)
      print_w = 1;
    if (print_h < 1)
      print_h = 1;
    if (print_w > img_w)
      print_w = img_w;
    if (print_h > img_h)
      print_h = img_h;
    print_l = left + (img_w - print_w) / 2;
    print_t = top + (img_h - print_h) / 2;

    stp_set_width(gp->vars, print_w);
    stp_set_height(gp->vars, print_h);
    stp_set_left(gp->vars, print_l);
    stp_set_top(gp->vars, print_t);

    papplLogJob(gp->job, PAPPL_LOGLEVEL_DEBUG,
                "Page geometry: raster=%dx%dpx @ %dx%d -> %dx%d pt; "
                "printable=%dx%d pt (margins hmm L%d R%d T%d B%d); "
                "print=%dx%d pt at (%d,%d) scale=%.4f; mono=%d res=%s.",
                h->cupsWidth, h->cupsHeight, xdpi, ydpi,
                raster_w_pt, raster_h_pt, img_w, img_h,
                ml_hmm, mr_hmm, mt_hmm, mb_hmm,
                print_w, print_h, print_l, print_t, s,
                gp->mono, resbuf);
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

  if (gp->mono && gp->rows && gp->width && gp->height)
  {
    size_t i, n;
    size_t ink = 0;
    unsigned long long sum = 0;
    unsigned char *p = gp->rows;
    double mean;
    const char *image_type;
    size_t pure_white = 0, pure_black = 0;

    /* Trust bytes-per-line for 8-bit mono (must match cupsWidth). */
    if (gp->row_bytes != (size_t)gp->width)
      papplLogJob(gp->job, PAPPL_LOGLEVEL_WARN,
                  "Mono row_bytes=%lu != width=%u; using row_bytes for analysis.",
                  (unsigned long)gp->row_bytes, gp->width);

    n = (size_t)gp->height * gp->row_bytes;
    for (i = 0; i < n; i++)
      sum += p[i];
    mean = (double)sum / (double)n;
    /*
     * LOCKED (Job 38 PASS — t-printable-a4-600.png):
     * PAPPL mono is often 0=white. Canon K output is COLOR_BLACK
     * ("Grayscale"). Setting Whitescale makes invert_output=1 and prints
     * inverted (Job 37). Do NOT use Whitescale. Normalize to 0=white /
     * 255=ink and always set InputImageType=Grayscale so invert_output=0
     * (high value = ink).
     */
    {
      int src_zero_is_white = (mean < 128.0);

      if (!src_zero_is_white)
      {
        for (i = 0; i < n; i++)
          p[i] = (unsigned char)(255 - p[i]);
      }
    }
    gp->zero_is_white = 1;
    image_type = "Grayscale";
    stp_set_string_parameter(gp->vars, "InputImageType", image_type);

    for (i = 0; i < n; i++)
      p[i] = (p[i] > 128) ? 255 : 0; /* 0=white; ink -> 255 */

    for (i = 0; i < n; i++)
    {
      if (p[i] == 0)
        pure_white++;
      else
      {
        pure_black++;
        ink++;
      }
    }

    papplLogJob(gp->job, PAPPL_LOGLEVEL_INFO,
                "Mono polarity: mean=%.1f normalized 0=white -> %s "
                "(zero_is_white=1); after threshold ink=%.2f%% white=%lu "
                "inked=%lu size=%ux%u row=%lu.",
                mean, image_type,
                100.0 * (double)ink / (double)n,
                (unsigned long)pure_white, (unsigned long)pure_black,
                gp->width, gp->height, (unsigned long)gp->row_bytes);

    if (ink == 0)
    {
      papplLogJob(gp->job, PAPPL_LOGLEVEL_ERROR,
                  "Aborting page: mono ink is 0%% after threshold "
                  "(blit/decode failure). Refusing empty page.");
      gp->page_open = 0;
      return -1;
    }

    if (!getenv("I9950_ALLOW_HIGH_INK") && ink * 100 > n * 8)
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
