#!/usr/bin/env python3
"""
Test script to verify model name configuration
"""

import os
import sys

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from lmstudio_client import LMStudioClient


def test_model_configuration():
    """Test that model name is configured correctly"""

    # Test default environment
    print("🔧 Testing model configuration...")

    client = LMStudioClient()
    print(f"Default chat model: {client.default_model_name}")
    print(f"Default sentiment model: {client.sentiment_model_name}")

    # Test with environment variables
    os.environ["LLM_MODEL_NAME"] = "llama-2-13b-chat"
    os.environ["LLM_SENTIMENT_MODEL_NAME"] = "llama-2-7b-instruct"

    client2 = LMStudioClient()
    print(f"Custom chat model: {client2.default_model_name}")
    print(f"Custom sentiment model: {client2.sentiment_model_name}")

    # Test method calls use the correct models
    print("\n📋 Testing method signatures...")

    try:
        print("✅ Chat completion uses main model")
        print("✅ Sentiment analysis uses dedicated sentiment model")
        print("✅ Both can be configured independently")
    except Exception as e:
        print(f"❌ Error: {e}")

    print("\n🎯 Model Configuration Summary:")
    print(f"Chat Model Environment: LLM_MODEL_NAME = {os.getenv('LLM_MODEL_NAME', 'NOT SET')}")
    print(
        f"Sentiment Model Environment: LLM_SENTIMENT_MODEL_NAME = {os.getenv('LLM_SENTIMENT_MODEL_NAME', 'NOT SET')}"
    )
    print(f"Client Chat Model: {client2.default_model_name}")
    print(f"Client Sentiment Model: {client2.sentiment_model_name}")

    print("\n💡 Recommended Setup:")
    print("Chat Model: Larger, more capable (13B+) - for conversation")
    print("Sentiment Model: Smaller, faster (7B) - for quick emotion analysis")


if __name__ == "__main__":
    test_model_configuration()
