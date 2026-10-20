# PS4 Homebrew Template

<p align="center">
  <a href="https://github.com/cjps4linux-creator/ps4-homebrew-template/actions/workflows/ci.yml"><img src="https://github.com/cjps4linux-creator/ps4-homebrew-template/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://github.com/cjps4linux-creator/ps4-homebrew-template/releases/tag/v1.0.0"><img src="https://img.shields.io/badge/release-v1.0.0-0a7563" alt="Release v1.0.0"></a>
</p>

A reusable OpenOrbis project scaffold for building PS4 homebrew `.pkg` files on Windows, Linux, and macOS.

## Prerequisites

- **LLVM/Clang 18+** with `lld` linker
- **OpenOrbis PS4 Toolchain** extracted somewhere
- **Environment variable** `OO_PS4_TOOLCHAIN` pointing to the toolchain root

### Windows Setup

```powershell
# Set toolchain path (once per session)
$env:OO_PS4_TOOLCHAIN = 'C:\path\to\PS4Toolchain'

# Make permanent
[System.Environment]::SetEnvironmentVariable('OO_PS4_TOOLCHAIN', 'C:\path\to\PS4Toolchain', 'User')
```

### Linux/macOS Setup

```bash
export OO_PS4_TOOLCHAIN=/path/to/PS4Toolchain
# Add to ~/.bashrc or ~/.zshrc for persistence
```

## Building

### Windows (Visual Studio / Developer Command Prompt)

```powershell
# From the project root
build.bat
```

### Linux/macOS (Make)

```bash
make clean    # Optional: clean previous build
make          # Build the PKG
```

## Output

After a successful build:

```
package/
└── IV0000-BREW00084_00-TEMPLATE000000.pkg   ← Your homebrew package
eboot.bin                                      ← The executable
build/
└── main.o                                     ← Compiled object
```

## Installation

1. Copy the `.pkg` to a USB drive root
2. Plug into PS4 port closest to the CD drive
3. On PS4: **Settings → Debug Settings → Package Installer**
4. Select your `.pkg` and install

## Customization

Edit `include/template_config.h` to change:

```c
#define APP_TITLE       "Your App Name"
#define APP_VERSION     "1.00"
#define TITLE_ID        "BREW00085"           // Must be unique
#define CONTENT_ID      "IV0000-BREW00085_00-YOURAPP000000"
#define CATEGORY        "gd"                  // gd = game/app, ac = application
```

Then modify `src/main.cpp` to implement your app logic.

## Project Structure

```
ps4-homebrew-template/
├── src/
│   └── main.cpp           # Your app entry point
├── include/
│   └── template_config.h  # App metadata and settings
├── data/                  # Runtime assets (accessed via /app0/)
├── sce_sys/
│   └── icon0.png          # 512x512 app icon (NO alpha)
├── sce_module/            # Optional .sprx modules
├── package/               # Build output directory
├── build.bat              # Windows build script
├── Makefile               # Linux/macOS build script
└── README.md
```

## Notes

- **STL is not supported** by the current toolchain — use C or C++ without STL
- **Heap is limited** to ~700-800MB — use Direct Memory for large buffers
- **Never return from main()** — PS4 apps must loop forever
- **All file paths** use `/app0/` prefix for sandboxed data access

## References

- [OpenOrbis Toolchain](https://github.com/OpenOrbis/OpenOrbis-PS4-Toolchain)
- [SpecterDev Tutorial Series](https://www.youtube.com/playlist?list=PL4EKilIHxxXAa6ZNTDlpydeJVi07aZ0uO)
- [ConsoleMods Wiki](https://consolemods.org/wiki/PS4:OpenOrbis_SDK)

---

Built by **Conrad CJ Wilson** — [GitHub](https://github.com/cjps4linux-creator) · [LinkedIn](https://linkedin.com/in/conradcjwilson)
