"""
Enhanced Async/IO with Lock Timeouts
===================================

This module provides improved versions of async enhancements with proper lock timeout handling
to prevent indefinite blocking in concurrent user scenarios.
"""

import asyncio
import threading
import time
import logging
from typing import Dict, Optional, Any, Callable, Awaitable
from functools import wraps
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class TimeoutLock:
    """Thread lock with configurable timeout support"""
    
    def __init__(self, timeout: float = 30.0, name: str = "unnamed"):
        self._lock = threading.Lock()
        self.timeout = timeout
        self.name = name
        self._acquired_by = None
        self._acquired_at = None
    
    def acquire(self, timeout: Optional[float] = None) -> bool:
        """Acquire lock with timeout"""
        effective_timeout = timeout if timeout is not None else self.timeout
        start_time = time.time()
        
        acquired = self._lock.acquire(timeout=effective_timeout)
        if acquired:
            self._acquired_by = threading.current_thread().name
            self._acquired_at = time.time()
            logger.debug(f"Lock '{self.name}' acquired by {self._acquired_by}")
        else:
            elapsed = time.time() - start_time
            logger.warning(f"Lock '{self.name}' timeout after {elapsed:.2f}s")
        
        return acquired
    
    def release(self):
        """Release the lock"""
        if self._acquired_by:
            held_time = time.time() - self._acquired_at if self._acquired_at else 0
            logger.debug(f"Lock '{self.name}' released by {self._acquired_by}, held for {held_time:.2f}s")
            self._acquired_by = None
            self._acquired_at = None
        
        self._lock.release()
    
    def __enter__(self):
        if not self.acquire():
            raise TimeoutError(f"Failed to acquire lock '{self.name}' within {self.timeout}s")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()


class EnhancedAsyncMemoryManager:
    """
    Enhanced memory manager with proper lock timeout handling
    """
    
    def __init__(self, memory_manager, lock_timeout: float = 30.0, max_workers: int = 4):
        self.memory_manager = memory_manager
        self.lock_timeout = lock_timeout
        
        # Per-user locks with timeouts
        self._user_locks: Dict[str, TimeoutLock] = {}
        self._user_locks_manager = TimeoutLock(timeout=5.0, name="user_locks_manager")
        
        # Global operation locks
        self._global_lock = TimeoutLock(timeout=lock_timeout, name="global_operations")
        
        # Emotion processing locks
        self._emotion_locks: Dict[str, TimeoutLock] = {}
        self._emotion_locks_manager = TimeoutLock(timeout=5.0, name="emotion_locks_manager")
        
        # Thread pool for CPU-intensive operations
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="memory")
        
        # Statistics
        self._operation_stats = {
            'successful_operations': 0,
            'timeout_errors': 0,
            'total_wait_time': 0.0
        }
        
    def _get_user_lock(self, user_id: str) -> TimeoutLock:
        """Get or create a per-user lock with timeout"""
        try:
            with self._user_locks_manager:
                if user_id not in self._user_locks:
                    self._user_locks[user_id] = TimeoutLock(
                        timeout=self.lock_timeout,
                        name=f"user_{user_id[:8]}"
                    )
                return self._user_locks[user_id]
        except TimeoutError:
            logger.error(f"Timeout getting user lock for {user_id}")
            raise TimeoutError(f"Unable to get user lock for {user_id}")

    def _get_emotion_lock(self, user_id: str) -> TimeoutLock:
        """Get or create a per-user emotion processing lock"""
        try:
            with self._emotion_locks_manager:
                if user_id not in self._emotion_locks:
                    self._emotion_locks[user_id] = TimeoutLock(
                        timeout=self.lock_timeout,
                        name=f"emotion_{user_id[:8]}"
                    )
                return self._emotion_locks[user_id]
        except TimeoutError:
            logger.error(f"Timeout getting emotion lock for {user_id}")
            raise TimeoutError(f"Unable to get emotion lock for {user_id}")

    async def store_conversation_async(self, user_id: str, user_message: str, 
                                     bot_response: str, channel_id: Optional[str] = None, 
                                     pre_analyzed_emotion_data: Optional[dict] = None,
                                     timeout: Optional[float] = None):
        """Async wrapper for thread-safe conversation storage with timeout"""
        
        def _store_with_timeout():
            start_time = time.time()
            try:
                user_lock = self._get_user_lock(user_id)
                with user_lock:
                    result = self.memory_manager.store_conversation(
                        user_id, user_message, bot_response, channel_id, pre_analyzed_emotion_data
                    )
                    self._operation_stats['successful_operations'] += 1
                    return result
            except TimeoutError as e:
                self._operation_stats['timeout_errors'] += 1
                logger.error(f"Storage timeout for user {user_id}: {e}")
                raise
            finally:
                self._operation_stats['total_wait_time'] += time.time() - start_time
        
        operation_timeout = timeout or (self.lock_timeout + 10.0)  # Add buffer for actual operation
        
        try:
            return await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(self._executor, _store_with_timeout),
                timeout=operation_timeout
            )
        except asyncio.TimeoutError:
            logger.error(f"Overall timeout for user {user_id} conversation storage")
            raise TimeoutError(f"Conversation storage timed out for user {user_id}")

    async def retrieve_memories_async(self, user_id: str, query: str, limit: int = 10,
                                    timeout: Optional[float] = None):
        """Async wrapper for thread-safe memory retrieval with timeout"""
        
        def _retrieve_with_timeout():
            start_time = time.time()
            try:
                user_lock = self._get_user_lock(user_id)
                with user_lock:
                    result = self.memory_manager.retrieve_relevant_memories(user_id, query, limit)
                    self._operation_stats['successful_operations'] += 1
                    return result
            except TimeoutError as e:
                self._operation_stats['timeout_errors'] += 1
                logger.error(f"Retrieval timeout for user {user_id}: {e}")
                raise
            finally:
                self._operation_stats['total_wait_time'] += time.time() - start_time
        
        operation_timeout = timeout or (self.lock_timeout + 5.0)
        
        try:
            return await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(self._executor, _retrieve_with_timeout),
                timeout=operation_timeout
            )
        except asyncio.TimeoutError:
            logger.error(f"Overall timeout for user {user_id} memory retrieval")
            raise TimeoutError(f"Memory retrieval timed out for user {user_id}")

    async def process_emotion_async(self, user_id: str, message: str, timeout: Optional[float] = None):
        """Async wrapper for thread-safe emotion processing with timeout"""
        
        def _process_emotion_with_timeout():
            start_time = time.time()
            try:
                if hasattr(self.memory_manager, 'emotion_manager') and self.memory_manager.emotion_manager:
                    emotion_lock = self._get_emotion_lock(user_id)
                    with emotion_lock:
                        result = self.memory_manager.emotion_manager.process_interaction(user_id, message)
                        self._operation_stats['successful_operations'] += 1
                        return result
                return None, None
            except TimeoutError as e:
                self._operation_stats['timeout_errors'] += 1
                logger.error(f"Emotion processing timeout for user {user_id}: {e}")
                raise
            finally:
                self._operation_stats['total_wait_time'] += time.time() - start_time
        
        operation_timeout = timeout or (self.lock_timeout + 10.0)  # Emotion analysis can take time
        
        try:
            return await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(self._executor, _process_emotion_with_timeout),
                timeout=operation_timeout
            )
        except asyncio.TimeoutError:
            logger.error(f"Overall timeout for user {user_id} emotion processing")
            # Return neutral emotion rather than failing completely
            return None, None

    async def store_global_fact_async(self, fact: str, context: str = "", added_by: str = "system",
                                     timeout: Optional[float] = None):
        """Async wrapper for thread-safe global fact storage with timeout"""
        
        def _store_global_fact_with_timeout():
            start_time = time.time()
            try:
                with self._global_lock:
                    result = self.memory_manager.store_global_fact(fact, context, added_by)
                    self._operation_stats['successful_operations'] += 1
                    return result
            except TimeoutError as e:
                self._operation_stats['timeout_errors'] += 1
                logger.error(f"Global fact storage timeout: {e}")
                raise
            finally:
                self._operation_stats['total_wait_time'] += time.time() - start_time
        
        operation_timeout = timeout or (self.lock_timeout + 5.0)
        
        try:
            return await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(self._executor, _store_global_fact_with_timeout),
                timeout=operation_timeout
            )
        except asyncio.TimeoutError:
            logger.error("Overall timeout for global fact storage")
            raise TimeoutError("Global fact storage timed out")

    def get_stats(self) -> Dict[str, Any]:
        """Get operation statistics"""
        return {
            **self._operation_stats,
            'active_user_locks': len(self._user_locks),
            'active_emotion_locks': len(self._emotion_locks),
            'average_wait_time': (
                self._operation_stats['total_wait_time'] / max(1, self._operation_stats['successful_operations'])
            )
        }

    def cleanup(self):
        """Clean up resources"""
        logger.info(f"Cleaning up EnhancedAsyncMemoryManager. Stats: {self.get_stats()}")
        self._executor.shutdown(wait=True)


class EnhancedConversationCache:
    """
    Enhanced conversation cache with lock timeout protection
    """
    
    def __init__(self, cache_timeout_minutes=15, bootstrap_limit=20, 
                 max_local_messages=50, lock_timeout_seconds=10.0):
        self.cache_timeout = float(cache_timeout_minutes) * 60
        self.bootstrap_limit = bootstrap_limit
        self.max_local_messages = max_local_messages
        self.lock_timeout = lock_timeout_seconds
        
        # Cache storage
        self._cache = {}
        
        # Thread-safe locks with timeouts
        self._cache_lock = TimeoutLock(timeout=lock_timeout_seconds, name="main_cache")
        self._bootstrap_locks: Dict[str, TimeoutLock] = {}
        self._bootstrap_lock_manager = TimeoutLock(timeout=5.0, name="bootstrap_manager")
        
        # Statistics
        self._stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'bootstrap_operations': 0,
            'timeout_errors': 0
        }
        
        logger.info(f"EnhancedConversationCache initialized with {lock_timeout_seconds}s lock timeout")

    def _get_bootstrap_lock(self, channel_id: str) -> TimeoutLock:
        """Get or create a bootstrap lock for specific channel"""
        try:
            with self._bootstrap_lock_manager:
                if channel_id not in self._bootstrap_locks:
                    self._bootstrap_locks[channel_id] = TimeoutLock(
                        timeout=self.lock_timeout,
                        name=f"bootstrap_{channel_id[:8]}"
                    )
                return self._bootstrap_locks[channel_id]
        except TimeoutError:
            logger.error(f"Timeout getting bootstrap lock for channel {channel_id}")
            raise TimeoutError(f"Unable to get bootstrap lock for channel {channel_id}")

    def add_message(self, channel_id: str, message: dict, timeout: Optional[float] = None):
        """Add message to cache with timeout protection"""
        try:
            with self._cache_lock:
                if channel_id not in self._cache:
                    self._cache[channel_id] = {
                        'messages': [],
                        'last_bootstrap': 0,
                        'created_at': time.time()
                    }
                
                # Add message and maintain size limit
                self._cache[channel_id]['messages'].append(message)
                if len(self._cache[channel_id]['messages']) > self.max_local_messages:
                    self._cache[channel_id]['messages'] = \
                        self._cache[channel_id]['messages'][-self.max_local_messages:]
                
                logger.debug(f"Message added to cache for channel {channel_id}")
                
        except TimeoutError:
            self._stats['timeout_errors'] += 1
            logger.warning(f"Cache lock timeout adding message to channel {channel_id}, skipping cache")
            # Continue without caching rather than blocking the user

    def get_conversation_context(self, channel_id: str) -> list:
        """Get conversation context with timeout protection"""
        try:
            with self._cache_lock:
                if channel_id in self._cache:
                    self._stats['cache_hits'] += 1
                    return self._cache[channel_id]['messages'].copy()
                else:
                    self._stats['cache_misses'] += 1
                    return []
        except TimeoutError:
            self._stats['timeout_errors'] += 1
            logger.warning(f"Cache lock timeout getting context for channel {channel_id}")
            return []  # Return empty rather than blocking

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            with self._cache_lock:
                cached_channels = len(self._cache)
                total_messages = sum(len(conv['messages']) for conv in self._cache.values())
        except TimeoutError:
            cached_channels = -1  # Indicate timeout
            total_messages = -1
        
        return {
            **self._stats,
            'cached_channels': cached_channels,
            'total_cached_messages': total_messages,
            'active_bootstrap_locks': len(self._bootstrap_locks),
            'cache_timeout_minutes': self.cache_timeout / 60,
        }


# Usage example and migration guide
"""
# Replace your current async enhancements with these enhanced versions:

# OLD:
async_memory_manager = AsyncMemoryManager(memory_manager)

# NEW:
async_memory_manager = EnhancedAsyncMemoryManager(
    memory_manager, 
    lock_timeout=30.0,  # 30 second timeout for locks
    max_workers=4
)

# OLD:
conversation_cache = HybridConversationCache()

# NEW:
conversation_cache = EnhancedConversationCache(
    cache_timeout_minutes=15,
    lock_timeout_seconds=10.0  # 10 second timeout for cache locks
)

# Monitor performance:
print("Memory manager stats:", async_memory_manager.get_stats())
print("Cache stats:", conversation_cache.get_stats())
"""
