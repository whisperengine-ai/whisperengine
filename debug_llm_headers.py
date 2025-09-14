#!/usr/bin/env python3
"""
Test LLM client with debugging to see exactly what headers are being sent
"""
import os
import logging
from env_manager import load_environment
from src.llm.llm_client import LLMClient

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

def test_llm_client_headers():
    """Test LLM client and debug headers"""
    load_environment()
    
    client = LLMClient()
    
    print(f"Service: {client.service_name}")
    print(f"Endpoint: {client.chat_endpoint}")
    print(f"Has API key: {'Yes' if client.api_key else 'No'}")
    print(f"Has API key manager: {'Yes' if client.api_key_manager else 'No'}")
    
    # Test message
    messages = [
        {"role": "user", "content": "Hello, test message"}
    ]
    
    try:
        print("\nTesting generate_chat_completion...")
        result = client.generate_chat_completion(messages, max_tokens=50)
        print(f"SUCCESS: {result.get('choices', [{}])[0].get('message', {}).get('content', 'No content')}")
    except Exception as e:
        print(f"FAILED: {e}")
        
        # Let's try to debug by making the request manually but mimicking the client
        print("\nDebug: Manual request with same setup...")
        
        # Recreate the headers the same way the client does
        headers = {"Content-Type": "application/json"}
        if client.api_key:
            if client.api_key_manager:
                print("Using API key manager for headers...")
                secure_headers = client.api_key_manager.secure_header_creation(client.api_key, "Bearer")
                headers.update(secure_headers)
                print(f"Secure headers: {list(secure_headers.keys())}")
            else:
                print("Using fallback headers...")
                headers["Authorization"] = f"Bearer {client.api_key}"
        
        payload = {
            "model": client.default_model_name,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 50,
            "stream": False
        }
        
        print(f"Headers (without auth): {[k for k in headers.keys() if k != 'Authorization']}")
        print(f"Has Authorization header: {'Authorization' in headers}")
        print(f"Payload model: {payload['model']}")
        
        # Try with direct requests
        import requests
        try:
            response = requests.post(
                client.chat_endpoint,
                json=payload,
                headers=headers,
                timeout=(client.connection_timeout, client.request_timeout)
            )
            print(f"Direct request status: {response.status_code}")
            if response.status_code != 200:
                print(f"Direct request error: {response.text}")
            else:
                result = response.json()
                print(f"Direct request success: {result.get('choices', [{}])[0].get('message', {}).get('content', 'No content')}")
        except Exception as e2:
            print(f"Direct request failed: {e2}")

if __name__ == "__main__":
    test_llm_client_headers()