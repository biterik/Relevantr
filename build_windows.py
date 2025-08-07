#!/usr/bin/env python3
"""
Windows-specific build script for Relevantr
Uses a comprehensive spec file to ensure all dependencies are included
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_environment():
    """Check if we're in the right environment"""
    print("[CHECK] Verifying environment...")
    
    # Check if we're in conda
    conda_prefix = os.environ.get('CONDA_PREFIX')
    if conda_prefix:
        print(f"[OK] Using conda environment: {conda_prefix}")
    else:
        print("[WARNING] Not in a conda environment")
    
    # Check critical imports
    critical_modules = ['google.generativeai', 'langchain', 'chromadb', 'tkinter']
    missing = []
    
    for module in critical_modules:
        try:
            __import__(module)
            print(f"[OK] {module} available")
        except ImportError:
            print(f"[ERROR] {module} missing")
            missing.append(module)
    
    if missing:
        print(f"[ERROR] Missing modules: {missing}")
        print("Install with: pip install google-generativeai langchain langchain-community langchain-google-genai chromadb pymupdf tqdm python-dotenv")
        return False
    
    return True

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
    print("[BUILD] Building with comprehensive spec file...")
    
    if not os.path.exists("relevantr_windows.spec"):
        print("[ERROR] relevantr_windows.spec not found!")
        print("Make sure to create the spec file first.")
        return False
    
    try:
        cmd = ['pyinstaller', 'relevantr_windows.spec']
        print(f"[CMD] Running: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("[OK] Build completed successfully!")
        print(f"[RESULT] Application built in: {Path('dist/Relevantr').absolute()}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Build failed: {e}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False

def test_built_app():
    """Test if the built application can start"""
    exe_path = Path("dist/Relevantr/Relevantr.exe")
    if exe_path.exists():
        print(f"[TEST] Built executable found: {exe_path}")
        print("[INFO] To test the app, run:")
        print(f"       cd dist\\Relevantr")
        print(f"       Relevantr.exe")
        return True
    else:
        print("[ERROR] Built executable not found!")
        return False

def create_debug_version():
    """Create a console version for debugging"""
    print("[DEBUG] Creating debug version with console...")
    
    # Read the spec file and modify for debugging
    with open("relevantr_windows.spec", "r") as f:
        spec_content = f.read()
    
    # Create debug version
    debug_spec = spec_content.replace("console=False", "console=True")
    debug_spec = debug_spec.replace("debug=False", "debug=True")
    debug_spec = debug_spec.replace("name='Relevantr'", "name='Relevantr_Debug'")
    
    with open("relevantr_debug.spec", "w") as f:
        f.write(debug_spec)
    
    try:
        cmd = ['pyinstaller', 'relevantr_debug.spec']
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("[OK] Debug version created: dist/Relevantr_Debug/Relevantr_Debug.exe")
        print("[INFO] Use debug version to see error messages in console")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Debug build failed: {e}")
        return False

def main():
    """Main build process"""
    print("=" * 60)
    print("Relevantr Windows Build Script")
    print("=" * 60)
    
    if not check_environment():
        sys.exit(1)
    
    if not os.path.exists("relevantr.py"):
        print("[ERROR] relevantr.py not found in current directory")
        sys.exit(1)
    
    # Clean and build
    clean_build()
    
    if build_with_spec():
        if test_built_app():
            print("\n[SUCCESS] Build completed successfully!")
            print("[INFO] Application ready in dist/Relevantr/")
            
            # Offer to create debug version
            create_debug = input("\nCreate debug version with console? (y/n): ").lower().strip()
            if create_debug.startswith('y'):
                create_debug_version()
            
        else:
            print("\n[WARNING] Build completed but executable not found")
    else:
        print("\n[FAILED] Build process failed!")
        print("\n[TIP] Try the debug version to see error messages:")
        create_debug_version()
        sys.exit(1)

if __name__ == "__main__":
    main()
