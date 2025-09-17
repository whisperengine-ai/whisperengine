#!/usr/bin/env python3
"""
Production Error Handling Framework
Enhanced error handling, recovery mechanisms, and user-friendly error messages for WhisperEngine
"""

import logging
import traceback
import asyncio
from enum import Enum
from typing import Optional, Dict, Any, Callable, Awaitable
from dataclasses import dataclass
from datetime import datetime, timedelta
import functools
import sys
import os

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels for different types of failures"""
    LOW = "low"          # Non-critical, system continues normally
    MEDIUM = "medium"    # Some features may be degraded
    HIGH = "high"        # Major functionality affected
    CRITICAL = "critical"  # System stability at risk


class ErrorCategory(Enum):
    """Categories of errors for better handling and user messaging"""
    LLM_CONNECTION = "llm_connection"
    MEMORY_SYSTEM = "memory_system"
    DISCORD_API = "discord_api"
    DATABASE = "database"
    CONFIGURATION = "configuration"
    NETWORK = "network"
    AUTHENTICATION = "authentication"
    RATE_LIMIT = "rate_limit"
    VALIDATION = "validation"
    SYSTEM_RESOURCE = "system_resource"
    UNKNOWN = "unknown"


@dataclass
class ErrorContext:
    """Context information for error tracking and recovery"""
    category: ErrorCategory
    severity: ErrorSeverity
    user_id: Optional[str] = None
    channel_id: Optional[str] = None
    operation: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    last_attempt: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ProductionErrorHandler:
    """
    Centralized error handling with recovery mechanisms and user-friendly messaging
    """
    
    def __init__(self):
        self.error_counts: Dict[str, int] = {}
        self.last_errors: Dict[str, datetime] = {}
        self.circuit_breakers: Dict[str, bool] = {}
        self.recovery_strategies: Dict[ErrorCategory, Callable] = {}
        self._setup_recovery_strategies()
    
    def _setup_recovery_strategies(self):
        """Setup recovery strategies for different error types"""
        self.recovery_strategies = {
            ErrorCategory.LLM_CONNECTION: self._recover_llm_connection,
            ErrorCategory.MEMORY_SYSTEM: self._recover_memory_system,
            ErrorCategory.DISCORD_API: self._recover_discord_api,
            ErrorCategory.DATABASE: self._recover_database,
            ErrorCategory.RATE_LIMIT: self._recover_rate_limit,
        }
    
    async def handle_error(self, error: Exception, context: ErrorContext) -> Optional[str]:
        """
        Main error handling entry point
        Returns user-friendly error message if applicable
        """
        error_key = f"{context.category.value}_{context.operation or 'unknown'}"
        
        # Track error frequency
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        self.last_errors[error_key] = datetime.now()
        
        # Log detailed error information
        self._log_error(error, context)
        
        # Check circuit breaker
        if self._should_circuit_break(error_key):
            self.circuit_breakers[error_key] = True
            logger.error(f"Circuit breaker activated for {error_key}")
            return self._get_circuit_breaker_message(context)
        
        # Attempt recovery if strategy available
        recovery_attempted = False
        if context.category in self.recovery_strategies:
            try:
                recovery_result = await self.recovery_strategies[context.category](error, context)
                if recovery_result:
                    logger.info(f"Successfully recovered from {context.category.value} error")
                    return None  # Recovery successful, no user message needed
                recovery_attempted = True
            except Exception as recovery_error:
                logger.error(f"Recovery strategy failed: {recovery_error}")
        
        # Generate user-friendly error message
        return self._generate_user_message(error, context, recovery_attempted)
    
    def _log_error(self, error: Exception, context: ErrorContext):
        """Log error with appropriate detail level based on severity"""
        error_msg = f"[{context.category.value.upper()}] {context.operation or 'Unknown operation'}: {str(error)}"
        
        if context.severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH]:
            logger.error(error_msg, exc_info=True)
        elif context.severity == ErrorSeverity.MEDIUM:
            logger.warning(error_msg)
        else:
            logger.info(error_msg)
        
        # Additional context logging
        if context.metadata:
            logger.debug(f"Error context: {context.metadata}")
    
    def _should_circuit_break(self, error_key: str) -> bool:
        """Determine if circuit breaker should activate"""
        count = self.error_counts.get(error_key, 0)
        last_error = self.last_errors.get(error_key)
        
        if not last_error:
            return False
        
        # Circuit break if more than 5 errors in 5 minutes
        if count >= 5 and datetime.now() - last_error < timedelta(minutes=5):
            return True
        
        return False
    
    def _get_circuit_breaker_message(self, context: ErrorContext) -> str:
        """Generate circuit breaker message for users"""
        if context.category == ErrorCategory.LLM_CONNECTION:
            return "🤖 AI services are temporarily unavailable. Please try again in a few minutes."
        elif context.category == ErrorCategory.MEMORY_SYSTEM:
            return "🧠 Memory systems are being restored. Some features may be limited temporarily."
        elif context.category == ErrorCategory.DISCORD_API:
            return "🔗 Discord connection issues detected. Retrying automatically..."
        else:
            return "⚠️ Some services are temporarily unavailable. Please try again shortly."
    
    def _generate_user_message(self, error: Exception, context: ErrorContext, recovery_attempted: bool) -> Optional[str]:
        """Generate user-friendly error messages"""
        
        # Don't show user messages for low severity errors
        if context.severity == ErrorSeverity.LOW:
            return None
        
        base_messages = {
            ErrorCategory.LLM_CONNECTION: {
                ErrorSeverity.MEDIUM: "🤖 AI is thinking a bit slower than usual. Give me a moment...",
                ErrorSeverity.HIGH: "🤖 Having trouble connecting to AI services. Please try again.",
                ErrorSeverity.CRITICAL: "🤖 AI services are currently unavailable. Please check configuration."
            },
            ErrorCategory.MEMORY_SYSTEM: {
                ErrorSeverity.MEDIUM: "🧠 Memory systems are catching up. Some context may be limited.",
                ErrorSeverity.HIGH: "🧠 Memory systems are having issues. Recent conversations may be affected.",
                ErrorSeverity.CRITICAL: "🧠 Memory systems are offline. Please contact an administrator."
            },
            ErrorCategory.DISCORD_API: {
                ErrorSeverity.MEDIUM: "🔗 Discord connection is unstable. Messages may be delayed.",
                ErrorSeverity.HIGH: "🔗 Discord API issues detected. Some features may not work.",
                ErrorSeverity.CRITICAL: "🔗 Cannot connect to Discord. Please check network connection."
            },
            ErrorCategory.DATABASE: {
                ErrorSeverity.MEDIUM: "💾 Database is running slowly. Please be patient.",
                ErrorSeverity.HIGH: "💾 Database connection issues. Some data may not be saved.",
                ErrorSeverity.CRITICAL: "💾 Database is offline. Please contact an administrator."
            },
            ErrorCategory.RATE_LIMIT: {
                ErrorSeverity.MEDIUM: "⏱️ Slow down a bit! I'm processing as fast as I can.",
                ErrorSeverity.HIGH: "⏱️ Rate limit reached. Please wait a moment before trying again.",
                ErrorSeverity.CRITICAL: "⏱️ System overloaded. Please try again in a few minutes."
            },
            ErrorCategory.CONFIGURATION: {
                ErrorSeverity.MEDIUM: "⚙️ Configuration issue detected. Some features may be limited.",
                ErrorSeverity.HIGH: "⚙️ Configuration problem. Please check your settings.",
                ErrorSeverity.CRITICAL: "⚙️ Critical configuration error. Please contact an administrator."
            }
        }
        
        category_messages = base_messages.get(context.category, {})
        message = category_messages.get(context.severity, "⚠️ Something went wrong. Please try again.")
        
        # Add recovery information if attempted
        if recovery_attempted and context.severity >= ErrorSeverity.MEDIUM:
            message += " (Attempting automatic recovery...)"
        
        return message
    
    # Recovery strategy implementations
    async def _recover_llm_connection(self, error: Exception, context: ErrorContext) -> bool:
        """Attempt to recover from LLM connection errors"""
        try:
            # Wait a bit for transient network issues
            await asyncio.sleep(min(2 ** context.retry_count, 10))
            
            # Test connection (this would be implemented based on your LLM client)
            # For now, just return False to indicate recovery should be handled elsewhere
            return False
            
        except Exception as e:
            logger.error(f"LLM recovery failed: {e}")
            return False
    
    async def _recover_memory_system(self, error: Exception, context: ErrorContext) -> bool:
        """Attempt to recover from memory system errors"""
        try:
            # Simple retry with exponential backoff
            await asyncio.sleep(min(1.5 ** context.retry_count, 5))
            return False  # Let calling code handle retry
            
        except Exception as e:
            logger.error(f"Memory system recovery failed: {e}")
            return False
    
    async def _recover_discord_api(self, error: Exception, context: ErrorContext) -> bool:
        """Attempt to recover from Discord API errors"""
        try:
            # Discord has specific rate limiting, so wait appropriately
            if "rate limit" in str(error).lower():
                await asyncio.sleep(5)
            else:
                await asyncio.sleep(min(2 ** context.retry_count, 15))
            return False
            
        except Exception as e:
            logger.error(f"Discord API recovery failed: {e}")
            return False
    
    async def _recover_database(self, error: Exception, context: ErrorContext) -> bool:
        """Attempt to recover from database errors"""
        try:
            # Wait for database to stabilize
            await asyncio.sleep(min(3 ** context.retry_count, 20))
            return False
            
        except Exception as e:
            logger.error(f"Database recovery failed: {e}")
            return False
    
    async def _recover_rate_limit(self, error: Exception, context: ErrorContext) -> bool:
        """Attempt to recover from rate limit errors"""
        try:
            # Wait based on rate limit type
            wait_time = min(5 * (context.retry_count + 1), 60)
            await asyncio.sleep(wait_time)
            return False
            
        except Exception as e:
            logger.error(f"Rate limit recovery failed: {e}")
            return False
    
    def reset_circuit_breaker(self, error_key: str):
        """Manually reset a circuit breaker"""
        if error_key in self.circuit_breakers:
            del self.circuit_breakers[error_key]
            logger.info(f"Circuit breaker reset for {error_key}")
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics for monitoring"""
        return {
            "error_counts": self.error_counts.copy(),
            "active_circuit_breakers": list(self.circuit_breakers.keys()),
            "last_errors": {k: v.isoformat() for k, v in self.last_errors.items()}
        }


# Global error handler instance
error_handler = ProductionErrorHandler()


def handle_errors(
    category: ErrorCategory,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    operation: Optional[str] = None,
    max_retries: int = 3,
    return_on_error: Any = None
):
    """
    Decorator for automatic error handling with recovery
    """
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            context = ErrorContext(
                category=category,
                severity=severity,
                operation=operation or func.__name__,
                max_retries=max_retries
            )
            
            for attempt in range(max_retries + 1):
                context.retry_count = attempt
                context.last_attempt = datetime.now()
                
                try:
                    return await func(*args, **kwargs)
                
                except Exception as e:
                    if attempt < max_retries:
                        logger.debug(f"Attempt {attempt + 1} failed for {func.__name__}: {e}")
                        await asyncio.sleep(min(2 ** attempt, 10))
                        continue
                    
                    # Final attempt failed
                    user_message = await error_handler.handle_error(e, context)
                    
                    # Log the final failure
                    logger.error(f"Function {func.__name__} failed after {max_retries + 1} attempts: {e}")
                    
                    # Return user message or default return value
                    if return_on_error is not None:
                        return return_on_error
                    
                    # Re-raise if no return value specified
                    raise
            
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            context = ErrorContext(
                category=category,
                severity=severity,
                operation=operation or func.__name__,
                max_retries=max_retries
            )
            
            for attempt in range(max_retries + 1):
                context.retry_count = attempt
                context.last_attempt = datetime.now()
                
                try:
                    return func(*args, **kwargs)
                
                except Exception as e:
                    if attempt < max_retries:
                        logger.debug(f"Attempt {attempt + 1} failed for {func.__name__}: {e}")
                        continue
                    
                    # Final attempt failed - log and handle
                    logger.error(f"Function {func.__name__} failed after {max_retries + 1} attempts: {e}")
                    
                    if return_on_error is not None:
                        return return_on_error
                    
                    raise
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def safe_async(
    category: ErrorCategory = ErrorCategory.UNKNOWN,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    return_on_error: Any = None,
    log_errors: bool = True
):
    """
    Simple async error wrapper for fire-and-forget operations
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    logger.error(f"Safe async operation {func.__name__} failed: {e}")
                return return_on_error
        return wrapper
    return decorator


class GracefulDegradation:
    """
    Context manager for graceful feature degradation
    """
    
    def __init__(self, feature_name: str, fallback_value: Any = None):
        self.feature_name = feature_name
        self.fallback_value = fallback_value
        self.error_occurred = False
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.error_occurred = True
            logger.warning(f"Feature {self.feature_name} degraded due to error: {exc_val}")
            return True  # Suppress the exception
        return False
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.error_occurred = True
            logger.warning(f"Feature {self.feature_name} degraded due to error: {exc_val}")
            return True  # Suppress the exception
        return False
    
    def get_result(self, success_value: Any = None) -> Any:
        """Get result with fallback if error occurred"""
        if self.error_occurred:
            return self.fallback_value
        return success_value if success_value is not None else self.fallback_value