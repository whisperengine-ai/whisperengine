"""
Concurrent LLM Manager with Proper Async Handling
Addresses: Blocking operations, connection management, timeout issues
"""

import asyncio
import logging
import time
from typing import Dict, Optional, Any
from concurrent.futures import ThreadPoolExecutor
import threading

logger = logging.getLogger(__name__)

class ConcurrentLLMManager:
    """Thread-safe LLM client wrapper with proper async handling"""
    
    def __init__(self, base_llm_client, max_workers=3):
        self.base_llm_client = base_llm_client
        self.max_workers = max_workers
        
        # Thread pool for blocking LLM operations
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="llm"
        )
        
        # Connection management
        self._connection_lock = threading.RLock()
        self._last_connection_check = 0
        self._connection_check_interval = 30  # seconds
        self._connection_status = None
        
        # Adaptive throttling based on rate limit responses
        self._rate_limit_backoff = 1.0  # Current backoff multiplier
        self._consecutive_rate_limits = 0  # Track consecutive rate limit hits
        self._throttle_lock = asyncio.Lock()
        
        # Active operations tracking
        self._active_operations = set()
        self._operations_lock = threading.Lock()
        
    async def generate_chat_completion_safe(self, messages, timeout=60.0, **kwargs):
        """Thread-safe chat completion with adaptive throttling"""
        operation_id = f"chat_{int(time.time() * 1000)}"
        
        # Track operation
        with self._operations_lock:
            self._active_operations.add(operation_id)
        
        # Apply adaptive throttling if needed
        async with self._throttle_lock:
            if self._rate_limit_backoff > 1.0:
                delay = (self._rate_limit_backoff - 1.0) * 0.5
                logger.debug(f"Applying adaptive throttling delay: {delay:.2f}s")
                await asyncio.sleep(delay)
                
        try:
            # Check connection before making request
            if not await self._check_connection_cached():
                raise Exception("LLM connection unavailable")
            
            # Run blocking operation in thread pool
            def _blocking_call():
                return self.base_llm_client.get_chat_response(messages, **kwargs)
            
            # Execute with timeout
            result = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    self._executor, _blocking_call
                ),
                timeout=timeout
            )
            
            # Success - gradually reduce backoff
            async with self._throttle_lock:
                if self._consecutive_rate_limits > 0:
                    self._consecutive_rate_limits = max(0, self._consecutive_rate_limits - 1)
                    self._rate_limit_backoff = max(1.0, self._rate_limit_backoff * 0.8)
                    if self._rate_limit_backoff <= 1.1:
                        self._rate_limit_backoff = 1.0
                        logger.debug("LLM rate limit backoff reset")
            
            logger.debug(f"LLM call completed for operation {operation_id}")
            return result
            
        except asyncio.TimeoutError:
            logger.error(f"LLM call timed out after {timeout}s for operation {operation_id}")
            raise
        except Exception as e:
            # Check if this was a rate limit error and adjust throttling
            error_str = str(e).lower()
            if "rate limit" in error_str or "429" in error_str or "ratelimiterror" in error_str:
                async with self._throttle_lock:
                    self._consecutive_rate_limits += 1
                    self._rate_limit_backoff = min(8.0, self._rate_limit_backoff * 1.5)
                    logger.warning(f"LLM rate limit detected, increasing backoff to {self._rate_limit_backoff:.1f}x")
            
            logger.error(f"LLM call failed for operation {operation_id}: {e}")
            raise
        finally:
            with self._operations_lock:
                self._active_operations.discard(operation_id)
                    
    async def _check_connection_cached(self) -> bool:
        """Check connection with caching to avoid excessive checks"""
        now = time.time()
        
        with self._connection_lock:
            if (self._connection_status is not None and 
                now - self._last_connection_check < self._connection_check_interval):
                return self._connection_status
                
        # Run connection check in thread pool to avoid blocking
        def _check_connection():
            try:
                return self.base_llm_client.check_connection()
            except Exception as e:
                logger.warning(f"Connection check failed: {e}")
                return False
                
        try:
            status = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    self._executor, _check_connection
                ),
                timeout=10.0
            )
            
            with self._connection_lock:
                self._connection_status = status
                self._last_connection_check = now
                
            return status
            
        except asyncio.TimeoutError:
            logger.warning("Connection check timed out")
            with self._connection_lock:
                self._connection_status = False
                self._last_connection_check = now
            return False
            
    async def check_connection_async(self) -> bool:
        """Async wrapper for connection check"""
        return await self._check_connection_cached()
        
    def has_vision_support(self) -> bool:
        """Check if vision is supported (non-blocking)"""
        return hasattr(self.base_llm_client, 'has_vision_support') and self.base_llm_client.has_vision_support()
        
    def get_vision_config(self):
        """Get vision config (non-blocking)"""
        if hasattr(self.base_llm_client, 'get_vision_config'):
            return self.base_llm_client.get_vision_config()
        return None
        
    async def cleanup(self):
        """Clean up resources"""
        logger.info("Cleaning up ConcurrentLLMManager...")
        
        # Wait for active operations
        if self._active_operations:
            logger.info(f"Waiting for {len(self._active_operations)} LLM operations to complete...")
            # Give operations time to complete naturally
            for _ in range(10):  # 10 seconds max
                if not self._active_operations:
                    break
                await asyncio.sleep(1)
                
        # Shutdown executor
        self._executor.shutdown(wait=True)
        logger.info("LLM manager cleanup complete")
        
    # Delegate other attributes to base client
    def __getattr__(self, name):
        return getattr(self.base_llm_client, name)
