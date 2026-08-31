#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Build the Relevantr standalone bundle for the current platform.

Dispatches on ``sys.platform`` to the matching PyInstaller spec
(``relevantr_macos.spec`` / ``relevantr_windows.spec`` / ``relevantr_linux.spec``)
and then produces the plain distributable artifact:

- macOS:   dist/Relevantr.app  + a compressed DMG (with /Applications symlink)
- Windows: dist/Relevantr/     + a .zip           (Inno Setup installer is CI's job)
- Linux:   dist/Relevantr/     + a .tar.gz        (AppImage is CI's job)

Run from the repository root, inside an environment where
``pip install ".[local]"`` and ``pip install pyinstaller`` have been done.
On Linux/Windows install torch from the CPU wheel index first
(``pip install torch --index-url https://download.pytorch.org/whl/cpu``).

``--version-tag vX.Y.Z[-rcN]`` (used by CI) names the artifacts after the git
tag and fails the build if the tag's base version does not match
``pyproject.toml``.
"""

import argparse
import platform
import shutil
import subprocess
import sys
import tarfile
import tomllib
import zipfile
from pathlib import Path

REPO = Path(__file__).parent


def pyproject_version() -> str:
    with open(REPO / "pyproject.toml", "rb") as fh:
        return tomllib.load(fh)["project"]["version"]


def artifact_version(version_tag: str | None) -> str:
    """Version string for artifact names; cross-checked against pyproject."""
    version = pyproject_version()
    if not version_tag:
        return version
    tag = version_tag.lstrip("v")
    base = tag.split("-", 1)[0]  # v2.0.0-rc1 -> 2.0.0
    if base != version:
        sys.exit(
            f"[ERROR] tag {version_tag!r} (base {base}) does not match "
            f"pyproject.toml version {version!r}"
        )
    return tag


def arch_name() -> str:
    machine = platform.machine().lower()
    return {"amd64": "x86_64", "aarch64": "arm64"}.get(machine, machine)


def run_pyinstaller(spec: str) -> None:
    for name in ("build", "dist"):
        path = REPO / name
        if path.exists():
            print(f"[CLEAN] removing {name}/")
            shutil.rmtree(path)
    cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", spec]
    print("[BUILD]", " ".join(cmd))
    subprocess.run(cmd, cwd=REPO, check=True)


def make_dmg(version: str) -> Path:
    staging = REPO / "dist" / "dmg"
    staging.mkdir()
    # ditto preserves the .app's symlinks/metadata; the original stays in
    # dist/ so it can be smoke-tested directly.
    subprocess.run(
        ["ditto", str(REPO / "dist" / "Relevantr.app"), str(staging / "Relevantr.app")],
        check=True,
    )
    (staging / "Applications").symlink_to("/Applications")
    dmg = REPO / "dist" / f"Relevantr-{version}-macos-{arch_name()}.dmg"
    subprocess.run(
        ["hdiutil", "create", "-volname", "Relevantr", "-srcfolder", str(staging),
         "-ov", "-format", "UDZO", str(dmg)],
        check=True,
    )
    return dmg


def make_zip(version: str) -> Path:
    out = REPO / "dist" / f"Relevantr-{version}-windows-{arch_name()}.zip"
    src = REPO / "dist" / "Relevantr"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(src.rglob("*")):
            zf.write(path, Path("Relevantr") / path.relative_to(src))
    return out


def make_targz(version: str) -> Path:
    out = REPO / "dist" / f"Relevantr-{version}-linux-{arch_name()}.tar.gz"
    with tarfile.open(out, "w:gz") as tf:
        tf.add(REPO / "dist" / "Relevantr", arcname="Relevantr")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version-tag", help="git tag (vX.Y.Z[-rcN]) to name artifacts")
    parser.add_argument(
        "--no-package", action="store_true",
        help="stop after PyInstaller; skip DMG/zip/tar.gz creation",
    )
    args = parser.parse_args()

    if not (REPO / "src" / "relevantr" / "__main__.py").exists():
        print("[ERROR] run this from the Relevantr repository root")
        return 1
    try:
        import relevantr  # noqa: F401
    except ImportError:
        print('[ERROR] relevantr is not installed; run: pip install ".[local]"')
        return 1

    version = artifact_version(args.version_tag)

    if sys.platform == "darwin":
        spec, bundle = "relevantr_macos.spec", "dist/Relevantr.app"
    elif sys.platform == "win32":
        spec, bundle = "relevantr_windows.spec", "dist/Relevantr"
    else:
        spec, bundle = "relevantr_linux.spec", "dist/Relevantr"

    run_pyinstaller(spec)
    print(f"[OK] built {bundle}")

    if args.no_package:
        return 0
    if sys.platform == "darwin":
        artifact = make_dmg(version)
    elif sys.platform == "win32":
        artifact = make_zip(version)
    else:
        artifact = make_targz(version)
    print(f"[OK] packaged {artifact.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
