/*
 * macOS menu bar status item (Lucide printer template icon).
 *
 * Copyright (C) 2026 i9950 driver project
 * SPDX-License-Identifier: GPL-2.0-or-later
 */

#ifdef __APPLE__

#import "i9950_status_bar.h"

#import <Cocoa/Cocoa.h>
#import <string.h>
#import <stdlib.h>
#import <stdio.h>

static NSStatusItem *status_item = nil;
static int status_web_port = 8501;

@interface I9950StatusBarDelegate : NSObject
@end

@implementation I9950StatusBarDelegate

- (void)openConfiguration:(id)sender
{
  (void)sender;
  char url[128];
  snprintf(url, sizeof(url), "http://127.0.0.1:%d/", status_web_port);
  [[NSWorkspace sharedWorkspace] openURL:[NSURL URLWithString:[NSString stringWithUTF8String:url]]];
}

- (void)quit:(id)sender
{
  (void)sender;
  [NSApp terminate:nil];
}

@end

static I9950StatusBarDelegate *status_delegate = nil;

bool
i9950_status_bar_wanted(int argc, char *argv[])
{
  const char *env;

  if (getenv("I9950_NO_MENU_BAR"))
    return false;

  if (argc < 2 || strcmp(argv[1], "server"))
    return false;

  for (int i = 2; i < argc; i++)
  {
    if (!strcmp(argv[i], "-o") && i + 1 < argc &&
        !strncmp(argv[i + 1], "private-server=", 15))
      return false;
    if (!strncmp(argv[i], "private-server=", 15))
      return false;
  }

  env = getenv("I9950_MENU_BAR");
  if (env && (!strcmp(env, "0") || !strcasecmp(env, "false") || !strcasecmp(env, "no")))
    return false;

  return true;
}

static int
i9950_status_bar_port(void)
{
  const char *env = getenv("I9950_WEB_PORT");
  if (env && env[0])
    return atoi(env);
  return 8501;
}

void
i9950_status_bar_init(const char *icon_path, int web_port)
{
  NSImage *image = nil;

  if (status_item)
    return;

  status_web_port = web_port > 0 ? web_port : i9950_status_bar_port();

  [NSApplication sharedApplication];
  [NSApp setActivationPolicy:NSApplicationActivationPolicyAccessory];

  status_item = [[NSStatusBar systemStatusBar]
      statusItemWithLength:NSSquareStatusItemLength];
  if (!status_item)
    return;

  if (icon_path && icon_path[0])
  {
    image = [[NSImage alloc] initWithContentsOfFile:[NSString stringWithUTF8String:icon_path]];
    if (image)
    {
      /* Only use PNGs that look like template art (transparent + dark strokes). */
      NSImageRep *any_rep = [NSBitmapImageRep imageRepWithContentsOfFile:
          [NSString stringWithUTF8String:icon_path]];
      NSBitmapImageRep *rep = [any_rep isKindOfClass:[NSBitmapImageRep class]]
          ? (NSBitmapImageRep *)any_rep : nil;
      bool template_ok = false;

      if (rep && [rep hasAlpha])
      {
        NSInteger iw = rep.pixelsWide, ih = rep.pixelsHigh;
        int transparent = 0, dark = 0, light = 0;

        for (NSInteger y = 0; y < ih; y++)
        {
          for (NSInteger x = 0; x < iw; x++)
          {
            NSColor *c = [rep colorAtX:x y:y];
            if (!c)
              continue;
            CGFloat r, g, b, a;

            [[c colorUsingColorSpace:[NSColorSpace genericRGBColorSpace]]
                getRed:&r green:&g blue:&b alpha:&a];
            if (a < 0.12)
              transparent++;
            else if (r > 0.85 && g > 0.85 && b > 0.85)
              light++;
            else if (r < 0.25 && g < 0.25 && b < 0.25)
              dark++;
          }
        }

        template_ok = (transparent > 0 && dark > 0 && light < dark);
      }

      if (template_ok)
      {
        [image setSize:NSMakeSize(18, 18)];
        image.template = YES;
      }
      else
        image = nil;
    }
  }

  if (!image)
  {
    if (@available(macOS 11.0, *))
      image = [NSImage imageWithSystemSymbolName:@"printer.fill"
                        accessibilityDescription:@"Canon i9950 Printer"];
  }

  if (image)
    status_item.button.image = image;

  status_item.button.toolTip = @"Canon i9950 Printer";

  status_delegate = [[I9950StatusBarDelegate alloc] init];
  NSMenu *menu = [[NSMenu alloc] initWithTitle:@"Canon i9950"];

  NSMenuItem *open_item =
      [[NSMenuItem alloc] initWithTitle:@"Open Configuration…"
                                 action:@selector(openConfiguration:)
                          keyEquivalent:@""];
  open_item.target = status_delegate;
  [menu addItem:open_item];

  [menu addItem:[NSMenuItem separatorItem]];

  NSMenuItem *quit_item =
      [[NSMenuItem alloc] initWithTitle:@"Quit"
                                 action:@selector(quit:)
                          keyEquivalent:@"q"];
  quit_item.target = status_delegate;
  [menu addItem:quit_item];

  status_item.menu = menu;
}

#endif /* __APPLE__ */
