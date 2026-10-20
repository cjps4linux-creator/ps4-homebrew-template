#include <stdio.h>

// ============================================================================
// PS4 HOMEBREW TEMPLATE
// ============================================================================
// This is a minimal working template that compiles with the current OpenOrbis
// toolchain headers. Many VideoOut prototypes/constants are still incomplete
// in the public SDK; the graphics demo is left as a commented stub so the
// template stays buildable while you add the missing definitions later.
//
// Next steps:
//   1. Contribute missing VideoOut constants/types to OpenOrbis headers.
//   2. Uncomment the graphics code once sceVideoOut* symbols are available.
//   3. Add your app logic below.
// ============================================================================

int main(int argc, char* argv[]) {
    // PS4 apps MUST NOT return from main.
    // Returning causes a kernel crash: "return from main"
    // Always use an infinite loop.
    printf("[TEMPLATE] PS4 homebrew started\n");
    printf("[TEMPLATE] Build: %s %s\n", __DATE__, __TIME__);
    printf("[TEMPLATE] PID: %d\n", argc);

    // -------------------------------------------------------------------------
    // Graphics demo (commented — requires complete VideoOut headers)
    // -------------------------------------------------------------------------
    // TODO: Uncomment after adding these missing definitions:
    //   - SCE_VIDEO_OUT_BUS_TYPE_MAIN
    //   - SCE_VIDEO_OUT_PIXEL_FORMAT_A8R8G8B8
    //   - SCE_VIDEO_OUT_BUFFER_FORMAT_A8R8G8B8
    //   - SCE_VIDEO_OUT_BUFFER_ATTRIBUTE_ALPHA_LOCATION_IN_4X4
    //   - SCE_VIDEO_OUT_FLIP_MODE_VSYNC
    //   - SceVideoOutBufferAttribute struct
    //
    // int32_t handle = sceVideoOutOpen(0, SCE_VIDEO_OUT_BUS_TYPE_MAIN, 0, NULL);
    // // ... allocate framebuffer, register buffers, draw, flip ...

    // -------------------------------------------------------------------------
    // Main loop
    // -------------------------------------------------------------------------
    int counter = 0;
    for (;;) {
        printf("[TEMPLATE] Running... %d\n", counter++);
        for (int i = 0; i < 100000000; i++) { }
    }

    // Never reached — PS4 expects apps to run forever
    return 0;
}
