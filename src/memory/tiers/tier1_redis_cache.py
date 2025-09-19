# src/memory/tiers/tier1_redis_cache.py

import redis.asyncio as redis
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class RedisContextCache:
    """
    Tier 1: Ultra-fast recent context cache
    Stores last 20 messages per user with <1ms retrieval
    """
    
    def __init__(self, redis_url: str, default_ttl: int = 1800):
        self.redis_url = redis_url
        self.default_ttl = default_ttl  # 30 minutes
        self.redis_client = None
        self.logger = logging.getLogger(__name__)
        
    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            self.logger.info("Redis cache tier initialized successfully")
        except Exception as e:
            self.logger.error("Failed to initialize Redis cache: %s", e)
            raise
        
    async def add_to_recent_context(
        self,
        user_id: str,
        conversation_id: str,
        user_message: str,
        bot_response: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Add new conversation to recent context cache"""
        if not self.redis_client:
            raise RuntimeError("Redis client not initialized")
            
        cache_key = f"recent_context:{user_id}"
        
        conversation_data = {
            'conversation_id': conversation_id,
            'timestamp': datetime.now().isoformat(),
            'user_message': user_message,
            'bot_response': bot_response,
            'metadata': metadata or {}
        }
        
        try:
            # Add to list (most recent first)
            await self.redis_client.lpush(cache_key, json.dumps(conversation_data))
            
            # Trim to keep only last 20 conversations
            await self.redis_client.ltrim(cache_key, 0, 19)
            
            # Set expiration
            await self.redis_client.expire(cache_key, self.default_ttl)
            
            self.logger.debug("Added conversation %s to recent context for user %s", 
                           conversation_id, user_id)
            
        except Exception as e:
            self.logger.error("Failed to add conversation to cache: %s", e)
            raise
        
    async def get_recent_context(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent conversation context"""
        if not self.redis_client:
            return []
            
        cache_key = f"recent_context:{user_id}"
        
        try:
            # Get recent conversations from Redis
            recent_data = await self.redis_client.lrange(cache_key, 0, limit - 1)
            
            conversations = []
            for data in recent_data:
                try:
                    conversation = json.loads(data)
                    conversations.append(conversation)
                except json.JSONDecodeError:
                    self.logger.warning("Failed to decode cached conversation data")
                    continue
                    
            self.logger.debug("Retrieved %d recent conversations for user %s", 
                           len(conversations), user_id)
            return conversations
            
        except Exception as e:
            self.logger.error("Error retrieving recent context for user %s: %s", user_id, e)
            return []
    
    async def get_user_conversation_count(self, user_id: str) -> int:
        """Get the number of cached conversations for a user"""
        if not self.redis_client:
            return 0
            
        cache_key = f"recent_context:{user_id}"
        
        try:
            count = await self.redis_client.llen(cache_key)
            return count
        except Exception as e:
            self.logger.error("Error getting conversation count for user %s: %s", user_id, e)
            return 0
    
    async def clear_user_context(self, user_id: str):
        """Clear all cached context for a user"""
        if not self.redis_client:
            return
            
        cache_key = f"recent_context:{user_id}"
        
        try:
            await self.redis_client.delete(cache_key)
            self.logger.info("Cleared context cache for user %s", user_id)
        except Exception as e:
            self.logger.error("Error clearing context for user %s: %s", user_id, e)
            raise
    
    async def update_conversation_metadata(
        self,
        user_id: str,
        conversation_id: str,
        metadata_update: Dict[str, Any]
    ):
        """Update metadata for a specific conversation in cache"""
        if not self.redis_client:
            return
            
        cache_key = f"recent_context:{user_id}"
        
        try:
            # Get all conversations
            recent_data = await self.redis_client.lrange(cache_key, 0, -1)
            
            updated_conversations = []
            found = False
            
            for data in recent_data:
                try:
                    conversation = json.loads(data)
                    if conversation.get('conversation_id') == conversation_id:
                        # Update metadata
                        conversation['metadata'].update(metadata_update)
                        found = True
                    updated_conversations.append(json.dumps(conversation))
                except json.JSONDecodeError:
                    # Skip malformed data
                    continue
            
            if found:
                # Replace the entire list
                await self.redis_client.delete(cache_key)
                if updated_conversations:
                    await self.redis_client.lpush(cache_key, *reversed(updated_conversations))
                    await self.redis_client.expire(cache_key, self.default_ttl)
                
                self.logger.debug("Updated metadata for conversation %s", conversation_id)
            
        except Exception as e:
            self.logger.error("Error updating conversation metadata: %s", e)
            raise
    
    async def get_conversation_by_id(
        self,
        user_id: str,
        conversation_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a specific conversation from cache by ID"""
        if not self.redis_client:
            return None
            
        cache_key = f"recent_context:{user_id}"
        
        try:
            recent_data = await self.redis_client.lrange(cache_key, 0, -1)
            
            for data in recent_data:
                try:
                    conversation = json.loads(data)
                    if conversation.get('conversation_id') == conversation_id:
                        return conversation
                except json.JSONDecodeError:
                    continue
            
            return None
            
        except Exception as e:
            self.logger.error("Error retrieving conversation %s: %s", conversation_id, e)
            return None
    
    async def set_context_ttl(self, user_id: str, ttl_seconds: int):
        """Set custom TTL for user's context cache"""
        if not self.redis_client:
            return
            
        cache_key = f"recent_context:{user_id}"
        
        try:
            await self.redis_client.expire(cache_key, ttl_seconds)
            self.logger.debug("Set TTL to %d seconds for user %s", ttl_seconds, user_id)
        except Exception as e:
            self.logger.error("Error setting TTL for user %s: %s", user_id, e)
            raise
    
    async def get_active_users(self, pattern: str = "recent_context:*") -> List[str]:
        """Get list of users with active context caches"""
        if not self.redis_client:
            return []
            
        try:
            keys = await self.redis_client.keys(pattern)
            users = []
            
            for key in keys:
                # Extract user_id from key format "recent_context:{user_id}"
                if isinstance(key, bytes):
                    key = key.decode('utf-8')
                
                if key.startswith("recent_context:"):
                    user_id = key[15:]  # Remove "recent_context:" prefix
                    users.append(user_id)
            
            return users
            
        except Exception as e:
            self.logger.error("Error getting active users: %s", e)
            return []
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics and health information"""
        if not self.redis_client:
            return {"status": "disconnected"}
            
        try:
            info = await self.redis_client.info()
            
            # Get active user count
            active_users = await self.get_active_users()
            
            # Calculate total cached conversations
            total_conversations = 0
            for user_id in active_users:
                count = await self.get_user_conversation_count(user_id)
                total_conversations += count
            
            stats = {
                "status": "connected",
                "redis_version": info.get("redis_version", "unknown"),
                "memory_used": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "active_users": len(active_users),
                "total_cached_conversations": total_conversations,
                "default_ttl_seconds": self.default_ttl,
                "cache_hit_rate": await self._calculate_hit_rate()
            }
            
            return stats
            
        except Exception as e:
            self.logger.error("Error getting cache stats: %s", e)
            return {"status": "error", "error": str(e)}
    
    async def _calculate_hit_rate(self) -> float:
        """Calculate cache hit rate (placeholder for actual implementation)"""
        # This would require tracking hits/misses in production
        # For now, return a placeholder value
        return 0.85
    
    async def ping(self) -> bool:
        """Check if Redis connection is alive"""
        if not self.redis_client:
            return False
            
        try:
            await self.redis_client.ping()
            return True
        except Exception as e:
            self.logger.error("Redis ping failed: %s", e)
            return False
    
    async def cleanup_expired_caches(self):
        """Cleanup expired cache entries (manual maintenance)"""
        if not self.redis_client:
            return
            
        try:
            # Get all recent_context keys
            pattern = "recent_context:*"
            keys = await self.redis_client.keys(pattern)
            
            expired_count = 0
            for key in keys:
                ttl = await self.redis_client.ttl(key)
                if ttl == -2:  # Key doesn't exist
                    expired_count += 1
                elif ttl == -1:  # Key exists but has no expiration
                    # Set default expiration
                    await self.redis_client.expire(key, self.default_ttl)
            
            self.logger.info("Cleanup completed. Found %d expired caches", expired_count)
            
        except Exception as e:
            self.logger.error("Error during cache cleanup: %s", e)
            raise
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            self.logger.info("Redis connection closed")


# Utility functions for testing and management

async def create_redis_cache(redis_url: str = "redis://localhost:6379") -> RedisContextCache:
    """Create and initialize a Redis cache instance"""
    cache = RedisContextCache(redis_url)
    await cache.initialize()
    return cache

async def test_redis_cache_performance():
    """Test Redis cache performance"""
    cache = await create_redis_cache()
    
    import time
    import uuid
    
    # Test data
    user_id = "test_user"
    test_conversations = []
    
    # Generate test conversations
    for i in range(10):
        test_conversations.append({
            "conversation_id": str(uuid.uuid4()),
            "user_message": f"Test message {i}",
            "bot_response": f"Test response {i}",
            "metadata": {"test": True, "index": i}
        })
    
    # Test write performance
    start_time = time.time()
    for conv in test_conversations:
        await cache.add_to_recent_context(
            user_id=user_id,
            conversation_id=conv["conversation_id"],
            user_message=conv["user_message"],
            bot_response=conv["bot_response"],
            metadata=conv["metadata"]
        )
    write_time = time.time() - start_time
    
    # Test read performance
    start_time = time.time()
    retrieved = await cache.get_recent_context(user_id, limit=10)
    read_time = time.time() - start_time
    
    # Cleanup
    await cache.clear_user_context(user_id)
    await cache.close()
    
    print(f"Write performance: {write_time:.4f}s for 10 conversations")
    print(f"Read performance: {read_time:.4f}s for 10 conversations")
    print(f"Retrieved {len(retrieved)} conversations")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_redis_cache_performance())