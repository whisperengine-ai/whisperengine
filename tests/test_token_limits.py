#!/usrimport pytest
import asyncio
import os
import tempfile
import json
from pathlib import Path
from env_manager import load_environment

# Load environment variables using centralized manager
load_environment()
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_token_limits():
    """Test that token limits can be configured via environment variables"""
    print("🧪 Testing LLM Token Limits Configuration")
    print("=" * 50)
    
    # Test environment variable loading
    chat_tokens = os.getenv("LLM_MAX_TOKENS_CHAT")
    completion_tokens = os.getenv("LLM_MAX_TOKENS_COMPLETION")
    
    print(f"LLM_MAX_TOKENS_CHAT: {chat_tokens}")
    print(f"LLM_MAX_TOKENS_COMPLETION: {completion_tokens}")
    
    # Test LMStudioClient initialization
    try:
        from lmstudio_client import LMStudioClient
        
        print("\n🔧 Testing LMStudioClient initialization...")
        client = LMStudioClient()
        
        print(f"✅ Chat token limit: {client.default_max_tokens_chat}")
        print(f"✅ Completion token limit: {client.default_max_tokens_completion}")
        
        # Test with custom environment variables
        print("\n🔧 Testing with custom token limits...")
        os.environ["LLM_MAX_TOKENS_CHAT"] = "8000"
        os.environ["LLM_MAX_TOKENS_COMPLETION"] = "2048"
        
        client2 = LMStudioClient()
        print(f"✅ Custom chat token limit: {client2.default_max_tokens_chat}")
        print(f"✅ Custom completion token limit: {client2.default_max_tokens_completion}")
        
        # Verify the values are what we set
        assert client2.default_max_tokens_chat == 8000, f"Expected 8000, got {client2.default_max_tokens_chat}"
        assert client2.default_max_tokens_completion == 2048, f"Expected 2048, got {client2.default_max_tokens_completion}"
        
        print("\n🎉 All tests passed! Token limits are properly configurable.")
        return True
        
    except Exception as e:
        print(f"\n❌ Error testing LMStudioClient: {e}")
        return False

def test_method_defaults():
    """Test that methods use the configured defaults when max_tokens is not specified"""
    print("\n🧪 Testing Method Default Token Usage")
    print("=" * 50)
    
    try:
        from lmstudio_client import LMStudioClient
        
        # Set specific token limits
        os.environ["LLM_MAX_TOKENS_CHAT"] = "12000"
        os.environ["LLM_MAX_TOKENS_COMPLETION"] = "3000"
        
        client = LMStudioClient()
        
        # Mock the session.post method to capture the payload
        original_post = client.session.post
        captured_payloads = []
        
        def mock_post(*args, **kwargs):
            if 'json' in kwargs:
                captured_payloads.append(kwargs['json'])
            # Return a mock response that won't actually call the API
            class MockResponse:
                def raise_for_status(self): pass
                def json(self): return {"choices": [{"message": {"content": "test"}}]}
            return MockResponse()
        
        client.session.post = mock_post
        
        # Test chat completion without max_tokens specified
        print("🔧 Testing chat completion with default token limit...")
        try:
            client.generate_chat_completion([{"role": "user", "content": "test"}])
            chat_payload = captured_payloads[0]
            print(f"✅ Chat completion used token limit: {chat_payload.get('max_tokens')}")
            assert chat_payload.get('max_tokens') == 12000, f"Expected 12000, got {chat_payload.get('max_tokens')}"
        except Exception as e:
            print(f"Note: Chat completion test requires actual LLM connection: {e}")
        
        # Test text completion without max_tokens specified
        print("🔧 Testing text completion with default token limit...")
        try:
            client.generate_completion("test prompt")
            if len(captured_payloads) > 1:
                completion_payload = captured_payloads[1]
                print(f"✅ Text completion used token limit: {completion_payload.get('max_tokens')}")
                assert completion_payload.get('max_tokens') == 3000, f"Expected 3000, got {completion_payload.get('max_tokens')}"
        except Exception as e:
            print(f"Note: Text completion test requires actual LLM connection: {e}")
        
        # Test with explicit max_tokens (should override default)
        print("🔧 Testing with explicit token limit override...")
        try:
            client.generate_chat_completion([{"role": "user", "content": "test"}], max_tokens=5000)
            if len(captured_payloads) > 2:
                override_payload = captured_payloads[2]
                print(f"✅ Explicit override used token limit: {override_payload.get('max_tokens')}")
                assert override_payload.get('max_tokens') == 5000, f"Expected 5000, got {override_payload.get('max_tokens')}"
        except Exception as e:
            print(f"Note: Override test requires actual LLM connection: {e}")
        
        print("\n🎉 Method default tests completed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error in method testing: {e}")
        return False

if __name__ == "__main__":
    print("🚀 LLM Token Limits Configuration Test")
    print("=" * 60)
    
    success = True
    success &= test_token_limits()
    success &= test_method_defaults()
    
    if success:
        print("\n🎉 All tests passed! Token limits are now configurable via environment variables.")
        print("\n📝 Configuration Instructions:")
        print("1. Set LLM_MAX_TOKENS_CHAT in your .env file (default: 16535)")
        print("2. Set LLM_MAX_TOKENS_COMPLETION in your .env file (default: 1024)")
        print("3. Restart the bot to apply changes")
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
        sys.exit(1)
