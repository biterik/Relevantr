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

def check_pyinstaller():
    """Check if PyInstaller is installed"""
    try:
        import PyInstaller
        print("✅ PyInstaller is installed")
        return True
    except ImportError:
        print("❌ PyInstaller not found")
        print("Install with: pip install pyinstaller")
        return False

def clean_build_dirs():
    """Clean previous build directories"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"🧹 Cleaning {dir_name}/")
            shutil.rmtree(dir_name)

def build_app(platform="auto"):
    """Build the application using PyInstaller"""
    print(f"🚀 Building Relevantr for {platform}...")
    
    # Clean previous builds
    clean_build_dirs()
    
    # Determine platform-specific options
    if sys.platform == "darwin":  # macOS
        print("🍎 Building for macOS...")
        cmd = [
            'pyinstaller',
            '--windowed',  # No console window
            '--onedir',    # Create directory bundle
            '--name=Relevantr',
            '--add-data=environment.yml:.',
            '--add-data=requirements.txt:.',
            '--hidden-import=tkinter',
            '--hidden-import=PIL._tkinter_finder',
            'relevantr.py'
        ]
    elif sys.platform == "win32":  # Windows
        print("🪟 Building for Windows...")
        cmd = [
            'pyinstaller',
            '--windowed',  # No console window
            '--onedir',    # Create directory bundle
            '--name=Relevantr',
            '--add-data=environment.yml;.',
            '--add-data=requirements.txt;.',
            '--hidden-import=tkinter',
            'relevantr.py'
        ]
    else:  # Linux
        print("🐧 Building for Linux...")
        cmd = [
            'pyinstaller',
            '--windowed',
            '--onedir',
            '--name=Relevantr',
            '--add-data=environment.yml:.',
            '--add-data=requirements.txt:.',
            '--hidden-import=tkinter',
            'relevantr.py'
        ]
    
    try:
        # Run PyInstaller
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Build completed successfully!")
        
        # Show build location
        dist_path = Path("dist") / "Relevantr"
        print(f"📦 Application built in: {dist_path.absolute()}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False

def create_installer_info():
    """Create installation instructions"""
    instructions = """
# Relevantr Standalone Application

## Installation Instructions

### macOS:
1. Unzip the downloaded file
2. Drag Relevantr.app to your Applications folder (if app bundle)
   OR run Relevantr executable from the extracted folder
3. First run: Right-click → Open (to bypass Gatekeeper)
4. Set up your Google Gemini API key when prompted

### Windows:
1. Extract the ZIP file to a folder (e.g., C:\\Relevantr)
2. Run Relevantr.exe
3. Set up your Google Gemini API key when prompted
4. Windows Defender might show a warning - click "More info" -> "Run anyway"

### First Time Setup:
1. Get a Google Gemini API key: https://makersuite.google.com/app/apikey
2. Create a folder for your PDFs
3. Point Relevantr to your PDF folder
4. Click "Process PDFs" to build your database
5. Start asking scientific questions!

### Notes:
- The app will create 'logs' and 'vector_db' folders in the same directory
- Your API key is stored securely in environment variables
- Vector database persists between sessions for faster startup
"""
    
    with open("INSTALLATION.md", "w") as f:
        f.write(instructions)
    
    print("📝 Created INSTALLATION.md with setup instructions")

def main():
    """Main build process"""
    print("🔨 Relevantr Build Process")
    print("=" * 40)
    
    # Check dependencies
    if not check_pyinstaller():
        sys.exit(1)
    
    # Check if main script exists
    if not os.path.exists("relevantr.py"):
        print("❌ relevantr.py not found in current directory")
        sys.exit(1)
    
    # Build the application
    if build_app():
        create_installer_info()
        print("\n🎉 Build process completed!")
        print("📦 Check the 'dist' folder for your application")
    else:
        print("\n💥 Build process failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
