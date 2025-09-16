#!/usr/bin/env python3
"""Test script to validate local LLM bundling functionality."""

import os
import sys
import asyncio

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from env_manager import load_environment
from src.llm.llm_client import LLMClient


async def test_bundled_llm():
    """Test that bundled local LLM is working."""
    print("🧪 Testing bundled local LLM functionality...")

    # Load environment
    if not load_environment():
        print("❌ Failed to load environment")
        return False

    # Check configuration
    api_url = os.getenv("LLM_CHAT_API_URL")
    if not api_url or not api_url.startswith("local://"):
        print(f"❌ Not configured for local LLM: {api_url}")
        return False

    print(f"✅ Local LLM configuration detected: {api_url}")

    try:
        # Initialize LLM client
        print("🔄 Initializing LLM client...")
        llm_client = LLMClient()

        # Simple test message
        print("🔄 Testing simple conversation...")
        test_messages = [
            {"role": "system", "content": "You are a helpful AI assistant. Respond briefly."},
            {"role": "user", "content": "Hello! Can you tell me your name?"},
        ]

        # Test basic generation (sync version)
        response = llm_client.generate_chat_completion(test_messages, max_tokens=50)

        if response and "choices" in response and len(response["choices"]) > 0:
            response_text = response["choices"][0]["message"]["content"]
            print(f"✅ Local LLM responded: {response_text}")
            return True
        else:
            print(f"❌ Invalid response format: {response}")
            return False

    except Exception as e:
        print(f"❌ Local LLM test failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_bundled_llm())
    print(
        f"\n{'✅ Local LLM bundling test PASSED' if success else '❌ Local LLM bundling test FAILED'}"
    )
    sys.exit(0 if success else 1)
