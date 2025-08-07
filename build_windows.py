#!/usr/bin/env python3
"""
Enhanced Windows-specific build script for Relevantr
Includes additional debugging and dependency fixes
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_environment():
    """Check if we're in the right environment with additional Windows checks"""
    print("[CHECK] Verifying environment...")
    
    # Check if we're in conda
    conda_prefix = os.environ.get('CONDA_PREFIX')
    if conda_prefix:
        print(f"[OK] Using conda environment: {conda_prefix}")
    else:
        print("[WARNING] Not in a conda environment")
    
    # Check Python version
    python_version = sys.version_info
    if python_version >= (3, 11):
        print(f"[OK] Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    else:
        print(f"[WARNING] Python {python_version.major}.{python_version.minor}.{python_version.micro} - Python 3.11+ recommended")
    
    # Check critical imports with more detailed error reporting
    critical_modules = {
        'tkinter': 'Built into Python',
        'google.generativeai': 'google-generativeai',
        'langchain': 'langchain',
        'langchain_community': 'langchain-community',
        'langchain_google_genai': 'langchain-google-genai',
        'chromadb': 'chromadb',
        'fitz': 'pymupdf',
        'tqdm': 'tqdm',
        'dotenv': 'python-dotenv'
    }
    
    missing = []
    
    for module, package in critical_modules.items():
        try:
            imported_module = __import__(module)
            version = getattr(imported_module, '__version__', 'unknown')
            print(f"[OK] {module} available (version: {version})")
        except ImportError as e:
            print(f"[ERROR] {module} missing: {e}")
            missing.append(package)
    
    # Check PyInstaller
    try:
        import PyInstaller
        print(f"[OK] PyInstaller {PyInstaller.__version__} available")
    except ImportError:
        print("[ERROR] PyInstaller not installed")
        missing.append('pyinstaller')
    
    if missing:
        print(f"[ERROR] Missing packages: {missing}")
        print("Install with: pip install " + " ".join(missing))
        return False
    
    return True

def create_enhanced_spec():
    """Create an enhanced spec file with Windows-specific fixes"""
    print("[SPEC] Creating enhanced Windows spec file...")
    
    spec_content = """# -*- mode: python ; coding: utf-8 -*-

import sys
import os

# No need for Path operations in spec file

block_cipher = None

# Enhanced hidden imports for Windows
hidden_imports = [
    # Core AI dependencies
    'google.generativeai',
    'google.ai.generativelanguage',
    'google.protobuf',
    'google.auth',
    'google.api_core',
    'grpc',
    'grpc._channel',
    
    # LangChain ecosystem
    'langchain',
    'langchain_community',
    'langchain_community.document_loaders',
    'langchain_community.document_loaders.pdf',
    'langchain_community.vectorstores',
    'langchain_community.vectorstores.chroma',
    'langchain_google_genai',
    'langchain_core',
    'langchain.text_splitter',
    
    # ChromaDB and dependencies
    'chromadb',
    'chromadb.config',
    'chromadb.utils',
    'chromadb.api',
    'sqlite3',
    'hnswlib',
    
    # PDF processing
    'fitz',
    'pymupdf',
    
    # Standard library modules that might need explicit inclusion
    'tkinter',
    'tkinter.ttk',
    'tkinter.filedialog',
    'tkinter.messagebox',
    'tkinter.scrolledtext',
    'json',
    'threading',
    'logging',
    'traceback',
    'dataclasses',
    'datetime',
    'pathlib',
    'uuid',
    
    # Utilities
    'tqdm',
    'dotenv',
    'requests',
    'urllib3',
    'certifi',
    'packaging',
    
    # Additional dependencies that might be missing
    'numpy',
    'typing_extensions',
    'pydantic',
    'pydantic_core',
    'tenacity',
    'charset_normalizer',
    'idna',
]

# Data files and binaries
datas = []

# Add any necessary data files
# Try to find and include important data files
try:
    import chromadb
    chromadb_path = os.path.dirname(chromadb.__file__)
    # Include chromadb data files if they exist
    for root, dirs, files in os.walk(chromadb_path):
        for file in files:
            if file.endswith(('.json', '.yaml', '.yml', '.txt')):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, chromadb_path)
                datas.append((full_path, f'chromadb/{rel_path}'))
except:
    pass

# Exclude problematic packages
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
    'conda',
]

a = Analysis(
    ['relevantr.py'],
    pathex=[],
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

# Remove duplicates
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
    console=False,  # No console for release
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
"""
    
    with open("relevantr_windows.spec", "w") as f:
        f.write(spec_content)
    
    print("[OK] Enhanced spec file created: relevantr_windows.spec")

def test_imports():
    """Test critical imports before building"""
    print("[TEST] Testing critical imports...")
    
    test_script = """
import sys
print("Testing imports...")

try:
    import tkinter as tk
    print("✓ tkinter OK")
except Exception as e:
    print(f"✗ tkinter ERROR: {e}")

try:
    import google.generativeai as genai
    print("✓ google.generativeai OK")
except Exception as e:
    print(f"✗ google.generativeai ERROR: {e}")

try:
    from langchain_community.document_loaders import PyMuPDFLoader
    print("✓ langchain_community OK")
except Exception as e:
    print(f"✗ langchain_community ERROR: {e}")

try:
    import chromadb
    print("✓ chromadb OK")
except Exception as e:
    print(f"✗ chromadb ERROR: {e}")

try:
    import fitz
    print("✓ PyMuPDF OK")
except Exception as e:
    print(f"✗ PyMuPDF ERROR: {e}")

print("Import test complete.")
"""
    
    try:
        result = subprocess.run([sys.executable, "-c", test_script], 
                              capture_output=True, text=True, timeout=30)
        print("[TEST RESULTS]")
        print(result.stdout)
        if result.stderr:
            print("[TEST ERRORS]")
            print(result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"[ERROR] Import test failed: {e}")
        return False

def clean_build():
    """Clean previous build artifacts"""
    print("[CLEAN] Removing old build files...")
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"[CLEAN] Removing {dir_name}/")
            shutil.rmtree(dir_name)

def build_with_spec():
    """Build using the comprehensive spec file"""
    print("[BUILD] Building with enhanced spec file...")
    
    if not os.path.exists("relevantr_windows.spec"):
        print("[ERROR] relevantr_windows.spec not found!")
        return False
    
    try:
        # Use more verbose output
        cmd = ['pyinstaller', '--clean', '--noconfirm', 'relevantr_windows.spec']
        print(f"[CMD] Running: {' '.join(cmd)}")
        
        # Run with real-time output
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                 text=True, universal_newlines=True)
        
        # Show output in real time
        for line in iter(process.stdout.readline, ''):
            print(f"[BUILD] {line.rstrip()}")
        
        process.wait()
        
        if process.returncode == 0:
            print("[OK] Build completed successfully!")
            print(f"[RESULT] Application built in: {Path('dist/Relevantr').absolute()}")
            return True
        else:
            print(f"[ERROR] Build failed with return code: {process.returncode}")
            return False
            
    except subprocess.TimeoutExpired:
        print("[ERROR] Build timed out")
        return False
    except Exception as e:
        print(f"[ERROR] Build failed: {e}")
        return False

# Rest of the functions remain the same...
def test_built_app():
    """Test if the built application can start"""
    exe_path = Path("dist/Relevantr/Relevantr.exe")
    if exe_path.exists():
        print(f"[TEST] Built executable found: {exe_path}")
        print(f"[INFO] Executable size: {exe_path.stat().st_size / (1024*1024):.1f} MB")
        print("[INFO] To test the app, run:")
        print(f"       cd dist\\Relevantr")
        print(f"       Relevantr.exe")
        return True
    else:
        print("[ERROR] Built executable not found!")
        return False

def create_debug_version():
    """Create a console version for debugging with error logging"""
    print("[DEBUG] Creating debug version with console and error logging...")
    
    # Read the spec file and modify for debugging
    with open("relevantr_windows.spec", "r") as f:
        spec_content = f.read()
    
    # Create debug version with console enabled
    debug_spec = spec_content.replace("console=False", "console=True")
    debug_spec = debug_spec.replace("debug=False", "debug=True")
    debug_spec = debug_spec.replace("name='Relevantr'", "name='Relevantr_Debug'")
    
    with open("relevantr_debug.spec", "w") as f:
        f.write(debug_spec)
    
    try:
        cmd = ['pyinstaller', '--clean', '--noconfirm', 'relevantr_debug.spec']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            create_debug_batch()
            print("[OK] Debug version created: dist/Relevantr_Debug/Relevantr_Debug.exe")
            print("[INFO] Use debug_run.bat to capture error messages to debug.log")
            return True
        else:
            print(f"[ERROR] Debug build failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Debug build failed: {e}")
        return False

def create_debug_batch():
    """Create a comprehensive batch file for debugging"""
    batch_content = """@echo off
echo ============================================
echo Relevantr Debug Version
echo ============================================
echo.
echo This will run Relevantr in debug mode and capture all output
echo to debug.log for troubleshooting.
echo.
echo Press any key to start...
pause > nul

cd /d "%~dp0"

echo ============================================ > debug.log
echo Relevantr Debug Log >> debug.log
echo Started at: %date% %time% >> debug.log
echo Current directory: %CD% >> debug.log
echo ============================================ >> debug.log
echo. >> debug.log

echo Running Relevantr Debug...
echo Output is being captured to debug.log
echo.

echo Starting Relevantr_Debug.exe... >> debug.log
Relevantr_Debug.exe >> debug.log 2>&1

set EXIT_CODE=%errorlevel%

echo. >> debug.log
echo ============================================ >> debug.log
echo Finished at: %date% %time% >> debug.log
echo Exit code: %EXIT_CODE% >> debug.log
echo ============================================ >> debug.log

echo.
echo ============================================
if %EXIT_CODE% equ 0 (
    echo SUCCESS: Relevantr ran without errors
    echo Check debug.log for any warnings or info messages
) else (
    echo ERROR: Relevantr failed to start properly
    echo Exit code: %EXIT_CODE%
    echo.
    echo Last 20 lines from debug.log:
    echo ----------------------------------------
    powershell "Get-Content debug.log | Select-Object -Last 20"
    echo ----------------------------------------
)
echo.
echo Full debug log saved to: debug.log
echo.
echo Press any key to exit...
pause > nul
"""
    
    batch_path = Path("dist") / "Relevantr_Debug" / "debug_run.bat"
    batch_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(batch_path, "w", encoding='ascii', errors='replace') as f:
        f.write(batch_content)
    
    print(f"[OK] Created debug batch file: {batch_path}")

def main():
    """Enhanced main build process"""
    print("=" * 60)
    print("Relevantr Enhanced Windows Build Script")
    print("=" * 60)
    
    if not check_environment():
        print("\n[CRITICAL] Environment check failed!")
        print("Please install missing dependencies and try again.")
        sys.exit(1)
    
    if not os.path.exists("relevantr.py"):
        print("[ERROR] relevantr.py not found in current directory")
        sys.exit(1)
    
    # Test imports before building
    if not test_imports():
        print("[WARNING] Some imports failed. Build may not work correctly.")
        proceed = input("Continue anyway? (y/n): ").lower().strip()
        if not proceed.startswith('y'):
            sys.exit(1)
    
    # Create enhanced spec file
    create_enhanced_spec()
    
    # Clean and build
    clean_build()
    
    print("\n[BUILD] Starting build process...")
    if build_with_spec():
        if test_built_app():
            print("\n" + "="*60)
            print("🎉 BUILD SUCCESSFUL!")
            print("="*60)
            print("[SUCCESS] Relevantr built successfully!")
            print("[INFO] Application ready in dist/Relevantr/")
            
            # Always create debug version for troubleshooting
            print("\n[DEBUG] Creating debug version for troubleshooting...")
            create_debug_version()
            
        else:
            print("\n[WARNING] Build completed but executable not found")
    else:
        print("\n" + "="*60)
        print("❌ BUILD FAILED!")
        print("="*60)
        print("[FAILED] Build process failed!")
        print("\n[TROUBLESHOOTING] Creating debug version...")
        create_debug_version()
        print("\n[NEXT STEPS]")
        print("1. Run dist/Relevantr_Debug/debug_run.bat")
        print("2. Check debug.log for specific error messages")
        print("3. Install any missing dependencies")
        print("4. Try building again")
        sys.exit(1)

if __name__ == "__main__":
    main()
