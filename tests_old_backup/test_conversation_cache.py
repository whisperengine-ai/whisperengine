"""
Test script for the Hybrid Conversation Cache
Verifies cache functionality without needing to run the full Discord bot.
"""

import asyncio
import time
from unittest.mock import Mock

from conversation_cache import HybridConversationCache


class MockMessage:
    """Mock Discord message for testing"""

    def __init__(self, content, author_id=123456789, message_id=None):
        self.content = content
        self.author = Mock()
        self.author.id = author_id
        self.id = message_id or int(time.time() * 1000)


class MockChannel:
    """Mock Discord channel for testing"""

    def __init__(self, channel_id=987654321):
        self.id = channel_id
        self._messages = []

    def add_mock_message(self, message):
        """Add a message to the mock channel history"""
        self._messages.append(message)

    async def history(self, limit=None):
        """Mock async generator for message history"""
        messages = self._messages[-limit:] if limit else self._messages
        for msg in reversed(messages):  # Discord returns newest first
            yield msg


import pytest


@pytest.mark.asyncio
async def test_cache_basic_functionality():
    """Test basic cache operations"""

    # Initialize cache with short timeout for testing
    cache = HybridConversationCache(
        cache_timeout_minutes=1, bootstrap_limit=5, max_local_messages=10  # 1 minute for testing
    )

    # Create mock objects
    channel = MockChannel(channel_id=123)

    # Add some messages to mock channel history
    for i in range(8):
        msg = MockMessage(f"Test message {i+1}", author_id=111)
        channel.add_mock_message(msg)

    # Test 1: First call should bootstrap from Discord
    messages = await cache.get_conversation_context(channel, limit=3)
    assert len(messages) == 3, f"Expected 3 messages, got {len(messages)}"

    # Test 2: Add new message and verify it's cached
    new_msg = MockMessage("New message", author_id=222)
    cache.add_message(str(channel.id), new_msg)

    messages = await cache.get_conversation_context(channel, limit=4)
    assert len(messages) == 4, f"Expected 4 messages, got {len(messages)}"
    assert messages[-1].content == "New message", "New message not found at end"

    # Test 3: Cache hit (should not call Discord API again)
    start_time = time.time()
    messages = await cache.get_conversation_context(channel, limit=3)
    elapsed = time.time() - start_time
    assert elapsed < 0.01, "Cache hit took too long - might be calling Discord API"

    # Test 4: Cache expiration
    await asyncio.sleep(7)  # Wait for cache to expire (timeout is 6 seconds)

    # This should trigger a new bootstrap
    messages = await cache.get_conversation_context(channel, limit=3)

    # Test 5: Statistics
    stats = cache.get_cache_stats()
    assert stats["cached_channels"] == 1, "Should have 1 cached channel"


if __name__ == "__main__":
    asyncio.run(test_cache_basic_functionality())
