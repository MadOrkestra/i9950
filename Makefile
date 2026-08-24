# Canon i9950 macOS Printer Application
#
# Copyright (C) 2026 i9950 driver project
# SPDX-License-Identifier: GPL-2.0-or-later

VERSION     ?= 0.2.1
ARCH        ?= arm64
BUILD_DIR   ?= build
PAPPL_DIR   := third_party/pappl
GUTEN_DIR   := third_party/gutenprint
GP_LIB      := $(GUTEN_DIR)/src/main/.libs/libgutenprint.a
PAPPL_LIB   := $(PAPPL_DIR)/pappl/libpappl.a

GP_INC      := -I$(GUTEN_DIR)/include -I$(GUTEN_DIR)
PAPPL_INC   := -I$(PAPPL_DIR)/pappl -I$(PAPPL_DIR)
CUPS_CFLAGS := $(shell cups-config --cflags 2>/dev/null)
CUPS_LIBS   := $(shell cups-config --image --libs 2>/dev/null)

CFLAGS      += -std=gnu23 -Wall -Wextra -O2 -arch $(ARCH) \
              -Iinclude -Isrc $(GP_INC) $(PAPPL_INC) $(CUPS_CFLAGS) \
              -I/opt/homebrew/opt/libusb/include \
              -DI9950_VERSION=\"$(VERSION)\" \
              -DI9950_GUTENPRINT_XMLDIR=\"$(abspath $(GUTEN_DIR)/src/xml)\"
ifeq ($(shell uname),Darwin)
CFLAGS      += -ObjC -fobjc-arc
endif
LDFLAGS     += -arch $(ARCH)
LIBS        += $(PAPPL_LIB) $(GP_LIB) $(CUPS_LIBS) \
              -framework AppKit -framework CoreFoundation \
              -framework SystemConfiguration -framework IOKit \
              -L/opt/homebrew/opt/jpeg-turbo/lib -ljpeg \
              -L/opt/homebrew/opt/libpng/lib -lpng16 -lz \
              -L/opt/homebrew/opt/libusb/lib -lusb-1.0 \
              -L/opt/homebrew/opt/openssl@3/lib -lssl -lcrypto \
              -liconv -lm -lpthread -lpam

APP_SRCS    := src/i9950-printer-app.c \
               src/pappl/i9950_driver.c \
               src/canon/gp_encoder.c \
               src/canon/usb_flush.c

ifeq ($(shell uname),Darwin)
APP_SRCS    += src/macos/i9950_status_bar.m \
               src/macos/i9950_icon_path.c
endif

TOOL_SRCS   := src/tools/i9950-tool.c

TEST_SRCS   := test/test_usb_flush.c

APP_OBJS    := $(patsubst %.c,$(BUILD_DIR)/%.o,$(filter %.c,$(APP_SRCS))) \
               $(patsubst %.m,$(BUILD_DIR)/%.o,$(filter %.m,$(APP_SRCS)))
TOOL_OBJS   := $(patsubst %.c,$(BUILD_DIR)/%.o,$(TOOL_SRCS))
TEST_OBJS   := $(patsubst %.c,$(BUILD_DIR)/%.o,$(TEST_SRCS))

.PHONY: all clean deps pappl gutenprint test install \
        normalize-capture run-tests package menu-icon

MENU_ICON   := $(BUILD_DIR)/share/i9950/lucide-printer-template.png

all: deps menu-icon $(BUILD_DIR)/i9950-printer-app $(BUILD_DIR)/i9950-tool

menu-icon: $(MENU_ICON)

$(MENU_ICON): assets/icons/lucide-printer.svg scripts/generate_menu_icon.py
	@python3 scripts/generate_menu_icon.py

deps: pappl gutenprint

PAPPL_PATCH := packaging/patches/pappl-i9950-menu-bar.patch

pappl:
	@export PKG_CONFIG_PATH="/opt/homebrew/opt/openssl@3/lib/pkgconfig:/opt/homebrew/opt/jpeg-turbo/lib/pkgconfig:/opt/homebrew/opt/libpng/lib/pkgconfig:/opt/homebrew/opt/libusb/lib/pkgconfig:$$PKG_CONFIG_PATH" && \
	  test -f $(PAPPL_DIR)/Makedefs || (cd $(PAPPL_DIR) && ./configure --disable-shared) && \
	  patch -d $(PAPPL_DIR) -p1 -N -s -r - < $(PAPPL_PATCH) || true && \
	  $(MAKE) -C $(PAPPL_DIR)/pappl libpappl.a

gutenprint:
	@test -f $(GP_LIB) || ( \
	  export PATH="/opt/homebrew/opt/libtool/libexec/gnubin:/opt/homebrew/opt/gettext/bin:$$PATH" && \
	  test -f $(GUTEN_DIR)/configure || (cd $(GUTEN_DIR) && ./autogen.sh) && \
	  cd $(GUTEN_DIR) && \
	  test -f config.status || ./configure --disable-nls --without-cups --without-gui --without-gimp --without-escputil --without-foomatic --without-cups-ppd-utils --disable-doc && \
	  $(MAKE) -C src/main )

$(BUILD_DIR)/%.o: %.c
	@mkdir -p $(dir $@)
	$(CC) $(CFLAGS) -c -o $@ $<

$(BUILD_DIR)/i9950-printer-app: $(APP_OBJS) $(PAPPL_LIB) $(GP_LIB) $(MENU_ICON)
	$(CC) $(LDFLAGS) -o $@ $(APP_OBJS) $(LIBS)

ifeq ($(shell uname),Darwin)
$(BUILD_DIR)/%.o: %.m
	@mkdir -p $(dir $@)
	$(CC) $(CFLAGS) -c -o $@ $<
endif

$(BUILD_DIR)/i9950-tool: $(TOOL_OBJS)
	$(CC) $(LDFLAGS) -o $@ $(TOOL_OBJS) \
	  -L/opt/homebrew/opt/libusb/lib -lusb-1.0

test: $(BUILD_DIR)/test_usb_flush
	$(BUILD_DIR)/test_usb_flush

$(BUILD_DIR)/test_usb_flush: $(TEST_OBJS)
	$(CC) $(LDFLAGS) -o $@ $(TEST_OBJS)

install: all
	install -d $(DESTDIR)/usr/local/bin
	install -m 755 $(BUILD_DIR)/i9950-printer-app $(DESTDIR)/usr/local/bin/
	install -m 755 $(BUILD_DIR)/i9950-tool $(DESTDIR)/usr/local/bin/
	install -d $(DESTDIR)/usr/local/share/i9950
	install -m 644 $(MENU_ICON) $(DESTDIR)/usr/local/share/i9950/
	install -d $(DESTDIR)/Library/LaunchAgents
	install -m 644 packaging/macos/com.i9950.printer-app.plist $(DESTDIR)/Library/LaunchAgents/

normalize-capture:
	python3 tools/normalize_capture.py $(CAP)

run-tests: all test
	./scripts/run-tests.sh

package: all
	./packaging/macos/build-pkg.sh

clean:
	rm -rf $(BUILD_DIR)
