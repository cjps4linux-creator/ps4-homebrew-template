# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- **Test suite style.** `re.M` is replaced with the explicit `re.MULTILINE`
  in the metadata consistency tests. This is cosmetic and changes no
  behaviour; it keeps the file clean under Ruff's full default rule set
  as well as the project's pinned `E4,E7,E9,F` selection.

## [1.0.0] — 2026-10-20

### Added

- **Real CI gates.** The workflow ran a Python-only Ruff check, which is
  meaningless for a C++ project. It is replaced with three real gates:
  a metadata-consistency pytest suite (21 tests), a `clang++ -fsyntax-only`
  check over `src/main.cpp`, and a required-document check.
- **Metadata consistency tests** (`tests/test_metadata_consistency.py`),
  which assert the package identity is coherent across the metadata, the
  build script and the documentation.
- **Initial release.** OpenOrbis-based PS4 homebrew scaffold with a
  Windows build script.

### Fixed

- **Truncated `CONTENT_ID`.** The canonical identifier
  `IV0000-BREW00084_00-TEMPLATE00000000` had been cut short, which would
  have produced a package that does not match its own metadata.
- **Fresh-clone safety.** The metadata check assumed a generated artefact
  (`package/pkg.gp4`) that is absent from a clean checkout, so the test
  failed on a fresh clone and passed only locally. The generated package
  is now ignored and the test no longer depends on it.

### Changed

- The generated `eboot.bin` and `package/pkg.gp4` are no longer tracked.
- The meaningless Python-only `ruff.toml` was removed.
- The complete GPL-3.0 licence text is included.
- **README author credit** added: Conrad CJ Wilson.

### Security

- Secret scanning and push protection enabled at the repository level.

[1.0.0]: https://github.com/cjps4linux-creator/ps4-homebrew-template/releases/tag/v1.0.0
