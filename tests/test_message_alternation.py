#!/usr/bin/env python3
"""
Test message alternation in conversation context building.

This test verifies that the conversation context maintains proper user/assistant alternation
as required by many LLM APIs (OpenAI, Anthropic, etc.).

Key requirements:
1. First message must be system
2. After initial system message(s), must alternate: user -> assistant -> user -> assistant
3. No system messages in the middle of user/assistant sequence
4. Last message must be user (the current message)
"""

import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.message_processor import MessageProcessor, MessageContext
from src.memory.memory_protocol import create_memory_manager
from src.llm.llm_protocol import create_llm_client


async def validate_message_alternation(messages):
    """Validate that messages follow proper alternation rules."""
    print("\n" + "="*80)
    print("MESSAGE ALTERNATION VALIDATION")
    print("="*80)
    
    errors = []
    
    # Rule 1: First message(s) must be system
    if not messages or messages[0].get("role") != "system":
        errors.append("❌ FAIL: First message must be 'system' role")
    else:
        print("✅ PASS: First message is 'system'")
    
    # Rule 2: Find where user/assistant messages start
    first_non_system_idx = 0
    for i, msg in enumerate(messages):
        if msg.get("role") != "system":
            first_non_system_idx = i
            break
    
    # Rule 3: All system messages must be at the beginning
    system_messages_at_start = messages[:first_non_system_idx]
    remaining_messages = messages[first_non_system_idx:]
    
    has_system_in_middle = any(msg.get("role") == "system" for msg in remaining_messages)
    if has_system_in_middle:
        errors.append("❌ FAIL: System messages found in middle of conversation")
        print("❌ FAIL: System messages found in middle of conversation")
        
        # Show where system messages appear
        for i, msg in enumerate(remaining_messages):
            if msg.get("role") == "system":
                print(f"   System message at position {first_non_system_idx + i}: '{msg.get('content', '')[:100]}...'")
    else:
        print(f"✅ PASS: All {len(system_messages_at_start)} system message(s) at beginning")
    
    # Rule 4: After system messages, must alternate user/assistant
    if remaining_messages:
        expected_role = "user"  # First message after system should be user
        for i, msg in enumerate(remaining_messages):
            actual_role = msg.get("role")
            
            if actual_role not in ["user", "assistant"]:
                errors.append(f"❌ FAIL: Invalid role '{actual_role}' at position {first_non_system_idx + i}")
                print(f"❌ FAIL: Invalid role '{actual_role}' at position {first_non_system_idx + i}")
                continue
            
            if actual_role != expected_role:
                errors.append(f"❌ FAIL: Expected '{expected_role}' but got '{actual_role}' at position {first_non_system_idx + i}")
                print(f"❌ FAIL: Expected '{expected_role}' but got '{actual_role}' at position {first_non_system_idx + i}")
            
            # Toggle expected role
            expected_role = "assistant" if expected_role == "user" else "user"
        
        if not errors:
            print(f"✅ PASS: Proper alternation maintained across {len(remaining_messages)} messages")
    
    # Rule 5: Last message should be user (current message)
    if messages and messages[-1].get("role") != "user":
        errors.append("❌ FAIL: Last message should be 'user' (current message)")
        print(f"❌ FAIL: Last message is '{messages[-1].get('role')}', expected 'user'")
    else:
        print("✅ PASS: Last message is 'user' (current message)")
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total messages: {len(messages)}")
    print(f"System messages: {len(system_messages_at_start)}")
    print(f"User/Assistant messages: {len(remaining_messages)}")
    
    if errors:
        print(f"\n❌ VALIDATION FAILED: {len(errors)} error(s) found")
        for error in errors:
            print(f"   {error}")
        return False
    else:
        print("\n✅ VALIDATION PASSED: All alternation rules satisfied")
        return True


async def test_message_alternation():
    """Test message alternation with actual message processor."""
    print("\n" + "="*80)
    print("TESTING MESSAGE ALTERNATION")
    print("="*80)
    
    # Setup
    memory_manager = create_memory_manager(memory_type="vector")
    llm_client = create_llm_client(llm_client_type="openrouter")
    message_processor = MessageProcessor(
        bot=None,
        memory_manager=memory_manager,
        llm_client=llm_client
    )
    
    # Test message context
    test_user_id = "test_user_alternation"
    test_message = "What did we talk about last time?"
    
    message_context = MessageContext(
        user_id=test_user_id,
        content=test_message,
        channel_type="dm",
        platform="discord"
    )
    
    # Build conversation context
    print(f"\nBuilding conversation context for: '{test_message}'")
    
    # Get relevant memories (may be empty for test user)
    relevant_memories = await memory_manager.retrieve_relevant_memories(
        user_id=test_user_id,
        query=test_message,
        limit=10
    )
    
    print(f"Retrieved {len(relevant_memories)} memories")
    
    # Build context
    conversation_context = await message_processor._build_conversation_context(
        message_context=message_context,
        relevant_memories=relevant_memories
    )
    
    print(f"\nGenerated {len(conversation_context)} messages in context")
    
    # Print message sequence
    print("\nMESSAGE SEQUENCE:")
    print("-" * 80)
    for i, msg in enumerate(conversation_context):
        role = msg.get("role")
        content = msg.get("content", "")
        preview = content[:100] + "..." if len(content) > 100 else content
        print(f"{i+1}. [{role.upper()}] {preview}")
    
    # Validate alternation
    is_valid = await validate_message_alternation(conversation_context)
    
    return is_valid


if __name__ == "__main__":
    # Set required environment variables
    os.environ.setdefault("FASTEMBED_CACHE_PATH", "/tmp/fastembed_cache")
    os.environ.setdefault("QDRANT_HOST", "localhost")
    os.environ.setdefault("QDRANT_PORT", "6334")
    os.environ.setdefault("POSTGRES_HOST", "localhost")
    os.environ.setdefault("POSTGRES_PORT", "5433")
    os.environ.setdefault("DISCORD_BOT_NAME", "TestBot")
    
    # Run test
    result = asyncio.run(test_message_alternation())
    
    # Exit with appropriate code
    sys.exit(0 if result else 1)
