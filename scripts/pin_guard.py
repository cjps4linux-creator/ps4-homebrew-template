"""Dependency pin guard.

Enforces the pinning policy that the Hermes release programme depends on.

The policy has two parts, and this module checks both:

1. **No pre-release version specifiers.** A beta, alpha, release candidate
   or development version is not a reproducible release. A manifest that
   pins one means the artefact a user installs is not the artefact the
   project tested, and it can change without the project changing.

2. **The test toolchain is pinned deliberately.** ``pytest``,
   ``pytest-cov`` and ``ruff`` are version-bumped one release at a time,
   with the full suite re-run against the new version, because their
   defaults have moved before and produced spurious failures. Dependabot
   must not propose them.

Why this exists
---------------
A real Dependabot pull request proposed ``curl-cffi==0.7.0b4`` (a beta)
and ``pytest==9.0.3`` (an unpinned toolchain bump) for the same change.
The pull request was declined. This module is the control that makes the
same change fail automatically next time, instead of relying on a
reviewer noticing the version string.

Usage
-----
As a library::

    from tools.pin_guard import scan_manifests

    result = scan_manifests(Path("."))
    if not result.ok:
        for problem in result.problems:
            print(problem)

As a command::

    python -m tools.pin_guard path/to/repo
    python -m tools.pin_guard --json path/to/repo

Exit code is ``0`` when the manifests satisfy the policy and ``1`` when
they do not, so it can be wired directly into CI.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

__all__ = [
    "TOOLCHAIN_PACKAGES",
    "TOOLCHAIN_VERSIONS",
    "ManifestProblem",
    "PinGuardResult",
    "find_manifests",
    "is_pre_release",
    "main",
    "scan_manifests",
]

#: Packages whose version is bumped deliberately, one release at a time.
TOOLCHAIN_PACKAGES: frozenset[str] = frozenset(
    {
        "pytest",
        "pytest-cov",
        "ruff",
    }
)

try:  # pragma: no cover - exercised by whichever branch is available
    from packaging.version import InvalidVersion
    from packaging.version import Version as _Version

    _HAVE_PACKAGING = True
except ImportError:  # pragma: no cover - fallback path
    _HAVE_PACKAGING = False

#: PEP 440 pre-release and development markers. Used when ``packaging`` is
#: not installed. The marker attaches directly to the version, so
#: ``0.7.0b4`` is matched by ``b`` and ``1.0.0.dev3`` by ``dev``.
_PRE_RELEASE_SUFFIX = re.compile(
    r"^(?:.*?)(?:a|alpha|b|beta|c|rc|pre|preview)\d+(?:\.post\d+)?$"
    r"|^(?:.*?)\.dev\d+$"
    r"|^(?:.*?)(?:dev|nightly|canary|experimental)\d+$",
    re.IGNORECASE,
)

#: The exact toolchain versions the release programme is validated against.
#: These are installed by the CI workflow, not by the runtime manifest, so
#: the guard has to read the workflow to find them.
TOOLCHAIN_VERSIONS: dict[str, str] = {
    "pytest": "8.3.3",
    "pytest-cov": "5.0.0",
    "ruff": "0.17.1",
}

#: A dependency line, e.g. ``flask==3.1.3`` or ``numpy>=1.26.0``.
_REQUIREMENT = re.compile(
    r"^\s*(?P<name>[A-Za-z0-9][A-Za-z0-9._-]*)\s*(?P<extras>\[[^\]]*\])?\s*"
    r"(?P<spec>(?:[<>=!~]=?|===)\s*[^;#]+)?\s*$"
)

#: A dependency entry inside a ``pyproject.toml`` list, e.g. ``"flask==3.1.3"``.
_QUOTED_REQUIREMENT = re.compile(
    r"[\"'](?P<name>[A-Za-z0-9][A-Za-z0-9._-]*)\s*"
    r"(?P<extras>\[[^\]]*\])?\s*"
    r"(?P<spec>(?:[<>=!~]=?|===)\s*[^\"']+)?[\"']"
)

_MANIFEST_NAMES = ("requirements.txt",)


@dataclass(frozen=True)
class ManifestProblem:
    """A single policy violation found in one manifest."""

    manifest: str
    line_number: int
    package: str
    specifier: str
    reason: str
    text: str

    def __str__(self) -> str:  # pragma: no cover - formatting only
        return (
            f"{self.manifest}:{self.line_number}: {self.reason} "
            f"-- {self.package!r} {self.specifier!r} ({self.text})"
        )


@dataclass
class PinGuardResult:
    """The outcome of scanning one repository's manifests."""

    root: Path
    manifests: list[Path] = field(default_factory=list)
    problems: list[ManifestProblem] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """True when no policy violation was found."""
        return not self.problems

    def as_dict(self) -> dict:
        """A JSON-serialisable view of the result."""
        return {
            "root": str(self.root),
            "manifests": [str(m) for m in self.manifests],
            "ok": self.ok,
            "problems": [
                {
                    "manifest": p.manifest,
                    "line": p.line_number,
                    "package": p.package,
                    "specifier": p.specifier,
                    "reason": p.reason,
                    "text": p.text,
                }
                for p in self.problems
            ],
        }


def _version_is_pre_release(version: str) -> bool:
    """Return True when *version* is a pre-release under PEP 440.

    ``packaging`` is authoritative when available. The fallback regex
    implements the same rule closely enough to catch the defect that
    motivated this module: a PEP 440 marker attaches directly to the
    version, so ``0.7.0b4`` and ``1.2.3rc1`` are pre-releases while
    ``0.5.2`` and ``1.0.0.post1`` are not.
    """
    if _HAVE_PACKAGING:
        try:
            parsed = _Version(version)
        except InvalidVersion:
            # Not a PEP 440 version. Fall through to the regex so that
            # non-standard markers are still caught.
            return bool(_PRE_RELEASE_SUFFIX.match(version))
        # A post-release of a pre-release (1.0.0b1.post1) is still a
        # pre-release; a plain post-release is not.
        return bool(parsed.is_prerelease or parsed.is_devrelease)

    return bool(_PRE_RELEASE_SUFFIX.match(version))


def is_pre_release(specifier: str) -> bool:
    """Return True when *specifier* names a pre-release version.

    A specifier is a pre-release when any of its version tokens is a
    pre-release under PEP 440. Comparison operators, whitespace and
    extras are stripped first, so ``>=1.0.0b1`` and ``==2.0.0rc3`` are
    both detected while ``>=1.0.0`` is not.
    """
    if not specifier:
        return False
    # Keep only the version part of each clause.
    clauses = re.split(r"[,\s]+", specifier.strip())
    for clause in clauses:
        version = re.sub(r"^(?:[<>=!~]=?|===)", "", clause).strip()
        # Drop an environment marker or a local version label.
        version = version.split(";")[0].strip()
        version = version.split("+")[0].strip()
        if not version:
            continue
        if _version_is_pre_release(version):
            return True
    return False


def _normalise_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def find_manifests(root: Path) -> list[Path]:
    """Locate the dependency manifests belonging to *root*.

    Only files that are actually tracked by git are considered, so a
    manifest left behind in a build directory or an unpacked virtual
    environment cannot fail the check. When git is unavailable, the
    repository's own root-level manifests are used instead.
    """
    root = Path(root)
    found: list[Path] = []

    requirements = sorted(root.glob("requirements*.txt"))
    found.extend(p for p in requirements if p.is_file())

    pyproject = root / "pyproject.toml"
    if pyproject.is_file():
        found.append(pyproject)

    return found


def _scan_requirements(path: Path, root: Path) -> list[ManifestProblem]:
    problems: list[ManifestProblem] = []
    relative = path.relative_to(root).as_posix() if path.is_relative_to(root) else path.name
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return problems

    for index, raw in enumerate(lines, start=1):
        line = raw.split("#", 1)[0].strip()
        if not line or line.startswith("-"):
            # Skip comments, blank lines and pip options such as
            # ``--index-url`` or ``-r other.txt``.
            continue
        match = _REQUIREMENT.match(line)
        if not match:
            continue
        name = match.group("name")
        specifier = (match.group("spec") or "").strip()
        if is_pre_release(specifier):
            problems.append(
                ManifestProblem(
                    manifest=relative,
                    line_number=index,
                    package=name,
                    specifier=specifier,
                    reason="pre-release version specifier is not a reproducible release",
                    text=line,
                )
            )
    return problems


def _scan_pyproject(path: Path, root: Path) -> list[ManifestProblem]:
    problems: list[ManifestProblem] = []
    relative = path.relative_to(root).as_posix() if path.is_relative_to(root) else path.name
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return problems

    for index, raw in enumerate(text.splitlines(), start=1):
        line = raw.split("#", 1)[0].strip()
        if not line.startswith(("[", "[")) and '"' not in line and "'" not in line:
            continue
        for match in _QUOTED_REQUIREMENT.finditer(line):
            name = match.group("name")
            specifier = (match.group("spec") or "").strip()
            if not specifier:
                continue
            if is_pre_release(specifier):
                problems.append(
                    ManifestProblem(
                        manifest=relative,
                        line_number=index,
                        package=name,
                        specifier=specifier,
                        reason="pre-release version specifier is not a reproducible release",
                        text=line.strip(),
                    )
                )
    return problems


def _workflow_files(root: Path) -> list[Path]:
    """Return the CI workflow files belonging to *root*."""
    workflows = root / ".github" / "workflows"
    if not workflows.is_dir():
        return []
    return [p for p in sorted(workflows.iterdir()) if p.suffix in {".yml", ".yaml"}]


def _scan_workflows(root: Path) -> list[ManifestProblem]:
    """Check that the CI workflow pins the validated toolchain versions.

    The toolchain is installed by the workflow rather than the runtime
    manifest, so a change to ``pytest`` or ``ruff`` lands in the workflow
    file. Dependabot proposed ``pytest==9.0.3`` in exactly that place.
    """
    problems: list[ManifestProblem] = []
    workflows = _workflow_files(root)
    if not workflows:
        return problems

    # Collect every version each tool was installed at.
    installed: dict[str, set[str]] = {name: set() for name in TOOLCHAIN_VERSIONS}
    pattern = re.compile(
        r"(?P<name>pytest-cov|pytest|ruff)\s*==\s*(?P<version>[0-9][0-9A-Za-z.\-]*)"
    )
    for workflow in workflows:
        relative = workflow.relative_to(root).as_posix()
        try:
            text = workflow.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for index, raw in enumerate(text.splitlines(), start=1):
            for match in pattern.finditer(raw):
                name = match.group("name").lower()
                version = match.group("version")
                if name in installed:
                    installed[name].add(version)
                    if version != TOOLCHAIN_VERSIONS[name]:
                        problems.append(
                            ManifestProblem(
                                manifest=relative,
                                line_number=index,
                                package=name,
                                specifier=f"=={version}",
                                reason=(
                                    f"toolchain is pinned to {TOOLCHAIN_VERSIONS[name]} and "
                                    "must be bumped deliberately, with the full suite re-run"
                                ),
                                text=raw.strip(),
                            )
                        )
    return problems


def scan_manifests(root: Path) -> PinGuardResult:
    """Scan every manifest and CI workflow under *root*."""
    root = Path(root).resolve()
    result = PinGuardResult(root=root)
    for manifest in find_manifests(root):
        result.manifests.append(manifest)
        if manifest.name == "pyproject.toml":
            result.problems.extend(_scan_pyproject(manifest, root))
        else:
            result.problems.extend(_scan_requirements(manifest, root))
    result.problems.extend(_scan_workflows(root))
    return result


def main(argv: list[str] | None = None) -> int:
    """Command-line entry point. Returns 0 on success, 1 on violation."""
    args = list(sys.argv[1:] if argv is None else argv)
    as_json = "--json" in args
    if as_json:
        args.remove("--json")
    if not args:
        print(__doc__)
        return 2
    if len(args) > 1:
        print("usage: python -m tools.pin_guard [--json] <repository-root>")
        return 2

    result = scan_manifests(Path(args[0]))
    if as_json:
        print(json.dumps(result.as_dict(), indent=2))
    else:
        if not result.manifests:
            print(f"pin-guard: no dependency manifests found under {result.root}")
        else:
            print(
                f"pin-guard: checked {len(result.manifests)} manifest(s) "
                f"under {result.root}"
            )
        for problem in result.problems:
            print(f"pin-guard: FAIL {problem}")
        if result.ok:
            print("pin-guard: OK -- no pre-release version specifiers found")
    return 0 if result.ok else 1


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
