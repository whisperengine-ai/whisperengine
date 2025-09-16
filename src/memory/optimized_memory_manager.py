"""
Enhanced Memory Manager with Memory Optimization Integration
This shows exactly where the new memory optimization components integrate
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

# Import existing WhisperEngine memory components
from src.memory.memory_manager import UserMemoryManager
from src.memory.integrated_memory_manager import IntegratedMemoryManager
from src.utils.embedding_manager import ExternalEmbeddingManager
from src.llm.llm_client import LLMClient

# Import our new memory optimization components
from src.memory.conversation_summarizer import AdvancedConversationSummarizer
from src.memory.semantic_deduplicator import SemanticDeduplicator
from src.memory.topic_clusterer import AdvancedTopicClusterer  
from src.memory.context_prioritizer import IntelligentContextPrioritizer

logger = logging.getLogger(__name__)

class OptimizedMemoryManager(IntegratedMemoryManager):
    """
    Enhanced memory manager that integrates all memory optimization components
    into the existing WhisperEngine memory system
    
    INTEGRATION POINTS:
    1. store_conversation() - Add summarization and deduplication
    2. retrieve_relevant_memories() - Add context prioritization  
    3. Background optimization - Topic clustering and analytics
    """
    
    def __init__(self, memory_manager: 'UserMemoryManager', **kwargs):
        """Initialize the OptimizedMemoryManager with all optimization components.
        
        Args:
            memory_manager: The base memory manager to wrap
            **kwargs: Additional arguments for optimization components
        """
        # Filter kwargs to only pass what IntegratedMemoryManager expects
        base_kwargs = {}
        optimization_kwargs = {}
        
        # Split kwargs between base manager and optimization components
        for key, value in kwargs.items():
            if key in ['embedding_manager', 'llm_client', 'enable_summarization', 
                      'enable_deduplication', 'enable_clustering', 'enable_prioritization']:
                optimization_kwargs[key] = value
            else:
                base_kwargs[key] = value
        
        # Initialize the base memory manager with filtered kwargs
        super().__init__(memory_manager, **base_kwargs)
        
        # Initialize optimization components using filtered kwargs
        self.llm_client = optimization_kwargs.get('llm_client')
        self.embedding_manager = optimization_kwargs.get('embedding_manager')
        
        # Memory optimization suite
        self.conversation_summarizer = None
        self.semantic_deduplicator = None
        self.topic_clusterer = None
        self.context_prioritizer = None
        
        # Configuration
        self.enable_summarization = optimization_kwargs.get('enable_summarization', True)
        self.enable_deduplication = optimization_kwargs.get('enable_deduplication', True)
        self.enable_clustering = optimization_kwargs.get('enable_clustering', True)
        self.enable_prioritization = optimization_kwargs.get('enable_prioritization', True)
        
        # Initialize optimization components
        self._initialize_optimization_components()
        
        logger.info("OptimizedMemoryManager initialized with memory optimization suite")
    
    def _initialize_optimization_components(self):
        """Initialize all memory optimization components"""
        try:
            if self.enable_summarization and self.llm_client:
                self.conversation_summarizer = AdvancedConversationSummarizer(
                    llm_client=self.llm_client,
                    memory_manager=self.memory_manager,
                    embedding_manager=self.embedding_manager
                )
                logger.debug("✅ Conversation summarizer initialized")
            
            if self.enable_deduplication and self.embedding_manager:
                self.semantic_deduplicator = SemanticDeduplicator(
                    embedding_manager=self.embedding_manager
                )
                logger.debug("✅ Semantic deduplicator initialized")
            
            if self.enable_clustering and self.embedding_manager:
                self.topic_clusterer = AdvancedTopicClusterer(
                    embedding_manager=self.embedding_manager,
                    llm_client=self.llm_client
                )
                logger.debug("✅ Topic clusterer initialized")
            
            if self.enable_prioritization and self.embedding_manager:
                self.context_prioritizer = IntelligentContextPrioritizer(
                    embedding_manager=self.embedding_manager
                )
                logger.debug("✅ Context prioritizer initialized")
                
        except Exception as e:
            logger.error(f"Failed to initialize optimization components: {e}")
    
    # ================================================================
    # INTEGRATION POINT 1: Enhanced Conversation Storage
    # ================================================================
    
    def store_conversation(self, user_id: str, user_message: str, bot_response: str, 
                          channel_id: Optional[str] = None, pre_analyzed_emotion_data: Optional[dict] = None, 
                          metadata: Optional[dict] = None):
        """
        Enhanced conversation storage with optimization integration
        
        WORKFLOW:
        1. Store conversation normally (existing system)
        2. Check if summarization is needed
        3. Run background deduplication if enabled
        4. Update topic clusters
        """
        
        # 1. Store conversation using existing system
        result = super().store_conversation(
            user_id, user_message, bot_response, channel_id, 
            pre_analyzed_emotion_data, metadata
        )
        
        # 2. Background optimization (non-blocking)
        if any([self.enable_summarization, self.enable_deduplication, self.enable_clustering]):
            asyncio.create_task(self._optimize_user_memory_background(
                user_id, user_message, bot_response
            ))
        
        return result
    
    async def _optimize_user_memory_background(self, user_id: str, user_message: str, bot_response: str):
        """Background memory optimization workflow"""
        try:
            # Get recent conversation history for this user
            recent_memories = await self._get_recent_conversation_history(user_id)
            
            # 1. Check if conversation summarization is needed
            if self.conversation_summarizer and len(recent_memories) > 0:
                should_summarize = await self.conversation_summarizer.should_summarize_conversation(
                    user_id, recent_memories
                )
                
                if should_summarize:
                    logger.info(f"Creating conversation summary for user {user_id}")
                    summary = await self.conversation_summarizer.create_conversation_summary(
                        user_id, recent_memories
                    )
                    # Store summary as a memory (this replaces multiple conversation memories)
                    await self._store_conversation_summary(user_id, summary)
            
            # 2. Run periodic deduplication
            if self.semantic_deduplicator:
                user_memories = await self.get_memories_by_user(user_id)
                memory_ids = [mem.get('memory_id', mem.get('id', '')) for mem in user_memories[-20:]]  # Last 20 memories
                
                if memory_ids:
                    dedup_result = self.semantic_deduplicator.optimize_memory_storage(memory_ids)
                    if dedup_result.get('optimization_opportunities', []):
                        logger.debug(f"Found {len(dedup_result['optimization_opportunities'])} optimization opportunities for user {user_id}")
            
            # 3. Update topic clustering
            if self.topic_clusterer:
                # Topic clustering happens in background and doesn't need immediate action
                pass
                
        except Exception as e:
            logger.error(f"Background memory optimization failed for user {user_id}: {e}")
    
    # ================================================================
    # INTEGRATION POINT 2: Enhanced Memory Retrieval
    # ================================================================
    
    def retrieve_relevant_memories(self, user_id: str, query: str, limit: int = 10):
        """
        Enhanced memory retrieval with context prioritization
        
        WORKFLOW:
        1. Get memories from existing system
        2. Apply context prioritization if enabled
        3. Return optimally ranked memories
        """
        
        # 1. Get memories using existing system
        base_memories = super().retrieve_relevant_memories(user_id, query, limit * 2)  # Get more for prioritization
        
        # 2. Apply context prioritization if available
        if self.context_prioritizer and base_memories:
            try:
                # Convert to context format
                context_items = self._convert_memories_to_context(base_memories)
                
                # Apply intelligent prioritization (async in sync context)
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    prioritized_items = loop.run_until_complete(
                        self.context_prioritizer.prioritize_context(
                            query, user_id, context_items, limit
                        )
                    )
                    
                    # Convert back to memory format
                    prioritized_memories = self._convert_context_to_memories(prioritized_items)
                    
                    logger.debug(f"Prioritized {len(prioritized_memories)} memories for user {user_id}")
                    return prioritized_memories
                    
                finally:
                    loop.close()
                    
            except Exception as e:
                logger.warning(f"Context prioritization failed, using base memories: {e}")
        
        # 3. Fallback to base memories
        return base_memories[:limit]
    
    # ================================================================
    # INTEGRATION POINT 3: Background Analytics & Optimization
    # ================================================================
    
    async def run_memory_optimization_cycle(self, user_id: Optional[str] = None):
        """
        Run a complete memory optimization cycle
        
        This can be called periodically or triggered by specific events
        """
        try:
            if user_id:
                # Optimize specific user
                await self._optimize_single_user_memory(user_id)
            else:
                # System-wide optimization (run for all users)
                await self._optimize_all_users_memory()
                
        except Exception as e:
            logger.error(f"Memory optimization cycle failed: {e}")
    
    async def _optimize_single_user_memory(self, user_id: str):
        """Comprehensive optimization for a single user"""
        
        # Get all user memories
        user_memories = await self.get_memories_by_user(user_id)
        
        if not user_memories:
            return
        
        logger.info(f"Running memory optimization for user {user_id} ({len(user_memories)} memories)")
        
        # 1. Topic clustering analysis
        if self.topic_clusterer:
            cluster_stats = self.topic_clusterer.get_clustering_stats()
            logger.debug(f"User {user_id} topic clusters: {cluster_stats['total_clusters']}")
        
        # 2. Deduplication analysis
        if self.semantic_deduplicator:
            memory_ids = [mem.get('memory_id', mem.get('id', '')) for mem in user_memories]
            dedup_result = self.semantic_deduplicator.optimize_memory_storage(memory_ids)
            
            if dedup_result.get('duplicate_groups', []):
                logger.info(f"Found {len(dedup_result['duplicate_groups'])} duplicate groups for user {user_id}")
        
        # 3. Context gap analysis
        if self.context_prioritizer:
            gap_analysis = await self.context_prioritizer.analyze_context_gaps(user_id, "recent activity")
            
            if gap_analysis['coverage_score'] < 0.7:
                logger.info(f"User {user_id} has low context coverage: {gap_analysis['coverage_score']:.2f}")
    
    # ================================================================
    # HELPER METHODS
    # ================================================================
    
    async def _get_recent_conversation_history(self, user_id: str, limit: int = 20) -> List[Dict]:
        """Get recent conversation history for summarization"""
        try:
            # Get recent memories and format as conversation
            recent_memories = await self.get_memories_by_user(user_id)
            
            # Convert to conversation format
            conversation_history = []
            for memory in recent_memories[-limit:]:
                content = memory.get('content', '')
                timestamp = memory.get('timestamp', datetime.now().isoformat())
                
                # Simple heuristic to determine if it's user or bot message
                role = 'user' if 'User:' in content or not content.startswith(('I ', 'Here', 'Based on')) else 'assistant'
                
                conversation_history.append({
                    'user_id': user_id if role == 'user' else 'assistant',
                    'content': content,
                    'timestamp': timestamp,
                    'role': role
                })
            
            return conversation_history
            
        except Exception as e:
            logger.error(f"Failed to get conversation history for user {user_id}: {e}")
            return []
    
    async def _store_conversation_summary(self, user_id: str, summary):
        """Store a conversation summary as a memory"""
        try:
            # Create metadata for summary
            metadata = {
                'type': 'conversation_summary',
                'original_message_count': summary.message_count,
                'compression_ratio': summary.compression_ratio,
                'key_topics': summary.key_topics,
                'timestamp_start': summary.timestamp_start,
                'timestamp_end': summary.timestamp_end
            }
            
            # Store summary as a memory
            self.memory_manager.store_conversation(
                user_id=user_id,
                user_message=f"Conversation Summary: {', '.join(summary.key_topics)}",
                bot_response=summary.summary_text,
                channel_id="",
                pre_analyzed_emotion_data={},
                metadata=metadata
            )
            
            logger.debug(f"Stored conversation summary for user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to store conversation summary: {e}")
    
    def _convert_memories_to_context(self, memories: List[Dict]) -> List[Dict]:
        """Convert memory objects to context format for prioritization"""
        context_items = []
        
        for i, memory in enumerate(memories):
            context_item = {
                'id': memory.get('memory_id', memory.get('id', f'mem_{i}')),
                'content': memory.get('content', ''),
                'timestamp': memory.get('timestamp', datetime.now().isoformat()),
                'metadata': memory.get('metadata', {}),
                'type': memory.get('metadata', {}).get('type', 'conversation')
            }
            
            # Add embedding if available
            if 'embedding' in memory:
                context_item['embedding'] = memory['embedding']
            
            context_items.append(context_item)
        
        return context_items
    
    def _convert_context_to_memories(self, context_items) -> List[Dict]:
        """Convert prioritized context items back to memory format"""
        memories = []
        
        for item in context_items:
            memory = {
                'id': item.item_id,
                'content': item.content,
                'timestamp': item.timestamp,
                'metadata': {
                    'relevance_score': item.final_score,
                    'confidence_level': item.confidence_level,
                    'context_type': item.context_type.value
                }
            }
            memories.append(memory)
        
        return memories
    
    async def _optimize_all_users_memory(self):
        """System-wide memory optimization (careful with resources)"""
        # This would be run periodically for system maintenance
        # Implementation depends on your user management system
        logger.info("System-wide memory optimization not implemented yet")
        pass
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get comprehensive optimization statistics"""
        stats = {
            'summarizer_available': self.conversation_summarizer is not None,
            'deduplicator_available': self.semantic_deduplicator is not None,
            'clusterer_available': self.topic_clusterer is not None,
            'prioritizer_available': self.context_prioritizer is not None,
        }
        
        # Get component-specific stats
        try:
            if self.context_prioritizer:
                prioritization_stats = self.context_prioritizer.get_prioritization_stats()
                stats.update({f'prioritization_{k}': v for k, v in prioritization_stats.items()})
            
            if self.topic_clusterer:
                clustering_stats = self.topic_clusterer.get_clustering_stats()
                stats.update({f'clustering_{k}': v for k, v in clustering_stats.items()})
        except Exception as e:
            logger.debug(f"Error getting component stats: {e}")
        
        return stats


# ================================================================
# INTEGRATION EXAMPLE: How to use in existing WhisperEngine code
# ================================================================

def create_optimized_memory_manager(llm_client=None, embedding_manager=None, memory_manager=None) -> OptimizedMemoryManager:
    """
    Factory function to create an optimized memory manager
    
    USE THIS in your existing bot initialization code:
    
    # In src/core/bot.py or wherever you initialize memory components
    base_memory_manager = UserMemoryManager(...)
    
    # Replace with optimized version
    memory_manager = create_optimized_memory_manager(llm_client, embedding_manager, base_memory_manager)
    """
    
    # Create base memory manager if not provided (your existing initialization)
    if memory_manager is None:
        memory_manager = UserMemoryManager()
    
    # Create optimized version
    optimized_manager = OptimizedMemoryManager(
        memory_manager=memory_manager,
        llm_client=llm_client,
        embedding_manager=embedding_manager,
        enable_summarization=llm_client is not None,
        enable_deduplication=embedding_manager is not None,
        enable_clustering=embedding_manager is not None,
        enable_prioritization=embedding_manager is not None
    )
    
    return optimized_manager


# ================================================================
# BACKGROUND TASK INTEGRATION
# ================================================================

async def run_periodic_memory_optimization(memory_manager: OptimizedMemoryManager, interval_hours: int = 24):
    """
    Background task for periodic memory optimization
    
    ADD THIS to your bot's background tasks:
    
    # In your bot startup code
    asyncio.create_task(run_periodic_memory_optimization(memory_manager))
    """
    while True:
        try:
            logger.info("Starting periodic memory optimization cycle")
            await memory_manager.run_memory_optimization_cycle()
            logger.info("Completed periodic memory optimization cycle")
            
            # Wait for next cycle
            await asyncio.sleep(interval_hours * 3600)
            
        except Exception as e:
            logger.error(f"Periodic memory optimization failed: {e}")
            await asyncio.sleep(3600)  # Wait 1 hour before retry