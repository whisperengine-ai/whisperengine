#!/usr/bin/env python3
"""
Test LLM Client configuration to diagnose the 404 error
"""

import os
import sys
sys.path.insert(0, '.')

# Load environment
from env_manager import load_environment
load_environment()

# Import and test LLM client
from src.llm.llm_client import LLMClient

def test_llm_client():
    print("=== Testing LLM Client Configuration ===")
    
    # Create LLM client
    client = LLMClient()
    
    print(f"API URL: {client.api_url}")
    print(f"Chat endpoint: {client.chat_endpoint}")
    print(f"Service name: {client.service_name}")
    print(f"Is local LLM: {client.is_local_llm}")
    print(f"API key present: {bool(client.api_key)}")
    
    # Test simple chat completion
    print("\n=== Testing Chat Completion ===")
    try:
        messages = [
            {"role": "user", "content": "Say hello briefly"}
        ]
        
        # Enable debug logging
        import logging
        logging.basicConfig(level=logging.DEBUG)
        
        response = client.get_chat_response(messages)
        print(f"Success! Response: {response[:100]}...")
        
    except Exception as e:
        print(f"Error: {e}")
        print(f"Error type: {type(e)}")
        
        # Try to get more details
        if hasattr(e, '__cause__') and e.__cause__:
            print(f"Cause: {e.__cause__}")
            
        # Test if the issue is with model parameter
        print("\n=== Testing with explicit model ===")
        try:
            response = client.generate_chat_completion(
                messages=messages,
                model="phi3:mini",
                temperature=0.7,
                max_tokens=50
            )
            print(f"Success with explicit model! Keys: {list(response.keys())}")
        except Exception as e2:
            print(f"Also failed with explicit model: {e2}")

if __name__ == "__main__":
    test_llm_client()