#!/bin/bash
# Build script for Relevantr with network connectivity fixes
# This script creates a standalone executable that should work with network connections

set -e  # Exit on any error

echo "=========================================="
echo "Relevantr Build Script with Network Fixes"
echo "=========================================="

# Check if we're on macOS or Linux
if [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="macOS"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    PLATFORM="Linux"
else
    PLATFORM="Unknown"
fi

echo "Platform detected: $PLATFORM"

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build dist *.spec

# Check Python version
echo "Checking Python version..."
python3 --version

# Check if required packages are installed
echo "Checking required packages..."
python3 -c "
import sys
required = [
    'pyinstaller', 'google-generativeai', 'langchain', 
    'langchain-community', 'langchain-google-genai', 
    'chromadb', 'tqdm', 'python-dotenv', 'requests', 
    'urllib3', 'certifi'
]

missing = []
for pkg in required:
    try:
        __import__(pkg.replace('-', '_'))
        print(f'✅ {pkg}')
    except ImportError:
        missing.append(pkg)
        print(f'❌ {pkg} - MISSING')

if missing:
    print(f'\\nInstall missing packages: pip install {\" \".join(missing)}')
    sys.exit(1)
else:
    print('\\n✅ All required packages found')
"

# Install additional packages that might be needed for network connectivity
echo "Installing additional network packages..."
pip3 install --upgrade certifi urllib3 requests

# Set environment variables for better gRPC/network compatibility
export GRPC_VERBOSITY=DEBUG
export GRPC_TRACE=all
export PYTHONHTTPSVERIFY=1

# Create the spec file if it doesn't exist
if [ ! -f "relevantr.spec" ]; then
    echo "Creating PyInstaller spec file..."
    cat > relevantr.spec << 'EOF'
# -*- mode: python ; coding: utf-8 -*-
import sys
import os
import certifi

block_cipher = None

# Get certificate bundle path
cert_path = certifi.where()

# Enhanced hidden imports for network connectivity
hidden_imports = [
    # Core networking
    'socket', 'ssl', 'certifi', 'urllib3', 'requests',
    'urllib3.util', 'urllib3.util.ssl_', 'urllib3.connection',
    'urllib3.connectionpool', 'urllib3.poolmanager',
    'urllib3.response', 'urllib3.exceptions',
    
    # HTTP/HTTPS
    'requests.adapters', 'requests.auth', 'requests.cookies',
    'requests.exceptions', 'requests.models', 'requests.sessions',
    'requests.structures', 'requests.utils',
    
    # Google API
    'google', 'google.auth', 'google.auth.transport',
    'google.auth.transport.requests', 'google.auth.transport.urllib3',
    'google.oauth2', 'google.oauth2.credentials',
    'google.generativeai', 'google.generativeai.client',
    'google.generativeai.types',
    
    # gRPC and Protocol Buffers
    'grpc', 'grpc._channel', 'grpc._common', 'grpc._compression',
    'grpc._plugin_wrapping', 'grpc._utilities',
    'google.protobuf', 'google.protobuf.any_pb2',
    'google.protobuf.descriptor', 'google.protobuf.descriptor_pb2',
    'google.protobuf.duration_pb2', 'google.protobuf.empty_pb2',
    'google.protobuf.field_mask_pb2', 'google.protobuf.json_format',
    'google.protobuf.message', 'google.protobuf.struct_pb2',
    'google.protobuf.timestamp_pb2', 'google.protobuf.wrappers_pb2',
    
    # LangChain
    'langchain', 'langchain.text_splitter', 'langchain.schema',
    'langchain.embeddings', 'langchain.llms', 'langchain.chat_models',
    'langchain_community', 'langchain_community.document_loaders',
    'langchain_community.vectorstores', 'langchain_community.embeddings',
    'langchain_google_genai', 'langchain_google_genai.embeddings',
    'langchain_google_genai.chat_models',
    
    # ChromaDB
    'chromadb', 'chromadb.api', 'chromadb.client', 'chromadb.config',
    'chromadb.db', 'chromadb.errors', 'chromadb.utils',
    
    # PDF processing
    'fitz', 'PyMuPDF',
    
    # Other
    'tqdm', 'dotenv', 'pathlib', 'threading', 'json',
    'datetime', 'warnings', 'logging', 'traceback',
]

a = Analysis(
    ['relevantr.py'],
    pathex=[],
    binaries=[],
    datas=[(cert_path, 'certifi')],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib', 'numpy.random._examples', 'scipy', 'pandas',
        'PIL.ImageQt', 'PyQt5', 'PyQt6', 'PySide2', 'PySide6',
        'jupyter', 'notebook'
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Relevantr',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
EOF
    echo "✅ Spec file created"
fi

# Build with PyInstaller
echo "Building with PyInstaller..."
echo "This may take several minutes..."

pyinstaller \
    --clean \
    --noconfirm \
    relevantr.spec

# Check if build was successful
if [ -f "dist/Relevantr" ] || [ -f "dist/Relevantr.exe" ]; then
    echo ""
    echo "=========================================="
    echo "✅ BUILD SUCCESSFUL!"
    echo "=========================================="
    echo ""
    echo "Executable location:"
    if [ -f "dist/Relevantr" ]; then
        echo "  📁 $(pwd)/dist/Relevantr"
        echo ""
        echo "Test the executable:"
        echo "  ./dist/Relevantr"
    elif [ -f "dist/Relevantr.exe" ]; then
        echo "  📁 $(pwd)/dist/Relevantr.exe"
        echo ""
        echo "Test the executable:"
        echo "  ./dist/Relevantr.exe"
    fi
    echo ""
    echo "IMPORTANT NOTES:"
    echo "- The first run may take longer as it extracts files"
    echo "- Make sure you have a stable internet connection"
    echo "- Check the Debug menu for network connectivity tests"
    echo "- Logs will be created in the 'logs' directory"
    echo ""
    echo "If you experience network issues:"
    echo "1. Run the executable from command line to see debug output"
    echo "2. Use Debug menu -> Test Network Connection"
    echo "3. Use Debug menu -> Test Google API"
    echo "4. Check firewall settings"
    echo ""
else
    echo ""
    echo "=========================================="
    echo "❌ BUILD FAILED!"
    echo "=========================================="
    echo ""
    echo "Check the build output above for errors."
    echo "Common issues:"
    echo "1. Missing dependencies - install with pip"
    echo "2. Python version compatibility"
    echo "3. PyInstaller version issues"
    echo ""
    echo "Try:"
    echo "  pip install --upgrade pyinstaller"
    echo "  pip install --upgrade setuptools"
    echo ""
    exit 1
fi

# Optional: Create a simple test script
echo "Creating test script..."
cat > test_relevantr.sh << 'EOF'
#!/bin/bash
# Test script for Relevantr

echo "Testing Relevantr executable..."
echo "=============================="

# Check if executable exists
if [ -f "dist/Relevantr" ]; then
    EXEC="./dist/Relevantr"
elif [ -f "dist/Relevantr.exe" ]; then
    EXEC="./dist/Relevantr.exe"
else
    echo "❌ Relevantr executable not found!"
    exit 1
fi

echo "Found executable: $EXEC"
echo ""
echo "Starting Relevantr..."
echo "Press Ctrl+C to stop"
echo ""

# Run the executable
$EXEC
EOF

chmod +x test_relevantr.sh

echo "✅ Test script created: test_relevantr.sh"
echo ""
echo "To test your build, run: ./test_relevantr.sh"
