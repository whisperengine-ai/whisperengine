#!/usr/bin/env python3
"""
Test complete Ollama integration with WhisperEngine
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.llm.llm_client import LLMClient

def test_ollama_integration():
    """Test complete Ollama integration"""
    print("🦙 Testing Ollama Integration")
    print("=" * 40)
    
    try:
        # Create LLM client with ollama URL from environment
        api_url = os.getenv('LLM_CHAT_API_URL', 'ollama://llama3.2:3b')
        print(f"API URL: {api_url}")
        
        client = LLMClient(api_url=api_url)
        
        # Check connection
        connection_status = client.check_connection()
        print(f"Connection: {'✅ Connected' if connection_status else '❌ Failed'}")
        
        if not connection_status:
            print("❌ Cannot proceed without connection")
            return False
        
        # Test simple generation
        print("\n🔄 Testing generation...")
        messages = [
            {"role": "user", "content": "Hello! Please respond with just 'Hi there!'"}
        ]
        
        response = client.generate_chat_completion(
            messages=messages,
            max_tokens=10,
            temperature=0.1
        )
        
        if response and 'choices' in response:
            content = response['choices'][0]['message']['content'].strip()
            print(f"✅ Response: {content}")
            print("✅ Ollama integration working perfectly!")
            return True
        else:
            print("❌ No response received")
            return False
            
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_ollama_integration()
    sys.exit(0 if success else 1)