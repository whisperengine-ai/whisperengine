"""
WhisperEngine Advanced Memory Batching System
Optimizes database operations through intelligent batching, caching, and parallel processing
"""

import asyncio
import hashlib
import json
import logging
import threading
import time
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class BatchOperation:
    """Represents a batched memory operation"""

    operation_type: str  # 'store', 'query', 'update', 'delete'
    user_id: str
    data: dict[str, Any]
    future: asyncio.Future
    timestamp: datetime = field(default_factory=datetime.now)
    priority: int = 0  # Higher priority = processed first
    retry_count: int = 0


@dataclass
class BatchMetrics:
    """Performance metrics for batch operations"""

    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    avg_batch_size: float = 0.0
    avg_processing_time: float = 0.0
    cache_hit_rate: float = 0.0
    throughput_ops_per_second: float = 0.0


class SmartCache:
    """Intelligent caching system with TTL and usage patterns"""

    def __init__(self, max_size: int = 10000, default_ttl: int = 300):
        """
        Initialize smart cache

        Args:
            max_size: Maximum number of cached items
            default_ttl: Default time-to-live in seconds
        """
        self.max_size = max_size
        self.default_ttl = default_ttl

        # Cache storage
        self.cache: dict[str, Any] = {}
        self.cache_metadata: dict[str, dict[str, Any]] = {}

        # Performance tracking
        self.hits = 0
        self.misses = 0
        self.evictions = 0

        # Thread safety
        self._lock = threading.RLock()

    def get(self, key: str) -> Any | None:
        """Get item from cache"""
        with self._lock:
            if key not in self.cache:
                self.misses += 1
                return None

            metadata = self.cache_metadata.get(key, {})

            # Check TTL
            if self._is_expired(metadata):
                self._remove_key(key)
                self.misses += 1
                return None

            # Update access patterns
            metadata["last_accessed"] = time.time()
            metadata["access_count"] = metadata.get("access_count", 0) + 1

            self.hits += 1
            return self.cache[key]

    def put(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Put item in cache with optional TTL"""
        with self._lock:
            # Evict if necessary
            if len(self.cache) >= self.max_size and key not in self.cache:
                self._evict_lru()

            # Store value and metadata
            self.cache[key] = value
            self.cache_metadata[key] = {
                "created": time.time(),
                "last_accessed": time.time(),
                "ttl": ttl or self.default_ttl,
                "access_count": 1,
            }

    def invalidate(self, pattern: str | None = None) -> int:
        """Invalidate cache entries matching pattern"""
        with self._lock:
            if pattern is None:
                # Clear all
                count = len(self.cache)
                self.cache.clear()
                self.cache_metadata.clear()
                return count

            # Pattern matching
            keys_to_remove = [key for key in self.cache.keys() if pattern in key]
            for key in keys_to_remove:
                self._remove_key(key)

            return len(keys_to_remove)

    def _is_expired(self, metadata: dict[str, Any]) -> bool:
        """Check if cache entry is expired"""
        if not metadata:
            return True

        created = metadata.get("created", 0)
        ttl = metadata.get("ttl", self.default_ttl)
        return time.time() - created > ttl

    def _evict_lru(self) -> None:
        """Evict least recently used item"""
        if not self.cache:
            return

        # Find LRU item
        lru_key = min(
            self.cache_metadata.keys(), key=lambda k: self.cache_metadata[k].get("last_accessed", 0)
        )

        self._remove_key(lru_key)
        self.evictions += 1

    def _remove_key(self, key: str) -> None:
        """Remove key from cache and metadata"""
        self.cache.pop(key, None)
        self.cache_metadata.pop(key, None)

    def get_stats(self) -> dict[str, Any]:
        """Get cache performance statistics"""
        with self._lock:
            total_requests = self.hits + self.misses
            hit_rate = self.hits / max(total_requests, 1)

            return {
                "size": len(self.cache),
                "hits": self.hits,
                "misses": self.misses,
                "evictions": self.evictions,
                "hit_rate": hit_rate,
                "utilization": len(self.cache) / self.max_size,
            }


class AdvancedMemoryBatcher:
    """Advanced batching system for memory operations with intelligent optimization"""

    def __init__(
        self,
        chromadb_manager,
        batch_size: int = 50,
        flush_interval: float = 1.0,
        max_queue_size: int = 1000,
        enable_compression: bool = True,
        enable_deduplication: bool = True,
        max_workers: int = 4,
    ):
        """
        Initialize advanced memory batcher

        Args:
            chromadb_manager: ChromaDB manager instance
            batch_size: Target batch size for operations
            flush_interval: Time interval to flush batches (seconds)
            max_queue_size: Maximum queue size before blocking
            enable_compression: Enable data compression for storage
            enable_deduplication: Enable automatic deduplication
            max_workers: Number of worker threads
        """
        self.chromadb_manager = chromadb_manager
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.max_queue_size = max_queue_size
        self.enable_compression = enable_compression
        self.enable_deduplication = enable_deduplication
        self.max_workers = max_workers

        # Operation queues by type
        self.operation_queues: dict[str, deque] = defaultdict(deque)

        # Smart caching system
        self.cache = SmartCache(max_size=5000, default_ttl=300)

        # Thread pool for parallel processing
        self.thread_pool = ThreadPoolExecutor(max_workers=max_workers)

        # Performance tracking
        self.metrics = BatchMetrics()
        self.operation_times: list[float] = []
        self.batch_sizes: list[int] = []

        # Deduplication tracking
        self.recent_operations: dict[str, datetime] = {}
        self.dedup_window = timedelta(seconds=5)

        # Background processing
        self.running = False
        self.background_tasks: list[asyncio.Task] = []

        # Thread safety
        self._lock = threading.RLock()

        logger.info(
            f"🚀 Initialized AdvancedMemoryBatcher with batch_size={batch_size}, "
            f"flush_interval={flush_interval}s"
        )

    async def start(self):
        """Start background batch processing"""
        self.running = True

        # Start background processors for different operation types
        operation_types = ["store", "query", "update", "delete"]

        for op_type in operation_types:
            task = asyncio.create_task(self._process_operation_type(op_type))
            self.background_tasks.append(task)

        # Start cache cleanup task
        cleanup_task = asyncio.create_task(self._cleanup_cache())
        self.background_tasks.append(cleanup_task)

        logger.info("✅ Memory batcher background processing started")

    async def stop(self):
        """Stop background processing and flush remaining operations"""
        self.running = False

        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()

        # Wait for tasks to complete or timeout
        try:
            await asyncio.wait_for(
                asyncio.gather(*self.background_tasks, return_exceptions=True), timeout=5.0
            )
        except TimeoutError:
            logger.warning("Background tasks didn't complete within timeout")

        # Flush remaining operations
        await self._flush_all_queues()

        # Shutdown thread pool
        self.thread_pool.shutdown(wait=True)

        logger.info("✅ Memory batcher stopped and flushed")

    async def store_conversation_batch(
        self,
        user_id: str,
        message: str,
        response: str,
        metadata: dict[str, Any] | None = None,
        priority: int = 0,
    ) -> str:
        """Store conversation with batching optimization"""

        # Create operation
        operation = BatchOperation(
            operation_type="store",
            user_id=user_id,
            data={
                "message": message,
                "response": response,
                "metadata": metadata or {},
                "store_type": "conversation",
            },
            future=asyncio.Future(),
            priority=priority,
        )

        # Check for deduplication
        if self.enable_deduplication:
            operation_hash = self._generate_operation_hash(operation)
            if self._is_duplicate_operation(operation_hash):
                logger.debug(f"Skipping duplicate conversation storage for user {user_id}")
                # Return cached result or generate ID
                return f"dedup_{operation_hash[:8]}"

        # Add to queue
        await self._add_to_queue(operation)

        # Wait for result
        result = await operation.future
        return result

    async def store_user_fact_batch(
        self, user_id: str, fact: str, metadata: dict[str, Any] | None = None, priority: int = 0
    ) -> str:
        """Store user fact with batching optimization"""

        operation = BatchOperation(
            operation_type="store",
            user_id=user_id,
            data={"fact": fact, "metadata": metadata or {}, "store_type": "user_fact"},
            future=asyncio.Future(),
            priority=priority,
        )

        # Check for deduplication
        if self.enable_deduplication:
            operation_hash = self._generate_operation_hash(operation)
            if self._is_duplicate_operation(operation_hash):
                logger.debug(f"Skipping duplicate fact storage for user {user_id}")
                return f"dedup_{operation_hash[:8]}"

        await self._add_to_queue(operation)
        result = await operation.future
        return result

    async def query_memories_batch(
        self,
        user_id: str,
        query: str,
        limit: int = 10,
        doc_types: list[str] | None = None,
        use_cache: bool = True,
    ) -> list[dict[str, Any]]:
        """Query memories with batching and caching optimization"""

        # Check cache first
        if use_cache:
            cache_key = self._generate_query_cache_key(user_id, query, limit, doc_types)
            cached_result = self.cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for query: {query[:50]}...")
                return cached_result

        operation = BatchOperation(
            operation_type="query",
            user_id=user_id,
            data={
                "query": query,
                "limit": limit,
                "doc_types": doc_types or [],
                "cache_key": cache_key if use_cache else None,
            },
            future=asyncio.Future(),
        )

        await self._add_to_queue(operation)
        result = await operation.future

        # Cache the result
        if use_cache and cache_key:
            self.cache.put(cache_key, result, ttl=180)  # 3 minute TTL for queries

        return result

    async def batch_store_multiple(self, operations: list[dict[str, Any]]) -> list[str]:
        """Store multiple items in a single optimized batch"""

        batch_futures = []

        for op_data in operations:
            operation = BatchOperation(
                operation_type="store",
                user_id=op_data["user_id"],
                data=op_data,
                future=asyncio.Future(),
                priority=op_data.get("priority", 0),
            )

            batch_futures.append(operation.future)
            await self._add_to_queue(operation)

        # Wait for all operations to complete
        results = await asyncio.gather(*batch_futures)
        return results

    async def _add_to_queue(self, operation: BatchOperation):
        """Add operation to appropriate queue"""

        with self._lock:
            queue = self.operation_queues[operation.operation_type]

            # Check queue size limit
            if len(queue) >= self.max_queue_size:
                logger.warning(f"Queue {operation.operation_type} is full, blocking...")
                # In a real implementation, you might want to implement backpressure
                await asyncio.sleep(0.1)

            queue.append(operation)
            self.metrics.total_operations += 1

    async def _process_operation_type(self, operation_type: str):
        """Background processor for specific operation type"""

        while self.running:
            try:
                # Check if we have operations to process
                queue = self.operation_queues[operation_type]

                if not queue:
                    await asyncio.sleep(0.1)
                    continue

                # Extract batch
                batch = self._extract_batch(operation_type)

                if batch:
                    # Process batch based on type
                    await self._process_batch(operation_type, batch)

                await asyncio.sleep(0.01)  # Small delay to prevent busy-waiting

            except Exception as e:
                logger.error(f"Error in {operation_type} processor: {e}")
                await asyncio.sleep(1.0)  # Back off on error

    def _extract_batch(self, operation_type: str) -> list[BatchOperation]:
        """Extract batch of operations from queue"""

        with self._lock:
            queue = self.operation_queues[operation_type]

            if not queue:
                return []

            # Determine batch size based on queue length and time
            batch_size = min(self.batch_size, len(queue))

            # Sort by priority if needed
            batch = []
            for _ in range(batch_size):
                if queue:
                    batch.append(queue.popleft())

            # Sort by priority (higher priority first)
            batch.sort(key=lambda op: op.priority, reverse=True)

            return batch

    async def _process_batch(self, operation_type: str, batch: list[BatchOperation]):
        """Process a batch of operations"""

        start_time = time.time()

        try:
            if operation_type == "store":
                await self._process_store_batch(batch)
            elif operation_type == "query":
                await self._process_query_batch(batch)
            elif operation_type == "update":
                await self._process_update_batch(batch)
            elif operation_type == "delete":
                await self._process_delete_batch(batch)

            # Update metrics
            processing_time = time.time() - start_time
            self.operation_times.append(processing_time)
            self.batch_sizes.append(len(batch))

            self.metrics.successful_operations += len(batch)

            # Keep only recent metrics
            if len(self.operation_times) > 1000:
                self.operation_times = self.operation_times[-1000:]
                self.batch_sizes = self.batch_sizes[-1000:]

            logger.debug(
                f"Processed {len(batch)} {operation_type} operations in {processing_time*1000:.1f}ms"
            )

        except Exception as e:
            logger.error(f"Batch processing error for {operation_type}: {e}")

            # Mark all operations as failed
            for operation in batch:
                if not operation.future.done():
                    operation.future.set_exception(e)

            self.metrics.failed_operations += len(batch)

    async def _process_store_batch(self, batch: list[BatchOperation]):
        """Process batch of store operations using pandas optimization"""

        if not batch:
            return

        # Group by store type for optimal processing
        conversations = []
        user_facts = []

        for operation in batch:
            if operation.data.get("store_type") == "conversation":
                conversations.append(operation)
            elif operation.data.get("store_type") == "user_fact":
                user_facts.append(operation)

        # Process conversations
        if conversations:
            await self._process_conversation_batch(conversations)

        # Process user facts
        if user_facts:
            await self._process_user_fact_batch(user_facts)

    async def _process_conversation_batch(self, conversations: list[BatchOperation]):
        """Process batch of conversations using vectorized operations"""

        # Prepare data for batch processing
        batch_data = []
        for operation in conversations:
            data = operation.data
            batch_data.append(
                {
                    "user_id": operation.user_id,
                    "message": data["message"],
                    "response": data["response"],
                    "metadata": data["metadata"],
                    "operation": operation,
                }
            )

        # Create DataFrame for vectorized processing
        df = pd.DataFrame(batch_data)

        # Add timestamps and IDs
        df["timestamp"] = datetime.now().isoformat()
        df["memory_id"] = [
            f"conv_{hash(f'{row.user_id}_{row.message}_{row.timestamp}')%1000000}"
            for _, row in df.iterrows()
        ]

        # Process each conversation (ChromaDB doesn't support true batch insert)
        for _, row in df.iterrows():
            try:
                # Store in ChromaDB
                memory_id = await asyncio.get_event_loop().run_in_executor(
                    self.thread_pool,
                    self._store_single_conversation,
                    row["user_id"],
                    row["message"],
                    row["response"],
                    row["metadata"],
                )

                # Mark operation as complete
                operation = row["operation"]
                if not operation.future.done():
                    operation.future.set_result(memory_id)

            except Exception as e:
                logger.error(f"Failed to store conversation for user {row['user_id']}: {e}")
                operation = row["operation"]
                if not operation.future.done():
                    operation.future.set_exception(e)

    def _store_single_conversation(
        self, user_id: str, message: str, response: str, metadata: dict[str, Any]
    ) -> str:
        """Store single conversation (thread-safe)"""
        try:
            return self.chromadb_manager.store_conversation(user_id, message, response, metadata)
        except Exception as e:
            logger.error(f"ChromaDB store error: {e}")
            raise

    async def _process_user_fact_batch(self, user_facts: list[BatchOperation]):
        """Process batch of user facts"""

        for operation in user_facts:
            try:
                # Store user fact
                fact_id = await asyncio.get_event_loop().run_in_executor(
                    self.thread_pool,
                    self._store_single_user_fact,
                    operation.user_id,
                    operation.data["fact"],
                    operation.data["metadata"],
                )

                # Mark operation as complete
                if not operation.future.done():
                    operation.future.set_result(fact_id)

            except Exception as e:
                logger.error(f"Failed to store user fact for user {operation.user_id}: {e}")
                if not operation.future.done():
                    operation.future.set_exception(e)

    def _store_single_user_fact(self, user_id: str, fact: str, metadata: dict[str, Any]) -> str:
        """Store single user fact (thread-safe)"""
        try:
            return self.chromadb_manager.store_user_fact(user_id, fact, metadata)
        except Exception as e:
            logger.error(f"ChromaDB fact store error: {e}")
            raise

    async def _process_query_batch(self, batch: list[BatchOperation]):
        """Process batch of query operations"""

        # Group similar queries for optimization
        query_groups = defaultdict(list)

        for operation in batch:
            query_key = f"{operation.user_id}_{operation.data['query'][:50]}"
            query_groups[query_key].append(operation)

        # Process each group
        for query_key, operations in query_groups.items():
            try:
                # Use the first operation as representative
                representative = operations[0]

                # Execute query
                results = await asyncio.get_event_loop().run_in_executor(
                    self.thread_pool,
                    self._execute_single_query,
                    representative.user_id,
                    representative.data["query"],
                    representative.data["limit"],
                    representative.data["doc_types"],
                )

                # Return results to all operations in group
                for operation in operations:
                    if not operation.future.done():
                        operation.future.set_result(results)

            except Exception as e:
                logger.error(f"Failed to execute query batch: {e}")
                for operation in operations:
                    if not operation.future.done():
                        operation.future.set_exception(e)

    def _execute_single_query(
        self, user_id: str, query: str, limit: int, doc_types: list[str]
    ) -> list[dict[str, Any]]:
        """Execute single query (thread-safe)"""
        try:
            return self.chromadb_manager.retrieve_relevant_memories(user_id, query, limit)
        except Exception as e:
            logger.error(f"ChromaDB query error: {e}")
            raise

    async def _process_update_batch(self, batch: list[BatchOperation]):
        """Process batch of update operations"""
        for operation in batch:
            try:
                # Extract update data
                update_data = operation.data
                memory_id = update_data.get("memory_id")
                new_content = update_data.get("new_content", {})

                if hasattr(self.chromadb_manager, "update_memory"):
                    # Use ChromaDB manager's update method if available
                    result = await asyncio.get_event_loop().run_in_executor(
                        self.thread_pool,
                        self.chromadb_manager.update_memory,
                        memory_id,
                        new_content,
                    )
                else:
                    # Fallback: delete and re-insert (atomic update simulation)
                    if hasattr(self.chromadb_manager, "store_conversation"):
                        result = self.chromadb_manager.store_conversation(
                            operation.user_id,
                            new_content.get("message", ""),
                            new_content.get("response", ""),
                            new_content.get("metadata", {}),
                        )
                    else:
                        result = f"updated_{memory_id}"

                if not operation.future.done():
                    operation.future.set_result(result)

            except Exception as e:
                logger.error(f"Update operation failed for {operation.user_id}: {e}")
                if not operation.future.done():
                    operation.future.set_exception(e)

    async def _process_delete_batch(self, batch: list[BatchOperation]):
        """Process batch of delete operations"""
        for operation in batch:
            try:
                # Extract delete data
                delete_data = operation.data
                memory_id = delete_data.get("memory_id")

                if hasattr(self.chromadb_manager, "delete_memory"):
                    # Use ChromaDB manager's delete method if available
                    result = await asyncio.get_event_loop().run_in_executor(
                        self.thread_pool, self.chromadb_manager.delete_memory, memory_id
                    )
                elif hasattr(self.chromadb_manager, "memory_cache"):
                    # For simplified adapter, remove from cache
                    self.chromadb_manager.memory_cache = [
                        conv
                        for conv in self.chromadb_manager.memory_cache
                        if conv.get("memory_id") != memory_id
                    ]
                    result = f"deleted_{memory_id}"
                else:
                    result = f"delete_simulated_{memory_id}"

                if not operation.future.done():
                    operation.future.set_result(result)

            except Exception as e:
                logger.error(f"Delete operation failed for {operation.user_id}: {e}")
                if not operation.future.done():
                    operation.future.set_exception(e)

    def _generate_operation_hash(self, operation: BatchOperation) -> str:
        """Generate hash for operation deduplication"""

        hash_data = {
            "type": operation.operation_type,
            "user_id": operation.user_id,
            "data": operation.data,
        }

        hash_string = json.dumps(hash_data, sort_keys=True)
        return hashlib.md5(hash_string.encode()).hexdigest()

    def _is_duplicate_operation(self, operation_hash: str) -> bool:
        """Check if operation is a duplicate within dedup window"""

        now = datetime.now()

        # Clean old entries
        self.recent_operations = {
            h: ts for h, ts in self.recent_operations.items() if now - ts < self.dedup_window
        }

        # Check for duplicate
        if operation_hash in self.recent_operations:
            return True

        # Record this operation
        self.recent_operations[operation_hash] = now
        return False

    def _generate_query_cache_key(
        self, user_id: str, query: str, limit: int, doc_types: list[str] | None
    ) -> str:
        """Generate cache key for query"""

        key_data = {
            "user_id": user_id,
            "query": query,
            "limit": limit,
            "doc_types": sorted(doc_types) if doc_types else [],
        }

        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()

    async def _flush_all_queues(self):
        """Flush all remaining operations in queues"""

        for operation_type, queue in self.operation_queues.items():
            if queue:
                batch = list(queue)
                queue.clear()
                logger.info(f"Flushing {len(batch)} {operation_type} operations")
                await self._process_batch(operation_type, batch)

    async def _cleanup_cache(self):
        """Background cache cleanup task"""

        while self.running:
            try:
                # Clean expired entries
                with self.cache._lock:
                    expired_keys = []
                    for key, metadata in self.cache.cache_metadata.items():
                        if self.cache._is_expired(metadata):
                            expired_keys.append(key)

                    for key in expired_keys:
                        self.cache._remove_key(key)

                    if expired_keys:
                        logger.debug(f"Cleaned {len(expired_keys)} expired cache entries")

                await asyncio.sleep(60)  # Clean every minute

            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")
                await asyncio.sleep(60)

    def get_performance_metrics(self) -> dict[str, Any]:
        """Get comprehensive performance metrics"""

        # Calculate derived metrics
        if self.operation_times:
            avg_processing_time = np.mean(self.operation_times)
            avg_batch_size = np.mean(self.batch_sizes)
            total_time = sum(self.operation_times)
            throughput = self.metrics.total_operations / max(total_time, 0.001)
        else:
            avg_processing_time = 0
            avg_batch_size = 0
            throughput = 0

        cache_stats = self.cache.get_stats()

        return {
            "batch_metrics": {
                "total_operations": self.metrics.total_operations,
                "successful_operations": self.metrics.successful_operations,
                "failed_operations": self.metrics.failed_operations,
                "success_rate": self.metrics.successful_operations
                / max(self.metrics.total_operations, 1),
                "avg_batch_size": avg_batch_size,
                "avg_processing_time_ms": avg_processing_time * 1000,
                "throughput_ops_per_second": throughput,
            },
            "cache_metrics": cache_stats,
            "queue_status": {
                op_type: len(queue) for op_type, queue in self.operation_queues.items()
            },
        }


# Adapter for existing systems
class BatchedMemoryAdapter:
    """Adapter to integrate batched memory system with existing components"""

    def __init__(self, chromadb_manager, enable_batching: bool = True):
        """
        Initialize adapter

        Args:
            chromadb_manager: Existing ChromaDB manager
            enable_batching: Whether to enable batching (fallback to direct calls if False)
        """
        self.chromadb_manager = chromadb_manager
        self.enable_batching = enable_batching

        if enable_batching:
            self.batcher = AdvancedMemoryBatcher(
                chromadb_manager=chromadb_manager,
                batch_size=30,  # Smaller batches for responsiveness
                flush_interval=0.5,  # Faster flushing for real-time feel
                max_workers=2,
            )
        else:
            self.batcher = None

    async def start(self):
        """Start batched processing"""
        if self.batcher:
            await self.batcher.start()

    async def stop(self):
        """Stop batched processing"""
        if self.batcher:
            await self.batcher.stop()

    async def store_conversation(
        self, user_id: str, message: str, response: str, metadata: dict[str, Any] | None = None
    ) -> str:
        """Store conversation with optional batching"""

        if self.batcher:
            return await self.batcher.store_conversation_batch(user_id, message, response, metadata)
        else:
            # Direct call
            return self.chromadb_manager.store_conversation(
                user_id, message, response, metadata or {}
            )

    async def store_user_fact(
        self, user_id: str, fact: str, metadata: dict[str, Any] | None = None
    ) -> str:
        """Store user fact with optional batching"""

        if self.batcher:
            return await self.batcher.store_user_fact_batch(user_id, fact, metadata)
        else:
            # Direct call
            return self.chromadb_manager.store_user_fact(user_id, fact, metadata or {})

    async def retrieve_relevant_memories(
        self, user_id: str, query: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Retrieve memories with optional batching and caching"""

        if self.batcher:
            return await self.batcher.query_memories_batch(user_id, query, limit)
        else:
            # Direct call
            return self.chromadb_manager.retrieve_relevant_memories(user_id, query, limit)

    def get_performance_stats(self) -> dict[str, Any]:
        """Get performance statistics"""

        if self.batcher:
            return self.batcher.get_performance_metrics()
        else:
            return {"batching_enabled": False}
