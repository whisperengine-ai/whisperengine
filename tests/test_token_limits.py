#!/usr/bin/env python3
"""Test script to validate token limits with realistic prompts."""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from env_manager import load_environment
from src.llm.llm_client import LLMClient


def test_token_limits():
    """Test DialoGPT with longer realistic prompts."""
    print("🧪 Testing token limits with realistic prompts...")

    # Load environment
    if not load_environment():
        print("❌ Failed to load environment")
        return False

    try:
        llm_client = LLMClient()

        # Create a longer, realistic prompt
        long_prompt = """You are Dream of the Endless, an ancient and powerful entity from Neil Gaiman's Sandman series. You embody dreams, stories, and the realm of sleep. You speak with wisdom that spans millennia, often in poetic or metaphorical language. You understand the deeper meanings behind human desires and fears.

A user approaches you in the Dreaming, seeking guidance about their recurring nightmares about being trapped in an endless maze. They've been having these dreams for months, and they're affecting their waking life. They feel lost and uncertain about their life direction.

Please respond as Dream would - with empathy, wisdom, and perhaps a touch of the mystical. Help them understand what their dreams might represent and offer guidance for both their dream life and waking concerns."""

        test_messages = [
            {"role": "system", "content": long_prompt},
            {
                "role": "user",
                "content": "Dream, I keep having these nightmares about being trapped in an endless maze. I run and run but never find the exit. I wake up exhausted and it's affecting my work and relationships. What does this mean? How can I find peace?",
            },
        ]

        # Count tokens (rough estimate: 4 chars = 1 token)
        total_chars = sum(len(msg["content"]) for msg in test_messages)
        estimated_tokens = total_chars // 4

        print(f"📊 Prompt Analysis:")
        print(f"   Total characters: {total_chars}")
        print(f"   Estimated tokens: {estimated_tokens}")
        print(f"   DialoGPT limit: 1024 tokens")
        print(f"   Status: {'❌ EXCEEDS LIMIT' if estimated_tokens > 1024 else '✅ Within limit'}")

        if estimated_tokens > 1024:
            print(f"⚠️  This prompt will likely cause issues with DialoGPT")
            print(f"   Overflow: {estimated_tokens - 1024} tokens over limit")

            # Try with shorter prompt
            short_messages = [
                {"role": "system", "content": "You are Dream of the Endless. Respond with wisdom."},
                {"role": "user", "content": "I have nightmares about mazes. What does this mean?"},
            ]

            print(f"\n🔄 Testing with shortened prompt...")
            response = llm_client.generate_chat_completion(short_messages, max_tokens=100)

            if response and "choices" in response:
                response_text = response["choices"][0]["message"]["content"]
                print(f"✅ Short prompt worked: {response_text[:100]}...")
                return True
        else:
            print(f"\n🔄 Testing full prompt...")
            response = llm_client.generate_chat_completion(test_messages, max_tokens=200)

            if response and "choices" in response:
                response_text = response["choices"][0]["message"]["content"]
                print(f"✅ Full prompt worked: {response_text[:100]}...")
                return True

    except Exception as e:
        print(f"❌ Token limit test failed: {e}")
        return False


if __name__ == "__main__":
    success = test_token_limits()
    sys.exit(0 if success else 1)
