"""
Thread-Safe Memory Manager with Proper Concurrency Control
Addresses: Race conditions, data corruption, concurrent access issues
"""

import asyncio
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class ThreadSafeMemoryManager:
    """Thread-safe wrapper for memory operations with proper concurrency control"""

    def __init__(self, base_memory_manager, max_workers=4):
        self.base_memory_manager = base_memory_manager
        self.max_workers = max_workers

        # Per-user locks for fine-grained concurrency
        self._user_locks: dict[str, threading.RLock] = {}
        self._user_locks_manager = threading.Lock()

        # Global locks for shared resources
        self._global_facts_lock = threading.RLock()
        self._backup_lock = threading.RLock()

        # Thread pool for CPU-bound operations
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="memory")

        # Operation tracking for graceful shutdown
        self._active_operations = set()
        self._operations_lock = threading.Lock()

        # Connection pooling for ChromaDB (if supported)
        self._connection_pool = {}
        self._pool_lock = threading.Lock()

    # Properties to delegate to base manager
    @property
    def enable_auto_facts(self):
        """Get enable_auto_facts from base manager"""
        return getattr(self.base_memory_manager, "enable_auto_facts", False)

    @enable_auto_facts.setter
    def enable_auto_facts(self, value):
        """Set enable_auto_facts on base manager"""
        if hasattr(self.base_memory_manager, "enable_auto_facts"):
            self.base_memory_manager.enable_auto_facts = value

    @property
    def fact_extractor(self):
        """Get fact_extractor from base manager"""
        return getattr(self.base_memory_manager, "fact_extractor", None)

    @fact_extractor.setter
    def fact_extractor(self, value):
        """Set fact_extractor on base manager"""
        if hasattr(self.base_memory_manager, "fact_extractor"):
            self.base_memory_manager.fact_extractor = value

    def _get_user_lock(self, user_id: str) -> threading.RLock:
        """Get or create per-user lock for thread safety"""
        with self._user_locks_manager:
            if user_id not in self._user_locks:
                self._user_locks[user_id] = threading.RLock()
            return self._user_locks[user_id]

    @contextmanager
    def _track_operation(self, operation_id: str):
        """Context manager to track active operations"""
        with self._operations_lock:
            self._active_operations.add(operation_id)
        try:
            yield
        finally:
            with self._operations_lock:
                self._active_operations.discard(operation_id)

    async def store_conversation_safe(
        self, user_id: str, user_message: str, bot_response: str, **kwargs
    ) -> bool:
        """Thread-safe conversation storage with retry logic"""
        operation_id = f"store_{user_id}_{int(time.time() * 1000)}"
        user_lock = self._get_user_lock(user_id)

        def _store_with_retry():
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    with user_lock:
                        with self._track_operation(operation_id):
                            return self.base_memory_manager.store_conversation(
                                user_id, user_message, bot_response, **kwargs
                            )
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    logger.warning(f"Storage attempt {attempt + 1} failed: {e}")
                    time.sleep(0.1 * (attempt + 1))  # Exponential backoff
            return False

        # Run in thread pool to avoid blocking event loop
        return await asyncio.get_event_loop().run_in_executor(self._executor, _store_with_retry)

    async def retrieve_memories_safe(self, user_id: str, query: str, limit: int = 10) -> list:
        """Thread-safe memory retrieval"""
        operation_id = f"retrieve_{user_id}_{int(time.time() * 1000)}"
        user_lock = self._get_user_lock(user_id)

        def _retrieve_with_lock():
            with user_lock:
                with self._track_operation(operation_id):
                    return self.base_memory_manager.retrieve_relevant_memories(
                        user_id, query, limit
                    )

        return await asyncio.get_event_loop().run_in_executor(self._executor, _retrieve_with_lock)

    async def store_global_fact_safe(
        self, fact: str, context: str = "", added_by: str = "system"
    ) -> bool:
        """Thread-safe global fact storage"""
        operation_id = f"global_fact_{int(time.time() * 1000)}"

        def _store_global_fact():
            with self._global_facts_lock:
                with self._track_operation(operation_id):
                    return self.base_memory_manager.store_global_fact(fact, context, added_by)

        return await asyncio.get_event_loop().run_in_executor(self._executor, _store_global_fact)

    def wait_for_completion(self, timeout: float = 30.0) -> bool:
        """Wait for all active operations to complete"""
        start_time = time.time()
        while self._active_operations and (time.time() - start_time) < timeout:
            time.sleep(0.1)

        remaining = len(self._active_operations)
        if remaining > 0:
            logger.warning(f"{remaining} operations did not complete in {timeout}s")
            return False

        logger.info("All memory operations completed")
        return True

    def cleanup(self):
        """Cleanup resources"""
        # Wait for operations to complete
        self.wait_for_completion()

        # Shutdown thread pool
        self._executor.shutdown(wait=True)

        # Clear locks
        with self._user_locks_manager:
            self._user_locks.clear()

        logger.info("Thread-safe memory manager cleaned up")

    # Delegate all other attributes to base memory manager
    def __getattr__(self, name):
        """Delegate unknown attributes to base memory manager"""
        return getattr(self.base_memory_manager, name)
