"""
Enhanced Shutdown Handler with Graceful Cleanup
Addresses: Data loss, incomplete operations, resource leaks
"""

import asyncio
import atexit
import logging
import signal
import threading

logger = logging.getLogger(__name__)


class GracefulShutdownManager:
    """Manages graceful shutdown with proper cleanup ordering"""

    def __init__(self, bot=None):
        self.shutdown_requested = False
        self.active_operations: set[asyncio.Task] = set()
        self.cleanup_functions = []
        self.shutdown_lock = threading.Lock()
        self.bot = bot  # Discord bot reference for proper shutdown
        self.signal_count = 0  # Track how many times shutdown signal was received

        # Register signal handlers only if we're in the main thread
        try:
            if threading.current_thread() == threading.main_thread():
                signal.signal(signal.SIGINT, self._signal_handler)
                signal.signal(signal.SIGTERM, self._signal_handler)
                logger.debug("Signal handlers registered in main thread")
            else:
                logger.debug("Skipping signal handler registration - not in main thread")
        except (ValueError, OSError) as e:
            logger.warning(f"Could not register signal handlers: {e}")

        atexit.register(self._emergency_cleanup)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.signal_count += 1
        logger.info(f"Shutdown signal {signum} received (count: {self.signal_count})")

        # If multiple Ctrl+C pressed, force immediate exit
        if self.signal_count >= 3:
            logger.warning("Multiple shutdown signals received - forcing immediate exit")
            import os

            os._exit(1)

        # If already shutting down, don't start another shutdown
        if self.shutdown_requested:
            return

        # Use asyncio's thread-safe call_soon_threadsafe to schedule shutdown
        try:
            loop = asyncio.get_running_loop()
            # Schedule the shutdown coroutine from the signal handler context
            asyncio.run_coroutine_threadsafe(self.graceful_shutdown(), loop)
            logger.debug("Graceful shutdown scheduled in event loop")
        except RuntimeError as e:
            logger.error(f"Could not schedule graceful shutdown: {e}")
            # Fallback: set shutdown flag and let the bot's main loop handle it
            self.shutdown_requested = True
            # Force bot close from signal context
            if self.bot and hasattr(self.bot, "close"):
                try:
                    # Schedule bot close in the event loop
                    loop = asyncio.get_running_loop()

                    def close_bot():
                        if self.bot and not self.bot.is_closed():
                            asyncio.create_task(self.bot.close())

                    loop.call_soon_threadsafe(close_bot)
                except (RuntimeError, AttributeError):
                    logger.warning("Could not schedule bot close from signal handler")
        except (RuntimeError, AttributeError) as e:
            logger.error(f"Error in signal handler: {e}")
            # Emergency fallback
            import os

            os._exit(1)

    def register_cleanup(self, cleanup_func, priority=0):
        """Register cleanup function with priority (higher = earlier)"""
        self.cleanup_functions.append((priority, cleanup_func))
        self.cleanup_functions.sort(key=lambda x: x[0], reverse=True)

    async def track_operation(self, operation_coro):
        """Track async operations for graceful completion"""
        task = asyncio.create_task(operation_coro)
        self.active_operations.add(task)

        try:
            result = await task
            return result
        finally:
            self.active_operations.discard(task)

    async def graceful_shutdown(self, timeout=30.0):
        """Perform graceful shutdown with timeout"""
        with self.shutdown_lock:
            if self.shutdown_requested:
                return
            self.shutdown_requested = True

        logger.info("Starting graceful shutdown...")

        # Wait for active operations to complete
        if self.active_operations:
            logger.info(f"Waiting for {len(self.active_operations)} operations to complete...")
            try:
                await asyncio.wait_for(
                    asyncio.gather(*self.active_operations, return_exceptions=True), timeout=timeout
                )
                logger.info("All operations completed")
            except TimeoutError:
                logger.warning("Some operations did not complete in time")
                # Cancel remaining operations
                for task in self.active_operations:
                    if not task.done():
                        task.cancel()

        # Execute cleanup functions in priority order
        for priority, cleanup_func in self.cleanup_functions:
            try:
                if asyncio.iscoroutinefunction(cleanup_func):
                    await cleanup_func()
                else:
                    cleanup_func()
                logger.debug(f"Cleanup function executed (priority {priority})")
            except Exception as e:
                logger.error(f"Error in cleanup function: {e}")

        logger.info("Graceful shutdown complete")

        # Ensure Discord bot is properly closed
        if self.bot:
            try:
                if not self.bot.is_closed():
                    await self.bot.close()
                    logger.info("Discord bot connection closed")
            except Exception as e:
                logger.error(f"Error closing Discord bot: {e}")

        # Force exit after cleanup
        import os

        logger.info("Forcing process exit...")
        os._exit(0)

    def _emergency_cleanup(self):
        """Emergency cleanup for atexit"""
        if self.cleanup_functions:
            logger.warning("Emergency cleanup triggered")
            for _priority, cleanup_func in self.cleanup_functions:
                try:
                    if not asyncio.iscoroutinefunction(cleanup_func):
                        cleanup_func()
                except Exception as e:
                    logger.error(f"Error in emergency cleanup: {e}")
