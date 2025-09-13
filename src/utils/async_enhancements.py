"""
Async/IO Enhancements for Discord Bot
Provides thread-safe wrappers and async utilities for concurrent user operations
"""

import asyncio
import threading
import time
import logging
from typing import Dict, Optional, Any, Callable, Awaitable
from functools import wraps
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class AsyncMemoryManager:
    """
    Thread-safe wrapper for memory operations to handle concurrent users
    """
    
    def __init__(self, memory_manager):
        self.memory_manager = memory_manager
        self._user_locks = {}  # Per-user locks for storage operations
        self._user_locks_manager = threading.Lock()
        self._global_lock = threading.Lock()
        self._emotion_locks = {}  # Per-user emotion processing locks
        self._emotion_locks_manager = threading.Lock()
        
        # Thread pool for CPU-intensive operations
        self._executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="memory")
        
    def _get_user_lock(self, user_id: str) -> threading.Lock:
        """Get or create a per-user lock for thread-safe operations"""
        with self._user_locks_manager:
            if user_id not in self._user_locks:
                self._user_locks[user_id] = threading.Lock()
            return self._user_locks[user_id]

    def _get_emotion_lock(self, user_id: str) -> threading.Lock:
        """Get or create a per-user emotion processing lock"""
        with self._emotion_locks_manager:
            if user_id not in self._emotion_locks:
                self._emotion_locks[user_id] = threading.Lock()
            return self._emotion_locks[user_id]

    async def store_conversation_async(self, user_id: str, user_message: str, 
                                     bot_response: str, channel_id: Optional[str] = None, 
                                     pre_analyzed_emotion_data: Optional[dict] = None,
                                     metadata: Optional[dict] = None):
        """Async wrapper for thread-safe conversation storage"""
        user_lock = self._get_user_lock(user_id)
        
        def _store_with_lock():
            with user_lock:
                return self.memory_manager.store_conversation(
                    user_id, user_message, bot_response, channel_id, pre_analyzed_emotion_data, metadata
                )
        
        # Run in thread pool to avoid blocking the event loop
        return await asyncio.get_event_loop().run_in_executor(
            self._executor, _store_with_lock
        )

    async def retrieve_memories_async(self, user_id: str, query: str, limit: int = 10):
        """Async wrapper for thread-safe memory retrieval"""
        user_lock = self._get_user_lock(user_id)
        
        def _retrieve_with_lock():
            with user_lock:
                return self.memory_manager.retrieve_relevant_memories(user_id, query, limit)
        
        return await asyncio.get_event_loop().run_in_executor(
            self._executor, _retrieve_with_lock
        )

    async def process_emotion_async(self, user_id: str, message: str):
        """Async wrapper for thread-safe emotion processing"""
        emotion_lock = self._get_emotion_lock(user_id)
        
        def _process_emotion_with_lock():
            if hasattr(self.memory_manager, 'emotion_manager') and self.memory_manager.emotion_manager:
                with emotion_lock:
                    return self.memory_manager.emotion_manager.process_interaction(user_id, message)
            return None, None
        
        return await asyncio.get_event_loop().run_in_executor(
            self._executor, _process_emotion_with_lock
        )

    async def store_global_fact_async(self, fact: str, context: str = "", added_by: str = "system"):
        """Async wrapper for thread-safe global fact storage"""
        def _store_global_fact():
            with self._global_lock:
                return self.memory_manager.store_global_fact(fact, context, added_by)
        
        return await asyncio.get_event_loop().run_in_executor(
            self._executor, _store_global_fact
        )

    def cleanup(self):
        """Clean up resources"""
        self._executor.shutdown(wait=True)


class AsyncLLMManager:
    """
    Rate-limited and thread-safe LLM client wrapper for concurrent users
    """
    
    def __init__(self, llm_client, max_concurrent_requests: int = 3):
        self.llm_client = llm_client
        self._semaphore = asyncio.Semaphore(max_concurrent_requests)
        
    async def get_chat_response_async(self, conversation_context: list, user_id: Optional[str] = None) -> str:
        """
        Async LLM call with concurrency control
        """
        # Use semaphore to limit concurrent requests
        async with self._semaphore:
            try:
                # Run the synchronous LLM call in a thread pool
                response = await asyncio.get_event_loop().run_in_executor(
                    None, self.llm_client.get_chat_response, conversation_context
                )
                return response
            except Exception as e:
                logger.error(f"LLM request failed for user {user_id}: {e}")
                raise

    async def analyze_emotion_async(self, user_message: str, user_id: Optional[str] = None) -> dict:
        """Async emotion analysis"""
        async with self._semaphore:
            try:
                # Run emotion analysis in thread pool
                if hasattr(self.llm_client, 'analyze_emotion_and_relationships'):
                    response = await asyncio.get_event_loop().run_in_executor(
                        None, self.llm_client.analyze_emotion_and_relationships, user_message
                    )
                    return response
                return {}
            except Exception as e:
                logger.error(f"Emotion analysis failed for user {user_id}: {e}")
                return {}


class ConcurrentImageProcessor:
    """
    Thread-safe image processor for handling multiple concurrent image operations
    """
    
    def __init__(self, image_processor, max_concurrent_downloads: int = 5):
        self.image_processor = image_processor
        self._download_semaphore = asyncio.Semaphore(max_concurrent_downloads)
        self._processing_lock = threading.Lock()
    
    async def process_attachments_concurrent(self, attachments):
        """Process multiple attachments concurrently with rate limiting"""
        async with self._download_semaphore:
            # Process attachments in the original method but with concurrency control
            with self._processing_lock:
                return await self.image_processor.process_multiple_attachments(attachments)


def async_timeout(timeout_seconds: float = 30.0):
    """
    Decorator for adding timeout protection to async functions
    """
    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout_seconds)
            except asyncio.TimeoutError:
                logger.warning(f"Function {func.__name__} timed out after {timeout_seconds}s")
                raise
        return wrapper
    return decorator


def with_user_lock(func: Callable) -> Callable:
    """
    Decorator to ensure user-specific operations are thread-safe
    """
    @wraps(func)
    def wrapper(self, user_id: str, *args, **kwargs):
        if hasattr(self, '_get_user_lock'):
            user_lock = self._get_user_lock(user_id)
            with user_lock:
                return func(self, user_id, *args, **kwargs)
        else:
            return func(self, user_id, *args, **kwargs)
    return wrapper


class AsyncUtilities:
    """
    Collection of utility functions for async operations
    """
    
    @staticmethod
    async def run_with_timeout(coro, timeout: float, default_value=None):
        """Run a coroutine with timeout, returning default value on timeout"""
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning(f"Operation timed out after {timeout}s")
            return default_value
    
    @staticmethod
    async def gather_with_limit(coroutines, limit: int = 5):
        """Run coroutines concurrently with a limit on concurrent operations"""
        semaphore = asyncio.Semaphore(limit)
        
        async def run_with_semaphore(coro):
            async with semaphore:
                return await coro
        
        return await asyncio.gather(*[run_with_semaphore(coro) for coro in coroutines])
    
    @staticmethod
    def create_user_context(user_id: str, operation: str) -> dict:
        """Create context information for logging and debugging"""
        return {
            'user_id': user_id,
            'operation': operation,
            'timestamp': time.time(),
            'thread_id': threading.get_ident()
        }


# Global instances (to be initialized by the main bot)
async_memory_manager: Optional[AsyncMemoryManager] = None
async_llm_manager: Optional[AsyncLLMManager] = None
concurrent_image_processor: Optional[ConcurrentImageProcessor] = None

def initialize_async_components(memory_manager, llm_client, image_processor):
    """Initialize all async components"""
    global async_memory_manager, async_llm_manager, concurrent_image_processor
    
    async_memory_manager = AsyncMemoryManager(memory_manager)
    async_llm_manager = AsyncLLMManager(llm_client)
    concurrent_image_processor = ConcurrentImageProcessor(image_processor)
    
    logger.info("Async components initialized for concurrent user operations")

def cleanup_async_components():
    """Clean up async components"""
    global async_memory_manager
    
    if async_memory_manager:
        async_memory_manager.cleanup()
    
    logger.info("Async components cleaned up")
