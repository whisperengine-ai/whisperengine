"""
Enhanced Async Components with Proper Resource Management
Addresses: Resource leaks, improper async handling, shutdown issues
"""

import asyncio
import logging
from contextlib import asynccontextmanager

import aiohttp

logger = logging.getLogger(__name__)


class AsyncResourceManager:
    """Manages async resources with proper lifecycle and cleanup"""

    def __init__(self):
        self._sessions: dict[str, aiohttp.ClientSession] = {}
        self._session_locks: dict[str, asyncio.Lock] = {}
        self._session_locks_manager = asyncio.Lock()
        self._active_requests: set[asyncio.Task] = set()
        self._cleanup_callbacks = []
        self._shutdown_event = asyncio.Event()

    async def get_session(
        self, session_name: str = "default", **session_kwargs
    ) -> aiohttp.ClientSession:
        """Get or create a managed aiohttp session"""
        async with self._session_locks_manager:
            if session_name not in self._session_locks:
                self._session_locks[session_name] = asyncio.Lock()

        session_lock = self._session_locks[session_name]
        async with session_lock:
            if session_name not in self._sessions or self._sessions[session_name].closed:
                # Create new session with proper settings
                connector = aiohttp.TCPConnector(
                    limit=100,  # Total connection pool size
                    limit_per_host=30,  # Per-host connection limit
                    ttl_dns_cache=300,  # DNS cache TTL
                    use_dns_cache=True,
                    keepalive_timeout=30,
                    enable_cleanup_closed=True,
                )

                timeout = aiohttp.ClientTimeout(
                    total=90,  # Total timeout
                    connect=10,  # Connection timeout
                    sock_read=60,  # Socket read timeout
                )

                session = aiohttp.ClientSession(
                    connector=connector, timeout=timeout, **session_kwargs
                )

                self._sessions[session_name] = session
                logger.debug(f"Created new aiohttp session: {session_name}")

            return self._sessions[session_name]

    @asynccontextmanager
    async def track_request(self, session_name: str = "default"):
        """Context manager to track active requests"""
        session = await self.get_session(session_name)
        task = asyncio.current_task()

        if task:
            self._active_requests.add(task)

        try:
            yield session
        finally:
            if task:
                self._active_requests.discard(task)

    async def wait_for_requests(self, timeout: float = 30.0):
        """Wait for all active requests to complete"""
        if not self._active_requests:
            return True

        logger.info(f"Waiting for {len(self._active_requests)} requests to complete...")

        try:
            await asyncio.wait_for(
                asyncio.gather(*self._active_requests, return_exceptions=True), timeout=timeout
            )
            logger.info("All requests completed")
            return True
        except TimeoutError:
            logger.warning(f"Some requests did not complete within {timeout}s")
            # Cancel remaining requests
            for task in self._active_requests:
                if not task.done():
                    task.cancel()
            return False

    def register_cleanup(self, cleanup_func):
        """Register cleanup callback"""
        self._cleanup_callbacks.append(cleanup_func)

    async def cleanup(self):
        """Cleanup all resources"""
        logger.info("Starting async resource cleanup...")

        # Signal shutdown
        self._shutdown_event.set()

        # Wait for active requests
        await self.wait_for_requests()

        # Execute cleanup callbacks
        for callback in self._cleanup_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
            except Exception as e:
                logger.error(f"Error in cleanup callback: {e}")

        # Close all sessions
        for session_name, session in self._sessions.items():
            try:
                if not session.closed:
                    await session.close()
                    logger.debug(f"Closed session: {session_name}")
            except Exception as e:
                logger.error(f"Error closing session {session_name}: {e}")

        self._sessions.clear()
        self._session_locks.clear()
        self._active_requests.clear()

        logger.info("Async resource cleanup complete")


# Global instance
_resource_manager: AsyncResourceManager | None = None


def get_resource_manager() -> AsyncResourceManager:
    """Get or create global resource manager"""
    global _resource_manager
    if _resource_manager is None:
        _resource_manager = AsyncResourceManager()
    return _resource_manager


async def cleanup_resources():
    """Cleanup global resources"""
    global _resource_manager
    if _resource_manager:
        await _resource_manager.cleanup()
        _resource_manager = None


class ConcurrentLLMManager:
    """Manages concurrent LLM requests with proper resource limits"""

    def __init__(self, base_llm_client, max_concurrent=5):
        self.base_llm_client = base_llm_client
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.resource_manager = get_resource_manager()

    async def generate_chat_completion_safe(self, **kwargs):
        """Thread-safe chat completion"""
        # Concurrency limiting
        async with self.semaphore:
            async with self.resource_manager.track_request("llm"):
                return await asyncio.get_event_loop().run_in_executor(
                    None, lambda: self.base_llm_client.generate_chat_completion(**kwargs)
                )
