"""
Redis-based Conversation Cache for Discord Bot
Replaces in-memory cache with persistent Redis storage.
Provides better scalability, persistence, and simplified locking.
"""

import json
import time
import logging
import asyncio
import pickle
import redis.asyncio as redis
from typing import Dict, List, Optional, Any
import discord
import os

logger = logging.getLogger(__name__)


class RedisConversationCache:
    """
    Redis-based conversation cache that provides persistence and better scalability.

    Features:
    - Persistent cache across container restarts
    - Automatic TTL-based expiration
    - Native Redis data structures for better performance
    - Built-in atomic operations (no custom locking needed)
    - Pub/Sub ready for future real-time features
    """

    def __init__(self, cache_timeout_minutes=15, bootstrap_limit=20, max_local_messages=50):
        self.cache_timeout = float(cache_timeout_minutes) * 60  # Convert to seconds
        self.bootstrap_limit = bootstrap_limit
        self.max_local_messages = max_local_messages

        # Redis connection configuration
        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(os.getenv("REDIS_PORT", "6379"))
        self.redis_db = int(os.getenv("REDIS_DB", "0"))

        # Redis client (will be initialized async)
        self.redis: Optional[redis.Redis] = None

        # Key prefixes for organization
        self.key_prefix = "discord_cache"
        self.messages_key = f"{self.key_prefix}:messages"
        self.meta_key = f"{self.key_prefix}:meta"
        self.bootstrap_lock_key = f"{self.key_prefix}:bootstrap_lock"

        logger.info(
            f"RedisConversationCache initialized: timeout={cache_timeout_minutes}min, "
            f"bootstrap_limit={bootstrap_limit}, max_local={max_local_messages}"
        )
        logger.info(f"Redis connection: {self.redis_host}:{self.redis_port}/{self.redis_db}")

    async def initialize(self):
        """Initialize Redis connection (must be called before use)"""
        try:
            self.redis = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                db=self.redis_db,
                decode_responses=False,  # We'll handle encoding ourselves for message objects
                socket_keepalive=True,
                socket_keepalive_options={},
                health_check_interval=30,
            )

            # Test connection
            await self.redis.ping()
            logger.info("Redis connection established successfully")

        except redis.ConnectionError as e:
            error_msg = f"Redis server is not available at {self.redis_host}:{self.redis_port}"
            logger.error(error_msg)
            logger.info("To fix: Start Redis with 'docker compose up redis' or disable Redis cache")
            raise ConnectionError(error_msg) from e
        except redis.AuthenticationError as e:
            error_msg = f"Redis authentication failed for {self.redis_host}:{self.redis_port}"
            logger.error(error_msg)
            logger.info("To fix: Check REDIS_PASSWORD environment variable")
            raise ConnectionError(error_msg) from e
        except redis.ResponseError as e:
            error_msg = f"Redis configuration error: {e}"
            logger.error(error_msg)
            logger.info("To fix: Check Redis server configuration and database number")
            raise ConnectionError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected Redis connection error: {e}"
            logger.error(error_msg)
            raise ConnectionError(error_msg) from e

    async def cleanup(self):
        """Cleanup Redis connection"""
        if self.redis:
            await self.redis.close()

    def _get_channel_message_key(self, channel_id: str) -> str:
        """Get Redis key for channel messages"""
        return f"{self.messages_key}:{channel_id}"

    def _get_channel_meta_key(self, channel_id: str) -> str:
        """Get Redis key for channel metadata"""
        return f"{self.meta_key}:{channel_id}"

    def _get_bootstrap_lock_key(self, channel_id: str) -> str:
        """Get Redis key for bootstrap lock"""
        return f"{self.bootstrap_lock_key}:{channel_id}"

    def _serialize_message(self, message: discord.Message) -> bytes:
        """Serialize Discord message for Redis storage"""
        # Create a simplified message dict with essential info
        # Convert Discord snowflake IDs to strings to avoid Redis integer overflow
        message_data = {
            "id": str(message.id),  # Convert to string to avoid integer overflow
            "content": message.content,
            "author_id": str(message.author.id),  # Convert to string
            "author_name": message.author.display_name,
            "timestamp": message.created_at.isoformat(),
            "channel_id": str(message.channel.id),  # Convert to string
            "guild_id": str(message.guild.id) if message.guild else None,  # Convert to string
            "bot": message.author.bot,
            "attachments": [att.url for att in message.attachments] if message.attachments else [],
            "embeds": len(message.embeds) > 0,
            "mentions": (
                [str(user.id) for user in message.mentions] if message.mentions else []
            ),  # Convert to strings
        }
        return pickle.dumps(message_data)

    def _deserialize_message(self, data: bytes) -> Dict[str, Any]:
        """Deserialize message data from Redis"""
        return pickle.loads(data)

    async def get_conversation_context(
        self, channel, limit=5, exclude_message_id=None
    ) -> List[Dict[str, Any]]:
        """
        Get recent conversation context with minimal API calls.

        Args:
            channel: Discord channel object
            limit: Number of recent messages to return
            exclude_message_id: Message ID to exclude from context (usually the current message)

        Returns:
            List of recent message dicts (most recent last)
        """
        if not self.redis:
            logger.error("Redis not initialized")
            return []

        channel_id = str(channel.id)
        now = time.time()

        # Check if we need to bootstrap (using Redis for atomic check)
        needs_bootstrap = await self._needs_bootstrap(channel_id, limit, now)

        if needs_bootstrap:
            # Use Redis distributed lock for bootstrap
            await self._bootstrap_with_lock(channel_id, channel)

        # Get messages from Redis
        messages = await self._get_cached_messages(channel_id, limit, exclude_message_id)

        # Fallback: Pull directly from Discord history if Redis cache is empty after bootstrap
        if not messages:
            logger.warning(
                f"No cached messages found in Redis for channel {channel_id} after bootstrap - falling back to Discord history"
            )
            try:
                # Direct Discord API call as final fallback
                fallback_messages = []
                async for msg in channel.history(limit=limit):
                    fallback_messages.append(msg)

                # Convert Discord messages to dict format and filter excluded message
                dict_messages = []
                for msg in fallback_messages:
                    if exclude_message_id and msg.id == exclude_message_id:
                        continue
                    dict_messages.append(
                        {
                            "id": msg.id,
                            "content": msg.content,
                            "author_id": msg.author.id,
                            "author_bot": msg.author.bot,
                            "timestamp": msg.created_at.timestamp(),
                            "channel_id": msg.channel.id,
                        }
                    )

                # Discord history returns newest first, return most recent messages in chronological order
                recent_messages = dict_messages[:limit]  # Take the most recent N messages
                recent_messages.reverse()  # Put them in chronological order (oldest first)
                return recent_messages
            except Exception as e:
                logger.error(f"Failed to fetch Discord history for channel {channel_id}: {e}")
                return []

        return messages

    async def get_user_conversation_context(
        self, channel, user_id: int, limit=5, exclude_message_id=None
    ) -> List[Dict[str, Any]]:
        """
        Get conversation context filtered by specific user ID.

        Args:
            channel: Discord channel object
            user_id: Discord user ID to filter messages for
            limit: Number of recent relevant messages to return
            exclude_message_id: Message ID to exclude from context

        Returns:
            List of message dicts from the user and bot responses
        """
        # Get all recent messages first
        all_messages = await self.get_conversation_context(channel, limit * 3, exclude_message_id)

        # Filter for user messages and bot responses
        user_relevant_messages = []
        bot_id = None  # We'll detect the bot ID from messages

        for msg in all_messages:
            # Detect bot messages
            if msg.get("bot", False):
                if bot_id is None:
                    bot_id = msg["author_id"]
                # Include bot messages
                user_relevant_messages.append(msg)
            # Include messages from the specific user
            elif msg["author_id"] == str(user_id):
                user_relevant_messages.append(msg)

        # Return the most recent messages up to limit
        return (
            user_relevant_messages[-limit:]
            if len(user_relevant_messages) >= limit
            else user_relevant_messages
        )

    async def add_message(self, channel_id: str, message: discord.Message):
        """Add a new message to the cache"""
        if not self.redis:
            return

        try:
            message_key = self._get_channel_message_key(channel_id)
            meta_key = self._get_channel_meta_key(channel_id)

            # Serialize message
            serialized_message = self._serialize_message(message)

            # Add to Redis list (LPUSH adds to beginning)
            await self.redis.lpush(message_key, serialized_message)

            # Trim list to max size
            await self.redis.ltrim(message_key, 0, self.max_local_messages - 1)

            # Update metadata with current timestamp
            await self.redis.hset(meta_key, "last_update", str(time.time()))

            # Set TTL on both keys (convert to int)
            await self.redis.expire(message_key, int(self.cache_timeout))
            await self.redis.expire(meta_key, int(self.cache_timeout))

            logger.debug(f"Added message to Redis cache for channel {channel_id}")

        except Exception as e:
            logger.error(f"Failed to add message to Redis cache: {e}")

    async def remove_message(self, channel_id: str, message_id: int):
        """Remove a specific message from cache"""
        if not self.redis:
            return

        try:
            message_key = self._get_channel_message_key(channel_id)

            # Get all messages to find and remove the specific one
            messages = await self.redis.lrange(message_key, 0, -1)

            for i, serialized_msg in enumerate(messages):
                try:
                    msg_data = self._deserialize_message(serialized_msg)
                    if msg_data["id"] == str(message_id):
                        # Remove the message at this index
                        # Redis doesn't have direct index removal, so we use a placeholder and remove
                        placeholder = b"__REMOVE_PLACEHOLDER__"
                        await self.redis.lset(message_key, i, placeholder)
                        await self.redis.lrem(message_key, 1, placeholder)
                        logger.debug(
                            f"Removed message {message_id} from Redis cache in channel {channel_id}"
                        )
                        break
                except Exception as e:
                    logger.warning(f"Error processing message during removal: {e}")
                    continue

        except Exception as e:
            logger.error(f"Failed to remove message from Redis cache: {e}")

    async def sync_with_storage(
        self, channel_id: str, message: discord.Message, storage_success: bool
    ):
        """Sync cache state with storage result"""
        if not storage_success:
            await self.remove_message(channel_id, message.id)
            logger.warning(f"Removed message from Redis cache due to storage failure: {channel_id}")

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.redis:
            return {"error": "Redis not initialized"}

        try:
            # Get all channel keys
            message_keys = await self.redis.keys(f"{self.messages_key}:*")

            total_messages = 0
            channels = 0

            for key in message_keys:
                length = await self.redis.llen(key)
                total_messages += length
                channels += 1

            return {
                "channels_cached": channels,
                "total_messages": total_messages,
                "avg_messages_per_channel": total_messages / channels if channels > 0 else 0,
                "cache_timeout_minutes": self.cache_timeout / 60,
                "bootstrap_limit": self.bootstrap_limit,
                "max_local_messages": self.max_local_messages,
                "redis_connected": True,
            }

        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"error": str(e)}

    async def _needs_bootstrap(
        self, channel_id: str, requested_limit: int, current_time: float
    ) -> bool:
        """Determine if we need to fetch from Discord API"""
        try:
            message_key = self._get_channel_message_key(channel_id)
            meta_key = self._get_channel_meta_key(channel_id)

            # Check if messages exist
            message_count = await self.redis.llen(message_key)
            if message_count == 0:
                return True  # No cache exists

            # Check if we have enough messages
            if message_count < requested_limit:
                logger.debug(
                    f"Insufficient cached messages for channel {channel_id} "
                    f"(have {message_count}, need {requested_limit})"
                )
                return True

            # Check if cache is stale
            last_bootstrap = await self.redis.hget(meta_key, "last_bootstrap")
            if last_bootstrap:
                last_bootstrap_time = float(last_bootstrap)
                if current_time - last_bootstrap_time > self.cache_timeout:
                    logger.debug(f"Cache expired for channel {channel_id}")
                    return True
            else:
                return True  # No bootstrap metadata

            return False

        except Exception as e:
            logger.error(f"Error checking bootstrap need: {e}")
            return True  # Bootstrap on error to be safe

    async def _bootstrap_with_lock(self, channel_id: str, channel):
        """Bootstrap conversation with Redis distributed lock"""
        lock_key = self._get_bootstrap_lock_key(channel_id)
        lock_timeout = 30  # 30 seconds lock timeout

        try:
            # Try to acquire lock with timeout
            lock_acquired = await self.redis.set(
                lock_key,
                "locked",
                nx=True,  # Only set if not exists
                ex=lock_timeout,  # Expire after timeout
            )

            if lock_acquired:
                try:
                    # Double-check if bootstrap is still needed
                    if await self._needs_bootstrap(channel_id, 1, time.time()):
                        logger.debug(f"Bootstrapping conversation cache for channel {channel_id}")
                        await self._bootstrap_conversation(channel_id, channel)
                finally:
                    # Release lock
                    await self.redis.delete(lock_key)
            else:
                # Wait for other process to finish bootstrapping
                for _ in range(10):  # Wait up to 5 seconds
                    await asyncio.sleep(0.5)
                    if not await self.redis.exists(lock_key):
                        break

        except Exception as e:
            logger.error(f"Error in bootstrap lock: {e}")
            # Fallback: try bootstrap anyway (might be duplicate work)
            await self._bootstrap_conversation(channel_id, channel)

    async def _bootstrap_conversation(self, channel_id: str, channel):
        """Fetch recent history from Discord to bootstrap/refresh cache"""
        try:
            # Fetch recent messages from Discord
            messages = []
            async for msg in channel.history(limit=self.bootstrap_limit):
                messages.append(msg)

            # Clear existing cache and add new messages
            message_key = self._get_channel_message_key(channel_id)
            meta_key = self._get_channel_meta_key(channel_id)

            # Use pipeline for atomic operations
            pipe = self.redis.pipeline()

            # Clear existing messages
            pipe.delete(message_key)

            # Add messages in reverse order (oldest first for LPUSH)
            for msg in messages:
                serialized_msg = self._serialize_message(msg)
                pipe.lpush(message_key, serialized_msg)

            # Trim to max size
            pipe.ltrim(message_key, 0, self.max_local_messages - 1)

            # Update metadata (convert timestamps to strings)
            pipe.hset(meta_key, "last_bootstrap", str(time.time()))
            pipe.hset(meta_key, "last_update", str(time.time()))

            # Set TTL (convert to int)
            pipe.expire(message_key, int(self.cache_timeout))
            pipe.expire(meta_key, int(self.cache_timeout))

            # Execute all operations atomically
            await pipe.execute()

            logger.debug(f"Bootstrapped {len(messages)} messages for channel {channel_id}")

        except Exception as e:
            logger.error(f"Failed to bootstrap conversation for channel {channel_id}: {e}")

    async def clear_channel_cache(self, channel_id: str):
        """Clear cache for a specific channel"""
        if not self.redis:
            return

        try:
            message_key = self._get_channel_message_key(channel_id)
            meta_key = self._get_channel_meta_key(channel_id)

            # Delete both message and metadata keys
            await self.redis.delete(message_key, meta_key)
            logger.debug(f"Cleared cache for channel {channel_id}")

        except Exception as e:
            logger.error(f"Error clearing channel cache: {e}")

    async def _get_cached_messages(
        self, channel_id: str, limit: int, exclude_message_id: Optional[int]
    ) -> List[Dict[str, Any]]:
        """Get cached messages from Redis"""
        if not self.redis:
            return []

        try:
            message_key = self._get_channel_message_key(channel_id)

            # Get messages (Redis LRANGE gets from list, 0 to -1 gets all)
            serialized_messages = await self.redis.lrange(
                message_key, 0, limit * 2
            )  # Get extra in case we need to filter

            messages = []
            for serialized_msg in serialized_messages:
                try:
                    msg_data = self._deserialize_message(serialized_msg)

                    # Filter out excluded message
                    if exclude_message_id and msg_data["id"] == str(exclude_message_id):
                        continue

                    messages.append(msg_data)

                    # Stop when we have enough
                    if len(messages) >= limit:
                        break

                except Exception as e:
                    logger.warning(f"Error deserializing message: {e}")
                    continue

            # Redis LPUSH puts newest first, but we want chronological order (oldest first)
            messages.reverse()

            return messages

        except Exception as e:
            logger.error(f"Error getting cached messages: {e}")
            return []
