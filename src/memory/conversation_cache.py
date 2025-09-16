"""
Hybrid Conversation Cache for Discord Bot
Reduces Discord API calls by caching recent messages locally with smart refresh logic.
Thread-safe implementation for concurrent user operations.
"""

import time
import logging
import asyncio
import threading
from collections import deque
from typing import Dict, List, Optional
import discord

logger = logging.getLogger(__name__)


class HybridConversationCache:
    """
    Smart conversation cache that minimizes Discord API calls while maintaining accuracy.

    Features:
    - Event-driven message caching (add messages as they arrive)
    - Time-based cache expiration for stale data
    - Bootstrap from Discord API when needed
    - Configurable limits and timeouts
    """

    def __init__(self, cache_timeout_minutes=15, bootstrap_limit=20, max_local_messages=50):
        self.conversations = {}  # channel_id -> {'messages': deque, 'last_bootstrap': timestamp}
        self.cache_timeout = float(cache_timeout_minutes) * 60  # Convert to seconds
        self.bootstrap_limit = bootstrap_limit
        self.max_local_messages = max_local_messages

        # Thread safety for concurrent users
        self._cache_lock = threading.RLock()  # Re-entrant lock for nested operations
        self._bootstrap_locks = {}  # Per-channel bootstrap locks to prevent concurrent API calls
        self._bootstrap_lock_manager = threading.Lock()  # Lock for managing bootstrap locks

        logger.info(
            f"HybridConversationCache initialized: timeout={cache_timeout_minutes}min, "
            f"bootstrap_limit={bootstrap_limit}, max_local={max_local_messages}"
        )

    async def get_conversation_context(
        self, channel, limit=5, exclude_message_id=None
    ) -> List[discord.Message]:
        """
        Get recent conversation context with minimal API calls.
        Thread-safe for concurrent users.

        Args:
            channel: Discord channel object
            limit: Number of recent messages to return
            exclude_message_id: Message ID to exclude from context (usually the current message)

        Returns:
            List of recent Discord messages (most recent last)
        """
        channel_id = str(channel.id)
        now = time.time()

        # Thread-safe bootstrap check and execution
        bootstrap_lock = self._get_bootstrap_lock(channel_id)

        async with asyncio.Lock():  # Prevent multiple async calls for same channel
            # Check if we need to bootstrap or refresh from Discord
            needs_bootstrap = self._needs_bootstrap(channel_id, limit, now)

            if needs_bootstrap:
                # Use threading lock to prevent multiple concurrent bootstraps
                with bootstrap_lock:
                    # Double-check after acquiring lock (another thread might have bootstrapped)
                    if self._needs_bootstrap(channel_id, limit, now):
                        logger.debug(f"Bootstrapping conversation cache for channel {channel_id}")
                        await self._bootstrap_conversation(channel_id, channel)

        # Thread-safe message retrieval
        with self._cache_lock:
            if channel_id in self.conversations and self.conversations[channel_id]["messages"]:
                messages = list(self.conversations[channel_id]["messages"])

                # Filter out the excluded message if specified
                if exclude_message_id:
                    messages = [msg for msg in messages if msg.id != exclude_message_id]

                return messages[-limit:] if len(messages) >= limit else messages

        # Fallback: Pull directly from Discord history if cache is still empty
        logger.warning(
            f"No cached messages for channel {channel_id} after bootstrap attempt - falling back to Discord history"
        )
        try:
            # Direct Discord API call as final fallback
            messages = []
            async for msg in channel.history(limit=limit):
                messages.append(msg)

            # Filter out excluded message if specified
            if exclude_message_id:
                messages = [msg for msg in messages if msg.id != exclude_message_id]

            # Discord history returns newest first, we want to return most recent messages
            # in chronological order (oldest first)
            recent_messages = messages[:limit]  # Take the most recent N messages
            recent_messages.reverse()  # Put them in chronological order (oldest first)
            return recent_messages
        except Exception as e:
            logger.error(f"Failed to fetch Discord history for channel {channel_id}: {e}")
            return []

    async def get_user_conversation_context(
        self, channel, user_id: int, limit=5, exclude_message_id=None
    ) -> List[discord.Message]:
        """
        SECURITY ENHANCEMENT: Get conversation context filtered by specific user ID to prevent cross-user contamination.

        This method ensures that only messages from the specified user and bot responses are included,
        preventing privacy breaches where User A could see User B's messages in the same channel.

        Args:
            channel: Discord channel object
            user_id: Discord user ID to filter messages for
            limit: Number of recent relevant messages to return
            exclude_message_id: Message ID to exclude from context (usually the current message)

        Returns:
            List of recent Discord messages from the specified user and bot responses (most recent last)
        """
        # First get all recent messages using existing method
        all_messages = await self.get_conversation_context(
            channel, limit=limit * 3, exclude_message_id=exclude_message_id
        )

        # Filter for current user and bot responses only
        user_specific_messages = []
        bot_user_id = None

        # Identify bot user ID from messages (bot messages have is_bot=True or webhook_id)
        for msg in all_messages:
            if msg.author.bot or (hasattr(msg, "webhook_id") and msg.webhook_id):
                bot_user_id = msg.author.id
                break

        for msg in all_messages:
            # Include messages from the specified user
            if msg.author.id == user_id:
                user_specific_messages.append(msg)
                logger.debug(f"Including user message from {user_id}: {msg.content[:50]}...")
            # Include bot responses (but we could further refine this to only include responses to this user)
            elif msg.author.bot or (bot_user_id and msg.author.id == bot_user_id):
                user_specific_messages.append(msg)
                logger.debug(f"Including bot response: {msg.content[:50]}...")
            else:
                # Skip messages from other users to prevent contamination
                logger.debug(
                    f"Filtering out message from user {msg.author.id} (target user: {user_id})"
                )

        # Return the most recent messages up to the limit
        return (
            user_specific_messages[-limit:]
            if len(user_specific_messages) >= limit
            else user_specific_messages
        )

    def add_message(self, channel_id: str, message: discord.Message):
        """
        Add a new message to the local cache (called from on_message event).
        Thread-safe for concurrent users.

        Args:
            channel_id: String channel ID
            message: Discord message object
        """
        channel_id = str(channel_id)  # Ensure string format

        with self._cache_lock:
            if channel_id in self.conversations:
                self.conversations[channel_id]["messages"].append(message)
                logger.debug(
                    f"Added message to cache for channel {channel_id} "
                    f"(cache size: {len(self.conversations[channel_id]['messages'])})"
                )
            else:
                # First message for this channel - initialize cache
                logger.debug(f"Initializing message cache for new channel {channel_id}")
                self.conversations[channel_id] = {
                    "messages": deque([message], maxlen=self.max_local_messages),
                    "last_bootstrap": time.time(),  # Mark as recently initialized
                }

    def clear_channel_cache(self, channel_id: str):
        """Clear cache for a specific channel. Thread-safe."""
        channel_id = str(channel_id)
        with self._cache_lock:
            if channel_id in self.conversations:
                del self.conversations[channel_id]
                logger.debug(f"Cleared cache for channel {channel_id}")

            # Also clean up bootstrap lock if it exists
            with self._bootstrap_lock_manager:
                if channel_id in self._bootstrap_locks:
                    del self._bootstrap_locks[channel_id]

    def get_cache_stats(self) -> Dict:
        """Get statistics about cache usage. Thread-safe."""
        with self._cache_lock:
            total_messages = sum(len(conv["messages"]) for conv in self.conversations.values())

            return {
                "cached_channels": len(self.conversations),
                "total_cached_messages": total_messages,
                "avg_messages_per_channel": (
                    total_messages / len(self.conversations) if self.conversations else 0
                ),
                "cache_timeout_minutes": self.cache_timeout / 60,
                "bootstrap_limit": self.bootstrap_limit,
                "max_local_messages": self.max_local_messages,
            }

    def _needs_bootstrap(self, channel_id: str, requested_limit: int, current_time: float) -> bool:
        """Determine if we need to fetch from Discord API. Thread-safe."""
        with self._cache_lock:
            if channel_id not in self.conversations:
                return True  # No cache exists

            conv = self.conversations[channel_id]

            # Check if cache is stale
            if current_time - conv["last_bootstrap"] > self.cache_timeout:
                logger.debug(f"Cache expired for channel {channel_id}")
                return True

            # Check if we don't have enough messages
            if len(conv["messages"]) < requested_limit:
                logger.debug(
                    f"Insufficient cached messages for channel {channel_id} "
                    f"(have {len(conv['messages'])}, need {requested_limit})"
                )
                return True

            return False

    def _get_bootstrap_lock(self, channel_id: str) -> threading.Lock:
        """Get or create a bootstrap lock for a specific channel to prevent concurrent API calls"""
        with self._bootstrap_lock_manager:
            if channel_id not in self._bootstrap_locks:
                self._bootstrap_locks[channel_id] = threading.Lock()
            return self._bootstrap_locks[channel_id]

    def sync_with_storage(self, channel_id: str, message, storage_success: bool):
        """Sync cache state with storage result"""
        if not storage_success:
            # Remove message from cache if storage failed
            self.remove_message(channel_id, message.id)
            logger.warning(f"Removed message from cache due to storage failure: {channel_id}")

    def remove_message(self, channel_id: str, message_id: int):
        """Remove a specific message from cache"""
        with self._cache_lock:
            if channel_id in self.conversations:
                messages = self.conversations[channel_id]["messages"]
                # Remove message with matching ID
                self.conversations[channel_id]["messages"] = deque(
                    [msg for msg in messages if msg.id != message_id],
                    maxlen=self.max_local_messages,
                )
                logger.debug(f"Removed message {message_id} from cache in channel {channel_id}")

    async def _bootstrap_conversation(self, channel_id: str, channel):
        """Fetch recent history from Discord to bootstrap/refresh cache. Thread-safe."""
        try:
            # Fetch recent messages from Discord
            messages = []
            async for msg in channel.history(limit=self.bootstrap_limit):
                messages.append(msg)

            # Reverse to get chronological order (oldest first)
            messages.reverse()

            # Thread-safe cache update
            with self._cache_lock:
                self.conversations[channel_id] = {
                    "messages": deque(messages, maxlen=self.max_local_messages),
                    "last_bootstrap": time.time(),
                }

            logger.debug(f"Bootstrapped {len(messages)} messages for channel {channel_id}")

        except Exception as e:
            logger.error(f"Failed to bootstrap conversation for channel {channel_id}: {e}")
            # Initialize empty cache to prevent repeated bootstrap attempts
            with self._cache_lock:
                self.conversations[channel_id] = {
                    "messages": deque(maxlen=self.max_local_messages),
                    "last_bootstrap": time.time(),
                }
