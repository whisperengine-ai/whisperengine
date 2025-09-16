#!/usr/bin/env python3
"""Test Phi-3-Mini with actual WhisperEngine system prompt."""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from env_manager import load_environment
from src.llm.llm_client import LLMClient


def test_phi3_with_full_prompt():
    """Test Phi-3-Mini with the actual WhisperEngine system prompt."""
    print("🧪 Testing Phi-3-Mini with full WhisperEngine system prompt...")

    # Load environment
    if not load_environment():
        print("❌ Failed to load environment")
        return False

    # Read the actual system prompt
    with open("system_prompt.md", "r") as f:
        system_prompt = f.read()

    # Check configuration
    api_url = os.getenv("LLM_CHAT_API_URL")
    local_model = os.getenv("LOCAL_LLM_MODEL")

    print(f"📊 Configuration:")
    print(f"   API URL: {api_url}")
    print(f"   Local Model: {local_model}")
    print(f"   System prompt: {len(system_prompt):,} chars (~{len(system_prompt)//4:,} tokens)")

    try:
        print("\n🔄 Initializing Phi-3-Mini LLM client...")
        llm_client = LLMClient()

        # Test with shorter system prompt first
        short_system = "You are Dream of the Endless. Respond with wisdom and empathy."
        user_message = "Hello Dream, can you tell me about the nature of dreams?"

        print("\n🔄 Testing with short system prompt...")
        short_messages = [
            {"role": "system", "content": short_system},
            {"role": "user", "content": user_message},
        ]

        response = llm_client.generate_chat_completion(short_messages, max_tokens=100)

        if response and "choices" in response and len(response["choices"]) > 0:
            response_text = response["choices"][0]["message"]["content"]
            print(f"✅ Short prompt test PASSED")
            print(f"   Response: {response_text[:150]}...")
        else:
            print(f"❌ Short prompt test failed: {response}")
            return False

        # Now test with a portion of the full system prompt
        print(f"\n🔄 Testing with medium system prompt (~1000 tokens)...")
        medium_system = system_prompt[:4000]  # ~1000 tokens
        medium_messages = [
            {"role": "system", "content": medium_system},
            {"role": "user", "content": user_message},
        ]

        response = llm_client.generate_chat_completion(medium_messages, max_tokens=100)

        if response and "choices" in response and len(response["choices"]) > 0:
            response_text = response["choices"][0]["message"]["content"]
            print(f"✅ Medium prompt test PASSED")
            print(f"   Response: {response_text[:150]}...")
        else:
            print(f"❌ Medium prompt test failed")
            return False

        # Test with full system prompt
        print(f"\n🔄 Testing with FULL system prompt (~3,837 tokens)...")
        full_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        # Estimate total tokens
        total_chars = len(system_prompt) + len(user_message)
        estimated_tokens = total_chars // 4

        print(f"   Total estimated tokens: {estimated_tokens:,}")
        print(f"   Phi-3-Mini limit: 4,096 tokens")
        print(f"   Status: {'✅ Within limit' if estimated_tokens <= 4096 else '❌ Over limit'}")

        response = llm_client.generate_chat_completion(full_messages, max_tokens=200)

        if response and "choices" in response and len(response["choices"]) > 0:
            response_text = response["choices"][0]["message"]["content"]
            print(f"✅ FULL PROMPT TEST PASSED! 🎉")
            print(f"   Phi-3-Mini successfully handled {estimated_tokens:,} token prompt")
            print(f"   Response: {response_text[:200]}...")
            return True
        else:
            print(f"❌ Full prompt test failed: {response}")
            return False

    except Exception as e:
        print(f"❌ Phi-3-Mini test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_phi3_with_full_prompt()
    print(f"\n{'✅ Phi-3-Mini upgrade SUCCESS' if success else '❌ Phi-3-Mini upgrade FAILED'}")
    sys.exit(0 if success else 1)
