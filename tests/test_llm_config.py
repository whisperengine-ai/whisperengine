#!/usr/bin/env python3
"""
Test LLM Client configuration to diagnose the 404 error
"""

import sys

sys.path.insert(0, ".")

# Load environment
from env_manager import load_environment

load_environment()

# Import and test LLM client
from src.llm.llm_client import LLMClient


def test_llm_client():

    # Create LLM client
    client = LLMClient()


    # Test simple chat completion
    try:
        messages = [{"role": "user", "content": "Say hello briefly"}]

        # Enable debug logging
        import logging

        logging.basicConfig(level=logging.DEBUG)

        client.get_chat_response(messages)

    except Exception as e:

        # Try to get more details
        if hasattr(e, "__cause__") and e.__cause__:
            pass

        # Test if the issue is with model parameter
        try:
            client.generate_chat_completion(
                messages=messages, model="phi3:mini", temperature=0.7, max_tokens=50
            )
        except Exception:
            pass


if __name__ == "__main__":
    test_llm_client()
