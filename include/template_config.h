#ifndef PS4_HOMEBREW_TEMPLATE_H
#define PS4_HOMEBREW_TEMPLATE_H

// ============================================================================
// CONFIGURATION
// ============================================================================
#define APP_TITLE       "PS4 Homebrew Template"
#define APP_VERSION     "1.00"
#define TITLE_ID        "BREW00084"
#define CONTENT_ID      "IV0000-BREW00084_00-TEMPLATE000000"
#define CATEGORY        "gd"  // gd = game/digital app, ac = application

// Display settings
#define DISPLAY_WIDTH   1920
#define DISPLAY_HEIGHT  1080
#define PIXEL_FORMAT    SCE_VIDEO_OUT_PIXEL_FORMAT_A8R8G8B8

// ============================================================================
// BUILD CONFIGURATION
// ============================================================================
#define TOOLCHAIN_ENV_VAR "OO_PS4_TOOLCHAIN"
#define REQUIRED_LLVM_VERSION 18

// ============================================================================
// PACKAGE CONFIGURATION
// ============================================================================
#define PKG_OUTPUT_DIR  "package"
#define DATA_DIR        "data"
#define SCE_SYS_DIR     "sce_sys"
#define ICON0_FILE      "sce_sys/icon0.png"
#define PARAM_SFO_FILE  "sce_sys/param.sfo"

// ============================================================================
// MEMORY CONFIGURATION
// ============================================================================
#define FRAMEBUFFER_SIZE (DISPLAY_WIDTH * DISPLAY_HEIGHT * 4)

// ============================================================================
// DEBUG FLAGS
// ============================================================================
#define DEBUG_PRINTF   1  // Enable kernel printf debugging
#define DEBUG_VIDEO    1  // Enable video output

#endif // PS4_HOMEBREW_TEMPLATE_H
