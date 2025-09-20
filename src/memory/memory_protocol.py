"""
Memory Manager Protocol Definition
Standardizes interface for all WhisperEngine memory manager implementations

This protocol enables A/B testing and future memory system innovations
while maintaining consistent async interfaces.
"""

from typing import Protocol, List, Dict, Any, Optional, Union


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
    
    # === HEALTH & STATUS ===
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the memory system."""
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
            
            async def health_check(self) -> Dict[str, Any]:
                return {"status": "healthy", "type": "mock"}
        
        return MockMemoryManager()
    
    elif memory_type == "vector":
        # Vector-native memory system using Qdrant + fastembed
        from src.memory.vector_memory_system import VectorMemoryManager
        
        # Create vector config from environment and overrides
        import os
        vector_config = {
            'qdrant': {
                'host': os.getenv('VECTOR_QDRANT_HOST', 'qdrant'),
                'port': int(os.getenv('VECTOR_QDRANT_PORT', '6333')),
                'grpc_port': int(os.getenv('VECTOR_QDRANT_GRPC_PORT', '6334')),
                'collection_name': os.getenv('VECTOR_QDRANT_COLLECTION', 'whisperengine_memory'),
                'vector_size': int(os.getenv('VECTOR_EMBEDDING_SIZE', '384'))
            },
            'embeddings': {
                'model_name': os.getenv('VECTOR_EMBEDDING_MODEL', 'snowflake/snowflake-arctic-embed-xs'),
                'device': os.getenv('VECTOR_EMBEDDING_DEVICE', 'cpu')
            },
            'postgresql': {
                'url': f"postgresql://{os.getenv('POSTGRESQL_USERNAME', 'bot_user')}:{os.getenv('POSTGRESQL_PASSWORD', 'securepassword123')}@{os.getenv('POSTGRESQL_HOST', 'postgres')}:{os.getenv('POSTGRESQL_PORT', '5432')}/{os.getenv('POSTGRESQL_DATABASE', 'whisper_engine')}"
            },
            'redis': {
                'url': f"redis://{os.getenv('REDIS_HOST', 'redis')}:{os.getenv('REDIS_PORT', '6379')}",
                'ttl': int(os.getenv('REDIS_TTL', '1800'))
            }
        }
        
        # Apply any config overrides
        vector_config.update(config)
        
        # Create and return the vector memory manager
        return VectorMemoryManager(vector_config)
    
    elif memory_type == "experimental_v2":
        # Future: Next-generation memory system
        raise NotImplementedError("Experimental V2 memory manager not yet implemented")
    
    else:
        raise ValueError(f"Unknown memory_type: {memory_type}. Supported: 'vector', 'test_mock', 'experimental_v2'")