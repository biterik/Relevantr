# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for the macOS build of Relevantr v2 (src/relevantr package).
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

a = Analysis(
    ["src/relevantr/__main__.py"],
    pathex=["src"],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="Relevantr",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=["assets/icon.icns"],
)
app = BUNDLE(
    exe,
    name="Relevantr.app",
    icon="assets/icon.icns",
    bundle_identifier=None,
)
