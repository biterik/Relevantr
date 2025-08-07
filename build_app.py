#!/usr/bin/env python3
"""
Relevantr Build Script
======================
Automated script to build standalone applications for Mac and Windows using PyInstaller
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import platform

def check_pyinstaller():
    """Check if PyInstaller is installed"""
    try:
        import PyInstaller
        print("[OK] PyInstaller is installed")
        return True
    except ImportError:
        print("[ERROR] PyInstaller not found")
        print("Install with: pip install pyinstaller")
        return False

def clean_build_dirs():
    """Clean previous build directories"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"[CLEAN] Cleaning {dir_name}/")
            shutil.rmtree(dir_name)

def find_python_dll():
    """Find the Python DLL location for Windows"""
    if sys.platform == "win32":
        python_dir = os.path.dirname(sys.executable)
        dll_name = f"python{sys.version_info.major}{sys.version_info.minor}.dll"
        dll_paths = [
            os.path.join(python_dir, dll_name),
            os.path.join(python_dir, "DLLs", dll_name),
            os.path.join(os.environ.get('CONDA_PREFIX', ''), dll_name),
            os.path.join(os.environ.get('CONDA_PREFIX', ''), "Library", "bin", dll_name),
        ]
        
        for dll_path in dll_paths:
            if os.path.exists(dll_path):
                print(f"[OK] Found Python DLL: {dll_path}")
                return dll_path
        
        print(f"[WARNING] Python DLL not found: {dll_name}")
        return None
    return None

def build_app(platform_name="auto"):
    """Build the application using PyInstaller"""
    print(f"[BUILD] Building Relevantr for {platform_name}...")
    
    # Clean previous builds
    clean_build_dirs()
    
    # Base command
    cmd = [
        'pyinstaller',
        '--name=Relevantr',
        '--windowed',  # No console window
        '--onedir',    # Create directory bundle (more reliable than onefile)
    ]
    
    # Platform-specific options
    if sys.platform == "darwin":  # macOS
        print("[PLATFORM] Building for macOS...")
        cmd.extend([
            '--add-data=environment.yml:.',
            '--add-data=requirements.txt:.',
            '--hidden-import=tkinter',
            '--hidden-import=PIL._tkinter_finder',
            '--collect-all=tkinter',
        ])
        
    elif sys.platform == "win32":  # Windows
        print("[PLATFORM] Building for Windows...")
        
        # Find and add Python DLL
        python_dll = find_python_dll()
        if python_dll:
            cmd.extend([
                f'--add-binary={python_dll};.',
            ])
        
        cmd.extend([
            '--add-data=environment.yml;.',
            '--add-data=requirements.txt;.',
            '--hidden-import=tkinter',
            '--hidden-import=tkinter.ttk',
            '--hidden-import=tkinter.filedialog',
            '--hidden-import=tkinter.messagebox',
            '--hidden-import=tkinter.scrolledtext',
            '--collect-all=tkinter',
            '--collect-submodules=google.generativeai',
            '--collect-submodules=langchain',
            '--collect-submodules=langchain_community',
            '--collect-submodules=langchain_google_genai',
            '--collect-submodules=chromadb',
            '--collect-data=chromadb',
            '--exclude-module=matplotlib',
            '--exclude-module=scipy',
            '--exclude-module=numpy.f2py',
        ])
        
    else:  # Linux
        print("[PLATFORM] Building for Linux...")
        cmd.extend([
            '--add-data=environment.yml:.',
            '--add-data=requirements.txt:.',
            '--hidden-import=tkinter',
            '--collect-all=tkinter',
        ])
    
    # Add the main script
    cmd.append('relevantr.py')
    
    try:
        print(f"[CMD] Running command: {' '.join(cmd)}")
        # Run PyInstaller
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("[OK] Build completed successfully!")
        
        # Show build location
        dist_path = Path("dist") / "Relevantr"
        print(f"[RESULT] Application built in: {dist_path.absolute()}")
        
        # Windows-specific post-build steps
        if sys.platform == "win32":
            print("[POST-BUILD] Performing Windows post-build steps...")
            
            # Copy Visual C++ redistributables if available
            vcredist_paths = [
                "C:\\Program Files\\Microsoft Visual Studio\\2022\\BuildTools\\VC\\Redist\\MSVC",
                "C:\\Program Files (x86)\\Microsoft Visual Studio\\14.0\\VC\\redist"
            ]
            
            for vcredist_path in vcredist_paths:
                if os.path.exists(vcredist_path):
                    print(f"[INFO] Visual C++ redistributables found at: {vcredist_path}")
                    break
            else:
                print("[INFO] Consider installing Visual C++ redistributables for broader compatibility")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Build failed: {e}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False

def create_windows_batch_file():
    """Create a batch file launcher for Windows"""
    if sys.platform == "win32":
        batch_content = """@echo off
echo Starting Relevantr...
cd /d "%~dp0"
Relevantr.exe
if errorlevel 1 (
    echo.
    echo ERROR: Failed to start Relevantr
    echo.
    echo Possible solutions:
    echo 1. Install Visual C++ Redistributables
    echo 2. Run as Administrator
    echo 3. Check antivirus software
    echo.
    pause
)
"""
        batch_path = Path("dist") / "Relevantr" / "Start_Relevantr.bat"
        with open(batch_path, "w", encoding='ascii', errors='replace') as f:
            f.write(batch_content)
        print("[OK] Created Windows batch launcher: Start_Relevantr.bat")

def create_installer_info():
    """Create installation instructions"""
    instructions = f"""
# Relevantr Standalone Application - Installation Guide

## System Requirements
- Windows 10/11 (64-bit) OR macOS 10.15+ OR Linux
- 4GB RAM minimum, 8GB recommended
- Internet connection for Google Gemini API

## Windows Installation:
1. Extract the ZIP file to a folder (e.g., C:\\Relevantr)
2. **IMPORTANT**: Install Visual C++ Redistributables if not already installed:
   - Download from: https://aka.ms/vs/17/release/vc_redist.x64.exe
3. Run Relevantr.exe OR double-click Start_Relevantr.bat
4. If Windows Defender shows a warning:
   - Click "More info" -> "Run anyway"
   - Or add the folder to Windows Defender exclusions

## macOS Installation:
1. Extract the downloaded file
2. Right-click Relevantr -> "Open" (to bypass Gatekeeper)
3. If prompted, allow network access for API calls

## First Time Setup:
1. Get a Google Gemini API key: https://makersuite.google.com/app/apikey
2. Create a folder for your PDFs
3. Launch Relevantr and enter your API key
4. Select your PDF folder and click "Process PDFs"
5. Start asking scientific questions!

## Troubleshooting:
- **"python312.dll not found"**: Install Visual C++ Redistributables
- **Antivirus blocking**: Add Relevantr folder to exclusions
- **Slow startup**: Normal for first run, subsequent starts are faster
- **API errors**: Check your Google Gemini API key

## Notes:
- The app creates 'logs' and 'vector_db' folders where you run it
- Your API key is stored securely in environment variables
- Vector database persists between sessions

Built with Python {sys.version_info.major}.{sys.version_info.minor} on {platform.platform()}
"""
    
    with open("INSTALLATION.md", "w", encoding='utf-8') as f:
        f.write(instructions)
    
    print("[OK] Created INSTALLATION.md with setup instructions")

def main():
    """Main build process"""
    print("=" * 50)
    print("Relevantr Build Process")
    print("=" * 50)
    
    # Check dependencies
    if not check_pyinstaller():
        sys.exit(1)
    
    # Check if main script exists
    if not os.path.exists("relevantr.py"):
        print("[ERROR] relevantr.py not found in current directory")
        sys.exit(1)
    
    # Build the application
    if build_app(platform.system()):
        create_installer_info()
        
        # Windows-specific post-build
        if sys.platform == "win32":
            create_windows_batch_file()
        
        print("")
        print("[SUCCESS] Build process completed!")
        print("[RESULT] Check the 'dist/Relevantr' folder for your application")
        
        if sys.platform == "win32":
            print("")
            print("[TIP] Windows users: Use 'Start_Relevantr.bat' to launch the app")
            print("[TIP] If you get DLL errors, install Visual C++ Redistributables")
    else:
        print("")
        print("[FAILED] Build process failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
