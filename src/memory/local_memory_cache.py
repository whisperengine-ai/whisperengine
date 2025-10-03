"""
Local Memory-based Cache for Desktop Mode
Provides Redis-compatible interface using in-memory storage with optional file persistence.
Replacement for Redis in desktop/local deployment scenarios.
"""

import asyncio
import json
import logging
import pickle
import threading
import time
from collections import OrderedDict
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class LocalMemoryCache:
    """
    Local memory-based cache that provides Redis-compatible interface.

    Features:
    - In-memory storage with optional file persistence
    - TTL-based expiration (compatible with Redis)
    - Thread-safe operations
    - Atomic operations simulation
    - Key namespacing and organization
    - Optional disk backup for persistence across restarts
    """

    def __init__(
        self,
        cache_timeout_minutes=15,
        bootstrap_limit=20,
        max_local_messages=50,
        enable_persistence=True,
        persistence_interval=300,
    ):
        # Read from environment variables if available
        import os
        cache_timeout_minutes = float(os.getenv('CONVERSATION_CACHE_TIMEOUT_MINUTES', cache_timeout_minutes))
        bootstrap_limit = int(os.getenv('CONVERSATION_CACHE_BOOTSTRAP_LIMIT', bootstrap_limit))
        max_local_messages = int(os.getenv('CONVERSATION_CACHE_MAX_LOCAL', max_local_messages))
        
        self.cache_timeout = float(cache_timeout_minutes) * 60  # Convert to seconds
        self.bootstrap_limit = bootstrap_limit
        self.max_local_messages = max_local_messages
        self.enable_persistence = enable_persistence
        self.persistence_interval = persistence_interval

        # In-memory storage
        self._data: dict[str, Any] = {}
        self._expiry: dict[str, float] = {}
        self._access_order: OrderedDict = OrderedDict()

        # Thread safety
        self._lock = threading.RLock()
        self._background_tasks = []

        # Persistence configuration
        self.cache_dir = Path.home() / ".whisperengine" / "cache"
        self.cache_file = self.cache_dir / "memory_cache.pkl"

        # Key prefixes for organization (Redis-compatible)
        self.key_prefix = "discord_cache"
        self.messages_key = f"{self.key_prefix}:messages"
        self.meta_key = f"{self.key_prefix}:meta"
        self.bootstrap_lock_key = f"{self.key_prefix}:bootstrap_lock"

        self._initialize()

        logger.info(
            f"LocalMemoryCache initialized: timeout={cache_timeout_minutes}min, "
            f"persistence={'enabled' if enable_persistence else 'disabled'}"
        )

    def _initialize(self):
        """Initialize cache directory and load persistent data if available"""
        if self.enable_persistence:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self._load_persistent_data()

            # Start background persistence task
            asyncio.create_task(self._periodic_persistence())

    def _load_persistent_data(self):
        """Load persistent cache data from disk"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, "rb") as f:
                    data = pickle.load(f)
                    self._data = data.get("data", {})
                    self._expiry = data.get("expiry", {})
                    # Clean expired entries on load
                    self._cleanup_expired_entries()
                logger.info(f"Loaded {len(self._data)} cache entries from persistent storage")
        except Exception as e:
            logger.warning(f"Failed to load persistent cache data: {e}")
            self._data = {}
            self._expiry = {}

    def _save_persistent_data(self):
        """Save cache data to disk"""
        if not self.enable_persistence:
            return

        try:
            with self._lock:
                # Clean expired entries before saving
                self._cleanup_expired_entries()

                data_to_save = {
                    "data": dict(self._data),
                    "expiry": dict(self._expiry),
                    "timestamp": time.time(),
                }

                # Atomic write using temporary file
                temp_file = self.cache_file.with_suffix(".tmp")
                with open(temp_file, "wb") as f:
                    pickle.dump(data_to_save, f)
                temp_file.replace(self.cache_file)

            logger.debug(f"Saved {len(self._data)} cache entries to persistent storage")
        except Exception as e:
            logger.error(f"Failed to save persistent cache data: {e}")

    async def _periodic_persistence(self):
        """Background task for periodic persistence"""
        while True:
            try:
                await asyncio.sleep(self.persistence_interval)
                self._save_persistent_data()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic persistence: {e}")

    def _cleanup_expired_entries(self):
        """Remove expired entries from cache"""
        current_time = time.time()
        expired_keys = []

        for key, expiry_time in self._expiry.items():
            if current_time > expiry_time:
                expired_keys.append(key)

        for key in expired_keys:
            self._data.pop(key, None)
            self._expiry.pop(key, None)
            self._access_order.pop(key, None)

        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")

    async def set(self, key: str, value: Any, ex: int | None = None) -> bool:
        """Set a key-value pair with optional expiration (Redis-compatible)"""
        with self._lock:
            self._data[key] = value
            self._access_order[key] = time.time()

            if ex is not None:
                self._expiry[key] = time.time() + ex
            elif key in self._expiry:
                # Remove expiry if not specified
                del self._expiry[key]

        return True

    async def get(self, key: str) -> Any | None:
        """Get value by key (Redis-compatible)"""
        with self._lock:
            # Check if key has expired
            if key in self._expiry and time.time() > self._expiry[key]:
                self._data.pop(key, None)
                self._expiry.pop(key, None)
                self._access_order.pop(key, None)
                return None

            # Update access order
            if key in self._data:
                self._access_order[key] = time.time()
                return self._data[key]

            return None

    async def delete(self, key: str) -> int:
        """Delete a key (Redis-compatible)"""
        with self._lock:
            if key in self._data:
                del self._data[key]
                self._expiry.pop(key, None)
                self._access_order.pop(key, None)
                return 1
            return 0

    async def exists(self, key: str) -> bool:
        """Check if key exists (Redis-compatible)"""
        value = await self.get(key)
        return value is not None

    async def lpush(self, key: str, *values) -> int:
        """Push values to the left of a list (Redis-compatible)"""
        with self._lock:
            if key not in self._data:
                self._data[key] = []
            elif not isinstance(self._data[key], list):
                self._data[key] = []

            # Insert at beginning (left push)
            for value in reversed(values):
                self._data[key].insert(0, value)

            self._access_order[key] = time.time()
            return len(self._data[key])

    async def rpush(self, key: str, *values) -> int:
        """Push values to the right of a list (Redis-compatible)"""
        with self._lock:
            if key not in self._data:
                self._data[key] = []
            elif not isinstance(self._data[key], list):
                self._data[key] = []

            # Append to end (right push)
            self._data[key].extend(values)

            self._access_order[key] = time.time()
            return len(self._data[key])

    async def lrange(self, key: str, start: int, stop: int) -> list[Any]:
        """Get a range of elements from a list (Redis-compatible)"""
        with self._lock:
            if key not in self._data or not isinstance(self._data[key], list):
                return []

            self._access_order[key] = time.time()

            # Handle negative indices (Redis-style)
            data_list = self._data[key]
            list_len = len(data_list)

            if start < 0:
                start = max(0, list_len + start)
            if stop < 0:
                stop = list_len + stop
            else:
                stop = min(stop, list_len - 1)

            if start > stop or start >= list_len:
                return []

            return data_list[start : stop + 1]

    async def ltrim(self, key: str, start: int, stop: int) -> bool:
        """Trim a list to the specified range (Redis-compatible)"""
        with self._lock:
            if key not in self._data or not isinstance(self._data[key], list):
                return True

            data_list = self._data[key]
            list_len = len(data_list)

            # Handle negative indices
            if start < 0:
                start = max(0, list_len + start)
            if stop < 0:
                stop = list_len + stop
            else:
                stop = min(stop, list_len - 1)

            if start > stop or start >= list_len:
                self._data[key] = []
            else:
                self._data[key] = data_list[start : stop + 1]

            self._access_order[key] = time.time()
            return True

    async def hset(self, key: str, field: str, value: Any) -> int:
        """Set field in a hash (Redis-compatible)"""
        with self._lock:
            if key not in self._data:
                self._data[key] = {}
            elif not isinstance(self._data[key], dict):
                self._data[key] = {}

            is_new = field not in self._data[key]
            self._data[key][field] = value
            self._access_order[key] = time.time()

            return 1 if is_new else 0

    async def hget(self, key: str, field: str) -> Any | None:
        """Get field from a hash (Redis-compatible)"""
        with self._lock:
            if key not in self._data or not isinstance(self._data[key], dict):
                return None

            self._access_order[key] = time.time()
            return self._data[key].get(field)

    async def hgetall(self, key: str) -> dict[str, Any]:
        """Get all fields from a hash (Redis-compatible)"""
        with self._lock:
            if key not in self._data or not isinstance(self._data[key], dict):
                return {}

            self._access_order[key] = time.time()
            return dict(self._data[key])

    async def flushall(self) -> bool:
        """Clear all data (Redis-compatible)"""
        with self._lock:
            self._data.clear()
            self._expiry.clear()
            self._access_order.clear()
        return True

    async def keys(self, pattern: str = "*") -> list[str]:
        """Get all keys matching pattern (Redis-compatible)"""
        with self._lock:
            self._cleanup_expired_entries()

            if pattern == "*":
                return list(self._data.keys())

            # Simple pattern matching (just * wildcard)
            import fnmatch

            return [key for key in self._data.keys() if fnmatch.fnmatch(key, pattern)]

    async def info(self, section: str = "memory") -> dict[str, Any]:
        """Get cache information (Redis-compatible)"""
        with self._lock:
            self._cleanup_expired_entries()

            total_memory = sum(len(str(k)) + len(str(v)) for k, v in self._data.items())

            return {
                "total_keys": len(self._data),
                "expired_keys": len(self._expiry),
                "estimated_memory_bytes": total_memory,
                "persistence_enabled": self.enable_persistence,
                "cache_timeout_seconds": self.cache_timeout,
            }

    async def ping(self) -> bool:
        """Health check (Redis-compatible)"""
        return True

    async def close(self):
        """Clean shutdown - save persistent data"""
        if self.enable_persistence:
            self._save_persistent_data()

        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()

        logger.info("LocalMemoryCache closed successfully")


class LocalMemoryCacheAdapter:
    """Adapter to make LocalMemoryCache compatible with existing Redis usage patterns"""

    def __init__(self, cache_timeout_minutes=15, bootstrap_limit=20, max_local_messages=50):
        self.cache = LocalMemoryCache(
            cache_timeout_minutes=cache_timeout_minutes,
            bootstrap_limit=bootstrap_limit,
            max_local_messages=max_local_messages,
        )

        # Key prefixes (matching Redis implementation)
        self.key_prefix = self.cache.key_prefix
        self.messages_key = self.cache.messages_key
        self.meta_key = self.cache.meta_key
        self.bootstrap_lock_key = self.cache.bootstrap_lock_key

    async def store_conversation(
        self, user_id: str, message: str, response: str, metadata: dict[str, Any] | None = None
    ) -> bool:
        """Store conversation in cache (compatible with existing interface)"""
        conversation_key = f"{self.messages_key}:{user_id}"

        conversation_entry = {
            "user_message": message,
            "ai_response": response,
            "timestamp": time.time(),
            "metadata": metadata or {},
        }

        # Add to conversation list
        await self.cache.rpush(conversation_key, json.dumps(conversation_entry))

        # Maintain size limit
        conversation_list = await self.cache.lrange(conversation_key, 0, -1)
        if len(conversation_list) > self.cache.max_local_messages:
            await self.cache.ltrim(conversation_key, -self.cache.max_local_messages, -1)

        return True

    async def get_conversation_history(self, user_id: str, limit: int = 10) -> list[dict[str, Any]]:
        """Get conversation history for user"""
        conversation_key = f"{self.messages_key}:{user_id}"
        raw_conversations = await self.cache.lrange(conversation_key, -limit, -1)

        conversations = []
        for raw_conv in raw_conversations:
            try:
                conversations.append(json.loads(raw_conv))
            except json.JSONDecodeError:
                continue

        return conversations

    async def get_stats(self) -> dict[str, Any]:
        """Get cache statistics"""
        info = await self.cache.info()
        all_keys = await self.cache.keys()

        message_keys = [k for k in all_keys if k.startswith(self.messages_key)]

        return {
            "total_keys": info["total_keys"],
            "conversation_keys": len(message_keys),
            "memory_usage_bytes": info["estimated_memory_bytes"],
            "cache_timeout_seconds": info["cache_timeout_seconds"],
            "type": "LocalMemoryCache",
        }

    async def clear_user_data(self, user_id: str) -> bool:
        """Clear all data for a specific user"""
        conversation_key = f"{self.messages_key}:{user_id}"
        result = await self.cache.delete(conversation_key)
        return result > 0

    async def close(self):
        """Clean shutdown"""
        await self.cache.close()
