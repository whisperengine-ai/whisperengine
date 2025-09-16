#!/usr/bin/env python3
"""Test actual WhisperEngine system prompt token usage."""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))


def test_actual_system_prompt():
    """Test real system prompt size."""

    # Read the actual system prompt
    with open("system_prompt.md") as f:
        system_prompt = f.read()

    # Count characters and estimate tokens
    chars = len(system_prompt)
    estimated_tokens = chars // 4


    # Test what happens with a typical user message too
    user_message = (
        "Hello Dream, I've been having strange dreams lately. Can you help me understand them?"
    )
    user_tokens = len(user_message) // 4

    estimated_tokens + user_tokens



if __name__ == "__main__":
    test_actual_system_prompt()
