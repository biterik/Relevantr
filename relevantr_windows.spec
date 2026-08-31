# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for the Windows build of Relevantr v2 (src/relevantr package).
from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = [
    "fitz",
    "keyring.backends.Windows",
    "tiktoken_ext.openai_public",
    "tiktoken_ext",
]
for package in ("lancedb", "sentence_transformers", "tiktoken", "keyring"):
    d, b, h = collect_all(package)
    datas += d
    binaries += b
    hiddenimports += h

excludes = [
    "matplotlib",
    "IPython",
    "jupyter",
    "notebook",
    "pytest",
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
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="Relevantr",
)
