"""
Memory Manager Protocol Definition
Standardizes interface for all WhisperEngine memory manager implementations

This protocol enables A/B testing and future memory system innovations
while maintaining consistent async interfaces.
"""

import logging
from typing import Protocol, List, Dict, Any, Optional, Union

logger = logging.getLogger(__name__)


class MemoryManagerProtocol(Protocol):
    """
    Protocol that defines the standardized interface for all WhisperEngine memory managers.
    
    This protocol ensures that all memory manager implementations provide consistent
    async interfaces for core operations, enabling easy A/B testing and system swapping.
    
    Key Design Principles:
    - All core methods are async to support WhisperEngine's scatter-gather concurrency model
    - Consistent parameter signatures across implementations  
    - Support for both legacy and new parameter names for backward compatibility
    """
    
    # === CORE STORAGE OPERATIONS ===
    
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
        """Store a conversation exchange between user and bot."""
        ...
    
    # === MEMORY RETRIEVAL OPERATIONS ===
    
    async def retrieve_relevant_memories(
        self,
        user_id: str,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Retrieve memories relevant to the given query."""
        ...
    
    async def retrieve_relevant_memories_fidelity_first(
        self,
        user_id: str,
        query: str,
        limit: int = 10,
        full_fidelity: bool = True,
        intelligent_ranking: bool = True,
        graduated_filtering: bool = True,
        preserve_character_nuance: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Retrieve memories with fidelity-first approach.
        
        This method implements character authenticity preservation:
        - Start with complete context preservation
        - Use intelligent semantic ranking instead of arbitrary truncation
        - Apply graduated filtering only when context limits are exceeded
        - Preserve character-specific memory nuance throughout
        """
        ...
    
    async def retrieve_context_aware_memories(
        self,
        user_id: str,
        query: Optional[str] = None,
        current_query: Optional[str] = None,  # Legacy compatibility
        max_memories: int = 10,
        limit: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Retrieve contextually relevant memories with enhanced context awareness."""
        ...
    
    # === CONVERSATION HISTORY ===
    
    async def get_conversation_history(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent conversation history for a user."""
        ...
    
    # === EMOTION & CONTEXT ===
    
    async def get_emotion_context(
        self,
        user_id: str
    ) -> Union[str, Dict[str, Any]]:
        """Get emotional context for a user."""
        ...
    
    # === EMBEDDING OPERATIONS ===
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for given text."""
        ...
    
    # === HEALTH & STATUS ===
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the memory system."""
        ...
    
    async def get_last_interaction_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about the very last interaction with this user, regardless of time window.
        Used for calculating 'time since last chat' context.
        """
        ...


def create_memory_manager(memory_type: str = "vector", **config) -> MemoryManagerProtocol:
    """
    Factory function to create memory manager instances of different types.
    
    Args:
        memory_type: Type of memory manager to create
        **config: Configuration parameters for the memory manager
        
    Returns:
        Memory manager implementing MemoryManagerProtocol
    """
    if memory_type == "hierarchical":
        # REMOVED: Hierarchical memory system has been replaced by vector-native memory
        # as per MEMORY_ARCHITECTURE_V2.md
        raise ValueError(
            "Hierarchical memory system has been REMOVED and replaced by vector-native memory. "
            "See MEMORY_ARCHITECTURE_V2.md for the new vector-native implementation. "
            "Use memory_type='vector' instead."
        )
    
    elif memory_type == "test_mock":
        # Mock implementation for testing
        from unittest.mock import AsyncMock
        
        class MockMemoryManager:
            """Mock memory manager for testing."""
            
            async def store_conversation(self, user_id: str, user_message: str, bot_response: str, 
                                       channel_id: Optional[str] = None, 
                                       pre_analyzed_emotion_data: Optional[Dict[str, Any]] = None,
                                       metadata: Optional[Dict[str, Any]] = None, **kwargs) -> bool:
                return True
            
            async def retrieve_relevant_memories(self, user_id: str, query: str, limit: int = 10) -> List[Dict[str, Any]]:
                return []
            
            async def retrieve_relevant_memories_fidelity_first(
                self, user_id: str, query: str, limit: int = 10,
                full_fidelity: bool = True, intelligent_ranking: bool = True,
                graduated_filtering: bool = True, preserve_character_nuance: bool = True
            ) -> List[Dict[str, Any]]:
                return []
            
            async def store_fact(self, user_id: str, fact: str, context: str, 
                               confidence: float = 1.0, metadata: Optional[Dict[str, Any]] = None) -> bool:
                return True
            
            async def retrieve_facts(self, user_id: str, query: str, limit: int = 10) -> List[Dict[str, Any]]:
                return []
            
            async def update_user_profile(self, user_id: str, profile_data: Dict[str, Any]) -> bool:
                return True
            
            async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
                return {}
            
            async def get_conversation_history(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
                return []
            
            async def search_memories(self, user_id: str, query: str, memory_types: Optional[List[str]] = None,
                                    limit: int = 10) -> List[Dict[str, Any]]:
                return []
            
            async def update_emotional_context(self, user_id: str, emotion_data: Dict[str, Any]) -> bool:
                return True
            
            async def get_emotional_context(self, user_id: str) -> Dict[str, Any]:
                return {}
            
            async def retrieve_context_aware_memories(self, user_id: str, query: Optional[str] = None,
                                            current_query: Optional[str] = None, max_memories: int = 10,
                                            limit: Optional[int] = None, context: Optional[Dict[str, Any]] = None,
                                            **kwargs) -> List[Dict[str, Any]]:
                return []
            
            async def get_emotion_context(self, user_id: str) -> Union[str, Dict[str, Any]]:
                return {}
                
            async def generate_embedding(self, text: str) -> List[float]:
                # Return a mock 384-dimensional embedding vector
                return [0.0] * 384
            
            async def health_check(self) -> Dict[str, Any]:
                return {"status": "healthy", "type": "mock"}
            
            async def get_last_interaction_info(self, user_id: str) -> Optional[Dict[str, Any]]:
                return None
        
        return MockMemoryManager()
    
    elif memory_type == "vector":
        # Vector-native memory system using Qdrant + fastembed
        from src.memory.vector_memory_system import VectorMemoryManager
        
        # Create vector config from environment and overrides
        import os
        
        # Use explicit collection name from environment variable
        # This allows precise control without auto-detection
        collection_name = os.getenv('QDRANT_COLLECTION_NAME', 'whisperengine_memory')
        
        config = {
            'qdrant': {
                'host': os.getenv('QDRANT_HOST', 'localhost'),
                'port': int(os.getenv('QDRANT_PORT', '6333')),
                'collection_name': collection_name
            },
            'embeddings': {
                'model_name': os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2'),  # Best 384D model - excellent quality and speed
                'device': os.getenv('EMBEDDING_DEVICE', 'cpu'),
                'dimension': int(os.getenv('VECTOR_DIMENSION', '384'))
            },
            'postgresql': {
                'host': os.getenv('POSTGRES_HOST', 'localhost'),
                'port': int(os.getenv('POSTGRES_PORT', '5432')),
                'database': os.getenv('POSTGRES_DB', 'whisperengine'),
                'user': os.getenv('POSTGRES_USER', 'whisperengine'),
                'password': os.getenv('POSTGRES_PASSWORD', 'whisperengine_password')
            },
            'redis': {
                'host': os.getenv('REDIS_HOST', 'localhost'),
                'port': int(os.getenv('REDIS_PORT', '6379')),
                'ttl': int(os.getenv('REDIS_TTL', '1800'))
            }
        }
        
        # Apply any config overrides if provided
        # (config parameter would be passed from calling function)
        
        # Create and return the vector memory manager
        return VectorMemoryManager(config)
    
    elif memory_type == "experimental_v2":
        # Future: Next-generation memory system
        raise NotImplementedError("Experimental V2 memory manager not yet implemented")
    
    else:
        raise ValueError(f"Unknown memory_type: {memory_type}. Supported: 'vector', 'test_mock', 'experimental_v2'")


def create_multi_bot_querier(memory_manager=None):
    """
    Create a multi-bot memory querier for advanced cross-bot analysis
    
    Features:
    - Query all bots (global search)
    - Query specific bot subsets  
    - Cross-bot memory analysis
    - Bot memory statistics
    
    Args:
        memory_manager: Optional existing memory manager to use
        
    Returns:
        MultiBotMemoryQuerier instance
    """
    try:
        from .multi_bot_memory_querier import MultiBotMemoryQuerier
        return MultiBotMemoryQuerier(memory_manager=memory_manager)
    except ImportError as e:
        logger.warning(f"MultiBotMemoryQuerier not available: {e}")
        return None


# LLM tool integration removed as part of memory system simplification
# Keep only core vector memory functionality for storing and retrieving memories