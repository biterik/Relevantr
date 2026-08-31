# SPDX-License-Identifier: AGPL-3.0-or-later
"""PyInstaller entry point.

`src/relevantr/__main__.py` uses relative imports, which fail when PyInstaller
runs it as a top-level script; importing it as a package module instead gives
it the proper package context.

`freeze_support()` is required in the frozen app: torch/sentence-transformers
start multiprocessing helper processes (resource tracker) by re-invoking this
executable, and PyInstaller's patched freeze_support diverts those invocations
before they reach the CLI parser.
"""

import multiprocessing
import sys

from relevantr.__main__ import main

if __name__ == "__main__":
    multiprocessing.freeze_support()
    sys.exit(main())
