import signal
import asyncio
from loguru import logger
from typing import List, Callable, Awaitable

class GracefulShutdown:
    def __init__(self):
        self.shutdown_event = asyncio.Event()
        self._cleanup_tasks: List[Callable[[], Awaitable[None]]] = []
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, self._signal_handler)

    def _signal_handler(self, sig, frame):
        logger.info(f"Received shutdown signal: {sig}")
        # Schedule the shutdown event to be set in the event loop
        loop = asyncio.get_event_loop()
        loop.call_soon_threadsafe(self.shutdown_event.set)

    def add_cleanup_task(self, task: Callable[[], Awaitable[None]]):
        """Add an async cleanup task to be run on shutdown."""
        self._cleanup_tasks.append(task)

    async def wait_for_shutdown_signal(self):
        """Wait until a shutdown signal is received."""
        await self.shutdown_event.wait()
        logger.info("Shutdown signal received. Starting cleanup...")
        await self._execute_cleanup()

    async def _execute_cleanup(self):
        """Execute all registered cleanup tasks."""
        if not self._cleanup_tasks:
            logger.info("No cleanup tasks registered.")
            return

        logger.info(f"Executing {len(self._cleanup_tasks)} cleanup tasks...")
        
        results = await asyncio.gather(
            *[task() for task in self._cleanup_tasks], 
            return_exceptions=True
        )
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Cleanup task {i+1} failed: {result}")
            else:
                logger.info(f"Cleanup task {i+1} completed successfully.")
        
        logger.info("Cleanup completed.")

# Global instance
shutdown_handler = GracefulShutdown()
