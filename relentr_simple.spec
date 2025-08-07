# -*- mode: python ; coding: utf-8 -*-
# Simple, reliable spec file for Relevantr Windows build

import os

block_cipher = None

# Essential hidden imports - only the most critical ones
hidden_imports = [
    # Core Google AI
    'google.generativeai',
    'google.ai.generativelanguage', 
    'google.protobuf',
    'google.auth',
    'google.api_core',
    
    # LangChain essentials
    'langchain',
    'langchain_community',
    'langchain_community.document_loaders',
    'langchain_community.vectorstores',
    'langchain_google_genai',
    'langchain_core',
    'langchain.text_splitter',
    
    # ChromaDB
    'chromadb',
    'chromadb.config',
    'chromadb.api',
    'sqlite3',
    
    # PDF processing
    'fitz',
    'pymupdf',
    
    # GUI
    'tkinter',
    'tkinter.ttk',
    'tkinter.filedialog',
    'tkinter.messagebox', 
    'tkinter.scrolledtext',
    
    # Utilities
    'tqdm',
    'dotenv',
    'requests',
    'json',
    'threading',
    'logging',
    'uuid',
    'pathlib',
    'dataclasses',
    'datetime',
    'traceback',
]

a = Analysis(
    ['relevantr.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Relevantr',
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
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Relevantr',
)
