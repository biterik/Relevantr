#!/usr/bin/env python3
"""Build the macOS app bundle for Relevantr v2 with PyInstaller.

The single macOS build path: cleans old build artifacts and runs
PyInstaller with relevantr.spec (which targets the src/relevantr package).
Run from the repository root, inside an environment where
`pip install -e ".[local]"` has been done.
"""

import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).parent


def main() -> int:
    if not (REPO / "src" / "relevantr" / "__main__.py").exists():
        print("[ERROR] run this from the Relevantr repository root")
        return 1
    try:
        import relevantr  # noqa: F401
    except ImportError:
        print('[ERROR] relevantr is not installed; run: pip install -e ".[local]"')
        return 1

    for name in ("build", "dist"):
        path = REPO / name
        if path.exists():
            print(f"[CLEAN] removing {name}/")
            shutil.rmtree(path)

    cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", "relevantr.spec"]
    print("[BUILD]", " ".join(cmd))
    result = subprocess.run(cmd, cwd=REPO)
    if result.returncode != 0:
        print("[ERROR] PyInstaller failed")
        return result.returncode

    print("[OK] built dist/Relevantr.app")
    return 0


if __name__ == "__main__":
    sys.exit(main())
