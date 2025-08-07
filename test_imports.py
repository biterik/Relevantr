#!/usr/bin/env python3
"""
Test script to verify all imports work before building with PyInstaller
Run this in your environment to check for missing dependencies
"""

import sys
print(f"Testing imports with Python {sys.version}")
print("=" * 50)

def test_import(module_name, description=""):
    """Test importing a module"""
    try:
        __import__(module_name)
        print(f"[OK] {module_name} - {description}")
        return True
    except ImportError as e:
        print(f"[FAIL] {module_name} - {e}")
        return False

def main():
    """Test all critical imports"""
    success_count = 0
    total_tests = 0
    
    # Test basic Python modules
    tests = [
        ("tkinter", "GUI framework"),
        ("tkinter.ttk", "Themed widgets"),
        ("tkinter.filedialog", "File dialogs"),
        ("tkinter.messagebox", "Message boxes"),
        ("tkinter.scrolledtext", "Scrolled text widgets"),
        
        # Test Google AI modules
        ("google", "Google namespace package"),
        ("google.generativeai", "Google Gemini AI"),
        
        # Test LangChain modules
        ("langchain", "LangChain framework"),
        ("langchain.text_splitter", "Text processing"),
        ("langchain_community", "Community extensions"),
        ("langchain_community.document_loaders", "Document loaders"),
        ("langchain_community.vectorstores", "Vector databases"),
        ("langchain_google_genai", "Google AI integration"),
        
        # Test ChromaDB
        ("chromadb", "Vector database"),
        
        # Test PDF processing
        ("fitz", "PyMuPDF PDF processing"),
        
        # Test utilities
        ("tqdm", "Progress bars"),
        ("dotenv", "Environment variables"),
        ("warnings", "Warning system"),
        ("logging", "Logging system"),
        ("threading", "Threading support"),
        ("json", "JSON processing"),
        ("datetime", "Date/time handling"),
        ("dataclasses", "Data classes"),
        ("typing", "Type hints"),
        ("pathlib", "Path handling"),
        ("sqlite3", "SQLite database"),
        ("ssl", "SSL/TLS support"),
        ("certifi", "Certificate bundle"),
        ("urllib3", "HTTP client"),
        ("requests", "HTTP requests"),
    ]
    
    for module, desc in tests:
        total_tests += 1
        if test_import(module, desc):
            success_count += 1
    
    print("=" * 50)
    print(f"Results: {success_count}/{total_tests} imports successful")
    
    if success_count == total_tests:
        print("[SUCCESS] All imports working! Ready to build with PyInstaller")
        return True
    else:
        print("[WARNING] Some imports failed. Install missing packages:")
        failed_modules = []
        for module, _ in tests:
            try:
                __import__(module)
            except ImportError:
                failed_modules.append(module)
        
        print("\nTo install missing packages:")
        if 'google.generativeai' in failed_modules:
            print("pip install google-generativeai")
        if any('langchain' in m for m in failed_modules):
            print("pip install langchain langchain-community langchain-google-genai")
        if 'chromadb' in failed_modules:
            print("pip install chromadb")
        if 'fitz' in failed_modules:
            print("pip install pymupdf")
        if 'tqdm' in failed_modules:
            print("pip install tqdm")
        if 'dotenv' in failed_modules:
            print("pip install python-dotenv")
        
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
