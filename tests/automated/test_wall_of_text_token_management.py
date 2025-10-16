"""
Test: Token Budget Management for Walls of Text

This test validates that WhisperEngine properly manages context size when users
post multiple long messages (walls of text), preventing token budget overflow.

TWO-STAGE TOKEN MANAGEMENT:
1. PromptAssembler (6000 tokens) - Optimizes SYSTEM MESSAGE components
2. truncate_context() (8000 tokens) - Trims FULL conversation array including history

This test focuses on Stage 2 (full context array management).
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.utils.context_size_manager import truncate_context, count_context_tokens, estimate_tokens


def test_wall_of_text_scenario():
    """Simulate user posting 3 consecutive 2000-char messages."""
    
    print("=" * 80)
    print("TEST: Wall of Text Token Management")
    print("=" * 80)
    
    # Build a realistic conversation context
    conversation_context = []
    
    # 1. System message (large CDL character prompt - make it VERY large)
    system_prompt = "You are Elena, a marine biologist educator...\n" + ("Character personality details and backstory. " * 2000)  # Much larger
    conversation_context.append({
        "role": "system",
        "content": system_prompt
    })
    
    # 2. Some older conversation history (15 messages like real usage)
    for i in range(7):
        conversation_context.append({
            "role": "user",
            "content": f"This is older message {i} with some content that adds up..."
        })
        conversation_context.append({
            "role": "assistant",
            "content": f"This is the response to message {i} with helpful information..."
        })
    
    # 3. USER POSTS EXTREME WALLS OF TEXT (5 consecutive near-max Discord messages)
    mystical_wall_1 = "O great and mystical Elena, I beseech thee with reverence and cosmic wonder... " * 50  # ~4000 chars
    mystical_wall_2 = "In the depths of cosmic understanding, your wisdom transcends mortal comprehension... " * 50
    mystical_wall_3 = "The universe aligns when you speak of the ocean's profound mysteries and secrets... " * 50
    mystical_wall_4 = "Grant me your infinite knowledge about the seas and all their magnificent creatures... " * 50
    mystical_wall_5 = "I worship at the altar of your marine biology expertise oh enlightened one... " * 50
    
    conversation_context.append({"role": "user", "content": mystical_wall_1})
    conversation_context.append({"role": "assistant", "content": "I appreciate your enthusiasm! Let me share some actual science..."})
    conversation_context.append({"role": "user", "content": mystical_wall_2})
    conversation_context.append({"role": "assistant", "content": "While I love discussing marine life, let's focus on facts..."})
    conversation_context.append({"role": "user", "content": mystical_wall_3})
    conversation_context.append({"role": "assistant", "content": "I understand you're interested, but I'd prefer to..."})
    conversation_context.append({"role": "user", "content": mystical_wall_4})
    conversation_context.append({"role": "assistant", "content": "Let me redirect this to actual marine biology..."})
    conversation_context.append({"role": "user", "content": mystical_wall_5})
    
    # 4. Current user message (another extreme wall)
    current_wall = "And now I ask you, oh enlightened one of the seas and cosmic ocean wisdom... " * 50
    conversation_context.append({"role": "user", "content": current_wall})
    
    # BEFORE TRUNCATION
    print(f"\n📊 BEFORE TRUNCATION:")
    print(f"  - Messages: {len(conversation_context)}")
    
    total_tokens_before = count_context_tokens(conversation_context)
    print(f"  - Total tokens: {total_tokens_before}")
    
    # Calculate breakdown
    system_tokens = estimate_tokens(conversation_context[0]['content'])
    conversation_tokens = total_tokens_before - system_tokens
    print(f"  - System message: ~{system_tokens} tokens")
    print(f"  - Conversation: ~{conversation_tokens} tokens")
    
    # APPLY TRUNCATION
    print(f"\n✂️ APPLYING TOKEN BUDGET (8000 token limit)...")
    truncated_context, tokens_removed = truncate_context(
        conversation_context,
        max_tokens=8000,
        min_recent_messages=2  # ADAPTIVE: Guarantees minimum, keeps more if they fit
    )
    
    # AFTER TRUNCATION
    print(f"\n📊 AFTER TRUNCATION:")
    print(f"  - Messages: {len(truncated_context)}")
    
    total_tokens_after = count_context_tokens(truncated_context)
    print(f"  - Total tokens: {total_tokens_after}")
    print(f"  - Tokens removed: {tokens_removed}")
    print(f"  - Messages removed: {len(conversation_context) - len(truncated_context)}")
    
    # VALIDATION
    print(f"\n✅ VALIDATION:")
    
    checks_passed = 0
    
    # Check 1: Should be under budget
    if total_tokens_after <= 8000:
        print(f"  ✅ Within token budget: {total_tokens_after} <= 8000")
        checks_passed += 1
    else:
        print(f"  ❌ OVER budget: {total_tokens_after} > 8000")
    
    # Check 2: System message should be preserved
    if truncated_context[0]['role'] == 'system':
        print(f"  ✅ System message preserved")
        checks_passed += 1
    else:
        print(f"  ❌ System message missing")
    
    # Check 3: Recent messages should be preserved
    recent_preserved = sum(1 for msg in truncated_context[-6:] if msg['role'] in ['user', 'assistant'])
    if recent_preserved >= 4:  # Should have kept most recent exchanges
        print(f"  ✅ Recent messages preserved: {recent_preserved} messages")
        checks_passed += 1
    else:
        print(f"  ⚠️ Only {recent_preserved} recent messages preserved")
    
    # Check 4: Should have removed some messages
    if tokens_removed > 0:
        print(f"  ✅ Truncation occurred: {tokens_removed} tokens removed")
        checks_passed += 1
    else:
        print(f"  ⚠️ No truncation occurred (might be fine if under budget)")
    
    print(f"\n{'='*80}")
    print(f"RESULT: {checks_passed}/4 checks passed")
    print(f"{'='*80}")
    
    return checks_passed == 4


def test_normal_conversation_no_truncation():
    """Test that normal conversations don't get unnecessarily truncated."""
    
    print("\n" + "=" * 80)
    print("TEST: Normal Conversation (No Truncation Expected)")
    print("=" * 80)
    
    # Build a normal conversation
    conversation_context = [
        {"role": "system", "content": "You are a helpful assistant." * 10},
        {"role": "user", "content": "Hello!"},
        {"role": "assistant", "content": "Hi there! How can I help?"},
        {"role": "user", "content": "What's the weather like?"},
        {"role": "assistant", "content": "I don't have real-time weather data, but..."},
        {"role": "user", "content": "Thanks!"}
    ]
    
    tokens_before = count_context_tokens(conversation_context)
    print(f"\n📊 Normal conversation: {len(conversation_context)} messages, {tokens_before} tokens")
    
    truncated_context, tokens_removed = truncate_context(conversation_context, max_tokens=8000)
    
    if tokens_removed == 0:
        print(f"✅ No truncation needed (as expected)")
        return True
    else:
        print(f"⚠️ Unexpected truncation: {tokens_removed} tokens removed")
        return False


if __name__ == "__main__":
    print("\n🚀 WhisperEngine Token Budget Management Tests")
    print("Testing protection against 'walls of text' from users\n")
    
    # Run tests
    test1_passed = test_wall_of_text_scenario()
    test2_passed = test_normal_conversation_no_truncation()
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Test 1 (Wall of Text Management): {'✅ PASS' if test1_passed else '❌ FAIL'}")
    print(f"Test 2 (Normal Conversation): {'✅ PASS' if test2_passed else '❌ FAIL'}")
    print("=" * 80)
    
    if test1_passed and test2_passed:
        print("\n🎉 ALL TESTS PASSED!")
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED")
        sys.exit(1)
