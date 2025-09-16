#!/usr/bin/env python3
"""Test script to validate local LLM bundling functionality."""

import asyncio
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from env_manager import load_environment
from src.llm.llm_client import LLMClient


async def test_bundled_llm():
    """Test that bundled local LLM is working."""

    # Load environment
    if not load_environment():
        return False

    # Check configuration
    api_url = os.getenv("LLM_CHAT_API_URL")
    if not api_url or not api_url.startswith("local://"):
        return False


    try:
        # Initialize LLM client
        llm_client = LLMClient()

        # Simple test message
        test_messages = [
            {"role": "system", "content": "You are a helpful AI assistant. Respond briefly."},
            {"role": "user", "content": "Hello! Can you tell me your name?"},
        ]

        # Test basic generation (sync version)
        response = llm_client.generate_chat_completion(test_messages, max_tokens=50)

        if response and "choices" in response and len(response["choices"]) > 0:
            response["choices"][0]["message"]["content"]
            return True
        else:
            return False

    except Exception:
        return False


if __name__ == "__main__":
    success = asyncio.run(test_bundled_llm())
    sys.exit(0 if success else 1)
