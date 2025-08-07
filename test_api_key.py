#!/usr/bin/env python3
"""
Test script to verify Google Gemini API key is working
"""

import os

def test_api_key():
    """Test the Google Gemini API key"""
    print("Testing Google Gemini API Key...")
    print("=" * 40)
    
    # Get API key
    api_key = input("Please paste your API key here: ").strip()
    
    if not api_key:
        print("❌ No API key provided")
        return False
    
    print(f"API Key format check:")
    print(f"  - Length: {len(api_key)} characters")
    print(f"  - Starts with 'AIza': {api_key.startswith('AIza')}")
    print(f"  - First 10 chars: {api_key[:10]}...")
    print()
    
    try:
        # Test import
        print("Testing import of google.generativeai...")
        import google.generativeai as genai
        print("✅ Import successful")
        
        # Configure API
        print("Configuring API key...")
        genai.configure(api_key=api_key)
        print("✅ API key configured")
        
        # Test with a simple request
        print("Testing API with simple request...")
        
        # Try the current model names
        model_names = ['gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-pro']
        
        for model_name in model_names:
            try:
                print(f"Trying model: {model_name}")
                model = genai.GenerativeModel(model_name)
                response = model.generate_content("Say hello")
                
                print("✅ API test successful!")
                print(f"Working model: {model_name}")
                print(f"Response: {response.text[:100]}...")
                
                return True
                
            except Exception as model_error:
                print(f"Model {model_name} failed: {model_error}")
                continue
        
        print("❌ All model names failed")
        
        # Try to list available models
        try:
            print("\n🔍 Listing available models:")
            models = genai.list_models()
            for model in models:
                if 'generateContent' in model.supported_generation_methods:
                    print(f"  - {model.name}")
        except Exception as list_error:
            print(f"Could not list models: {list_error}")
        
        return False
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        print()
        
        # Common error messages and solutions
        error_str = str(e).lower()
        
        if "api key not valid" in error_str or "invalid api key" in error_str:
            print("🔍 Possible solutions:")
            print("1. Double-check you copied the complete API key")
            print("2. Make sure you're using a Gemini API key (not other Google APIs)")
            print("3. Try regenerating the API key at https://makersuite.google.com/app/apikey")
            
        elif "quota exceeded" in error_str:
            print("🔍 Possible solutions:")
            print("1. You've exceeded the free tier limits")
            print("2. Wait 24 hours for quota reset")
            print("3. Check usage at https://makersuite.google.com/")
            
        elif "permission denied" in error_str or "forbidden" in error_str:
            print("🔍 Possible solutions:")
            print("1. Make sure Gemini API is enabled for your project")
            print("2. Check if your Google account has access to Gemini API")
            
        elif "network" in error_str or "connection" in error_str:
            print("🔍 Possible solutions:")
            print("1. Check your internet connection")
            print("2. Try again in a few minutes")
            
        else:
            print("🔍 General troubleshooting:")
            print("1. Visit https://makersuite.google.com/app/apikey")
            print("2. Delete the old API key and create a new one")
            print("3. Make sure you're signed in with the correct Google account")
        
        return False

if __name__ == "__main__":
    test_api_key()
    input("\nPress Enter to exit...")
