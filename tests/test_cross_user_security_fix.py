#!/usr/bin/env python3
"""
Test script to verify the cross-user message contamination security fix.
This test simulates the vulnerability scenario described in the security assessment.
"""

import asyncio
import sys
from collections import deque
from unittest.mock import Mock

import discord

# Import the conversation cache
from conversation_cache import HybridConversationCache


async def test_user_specific_filtering():
    """Test that user-specific conversation context properly filters messages by user ID."""

    # Create mock Discord messages from different users
    def create_mock_message(
        user_id: int, content: str, message_id: int = None, is_bot: bool = False
    ):
        msg = Mock(spec=discord.Message)
        msg.id = message_id or hash(content) % 100000
        msg.content = content
        msg.author = Mock()
        msg.author.id = user_id
        msg.author.bot = is_bot
        return msg

    # Create test messages simulating the vulnerability scenario
    user_alice = 123456789  # Alice's Discord ID
    user_bob = 987654321  # Bob's Discord ID
    user_charlie = 555666777  # Charlie's Discord ID
    bot_user = 111111111  # Bot's Discord ID

    # Simulate a channel with mixed messages from multiple users
    test_messages = [
        create_mock_message(user_alice, "Hi bot, what health conditions do I have?", 1001),
        create_mock_message(user_bob, "I have diabetes and take insulin daily", 1002),
        create_mock_message(user_charlie, "My depression medication isn't working well", 1003),
        create_mock_message(
            bot_user, "I don't have any previous health information about you.", 1004, is_bot=True
        ),
        create_mock_message(user_alice, "@bot remind me what I told you about my health", 1005),
        create_mock_message(user_bob, "Also I have high blood pressure", 1006),
        create_mock_message(
            bot_user,
            "Based on our conversation, I don't see any health information you've shared.",
            1007,
            is_bot=True,
        ),
    ]

    # Create mock channel
    mock_channel = Mock()
    mock_channel.id = 999888777

    # Create conversation cache and manually populate it
    cache = HybridConversationCache()
    channel_id = str(mock_channel.id)

    # Manually populate cache to simulate real usage
    with cache._cache_lock:
        cache.conversations[channel_id] = {
            "messages": deque(test_messages, maxlen=50),
            "last_bootstrap": 999999999,  # High timestamp to avoid re-bootstrap
        }

    # Test 1: Get messages using OLD vulnerable method (simulated)
    all_messages = await cache.get_conversation_context(mock_channel, limit=10)
    for _msg in all_messages[-5:]:  # Show last 5
        pass

    # Test 2: Get messages using NEW secure method
    alice_messages = await cache.get_user_conversation_context(mock_channel, user_alice, limit=10)
    for _msg in alice_messages:
        pass

    # Test 3: Verify Bob gets only his messages
    bob_messages = await cache.get_user_conversation_context(mock_channel, user_bob, limit=10)
    for _msg in bob_messages:
        pass

    # Test 4: Verify Charlie gets only his messages
    charlie_messages = await cache.get_user_conversation_context(
        mock_channel, user_charlie, limit=10
    )
    for _msg in charlie_messages:
        pass

    # Verification tests

    # Test that Alice's messages don't contain Bob's or Charlie's content
    alice_content = " ".join([msg.content for msg in alice_messages if not msg.author.bot])

    if "diabetes" in alice_content.lower() or "insulin" in alice_content.lower():
        return False
    else:
        pass

    if "depression" in alice_content.lower() or "medication" in alice_content.lower():
        return False
    else:
        pass

    # Test that Bob's messages don't contain Alice's or Charlie's content
    bob_content = " ".join([msg.content for msg in bob_messages if not msg.author.bot])

    if "what health conditions do I have" in bob_content.lower():
        return False
    else:
        pass

    if "depression" in bob_content.lower():
        return False
    else:
        pass

    # Test that Charlie's messages don't contain Alice's or Bob's content
    charlie_content = " ".join([msg.content for msg in charlie_messages if not msg.author.bot])

    if "diabetes" in charlie_content.lower() or "insulin" in charlie_content.lower():
        return False
    else:
        pass

    if "what health conditions do I have" in charlie_content.lower():
        return False
    else:
        pass

    return True


async def main():
    """Run the security fix verification test."""
    try:
        success = await test_user_specific_filtering()
        if success:
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception:
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
