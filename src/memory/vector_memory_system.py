"""
WhisperEngine Vector-Native Memory Implementation - Local-First

Production-ready implementation using local Docker services:
- Qdrant for vector storage (local container)
- sentence-transformers for embeddings (local model)
- No external API dependencies except LLM endpoints

This supersedes all previous memory system implementations.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from uuid import uuid4

# Local-First AI/ML Libraries
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from pydantic import BaseModel, Field

# Performance & Async (PostgreSQL for system data, Redis for session cache)
import asyncpg
import redis.asyncio as redis

# Import memory context classes for Discord context classification
from src.memory.context_aware_memory_security import (
    MemoryContext, 
    MemoryContextType, 
    ContextSecurity
)

logger = logging.getLogger(__name__)


class MemoryType(Enum):
    """Types of memories in the vector store"""
    CONVERSATION = "conversation"
    FACT = "fact"
    CONTEXT = "context"
    CORRECTION = "correction"
    RELATIONSHIP = "relationship"
    PREFERENCE = "preference"


@dataclass
class VectorMemory:
    """Unified memory object for vector storage"""
    id: str
    user_id: str
    memory_type: MemoryType
    content: str
    embedding: Optional[List[float]] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None
    confidence: float = 0.8
    source: str = "system"
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}


class VectorMemoryStore:
    """
    Production vector memory store using LOCAL Qdrant + sentence-transformers
    
    This is the single source of truth for all WhisperEngine memory.
    Replaces the problematic hierarchical Redis/PostgreSQL/ChromaDB system.
    Local-first deployment - no external API dependencies.
    """
    
    def __init__(self, 
                 qdrant_host: str = "localhost",
                 qdrant_port: int = 6333,
                 collection_name: str = "whisperengine_memory",
                 embedding_model: str = "all-MiniLM-L6-v2"):
        
        # Initialize Qdrant (Local Vector DB in Docker)
        self.client = QdrantClient(host=qdrant_host, port=qdrant_port)
        self.collection_name = collection_name
        
        # Initialize sentence-transformers (Local embedding model)
        self.embedder = SentenceTransformer(embedding_model)
        self.embedding_dimension = self.embedder.get_sentence_embedding_dimension()
        
        # Initialize collection if it doesn't exist
        self._ensure_collection_exists()
        
        # Performance tracking
        self.stats = {
            "embeddings_generated": 0,
            "searches_performed": 0,
            "memories_stored": 0,
            "contradictions_detected": 0
        }
        
        logger.info(f"VectorMemoryStore initialized: {qdrant_host}:{qdrant_port}, "
                   f"collection={collection_name}, embedding_dim={self.embedding_dimension}")
    
    def _ensure_collection_exists(self):
        """Create collection if it doesn't exist"""
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_dimension,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created new collection: {self.collection_name}")
            else:
                logger.info(f"Using existing collection: {self.collection_name}")
                
        except Exception as e:
            logger.error(f"Error ensuring collection exists: {e}")
            raise
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate high-quality embedding using local sentence-transformers"""
        try:
            # Run embedding generation in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None, self.embedder.encode, text
            )
            
            self.stats["embeddings_generated"] += 1
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
            
            self.stats["embeddings_generated"] += 1
            return response['data'][0]['embedding']
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise
    
    async def store_memory(self, memory: VectorMemory) -> str:
        """Store memory in Qdrant vector database"""
        try:
            # Generate embedding if not provided
            if memory.embedding is None:
                memory.embedding = await self.generate_embedding(memory.content)
            
            # Prepare payload for Qdrant
            payload = {
                "user_id": memory.user_id,
                "memory_type": memory.memory_type.value,
                "content": memory.content,
                "timestamp": memory.timestamp.isoformat(),
                "confidence": memory.confidence,
                "source": memory.source,
                **memory.metadata
            }
            
            # Store in Qdrant
            point = PointStruct(
                id=memory.id,
                vector=memory.embedding,
                payload=payload
            )
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            self.stats["memories_stored"] += 1
            logger.info(f"Stored memory {memory.id} for user {memory.user_id}")
            
            return memory.id
            
        except Exception as e:
            logger.error(f"Memory storage failed: {e}")
            raise
    
    async def search_memories(self, 
                            query: str,
                            user_id: str,
                            memory_types: Optional[List[MemoryType]] = None,
                            top_k: int = 10,
                            min_score: float = 0.7) -> List[Dict[str, Any]]:
        """Semantic search across user's memories using Qdrant"""
        try:
            # Generate query embedding
            query_embedding = await self.generate_embedding(query)
            
            # Prepare filter conditions
            filter_conditions = [
                models.FieldCondition(
                    key="user_id",
                    match=models.MatchValue(value=user_id)
                )
            ]
            
            if memory_types:
                memory_type_values = [mt.value for mt in memory_types]
                filter_conditions.append(
                    models.FieldCondition(
                        key="memory_type",
                        match=models.MatchAny(any=memory_type_values)
                    )
                )
            
            # Search Qdrant
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                query_filter=models.Filter(must=filter_conditions),
                limit=top_k,
                score_threshold=min_score
            )
            
            # Format results
            formatted_results = []
            for point in results:
                formatted_results.append({
                    "id": point.id,
                    "score": point.score,
                    "content": point.payload['content'],
                    "memory_type": point.payload['memory_type'],
                    "timestamp": point.payload['timestamp'],
                    "confidence": point.payload['confidence'],
                    "metadata": point.payload
                })
            
            self.stats["searches_performed"] += 1
            logger.debug(f"Found {len(formatted_results)} memories for query: {query[:50]}")
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Memory search failed: {e}")
            raise
    
    async def detect_contradictions(self, 
                                  new_content: str,
                                  user_id: str,
                                  similarity_threshold: float = 0.85) -> List[Dict[str, Any]]:
        """
        Detect contradictory facts using semantic similarity
        
        This solves the goldfish name problem by finding semantically
        similar but factually different information.
        """
        try:
            # Search for similar content
            similar_memories = await self.search_memories(
                query=new_content,
                user_id=user_id,
                memory_types=[MemoryType.FACT, MemoryType.PREFERENCE],
                top_k=20,
                min_score=similarity_threshold
            )
            
            contradictions = []
            new_embedding = await self.generate_embedding(new_content)
            
            for memory in similar_memories:
                # High semantic similarity but different content suggests contradiction
                memory_embedding = await self.generate_embedding(memory['content'])
                
                # Calculate similarity using numpy arrays
                content_similarity = cosine_similarity(
                    np.array([new_embedding]),
                    np.array([memory_embedding])
                )[0][0]
                
                # If semantically similar but textually different = potential contradiction
                if (content_similarity > similarity_threshold and 
                    new_content.lower() != memory['content'].lower()):
                    
                    contradictions.append({
                        "existing_memory": memory,
                        "new_content": new_content,
                        "similarity_score": float(content_similarity),
                        "detected_at": datetime.utcnow().isoformat()
                    })
            
            if contradictions:
                self.stats["contradictions_detected"] += len(contradictions)
                logger.warning(f"Detected {len(contradictions)} contradictions for user {user_id}")
            
            return contradictions
            
        except Exception as e:
            logger.error(f"Contradiction detection failed: {e}")
            raise
    
    async def update_memory(self, memory_id: str, new_content: str, reason: str) -> bool:
        """Update existing memory (for user corrections)"""
        try:
            # Generate new embedding
            new_embedding = await self.generate_embedding(new_content)
            
            # Get existing point
            existing_points = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[memory_id]
            )
            
            if not existing_points:
                logger.error(f"Memory {memory_id} not found for update")
                return False
            
            # Update payload
            existing_payload = existing_points[0].payload
            existing_payload.update({
                "content": new_content,
                "updated_at": datetime.utcnow().isoformat(),
                "update_reason": reason,
                "corrected": True
            })
            
            # Store updated version
            updated_point = PointStruct(
                id=memory_id,
                vector=new_embedding,
                payload=existing_payload
            )
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=[updated_point]
            )
            
            logger.info(f"Updated memory {memory_id}: {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Memory update failed: {e}")
            return False
    
    async def delete_memory(self, memory_id: str) -> bool:
        """Delete memory by ID"""
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.PointIdsList(points=[memory_id])
            )
            logger.info(f"Deleted memory {memory_id}")
            return True
        except Exception as e:
            logger.error(f"Memory deletion failed: {e}")
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get performance and usage statistics"""
        try:
            collection_info = self.client.get_collection(self.collection_name)
            
            return {
                "performance": self.stats,
                "storage": {
                    "total_vectors": collection_info.points_count,
                    "dimension": self.embedding_dimension,
                    "collection_name": self.collection_name
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {
                "performance": self.stats,
                "storage": {"error": str(e)},
                "timestamp": datetime.utcnow().isoformat()
            }


class MemoryTools:
    """
    LLM-callable tools for memory management
    
    Enables natural language memory corrections:
    "Actually, my goldfish is named Bubbles, not Orion"
    """
    
    def __init__(self, vector_store: VectorMemoryStore):
        self.vector_store = vector_store
        # Note: Tools removed - LangChain dependency eliminated
    
    def _create_memory_tools(self) -> dict:
        """Create simple memory management tools without LangChain dependency"""
        
        return {
            "update_memory_fact": self._update_fact_tool,
            "search_user_memory": self._search_memory_tool, 
            "delete_incorrect_memory": self._delete_memory_tool
        }
    
    async def _update_fact_tool(self, **kwargs) -> str:
        """Tool function for updating facts"""
        user_id = kwargs.get('user_id')
        subject = kwargs.get('subject')
        old_value = kwargs.get('old_value')
        new_value = kwargs.get('new_value')
        reason = kwargs.get('reason', 'User correction')
        
        try:
            # Find existing fact
            existing_memories = await self.vector_store.search_memories(
                query=f"{subject} {old_value}",
                user_id=user_id,
                memory_types=[MemoryType.FACT]
            )
            
            # Update or create new fact
            if existing_memories:
                # Update existing
                memory_id = existing_memories[0]['id']
                success = await self.vector_store.update_memory(
                    memory_id=memory_id,
                    new_content=f"{subject} is {new_value}",
                    reason=reason
                )
                
                if success:
                    return f"Updated {subject} from '{old_value}' to '{new_value}'"
                else:
                    return f"Failed to update {subject}"
            else:
                # Create new fact
                new_memory = VectorMemory(
                    id=f"fact_{user_id}_{uuid4()}",
                    user_id=user_id,
                    memory_type=MemoryType.FACT,
                    content=f"{subject} is {new_value}",
                    confidence=0.95,  # High confidence for user corrections
                    source="user_correction",
                    metadata={
                        "subject": subject,
                        "value": new_value,
                        "corrected_from": old_value,
                        "reason": reason
                    }
                )
                
                await self.vector_store.store_memory(new_memory)
                return f"Created new fact: {subject} is {new_value}"
                
        except Exception as e:
            logger.error(f"Fact update tool failed: {e}")
            return f"Error updating fact: {str(e)}"
    
    async def _search_memory_tool(self, **kwargs) -> str:
        """Tool function for searching memory"""
        user_id = kwargs.get('user_id')
        query = kwargs.get('query')
        memory_type = kwargs.get('memory_type')
        
        try:
            memory_types = None
            if memory_type:
                memory_types = [MemoryType(memory_type)]
            
            results = await self.vector_store.search_memories(
                query=query,
                user_id=user_id,
                memory_types=memory_types,
                top_k=5
            )
            
            if results:
                formatted_results = []
                for result in results:
                    formatted_results.append(
                        f"- {result['content']} (confidence: {result['confidence']:.2f})"
                    )
                return f"Found {len(results)} memories:\n" + "\n".join(formatted_results)
            else:
                return f"No memories found for query: {query}"
                
        except Exception as e:
            logger.error(f"Memory search tool failed: {e}")
            return f"Error searching memory: {str(e)}"
    
    async def _delete_memory_tool(self, **kwargs) -> str:
        """Tool function for deleting memory"""
        user_id = kwargs.get('user_id')
        content = kwargs.get('content_to_delete')
        reason = kwargs.get('reason', 'User requested deletion')
        
        try:
            # Find memories to delete
            memories = await self.vector_store.search_memories(
                query=content,
                user_id=user_id,
                top_k=5,
                min_score=0.9  # High threshold for deletion
            )
            
            deleted_count = 0
            for memory in memories:
                if await self.vector_store.delete_memory(memory['id']):
                    deleted_count += 1
            
            return f"Deleted {deleted_count} memories matching '{content}'"
            
        except Exception as e:
            logger.error(f"Memory deletion tool failed: {e}")
            return f"Error deleting memory: {str(e)}"


class VectorMemoryManager:
    """
    Main memory manager for WhisperEngine
    
    Replaces the entire hierarchical memory system with vector-native approach.
    This is the new primary memory interface.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize VectorMemoryManager with configuration dict
        
        Args:
            config: Configuration dictionary with qdrant, embeddings, postgresql, redis settings
        """
        
        # Extract Qdrant configuration
        qdrant_config = config.get('qdrant', {})
        qdrant_host = qdrant_config.get('host', 'localhost')
        qdrant_port = qdrant_config.get('port', 6333)
        collection_name = qdrant_config.get('collection_name', 'whisperengine_memory')
        
        # Extract embeddings configuration
        embeddings_config = config.get('embeddings', {})
        embedding_model = embeddings_config.get('model_name', 'all-MiniLM-L6-v2')
        
        # Core vector store (single source of truth) - LOCAL IMPLEMENTATION
        self.vector_store = VectorMemoryStore(
            qdrant_host=qdrant_host,
            qdrant_port=qdrant_port,
            collection_name=collection_name,
            embedding_model=embedding_model
        )
        
        # Store config for other services (PostgreSQL for user data, Redis for session cache)
        self.config = config
        
        # LLM-callable memory tools
        self.memory_tools = MemoryTools(self.vector_store)
        
        # Session cache for performance (Redis for hot data only)
        self.session_cache = None  # Will be initialized if Redis available
        
        logger.info("VectorMemoryManager initialized - local-first single source of truth ready")
    
    async def process_user_message(self, 
                                 user_id: str,
                                 message_content: str) -> Dict[str, Any]:
        """
        Process user message for memory operations
        
        This replaces the complex hierarchical memory processing.
        """
        start_time = time.time()
        
        try:
            # 1. Check for contradiction with existing memories
            contradictions = await self.vector_store.detect_contradictions(
                new_content=message_content,
                user_id=user_id
            )
            
            # 2. Store conversation memory
            conversation_memory = VectorMemory(
                id=str(uuid4()),  # Pure UUID for Qdrant compatibility
                user_id=user_id,
                memory_type=MemoryType.CONVERSATION,
                content=message_content,
                source="user_message",
                metadata={
                    "processed_at": datetime.utcnow().isoformat(),
                    "contradictions_found": len(contradictions)
                }
            )
            
            await self.vector_store.store_memory(conversation_memory)
            
            # 3. Extract and store facts (simple pattern matching for now)
            facts = await self._extract_facts(message_content, user_id)
            for fact in facts:
                await self.vector_store.store_memory(fact)
            
            # 4. Get relevant context for response
            context = await self.get_conversation_context(user_id, message_content)
            
            processing_time = time.time() - start_time
            
            return {
                "success": True,
                "contradictions": contradictions,
                "facts_extracted": len(facts),
                "context": context,
                "processing_time_ms": processing_time * 1000,
                "memory_id": conversation_memory.id
            }
            
        except Exception as e:
            logger.error(f"Message processing failed for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "processing_time_ms": (time.time() - start_time) * 1000
            }
    
    async def get_conversation_context(self, 
                                     user_id: str,
                                     current_message: str,
                                     max_context_length: int = 4000) -> str:
        """
        Get unified conversation context from vector store
        
        This replaces the complex hierarchical context assembly.
        """
        try:
            # Search for relevant memories
            relevant_memories = await self.vector_store.search_memories(
                query=current_message,
                user_id=user_id,
                memory_types=[
                    MemoryType.CONVERSATION,
                    MemoryType.FACT,
                    MemoryType.PREFERENCE
                ],
                top_k=20,
                min_score=0.6
            )
            
            # Assemble context prioritizing recent and relevant
            context_parts = []
            current_length = 0
            
            # Sort by relevance score and recency
            sorted_memories = sorted(
                relevant_memories,
                key=lambda x: (x['score'], x['timestamp']),
                reverse=True
            )
            
            for memory in sorted_memories:
                content = memory['content']
                if current_length + len(content) < max_context_length:
                    context_parts.append(content)
                    current_length += len(content)
                else:
                    break
            
            return "\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"Context assembly failed: {e}")
            return ""
    
    async def _extract_facts(self, message: str, user_id: str) -> List[VectorMemory]:
        """Extract facts from message (simplified for initial implementation)"""
        facts = []
        
        # Simple pattern matching (will be enhanced with NLP)
        patterns = [
            (r"my (\w+) is (?:named|called) (\w+)", "pet", "is_named"),
            (r"i (?:like|love|enjoy) (\w+)", "user", "likes"),
            (r"i (?:have|own) a (\w+)", "user", "owns"),
            (r"my name is (\w+)", "user", "is_named"),
        ]
        
        import re
        for pattern, subject, predicate in patterns:
            matches = re.findall(pattern, message.lower())
            for match in matches:
                if isinstance(match, tuple):
                    if predicate == "is_named":
                        obj = match[1] if len(match) > 1 else match[0]
                        subj = match[0] if len(match) > 1 else subject
                    else:
                        obj = match[0]
                        subj = subject
                else:
                    obj = match
                    subj = subject
                
                fact = VectorMemory(
                    id=f"fact_{user_id}_{uuid4()}",
                    user_id=user_id,
                    memory_type=MemoryType.FACT,
                    content=f"{subj} {predicate} {obj}",
                    confidence=0.8,
                    source="extracted_from_message",
                    metadata={
                        "subject": subj,
                        "predicate": predicate,
                        "object": obj,
                        "extracted_from": message[:100]
                    }
                )
                facts.append(fact)
        
        return facts
    
    async def handle_user_correction(self, 
                                   user_id: str,
                                   correction_message: str) -> Dict[str, Any]:
        """
        Handle explicit user corrections using tool calling
        
        Example: "Actually, my goldfish is named Bubbles, not Orion"
        """
        try:
            # Detect correction intent
            if any(word in correction_message.lower() for word in [
                "actually", "correction", "i meant", "not", "wrong", "mistake"
            ]):
                
                # Use LLM tools to process correction
                # This would integrate with tool calling for automatic corrections
                result = await self._process_correction_with_tools(
                    user_id=user_id,
                    message=correction_message
                )
                
                return {
                    "correction_processed": True,
                    "result": result
                }
            
            return {"correction_processed": False}
            
        except Exception as e:
            logger.error(f"Correction handling failed: {e}")
            return {"correction_processed": False, "error": str(e)}
    
    async def _process_correction_with_tools(self, user_id: str, message: str) -> str:
        """Process correction using memory tools (placeholder for full implementation)"""
        # This would use an agent executor with our memory tools
        # For now, simple implementation
        
        # Extract what's being corrected
        import re
        
        # Pattern: "X is Y, not Z" -> update X from Z to Y
        pattern = r"(\w+) is (\w+), not (\w+)"
        match = re.search(pattern, message, re.IGNORECASE)
        
        if match:
            subject = match.group(1)
            new_value = match.group(2)
            old_value = match.group(3)
            
            return await self.memory_tools._update_fact_tool(
                user_id=user_id,
                subject=subject,
                old_value=old_value,
                new_value=new_value,
                reason="User correction"
            )
        
        return "Could not parse correction"
    
    async def get_health_stats(self) -> Dict[str, Any]:
        """Get system health and performance stats"""
        return await self.vector_store.get_stats()
    
    # === PROTOCOL COMPLIANCE METHODS ===
    # These methods ensure VectorMemoryManager implements MemoryManagerProtocol
    
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
        try:
            # Store user message
            user_memory = VectorMemory(
                id=str(uuid4()),  # Pure UUID for Qdrant compatibility
                user_id=user_id,
                memory_type=MemoryType.CONVERSATION,
                content=user_message,
                source="user_message",
                metadata={
                    "channel_id": channel_id,
                    "emotion_data": pre_analyzed_emotion_data,
                    "role": "user",
                    **(metadata or {})
                }
            )
            await self.vector_store.store_memory(user_memory)
            
            # Store bot response
            bot_memory = VectorMemory(
                id=str(uuid4()),  # Pure UUID for Qdrant compatibility
                user_id=user_id,
                memory_type=MemoryType.CONVERSATION,
                content=bot_response,
                source="bot_response",
                metadata={
                    "channel_id": channel_id,
                    "role": "bot",
                    **(metadata or {})
                }
            )
            await self.vector_store.store_memory(bot_memory)
            
            return True
        except Exception as e:
            logger.error(f"Failed to store conversation: {e}")
            return False
    
    async def retrieve_relevant_memories(
        self,
        user_id: str,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Retrieve memories relevant to the given query."""
        try:
            results = await self.vector_store.search_memories(
                query=query,
                user_id=user_id,
                top_k=limit,
                min_score=0.5
            )
            return [
                {
                    "content": r["content"],
                    "score": r["score"],
                    "timestamp": r["timestamp"],
                    "metadata": r.get("metadata", {}),
                    "memory_type": r.get("memory_type", "unknown")
                }
                for r in results
            ]
        except Exception as e:
            logger.error(f"Failed to retrieve memories: {e}")
            return []
    
    async def retrieve_context_aware_memories(
        self,
        user_id: str,
        query: Optional[str] = None,
        current_query: Optional[str] = None,
        max_memories: int = 10,
        limit: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Retrieve context-aware memories with enhanced filtering."""
        effective_query = query or current_query or ""
        effective_limit = limit or max_memories
        
        return await self.retrieve_relevant_memories(
            user_id=user_id,
            query=effective_query,
            limit=effective_limit
        )
    
    async def get_recent_conversations(
        self, 
        user_id: str, 
        limit: int = 5,
        context_filter: Optional[Any] = None
    ) -> List[Dict[str, Any]]:
        """Get recent conversation history for a user."""
        try:
            # Search for recent conversation memories
            results = await self.vector_store.search_memories(
                query="conversation user_message bot_response",
                user_id=user_id,
                memory_types=[MemoryType.CONVERSATION],
                top_k=limit * 2  # Get more to filter properly
            )
            
            conversations = []
            seen_pairs = set()
            
            for result in results:
                content = result.get("content", "")
                metadata = result.get("metadata", {})
                role = metadata.get("role", "")
                
                # Group user/bot message pairs
                if role == "user":
                    user_message = content
                    # Look for corresponding bot response
                    bot_response = ""
                    for r in results:
                        r_metadata = r.get("metadata", {})
                        if (r_metadata.get("role") == "assistant" and 
                            abs(r.get("timestamp", 0) - result.get("timestamp", 0)) < 60):  # Within 1 minute
                            bot_response = r.get("content", "")
                            break
                    
                    pair_key = (user_message[:50], bot_response[:50])  # Use truncated content as key
                    if pair_key not in seen_pairs:
                        conversations.append({
                            'user_message': user_message,
                            'bot_response': bot_response,
                            'timestamp': result.get("timestamp", ""),
                            'metadata': metadata
                        })
                        seen_pairs.add(pair_key)
                        
                        if len(conversations) >= limit:
                            break
            
            # Sort by timestamp (most recent first)
            conversations.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            return conversations[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get recent conversations: {e}")
            return []
    
    async def store_fact(
        self,
        user_id: str,
        fact: str,
        context: str,
        confidence: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Store a fact for the user."""
        try:
            fact_memory = VectorMemory(
                id=f"fact_{user_id}_{uuid4()}",
                user_id=user_id,
                memory_type=MemoryType.FACT,
                content=fact,
                confidence=confidence,
                source="explicit_fact",
                metadata={
                    "context": context,
                    **(metadata or {})
                }
            )
            await self.vector_store.store_memory(fact_memory)
            return True
        except Exception as e:
            logger.error(f"Failed to store fact: {e}")
            return False
    
    async def retrieve_facts(
        self,
        user_id: str,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Retrieve facts for the user based on query."""
        try:
            results = await self.vector_store.search_memories(
                query=query,
                user_id=user_id,
                memory_types=[MemoryType.FACT],
                top_k=limit,
                min_score=0.6
            )
            return [
                {
                    "fact": r["content"],
                    "confidence": r.get("confidence", 0.8),
                    "timestamp": r["timestamp"],
                    "context": r.get("metadata", {}).get("context", ""),
                    "metadata": r.get("metadata", {})
                }
                for r in results
            ]
        except Exception as e:
            logger.error(f"Failed to retrieve facts: {e}")
            return []
    
    async def update_user_profile(
        self,
        user_id: str,
        profile_data: Dict[str, Any]
    ) -> bool:
        """Update user profile data."""
        try:
            # Store profile data as preference memories
            for key, value in profile_data.items():
                preference_memory = VectorMemory(
                    id=f"profile_{user_id}_{key}_{uuid4()}",
                    user_id=user_id,
                    memory_type=MemoryType.PREFERENCE,
                    content=f"{key}: {value}",
                    source="profile_update",
                    metadata={
                        "profile_key": key,
                        "profile_value": str(value)
                    }
                )
                await self.vector_store.store_memory(preference_memory)
            return True
        except Exception as e:
            logger.error(f"Failed to update user profile: {e}")
            return False
    
    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Get user profile data."""
        try:
            results = await self.vector_store.search_memories(
                query="",
                user_id=user_id,
                memory_types=[MemoryType.PREFERENCE],
                top_k=50,
                min_score=0.0
            )
            
            profile = {}
            for r in results:
                metadata = r.get("metadata", {})
                key = metadata.get("profile_key")
                value = metadata.get("profile_value")
                if key and value:
                    profile[key] = value
            
            return profile
        except Exception as e:
            logger.error(f"Failed to get user profile: {e}")
            return {}
    
    async def get_conversation_history(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get conversation history for the user."""
        try:
            results = await self.vector_store.search_memories(
                query="",
                user_id=user_id,
                memory_types=[MemoryType.CONVERSATION],
                top_k=limit,
                min_score=0.0
            )
            
            return [
                {
                    "content": r["content"],
                    "timestamp": r["timestamp"],
                    "role": r.get("metadata", {}).get("role", "unknown"),
                    "metadata": r.get("metadata", {})
                }
                for r in sorted(results, key=lambda x: x["timestamp"], reverse=True)
            ]
        except Exception as e:
            logger.error(f"Failed to get conversation history: {e}")
            return []
    
    async def search_memories(
        self,
        user_id: str,
        query: str,
        memory_types: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search memories with optional type filtering."""
        try:
            vector_memory_types = []
            if memory_types:
                for mem_type in memory_types:
                    try:
                        vector_memory_types.append(MemoryType(mem_type))
                    except ValueError:
                        # Skip unknown memory types
                        pass
            
            results = await self.vector_store.search_memories(
                query=query,
                user_id=user_id,
                memory_types=vector_memory_types if vector_memory_types else None,
                top_k=limit,
                min_score=0.5
            )
            
            return [
                {
                    "content": r["content"],
                    "memory_type": r.get("memory_type", "unknown"),
                    "score": r["score"],
                    "timestamp": r["timestamp"],
                    "metadata": r.get("metadata", {})
                }
                for r in results
            ]
        except Exception as e:
            logger.error(f"Failed to search memories: {e}")
            return []
    
    async def update_emotional_context(
        self,
        user_id: str,
        emotion_data: Dict[str, Any]
    ) -> bool:
        """Update emotional context for the user."""
        try:
            emotion_memory = VectorMemory(
                id=f"emotion_{user_id}_{uuid4()}",
                user_id=user_id,
                memory_type=MemoryType.CONTEXT,
                content=f"Emotional state: {emotion_data}",
                source="emotion_update",
                metadata={
                    "emotion_data": emotion_data,
                    "update_type": "emotional_context"
                }
            )
            await self.vector_store.store_memory(emotion_memory)
            return True
        except Exception as e:
            logger.error(f"Failed to update emotional context: {e}")
            return False
    
    async def get_emotional_context(self, user_id: str) -> Dict[str, Any]:
        """Get emotional context for the user."""
        try:
            results = await self.vector_store.search_memories(
                query="emotional state",
                user_id=user_id,
                memory_types=[MemoryType.CONTEXT],
                top_k=10,
                min_score=0.5
            )
            
            # Get the most recent emotional context
            if results:
                latest = max(results, key=lambda x: x["timestamp"])
                return latest.get("metadata", {}).get("emotion_data", {})
            
            return {}
        except Exception as e:
            logger.error(f"Failed to get emotional context: {e}")
            return {}
    
    # Alias for protocol compatibility
    async def get_emotion_context(self, user_id: str) -> Dict[str, Any]:
        """Alias for get_emotional_context."""
        return await self.get_emotional_context(user_id)
    
    def classify_discord_context(self, message) -> MemoryContext:
        """
        Classify Discord message context for security boundaries.
        
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
        Check if a Discord channel is private based on permissions.
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
            
        except Exception as e:
            logger.error(f"Error checking channel privacy: {e}")
            # Default to private for safety
            return True
    
    async def health_check(self) -> Dict[str, Any]:
        """Get system health status."""
        try:
            stats = await self.get_health_stats()
            return {
                "status": "healthy",
                "type": "vector",
                "stats": stats,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "type": "vector",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


# Example usage and testing
async def test_vector_memory_system():
    """Test the new vector memory system - LOCAL DEPLOYMENT"""
    
    # Initialize (using local Docker services)
    config = {
        'qdrant': {
            'host': 'localhost',
            'port': 6333,
            'collection_name': 'whisperengine_memory'
        },
        'embeddings': {
            'model_name': 'all-MiniLM-L6-v2'
        }
    }
    
    memory_manager = VectorMemoryManager(config)
    
    user_id = "test_user_123"
    
    # Test 1: Store initial fact
    result1 = await memory_manager.process_user_message(
        user_id=user_id,
        message_content="My goldfish is named Orion"
    )
    print(f"Initial fact stored: {result1}")
    
    # Test 2: User correction (this would detect contradiction)
    result2 = await memory_manager.process_user_message(
        user_id=user_id,
        message_content="Actually, my goldfish is named Bubbles"
    )
    print(f"Correction processed: {result2}")
    
    # Test 3: Handle explicit correction
    correction_result = await memory_manager.handle_user_correction(
        user_id=user_id,
        correction_message="My goldfish is Bubbles, not Orion"
    )
    print(f"Explicit correction: {correction_result}")
    
    # Test 4: Get context (should now show correct name)
    context = await memory_manager.get_conversation_context(
        user_id=user_id,
        current_message="Tell me about my goldfish"
    )
    print(f"Current context: {context}")
    
    # Test 5: Health stats
    stats = await memory_manager.get_health_stats()
    print(f"System health: {stats}")


if __name__ == "__main__":
    asyncio.run(test_vector_memory_system())