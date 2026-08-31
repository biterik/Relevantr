# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for the Linux build of Relevantr v2: one-dir bundle.
# Build with `python build.py` in an environment where torch was installed
# from the CPU wheel index (https://download.pytorch.org/whl/cpu) BEFORE
# `pip install ".[local]"` — otherwise CUDA libraries balloon the bundle by
# gigabytes. Build on the oldest supported distro (ubuntu-22.04 in CI) for
# glibc compatibility; tkinter's tcl/tk data is picked up by PyInstaller's
# standard hook as long as the build Python has a working tkinter.
from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = [
    "fitz",
    "keyring.backends.SecretService",
    "keyring.backends.kwallet",
    "tiktoken_ext.openai_public",
    "tiktoken_ext",
]
for package in ("lancedb", "sentence_transformers", "tiktoken", "keyring"):
    d, b, h = collect_all(package)
    datas += d
    binaries += b
    hiddenimports += h

# Keep dev tools and CUDA support libraries out of the bundle.
excludes = [
    "matplotlib",
    "IPython",
    "jupyter",
    "notebook",
    "pytest",
    "nvidia",
    "triton",
    "cupy",
]

a = Analysis(
    ["src/relevantr/__main__.py"],
    pathex=["src"],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Relevantr",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="Relevantr",
)
