#!/usr/bin/env python3
"""
Hierarchical Memory Adapter for WhisperEngine Bot Handlers
Bridges hierarchical memory system with existing bot handler interface

This adapter implements the MemoryManagerProtocol to ensure consistent
async interfaces across all memory operations.
"""

import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

# Import memory context classes for Discord context classification
from src.memory.context_aware_memory_security import (
    MemoryContext, 
    MemoryContextType, 
    ContextSecurity
)

# Import the standardized protocol
from src.memory.memory_protocol import MemoryManagerProtocol

logger = logging.getLogger(__name__)

class HierarchicalMemoryAdapter:
    """
    Adapter that wraps HierarchicalMemoryManager to provide 
    the same interface as the original memory managers that 
    bot handlers expect.
    
    Implements MemoryManagerProtocol for consistent async interfaces.
    """
    
    def __init__(self, hierarchical_memory_manager):
        self.hierarchical_memory_manager = hierarchical_memory_manager
        self.logger = logger
        
    # === CORE STORAGE METHODS ===
    
    async def store_conversation_safe(
        self, 
        user_id: str, 
        user_message: str, 
        bot_response: str, 
        channel_id: Optional[str] = None,
        pre_analyzed_emotion_data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs  # Accept any additional parameters for compatibility
    ) -> bool:
        """Store conversation using hierarchical memory system"""
        try:
            # Merge all metadata including channel_id and emotion data
            full_metadata = metadata or {}
            
            if channel_id:
                full_metadata['channel_id'] = channel_id
                
            if pre_analyzed_emotion_data:
                full_metadata['emotion_data'] = pre_analyzed_emotion_data
                
            # Include any additional kwargs in metadata
            for key, value in kwargs.items():
                if key not in ['user_id', 'user_message', 'bot_response']:
                    full_metadata[key] = value
            
            await self.hierarchical_memory_manager.store_conversation(
                user_id=user_id,
                user_message=user_message, 
                bot_response=bot_response,
                metadata=full_metadata
            )
            return True
        except Exception as e:
            self.logger.error("Failed to store conversation: %s", str(e))
            return False
    
    # === CONTEXT RETRIEVAL METHODS ===
    
    async def retrieve_context_aware_memories(
        self, 
        user_id: str, 
        query: Optional[str] = None,  # New parameter name
        current_query: Optional[str] = None,  # Legacy parameter name for compatibility
        max_memories: int = 10,
        limit: Optional[int] = None,  # Alternative parameter name for compatibility
        **kwargs  # Accept any additional parameters
    ) -> List[Dict[str, Any]]:
        """Retrieve contextually relevant memories"""
        try:
            # Use the new 'query' parameter if provided, otherwise fall back to 'current_query'
            actual_query = query if query is not None else current_query
            if actual_query is None:
                raise ValueError("Either 'query' or 'current_query' parameter must be provided")
            
            # Use limit if provided, otherwise use max_memories
            actual_limit = limit if limit is not None else max_memories
            
            context = await self.hierarchical_memory_manager.get_conversation_context(
                user_id=user_id,
                current_query=actual_query
            )
            
            # Convert hierarchical context to expected format
            memories = []
            
            # Add recent messages
            for msg in context.recent_messages[:max_memories//2]:
                memories.append({
                    'content': f"User: {msg.get('user_message', '')}\nBot: {msg.get('bot_response', '')}",
                    'timestamp': msg.get('timestamp', datetime.now().isoformat()),
                    'relevance_score': 0.9,  # Recent = high relevance
                    'memory_type': 'recent_conversation'
                })
            
            # Add semantic summaries  
            for summary in context.semantic_summaries[:max_memories//2]:
                memories.append({
                    'content': summary.get('summary', ''),
                    'timestamp': summary.get('timestamp', datetime.now().isoformat()),
                    'relevance_score': summary.get('relevance_score', 0.7),
                    'memory_type': 'semantic_summary'
                })
                
            return memories[:max_memories]
            
        except Exception as e:
            self.logger.error("Failed to retrieve context-aware memories: %s", str(e))
            return []
    
    async def retrieve_relevant_memories(
        self, 
        user_id: str, 
        query: str, 
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve memories relevant to query - SEMANTIC SEARCH ONLY
        
        🚨 IMPORTANT: This method is for SEMANTIC SEARCH only!
        For conversation history, use get_recent_conversations() instead.
        """
        
        # HARD GUARD: Prevent conversation history abuse
        conversation_keywords = [
            'conversation', 'recent messages', 'chat history', 'message history',
            'recent chat', 'conversation history', 'last messages', 'recent talk'
        ]
        
        if any(keyword in query.lower() for keyword in conversation_keywords):
            raise ValueError(
                f"❌ DEPRECATED: retrieve_relevant_memories() called with conversation query: '{query}'\n"
                f"🔄 Use get_recent_conversations(user_id, limit) for conversation history instead!\n"
                f"💡 This method is for SEMANTIC SEARCH only - not conversation retrieval."
            )
        
        try:
            context = await self.hierarchical_memory_manager.get_conversation_context(
                user_id=user_id,
                current_query=query
            )
            
            # Combine all context types
            memories = []
            
            # Add semantic matches (highest priority for query relevance)
            for item in context.semantic_summaries[:limit]:
                memories.append({
                    'content': item.get('summary', ''),
                    'relevance_score': item.get('relevance_score', 0.8),
                    'timestamp': item.get('timestamp', datetime.now().isoformat()),
                    'memory_type': 'semantic'
                })
            
            # Add related topics
            for topic in context.related_topics[:limit]:
                memories.append({
                    'content': f"Topic: {topic.get('topic', '')}", 
                    'relevance_score': topic.get('relevance_score', 0.6),
                    'timestamp': topic.get('timestamp', datetime.now().isoformat()),
                    'memory_type': 'topical'
                })
                
            return memories[:limit]
            
        except Exception as e:
            self.logger.error("Failed to retrieve relevant memories: %s", str(e))
            return []
    
    # === CONVERSATION HISTORY METHODS ===
    
    async def get_recent_conversations(
        self, 
        user_id: str, 
        limit: int = 5,
        context_filter: str | None = None
    ) -> List[Dict[str, Any]]:
        """Get recent conversation history
        
        Args:
            user_id: User ID to get conversations for
            limit: Maximum number of conversations to return
            context_filter: Optional context filter (currently unused, for future filtering by context)
        """
        try:
            conversation_context = await self.hierarchical_memory_manager.get_conversation_context(
                user_id=user_id,
                current_query=""  # Empty query for just recent history
            )
            
            conversations = []
            for msg in conversation_context.recent_messages[:limit]:
                conversations.append({
                    'user_message': msg.get('user_message', ''),
                    'bot_response': msg.get('bot_response', ''),
                    'timestamp': msg.get('timestamp', datetime.now().isoformat()),
                    'metadata': msg.get('metadata', {})
                })
                
            return conversations
            
        except Exception as e:
            self.logger.error("Failed to get recent conversations: %s", str(e))
            return []
    
    # === EMOTION & CONTEXT METHODS ===
    
    async def get_emotion_context(self, user_id: str) -> Dict[str, Any]:
        """Get emotional context for user"""
        try:
            context = await self.hierarchical_memory_manager.get_conversation_context(
                user_id=user_id,
                current_query="emotion mood feeling"
            )
            
            # Extract emotional indicators from recent conversations
            emotion_indicators = []
            for msg in context.recent_messages[:3]:
                if any(word in msg.get('user_message', '').lower() 
                      for word in ['happy', 'sad', 'angry', 'excited', 'worried', 'feel']):
                    emotion_indicators.append(msg.get('user_message', ''))
            
            return {
                'recent_emotions': emotion_indicators,
                'context_available': len(emotion_indicators) > 0,
                'last_emotional_exchange': emotion_indicators[0] if emotion_indicators else None
            }
            
        except Exception as e:
            self.logger.error("Failed to get emotion context: %s", str(e))
            return {'recent_emotions': [], 'context_available': False}
    
    async def get_memories_by_user(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve all memories for a specific user"""
        try:
            # Get conversation context which includes recent memories
            context = await self.hierarchical_memory_manager.get_conversation_context(
                user_id=user_id,
                current_query=""  # Empty query to get general user memories
            )
            
            # Extract memories from context
            memories = []
            
            # Add recent messages
            for msg in context.recent_messages[:limit]:
                memory = {
                    'user_id': user_id,
                    'content': msg.get('user_message', ''),
                    'response': msg.get('bot_response', ''),
                    'timestamp': msg.get('timestamp', ''),
                    'metadata': msg.get('metadata', {}),
                    'source': 'conversation'
                }
                memories.append(memory)
            
            # Add semantic memories if available
            if hasattr(context, 'semantic_memories') and context.semantic_memories:
                for semantic_mem in context.semantic_memories[:limit//2]:
                    memory = {
                        'user_id': user_id,
                        'content': semantic_mem.get('content', ''),
                        'metadata': semantic_mem.get('metadata', {}),
                        'source': 'semantic',
                        'relevance_score': semantic_mem.get('score', 0.0)
                    }
                    memories.append(memory)
            
            # Trim to limit
            return memories[:limit]
            
        except Exception as e:
            self.logger.error("Failed to get memories by user: %s", str(e))
            return []
    
    async def get_phase4_response_context(
        self, 
        user_id: str, 
        current_message: str
    ) -> Dict[str, Any]:
        """Get comprehensive context for Phase 4 response generation"""
        try:
            context = await self.hierarchical_memory_manager.get_conversation_context(
                user_id=user_id,
                current_query=current_message
            )
            
            return {
                'recent_conversations': context.recent_messages[:5],
                'semantic_context': context.semantic_summaries[:3],
                'topic_context': context.related_topics[:3],
                'assembly_time_ms': context.assembly_metadata.get('total_time_ms', 0),
                'context_quality': 'hierarchical_memory',
                'tiers_used': context.assembly_metadata.get('tiers_used', [])
            }
            
        except Exception as e:
            self.logger.error("Failed to get Phase 4 response context: %s", str(e))
            return {
                'recent_conversations': [],
                'semantic_context': [],
                'topic_context': [],
                'assembly_time_ms': 0,
                'context_quality': 'error'
            }
    
    # === COMPATIBILITY METHODS ===
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get memory collection statistics"""
        return {
            'memory_type': 'hierarchical_4_tier',
            'tiers': ['redis_cache', 'postgresql_archive', 'chromadb_semantic', 'neo4j_graph'],
            'estimated_performance': '<100ms context assembly',
            'features': ['semantic_search', 'topic_modeling', 'relationship_mapping']
        }
    
    # === HEALTH & MONITORING ===
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of hierarchical memory system"""
        try:
            return await self.hierarchical_memory_manager.health_check()
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    # === DISCORD CONTEXT CLASSIFICATION ===
    
    def classify_discord_context(self, message) -> MemoryContext:
        """
        Classify Discord message context for security boundaries
        Extracted from context_aware_memory_security.py for compatibility
        
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
                    security_level=ContextSecurity.PRIVATE_DM,
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
                    security_level=ContextSecurity.PRIVATE_CHANNEL,
                )
            else:
                return MemoryContext(
                    context_type=MemoryContextType.PUBLIC_CHANNEL,
                    server_id=server_id,
                    channel_id=channel_id,
                    is_private=False,
                    security_level=ContextSecurity.PUBLIC_CHANNEL,
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
        Check if a Discord channel is private based on permissions
        Simplified implementation for adapter compatibility
        """
        try:
            # Basic heuristic: if channel has specific permission overwrites 
            # or is a thread/DM, consider it private
            if hasattr(channel, 'overwrites') and len(channel.overwrites) > 0:
                return True
            
            # Thread channels are typically more private
            if hasattr(channel, 'parent') and channel.parent:
                return True
                
            return False
            
        except Exception:
            # Default to private for safety
            return True
    
    # === STANDARDIZED INTERFACE METHODS ===
    
    async def store_conversation(
        self, 
        user_id: str, 
        user_message: str, 
        bot_response: str, 
        channel_id: Optional[str] = None,
        pre_analyzed_emotion_data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> bool:
        """Standard store_conversation interface - delegates to store_conversation_safe"""
        return await self.store_conversation_safe(
            user_id=user_id,
            user_message=user_message,
            bot_response=bot_response,
            channel_id=channel_id,
            pre_analyzed_emotion_data=pre_analyzed_emotion_data,
            metadata=metadata,
            **kwargs
        )
    
    async def get_conversation_history(
        self, 
        user_id: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Standard conversation history interface"""
        return await self.get_recent_conversations(user_id=user_id, limit=limit)
    
    # === DELEGATION TO UNDERLYING MANAGER ===
    
    def __getattr__(self, name):
        """Delegate unknown method calls to underlying hierarchical memory manager"""
        if hasattr(self.hierarchical_memory_manager, name):
            return getattr(self.hierarchical_memory_manager, name)
        else:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")


def create_hierarchical_memory_adapter(hierarchical_memory_manager):
    """Factory function to create hierarchical memory adapter"""
    return HierarchicalMemoryAdapter(hierarchical_memory_manager)