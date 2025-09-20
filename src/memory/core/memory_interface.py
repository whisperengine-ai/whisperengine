"""
Unified Memory Manager Interface for WhisperEngine

This module defines the canonical async-first interface that all memory managers
must implement, eliminating the async/sync detection chaos.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol
from dataclasses import dataclass
from enum import Enum

from src.utils.exceptions import MemoryError, MemoryRetrievalError, MemoryStorageError


class MemoryContextType(Enum):
    """Types of memory contexts"""
    DM = "dm"
    GUILD_PUBLIC = "guild_public"
    GUILD_PRIVATE = "guild_private"
    THREAD = "thread"


@dataclass
class MemoryContext:
    """Standardized memory context for all operations"""
    context_type: MemoryContextType
    channel_id: Optional[str] = None
    guild_id: Optional[str] = None
    thread_id: Optional[str] = None
    security_level: str = "private"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "context_type": self.context_type.value,
            "channel_id": self.channel_id,
            "guild_id": self.guild_id,
            "thread_id": self.thread_id,
            "security_level": self.security_level,
        }


@dataclass
class MemoryEntry:
    """Standardized memory entry format"""
    id: str
    user_id: str
    content: str
    metadata: Dict[str, Any]
    timestamp: str
    score: float = 0.0
    context: Optional[MemoryContext] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "score": self.score,
            "context": self.context.to_dict() if self.context else None,
        }


@dataclass
class EmotionContext:
    """Standardized emotion context"""
    current_emotion: str
    emotion_intensity: float
    relationship_level: str
    interaction_count: int
    emotional_patterns: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "current_emotion": self.current_emotion,
            "emotion_intensity": self.emotion_intensity,
            "relationship_level": self.relationship_level,
            "interaction_count": self.interaction_count,
            "emotional_patterns": self.emotional_patterns,
        }


class MemoryManagerProtocol(Protocol):
    """Protocol defining the unified memory manager interface"""
    
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
        """Store a conversation memory entry. Returns memory ID."""
        ...
    
    async def store_user_fact(
        self,
        user_id: str,
        fact: str,
        *,
        context: Optional[MemoryContext] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Store a user fact. Returns fact ID."""
        ...
    
    # === MEMORY RETRIEVAL ===
    
    async def retrieve_memories(
        self,
        user_id: str,
        query: str,
        *,
        limit: int = 10,
        context: Optional[MemoryContext] = None,
        min_score: float = 0.0,
    ) -> List[MemoryEntry]:
        """Retrieve relevant memories for user and query."""
        ...
    
    async def retrieve_conversation_history(
        self,
        user_id: str,
        *,
        limit: int = 10,
        context: Optional[MemoryContext] = None,
    ) -> List[MemoryEntry]:
        """Retrieve recent conversation history."""
        ...
    
    # === EMOTION & CONTEXT ===
    
    async def get_emotion_context(
        self,
        user_id: str,
        *,
        context: Optional[MemoryContext] = None,
    ) -> EmotionContext:
        """Get emotional context for user."""
        ...
    
    async def update_emotion_state(
        self,
        user_id: str,
        emotion: str,
        intensity: float,
        *,
        context: Optional[MemoryContext] = None,
    ) -> None:
        """Update user's emotional state."""
        ...
    
    # === MEMORY MANAGEMENT ===
    
    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a specific memory by ID."""
        ...
    
    async def delete_user_memories(
        self,
        user_id: str,
        *,
        context: Optional[MemoryContext] = None,
    ) -> int:
        """Delete all memories for a user in context. Returns count deleted."""
        ...
    
    # === ANALYTICS & INSIGHTS ===
    
    async def get_memory_stats(self, user_id: str) -> Dict[str, Any]:
        """Get memory statistics for user."""
        ...
    
    async def get_relationship_insights(self, user_id: str) -> Dict[str, Any]:
        """Get relationship insights based on memory patterns."""
        ...


class UnifiedMemoryManager(ABC):
    """
    Abstract base class for all memory managers.
    
    This enforces the async-first interface and provides common functionality
    while allowing concrete implementations to handle storage specifics.
    """
    
    def __init__(self):
        self._initialized = False
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the memory manager (async setup)."""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Close and cleanup resources."""
        pass
    
    # === REQUIRED IMPLEMENTATIONS ===
    
    @abstractmethod
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
        """Store a conversation memory entry."""
        pass
    
    @abstractmethod
    async def retrieve_memories(
        self,
        user_id: str,
        query: str,
        *,
        limit: int = 10,
        context: Optional[MemoryContext] = None,
        min_score: float = 0.0,
    ) -> List[MemoryEntry]:
        """Retrieve relevant memories."""
        pass
    
    @abstractmethod
    async def get_emotion_context(
        self,
        user_id: str,
        *,
        context: Optional[MemoryContext] = None,
    ) -> EmotionContext:
        """Get emotional context."""
        pass
    
    # === COMMON IMPLEMENTATIONS ===
    
    async def store_user_fact(
        self,
        user_id: str,
        fact: str,
        *,
        context: Optional[MemoryContext] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Default implementation stores facts as special conversation entries."""
        fact_metadata = {"type": "user_fact", "fact": fact}
        if metadata:
            fact_metadata.update(metadata)
        
        return await self.store_conversation(
            user_id=user_id,
            user_message=f"User fact: {fact}",
            bot_response="Fact noted.",
            context=context,
            metadata=fact_metadata,
        )
    
    async def retrieve_conversation_history(
        self,
        user_id: str,
        *,
        limit: int = 10,
        context: Optional[MemoryContext] = None,
    ) -> List[MemoryEntry]:
        """Default implementation uses retrieve_memories with empty query."""
        return await self.retrieve_memories(
            user_id=user_id,
            query="",
            limit=limit,
            context=context,
        )
    
    # === UTILITIES ===
    
    def _ensure_initialized(self) -> None:
        """Ensure the manager is initialized."""
        if not self._initialized:
            raise MemoryError("Memory manager not initialized. Call await manager.initialize() first.")
    
    def _create_memory_context(
        self,
        channel_id: Optional[str] = None,
        guild_id: Optional[str] = None,
        context_type: MemoryContextType = MemoryContextType.DM,
    ) -> MemoryContext:
        """Helper to create standardized memory context."""
        return MemoryContext(
            context_type=context_type,
            channel_id=channel_id,
            guild_id=guild_id,
        )