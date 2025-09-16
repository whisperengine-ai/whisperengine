#!/usr/bin/env python3
"""Test Phi-3-Mini with actual WhisperEngine system prompt."""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from env_manager import load_environment
from src.llm.llm_client import LLMClient


def test_phi3_with_full_prompt():
    """Test Phi-3-Mini with the actual WhisperEngine system prompt."""

    # Load environment
    if not load_environment():
        return False

    # Read the actual system prompt
    with open("system_prompt.md") as f:
        system_prompt = f.read()

    # Check configuration
    os.getenv("LLM_CHAT_API_URL")
    os.getenv("LOCAL_LLM_MODEL")


    try:
        llm_client = LLMClient()

        # Test with shorter system prompt first
        short_system = "You are Dream of the Endless. Respond with wisdom and empathy."
        user_message = "Hello Dream, can you tell me about the nature of dreams?"

        short_messages = [
            {"role": "system", "content": short_system},
            {"role": "user", "content": user_message},
        ]

        response = llm_client.generate_chat_completion(short_messages, max_tokens=100)

        if response and "choices" in response and len(response["choices"]) > 0:
            response["choices"][0]["message"]["content"]
        else:
            return False

        # Now test with a portion of the full system prompt
        medium_system = system_prompt[:4000]  # ~1000 tokens
        medium_messages = [
            {"role": "system", "content": medium_system},
            {"role": "user", "content": user_message},
        ]

        response = llm_client.generate_chat_completion(medium_messages, max_tokens=100)

        if response and "choices" in response and len(response["choices"]) > 0:
            response["choices"][0]["message"]["content"]
        else:
            return False

        # Test with full system prompt
        full_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        # Estimate total tokens
        total_chars = len(system_prompt) + len(user_message)
        total_chars // 4


        response = llm_client.generate_chat_completion(full_messages, max_tokens=200)

        if response and "choices" in response and len(response["choices"]) > 0:
            response["choices"][0]["message"]["content"]
            return True
        else:
            return False

    except Exception:
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_phi3_with_full_prompt()
    sys.exit(0 if success else 1)
