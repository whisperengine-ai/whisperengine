"""
Redis-based cache utility for personality profiles and memory retrievals.
"""
import os
import json
import logging
import time
import redis.asyncio as redis

logger = logging.getLogger(__name__)

class RedisProfileAndMemoryCache:
    def __init__(self, cache_timeout_minutes=15):  # 🔧 HARMONIZED: Changed from 20 to 15 minutes to match conversation cache
        self.cache_timeout = int(cache_timeout_minutes) * 60
        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(os.getenv("REDIS_PORT", "6379"))
        self.redis_db = int(os.getenv("REDIS_DB", "0"))
        self.key_prefix = "profile_memory_cache"
        self.redis = None

    async def initialize(self):
        self.redis = await redis.from_url(
            f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}",
            decode_responses=True,
        )
        logger.info("RedisProfileAndMemoryCache initialized")

    def _profile_key(self, user_id: str) -> str:
        return f"{self.key_prefix}:profile:{user_id}"

    def _memory_key(self, user_id: str, query_hash: str) -> str:
        return f"{self.key_prefix}:memory:{user_id}:{query_hash}"

    async def set_profile(self, user_id: str, profile: dict):
        if not self.redis:
            raise RuntimeError("Redis not initialized")
        key = self._profile_key(user_id)
        await self.redis.set(key, json.dumps(profile), ex=self.cache_timeout)
        logger.debug("Cached personality profile for user %s", user_id)

    async def get_profile(self, user_id: str) -> dict | None:
        if not self.redis:
            raise RuntimeError("Redis not initialized")
        key = self._profile_key(user_id)
        data = await self.redis.get(key)
        if data:
            logger.debug("Profile cache hit for user %s", user_id)
            return json.loads(data)
        logger.debug("Profile cache miss for user %s", user_id)
        return None

    async def set_memory_retrieval(self, user_id: str, query: str, memories: list[dict]):
        if not self.redis:
            if logger:
                logger.debug("Redis not initialized; skipping memory cache")
            return
        try:
            import hashlib
            query_hash = hashlib.md5(query.encode()).hexdigest()
            key = self._memory_key(user_id, query_hash)
            await self.redis.set(key, json.dumps(memories), ex=self.cache_timeout)
            logger.debug("Cached memory retrieval for user %s, query hash %s", user_id, query_hash)
        except Exception as e:
            if logger:
                logger.debug("Failed to cache memory retrieval: %s", e)

    async def get_memory_retrieval(self, user_id: str, query: str) -> list[dict] | None:
        if not self.redis:
            if logger:
                logger.debug("Redis not initialized; skipping memory cache")
            return None
        try:
            import hashlib
            query_hash = hashlib.md5(query.encode()).hexdigest()
            key = self._memory_key(user_id, query_hash)
            data = await self.redis.get(key)
            if data:
                logger.debug("Memory cache hit for user %s, query hash %s", user_id, query_hash)
                return json.loads(data)
            logger.debug("Memory cache miss for user %s, query hash %s", user_id, query_hash)
            return None
        except Exception as e:
            if logger:
                logger.debug("Failed to get memory from cache: %s", e)
            return None

    async def clear_profile(self, user_id: str):
        if not self.redis:
            raise RuntimeError("Redis not initialized")
        key = self._profile_key(user_id)
        await self.redis.delete(key)

    async def clear_memory(self, user_id: str, query: str):
        if not self.redis:
            raise RuntimeError("Redis not initialized")
        import hashlib
        query_hash = hashlib.md5(query.encode()).hexdigest()
        key = self._memory_key(user_id, query_hash)
        await self.redis.delete(key)
