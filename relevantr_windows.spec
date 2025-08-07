# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

# Get the absolute path to the script directory
script_dir = Path(__file__).parent.absolute()

block_cipher = None

# Hidden imports for Windows compatibility
hidden_imports = [
    # Core dependencies
    'google.generativeai',
    'google.ai.generativelanguage',
    'langchain',
    'langchain_community',
    'langchain_community.document_loaders',
    'langchain_community.vectorstores',
    'langchain_google_genai',
    'langchain_core',
    'langchain.text_splitter',
    'chromadb',
    'chromadb.config',
    'chromadb.utils',
    
    # PDF processing
    'fitz',  # PyMuPDF
    'pymupdf',
    
    # Utilities
    'tqdm',
    'dotenv',
    'json',
    'threading',
    'logging',
    'traceback',
    'dataclasses',
    'datetime',
    
    # Tkinter (should be included but let's be explicit)
    'tkinter',
    'tkinter.ttk',
    'tkinter.filedialog',
    'tkinter.messagebox',
    'tkinter.scrolledtext',
    
    # Additional ChromaDB dependencies
    'sqlite3',
    'uuid',
    'hnswlib',
    'sentence_transformers',
    'transformers',
    'torch',
    'numpy',
    'pandas',
    
    # Google API dependencies
    'grpc',
    'google.auth',
    'google.api_core',
    'google.protobuf',
    'requests',
    'urllib3',
    'certifi',
    'charset_normalizer',
    'idna',
    
    # Other potential dependencies
    'pkg_resources',
    'packaging',
    'importlib_metadata',
]

# Data files to include
datas = [
    # Include any data files if needed
    # ('path/to/data/file', 'destination/in/bundle')
]

# Binary files to exclude (these can cause issues)
excludes = [
    'matplotlib',
    'scipy',
    'IPython',
    'jupyter',
    'notebook',
    'pytest',
    'setuptools',
    'pip',
    'wheel',
]

a = Analysis(
    ['relevantr.py'],
    pathex=[str(script_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Remove duplicate entries
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
    console=False,  # Set to True for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add path to .ico file if you have one
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
