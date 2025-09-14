#!/usr/bin/env python3
"""
Debug script to test OpenRouter API directly
"""
import os
import requests
import json
from env_manager import load_environment

def test_openrouter_direct():
    """Test OpenRouter API with direct HTTP request"""
    load_environment()
    
    api_url = os.getenv('LLM_CHAT_API_URL')
    api_key = os.getenv('LLM_CHAT_API_KEY')
    model = os.getenv('LLM_CHAT_MODEL')
    
    print(f"API URL: {api_url}")
    print(f"Model: {model}")
    print(f"API Key (first 10): {api_key[:10] if api_key else 'Not set'}")
    
    if not api_key:
        print("ERROR: No API key found!")
        return
    
    endpoint = f"{api_url}/chat/completions"
    print(f"Full endpoint: {endpoint}")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Add OpenRouter-specific headers
    if api_url and "openrouter.ai" in api_url:
        headers["HTTP-Referer"] = "https://whisperengine.local"
        headers["X-Title"] = "WhisperEngine Desktop"
    
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": "Hello, just testing connection"}
        ],
        "max_tokens": 50,
        "temperature": 0.7
    }
    
    print("\nMaking request...")
    print(f"Headers: {json.dumps({k: v for k, v in headers.items() if k != 'Authorization'}, indent=2)}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(endpoint, headers=headers, json=payload, timeout=30)
        print(f"\nResponse status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"SUCCESS! Response: {json.dumps(result, indent=2)}")
        else:
            print(f"ERROR! Response text: {response.text}")
            
    except Exception as e:
        print(f"EXCEPTION: {e}")

if __name__ == "__main__":
    test_openrouter_direct()