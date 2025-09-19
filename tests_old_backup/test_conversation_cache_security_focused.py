#!/usr/bin/env python3
"""
Focused Test for Conversation Cache Mixing Security Fix
Tests the fix for CVSS 7.2 vulnerability - Conversation Cache Mixing
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
import time
from unittest.mock import Mock

from conversation_cache import HybridConversationCache


def create_mock_message(user_id: int, content: str, is_bot: bool = False, message_id=None):
    """Create a mock Discord message"""
    mock_message = Mock()
    mock_message.id = message_id or int(time.time() * 1000) + user_id  # Unique ID
    mock_message.content = content
    mock_message.author = Mock()
    mock_message.author.id = user_id
    mock_message.author.bot = is_bot
    mock_message.webhook_id = None
    return mock_message


def create_mock_channel(channel_id: int):
    """Create a mock Discord channel"""
    mock_channel = Mock()
    mock_channel.id = channel_id
    return mock_channel


async def test_cache_user_filtering():
    """Test the core security fix: user-specific filtering in conversation cache"""

    cache = HybridConversationCache()
    mock_channel = create_mock_channel(12345)

    # Create messages from different users in the same channel
    user_alice = 1001
    user_bob = 1002
    bot_user = 9999

    messages = [
        create_mock_message(user_alice, "Hello, I'm Alice", message_id=1),
        create_mock_message(bot_user, "Hi Alice! How can I help you?", is_bot=True, message_id=2),
        create_mock_message(user_bob, "Hey bot, I'm Bob with secret info", message_id=3),
        create_mock_message(
            bot_user, "Hello Bob! What can I do for you?", is_bot=True, message_id=4
        ),
        create_mock_message(user_alice, "I want to plan a surprise party", message_id=5),
        create_mock_message(bot_user, "That sounds fun, Alice!", is_bot=True, message_id=6),
    ]

    # Add all messages to cache (this simulates the cache being populated)
    for msg in messages:
        cache.add_message(str(mock_channel.id), msg)

    # Key test: Check that Alice only sees her own messages + bot responses
    alice_context = await cache.get_user_conversation_context(mock_channel, user_alice, limit=10)

    for msg in alice_context:
        pass

    # Verify security: Alice should NOT see Bob's messages
    alice_content = " ".join([msg.content for msg in alice_context])

    # Alice should see her own content
    assert "Hello, I'm Alice" in alice_content, "Alice should see her own messages"
    assert "surprise party" in alice_content, "Alice should see her party planning"

    # Alice should see bot responses
    assert "Hi Alice!" in alice_content, "Alice should see bot responses to her"

    # CRITICAL: Alice should NOT see Bob's secret information
    assert (
        "secret info" not in alice_content
    ), "🚨 SECURITY BREACH: Alice should NOT see Bob's secret info!"
    assert (
        "Hey bot, I'm Bob" not in alice_content
    ), "🚨 SECURITY BREACH: Alice should NOT see Bob's messages!"

    # Test Bob's context as well
    bob_context = await cache.get_user_conversation_context(mock_channel, user_bob, limit=10)

    for msg in bob_context:
        pass

    bob_content = " ".join([msg.content for msg in bob_context])

    # Bob should see his own content
    assert "secret info" in bob_content, "Bob should see his own secret info"
    assert "Hey bot, I'm Bob" in bob_content, "Bob should see his own messages"

    # CRITICAL: Bob should NOT see Alice's information
    assert (
        "surprise party" not in bob_content
    ), "🚨 SECURITY BREACH: Bob should NOT see Alice's party plans!"
    assert (
        "Hello, I'm Alice" not in bob_content
    ), "🚨 SECURITY BREACH: Bob should NOT see Alice's messages!"


async def test_dm_isolation():
    """Test that DM conversations are properly isolated"""

    cache = HybridConversationCache()

    # Different DM channels
    alice_dm = create_mock_channel(20001)
    bob_dm = create_mock_channel(20002)

    user_alice = 1001
    user_bob = 1002
    bot_user = 9999

    # Alice's private DM conversation
    alice_messages = [
        create_mock_message(user_alice, "I'm having relationship problems", message_id=101),
        create_mock_message(
            bot_user, "I'm sorry to hear that. Want to talk about it?", is_bot=True, message_id=102
        ),
        create_mock_message(user_alice, "My partner doesn't know about my anxiety", message_id=103),
    ]

    # Bob's private DM conversation
    bob_messages = [
        create_mock_message(user_bob, "I got fired from my job today", message_id=201),
        create_mock_message(
            bot_user,
            "That must be really difficult. How are you feeling?",
            is_bot=True,
            message_id=202,
        ),
    ]

    # Add messages to respective DM caches
    for msg in alice_messages:
        cache.add_message(str(alice_dm.id), msg)

    for msg in bob_messages:
        cache.add_message(str(bob_dm.id), msg)

    # Test Alice's DM context
    alice_dm_context = await cache.get_user_conversation_context(alice_dm, user_alice, limit=10)
    alice_dm_content = " ".join([msg.content for msg in alice_dm_context])

    # Alice should see her private information
    assert "relationship problems" in alice_dm_content, "Alice should see her own DM content"
    assert "anxiety" in alice_dm_content, "Alice should see her private anxiety discussion"

    # Alice should NOT see Bob's private information
    assert "fired" not in alice_dm_content, "🚨 Alice should NOT see Bob's job loss!"
    assert "job today" not in alice_dm_content, "🚨 Alice should NOT see Bob's private DM!"

    # Test Bob's DM context
    bob_dm_context = await cache.get_user_conversation_context(bob_dm, user_bob, limit=10)
    bob_dm_content = " ".join([msg.content for msg in bob_dm_context])

    # Bob should see his private information
    assert "fired" in bob_dm_content, "Bob should see his own DM content"
    assert "job today" in bob_dm_content, "Bob should see his private job discussion"

    # Bob should NOT see Alice's private information
    assert (
        "relationship problems" not in bob_dm_content
    ), "🚨 Bob should NOT see Alice's relationship issues!"
    assert "anxiety" not in bob_dm_content, "🚨 Bob should NOT see Alice's private DM!"


async def test_bot_integration():
    """Test that the bot integration fix works correctly"""

    # This test verifies that the bot code changes work
    # We can't directly test the bot here, but we can verify the cache behavior
    # that the bot relies on

    cache = HybridConversationCache()
    mock_channel = create_mock_channel(30001)

    user_alice = 1001
    user_bob = 1002
    bot_user = 9999

    # Simulate a busy channel with multiple users
    busy_channel_messages = [
        create_mock_message(user_alice, "Hi bot!", message_id=1),
        create_mock_message(
            user_bob, "Hey everyone, check out this link: malicious-site.com", message_id=2
        ),
        create_mock_message(user_alice, "Can you help me with my homework?", message_id=3),
        create_mock_message(bot_user, "Sure Alice! What subject?", is_bot=True, message_id=4),
        create_mock_message(user_bob, "I need help hacking into my school system", message_id=5),
        create_mock_message(user_alice, "It's math homework about derivatives", message_id=6),
        create_mock_message(
            bot_user, "Great! Let's start with basic derivatives", is_bot=True, message_id=7
        ),
    ]

    # Add all messages to cache
    for msg in busy_channel_messages:
        cache.add_message(str(mock_channel.id), msg)

    # When Alice sends a message, the bot should only see Alice's conversation context
    alice_safe_context = await cache.get_user_conversation_context(
        mock_channel, user_alice, limit=10
    )
    alice_safe_content = " ".join([msg.content for msg in alice_safe_context])

    # Alice should see her legitimate conversation
    assert "homework" in alice_safe_content, "Alice should see her homework discussion"
    assert "derivatives" in alice_safe_content, "Alice should see her math topic"

    # CRITICAL: Alice should NOT see Bob's problematic content
    assert (
        "malicious-site.com" not in alice_safe_content
    ), "🚨 Alice should NOT see Bob's malicious link!"
    assert "hacking" not in alice_safe_content, "🚨 Alice should NOT see Bob's hacking request!"

    # When Bob sends a message, his problematic history should be contained to him
    bob_context = await cache.get_user_conversation_context(mock_channel, user_bob, limit=10)
    bob_content = " ".join([msg.content for msg in bob_context])

    # Bob should see his own messages (even problematic ones)
    assert "malicious-site.com" in bob_content, "Bob should see his own messages"
    assert "hacking" in bob_content, "Bob should see his own messages"

    # Bob should NOT see Alice's innocent homework discussion
    assert "derivatives" not in bob_content, "Bob should NOT see Alice's homework"
    assert "math homework" not in bob_content, "Bob should NOT see Alice's study session"


if __name__ == "__main__":

    async def run_tests():
        try:
            await test_cache_user_filtering()
            await test_dm_isolation()
            await test_bot_integration()

        except Exception:
            import traceback

            traceback.print_exc()
            sys.exit(1)

    asyncio.run(run_tests())
