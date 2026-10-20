@echo off
REM ============================================================================
REM PS4 Homebrew Template - Windows Build Script
REM ============================================================================

setlocal enabledelayedexpansion

echo.
echo ========================================
echo   PS4 Homebrew Template Builder
echo ========================================
echo.

REM --------------------------------------------------------------------------
REM App configuration
REM --------------------------------------------------------------------------
set APP_TITLE=PS4 Homebrew Template
set APP_VERSION=1.00
set TITLE_ID=BREW00084
set CONTENT_ID=IV0000-BREW00084_00-TEMPLATE00000000
set CATEGORY=gd

REM --------------------------------------------------------------------------
REM Validate environment
REM --------------------------------------------------------------------------
if "%OO_PS4_TOOLCHAIN%"=="" (
    echo [ERROR] OO_PS4_TOOLCHAIN environment variable not set.
    echo.
    echo Set it with:
    echo   setx OO_PS4_TOOLCHAIN "C:\path\to\PS4Toolchain"
    echo.
    pause
    exit /b 1
)

echo [INFO] Toolchain: %OO_PS4_TOOLCHAIN%
echo [INFO] Building: %APP_TITLE% v%APP_VERSION%
echo.

REM --------------------------------------------------------------------------
REM Validate LLVM
REM --------------------------------------------------------------------------
where clang >nul 2>&1
if errorlevel 1 (
    echo [ERROR] clang not found. Install LLVM/Clang and add to PATH.
    pause
    exit /b 1
)

where lld-link >nul 2>&1
if errorlevel 1 (
    echo [ERROR] lld-link not found. Install LLVM with lld component.
    pause
    exit /b 1
)

echo [OK] clang and lld found
echo.

REM --------------------------------------------------------------------------
REM Create directories
REM --------------------------------------------------------------------------
if not exist "build" mkdir build
if not exist "package\sce_sys" mkdir package\sce_sys
if not exist "package\data" mkdir package\data

REM --------------------------------------------------------------------------
REM Compile
REM --------------------------------------------------------------------------
echo [STEP 1/5] Compiling source...
clang++ --target=x86_64-pc-freebsd12-elf ^
    -fPIC ^
    -funwind-tables ^
    -c ^
    -isysroot "%OO_PS4_TOOLCHAIN%" ^
    -isystem "%OO_PS4_TOOLCHAIN%\include" ^
    -isystem "%OO_PS4_TOOLCHAIN%\include\c++\v1" ^
    -I "include" ^
    src\main.cpp ^
    -o build\main.o

if errorlevel 1 (
    echo [ERROR] Compilation failed
    pause
    exit /b 1
)

echo [OK] Compilation successful
echo.

REM --------------------------------------------------------------------------
REM Link
REM --------------------------------------------------------------------------
echo [STEP 2/5] Linking...
"C:\Program Files\LLVM\bin\ld.lld.exe" -m elf_x86_64 -pie ^
    --script "%OO_PS4_TOOLCHAIN%\link.x" ^
    --eh-frame-hdr ^
    -L "%OO_PS4_TOOLCHAIN%\lib" ^
    -L "C:\Program Files\LLVM\lib" ^
    build\main.o ^
    -o build\app.elf ^
    "%OO_PS4_TOOLCHAIN%\lib\crt1.o" ^
    -lc -lkernel -lc++

if errorlevel 1 (
    echo [ERROR] Linking failed
    pause
    exit /b 1
)

echo [OK] Linking successful
echo.

REM --------------------------------------------------------------------------
REM Create fake SELF (eboot.bin)
REM --------------------------------------------------------------------------
echo [STEP 3/5] Creating eboot.bin...
"%OO_PS4_TOOLCHAIN%\bin\windows\create-fself.exe" ^
    -in=build\app.elf ^
    -out=eboot.bin ^
    --eboot "eboot.bin" ^
    --paid 0x3800000000000011

if errorlevel 1 (
    echo [ERROR] create-fself failed
    pause
    exit /b 1
)

echo [OK] eboot.bin created
echo.

REM --------------------------------------------------------------------------
REM Generate param.sfo
REM --------------------------------------------------------------------------
echo [STEP 4/5] Generating param.sfo...
copy /Y sce_sys\icon0.png package\sce_sys\ >nul 2>&1

"%OO_PS4_TOOLCHAIN%\bin\windows\PkgTool.Core.exe" sfo_new package\sce_sys\param.sfo
"%OO_PS4_TOOLCHAIN%\bin\windows\PkgTool.Core.exe" sfo_setentry package\sce_sys\param.sfo APP_TYPE --type Integer --maxsize 4 --value 1
"%OO_PS4_TOOLCHAIN%\bin\windows\PkgTool.Core.exe" sfo_setentry package\sce_sys\param.sfo APP_VER --type Utf8 --maxsize 8 --value "%APP_VERSION%"
"%OO_PS4_TOOLCHAIN%\bin\windows\PkgTool.Core.exe" sfo_setentry package\sce_sys\param.sfo ATTRIBUTE --type Integer --maxsize 4 --value 0
"%OO_PS4_TOOLCHAIN%\bin\windows\PkgTool.Core.exe" sfo_setentry package\sce_sys\param.sfo CATEGORY --type Utf8 --maxsize 4 --value %CATEGORY%
"%OO_PS4_TOOLCHAIN%\bin\windows\PkgTool.Core.exe" sfo_setentry package\sce_sys\param.sfo CONTENT_ID --type Utf8 --maxsize 48 --value %CONTENT_ID%
"%OO_PS4_TOOLCHAIN%\bin\windows\PkgTool.Core.exe" sfo_setentry package\sce_sys\param.sfo DOWNLOAD_DATA_SIZE --type Integer --maxsize 4 --value 0
"%OO_PS4_TOOLCHAIN%\bin\windows\PkgTool.Core.exe" sfo_setentry package\sce_sys\param.sfo SYSTEM_VER --type Integer --maxsize 4 --value 0
"%OO_PS4_TOOLCHAIN%\bin\windows\PkgTool.Core.exe" sfo_setentry package\sce_sys\param.sfo TITLE --type Utf8 --maxsize 128 --value "%APP_TITLE%"
"%OO_PS4_TOOLCHAIN%\bin\windows\PkgTool.Core.exe" sfo_setentry package\sce_sys\param.sfo TITLE_ID --type Utf8 --maxsize 12 --value %TITLE_ID%
"%OO_PS4_TOOLCHAIN%\bin\windows\PkgTool.Core.exe" sfo_setentry package\sce_sys\param.sfo VERSION --type Utf8 --maxsize 8 --value "%APP_VERSION%"

echo [OK] param.sfo generated
echo.

REM --------------------------------------------------------------------------
REM Create GP4 and build PKG
REM --------------------------------------------------------------------------
echo [STEP 5/5] Building package...
copy /Y eboot.bin package\ >nul

REM Build GP4 from the package/ working directory so relative paths match
pushd package

"%OO_PS4_TOOLCHAIN%\bin\windows\create-gp4.exe" ^
    -out pkg.gp4 ^
    -content-id %CONTENT_ID% ^
    -files "eboot.bin sce_sys/param.sfo sce_sys/icon0.png"

if errorlevel 1 (
    echo [ERROR] create-gp4 failed
    popd
    pause
    exit /b 1
)

"%OO_PS4_TOOLCHAIN%\bin\windows\PkgTool.Core.exe" pkg_build pkg.gp4 .

if errorlevel 1 (
    echo [ERROR] pkg_build failed
    popd
    pause
    exit /b 1
)

popd

echo.
echo ========================================
echo   BUILD SUCCESSFUL
echo ========================================
echo.
echo Output: package\%CONTENT_ID%.pkg
echo.
echo To install:
echo   1. Copy the .pkg to a USB drive
echo   2. Plug into PS4 (port closest to CD drive)
echo   3. Settings -^> Debug Settings -^> Package Installer
echo   4. Select and install the package
echo.
pause
