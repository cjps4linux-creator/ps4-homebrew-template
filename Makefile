# Package metadata
TITLE       := PS4 Homebrew Template
VERSION     := 1.00
TITLE_ID    := BREW00084
CONTENT_ID  := IV0000-BREW00084_00-TEMPLATE00000000

# Libraries
LIBS        := -lc -lkernel -lc++

# Asset directories
ASSETS      := $(wildcard data/**/*)
LIBMODULES  := $(wildcard sce_module/*)

# Root vars
TOOLCHAIN   := $(OO_PS4_TOOLCHAIN)
PROJDIR     := $(shell basename $(CURDIR))
INTDIR      := $(PROJDIR)/build

# Compiler flags
CFLAGS      := --target=x86_64-pc-freebsd12-elf -fPIC -funwind-tables -c \
               -isysroot $(TOOLCHAIN) \
               -isystem $(TOOLCHAIN)/include \
               -I include
CXXFLAGS    := $(CFLAGS) -isystem $(TOOLCHAIN)/include/c++/v1
LDFLAGS     := -m elf_x86_64 -pie \
               --script $(TOOLCHAIN)/link.x \
               --eh-frame-hdr \
               -L$(TOOLCHAIN)/lib \
               -L/usr/lib/llvm-18/lib \
               $(LIBS) \
               $(TOOLCHAIN)/lib/crt1.o

# Source files
CFILES      := $(wildcard src/*.c)
CPPFILES    := $(wildcard src/*.cpp)
OBJS        := $(patsubst src/%.c, $(INTDIR)/%.o, $(CFILES)) \
               $(patsubst src/%.cpp, $(INTDIR)/%.o, $(CPPFILES))

# Platform detection
UNAME_S     := $(shell uname -s)

ifeq ($(UNAME_S),Linux)
    CC      := clang
    CCX     := clang++
    LD      := ld.lld
    CDIR    := linux
endif
ifeq ($(UNAME_S),Darwin)
    CC      := /usr/local/opt/llvm/bin/clang
    CCX     := /usr/local/opt/llvm/bin/clang++
    LD      := /usr/local/opt/llvm/bin/ld.lld
    CDIR    := macos
endif
ifeq ($(OS),Windows_NT)
    CC      := clang
    CCX     := clang++
    LD      := ld.lld
    CDIR    := windows
endif

# Default target
all: $(CONTENT_ID).pkg

# Package build
$(CONTENT_ID).pkg: pkg.gp4
	$(TOOLCHAIN)/bin/$(CDIR)/PkgTool.Core pkg_build $< .

# GP4 generation
pkg.gp4: eboot.bin sce_sys/param.sfo sce_sys/icon0.png $(LIBMODULES) $(ASSETS)
	$(TOOLCHAIN)/bin/$(CDIR)/create-gp4 \
		-out $@ \
		--content-id=$(CONTENT_ID) \
		--files "$^"

# SFO generation
sce_sys/param.sfo: Makefile
	$(TOOLCHAIN)/bin/$(CDIR)/PkgTool.Core sfo_new $@
	$(TOOLCHAIN)/bin/$(CDIR)/PkgTool.Core sfo_setentry $@ APP_TYPE --type Integer --maxsize 4 --value 1
	$(TOOLCHAIN)/bin/$(CDIR)/PkgTool.Core sfo_setentry $@ APP_VER --type Utf8 --maxsize 8 --value '$(VERSION)'
	$(TOOLCHAIN)/bin/$(CDIR)/PkgTool.Core sfo_setentry $@ ATTRIBUTE --type Integer --maxsize 4 --value 0
	$(TOOLCHAIN)/bin/$(CDIR)/PkgTool.Core sfo_setentry $@ CATEGORY --type Utf8 --maxsize 4 --value '$(CATEGORY)'
	$(TOOLCHAIN)/bin/$(CDIR)/PkgTool.Core sfo_setentry $@ CONTENT_ID --type Utf8 --maxsize 48 --value '$(CONTENT_ID)'
	$(TOOLCHAIN)/bin/$(CDIR)/PkgTool.Core sfo_setentry $@ DOWNLOAD_DATA_SIZE --type Integer --maxsize 4 --value 0
	$(TOOLCHAIN)/bin/$(CDIR)/PkgTool.Core sfo_setentry $@ SYSTEM_VER --type Integer --maxsize 4 --value 0
	$(TOOLCHAIN)/bin/$(CDIR)/PkgTool.Core sfo_setentry $@ TITLE --type Utf8 --maxsize 128 --value '$(TITLE)'
	$(TOOLCHAIN)/bin/$(CDIR)/PkgTool.Core sfo_setentry $@ TITLE_ID --type Utf8 --maxsize 12 --value '$(TITLE_ID)'
	$(TOOLCHAIN)/bin/$(CDIR)/PkgTool.Core sfo_setentry $@ VERSION --type Utf8 --maxsize 8 --value '$(VERSION)'

# eboot.bin build
eboot.bin: $(INTDIR) $(OBJS)
	$(LD) $(INTDIR)/*.o -o $(INTDIR)/$(PROJDIR).elf $(LDFLAGS)
	$(TOOLCHAIN)/bin/$(CDIR)/create-fself \
		-in=$(INTDIR)/$(PROJDIR).elf \
		-out=$(INTDIR)/$(PROJDIR).oelf \
		--eboot "eboot.bin" \
		--paid 0x3800000000000011
	cp $(INTDIR)/eboot.bin ./eboot.bin

# Compile rules
$(INTDIR)/%.o: src/%.c
	$(CC) $(CFLAGS) -o $@ $<

$(INTDIR)/%.o: src/%.cpp
	$(CCX) $(CXXFLAGS) -o $@ $<

# Directory creation
$(INTDIR):
	mkdir -p $(INTDIR)

# Clean
clean:
	rm -f $(CONTENT_ID).pkg pkg.gp4 eboot.bin
	rm -f $(INTDIR)/*.o $(INTDIR)/*.elf $(INTDIR)/*.oelf
	rm -rf package

# Help
help:
	@echo "PS4 Homebrew Template - Make Targets"
	@echo ""
	@echo "  make          - Build PKG (default)"
	@echo "  make clean    - Remove build artifacts"
	@echo "  make help     - Show this help"
	@echo ""
	@echo "Environment:"
	@echo "  OO_PS4_TOOLCHAIN must be set to your OpenOrbis installation"
