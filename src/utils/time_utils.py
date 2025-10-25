"""
Time formatting utilities for human-readable timestamps.

Provides functions to convert datetime objects to natural language
relative time strings like "28 minutes ago" or "2 days ago".
"""

from datetime import datetime, timezone
from typing import Union, Optional
import logging

logger = logging.getLogger(__name__)


def format_relative_time(timestamp: Union[datetime, str], now: Optional[datetime] = None) -> str:
    """
    Convert timestamp to human-readable relative time.
    
    Args:
        timestamp: datetime object or ISO string
        now: Optional current time (defaults to datetime.now(UTC))
        
    Returns:
        Human-readable string like "28 minutes ago", "3 hours ago", "2 days ago"
        
    Examples:
        >>> format_relative_time(datetime.now() - timedelta(minutes=5))
        "5 minutes ago"
        
        >>> format_relative_time("2025-10-24T14:32:15.123456Z")
        "2 hours ago"
    """
    try:
        # Handle string timestamps
        if isinstance(timestamp, str):
            # Remove 'Z' and parse as UTC
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        
        # Ensure timezone-aware datetime
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        
        # Get current time
        if now is None:
            now = datetime.now(timezone.utc)
        elif now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        
        # Calculate time difference
        delta = now - timestamp
        seconds = delta.total_seconds()
        
        # Handle future timestamps (shouldn't happen, but be safe)
        if seconds < 0:
            return "just now"
        
        # Format based on time elapsed
        if seconds < 60:
            return "just now"
        elif seconds < 3600:  # Less than 1 hour
            minutes = int(seconds / 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif seconds < 86400:  # Less than 1 day
            hours = int(seconds / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif seconds < 604800:  # Less than 1 week
            days = int(seconds / 86400)
            return f"{days} day{'s' if days != 1 else ''} ago"
        elif seconds < 2592000:  # Less than ~30 days
            weeks = int(seconds / 604800)
            return f"{weeks} week{'s' if weeks != 1 else ''} ago"
        elif seconds < 31536000:  # Less than 1 year
            months = int(seconds / 2592000)
            return f"{months} month{'s' if months != 1 else ''} ago"
        else:
            years = int(seconds / 31536000)
            return f"{years} year{'s' if years != 1 else ''} ago"
            
    except (ValueError, AttributeError, TypeError) as e:
        logger.warning("Failed to format relative time for %s: %s", timestamp, e)
        # Fallback to original timestamp string if possible
        if isinstance(timestamp, str):
            return timestamp
        return str(timestamp)


def format_relative_time_short(timestamp: Union[datetime, str], now: Optional[datetime] = None) -> str:
    """
    Convert timestamp to short human-readable format (for compact display).
    
    Args:
        timestamp: datetime object or ISO string
        now: Optional current time (defaults to datetime.now(UTC))
        
    Returns:
        Short format like "5m ago", "3h ago", "2d ago"
        
    Examples:
        >>> format_relative_time_short(datetime.now() - timedelta(minutes=5))
        "5m ago"
        
        >>> format_relative_time_short("2025-10-24T14:32:15.123456Z")
        "2h ago"
    """
    try:
        # Handle string timestamps
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        
        # Ensure timezone-aware datetime
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        
        # Get current time
        if now is None:
            now = datetime.now(timezone.utc)
        elif now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        
        # Calculate time difference
        delta = now - timestamp
        seconds = delta.total_seconds()
        
        # Handle future timestamps
        if seconds < 0:
            return "now"
        
        # Short format based on time elapsed
        if seconds < 60:
            return "now"
        elif seconds < 3600:  # Less than 1 hour
            minutes = int(seconds / 60)
            return f"{minutes}m ago"
        elif seconds < 86400:  # Less than 1 day
            hours = int(seconds / 3600)
            return f"{hours}h ago"
        elif seconds < 604800:  # Less than 1 week
            days = int(seconds / 86400)
            return f"{days}d ago"
        elif seconds < 2592000:  # Less than ~30 days
            weeks = int(seconds / 604800)
            return f"{weeks}w ago"
        elif seconds < 31536000:  # Less than 1 year
            months = int(seconds / 2592000)
            return f"{months}mo ago"
        else:
            years = int(seconds / 31536000)
            return f"{years}y ago"
            
    except (ValueError, AttributeError, TypeError) as e:
        logger.warning("Failed to format short relative time for %s: %s", timestamp, e)
        return "unknown"


def get_oldest_memory_age(memories: list) -> str:
    """
    Get human-readable age of oldest memory from a list.
    
    Args:
        memories: List of memory dictionaries with 'timestamp' field
        
    Returns:
        Human-readable age string or "none" if no memories
        
    Example:
        >>> memories = [
        ...     {"timestamp": "2025-10-20T10:00:00Z", "content": "..."},
        ...     {"timestamp": "2025-10-23T15:00:00Z", "content": "..."}
        ... ]
        >>> get_oldest_memory_age(memories)
        "4 days ago"
    """
    if not memories:
        return "none"
    
    try:
        # Find oldest timestamp
        oldest = None
        for memory in memories:
            timestamp = memory.get('timestamp')
            if timestamp:
                if isinstance(timestamp, str):
                    timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                
                if oldest is None or timestamp < oldest:
                    oldest = timestamp
        
        if oldest:
            return format_relative_time(oldest)
        return "unknown"
        
    except (ValueError, AttributeError, TypeError, KeyError) as e:
        logger.warning("Failed to get oldest memory age: %s", e)
        return "unknown"
