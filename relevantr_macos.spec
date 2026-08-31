# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for the macOS build of Relevantr v2: one-dir .app bundle.
# Build with `python build.py` in an environment where `pip install ".[local]"`
# has been done. Torch from PyPI is already CPU/MPS-only on macOS, so no
# special index is needed here (unlike Linux/Windows).
from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = [
    "fitz",
    "keyring.backends.macOS",
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

# One-dir mode (exclude_binaries + COLLECT): faster startup and friendlier to
# antivirus scanners than one-file.
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
    icon=["assets/icon.icns"],
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
app = BUNDLE(
    coll,
    name="Relevantr.app",
    icon="assets/icon.icns",
    bundle_identifier="com.github.biterik.relevantr",
)
