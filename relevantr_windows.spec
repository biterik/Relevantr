# -*- mode: python ; coding: utf-8 -*-
# Comprehensive PyInstaller spec file for Relevantr Windows build

import sys
import os
from pathlib import Path

# Get the conda environment site-packages path
conda_prefix = os.environ.get('CONDA_PREFIX')
if conda_prefix:
    site_packages = os.path.join(conda_prefix, 'Lib', 'site-packages')
else:
    site_packages = os.path.join(sys.prefix, 'Lib', 'site-packages')

print(f"Using site-packages: {site_packages}")

block_cipher = None

# Manually add package paths
package_paths = [
    ('google', 'google'),
    ('langchain', 'langchain'),
    ('langchain_community', 'langchain_community'),
    ('langchain_google_genai', 'langchain_google_genai'),
    ('langchain_core', 'langchain_core'),  # Often needed by langchain_google_genai
    ('chromadb', 'chromadb'),
    ('tqdm', 'tqdm'),
    ('dotenv', 'dotenv'),
]

datas = [
    # Environment files
    ('environment.yml', '.'),
    ('requirements.txt', '.'),
]

# Add packages as data if they exist
for package_name, dest_name in package_paths:
    package_path = os.path.join(site_packages, package_name)
    if os.path.exists(package_path):
        datas.append((package_path, dest_name))
        print(f"Added {package_name} from: {package_path}")
    else:
        print(f"WARNING: {package_name} not found at: {package_path}")

binaries = []

# Add Python DLL for Windows
if sys.platform == "win32":
    python_dll_name = f"python{sys.version_info.major}{sys.version_info.minor}.dll"
    possible_dll_paths = [
        os.path.join(os.path.dirname(sys.executable), python_dll_name),
        os.path.join(conda_prefix or '', python_dll_name),
        os.path.join(conda_prefix or '', 'Library', 'bin', python_dll_name),
    ]
    
    for dll_path in possible_dll_paths:
        if os.path.exists(dll_path):
            binaries.append((dll_path, '.'))
            print(f"Added Python DLL: {dll_path}")
            break

a = Analysis(
    ['relevantr.py'],
    pathex=[site_packages],  # Add site-packages to Python path
    binaries=binaries,
    datas=datas,
    hiddenimports=[
        # Core Python modules
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.scrolledtext',
        '_tkinter',
        
        # Google AI - comprehensive list
        'google',
        'google.generativeai',
        'google.generativeai.client',
        'google.generativeai.types',
        'google.generativeai.types.generation_types',
        'google.generativeai.types.safety_types',
        'google.api_core',
        'google.api_core.client_options',
        'google.api_core.gapic_v1',
        'google.auth',
        'google.auth.transport',
        'google.auth.transport.requests',
        'google.protobuf',
        'google.rpc',
        
        # LangChain - COMPREHENSIVE
        'langchain',
        'langchain.text_splitter',
        'langchain.schema',
        'langchain.schema.document',
        'langchain.document_loaders',
        'langchain.vectorstores',
        'langchain.embeddings',
        'langchain.chat_models',
        
        # LangChain Community - CRITICAL
        'langchain_community',
        'langchain_community.document_loaders',
        'langchain_community.document_loaders.base',
        'langchain_community.document_loaders.pdf',
        'langchain_community.document_loaders.pymupdf',
        'langchain_community.vectorstores',
        'langchain_community.vectorstores.base',
        'langchain_community.vectorstores.chroma',
        'langchain_community.embeddings',
        'langchain_community.utils',
        
        # LangChain Google GenAI
        'langchain_google_genai',
        'langchain_google_genai.embeddings',
        'langchain_google_genai.chat_models',
        'langchain_google_genai.llms',
        
        # ChromaDB
        'chromadb',
        'chromadb.config',
        'chromadb.utils',
        'chromadb.api',
        'chromadb.api.models',
        'chromadb.db',
        'chromadb.db.impl',
        'chromadb.db.impl.sqlite',
        
        # PDF processing
        'fitz',
        'pymupdf',
        
        # Utilities
        'tqdm',
        'dotenv',
        'warnings',
        'logging',
        'threading',
        'json',
        'datetime',
        'dataclasses',
        'typing',
        'pathlib',
        'sqlite3',
        'ssl',
        'certifi',
        'urllib3',
        'requests',
        'http',
        'http.client',
        'urllib',
        'urllib.request',
        'urllib.parse',
        
        # Additional dependencies
        'numpy',
        'packaging',
        'importlib_metadata',
        'grpcio',
        'proto-plus',
        'protobuf',
        'pydantic',
        'pydantic_core',
        'yaml',
        'tenacity',
        'jsonschema',
        'click',
        'colorama',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Large packages we don't need
        'matplotlib',
        'scipy',
        'pandas',
        'jupyter',
        'IPython',
        'notebook',
        'pytest',
        'PIL',
        'cv2',
        'sklearn',
        'tensorflow',
        'torch',
    ],
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
    debug=False,  # Set to True for debugging
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Set to True to see error messages during development
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
