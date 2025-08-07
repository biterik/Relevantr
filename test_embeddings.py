#!/usr/bin/env python3
"""
Test script to verify Google embeddings work with explicit API key
"""

import os
import google.generativeai as genai
from langchain_google_genai import GoogleGenerativeAIEmbeddings

def test_embeddings():
    """Test embedding initialization with explicit API key"""
    print("Testing Google Embeddings...")
    print("=" * 40)
    
    # Get API key
    api_key = input("Please paste your API key here: ").strip()
    
    if not api_key:
        print("❌ No API key provided")
        return False
    
    try:
        # Configure genai
        print("Configuring Google AI...")
        genai.configure(api_key=api_key)
        print("✅ Google AI configured")
        
        # Test embeddings with explicit API key
        print("Testing embeddings with explicit API key...")
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=api_key
        )
        
        # Test embedding a simple query
        print("Testing embedding generation...")
        test_embedding = embeddings.embed_query("This is a test")
        
        print(f"✅ Embeddings working! Vector length: {len(test_embedding)}")
        
        # Test embedding multiple documents
        print("Testing batch embeddings...")
        docs = ["Document 1", "Document 2", "Document 3"]
        doc_embeddings = embeddings.embed_documents(docs)
        
        print(f"✅ Batch embeddings working! Generated {len(doc_embeddings)} vectors")
        
        return True
        
    except Exception as e:
        print(f"❌ Embeddings test failed: {e}")
        
        error_str = str(e).lower()
        if "credentials" in error_str or "authentication" in error_str:
            print("\n🔍 Authentication issue detected:")
            print("This suggests the API key isn't being passed correctly.")
            print("Try using explicit google_api_key parameter.")
        
        return False

if __name__ == "__main__":
    test_embeddings()
    input("\nPress Enter to exit...")
