#!/usr/bin/env python3
"""
Simple Windows build script for Relevantr
Avoids Unicode issues and focuses on getting a working build
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_basic_requirements():
    """Basic requirement check without Unicode characters"""
    print("[CHECK] Verifying basic requirements...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("[ERROR] Python 3.8+ required")
        return False
    print(f"[OK] Python {sys.version_info.major}.{sys.version_info.minor}")
    
    # Check PyInstaller
    try:
        import PyInstaller
        print(f"[OK] PyInstaller {PyInstaller.__version__}")
    except ImportError:
        print("[ERROR] PyInstaller not found. Install with: pip install pyinstaller")
        return False
    
    # Check if main script exists
    if not os.path.exists("relevantr.py"):
        print("[ERROR] relevantr.py not found in current directory")
        return False
    print("[OK] relevantr.py found")
    
    return True

def clean_build():
    """Clean previous build artifacts"""
    print("[CLEAN] Removing old build files...")
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"[CLEAN] Removing {dir_name}/")
            shutil.rmtree(dir_name)

def create_simple_spec():
    """Create a minimal, working spec file"""
    print("[SPEC] Creating simple spec file...")
    
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Core hidden imports - includes ChromaDB telemetry fix
hidden_imports = [
    # Google AI
    'google.generativeai',
    'google.ai.generativelanguage',
    'google.protobuf',
    'google.auth',
    'google.api_core',
    
    # LangChain
    'langchain',
    'langchain_community',
    'langchain_community.document_loaders',
    'langchain_community.vectorstores', 
    'langchain_google_genai',
    'langchain_core',
    'langchain.text_splitter',
    
    # ChromaDB with telemetry modules (fixes the missing module error)
    'chromadb',
    'chromadb.api',
    'chromadb.config',
    'chromadb.utils',
    'chromadb.telemetry',
    'chromadb.telemetry.product',
    'chromadb.telemetry.product.posthog',
    'chromadb.telemetry.events',
    'chromadb.db',
    'chromadb.db.impl',
    'chromadb.segment',
    'chromadb.segment.impl',
    'chromadb.segment.impl.vector',
    'chromadb.segment.impl.vector.local_hnsw',
    
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
    'sqlite3',
    'json',
    'threading',
    'logging',
    'uuid',
    'pathlib',
    'dataclasses',
    'datetime',
    'traceback',
    
    # Additional ChromaDB dependencies
    'hnswlib',
    'posthog',
    'requests',
    'urllib3',
    'certifi',
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
    excludes=['matplotlib', 'scipy', 'numpy', 'pandas'],
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
'''
    
    with open("relevantr_simple.spec", "w", encoding='utf-8') as f:
        f.write(spec_content)
    
    print("[OK] Simple spec file created")
    return True

def create_debug_spec():
    """Create debug version spec file"""
    print("[DEBUG] Creating debug spec file...")
    
    # Read the simple spec and modify for debugging
    with open("relevantr_simple.spec", "r", encoding='utf-8') as f:
        spec_content = f.read()
    
    debug_spec = spec_content.replace("console=False", "console=True")
    debug_spec = debug_spec.replace("name='Relevantr'", "name='Relevantr_Debug'")
    
    with open("relevantr_debug.spec", "w", encoding='utf-8') as f:
        f.write(debug_spec)
    
    print("[OK] Debug spec file created")
    return True

def build_application(spec_file, app_name):
    """Build the application using PyInstaller"""
    print(f"[BUILD] Building {app_name}...")
    
    try:
        cmd = ['pyinstaller', '--clean', '--noconfirm', spec_file]
        print(f"[CMD] {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True, 
                              encoding='utf-8', errors='replace', timeout=300)
        
        if result.returncode == 0:
            print(f"[OK] {app_name} built successfully")
            return True
        else:
            print(f"[ERROR] {app_name} build failed")
            print("STDOUT:", result.stdout[-500:])  # Last 500 chars
            print("STDERR:", result.stderr[-500:])  # Last 500 chars
            return False
            
    except subprocess.TimeoutExpired:
        print(f"[ERROR] {app_name} build timed out")
        return False
    except Exception as e:
        print(f"[ERROR] {app_name} build failed: {e}")
        return False

def test_executable(exe_path):
    """Test if executable exists and get info"""
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"[OK] Executable found: {exe_path}")
        print(f"[INFO] Size: {size_mb:.1f} MB")
        return True
    else:
        print(f"[ERROR] Executable not found: {exe_path}")
        return False

def create_debug_batch():
    """Create simple debug batch file"""
    batch_content = '''@echo off
echo Starting Relevantr Debug...
echo.

cd /d "%~dp0"

echo Running debug version...
echo Output will be saved to debug.log
echo.

Relevantr_Debug.exe > debug.log 2>&1

set EXIT_CODE=%errorlevel%

echo.
if %EXIT_CODE% equ 0 (
    echo Success: No errors detected
) else (
    echo Error detected. Exit code: %EXIT_CODE%
    echo.
    echo Last 10 lines of debug.log:
    echo ========================
    powershell "Get-Content debug.log | Select-Object -Last 10"
    echo ========================
)

echo.
echo Full log saved to debug.log
echo Press any key to exit...
pause > nul
'''
    
    debug_dir = Path("dist/Relevantr_Debug")
    if debug_dir.exists():
        batch_path = debug_dir / "debug_run.bat"
        with open(batch_path, "w", encoding='ascii', errors='replace') as f:
            f.write(batch_content)
        print(f"[OK] Debug batch created: {batch_path}")

def main():
    """Main build process"""
    print("=" * 50)
    print("Relevantr Simple Windows Build")
    print("=" * 50)
    
    # Basic checks
    if not check_basic_requirements():
        print("\n[FAILED] Requirements not met")
        sys.exit(1)
    
    # Clean old builds
    clean_build()
    
    # Create spec files
    if not create_simple_spec():
        print("\n[FAILED] Could not create spec file")
        sys.exit(1)
    
    # Build main application
    print("\n[STEP 1] Building main application...")
    if build_application("relevantr_simple.spec", "Relevantr"):
        exe_path = Path("dist/Relevantr/Relevantr.exe")
        if test_executable(exe_path):
            print("\n[SUCCESS] Main application built successfully!")
            print(f"[INFO] Location: {exe_path.absolute()}")
        else:
            print("\n[WARNING] Build completed but executable not found")
    else:
        print("\n[FAILED] Main application build failed")
    
    # Build debug version
    print("\n[STEP 2] Building debug version...")
    create_debug_spec()
    if build_application("relevantr_debug.spec", "Relevantr_Debug"):
        debug_exe = Path("dist/Relevantr_Debug/Relevantr_Debug.exe")
        if test_executable(debug_exe):
            create_debug_batch()
            print("\n[SUCCESS] Debug version built successfully!")
            print(f"[INFO] Location: {debug_exe.absolute()}")
            print(f"[USAGE] Run debug_run.bat in the debug folder to troubleshoot issues")
        else:
            print("\n[WARNING] Debug build completed but executable not found")
    else:
        print("\n[FAILED] Debug version build failed")
    
    print("\n" + "=" * 50)
    print("Build process complete!")
    print("=" * 50)
    
    # Final instructions
    print("\nNEXT STEPS:")
    print("1. Test the main app: dist\\Relevantr\\Relevantr.exe")
    print("2. If it doesn't work, run: dist\\Relevantr_Debug\\debug_run.bat")
    print("3. Check debug.log for specific error messages")

if __name__ == "__main__":
    main()
