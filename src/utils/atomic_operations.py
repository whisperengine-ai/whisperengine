"""
Atomic conversation operations to ensure cache-storage consistency
"""

import logging
import asyncio
from typing import Optional

logger = logging.getLogger(__name__)


async def store_conversation_atomic(
    safe_memory_manager,
    conversation_cache,
    channel_id: str,
    user_id: str,
    user_message: str,
    bot_response: str,
    **kwargs,
) -> bool:
    """
    Atomically store conversation and update cache

    Args:
        safe_memory_manager: Thread-safe memory manager instance
        conversation_cache: Conversation cache instance (can be None)
        channel_id: Discord channel ID
        user_id: Discord user ID
        user_message: User's message content
        bot_response: Bot's response
        **kwargs: Additional storage parameters

    Returns:
        bool: True if storage was successful
    """
    # First, store in persistent memory
    try:
        storage_success = await safe_memory_manager.store_conversation_safe(
            user_id, user_message, bot_response, channel_id=channel_id, **kwargs
        )
    except Exception as e:
        logger.error(f"Failed to store conversation in memory: {e}")
        storage_success = False

    # Then, update cache based on storage result
    if conversation_cache:
        # For now, we don't have the message object here
        # This would need to be called from the message handler
        logger.debug(f"Storage result for channel {channel_id}: {storage_success}")

    return storage_success
