#!/usr/bin/env python3
"""
Test Docker LM Studio Integration
Validates that Docker containers can connect to host LM Studio server
"""

import os
import sys
import logging

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from llm.llm_protocol import create_llm_client

def test_docker_lmstudio_connection():
    """Test LM Studio connection from Docker environment"""
    
    # Use environment variables from Docker
    llm_client_type = os.getenv('LLM_CLIENT_TYPE', 'lmstudio')
    api_url = os.getenv('LLM_CHAT_API_URL', 'http://host.docker.internal:1234/v1')
    model = os.getenv('LLM_CHAT_MODEL', 'local-model')
    
    print(f"Testing LM Studio connection:")
    print(f"  Client Type: {llm_client_type}")
    print(f"  API URL: {api_url}")
    print(f"  Model: {model}")
    
    try:
        # Create LLM client
        llm_client = create_llm_client(llm_client_type)
        print("✅ LLM client created successfully")
        
        # Test simple generation
        test_prompt = "Hello! How are you today?"
        print(f"\n🧪 Testing generation with prompt: '{test_prompt}'")
        
        # Use chat completion format like the synthetic generator
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": test_prompt}
        ]
        
        # Use the correct method from LLMClient
        response = llm_client.generate_chat_completion(messages, max_tokens=50, temperature=0.7)
        
        # Handle async if needed
        if hasattr(response, '__await__'):
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response = loop.run_until_complete(response)
            loop.close()
        
        print(f"✅ LM Studio response: {response[:100]}...")
        print("🎉 Docker LM Studio integration working!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing LM Studio connection: {e}")
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success = test_docker_lmstudio_connection()
    sys.exit(0 if success else 1)