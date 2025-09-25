"""
Simple Rate Limiter for Discord Commands
Provides basic per-user rate limiting to prevent abuse
"""

import logging
import time
from collections import defaultdict
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class SimpleRateLimiter:
    """Basic rate limiter for Discord commands"""
    
    def __init__(self):
        # user_id -> command_type -> list of timestamps
        self.user_command_history: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
        
        # Rate limits: (max_requests, time_window_seconds)
        self.rate_limits = {
            "voice": (5, 300),        # 5 TTS commands per 5 minutes
            "web_search": (10, 600),  # 10 searches per 10 minutes
            "memory": (20, 300),      # 20 memory commands per 5 minutes
            "admin": (50, 3600),      # 50 admin commands per hour
            "default": (30, 60),      # 30 commands per minute
        }
        
        # Track warnings to avoid spam
        self.warned_users = set()
    
    def check_rate_limit(self, user_id: str, command_type: str = "default") -> bool:
        """
        Check if user is within rate limits for command type
        
        Args:
            user_id: Discord user ID
            command_type: Type of command (voice, web_search, memory, admin, default)
            
        Returns:
            True if request is allowed, False if rate limited
        """
        now = time.time()
        max_requests, time_window = self.rate_limits.get(command_type, self.rate_limits["default"])
        
        # Clean old entries
        user_history = self.user_command_history[user_id][command_type]
        cutoff_time = now - time_window
        
        # Remove timestamps older than the time window
        self.user_command_history[user_id][command_type] = [
            timestamp for timestamp in user_history if timestamp > cutoff_time
        ]
        
        current_count = len(self.user_command_history[user_id][command_type])
        
        if current_count >= max_requests:
            # Log rate limit hit
            if user_id not in self.warned_users:
                self.warned_users.add(user_id)
                logger.warning(
                    "SECURITY: Rate limit exceeded by user %s for %s commands (%d/%d in %d seconds)",
                    user_id, command_type, current_count, max_requests, time_window
                )
                # Reset warning after an hour
                # (in production, you'd want a more sophisticated system)
            
            return False
        
        # Record this request
        self.user_command_history[user_id][command_type].append(now)
        return True
    
    def get_rate_limit_info(self, user_id: str, command_type: str = "default") -> Tuple[int, int, int]:
        """
        Get rate limit information for a user/command type
        
        Returns:
            (current_usage, max_allowed, time_window_seconds)
        """
        now = time.time()
        max_requests, time_window = self.rate_limits.get(command_type, self.rate_limits["default"])
        
        # Clean old entries
        user_history = self.user_command_history[user_id][command_type]
        cutoff_time = now - time_window
        
        current_usage = len([ts for ts in user_history if ts > cutoff_time])
        
        return current_usage, max_requests, int(time_window)
    
    def reset_user_limits(self, user_id: str):
        """Reset all rate limits for a user (admin function)"""
        if user_id in self.user_command_history:
            del self.user_command_history[user_id]
        self.warned_users.discard(user_id)
        logger.info("SECURITY: Rate limits reset for user %s", user_id)


# Global rate limiter instance
rate_limiter = SimpleRateLimiter()


def check_rate_limit(user_id: str, command_type: str = "default") -> bool:
    """Convenience function to check rate limits"""
    return rate_limiter.check_rate_limit(user_id, command_type)