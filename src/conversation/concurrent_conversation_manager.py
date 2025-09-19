"""
WhisperEngine Concurrent Conversation Manager
Optimizes conversation thread handling for massive concurrent multi-user scenarios
"""

import asyncio
import logging
import threading
import time
from collections import defaultdict, deque
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class ConversationSession:
    """Represents an active conversation session for concurrency tracking"""

    user_id: str
    channel_id: str
    thread_id: str | None
    started_at: datetime
    last_activity: datetime
    message_count: int = 0
    processing_priority: int = 0
    is_active: bool = True
    concurrent_users: set[str] = field(default_factory=set)
    context_cache: dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationLoadMetrics:
    """Tracks conversation processing load and performance"""

    active_sessions: int = 0
    messages_per_second: float = 0.0
    avg_response_time: float = 0.0
    concurrent_users: int = 0
    queue_length: int = 0
    cpu_utilization: float = 0.0
    memory_usage_mb: float = 0.0
    thread_pool_utilization: float = 0.0


class ConversationQueue:
    """High-performance queue for conversation processing with priority support"""

    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.queues = {
            "critical": deque(),  # Urgent emotional support, errors
            "high": deque(),  # Active conversations, real-time
            "normal": deque(),  # Standard conversations
            "low": deque(),  # Background processing, history
        }
        self.queue_weights = {"critical": 4, "high": 3, "normal": 2, "low": 1}
        self._lock = threading.RLock()
        self.total_items = 0

    async def put(self, item: dict[str, Any], priority: str = "normal"):
        """Add item to appropriate priority queue"""
        with self._lock:
            if self.total_items >= self.max_size:
                # Drop lowest priority items if full
                self._drop_low_priority_items()

            self.queues[priority].append(item)
            self.total_items += 1

    async def get(self) -> dict[str, Any] | None:
        """Get next item using weighted priority selection"""
        with self._lock:
            if self.total_items == 0:
                return None

            # Weighted random selection based on priority
            total_weight = 0
            queue_options = []

            for priority, queue in self.queues.items():
                if queue:
                    weight = self.queue_weights[priority] * len(queue)
                    total_weight += weight
                    queue_options.append((priority, weight))

            if not queue_options:
                return None

            # Select queue based on weights
            import random

            rand_val = random.random() * total_weight
            cumulative = 0

            for priority, weight in queue_options:
                cumulative += weight
                if rand_val <= cumulative:
                    item = self.queues[priority].popleft()
                    self.total_items -= 1
                    return item

            # Fallback to first available
            for priority in ["critical", "high", "normal", "low"]:
                if self.queues[priority]:
                    item = self.queues[priority].popleft()
                    self.total_items -= 1
                    return item

            return None

    def _drop_low_priority_items(self, drop_count: int = 10):
        """Drop low priority items when queue is full"""
        dropped = 0
        for priority in ["low", "normal"]:
            queue = self.queues[priority]
            while queue and dropped < drop_count:
                queue.popleft()
                self.total_items -= 1
                dropped += 1
                if dropped >= drop_count:
                    break

    def get_stats(self) -> dict[str, int]:
        """Get queue statistics"""
        with self._lock:
            return {priority: len(queue) for priority, queue in self.queues.items()}


class ConcurrentConversationManager:
    """High-performance concurrent conversation manager for thousands of users"""

    def __init__(
        self,
        advanced_thread_manager=None,
        memory_batcher=None,
        emotion_engine=None,
        max_concurrent_sessions: int = 1000,
        max_workers_threads: int | None = None,
        max_workers_processes: int | None = None,
        session_timeout_minutes: int = 30,
    ):
        """
        Initialize concurrent conversation manager

        Args:
            advanced_thread_manager: Advanced thread manager instance
            memory_batcher: Memory batching system
            emotion_engine: Emotion processing engine
            max_concurrent_sessions: Maximum concurrent conversation sessions
            max_workers_threads: Thread pool size for I/O operations (auto-detected if None)
            max_workers_processes: Process pool size for CPU operations (auto-detected if None)
            session_timeout_minutes: Session timeout in minutes
        """
        import os
        
        # Auto-detect CPU cores for optimal worker configuration
        cpu_count = os.cpu_count() or 4
        
        # Use environment variables or auto-scale based on CPU cores
        if max_workers_threads is None:
            max_workers_threads = min(int(os.getenv("MAX_WORKER_THREADS", cpu_count * 2)), 16)
        if max_workers_processes is None:
            max_workers_processes = min(int(os.getenv("MAX_WORKER_PROCESSES", cpu_count)), 8)
            
        self.advanced_thread_manager = advanced_thread_manager
        self.memory_batcher = memory_batcher
        self.emotion_engine = emotion_engine

        self.max_concurrent_sessions = max_concurrent_sessions
        self.max_workers_threads = max_workers_threads
        self.max_workers_processes = max_workers_processes
        self.session_timeout = timedelta(minutes=session_timeout_minutes)

        # Session management
        self.active_sessions: dict[str, ConversationSession] = {}  # user_id -> session
        self.channel_sessions: dict[str, set[str]] = defaultdict(set)  # channel_id -> user_ids

        # Processing infrastructure
        self.conversation_queue = ConversationQueue(max_size=50000)
        self.thread_pool = ThreadPoolExecutor(max_workers=max_workers_threads)
        self.process_pool = ProcessPoolExecutor(max_workers=max_workers_processes)

        # Performance tracking
        self.metrics = ConversationLoadMetrics()
        self.processing_times: deque = deque(maxlen=1000)
        self.message_timestamps: deque = deque(maxlen=1000)

        # Context caching for performance
        self.context_cache: dict[str, Any] = {}
        self.cache_ttl: dict[str, datetime] = {}
        self.cache_max_size = 5000
        self.cache_ttl_seconds = 120

        # Background processing
        self.running = False
        self.background_tasks: list[asyncio.Task] = []

        # Thread safety
        self._session_lock = threading.RLock()
        self._cache_lock = threading.RLock()

        logger.info(
            f"✨ Initialized ConcurrentConversationManager "
            f"(sessions: {max_concurrent_sessions}, "
            f"threads: {max_workers_threads}, "
            f"processes: {max_workers_processes})"
        )

    async def start(self):
        """Start concurrent conversation processing"""
        self.running = True

        # Start background processors
        processors = [
            self._conversation_processor(),
            self._session_manager(),
            self._metrics_collector(),
            self._cache_cleaner(),
            self._load_balancer(),
        ]

        for processor in processors:
            task = asyncio.create_task(processor)
            self.background_tasks.append(task)

        logger.info("✅ Concurrent conversation processing started")

    async def stop(self):
        """Stop concurrent processing and cleanup"""
        self.running = False

        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()

        try:
            await asyncio.wait_for(
                asyncio.gather(*self.background_tasks, return_exceptions=True), timeout=5.0
            )
        except TimeoutError:
            logger.warning("Background tasks didn't complete within timeout")

        # Shutdown thread pools
        self.thread_pool.shutdown(wait=True)
        self.process_pool.shutdown(wait=True)

        logger.info("✅ Concurrent conversation manager stopped")

    async def process_conversation_message(
        self,
        user_id: str,
        message: str,
        channel_id: str = "default",
        context: dict[str, Any] | None = None,
        priority: str = "normal",
    ) -> dict[str, Any]:
        """Process conversation message with full concurrency optimization"""

        start_time = time.time()

        # Update or create session
        session = await self._update_session(user_id, channel_id, message)

        # Determine processing priority
        processing_priority = self._calculate_processing_priority(session, message, context or {})

        # Create processing task
        task_data = {
            "user_id": user_id,
            "message": message,
            "channel_id": channel_id,
            "context": context or {},
            "session_id": f"{user_id}_{channel_id}",
            "timestamp": datetime.now(),
            "priority_score": processing_priority,
            "start_time": start_time,
        }

        # Add to priority queue
        await self.conversation_queue.put(task_data, priority)

        # For high-priority messages, process immediately
        if priority in ["critical", "high"]:
            return await self._process_message_immediate(task_data)

        # Return acknowledgment for normal/low priority
        return {
            "status": "queued",
            "priority": priority,
            "estimated_wait_seconds": self._estimate_processing_time(),
            "session_id": task_data["session_id"],
        }

    async def _process_message_immediate(self, task_data: dict[str, Any]) -> dict[str, Any]:
        """Process high-priority message immediately"""

        try:
            # Get cached context if available
            context_key = f"{task_data['user_id']}_{task_data['channel_id']}"
            cached_context = self._get_cached_context(context_key)

            if cached_context:
                task_data["context"].update(cached_context)

            # Process through thread manager if available
            if self.advanced_thread_manager:
                thread_result = await self.advanced_thread_manager.process_user_message(
                    task_data["user_id"], task_data["message"], task_data["context"]
                )
            else:
                thread_result = {
                    "current_thread": "default",
                    "thread_analysis": {"keywords": []},
                    "response_guidance": {"tone": "helpful"},
                }

            # Process emotions concurrently if available
            emotion_result = None
            if self.emotion_engine:
                emotion_result = await self.emotion_engine.analyze_emotion(
                    task_data["message"], task_data["user_id"]
                )

            # Cache context for future use
            self._cache_context(
                context_key,
                {
                    "thread_context": thread_result,
                    "recent_emotions": emotion_result,
                    "last_updated": datetime.now(),
                },
            )

            # Track performance
            processing_time = time.time() - task_data["start_time"]
            self.processing_times.append(processing_time)

            return {
                "status": "processed",
                "thread_result": thread_result,
                "emotion_result": emotion_result,
                "processing_time_ms": processing_time * 1000,
                "session_context": self._get_session_context(task_data["user_id"]),
            }

        except Exception as e:
            logger.error(f"Error processing immediate message: {e}")
            return {"status": "error", "error": str(e), "fallback_response": True}

    async def _conversation_processor(self):
        """Background conversation processor"""

        while self.running:
            try:
                # Get next conversation task
                task_data = await self.conversation_queue.get()

                if not task_data:
                    await asyncio.sleep(0.01)
                    continue

                # Process conversation in thread pool
                result = await asyncio.get_event_loop().run_in_executor(
                    self.thread_pool, self._process_conversation_sync, task_data
                )

                # Store result if needed
                if result and result.get("status") == "processed":
                    self._update_session_result(task_data["user_id"], result)

                await asyncio.sleep(0.001)  # Prevent busy waiting

            except Exception as e:
                logger.error(f"Error in conversation processor: {e}")
                await asyncio.sleep(0.1)

    def _process_conversation_sync(self, task_data: dict[str, Any]) -> dict[str, Any]:
        """Synchronous conversation processing for thread pool"""

        try:
            # Simulate conversation processing
            # In real implementation, this would call the actual processing logic

            processing_time = time.time() - task_data["start_time"]

            return {
                "status": "processed",
                "user_id": task_data["user_id"],
                "processing_time": processing_time,
                "result": {
                    "message_processed": True,
                    "context_updated": True,
                    "memory_stored": True,
                },
            }

        except Exception as e:
            logger.error(f"Sync processing error: {e}")
            return {"status": "error", "error": str(e)}

    async def _update_session(
        self, user_id: str, channel_id: str, message: str
    ) -> ConversationSession:
        """Update or create conversation session"""

        with self._session_lock:
            session_key = user_id
            current_time = datetime.now()

            if session_key in self.active_sessions:
                # Update existing session
                session = self.active_sessions[session_key]
                session.last_activity = current_time
                session.message_count += 1
                session.concurrent_users.add(user_id)

                # Update channel tracking
                if session.channel_id != channel_id:
                    # User switched channels
                    old_channel = session.channel_id
                    if old_channel in self.channel_sessions:
                        self.channel_sessions[old_channel].discard(user_id)

                    session.channel_id = channel_id
                    self.channel_sessions[channel_id].add(user_id)
            else:
                # Create new session
                if len(self.active_sessions) >= self.max_concurrent_sessions:
                    self._cleanup_inactive_sessions()

                session = ConversationSession(
                    user_id=user_id,
                    channel_id=channel_id,
                    thread_id=None,
                    started_at=current_time,
                    last_activity=current_time,
                    message_count=1,
                    concurrent_users={user_id},
                )

                self.active_sessions[session_key] = session
                self.channel_sessions[channel_id].add(user_id)

            return session

    def _calculate_processing_priority(
        self, session: ConversationSession, message: str, context: dict[str, Any]
    ) -> int:
        """Calculate processing priority for conversation"""

        priority = 50  # Base priority

        # Active session gets higher priority
        if session.message_count > 1:
            priority += 20

        # Recent activity gets higher priority
        time_since_last = (datetime.now() - session.last_activity).total_seconds()
        if time_since_last < 30:  # Less than 30 seconds
            priority += 15

        # Emotional urgency indicators
        urgent_words = ["help", "urgent", "emergency", "problem", "error", "stuck"]
        if any(word in message.lower() for word in urgent_words):
            priority += 30

        # Question indicators get higher priority
        if "?" in message or message.lower().startswith(("what", "how", "why", "when", "where")):
            priority += 10

        # Channel activity level
        channel_activity = len(self.channel_sessions.get(session.channel_id, set()))
        if channel_activity > 5:  # Busy channel
            priority += 5

        return min(priority, 100)  # Cap at 100

    def _estimate_processing_time(self) -> float:
        """Estimate processing time based on current load"""

        queue_stats = self.conversation_queue.get_stats()
        total_queued = sum(queue_stats.values())

        if not self.processing_times:
            return 1.0  # Default 1 second

        avg_processing_time = np.mean(list(self.processing_times))

        # Factor in queue length
        estimated_wait = (total_queued / self.max_workers_threads) * avg_processing_time

        return min(float(estimated_wait), 30.0)  # Cap at 30 seconds

    def _get_cached_context(self, context_key: str) -> dict[str, Any] | None:
        """Get cached context if still valid"""

        with self._cache_lock:
            if context_key not in self.context_cache:
                return None

            # Check TTL
            if context_key in self.cache_ttl:
                if datetime.now() > self.cache_ttl[context_key]:
                    del self.context_cache[context_key]
                    del self.cache_ttl[context_key]
                    return None

            return self.context_cache[context_key]

    def _cache_context(self, context_key: str, context_data: dict[str, Any]):
        """Cache context data with TTL"""

        with self._cache_lock:
            # Evict old entries if cache is full
            if len(self.context_cache) >= self.cache_max_size:
                self._evict_cache_entries()

            self.context_cache[context_key] = context_data
            self.cache_ttl[context_key] = datetime.now() + timedelta(seconds=self.cache_ttl_seconds)

    def _evict_cache_entries(self, evict_count: int = 500):
        """Evict oldest cache entries"""

        # Sort by TTL and remove oldest
        sorted_entries = sorted(self.cache_ttl.items(), key=lambda x: x[1])

        for i in range(min(evict_count, len(sorted_entries))):
            key, _ = sorted_entries[i]
            self.context_cache.pop(key, None)
            self.cache_ttl.pop(key, None)

    def _get_session_context(self, user_id: str) -> dict[str, Any]:
        """Get session context for user"""

        with self._session_lock:
            session = self.active_sessions.get(user_id)
            if not session:
                return {}

            return {
                "session_duration_minutes": (datetime.now() - session.started_at).total_seconds()
                / 60,
                "message_count": session.message_count,
                "channel_id": session.channel_id,
                "concurrent_users_in_channel": len(
                    self.channel_sessions.get(session.channel_id, set())
                ),
                "is_active_conversation": session.message_count > 1,
            }

    def _update_session_result(self, user_id: str, result: dict[str, Any]):
        """Update session with processing result"""

        with self._session_lock:
            if user_id in self.active_sessions:
                session = self.active_sessions[user_id]
                session.context_cache.update(
                    {"last_result": result, "last_processed": datetime.now()}
                )

    async def _session_manager(self):
        """Background session management and cleanup"""

        while self.running:
            try:
                self._cleanup_inactive_sessions()
                await asyncio.sleep(30)  # Cleanup every 30 seconds
            except Exception as e:
                logger.error(f"Session manager error: {e}")
                await asyncio.sleep(30)

    def _cleanup_inactive_sessions(self):
        """Cleanup inactive sessions"""

        with self._session_lock:
            current_time = datetime.now()
            inactive_sessions = []

            for user_id, session in self.active_sessions.items():
                if current_time - session.last_activity > self.session_timeout:
                    inactive_sessions.append(user_id)

            for user_id in inactive_sessions:
                session = self.active_sessions.pop(user_id, None)
                if session:
                    # Remove from channel tracking
                    self.channel_sessions[session.channel_id].discard(user_id)
                    logger.debug(f"Cleaned up inactive session for user {user_id}")

            if inactive_sessions:
                logger.info(f"Cleaned up {len(inactive_sessions)} inactive sessions")

    async def _metrics_collector(self):
        """Collect performance metrics"""

        while self.running:
            try:
                with self._session_lock:
                    self.metrics.active_sessions = len(self.active_sessions)
                    self.metrics.concurrent_users = len(self.active_sessions)

                # Calculate messages per second
                current_time = time.time()
                self.message_timestamps.append(current_time)

                # Remove timestamps older than 60 seconds
                minute_ago = current_time - 60
                while self.message_timestamps and self.message_timestamps[0] < minute_ago:
                    self.message_timestamps.popleft()

                self.metrics.messages_per_second = len(self.message_timestamps) / 60.0

                # Calculate average response time
                if self.processing_times:
                    self.metrics.avg_response_time = float(np.mean(list(self.processing_times)))

                # Queue length
                queue_stats = self.conversation_queue.get_stats()
                self.metrics.queue_length = sum(queue_stats.values())

                # Thread pool utilization
                if hasattr(self.thread_pool, "_threads"):
                    active_threads = sum(1 for t in self.thread_pool._threads if t.is_alive())
                    self.metrics.thread_pool_utilization = active_threads / self.max_workers_threads

                await asyncio.sleep(5)  # Update every 5 seconds

            except Exception as e:
                logger.error(f"Metrics collector error: {e}")
                await asyncio.sleep(5)

    async def _cache_cleaner(self):
        """Background cache cleanup"""

        while self.running:
            try:
                with self._cache_lock:
                    current_time = datetime.now()
                    expired_keys = []

                    for key, expiry_time in self.cache_ttl.items():
                        if current_time > expiry_time:
                            expired_keys.append(key)

                    for key in expired_keys:
                        self.context_cache.pop(key, None)
                        self.cache_ttl.pop(key, None)

                    if expired_keys:
                        logger.debug(f"Cleaned {len(expired_keys)} expired cache entries")

                await asyncio.sleep(60)  # Clean every minute

            except Exception as e:
                logger.error(f"Cache cleaner error: {e}")
                await asyncio.sleep(60)

    async def _load_balancer(self):
        """Dynamic load balancing and resource management"""

        while self.running:
            try:
                # Monitor queue sizes and adjust priorities
                queue_stats = self.conversation_queue.get_stats()
                total_queued = sum(queue_stats.values())

                # If queues are backing up, prioritize differently
                if total_queued > 1000:
                    logger.warning(f"High queue load: {total_queued} items")
                    # Could implement adaptive batching or additional workers

                # Monitor processing times
                if self.processing_times:
                    avg_time = np.mean(list(self.processing_times))
                    if avg_time > 2.0:  # Taking too long
                        logger.warning(f"High processing latency: {avg_time:.2f}s")

                await asyncio.sleep(10)  # Monitor every 10 seconds

            except Exception as e:
                logger.error(f"Load balancer error: {e}")
                await asyncio.sleep(10)

    def get_performance_stats(self) -> dict[str, Any]:
        """Get comprehensive performance statistics"""

        queue_stats = self.conversation_queue.get_stats()

        with self._session_lock:
            channel_stats = {
                channel: len(users) for channel, users in self.channel_sessions.items()
            }

        return {
            "sessions": {
                "active_sessions": self.metrics.active_sessions,
                "max_sessions": self.max_concurrent_sessions,
                "utilization": self.metrics.active_sessions / self.max_concurrent_sessions,
            },
            "performance": {
                "messages_per_second": self.metrics.messages_per_second,
                "avg_response_time_ms": self.metrics.avg_response_time * 1000,
                "queue_length": self.metrics.queue_length,
                "thread_pool_utilization": self.metrics.thread_pool_utilization,
            },
            "queues": queue_stats,
            "channels": {
                "active_channels": len(self.channel_sessions),
                "channel_distribution": channel_stats,
            },
            "cache": {
                "size": len(self.context_cache),
                "max_size": self.cache_max_size,
                "utilization": len(self.context_cache) / self.cache_max_size,
            },
        }


# Factory function for easy integration
async def create_concurrent_conversation_manager(**kwargs) -> ConcurrentConversationManager:
    """Create and start concurrent conversation manager"""

    manager = ConcurrentConversationManager(**kwargs)
    await manager.start()
    return manager
