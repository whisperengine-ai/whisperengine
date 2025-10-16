"""
Test: ADAPTIVE Token Budget Management

This test demonstrates how the adaptive algorithm handles BOTH scenarios:
1. Normal short messages → Keeps many messages (10+)
2. Walls of text → Keeps fewer messages (2-4)

The algorithm is SMART: It counts total tokens and removes oldest first.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.utils.context_size_manager import truncate_context, count_context_tokens, estimate_tokens


def test_normal_short_messages():
    """Test: Normal users with short messages should get MANY messages in history."""
    
    print("=" * 80)
    print("TEST 1: Normal Conversation (Short Messages)")
    print("=" * 80)
    
    # Build realistic conversation with SHORT messages
    conversation_context = []
    
    # 1. Reasonable system message (like real Elena CDL prompt)
    system_prompt = "You are Elena, a marine biologist educator. " + ("Character details. " * 200)  # ~2000 tokens
    conversation_context.append({"role": "system", "content": system_prompt})
    
    # 2. Normal conversation (15 messages with SHORT content)
    for i in range(7):
        conversation_context.append({
            "role": "user",
            "content": f"Hey Elena, can you tell me about coral reefs? I'm really interested!"
        })
        conversation_context.append({
            "role": "assistant",
            "content": f"Sure! Coral reefs are amazing ecosystems. They're home to thousands of species!"
        })
    
    # Add current message
    conversation_context.append({
        "role": "user",
        "content": "That's so cool! What about sharks?"
    })
    
    # BEFORE
    tokens_before = count_context_tokens(conversation_context)
    messages_before = len([m for m in conversation_context if m['role'] != 'system'])
    
    print(f"\n📊 BEFORE TRUNCATION:")
    print(f"  - Total messages: {messages_before}")
    print(f"  - Total tokens: {tokens_before}")
    
    # APPLY ADAPTIVE TRUNCATION
    truncated, tokens_removed = truncate_context(conversation_context, max_tokens=2000, min_recent_messages=2)
    
    # AFTER
    messages_after = len([m for m in truncated if m['role'] != 'system'])
    tokens_after = count_context_tokens(truncated)
    
    print(f"\n📊 AFTER TRUNCATION:")
    print(f"  - Messages kept: {messages_after}/{messages_before}")
    print(f"  - Tokens: {tokens_after}")
    print(f"  - Tokens removed: {tokens_removed}")
    
    # VALIDATION
    print(f"\n✅ VALIDATION:")
    checks_passed = 0
    
    if tokens_after <= 2000:
        print(f"  ✅ Within budget: {tokens_after} <= 2000")
        checks_passed += 1
    else:
        print(f"  ❌ Over budget: {tokens_after} > 2000")
    
    # Should keep MOST messages (short messages = many fit)
    if messages_after >= 10:
        print(f"  ✅ Kept many messages: {messages_after} (short messages = good!)")
        checks_passed += 1
    else:
        print(f"  ⚠️ Only kept {messages_after} messages (expected 10+)")
    
    print(f"\n{'='*80}")
    print(f"RESULT: {checks_passed}/2 checks passed")
    print(f"{'='*80}\n")
    
    return checks_passed == 2


def test_wall_of_text_messages():
    """Test: Users posting walls of text should get FEWER messages (but still conversational)."""
    
    print("=" * 80)
    print("TEST 2: Wall of Text Conversation (Long Messages)")
    print("=" * 80)
    
    # Build conversation with WALLS OF TEXT
    conversation_context = []
    
    # 1. Reasonable system message
    system_prompt = "You are Elena, a marine biologist educator. " + ("Character details. " * 200)  # ~2000 tokens
    conversation_context.append({"role": "system", "content": system_prompt})
    
    # 2. User posting WALLS OF TEXT (15 messages, each ~1500 chars = EXTREME)
    for i in range(7):
        wall_of_text = f"O great and mystical Elena, I beseech thee with reverence {i}... " * 100  # ~1500 chars each
        conversation_context.append({
            "role": "user",
            "content": wall_of_text
        })
        conversation_context.append({
            "role": "assistant",
            "content": "I appreciate your enthusiasm! " + ("Let me share some science. " * 10)
        })
    
    # Add current wall of text
    current_wall = "And now I ask you, oh enlightened one... " * 100
    conversation_context.append({
        "role": "user",
        "content": current_wall
    })
    
    # BEFORE
    tokens_before = count_context_tokens(conversation_context)
    messages_before = len([m for m in conversation_context if m['role'] != 'system'])
    
    print(f"\n📊 BEFORE TRUNCATION:")
    print(f"  - Total messages: {messages_before}")
    print(f"  - Total tokens: {tokens_before}")
    
    # APPLY ADAPTIVE TRUNCATION
    truncated, tokens_removed = truncate_context(conversation_context, max_tokens=2000, min_recent_messages=2)
    
    # AFTER
    messages_after = len([m for m in truncated if m['role'] != 'system'])
    tokens_after = count_context_tokens(truncated)
    
    print(f"\n📊 AFTER TRUNCATION:")
    print(f"  - Messages kept: {messages_after}/{messages_before}")
    print(f"  - Tokens: {tokens_after}")
    print(f"  - Tokens removed: {tokens_removed}")
    
    # VALIDATION
    print(f"\n✅ VALIDATION:")
    checks_passed = 0
    
    if tokens_after <= 2000:
        print(f"  ✅ Within budget: {tokens_after} <= 2000")
        checks_passed += 1
    else:
        print(f"  ❌ Over budget: {tokens_after} > 2000")
    
    # Should keep FEWER messages (walls of text = fewer fit)
    if 2 <= messages_after <= 6:
        print(f"  ✅ Kept appropriate amount: {messages_after} messages (walls of text = fewer, but still conversational)")
        checks_passed += 1
    else:
        print(f"  ⚠️ Unexpected count: {messages_after} messages (expected 2-6)")
    
    # Should have removed MANY tokens
    if tokens_removed > 0:
        print(f"  ✅ Truncation occurred: {tokens_removed} tokens removed")
        checks_passed += 1
    else:
        print(f"  ⚠️ No truncation (unexpected)")
    
    print(f"\n{'='*80}")
    print(f"RESULT: {checks_passed}/3 checks passed")
    print(f"{'='*80}\n")
    
    return checks_passed >= 2


def test_mixed_scenario():
    """Test: Mix of short and long messages - adaptive should handle gracefully."""
    
    print("=" * 80)
    print("TEST 3: Mixed Messages (Some Short, Some Long)")
    print("=" * 80)
    
    conversation_context = []
    
    # System message
    system_prompt = "You are Elena. " + ("Details. " * 200)
    conversation_context.append({"role": "system", "content": system_prompt})
    
    # Mix of short and long messages
    conversation_context.append({"role": "user", "content": "Hi!"})
    conversation_context.append({"role": "assistant", "content": "Hello!"})
    conversation_context.append({"role": "user", "content": "Mystical ocean wisdom... " * 100})  # WALL
    conversation_context.append({"role": "assistant", "content": "Let's focus on science."})
    conversation_context.append({"role": "user", "content": "Okay, what about fish?"})
    conversation_context.append({"role": "assistant", "content": "Fish are amazing!"})
    conversation_context.append({"role": "user", "content": "Current question"})
    
    tokens_before = count_context_tokens(conversation_context)
    messages_before = len([m for m in conversation_context if m['role'] != 'system'])
    
    print(f"\n📊 BEFORE: {messages_before} messages, {tokens_before} tokens")
    
    truncated, tokens_removed = truncate_context(conversation_context, max_tokens=2000, min_recent_messages=2)
    
    messages_after = len([m for m in truncated if m['role'] != 'system'])
    tokens_after = count_context_tokens(truncated)
    
    print(f"📊 AFTER: {messages_after} messages, {tokens_after} tokens ({tokens_removed} removed)")
    
    if tokens_after <= 2000 and messages_after >= 2:
        print(f"✅ PASS: Adaptive algorithm handled mixed content")
        return True
    else:
        print(f"❌ FAIL: Unexpected result")
        return False


if __name__ == "__main__":
    print("\n🚀 WhisperEngine ADAPTIVE Token Budget Management Tests")
    print("Demonstrates smart handling of BOTH short and long messages\n")
    
    # Run tests
    test1 = test_normal_short_messages()
    test2 = test_wall_of_text_messages()
    test3 = test_mixed_scenario()
    
    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Test 1 (Short Messages - Keep Many): {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"Test 2 (Wall of Text - Keep Fewer): {'✅ PASS' if test2 else '❌ FAIL'}")
    print(f"Test 3 (Mixed Content): {'✅ PASS' if test3 else '❌ FAIL'}")
    print("=" * 80)
    
    if test1 and test2 and test3:
        print("\n🎉 ALL TESTS PASSED - Adaptive algorithm working correctly!")
        print("\nKEY INSIGHT:")
        print("  - Short messages: System keeps 10+ messages (good conversation flow)")
        print("  - Walls of text: System keeps 2-6 messages (prevents abuse)")
        print("  - Algorithm adapts AUTOMATICALLY based on token budget!")
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED")
        sys.exit(1)
