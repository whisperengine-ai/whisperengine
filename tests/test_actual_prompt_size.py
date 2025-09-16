#!/usr/bin/env python3
"""Test actual WhisperEngine system prompt token usage."""

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_actual_system_prompt():
    """Test real system prompt size."""
    print("🧪 Testing actual WhisperEngine system prompt...")
    
    # Read the actual system prompt
    with open('system_prompt.md', 'r') as f:
        system_prompt = f.read()
    
    # Count characters and estimate tokens
    chars = len(system_prompt)
    estimated_tokens = chars // 4
    
    print(f"📊 WhisperEngine System Prompt Analysis:")
    print(f"   Total characters: {chars:,}")
    print(f"   Estimated tokens: {estimated_tokens:,}")
    print(f"   DialoGPT limit: 1,024 tokens")
    print(f"   Overflow: {estimated_tokens - 1024:,} tokens over limit")
    print(f"   Multiplier: {estimated_tokens / 1024:.1f}x over limit")
    
    # Test what happens with a typical user message too
    user_message = "Hello Dream, I've been having strange dreams lately. Can you help me understand them?"
    user_tokens = len(user_message) // 4
    
    total_tokens = estimated_tokens + user_tokens
    print(f"\n📊 With User Message:")
    print(f"   User message tokens: {user_tokens}")
    print(f"   Total prompt tokens: {total_tokens:,}")
    print(f"   Final overflow: {total_tokens - 1024:,} tokens over limit")
    
    print(f"\n💡 Recommendation:")
    print(f"   DialoGPT is completely inadequate for this use case")
    print(f"   Need model with at least 4096+ token context")
    print(f"   Suggested alternatives:")
    print(f"   - Phi-3-Mini (4096 tokens, ~2GB)")
    print(f"   - Llama-2-7B-Chat (4096 tokens, ~4GB)")  
    print(f"   - TinyLlama (2048 tokens, ~600MB)")

if __name__ == "__main__":
    test_actual_system_prompt()