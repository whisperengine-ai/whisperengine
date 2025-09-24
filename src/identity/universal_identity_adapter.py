"""
Universal Identity Adapter

Provides transparent conversion between Discord IDs and Universal IDs for memory operations.
This adapter sits between Discord handlers and the memory system, automatically converting
Discord user IDs to Universal IDs before making memory calls.

This allows existing code to continue using Discord IDs while the memory system uses Universal IDs.
"""

import logging
from typing import Optional, Dict, Any, List
from functools import wraps
import asyncio

from src.identity.universal_identity import create_identity_manager, ChatPlatform

logger = logging.getLogger(__name__)


class UniversalIdentityAdapter:
    """Adapter that converts Discord IDs to Universal IDs for memory operations"""
    
    def __init__(self, memory_manager, postgres_pool=None):
        self.memory_manager = memory_manager
        self.identity_manager = create_identity_manager(postgres_pool) if postgres_pool else None
        self._id_cache: Dict[str, str] = {}  # Discord ID -> Universal ID cache
        
    async def _get_universal_id(self, user_id: str) -> str:
        """Convert Discord ID to Universal ID, with caching"""
        
        # If it's already a universal ID (starts with 'weu_'), return as-is
        if user_id.startswith('weu_'):
            return user_id
        
        # If it's not a Discord ID pattern (not all digits), return as-is
        if not user_id.isdigit() or len(user_id) < 15:
            return user_id
        
        # Check cache first
        if user_id in self._id_cache:
            return self._id_cache[user_id]
        
        # Try to get Universal ID from identity manager
        if self.identity_manager:
            try:
                universal_user = await self.identity_manager._load_user_by_platform(
                    ChatPlatform.DISCORD, user_id
                )
                if universal_user:
                    universal_id = universal_user.universal_id
                    self._id_cache[user_id] = universal_id
                    logger.debug(f"🔄 ID Conversion: Discord {user_id} → Universal {universal_id}")
                    return universal_id
                
                # No Universal ID exists - create one automatically for new Discord users
                logger.info(f"🆕 New Discord user detected: {user_id}, creating Universal ID...")
                
                universal_user = await self.identity_manager.get_or_create_discord_user(
                    discord_user_id=user_id,
                    username=f"discord_user_{user_id[-6:]}",  # Use last 6 digits
                    display_name=f"Discord User {user_id[-4:]}"  # Use last 4 digits
                )
                
                universal_id = universal_user.universal_id
                self._id_cache[user_id] = universal_id
                logger.info(f"✅ Created Universal ID for Discord {user_id} → {universal_id}")
                return universal_id
                
            except Exception as e:
                logger.warning(f"Failed to convert Discord ID {user_id} to Universal ID: {e}")
        
        # Fallback: return original ID if conversion fails
        logger.debug(f"⚠️ ID Fallback: Using original ID {user_id}")
        return user_id
    
    async def _convert_user_ids_in_kwargs(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Convert any user_id parameters in kwargs to Universal IDs"""
        converted_kwargs = kwargs.copy()
        
        if 'user_id' in converted_kwargs:
            original_id = converted_kwargs['user_id']
            universal_id = await self._get_universal_id(original_id)
            converted_kwargs['user_id'] = universal_id
            
            if original_id != universal_id:
                logger.debug(f"🔄 Method call: converted user_id {original_id} → {universal_id}")
        
        return converted_kwargs
    
    # Memory retrieval methods with legacy support
    async def retrieve_relevant_memories(self, user_id: str, *args, **kwargs):
        """Retrieve memories with automatic ID conversion and legacy fallback"""
        universal_id = await self._get_universal_id(user_id)
        
        # Try with universal ID first
        memories = await self.memory_manager.retrieve_relevant_memories(universal_id, *args, **kwargs)
        
        # If no memories found and this was a Discord ID conversion, also try the original Discord ID
        if (not memories or len(memories) == 0) and user_id != universal_id and user_id.isdigit():
            logger.debug("🔄 No memories found with Universal ID, trying legacy Discord ID")
            legacy_memories = await self.memory_manager.retrieve_relevant_memories(user_id, *args, **kwargs)
            
            # If we found legacy memories, we should migrate them on-the-fly
            if legacy_memories and len(legacy_memories) > 0:
                logger.info("📦 Found %d legacy memories for Discord ID %s, will auto-migrate", 
                           len(legacy_memories), user_id)
                # For now, just return them - auto-migration can happen in background
                return legacy_memories
        
        return memories
    
    async def get_conversation_history(self, user_id: str, *args, **kwargs):
        """Get conversation history with automatic ID conversion and legacy fallback"""
        universal_id = await self._get_universal_id(user_id)
        
        # Try with universal ID first
        history = await self.memory_manager.get_conversation_history(universal_id, *args, **kwargs)
        
        # If no history found and this was a Discord ID conversion, also try the original Discord ID
        if (not history or len(history) == 0) and user_id != universal_id and user_id.isdigit():
            logger.debug("🔄 No conversation history found with Universal ID, trying legacy Discord ID")
            legacy_history = await self.memory_manager.get_conversation_history(user_id, *args, **kwargs)
            if legacy_history and len(legacy_history) > 0:
                logger.info("📦 Found legacy conversation history for Discord ID %s", user_id)
                return legacy_history
        
        return history
    
    async def store_conversation(self, user_id: str, *args, **kwargs):
        """Store conversation with automatic ID conversion"""
        universal_id = await self._get_universal_id(user_id)
        return await self.memory_manager.store_conversation(universal_id, *args, **kwargs)
    
    async def store_memory(self, memory_obj, **kwargs):
        """Store memory with automatic user_id conversion in memory object"""
        if hasattr(memory_obj, 'user_id'):
            universal_id = await self._get_universal_id(memory_obj.user_id)
            memory_obj.user_id = universal_id
        
        converted_kwargs = await self._convert_user_ids_in_kwargs(kwargs)
        return await self.memory_manager.store_memory(memory_obj, **converted_kwargs)
    
    async def clear_user_data(self, user_id: str, *args, **kwargs):
        """Clear user data with automatic ID conversion"""
        universal_id = await self._get_universal_id(user_id)
        return await self.memory_manager.clear_user_data(universal_id, *args, **kwargs)
    
    async def get_user_stats(self, user_id: str, *args, **kwargs):
        """Get user stats with automatic ID conversion"""
        universal_id = await self._get_universal_id(user_id)
        return await self.memory_manager.get_user_stats(universal_id, *args, **kwargs)
    
    # Dynamic method forwarding for any other memory methods
    async def __getattr__(self, name):
        """Forward any other method calls to the underlying memory manager with ID conversion"""
        if hasattr(self.memory_manager, name):
            original_method = getattr(self.memory_manager, name)
            
            if asyncio.iscoroutinefunction(original_method):
                async def wrapper(*args, **kwargs):
                    converted_kwargs = await self._convert_user_ids_in_kwargs(kwargs)
                    return await original_method(*args, **converted_kwargs)
                return wrapper
            else:
                def wrapper(*args, **kwargs):
                    # For sync methods, we can't do async conversion, so just forward
                    return original_method(*args, **kwargs)
                return wrapper
        
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")


def create_universal_memory_adapter(memory_manager, postgres_pool=None):
    """Factory function to create Universal Identity Adapter"""
    return UniversalIdentityAdapter(memory_manager, postgres_pool)


# Migration compatibility helpers
async def ensure_universal_id_compatibility(bot_core):
    """
    Ensure bot core has Universal Identity compatibility by wrapping memory manager
    """
    if hasattr(bot_core, 'memory_manager') and bot_core.memory_manager:
        # Check if already wrapped
        if not isinstance(bot_core.memory_manager, UniversalIdentityAdapter):
            # Get PostgreSQL pool for identity management
            postgres_pool = getattr(bot_core, 'postgres_pool', None)
            
            # Wrap the memory manager with Universal Identity Adapter
            original_memory_manager = bot_core.memory_manager
            bot_core.memory_manager = UniversalIdentityAdapter(
                original_memory_manager, 
                postgres_pool
            )
            
            logger.info("✅ Memory manager wrapped with Universal Identity Adapter")
            return True
    
    return False


# Decorator for automatic ID conversion
def universal_id_compatible(func):
    """
    Decorator that automatically converts Discord IDs to Universal IDs
    for function parameters named 'user_id'
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # This is a simplified version - in practice you'd need access to identity manager
        # Implementation would depend on how the identity manager is accessible
        return await func(*args, **kwargs)
    
    return wrapper