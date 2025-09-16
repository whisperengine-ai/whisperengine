#!/usr/bin/env python3
"""
Test for Conversation Cache Mixing Security Fix
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

    # Mock the history method to return async iterator
    class MockHistory:
        def __init__(self, messages=None):
            self.messages = messages or []

        def __aiter__(self):
            return self

        async def __anext__(self):
            if not self.messages:
                raise StopAsyncIteration
            return self.messages.pop(0)

    def mock_history(limit=50):
        # Return empty async iterator for now - we'll populate this in tests as needed
        return MockHistory([])

    mock_channel.history = mock_history
    return mock_channel


async def test_user_specific_filtering():
    """Test that user-specific filtering works correctly"""


    cache = HybridConversationCache()
    mock_channel = create_mock_channel(12345)

    # Create messages from different users in the same channel
    user_alice = 1001
    user_bob = 1002
    user_charlie = 1003
    bot_user = 9999

    messages = [
        create_mock_message(user_alice, "Hello, I'm Alice", message_id=1),
        create_mock_message(bot_user, "Hi Alice! How can I help you?", is_bot=True, message_id=2),
        create_mock_message(user_bob, "Hey bot, I'm Bob", message_id=3),
        create_mock_message(
            bot_user, "Hello Bob! What can I do for you?", is_bot=True, message_id=4
        ),
        create_mock_message(user_alice, "I want to know about the weather", message_id=5),
        create_mock_message(
            bot_user, "The weather today is sunny, Alice", is_bot=True, message_id=6
        ),
        create_mock_message(user_charlie, "Secret message from Charlie", message_id=7),
        create_mock_message(user_bob, "What's my name?", message_id=8),
        create_mock_message(bot_user, "Your name is Bob!", is_bot=True, message_id=9),
    ]

    # Add all messages to cache
    for msg in messages:
        cache.add_message(str(mock_channel.id), msg)


    # Test Alice's conversation context - should only see Alice + bot messages
    alice_context = await cache.get_user_conversation_context(mock_channel, user_alice, limit=10)

    for msg in alice_context:
        pass

    # Validate Alice's context
    alice_user_messages = [msg for msg in alice_context if msg.author.id == user_alice]
    alice_bot_messages = [msg for msg in alice_context if msg.author.bot]
    other_user_messages = [
        msg for msg in alice_context if not msg.author.bot and msg.author.id != user_alice
    ]

    assert (
        len(alice_user_messages) == 2
    ), f"Alice should see 2 of her own messages, got {len(alice_user_messages)}"
    assert (
        len(alice_bot_messages) >= 2
    ), f"Alice should see bot responses, got {len(alice_bot_messages)}"
    assert (
        len(other_user_messages) == 0
    ), f"Alice should NOT see other users' messages, got {len(other_user_messages)}"

    # Verify specific content is correct
    alice_contents = [msg.content for msg in alice_user_messages]
    assert "Hello, I'm Alice" in alice_contents, "Alice should see her first message"
    assert (
        "I want to know about the weather" in alice_contents
    ), "Alice should see her weather question"

    # Verify Alice does NOT see other users' secrets
    all_alice_content = " ".join([msg.content for msg in alice_context])
    assert (
        "Secret message from Charlie" not in all_alice_content
    ), "Alice should NOT see Charlie's secret"
    assert "Hey bot, I'm Bob" not in all_alice_content, "Alice should NOT see Bob's messages"


    # Test Bob's conversation context
    bob_context = await cache.get_user_conversation_context(mock_channel, user_bob, limit=10)

    for msg in bob_context:
        pass

    # Validate Bob's context
    bob_user_messages = [msg for msg in bob_context if msg.author.id == user_bob]
    other_user_messages_bob = [
        msg for msg in bob_context if not msg.author.bot and msg.author.id != user_bob
    ]

    assert (
        len(bob_user_messages) == 2
    ), f"Bob should see 2 of his own messages, got {len(bob_user_messages)}"
    assert (
        len(other_user_messages_bob) == 0
    ), f"Bob should NOT see other users' messages, got {len(other_user_messages_bob)}"

    # Verify Bob does NOT see other users' content
    all_bob_content = " ".join([msg.content for msg in bob_context])
    assert "Hello, I'm Alice" not in all_bob_content, "Bob should NOT see Alice's messages"
    assert (
        "Secret message from Charlie" not in all_bob_content
    ), "Bob should NOT see Charlie's secret"
    assert "weather" not in all_bob_content, "Bob should NOT see Alice's weather question"


    # Test Charlie's conversation context (should only see his own message)
    charlie_context = await cache.get_user_conversation_context(
        mock_channel, user_charlie, limit=10
    )

    for msg in charlie_context:
        pass

    # Validate Charlie's context
    charlie_user_messages = [msg for msg in charlie_context if msg.author.id == user_charlie]
    other_user_messages_charlie = [
        msg for msg in charlie_context if not msg.author.bot and msg.author.id != user_charlie
    ]

    assert (
        len(charlie_user_messages) == 1
    ), f"Charlie should see 1 of his own messages, got {len(charlie_user_messages)}"
    assert (
        len(other_user_messages_charlie) == 0
    ), f"Charlie should NOT see other users' messages, got {len(other_user_messages_charlie)}"

    # Verify Charlie's message content
    assert (
        charlie_user_messages[0].content == "Secret message from Charlie"
    ), "Charlie should see his secret message"

    # Verify Charlie does NOT see other users' content
    all_charlie_content = " ".join([msg.content for msg in charlie_context])
    assert "Alice" not in all_charlie_content, "Charlie should NOT see Alice's name or messages"
    assert "Bob" not in all_charlie_content, "Charlie should NOT see Bob's name or messages"




async def test_dm_security():
    """Test security in DM context where cache mixing is still possible"""


    cache = HybridConversationCache()

    # Simulate DM channels (each user has their own channel ID with bot)
    alice_dm_channel = create_mock_channel(20001)  # Alice's DM with bot
    bob_dm_channel = create_mock_channel(20002)  # Bob's DM with bot

    user_alice = 1001
    user_bob = 1002
    bot_user = 9999

    # Add messages to Alice's DM
    alice_messages = [
        create_mock_message(user_alice, "Hi bot, this is Alice's secret plan", message_id=101),
        create_mock_message(
            bot_user, "Tell me more about your plan, Alice", is_bot=True, message_id=102
        ),
        create_mock_message(
            user_alice, "I want to surprise my friend with a party", message_id=103
        ),
        create_mock_message(
            bot_user, "That sounds wonderful! Need help planning?", is_bot=True, message_id=104
        ),
    ]

    # Add messages to Bob's DM
    bob_messages = [
        create_mock_message(user_bob, "Hey bot, I need help with work", message_id=201),
        create_mock_message(
            bot_user, "What kind of work help do you need, Bob?", is_bot=True, message_id=202
        ),
        create_mock_message(
            user_bob, "I'm struggling with my presentation tomorrow", message_id=203
        ),
    ]

    # Add Alice's messages to her DM channel cache
    for msg in alice_messages:
        cache.add_message(str(alice_dm_channel.id), msg)

    # Add Bob's messages to his DM channel cache
    for msg in bob_messages:
        cache.add_message(str(bob_dm_channel.id), msg)


    # Test Alice's DM context - should only see Alice + bot from her DM
    alice_dm_context = await cache.get_user_conversation_context(
        alice_dm_channel, user_alice, limit=10
    )

    for msg in alice_dm_context:
        pass

    # Validate Alice's DM context
    alice_dm_content = " ".join([msg.content for msg in alice_dm_context])
    assert "secret plan" in alice_dm_content, "Alice should see her secret plan message"
    assert "surprise my friend" in alice_dm_content, "Alice should see her party planning message"
    assert "work" not in alice_dm_content, "Alice should NOT see Bob's work messages"
    assert "presentation" not in alice_dm_content, "Alice should NOT see Bob's presentation message"

    # Test Bob's DM context - should only see Bob + bot from his DM
    bob_dm_context = await cache.get_user_conversation_context(bob_dm_channel, user_bob, limit=10)

    for msg in bob_dm_context:
        pass

    # Validate Bob's DM context
    bob_dm_content = " ".join([msg.content for msg in bob_dm_context])
    assert "work" in bob_dm_content, "Bob should see his work message"
    assert "presentation" in bob_dm_content, "Bob should see his presentation message"
    assert "secret plan" not in bob_dm_content, "Bob should NOT see Alice's secret plan"
    assert "surprise" not in bob_dm_content, "Bob should NOT see Alice's party planning"



async def test_bot_response_filtering():
    """Test that bot responses are correctly included and attributed"""


    cache = HybridConversationCache()
    mock_channel = create_mock_channel(30001)

    user_alice = 1001
    user_bob = 1002
    bot_user = 9999

    # Create a conversation where bot responds to different users
    messages = [
        create_mock_message(user_alice, "What's 2+2?", message_id=301),
        create_mock_message(bot_user, "2+2 equals 4, Alice!", is_bot=True, message_id=302),
        create_mock_message(user_bob, "What's the capital of France?", message_id=303),
        create_mock_message(
            bot_user, "The capital of France is Paris, Bob!", is_bot=True, message_id=304
        ),
        create_mock_message(user_alice, "Thanks for the math help!", message_id=305),
        create_mock_message(
            bot_user, "You're welcome, Alice! Need more help?", is_bot=True, message_id=306
        ),
    ]

    # Add all messages to cache
    for msg in messages:
        cache.add_message(str(mock_channel.id), msg)


    # Test Alice's context - should see her messages + all bot responses
    alice_context = await cache.get_user_conversation_context(mock_channel, user_alice, limit=10)

    for msg in alice_context:
        pass

    # Validate Alice sees her conversation with the bot
    alice_content = " ".join([msg.content for msg in alice_context])
    assert "2+2" in alice_content, "Alice should see her math question"
    assert "2+2 equals 4, Alice!" in alice_content, "Alice should see bot's math response"
    assert "Thanks for the math help!" in alice_content, "Alice should see her thank you"
    assert "You're welcome, Alice!" in alice_content, "Alice should see bot's welcome response"

    # Alice should NOT see Bob's conversation parts
    assert "capital of France" not in alice_content, "Alice should NOT see Bob's geography question"
    assert "Paris, Bob!" not in alice_content, "Alice should NOT see bot's response to Bob"

    # Test Bob's context - should see his messages + all bot responses
    bob_context = await cache.get_user_conversation_context(mock_channel, user_bob, limit=10)

    for msg in bob_context:
        pass

    # Validate Bob sees his conversation with the bot
    bob_content = " ".join([msg.content for msg in bob_context])
    assert "capital of France" in bob_content, "Bob should see his geography question"
    assert "Paris, Bob!" in bob_content, "Bob should see bot's geography response"

    # Bob should NOT see Alice's conversation parts
    assert "2+2" not in bob_content, "Bob should NOT see Alice's math question"
    assert "Thanks for the math help!" not in bob_content, "Bob should NOT see Alice's thank you"

    # However, there's an issue: Bob might see ALL bot responses, not just ones to him
    # This is a design decision - we could further filter bot responses to only include
    # those that are contextually relevant to the current user



async def test_performance_and_limits():
    """Test that the security filtering doesn't cause performance issues"""


    cache = HybridConversationCache()
    mock_channel = create_mock_channel(40001)

    user_alice = 1001
    bot_user = 9999

    # Create a large number of messages to test performance
    messages = []
    for i in range(100):  # 100 messages
        if i % 2 == 0:
            messages.append(
                create_mock_message(user_alice, f"Alice message {i}", message_id=1000 + i)
            )
        else:
            messages.append(
                create_mock_message(bot_user, f"Bot response {i}", is_bot=True, message_id=1000 + i)
            )

    # Add all messages to cache
    start_time = time.time()
    for msg in messages:
        cache.add_message(str(mock_channel.id), msg)
    time.time() - start_time


    # Test retrieval performance
    start_time = time.time()
    alice_context = await cache.get_user_conversation_context(mock_channel, user_alice, limit=10)
    retrieval_time = time.time() - start_time


    # Validate we get the expected limit
    assert len(alice_context) == 10, f"Should get exactly 10 messages, got {len(alice_context)}"

    # Validate performance is reasonable (should be very fast for this test)
    assert retrieval_time < 1.0, f"Context retrieval took too long: {retrieval_time:.3f}s"



async def test_edge_cases():
    """Test edge cases like empty channels, no bot messages, etc."""


    cache = HybridConversationCache()

    # Test 1: Empty channel
    empty_channel = create_mock_channel(50001)
    user_alice = 1001

    empty_context = await cache.get_user_conversation_context(empty_channel, user_alice, limit=5)
    assert len(empty_context) == 0, "Empty channel should return empty context"

    # Test 2: Channel with only other users' messages
    other_users_channel = create_mock_channel(50002)
    user_bob = 1002
    user_charlie = 1003

    # Add messages from other users only
    other_messages = [
        create_mock_message(user_bob, "Bob's message", message_id=501),
        create_mock_message(user_charlie, "Charlie's message", message_id=502),
    ]

    for msg in other_messages:
        cache.add_message(str(other_users_channel.id), msg)

    alice_context_empty = await cache.get_user_conversation_context(
        other_users_channel, user_alice, limit=5
    )
    assert len(alice_context_empty) == 0, "Alice should see no messages from other users"

    # Test 3: Channel with only bot messages (no user messages)
    bot_only_channel = create_mock_channel(50003)
    bot_user = 9999

    bot_only_messages = [
        create_mock_message(bot_user, "Bot announcement 1", is_bot=True, message_id=601),
        create_mock_message(bot_user, "Bot announcement 2", is_bot=True, message_id=602),
    ]

    for msg in bot_only_messages:
        cache.add_message(str(bot_only_channel.id), msg)

    alice_bot_context = await cache.get_user_conversation_context(
        bot_only_channel, user_alice, limit=5
    )
    # Alice should still see bot messages even if she hasn't sent any
    assert (
        len(alice_bot_context) == 2
    ), f"Alice should see bot messages, got {len(alice_bot_context)}"



if __name__ == "__main__":

    async def run_all_tests():
        try:
            await test_user_specific_filtering()
            await test_dm_security()
            await test_bot_response_filtering()
            await test_performance_and_limits()
            await test_edge_cases()





        except Exception:
            import traceback

            traceback.print_exc()
            sys.exit(1)

    # Run the tests
    asyncio.run(run_all_tests())
