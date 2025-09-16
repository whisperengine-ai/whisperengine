"""
Conversation utilities for the Discord bot.
Manages conversation history with memory leak protection.
"""

import logging
from collections import OrderedDict

logger = logging.getLogger(__name__)


class ConversationHistoryManager:
    """Manages conversation history with memory leak protection"""

    def __init__(self, max_channels: int = 100, max_messages_per_channel: int = 20):
        self.max_channels = max_channels
        self.max_messages_per_channel = max_messages_per_channel
        self.channels = OrderedDict()
        logger.debug(
            f"ConversationHistoryManager initialized: max_channels={max_channels}, max_messages={max_messages_per_channel}"
        )

    def add_message(self, channel_id: str, message: dict):
        """Add a message to the conversation history with automatic cleanup"""
        # Remove oldest channel if we exceed limit
        if channel_id not in self.channels and len(self.channels) >= self.max_channels:
            oldest_channel = next(iter(self.channels))
            removed = self.channels.pop(oldest_channel)
            logger.debug(
                f"Removed conversation history for channel {oldest_channel} ({len(removed)} messages)"
            )

        # Initialize channel if needed
        if channel_id not in self.channels:
            self.channels[channel_id] = []

        # Add message
        self.channels[channel_id].append(message)

        # Trim messages if channel exceeds limit
        if len(self.channels[channel_id]) > self.max_messages_per_channel:
            removed_count = len(self.channels[channel_id]) - self.max_messages_per_channel
            self.channels[channel_id] = self.channels[channel_id][-self.max_messages_per_channel :]
            logger.debug(f"Trimmed {removed_count} old messages from channel {channel_id}")

        # Move to end (most recently used)
        self.channels.move_to_end(channel_id)

    def get_messages(self, channel_id: str) -> list:
        """Get messages for a channel"""
        return self.channels.get(channel_id, [])

    def clear_channel(self, channel_id: str):
        """Clear messages for a specific channel"""
        if channel_id in self.channels:
            message_count = len(self.channels[channel_id])
            del self.channels[channel_id]
            logger.debug(f"Cleared {message_count} messages from channel {channel_id}")

    def get_stats(self) -> dict:
        """Get memory usage statistics"""
        total_messages = sum(len(messages) for messages in self.channels.values())
        return {
            "channels": len(self.channels),
            "total_messages": total_messages,
            "avg_messages_per_channel": total_messages / len(self.channels) if self.channels else 0,
        }
