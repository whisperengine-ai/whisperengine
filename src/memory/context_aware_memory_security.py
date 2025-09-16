"""
Context-Aware Memory Security Module

This module implements security boundaries for memory retrieval to prevent
cross-context information leakage between:
- DMs vs Server Channels
- Different Servers/Guilds  
- Public vs Private Channels
- Different Channel Categories

SECURITY ISSUE ADDRESSED: Cross-Context Memory Leakage (CVSS 8.5)
"""

import logging
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
import hashlib

logger = logging.getLogger(__name__)

class ContextSecurity(Enum):
    """Security levels for different contexts"""
    PRIVATE_DM = "private_dm"           # Highest privacy - DM conversations
    PRIVATE_CHANNEL = "private_channel" # High privacy - Private server channels
    PUBLIC_CHANNEL = "public_channel"   # Medium privacy - Public server channels
    CROSS_SERVER = "cross_server"       # Lowest privacy - Information safe across servers

class MemoryContextType(Enum):
    """Types of memory contexts"""
    DM = "dm"                           # Direct message context
    SERVER_CHANNEL = "server_channel"   # Server channel context
    PRIVATE_CHANNEL = "private_channel" # Private server channel context
    PUBLIC_CHANNEL = "public_channel"   # Public server channel context

@dataclass
class MemoryContext:
    """Represents the context of a memory interaction"""
    context_type: MemoryContextType
    server_id: Optional[str] = None     # Guild/Server ID (None for DMs)
    channel_id: Optional[str] = None    # Channel ID
    is_private: bool = True             # Default to private for safety
    security_level: ContextSecurity = ContextSecurity.PRIVATE_DM  # Default, may be overridden
    
    def __post_init__(self):
        """Set security level based on context type (only if using default)"""
        # Only override if using the default PRIVATE_DM and context suggests otherwise
        if self.security_level == ContextSecurity.PRIVATE_DM and self.context_type != MemoryContextType.DM:
            if self.context_type == MemoryContextType.DM:
                self.security_level = ContextSecurity.PRIVATE_DM
                self.is_private = True
            elif self.context_type == MemoryContextType.PRIVATE_CHANNEL:
                self.security_level = ContextSecurity.PRIVATE_CHANNEL
                self.is_private = True
            elif self.context_type == MemoryContextType.PUBLIC_CHANNEL:
                self.security_level = ContextSecurity.PUBLIC_CHANNEL
                self.is_private = False
            else:  # SERVER_CHANNEL
                self.security_level = ContextSecurity.PUBLIC_CHANNEL
                self.is_private = False

class ContextAwareMemoryManager:
    """
    Secure memory manager that prevents cross-context information leakage
    """
    
    def __init__(self, base_memory_manager):
        """Initialize with base memory manager"""
        self.base_memory_manager = base_memory_manager
        self.user_privacy_settings = {}  # user_id -> privacy preferences
        
        # Define context compatibility matrix
        self.context_compatibility = {
            ContextSecurity.PRIVATE_DM: [ContextSecurity.PRIVATE_DM, ContextSecurity.CROSS_SERVER],
            ContextSecurity.PRIVATE_CHANNEL: [ContextSecurity.PRIVATE_CHANNEL, ContextSecurity.CROSS_SERVER],
            ContextSecurity.PUBLIC_CHANNEL: [ContextSecurity.PUBLIC_CHANNEL, ContextSecurity.CROSS_SERVER],
            ContextSecurity.CROSS_SERVER: [ContextSecurity.CROSS_SERVER]
        }
        
        logger.info("Context-aware memory security manager initialized")
    
    def classify_discord_context(self, message) -> MemoryContext:
        """
        Classify Discord message context for security boundaries
        
        Args:
            message: Discord message object
            
        Returns:
            MemoryContext object with security classification
        """
        try:
            # DM Context
            if message.guild is None:
                return MemoryContext(
                    context_type=MemoryContextType.DM,
                    server_id=None,
                    channel_id=str(message.channel.id),
                    is_private=True,
                    security_level=ContextSecurity.PRIVATE_DM
                )
            
            # Server Context
            server_id = str(message.guild.id)
            channel_id = str(message.channel.id)
            
            # Check if channel is private (permissions-based)
            is_private_channel = self._is_private_channel(message.channel)
            
            if is_private_channel:
                return MemoryContext(
                    context_type=MemoryContextType.PRIVATE_CHANNEL,
                    server_id=server_id,
                    channel_id=channel_id,
                    is_private=True,
                    security_level=ContextSecurity.PRIVATE_CHANNEL
                )
            else:
                return MemoryContext(
                    context_type=MemoryContextType.PUBLIC_CHANNEL,
                    server_id=server_id,
                    channel_id=channel_id,
                    is_private=False,
                    security_level=ContextSecurity.PUBLIC_CHANNEL
                )
                
        except Exception as e:
            logger.error(f"Error classifying context: {e}")
            # Default to most private for safety
            return MemoryContext(
                context_type=MemoryContextType.DM,
                security_level=ContextSecurity.PRIVATE_DM
            )
    
    def _is_private_channel(self, channel) -> bool:
        """
        Determine if a Discord channel should be considered private
        
        Args:
            channel: Discord channel object
            
        Returns:
            True if channel should be treated as private
        """
        try:
            # Check channel permissions - if @everyone can't read, it's private
            everyone_role = channel.guild.default_role
            permissions = channel.permissions_for(everyone_role)
            
            # Private if @everyone cannot read messages
            return not permissions.read_messages
            
        except Exception as e:
            logger.warning(f"Could not determine channel privacy, defaulting to private: {e}")
            return True  # Default to private for safety
    
    def create_context_key(self, user_id: str, context: MemoryContext) -> str:
        """
        Create a unique context key for memory storage/retrieval
        
        Args:
            user_id: User ID
            context: Memory context
            
        Returns:
            Unique context key for this user-context combination
        """
        # Create context-specific identifier
        context_parts = [user_id, context.context_type.value]
        
        if context.server_id:
            context_parts.append(f"server_{context.server_id}")
        if context.channel_id:
            context_parts.append(f"channel_{context.channel_id}")
        
        # Create hash for consistent but secure context identification
        context_string = "|".join(context_parts)
        context_hash = hashlib.sha256(context_string.encode()).hexdigest()[:16]
        
        return f"ctx_{context_hash}"
    
    def get_compatible_contexts(self, current_context: MemoryContext) -> List[ContextSecurity]:
        """
        Get list of context security levels that are compatible with current context
        
        Args:
            current_context: Current memory context
            
        Returns:
            List of compatible security levels
        """
        return self.context_compatibility.get(
            current_context.security_level, 
            [current_context.security_level]
        )
    
    def retrieve_context_aware_memories(self, user_id: str, query: str, context: MemoryContext, limit: int = 10) -> List[Dict]:
        """
        Retrieve memories with context-aware security filtering
        
        Args:
            user_id: User ID
            query: Search query
            context: Current memory context
            limit: Maximum number of memories to retrieve
            
        Returns:
            List of memories filtered by context security
        """
        try:
            # Get all memories from base manager
            all_memories = self.base_memory_manager.retrieve_relevant_memories(user_id, query, limit * 2)
            
            # Filter memories based on context compatibility
            compatible_contexts = self.get_compatible_contexts(context)
            filtered_memories = []
            
            for memory in all_memories:
                memory_context = self._get_memory_context(memory)
                
                # Check if memory context is compatible with current context
                if self._is_context_compatible(memory_context, context, compatible_contexts):
                    filtered_memories.append(memory)
                    
                    # Add context security metadata
                    memory['metadata']['context_filtered'] = True
                    memory['metadata']['current_context'] = context.context_type.value
                    memory['metadata']['current_security_level'] = context.security_level.value
                    # Note: Preserve original security_level, don't overwrite it
                
                if len(filtered_memories) >= limit:
                    break
            
            logger.debug(f"Context filtering: {len(all_memories)} -> {len(filtered_memories)} memories")
            return filtered_memories
            
        except Exception as e:
            logger.error(f"Error in context-aware memory retrieval: {e}")
            # Fallback to most restrictive filtering
            return self._emergency_safe_retrieval(user_id, query, context, limit)
    
    def _get_memory_context(self, memory: Dict) -> MemoryContext:
        """
        Extract context information from stored memory
        
        Args:
            memory: Memory dictionary
            
        Returns:
            MemoryContext object representing where memory was created
        """
        try:
            metadata = memory.get('metadata', {})
            
            # Check for context metadata (added by new system)
            if 'context_type' in metadata:
                return MemoryContext(
                    context_type=MemoryContextType(metadata['context_type']),
                    server_id=metadata.get('server_id'),
                    channel_id=metadata.get('channel_id'),
                    is_private=metadata.get('is_private', True),
                    security_level=ContextSecurity(metadata.get('security_level', 'private_dm'))
                )
            
            # Legacy memory without context metadata - classify conservatively
            # If no context info, assume most private
            return MemoryContext(
                context_type=MemoryContextType.DM,
                security_level=ContextSecurity.PRIVATE_DM
            )
            
        except Exception as e:
            logger.warning(f"Could not determine memory context, assuming private: {e}")
            return MemoryContext(
                context_type=MemoryContextType.DM,
                security_level=ContextSecurity.PRIVATE_DM
            )
    
    def _is_context_compatible(self, memory_context: MemoryContext, 
                             current_context: MemoryContext, 
                             compatible_levels: List[ContextSecurity]) -> bool:
        """
        Check if memory context is compatible with current context
        
        Args:
            memory_context: Context where memory was created
            current_context: Current interaction context
            compatible_levels: List of compatible security levels
            
        Returns:
            True if memory can be shared in current context
        """
        # Memory security level must be in compatible levels
        if memory_context.security_level not in compatible_levels:
            return False
        
        # Same server context check
        if (current_context.server_id and memory_context.server_id and 
            current_context.server_id == memory_context.server_id):
            return True
        
        # DM context check
        if (current_context.context_type == MemoryContextType.DM and 
            memory_context.context_type == MemoryContextType.DM):
            return True
        
        # Cross-server safe content check
        if memory_context.security_level == ContextSecurity.CROSS_SERVER:
            return True
        
        # Default to not compatible for safety
        return False
    
    def _emergency_safe_retrieval(self, user_id: str, query: str, context: MemoryContext, limit: int) -> List[Dict]:
        """
        Emergency fallback that only returns the safest memories
        
        Args:
            user_id: User ID
            query: Search query  
            context: Current context
            limit: Maximum memories to return
            
        Returns:
            List of only the safest memories
        """
        logger.warning("Using emergency safe memory retrieval")
        
        try:
            # Only return memories explicitly marked as cross-server safe
            all_memories = self.base_memory_manager.retrieve_relevant_memories(user_id, query, limit * 3)
            safe_memories = []
            
            for memory in all_memories:
                metadata = memory.get('metadata', {})
                if metadata.get('security_level') == 'cross_server':
                    safe_memories.append(memory)
                    if len(safe_memories) >= limit:
                        break
            
            return safe_memories
            
        except Exception as e:
            logger.error(f"Emergency safe retrieval failed: {e}")
            return []  # Return empty rather than risk data leakage
    
    def enhance_memory_with_context(self, memory_data: Dict, context: MemoryContext) -> Dict:
        """
        Add context metadata to memory before storage
        
        Args:
            memory_data: Memory data to enhance
            context: Context information
            
        Returns:
            Enhanced memory data with context metadata
        """
        if 'metadata' not in memory_data:
            memory_data['metadata'] = {}
        
        # Add context security metadata
        memory_data['metadata'].update({
            'context_type': context.context_type.value,
            'server_id': context.server_id,
            'channel_id': context.channel_id, 
            'is_private': context.is_private,
            'security_level': context.security_level.value,
            'context_timestamp': None  # Could add datetime.now().isoformat() if needed
        })
        
        return memory_data
    
    # ========================================
    # DELEGATION METHODS FOR DROP-IN REPLACEMENT
    # ========================================
    
    def retrieve_relevant_memories(self, user_id: str, query: str, limit: int = 10, context: Optional[MemoryContext] = None) -> List[Dict]:
        """
        Drop-in replacement for base memory manager with context awareness
        
        Args:
            user_id: User ID
            query: Search query
            limit: Maximum number of memories
            context: Optional context (if not provided, will assume most private)
            
        Returns:
            Context-filtered memories
        """
        # If no context provided, assume most private (DM context)
        if context is None:
            context = MemoryContext(
                context_type=MemoryContextType.DM,
                security_level=ContextSecurity.PRIVATE_DM
            )
        
        return self.retrieve_context_aware_memories(user_id, query, context, limit)
    
    def store_conversation(self, user_id: str, user_message: str, bot_response: str, 
                          context: Optional[MemoryContext] = None, **kwargs) -> None:
        """
        Context-aware conversation storage that includes context metadata
        
        Args:
            user_id: User ID
            user_message: User's message
            bot_response: Bot's response
            context: Memory context (if not provided, will try to infer from kwargs)
            **kwargs: Additional arguments passed to base storage method
        """
        try:
            # If context not provided, try to create from channel information
            if context is None and 'channel_id' in kwargs:
                # This is a fallback - ideally context should be passed explicitly
                context = MemoryContext(
                    context_type=MemoryContextType.DM,  # Conservative default
                    channel_id=kwargs['channel_id'],
                    security_level=ContextSecurity.PRIVATE_DM
                )
            
            # Enhance the conversation data with context metadata if context available
            if context:
                # Add context metadata to kwargs for storage
                context_metadata = {
                    'context_type': context.context_type.value,
                    'server_id': context.server_id,
                    'channel_id': context.channel_id,
                    'is_private': context.is_private,
                    'security_level': context.security_level.value
                }
                
                # Merge with existing metadata if present
                if 'metadata' in kwargs:
                    kwargs['metadata'].update(context_metadata)
                else:
                    kwargs['metadata'] = context_metadata
                
                logger.debug(f"Storing conversation with context: {context.context_type.value} (security: {context.security_level.value})")
            
            # Call base storage method
            return self.base_memory_manager.store_conversation(user_id, user_message, bot_response, **kwargs)
            
        except Exception as e:
            logger.error(f"Error in context-aware conversation storage: {e}")
            # Fallback to base storage without context
            return self.base_memory_manager.store_conversation(user_id, user_message, bot_response, **kwargs)
    
    def __getattr__(self, name):
        """
        Delegate all other method calls to the base memory manager
        
        This allows the ContextAwareMemoryManager to be a drop-in replacement
        for the base UserMemoryManager
        """
        # Handle special case for embedding-related attributes that might be None
        if name in ['add_documents_with_embeddings', 'query_with_embeddings']:
            try:
                base_attr = getattr(self.base_memory_manager, name, None)
                # Always return the actual attribute value, even if it's None
                return base_attr
            except AttributeError:
                # If the base manager doesn't have the attribute, return None
                return None
        
        try:
            return getattr(self.base_memory_manager, name)
        except AttributeError:
            # If the attribute doesn't exist on the base manager, 
            # raise AttributeError as expected
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
    
    def __setattr__(self, name, value):
        """
        Delegate attribute assignment to base manager (except for our own attributes)
        """
        # Our own attributes
        if name in ['base_memory_manager', 'user_privacy_settings', 'context_compatibility']:
            super().__setattr__(name, value)
        else:
            # Check if this is a base manager attribute
            if hasattr(self, 'base_memory_manager') and hasattr(self.base_memory_manager, name):
                setattr(self.base_memory_manager, name, value)
            else:
                super().__setattr__(name, value)
