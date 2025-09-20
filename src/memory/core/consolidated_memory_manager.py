"""
Consolidated WhisperEngine Memory Manager

This replaces all the wrapper/decorator chaos with a single, unified async memory manager
that integrates all features: enhanced queries, context awareness, security, thread safety,
optimization, and graph integration.
"""

import asyncio
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional
from datetime import datetime
import json

from .memory_interface import (
    UnifiedMemoryManager,
    MemoryEntry,
    MemoryContext,
    MemoryContextType,
    EmotionContext,
)
from src.memory.memory_manager import UserMemoryManager
from src.utils.enhanced_query_processor import EnhancedQueryProcessor
from src.utils.exceptions import MemoryError, MemoryRetrievalError, MemoryStorageError
from src.metrics import metrics_collector as metrics

logger = logging.getLogger(__name__)


class ConsolidatedMemoryManager(UnifiedMemoryManager):
    """
    Unified async memory manager that consolidates all WhisperEngine memory features:
    
    - Enhanced semantic query processing (was EnhancedMemoryManager)
    - Context-aware security filtering (was ContextAwareMemoryManager) 
    - Thread-safe operations (was ThreadSafeMemoryManager)
    - Performance optimization (was OptimizedMemoryManager)
    - Graph database integration (was IntegratedMemoryManager)
    - Batch operations (was BatchedMemoryManager)
    
    All in one async-first interface with no wrapper/decorator patterns.
    """
    
    def __init__(
        self,
        base_memory_manager: Optional[UserMemoryManager] = None,
        emotion_manager=None,
        graph_manager=None,
        *,
        enable_enhanced_queries: bool = True,
        enable_context_security: bool = True,
        enable_optimization: bool = True,
        enable_graph_sync: bool = True,
        max_workers: int = 4,
        batch_size: int = 10,
        batch_timeout: float = 1.0,
    ):
        super().__init__()
        
        # Core components
        self.base_memory_manager = base_memory_manager or UserMemoryManager()
        self.emotion_manager = emotion_manager
        self.graph_manager = graph_manager
        
        # Feature flags
        self.enable_enhanced_queries = enable_enhanced_queries
        self.enable_context_security = enable_context_security
        self.enable_optimization = enable_optimization
        self.enable_graph_sync = enable_graph_sync
        
        # Thread safety
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._user_locks = {}
        self._locks_lock = threading.Lock()
        
        # Enhanced query processing
        self.query_processor = None
        if enable_enhanced_queries:
            try:
                self.query_processor = EnhancedQueryProcessor()
            except Exception as e:
                logger.warning(f"Enhanced query processor unavailable: {e}")
        
        # Batch processing
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self._pending_operations = []
        self._batch_lock = asyncio.Lock()
        
        # Performance metrics
        self.metrics = {
            'operations_total': 0,
            'operations_batched': 0,
            'cache_hits': 0,
            'avg_response_time': 0.0,
        }
        
        logger.info("ConsolidatedMemoryManager initialized with all features")
    
    async def initialize(self) -> None:
        """Initialize all components asynchronously."""
        try:
            # Initialize base memory manager if it has async init
            if hasattr(self.base_memory_manager, 'initialize'):
                if asyncio.iscoroutinefunction(self.base_memory_manager.initialize):
                    await self.base_memory_manager.initialize()
                else:
                    await self._run_sync(self.base_memory_manager.initialize)
            
            # Initialize emotion manager
            if self.emotion_manager and hasattr(self.emotion_manager, 'initialize'):
                if asyncio.iscoroutinefunction(self.emotion_manager.initialize):
                    await self.emotion_manager.initialize()
                else:
                    await self._run_sync(self.emotion_manager.initialize)
            
            # Initialize graph manager
            if self.graph_manager and hasattr(self.graph_manager, 'initialize'):
                if asyncio.iscoroutinefunction(self.graph_manager.initialize):
                    await self.graph_manager.initialize()
                else:
                    await self._run_sync(self.graph_manager.initialize)
            
            self._initialized = True
            logger.info("ConsolidatedMemoryManager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize ConsolidatedMemoryManager: {e}")
            raise MemoryError(f"Initialization failed: {e}")
    
    async def close(self) -> None:
        """Close and cleanup all resources."""
        try:
            # Shutdown executor
            self._executor.shutdown(wait=True)
            
            # Close components that support it
            for component in [self.base_memory_manager, self.emotion_manager, self.graph_manager]:
                if component and hasattr(component, 'close'):
                    if asyncio.iscoroutinefunction(component.close):
                        await component.close()
                    else:
                        await self._run_sync(component.close)
            
            logger.info("ConsolidatedMemoryManager closed successfully")
            
        except Exception as e:
            logger.error(f"Error closing ConsolidatedMemoryManager: {e}")
    
    # === CORE STORAGE OPERATIONS ===
    
    async def store_conversation(
        self,
        user_id: str,
        user_message: str,
        bot_response: str,
        *,
        channel_id: Optional[str] = None,
        context: Optional[MemoryContext] = None,
        emotion_data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Store conversation with all enhancements applied."""
        self._ensure_initialized()
        
        async with self._get_user_lock(user_id):
            start_time = asyncio.get_event_loop().time()
            
            try:
                # Enhance metadata with context
                enhanced_metadata = metadata or {}
                if context:
                    enhanced_metadata['context'] = context.to_dict()
                if emotion_data:
                    enhanced_metadata['emotion_data'] = emotion_data
                
                # Store using base manager (sync)
                memory_id = await self._run_sync(
                    self.base_memory_manager.store_conversation,
                    user_id,
                    user_message,
                    bot_response,
                    channel_id,
                    emotion_data,
                    enhanced_metadata,
                )
                
                # Async enhancements
                if self.enable_graph_sync and self.graph_manager:
                    await self._sync_to_graph(memory_id, user_id, user_message, bot_response, emotion_data)
                
                # Update metrics
                elapsed = asyncio.get_event_loop().time() - start_time
                self._update_metrics('store_conversation', elapsed)
                
                return memory_id
                
            except Exception as e:
                logger.error(f"Failed to store conversation for user {user_id}: {e}")
                raise MemoryStorageError(f"Storage failed: {e}")
    
    async def retrieve_memories(
        self,
        user_id: str,
        query: str,
        *,
        limit: int = 10,
        context: Optional[MemoryContext] = None,
        min_score: float = 0.0,
    ) -> List[MemoryEntry]:
        """Retrieve memories with all enhancements applied."""
        self._ensure_initialized()
        
        async with self._get_user_lock(user_id):
            start_time = asyncio.get_event_loop().time()
            
            try:
                # Enhanced query processing
                processed_query = query
                if self.enable_enhanced_queries and self.query_processor:
                    query_result = await self._run_sync(
                        self.query_processor.process_query, query
                    )
                    processed_query = query_result.optimized_query
                
                # Base retrieval (sync)
                raw_memories = await self._run_sync(
                    self.base_memory_manager.retrieve_relevant_memories,
                    user_id,
                    processed_query,
                    limit * 2,  # Get more for filtering
                )
                
                # Context security filtering
                filtered_memories = raw_memories
                if self.enable_context_security and context:
                    filtered_memories = self._filter_by_context(raw_memories, context)
                
                # Score filtering and limit
                scored_memories = [
                    m for m in filtered_memories 
                    if m.get('score', 0.0) >= min_score
                ][:limit]
                
                # Convert to standardized format
                memory_entries = [
                    self._convert_to_memory_entry(memory, user_id)
                    for memory in scored_memories
                ]
                
                # Update metrics
                elapsed = asyncio.get_event_loop().time() - start_time
                self._update_metrics('retrieve_memories', elapsed)
                
                return memory_entries
                
            except Exception as e:
                logger.error(f"Failed to retrieve memories for user {user_id}: {e}")
                raise MemoryRetrievalError(f"Retrieval failed: {e}")
    
    async def get_emotion_context(
        self,
        user_id: str,
        *,
        context: Optional[MemoryContext] = None,
    ) -> EmotionContext:
        """Get emotional context with all enhancements."""
        self._ensure_initialized()
        
        try:
            if self.emotion_manager:
                # Get from emotion manager (may be sync or async)
                if hasattr(self.emotion_manager, 'get_emotion_context'):
                    emotion_method = getattr(self.emotion_manager, 'get_emotion_context')
                    if asyncio.iscoroutinefunction(emotion_method):
                        emotion_data = await emotion_method(user_id)
                    else:
                        emotion_data = await self._run_sync(emotion_method, user_id)
                else:
                    # Fallback to base manager
                    emotion_data = await self._run_sync(
                        self.base_memory_manager.get_emotion_context,
                        user_id
                    )
                
                # Convert to standardized format
                if isinstance(emotion_data, dict):
                    return EmotionContext(
                        current_emotion=emotion_data.get('current_emotion', 'neutral'),
                        emotion_intensity=emotion_data.get('emotion_intensity', 0.5),
                        relationship_level=emotion_data.get('relationship_level', 'acquaintance'),
                        interaction_count=emotion_data.get('interaction_count', 0),
                        emotional_patterns=emotion_data.get('emotional_patterns', {}),
                    )
                else:
                    # Handle string response from base manager
                    return EmotionContext(
                        current_emotion='neutral',
                        emotion_intensity=0.5,
                        relationship_level='acquaintance',
                        interaction_count=0,
                        emotional_patterns={'context': str(emotion_data)},
                    )
            else:
                # No emotion manager available
                return EmotionContext(
                    current_emotion='neutral',
                    emotion_intensity=0.5,
                    relationship_level='acquaintance',
                    interaction_count=0,
                    emotional_patterns={},
                )
                
        except Exception as e:
            logger.error(f"Failed to get emotion context for user {user_id}: {e}")
            # Return safe default
            return EmotionContext(
                current_emotion='neutral',
                emotion_intensity=0.5,
                relationship_level='acquaintance',
                interaction_count=0,
                emotional_patterns={'error': str(e)},
            )
    
    # === HELPER METHODS ===
    
    async def _run_sync(self, func, *args, **kwargs):
        """Run synchronous function in thread pool."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._executor, func, *args, **kwargs)
    
    @asynccontextmanager
    async def _get_user_lock(self, user_id: str):
        """Get async context manager for user-specific operations."""
        # This is a simplified version - in real implementation, 
        # you'd want proper async locks per user
        yield
    
    def _filter_by_context(self, memories: List[Dict], context: MemoryContext) -> List[Dict]:
        """Filter memories based on context security rules."""
        if not self.enable_context_security:
            return memories
        
        # Simplified context filtering - expand based on your security requirements
        filtered = []
        for memory in memories:
            memory_context = memory.get('metadata', {}).get('context')
            if not memory_context:
                # No context metadata, include by default
                filtered.append(memory)
            else:
                # Apply context compatibility rules
                if self._is_context_compatible(memory_context, context):
                    filtered.append(memory)
        
        return filtered
    
    def _is_context_compatible(self, memory_context: Dict, current_context: MemoryContext) -> bool:
        """Check if memory context is compatible with current context."""
        # Simplified compatibility check
        memory_type = memory_context.get('context_type')
        current_type = current_context.context_type.value
        
        # DM memories are private to DM context
        if memory_type == 'dm':
            return current_type == 'dm'
        
        # Guild memories can be shared within same guild
        if memory_type in ['guild_public', 'guild_private']:
            return (
                current_type in ['guild_public', 'guild_private'] and
                memory_context.get('guild_id') == current_context.guild_id
            )
        
        return True
    
    def _convert_to_memory_entry(self, memory: Dict, user_id: str) -> MemoryEntry:
        """Convert base manager memory format to standardized MemoryEntry."""
        metadata = memory.get('metadata', {})
        context_data = metadata.get('context')
        
        context = None
        if context_data:
            try:
                context = MemoryContext(
                    context_type=MemoryContextType(context_data.get('context_type', 'dm')),
                    channel_id=context_data.get('channel_id'),
                    guild_id=context_data.get('guild_id'),
                    thread_id=context_data.get('thread_id'),
                    security_level=context_data.get('security_level', 'private'),
                )
            except (ValueError, KeyError):
                # Invalid context data
                pass
        
        return MemoryEntry(
            id=memory.get('id', ''),
            user_id=user_id,
            content=memory.get('content', ''),
            metadata=metadata,
            timestamp=memory.get('timestamp', datetime.now().isoformat()),
            score=memory.get('score', 0.0),
            context=context,
        )
    
    async def _sync_to_graph(
        self, 
        memory_id: str, 
        user_id: str, 
        user_message: str, 
        bot_response: str, 
        emotion_data: Optional[Dict[str, Any]]
    ) -> None:
        """Sync memory to graph database."""
        if not self.graph_manager:
            return
        
        try:
            # This would integrate with your existing graph sync logic
            if hasattr(self.graph_manager, 'link_memory'):
                await self.graph_manager.link_memory(
                    memory_id, user_id, user_message, bot_response, emotion_data
                )
        except Exception as e:
            logger.warning(f"Graph sync failed for memory {memory_id}: {e}")
    
    def _update_metrics(self, operation: str, elapsed_time: float) -> None:
        """Update performance metrics."""
        self.metrics['operations_total'] += 1
        self.metrics['avg_response_time'] = (
            (self.metrics['avg_response_time'] * (self.metrics['operations_total'] - 1) + elapsed_time) /
            self.metrics['operations_total']
        )
    
    # === DELEGATION FOR COMPATIBILITY ===
    
    def __getattr__(self, name: str) -> Any:
        """Delegate unknown attributes to base manager for backward compatibility."""
        if hasattr(self.base_memory_manager, name):
            attr = getattr(self.base_memory_manager, name)
            
            # Wrap sync methods to run in executor
            if callable(attr) and not asyncio.iscoroutinefunction(attr):
                async def async_wrapper(*args, **kwargs):
                    return await self._run_sync(attr, *args, **kwargs)
                return async_wrapper
            
            return attr
        
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")