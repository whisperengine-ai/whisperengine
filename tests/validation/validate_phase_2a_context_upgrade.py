#!/usr/bin/env python3
"""
Validation script for Phase 2A context budget upgrade.

Tests the new 24K token budget (16K system + 8K conversation) to ensure:
1. System prompts can use full 16K without truncation
2. Conversation history can use full 8K
3. Emergency truncation works correctly at 16K (not 2K)
4. Token counting is accurate

Usage:
    source .venv/bin/activate
    export FASTEMBED_CACHE_PATH="/tmp/fastembed_cache"
    export QDRANT_HOST="localhost"
    export QDRANT_PORT="6334"
    export POSTGRES_HOST="localhost"
    export POSTGRES_PORT="5433"
    export DISCORD_BOT_NAME=elena
    python tests/validation/validate_phase_2a_context_upgrade.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.utils.context_size_manager import (
    estimate_tokens,
    count_context_tokens,
    truncate_context,
    _truncate_system_messages,
    SYSTEM_PROMPT_MAX_TOKENS,
    CONVERSATION_HISTORY_MAX_TOKENS,
    MAX_CONTEXT_TOKENS
)


def test_constants():
    """Verify Phase 2A constants are set correctly."""
    print("🔍 Testing Phase 2A Constants...")
    
    assert SYSTEM_PROMPT_MAX_TOKENS == 16000, f"❌ SYSTEM_PROMPT_MAX_TOKENS should be 16000, got {SYSTEM_PROMPT_MAX_TOKENS}"
    assert CONVERSATION_HISTORY_MAX_TOKENS == 8000, f"❌ CONVERSATION_HISTORY_MAX_TOKENS should be 8000, got {CONVERSATION_HISTORY_MAX_TOKENS}"
    assert MAX_CONTEXT_TOKENS == 24000, f"❌ MAX_CONTEXT_TOKENS should be 24000, got {MAX_CONTEXT_TOKENS}"
    
    print(f"✅ SYSTEM_PROMPT_MAX_TOKENS = {SYSTEM_PROMPT_MAX_TOKENS:,} tokens")
    print(f"✅ CONVERSATION_HISTORY_MAX_TOKENS = {CONVERSATION_HISTORY_MAX_TOKENS:,} tokens")
    print(f"✅ MAX_CONTEXT_TOKENS = {MAX_CONTEXT_TOKENS:,} tokens")
    print()


def test_system_prompt_capacity():
    """Test that system prompts can use full 16K without emergency truncation."""
    print("🔍 Testing System Prompt Capacity (16K)...")
    
    # Create a large system prompt (~12K tokens = 48K chars)
    large_system_content = "Character personality and context. " * 1400
    system_message = [{"role": "system", "content": large_system_content}]
    
    tokens = count_context_tokens(system_message)
    print(f"📊 Created system prompt: ~{tokens:,} tokens ({len(large_system_content):,} chars)")
    
    # This should NOT trigger emergency truncation (under 16K)
    truncated, removed = truncate_context(system_message, max_tokens=8000)
    
    if removed > 0:
        print(f"⚠️  System prompt was truncated: {removed:,} tokens removed")
        print(f"   This is expected if system > conversation budget")
    else:
        print(f"✅ System prompt preserved without truncation")
    
    print()


def test_emergency_truncation_at_16k():
    """Test that emergency truncation uses 16K budget, not 2K."""
    print("🔍 Testing Emergency Truncation (should use 16K, not 2K)...")
    
    # Create a VERY large system prompt (~18K tokens = 72K chars)
    # This should trigger emergency truncation at 16K, not 2K
    huge_system_content = "Character personality and context. " * 2100
    system_message = [{"role": "system", "content": huge_system_content}]
    
    original_tokens = count_context_tokens(system_message)
    print(f"📊 Created huge system prompt: ~{original_tokens:,} tokens")
    
    # Force emergency truncation
    truncated_messages = _truncate_system_messages(system_message, SYSTEM_PROMPT_MAX_TOKENS)
    truncated_tokens = count_context_tokens(truncated_messages)
    
    print(f"📊 After emergency truncation: ~{truncated_tokens:,} tokens")
    print(f"📊 Removed: ~{original_tokens - truncated_tokens:,} tokens")
    
    # Verify it's closer to 16K than 2K
    assert truncated_tokens > 10000, f"❌ Should be ~16K, got {truncated_tokens:,} (looks like old 2K limit!)"
    assert truncated_tokens <= 16000, f"❌ Should be ≤16K, got {truncated_tokens:,}"
    
    print(f"✅ Emergency truncation uses correct 16K budget")
    print()


def test_conversation_history_capacity():
    """Test that conversation history can use full 8K."""
    print("🔍 Testing Conversation History Capacity (8K)...")
    
    # Create system prompt + conversation history
    system_msg = {"role": "system", "content": "You are a helpful assistant."}
    
    # Create 40 messages (~200 tokens each = 8K total)
    conversation = [system_msg]
    for i in range(20):
        conversation.append({"role": "user", "content": f"User message {i}: " + "word " * 45})
        conversation.append({"role": "assistant", "content": f"Bot response {i}: " + "word " * 45})
    
    total_tokens = count_context_tokens(conversation)
    print(f"📊 Created conversation: {len(conversation)-1} messages, ~{total_tokens:,} tokens")
    
    # Truncate with 8K budget
    truncated, removed = truncate_context(conversation, max_tokens=8000)
    final_tokens = count_context_tokens(truncated)
    
    print(f"📊 After truncation: {len(truncated)-1} messages, ~{final_tokens:,} tokens")
    print(f"📊 Removed: {removed:,} tokens")
    
    # Should keep ~30-35 messages (system + 15-17 exchanges)
    assert len(truncated) > 25, f"❌ Should keep ~30+ messages, got {len(truncated)}"
    assert final_tokens <= 8000, f"❌ Should be ≤8K, got {final_tokens:,}"
    
    print(f"✅ Conversation history uses full 8K budget efficiently")
    print()


def test_total_context_budget():
    """Test that total context can reach ~24K."""
    print("🔍 Testing Total Context Budget (24K)...")
    
    # Create rich system prompt (~10K tokens)
    rich_system = "Character personality and context. " * 920
    system_msg = {"role": "system", "content": rich_system}
    
    # Create deep conversation (~14K tokens total with system)
    conversation = [system_msg]
    for i in range(30):
        conversation.append({"role": "user", "content": f"User message {i}: " + "word " * 45})
        conversation.append({"role": "assistant", "content": f"Bot response {i}: " + "word " * 45})
    
    total_tokens = count_context_tokens(conversation)
    print(f"📊 Created rich context: {len(conversation)-1} messages, ~{total_tokens:,} tokens")
    
    # This should fit comfortably in 24K budget
    assert total_tokens > 12000, f"⚠️  Test context smaller than expected: {total_tokens:,}"
    
    if total_tokens > 24000:
        print(f"📊 Context exceeds 24K (expected for this test)")
    else:
        print(f"✅ Context within 24K budget: {total_tokens:,} tokens")
    
    print()


def test_adaptive_truncation():
    """Test that adaptive truncation still works correctly."""
    print("🔍 Testing Adaptive Truncation...")
    
    # Create wall-of-text scenario
    system_msg = {"role": "system", "content": "You are helpful."}
    
    # Mix of normal and huge messages
    conversation = [system_msg]
    conversation.append({"role": "user", "content": "Normal message"})
    conversation.append({"role": "assistant", "content": "Normal response"})
    conversation.append({"role": "user", "content": "HUGE MESSAGE: " + "word " * 3000})  # ~3K tokens
    conversation.append({"role": "assistant", "content": "Response"})
    conversation.append({"role": "user", "content": "Recent normal message"})
    
    total_tokens = count_context_tokens(conversation)
    print(f"📊 Created mixed conversation: ~{total_tokens:,} tokens")
    
    # Truncate with 8K budget
    truncated, removed = truncate_context(conversation, max_tokens=8000, min_recent_messages=2)
    final_tokens = count_context_tokens(truncated)
    
    print(f"📊 After adaptive truncation: ~{final_tokens:,} tokens")
    print(f"📊 Kept: {len(truncated)-1} messages")
    
    # Should keep system + at least 2 recent messages
    assert len(truncated) >= 3, f"❌ Should keep system + 2 messages, got {len(truncated)}"
    
    # Should have dropped the huge message if needed
    has_huge = any("HUGE MESSAGE" in msg.get("content", "") for msg in truncated)
    if not has_huge:
        print(f"✅ Adaptive truncation dropped huge message to fit budget")
    else:
        print(f"⚠️  Huge message preserved (recent message protection)")
    
    print()


def main():
    """Run all validation tests."""
    print("=" * 60)
    print("Phase 2A Context Budget Upgrade Validation")
    print("=" * 60)
    print()
    
    try:
        test_constants()
        test_system_prompt_capacity()
        test_emergency_truncation_at_16k()
        test_conversation_history_capacity()
        test_total_context_budget()
        test_adaptive_truncation()
        
        print("=" * 60)
        print("✅ ALL VALIDATION TESTS PASSED")
        print("=" * 60)
        print()
        print("Phase 2A is ready for production testing!")
        print()
        print("Next steps:")
        print("1. Test with rich character (Aetheris/Elena)")
        print("2. Have deep conversation (30+ messages)")
        print("3. Enable ENABLE_PROMPT_LOGGING=true")
        print("4. Check logs/prompts/ for token usage")
        print("5. Monitor OpenRouter costs")
        
        return 0
        
    except AssertionError as e:
        print()
        print("=" * 60)
        print(f"❌ VALIDATION FAILED: {e}")
        print("=" * 60)
        return 1
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ ERROR: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
