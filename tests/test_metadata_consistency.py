"""Consistency checks for the PS4 Homebrew Template metadata.

This repository contains no Python source, so the CI gate is a metadata
consistency test rather than a unit-test suite. The package identity
(TITLE_ID / CONTENT_ID) is declared in four separate places; if they drift,
the built PKG and the C source will disagree about what the app is called.

Run with:  pytest -q
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

MAKEFILE = REPO_ROOT / "Makefile"
CONFIG_H = REPO_ROOT / "include" / "template_config.h"
BUILD_BAT = REPO_ROOT / "build.bat"
GP4 = REPO_ROOT / "package" / "pkg.gp4"
MAIN_CPP = REPO_ROOT / "src" / "main.cpp"


def _read(path: Path) -> str:
    assert path.exists(), f"missing required file: {path}"
    return path.read_text(encoding="utf-8", errors="replace")


def _makefile_value(key: str) -> str:
    # Capture to end of line — values contain spaces (e.g. "PS4 Homebrew Template").
    # The key is anchored with a word boundary so TITLE does not match TITLE_ID.
    m = re.search(rf"^{key}\b\s*:=\s*(.+?)\s*$", _read(MAKEFILE), re.M)
    assert m, f"{key} not found in Makefile"
    return m.group(1)


def _header_value(key: str) -> str:
    m = re.search(rf'^#define\s+{key}\b\s+"([^"]*)"', _read(CONFIG_H), re.M)
    assert m, f"{key} not found in template_config.h"
    return m.group(1)


def _bat_value(key: str) -> str:
    m = re.search(rf"^set {key}=(.*?)\s*$", _read(BUILD_BAT), re.M | re.I)
    assert m, f"{key} not found in build.bat"
    return m.group(1).strip()


def _gp4_content_id() -> str:
    m = re.search(r'content_id="([^"]+)"', _read(GP4))
    assert m, "content_id not found in pkg.gp4"
    return m.group(1)


# ---------------------------------------------------------------------------
# Package identity must agree everywhere
# ---------------------------------------------------------------------------

def test_content_id_matches_across_all_four_sources():
    ids = {
        "Makefile": _makefile_value("CONTENT_ID"),
        "template_config.h": _header_value("CONTENT_ID"),
        "build.bat": _bat_value("CONTENT_ID"),
        "pkg.gp4": _gp4_content_id(),
    }
    assert len(set(ids.values())) == 1, f"CONTENT_ID differs between sources: {ids}"


def test_title_id_matches_across_all_three_sources():
    ids = {
        "Makefile": _makefile_value("TITLE_ID"),
        "template_config.h": _header_value("TITLE_ID"),
        "build.bat": _bat_value("TITLE_ID"),
    }
    assert len(set(ids.values())) == 1, f"TITLE_ID differs between sources: {ids}"


def test_content_id_starts_with_iv0000_prefix():
    assert _makefile_value("CONTENT_ID").startswith("IV0000-")


def test_content_id_embeds_title_id():
    assert _makefile_value("TITLE_ID") in _makefile_value("CONTENT_ID")


def test_content_id_length_is_36():
    # PS4 content IDs are 36 characters: IV0000-<TID>_<TID>_<NAME>
    assert len(_makefile_value("CONTENT_ID")) == 36


def test_app_title_matches():
    assert _makefile_value("TITLE") == _header_value("APP_TITLE")
    assert _bat_value("APP_TITLE") == _header_value("APP_TITLE")


def test_app_version_matches():
    assert _makefile_value("VERSION") == _header_value("APP_VERSION")
    assert _bat_value("APP_VERSION") == _header_value("APP_VERSION")


def test_category_is_valid():
    assert _header_value("CATEGORY") in {"gd", "ac"}
    assert _bat_value("CATEGORY") == _header_value("CATEGORY")


# ---------------------------------------------------------------------------
# Source sanity
# ---------------------------------------------------------------------------

def test_main_cpp_never_returns_from_main():
    # Returning from main on PS4 causes a kernel crash.
    src = _read(MAIN_CPP)
    body = src[src.index("int main("):]
    assert "for (;;)" in body or "while (1)" in body or "while(true)" in body, (
        "main() must contain an infinite loop — PS4 apps must not return from main"
    )


def test_main_cpp_includes_stdio():
    assert "#include <stdio.h>" in _read(MAIN_CPP)


def test_header_has_include_guard():
    src = _read(CONFIG_H)
    assert "#ifndef" in src
    assert "#define PS4_HOMEBREW_TEMPLATE_H" in src
    assert "#endif" in src


# ---------------------------------------------------------------------------
# Required files exist
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "rel",
    [
        "Makefile",
        "build.bat",
        "include/template_config.h",
        "src/main.cpp",
        "sce_sys/icon0.png",
        "package/pkg.gp4",
        "LICENSE",
        "README.md",
    ],
)
def test_required_file_exists(rel):
    assert (REPO_ROOT / rel).exists(), f"missing required file: {rel}"


def test_icon_is_a_real_png():
    data = (REPO_ROOT / "sce_sys" / "icon0.png").read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "icon0.png is not a valid PNG"


def test_license_is_gpl3():
    text = _read(REPO_ROOT / "LICENSE")
    assert "GNU GENERAL PUBLIC LICENSE" in text
    assert "Version 3" in text
