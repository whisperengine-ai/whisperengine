#!/usr/bin/env python3
"""
Integration test to verify the conversation cache security fix doesn't break bot functionality
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
from unittest.mock import Mock, patch

from conversation_cache import HybridConversationCache


def create_mock_message(user_id: int, content: str, is_bot: bool = False, message_id=None):
    """Create a mock Discord message"""
    mock_message = Mock()
    mock_message.id = message_id or (user_id * 1000)
    mock_message.content = content
    mock_message.author = Mock()
    mock_message.author.id = user_id
    mock_message.author.bot = is_bot
    mock_message.webhook_id = None
    return mock_message


async def test_integration_functionality():
    """Test that bot functionality still works with security fix"""


    # Test that get_user_conversation_context still provides good conversation flow
    cache = HybridConversationCache()
    mock_channel = Mock()
    mock_channel.id = 12345

    user_alice = 1001
    bot_user = 9999

    # Create a realistic conversation
    conversation = [
        create_mock_message(user_alice, "Hi bot!", message_id=1),
        create_mock_message(
            bot_user, "Hello! How can I help you today?", is_bot=True, message_id=2
        ),
        create_mock_message(user_alice, "I'm working on a Python project", message_id=3),
        create_mock_message(
            bot_user, "That's great! What kind of Python project?", is_bot=True, message_id=4
        ),
        create_mock_message(user_alice, "A web scraper for news articles", message_id=5),
        create_mock_message(
            bot_user,
            "Interesting! Are you using any specific libraries like BeautifulSoup or Scrapy?",
            is_bot=True,
            message_id=6,
        ),
    ]

    # Mock the base method
    async def mock_get_conversation_context(channel, limit=5, exclude_message_id=None):
        result = conversation.copy()
        if exclude_message_id:
            result = [msg for msg in result if msg.id != exclude_message_id]
        return result

    with patch.object(cache, "get_conversation_context", mock_get_conversation_context):
        # Test that Alice gets good conversation context
        alice_context = await cache.get_user_conversation_context(
            mock_channel, user_alice, limit=10
        )

        for _i, _msg in enumerate(alice_context):
            pass

        # Verify the context maintains good conversation flow
        assert len(alice_context) == 6, f"Should get full conversation, got {len(alice_context)}"

        # Verify messages are in chronological order
        assert alice_context[0].content == "Hi bot!", "First message should be Alice's greeting"
        assert alice_context[-1].content.startswith(
            "Interesting!"
        ), "Last message should be bot's latest response"

        # Verify alternating conversation pattern is preserved
        assert alice_context[0].author.id == user_alice, "Should start with user"
        assert alice_context[1].author.bot, "Should be followed by bot"
        assert alice_context[2].author.id == user_alice, "Should continue with user"


        # Test with limit to ensure it respects limits
        limited_context = await cache.get_user_conversation_context(
            mock_channel, user_alice, limit=3
        )
        assert len(limited_context) == 3, f"Should respect limit of 3, got {len(limited_context)}"

        # Should get the most recent messages
        assert "web scraper" in limited_context[-2].content, "Should include recent user message"
        assert "BeautifulSoup" in limited_context[-1].content, "Should include latest bot response"


        # Test exclude_message_id functionality
        excluded_context = await cache.get_user_conversation_context(
            mock_channel, user_alice, limit=10, exclude_message_id=5
        )
        excluded_ids = [msg.id for msg in excluded_context]
        assert 5 not in excluded_ids, "Should exclude message with ID 5"
        assert len(excluded_context) == 5, "Should have 5 messages after excluding 1"




async def test_performance_impact():
    """Test that the security fix doesn't significantly impact performance"""


    import time

    cache = HybridConversationCache()
    mock_channel = Mock()
    mock_channel.id = 99999

    # Create a large conversation with mixed users
    large_conversation = []
    for i in range(200):  # 200 messages
        if i % 3 == 0:
            large_conversation.append(create_mock_message(1001, f"Alice message {i}", message_id=i))
        elif i % 3 == 1:
            large_conversation.append(create_mock_message(1002, f"Bob message {i}", message_id=i))
        else:
            large_conversation.append(
                create_mock_message(9999, f"Bot response {i}", is_bot=True, message_id=i)
            )

    async def mock_get_conversation_context(channel, limit=5, exclude_message_id=None):
        return large_conversation

    with patch.object(cache, "get_conversation_context", mock_get_conversation_context):
        # Time the filtering operation
        start_time = time.time()

        # Run multiple filtering operations to get average
        for _ in range(10):
            alice_context = await cache.get_user_conversation_context(mock_channel, 1001, limit=10)

        end_time = time.time()
        avg_time = (end_time - start_time) / 10


        # Performance should be reasonable (under 0.1 seconds for this test)
        assert avg_time < 0.1, f"Filtering too slow: {avg_time:.4f}s"

        # Verify filtering still works correctly with large dataset
        alice_user_msgs = [msg for msg in alice_context if msg.author.id == 1001]
        other_user_msgs = [
            msg for msg in alice_context if not msg.author.bot and msg.author.id != 1001
        ]

        assert len(alice_user_msgs) > 0, "Should find Alice's messages"
        assert len(other_user_msgs) == 0, "Should not include other users' messages"




if __name__ == "__main__":

    async def run_tests():
        try:
            await test_integration_functionality()
            await test_performance_impact()





        except Exception:
            import traceback

            traceback.print_exc()
            sys.exit(1)

    asyncio.run(run_tests())
