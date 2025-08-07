#!/usr/bin/env python3
"""
macOS-specific build script for Relevantr
Handles ChromaDB and other macOS-specific packaging issues
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import site

def get_site_packages():
    """Get the site-packages directory"""
    site_packages = site.getsitepackages()
    if site_packages:
        return site_packages[0]
    
    # Fallback for conda environments
    conda_prefix = os.environ.get('CONDA_PREFIX')
    if conda_prefix:
        return os.path.join(conda_prefix, 'lib', 'python' + sys.version[:3], 'site-packages')
    
    return None

def check_chromadb_modules():
    """Check which ChromaDB modules are available"""
    print("[CHECK] Verifying ChromaDB installation...")
    
    try:
        import chromadb
        import chromadb.telemetry
        import chromadb.telemetry.product
        import chromadb.telemetry.product.posthog
        print("[OK] All ChromaDB modules found")
        return True
    except ImportError as e:
        print(f"[ERROR] Missing ChromaDB module: {e}")
        return False

def build_mac_app():
    """Build macOS application with comprehensive ChromaDB support"""
    print("[BUILD] Building Relevantr for macOS...")
    
    # Clean previous builds
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"[CLEAN] Removing {dir_name}/")
            shutil.rmtree(dir_name)
    
    # Get site-packages path
    site_pkg = get_site_packages()
    if not site_pkg:
        print("[ERROR] Could not find site-packages directory")
        return False
    
    print(f"[INFO] Using site-packages: {site_pkg}")
    
    # Build command with comprehensive ChromaDB inclusion
    cmd = [
        'pyinstaller',
        '--windowed',
        '--onedir',
        '--name=Relevantr',
        
        # Add data files
        '--add-data=environment.yml:.',
        '--add-data=requirements.txt:.',
        
        # ChromaDB - COMPREHENSIVE INCLUSION
        f'--add-data={site_pkg}/chromadb:chromadb',
        '--hidden-import=chromadb',
        '--hidden-import=chromadb.config',
        '--hidden-import=chromadb.utils',
        '--hidden-import=chromadb.api',
        '--hidden-import=chromadb.db',
        '--hidden-import=chromadb.db.impl',
        '--hidden-import=chromadb.telemetry',
        '--hidden-import=chromadb.telemetry.product',
        '--hidden-import=chromadb.telemetry.product.posthog',
        '--hidden-import=chromadb.segment',
        '--collect-all=chromadb',
        
        # Google AI
        f'--add-data={site_pkg}/google:google',
        '--hidden-import=google',
        '--hidden-import=google.generativeai',
        '--collect-all=google',
        '--collect-all=google.generativeai',
        
        # LangChain
        f'--add-data={site_pkg}/langchain:langchain',
        f'--add-data={site_pkg}/langchain_community:langchain_community',
        f'--add-data={site_pkg}/langchain_google_genai:langchain_google_genai',
        '--collect-all=langchain',
        '--collect-all=langchain_community',
        '--collect-all=langchain_google_genai',
        
        # Core dependencies
        '--hidden-import=tkinter',
        '--hidden-import=tkinter.ttk',
        '--hidden-import=tkinter.filedialog',
        '--hidden-import=tkinter.messagebox',
        '--hidden-import=tkinter.scrolledtext',
        '--collect-all=tkinter',
        
        # PDF processing
        '--hidden-import=fitz',
        '--collect-all=pymupdf',
        
        # Utilities
        '--hidden-import=tqdm',
        '--hidden-import=dotenv',
        '--collect-all=tqdm',
        
        # Additional ChromaDB dependencies that might be missing
        '--hidden-import=posthog',
        '--hidden-import=segment_analytics_python',
        '--hidden-import=overrides',
        '--hidden-import=typing_extensions',
        '--hidden-import=pydantic',
        '--hidden-import=sqlite3',
        
        # Main script
        'relevantr.py'
    ]
    
    try:
        print(f"[CMD] Running PyInstaller...")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("[OK] Build completed successfully!")
        
        # Show build location
        app_path = Path("dist/Relevantr")
        print(f"[RESULT] Application built in: {app_path.absolute()}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Build failed: {e}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False

def create_app_bundle():
    """Create a proper macOS .app bundle"""
    print("[BUNDLE] Creating macOS .app bundle...")
    
    try:
        # Use --onefile for proper .app creation
        cmd = [
            'pyinstaller',
            '--windowed',
            '--onefile',  # Creates .app bundle
            '--name=Relevantr',
            '--icon=assets/icon.icns',  # Add icon if available
            
            # Same comprehensive includes as above
            '--collect-all=chromadb',
            '--collect-all=google',
            '--collect-all=langchain',
            '--collect-all=langchain_community',
            '--collect-all=langchain_google_genai',
            
            # Add the most critical missing modules
            '--hidden-import=chromadb.telemetry.product.posthog',
            '--hidden-import=posthog',
            
            'relevantr.py'
        ]
        
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("[OK] .app bundle created: dist/Relevantr.app")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] App bundle creation failed: {e}")
        return False

def main():
    """Main build process"""
    print("=" * 60)
    print("Relevantr macOS Build Script")
    print("=" * 60)
    
    if not os.path.exists("relevantr.py"):
        print("[ERROR] relevantr.py not found in current directory")
        sys.exit(1)
    
    if not check_chromadb_modules():
        print("[ERROR] ChromaDB modules missing. Try reinstalling:")
        print("pip uninstall chromadb -y")
        print("pip install chromadb")
        sys.exit(1)
    
    # Build directory version first
    if build_mac_app():
        print("\n[SUCCESS] Directory version built successfully!")
        
        # Ask if user wants .app bundle
        create_bundle = input("\nCreate .app bundle? (y/n): ").lower().strip()
        if create_bundle.startswith('y'):
            create_app_bundle()
        
        print("\n[INFO] Build complete!")
        print("[INFO] Test the app from: dist/Relevantr/Relevantr")
    else:
        print("\n[FAILED] Build process failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
