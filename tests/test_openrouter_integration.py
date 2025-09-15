#!/usr/bin/env python3
"""
Test script to verify OpenRouter integration
Run this to test your OpenRouter configuration before starting the bot.
"""
import os
import sys
from lmstudio_client import LMStudioClient

def test_openrouter_config():
    """Test OpenRouter configuration"""
    print("🧪 Testing OpenRouter Integration")
    print("=" * 50)
    
    # Check environment variables
    api_url = os.getenv("LLM_CHAT_API_URL")
    api_key = os.getenv("OPENROUTER_API_KEY") 
    model_name = os.getenv("LLM_MODEL_NAME", "local-llm")
    
    # Check sentiment endpoint configuration
    sentiment_api_url = os.getenv("LLM_SENTIMENT_API_URL", api_url)
    sentiment_api_key = os.getenv("LLM_SENTIMENT_API_KEY", api_key)
    sentiment_model_name = os.getenv("LLM_SENTIMENT_MODEL_NAME", model_name)
    
    print(f"📍 Main API URL: {api_url}")
    print(f"🔑 Main API Key: {'✅ Set' if api_key else '❌ Not set'}")
    print(f"🤖 Main Model: {model_name}")
    print()
    
    same_endpoint = sentiment_api_url == api_url
    if same_endpoint:
        print(f"🧠 Analysis Service: Using same endpoint as main")
        print(f"🤖 Analysis Model: {sentiment_model_name}")
    else:
        print(f"🧠 Analysis API URL: {sentiment_api_url}")
        print(f"🔑 Analysis API Key: {'✅ Set' if sentiment_api_key else '❌ Not set'}")
        print(f"🤖 Analysis Model: {sentiment_model_name}")
    print()
    
    # Initialize client
    try:
        client = LMStudioClient()
        print(f"✅ Client initialized successfully")
        print(f"   Main Service: {client.service_name}")
        print(f"   Analysis Service: {client.sentiment_service_name}")
        print(f"   Separate endpoints: {'Yes' if client.sentiment_api_url != client.api_url else 'No'}")
        print()
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        return False
    
    # Test connection
    print("🔗 Testing connection...")
    try:
        is_connected = client.check_connection()
        if is_connected:
            print("✅ Connection successful!")
        else:
            print("❌ Connection failed!")
            if client.is_openrouter:
                print("   💡 For OpenRouter:")
                print("      - Check your API key is valid")
                print("      - Verify you have credits in your account")
                print("      - Ensure the URL is https://openrouter.ai/api/v1")
            else:
                print("   💡 For local LLM:")
                print("      - Make sure LM Studio/Ollama is running")
                print("      - Check the server URL is correct")
        print()
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False
    
    # Test simple chat (only if connected)
    if is_connected:
        print("💬 Testing simple chat completion...")
        try:
            messages = [
                {"role": "user", "content": "Say 'Hello from OpenRouter!' if you can read this."}
            ]
            response = client.generate_chat_completion(messages, max_tokens=50)
            
            if response and 'choices' in response and len(response['choices']) > 0:
                reply = response['choices'][0]['message']['content']
                print(f"✅ Chat test successful!")
                print(f"   Bot replied: '{reply.strip()}'")
            else:
                print(f"❌ Chat test failed: Unexpected response format")
        except Exception as e:
            print(f"❌ Chat test failed: {e}")
            return False
    
    print()
    print("🎉 All tests completed!")
    return is_connected

def main():
    """Main test function"""
    # Load environment from .env if available
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("📋 Loaded configuration from .env file")
    except ImportError:
        print("📋 python-dotenv not available, using system environment variables")
    except Exception as e:
        print(f"📋 Could not load .env file: {e}")
    
    print()
    
    success = test_openrouter_config()
    
    if success:
        print("\n✅ Configuration test passed! Your bot should work with this setup.")
        sys.exit(0)
    else:
        print("\n❌ Configuration test failed. Check the issues above before starting the bot.")
        sys.exit(1)

if __name__ == "__main__":
    main()
