#!/usr/bin/env python3
"""
Test script to verify LLM integration works in desktop app
"""

import os
import sys
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_llm_client():
    """Test LLM client functionality"""
    print("🧠 Testing LLM Client Integration")
    print("=" * 40)
    
    try:
        # Load environment
        from env_manager import load_environment
        if not load_environment():
            print("❌ Failed to load environment")
            return False
        
        print("✅ Environment loaded")
        
        # Test LLM client
        from src.llm.llm_client import LLMClient
        
        print("Creating LLM client...")
        llm_client = LLMClient()
        
        print(f"✅ LLM Client created")
        print(f"   Service: {llm_client.service_name}")
        print(f"   API URL: {llm_client.api_url}")
        print(f"   Model: {llm_client.chat_model_name}")
        print(f"   Has API Key: {bool(llm_client.api_key)}")
        
        # Test connection
        print("\nTesting connection...")
        if llm_client.check_connection():
            print("✅ LLM connection successful")
        else:
            print("❌ LLM connection failed")
            return False
        
        # Test chat response
        print("\nTesting chat response...")
        messages = [
            {
                "role": "system",
                "content": "You are a helpful AI assistant. Respond briefly."
            },
            {
                "role": "user", 
                "content": "Hello! Can you tell me you're working correctly?"
            }
        ]
        
        response = llm_client.get_chat_response(messages)
        print(f"✅ Chat response received ({len(response)} characters)")
        print(f"Response preview: {response[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing LLM client: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_web_ui_integration():
    """Test web UI with real LLM integration"""
    print("\n🌐 Testing Web UI LLM Integration")
    print("=" * 40)
    
    try:
        from src.ui.web_ui import WhisperEngineWebUI
        
        print("Creating Web UI...")
        web_ui = WhisperEngineWebUI()
        
        # Test AI response generation
        print("Testing AI response generation...")
        
        # This is an async function, so we need to handle it properly
        import asyncio
        
        async def test_response():
            response = await web_ui.generate_ai_response("test_user", "Hello, can you confirm you're working?")
            return response
        
        response = asyncio.run(test_response())
        
        print(f"✅ AI response generated")
        print(f"Content length: {len(response['content'])} characters")
        print(f"Metadata: {response['metadata']}")
        print(f"Response preview: {response['content'][:150]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing web UI integration: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 WhisperEngine LLM Integration Test")
    print("=" * 50)
    
    # Test LLM client
    llm_success = test_llm_client()
    
    # Test web UI integration
    webui_success = test_web_ui_integration()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"  LLM Client: {'✅ PASS' if llm_success else '❌ FAIL'}")
    print(f"  Web UI Integration: {'✅ PASS' if webui_success else '❌ FAIL'}")
    
    if llm_success and webui_success:
        print("\n🎉 All tests passed! Chat functionality should work correctly.")
    else:
        print("\n⚠️ Some tests failed. Check the error messages above.")
        
    print("\nNext steps:")
    print("1. If tests pass, rebuild the desktop app to include the fix")
    print("2. If tests fail, check your .env configuration")
    print("3. Ensure OpenRouter API key is valid and has credit")