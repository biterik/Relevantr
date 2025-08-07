#!/usr/bin/env python3
"""
Test script to debug PDF processing issues on Windows
"""

import os
import sys
from pathlib import Path

def test_pdf_imports():
    """Test PDF processing imports"""
    print("Testing PDF processing imports...")
    print("=" * 50)
    
    # Test PyMuPDF import
    try:
        import fitz
        print("✅ PyMuPDF (fitz) imported successfully")
        print(f"   Version: {fitz.version}")
    except ImportError as e:
        print(f"❌ PyMuPDF import failed: {e}")
        return False
    
    # Test LangChain PDF loader
    try:
        from langchain_community.document_loaders import PyMuPDFLoader
        print("✅ PyMuPDFLoader imported successfully")
    except ImportError as e:
        print(f"❌ PyMuPDFLoader import failed: {e}")
        return False
    
    # Test text splitter
    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        print("✅ RecursiveCharacterTextSplitter imported successfully")
    except ImportError as e:
        print(f"❌ RecursiveCharacterTextSplitter import failed: {e}")
        return False
    
    return True

def test_pdf_directory():
    """Test PDF directory and files"""
    print("\nTesting PDF directory...")
    print("=" * 50)
    
    pdf_dir = input("Enter path to your PDF directory: ").strip()
    if not pdf_dir:
        pdf_dir = "pdfs"  # Default
    
    print(f"Checking directory: {pdf_dir}")
    
    if not os.path.exists(pdf_dir):
        print(f"❌ Directory does not exist: {pdf_dir}")
        return False, []
    
    print(f"✅ Directory exists: {pdf_dir}")
    
    # Find PDF files
    pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]
    print(f"Found {len(pdf_files)} PDF files:")
    
    for i, pdf_file in enumerate(pdf_files[:5]):  # Show first 5
        pdf_path = os.path.join(pdf_dir, pdf_file)
        size = os.path.getsize(pdf_path)
        print(f"  {i+1}. {pdf_file} ({size:,} bytes)")
    
    if len(pdf_files) > 5:
        print(f"  ... and {len(pdf_files) - 5} more files")
    
    if not pdf_files:
        print("❌ No PDF files found!")
        return False, []
    
    return True, [(pdf_dir, pdf_files)]

def test_single_pdf_processing(pdf_dir, pdf_files):
    """Test processing a single PDF"""
    print("\nTesting single PDF processing...")
    print("=" * 50)
    
    if not pdf_files:
        print("❌ No PDF files to test")
        return False
    
    # Test the first PDF file
    test_file = pdf_files[0]
    test_path = os.path.join(pdf_dir, test_file)
    
    print(f"Testing file: {test_file}")
    print(f"Full path: {test_path}")
    print(f"File size: {os.path.getsize(test_path):,} bytes")
    
    try:
        # Test direct PyMuPDF access
        import fitz
        print("\n1. Testing direct PyMuPDF access...")
        
        doc = fitz.open(test_path)
        page_count = len(doc)
        print(f"   ✅ PDF opened successfully")
        print(f"   ✅ Page count: {page_count}")
        
        if page_count > 0:
            # Try to extract text from first page
            page = doc[0]
            text = page.get_text()
            text_length = len(text.strip())
            print(f"   ✅ First page text length: {text_length} characters")
            
            if text_length > 0:
                print(f"   ✅ Sample text: {text[:100]}...")
            else:
                print("   ⚠️  First page appears to have no text")
        
        doc.close()
        
    except Exception as e:
        print(f"   ❌ Direct PyMuPDF failed: {e}")
        return False
    
    try:
        # Test LangChain PyMuPDF loader
        print("\n2. Testing LangChain PyMuPDFLoader...")
        from langchain_community.document_loaders import PyMuPDFLoader
        
        loader = PyMuPDFLoader(test_path)
        docs = loader.load()
        
        print(f"   ✅ PyMuPDFLoader worked")
        print(f"   ✅ Loaded {len(docs)} document pages")
        
        if docs:
            print(f"   ✅ First doc content length: {len(docs[0].page_content)}")
            print(f"   ✅ First doc metadata: {docs[0].metadata}")
        
    except Exception as e:
        print(f"   ❌ PyMuPDFLoader failed: {e}")
        return False
    
    try:
        # Test with text splitter
        print("\n3. Testing with text splitter...")
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            is_separator_regex=False,
        )
        
        split_docs = loader.load_and_split(text_splitter=text_splitter)
        print(f"   ✅ Text splitting worked")
        print(f"   ✅ Created {len(split_docs)} chunks")
        
        if split_docs:
            print(f"   ✅ First chunk length: {len(split_docs[0].page_content)}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Text splitting failed: {e}")
        return False

def main():
    """Main test function"""
    print("Relevantr PDF Processing Diagnostics")
    print("=" * 60)
    
    # Test imports
    if not test_pdf_imports():
        print("\n❌ Import test failed - cannot proceed")
        return
    
    # Test PDF directory
    dir_ok, dir_info = test_pdf_directory()
    if not dir_ok:
        print("\n❌ PDF directory test failed")
        return
    
    # Test single PDF processing
    pdf_dir, pdf_files = dir_info[0]
    if test_single_pdf_processing(pdf_dir, pdf_files):
        print("\n✅ All tests passed! PDF processing should work.")
    else:
        print("\n❌ PDF processing test failed!")
        print("\nPossible solutions:")
        print("1. Make sure your PDFs are not corrupted")
        print("2. Try with different PDF files")
        print("3. Check if PyMuPDF is properly bundled in the app")

if __name__ == "__main__":
    main()
    input("\nPress Enter to exit...")
