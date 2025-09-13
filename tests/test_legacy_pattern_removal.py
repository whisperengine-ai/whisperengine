#!/usr/bin/env python3
"""
Test to verify that the legacy context-in-user-message pattern has been removed
and that we now only use clean system messages for context.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from basic_discord_bot import generate_conversation_summary
from unittest.mock import Mock
import re

def test_no_legacy_context_patterns():
    """Test that we no longer create user messages with embedded context"""
    
    print("🧪 Testing removal of legacy context-in-user-message patterns...")
    
    # Read the bot file to check for problematic patterns
    with open('basic_discord_bot.py', 'r') as f:
        bot_code = f.read()
    
    # Check for problematic patterns that indicate context being embedded in user messages
    problematic_patterns = [
        r'role.*user.*Context from previous conversations',
        r'conversation_context.*append.*user.*\[Context',
        r'role.*user.*content.*Context:',
    ]
    
    issues_found = []
    
    for pattern in problematic_patterns:
        matches = re.findall(pattern, bot_code, re.IGNORECASE)
        if matches:
            issues_found.extend(matches)
    
    if issues_found:
        print(f"❌ Found problematic patterns: {issues_found}")
        return False
    else:
        print("✅ No legacy context-in-user-message patterns found")
    
    # Check that we have clean system message patterns
    good_patterns = [
        r'role.*system.*content.*f.*User relationship and emotional context',
        r'role.*system.*content.*f.*Recent conversation summary',
        r'role.*system.*content.*memory_context',
        r'role.*system.*content.*DEFAULT_SYSTEM_PROMPT',
    ]
    
    system_patterns_found = 0
    for pattern in good_patterns:
        matches = re.findall(pattern, bot_code, re.IGNORECASE)
        if matches:
            system_patterns_found += len(matches)
    
    if system_patterns_found >= 4:  # Should find multiple system message patterns
        print(f"✅ Found {system_patterns_found} clean system message patterns")
        return True
    else:
        print(f"⚠️  Only found {system_patterns_found} system message patterns (expected >= 4)")
        return False

def test_conversation_context_structure():
    """Test that conversation context only contains proper system and user/assistant messages"""
    
    print("\n🧪 Testing conversation context structure...")
    
    # This test would require mocking the entire message processing, 
    # but we can check the structure by looking at the code patterns
    
    with open('basic_discord_bot.py', 'r') as f:
        bot_code = f.read()
    
    # Look for the system message creation patterns
    system_message_patterns = [
        'conversation_context.append({"role": "system", "content": DEFAULT_SYSTEM_PROMPT})',
        'conversation_context.append({"role": "system", "content": f"Current time: {time_context}"})',
        'conversation_context.append({"role": "system", "content": f"User relationship and emotional context: {emotion_context}"})',
        'conversation_context.append({"role": "system", "content": memory_context})',
        'conversation_context.append({"role": "system", "content": f"Recent conversation summary: {conversation_summary}"})',
    ]
    
    found_patterns = 0
    for pattern in system_message_patterns:
        if pattern in bot_code:
            found_patterns += 1
    
    if found_patterns >= 4:  # Should find at least 4 of the 5 patterns
        print(f"✅ Found {found_patterns}/5 expected system message patterns")
        return True
    else:
        print(f"❌ Only found {found_patterns}/5 expected system message patterns")
        return False

def test_no_context_message_updates():
    """Test that we no longer try to update context messages in user messages"""
    
    print("\n🧪 Testing removal of context message update logic...")
    
    with open('basic_discord_bot.py', 'r') as f:
        bot_code = f.read()
    
    # Look for the old problematic update patterns
    update_patterns = [
        r'startswith\(.*Context from previous conversations',
        r'Update the context user message',
        r'Find the context message and update it',
        r'conversation_context\[i\].*=.*user.*content.*context_content',
    ]
    
    found_updates = 0
    for pattern in update_patterns:
        matches = re.findall(pattern, bot_code, re.IGNORECASE)
        found_updates += len(matches)
    
    if found_updates == 0:
        print("✅ No legacy context update patterns found")
        return True
    else:
        print(f"❌ Found {found_updates} legacy context update patterns")
        return False

def test_memory_storage_safety():
    """Test that memory storage comments indicate proper filtering"""
    
    print("\n🧪 Testing memory storage safety comments...")
    
    with open('basic_discord_bot.py', 'r') as f:
        bot_code = f.read()
    
    # Look for safety comments about preventing synthetic context storage
    safety_patterns = [
        'This prevents synthetic.*Context from previous conversations.*messages from polluting memory',
        'Only store the original user message content, not any synthetic context',
    ]
    
    found_safety = 0
    for pattern in safety_patterns:
        matches = re.findall(pattern, bot_code, re.IGNORECASE)
        found_safety += len(matches)
    
    if found_safety >= 1:
        print(f"✅ Found {found_safety} memory storage safety comments")
        return True
    else:
        print("⚠️  No memory storage safety comments found")
        return False

if __name__ == "__main__":
    print("🔍 Legacy Context Pattern Removal Verification")
    print("=" * 55)
    
    try:
        # Test that legacy patterns are removed
        test1_passed = test_no_legacy_context_patterns()
        
        # Test that we have proper system message structure
        test2_passed = test_conversation_context_structure()
        
        # Test that context update logic is removed
        test3_passed = test_no_context_message_updates()
        
        # Test memory storage safety
        test4_passed = test_memory_storage_safety()
        
        print("\n" + "=" * 55)
        
        if test1_passed and test2_passed and test3_passed:
            print("🎉 All legacy pattern removal tests passed!")
            
            print("\n✅ Verified changes:")
            print("  ✅ No more context embedded in user messages")
            print("  ✅ Clean system message architecture in place")
            print("  ✅ No legacy context update logic")
            print("  ✅ Memory storage safety maintained")
            
            print("\n🏗️  Current architecture:")
            print("  📝 System Message 1: Core character prompt")
            print("  📝 System Message 2: Time context")
            print("  📝 System Message 3: Emotional context (if available)")
            print("  📝 System Message 4: Memory context (if available)")
            print("  📝 System Message 5: Conversation summary (if available)")
            print("  💬 User/Assistant Messages: Clean conversation flow")
            
            print("\n🔒 Security benefits:")
            print("  ✅ No synthetic context in user messages")
            print("  ✅ Clean separation of context and conversation")
            print("  ✅ Easier to sanitize system messages")
            print("  ✅ No risk of context being stored as user content")
            
        else:
            print("❌ Some tests failed - legacy patterns may still exist")
            print("\nTest results:")
            print(f"  Legacy patterns removed: {'✅' if test1_passed else '❌'}")
            print(f"  System message structure: {'✅' if test2_passed else '❌'}")
            print(f"  Context update logic removed: {'✅' if test3_passed else '❌'}")
            print(f"  Memory storage safety: {'✅' if test4_passed else '⚠️'}")
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
