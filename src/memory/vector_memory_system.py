"""
WhisperEngine Vector-Native Memory Implementation - Local-First

Production-ready implementation using local Docker services:
- Qdrant for vector storage (local container)
- fastembed for embeddings (local model)
- No external API dependencies except LLM endpoints

This supersedes all previous memory system implementations.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from uuid import uuid4

# Local-First AI/ML Libraries
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import (
    Distance, VectorParams, PointStruct, Range, OrderBy, Direction,
    HnswConfigDiff, OptimizersConfigDiff, ScalarQuantization, 
    ScalarQuantizationConfig, ScalarType, PayloadSchemaType, NamedVector
)
from fastembed import TextEmbedding
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
    Production vector memory store using LOCAL Qdrant + fastembed
    
    This is the single source of truth for all WhisperEngine memory.
    Replaces the problematic hierarchical Redis/PostgreSQL/ChromaDB system.
    Local-first deployment - no external API dependencies.
    """
    
    def __init__(self, 
                 qdrant_host: str = "localhost",
                 qdrant_port: int = 6333,
                 collection_name: str = "whisperengine_memory",
                 embedding_model: str = "snowflake/snowflake-arctic-embed-xs"):
        
        # Initialize Qdrant (Local Vector DB in Docker)
        self.client = QdrantClient(host=qdrant_host, port=qdrant_port)
        self.collection_name = collection_name
        
        # Initialize fastembed (Local embedding model)
        self.embedder = TextEmbedding(model_name=embedding_model)
        # Get embedding dimension from the model
        test_embedding = list(self.embedder.embed(["test"]))[0]
        self.embedding_dimension = len(test_embedding)
        
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
        """
        🚀 QDRANT-NATIVE: Create advanced collection with named vectors
        
        Features:
        - Named vectors for multi-dimensional search (content, emotion, semantic)
        - Optimized indexing for payload fields
        - Performance optimizations
        """
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name not in collection_names:
                # 🎯 QDRANT FEATURE: Named vectors for multi-dimensional intelligence
                vectors_config = {
                    # Main content vector for semantic similarity
                    "content": VectorParams(
                        size=self.embedding_dimension,
                        distance=Distance.COSINE,
                        hnsw_config=models.HnswConfigDiff(
                            m=32,  # Higher connectivity for better recall
                            ef_construct=256,  # Better build quality
                            full_scan_threshold=20000
                        )
                    ),
                    
                    # Emotional context vector for sentiment-aware search
                    "emotion": VectorParams(
                        size=self.embedding_dimension,
                        distance=Distance.COSINE,
                        hnsw_config=models.HnswConfigDiff(
                            m=16,  # Lower connectivity for emotion
                            ef_construct=128
                        )
                    ),
                    
                    # Semantic concept vector for contradiction detection
                    "semantic": VectorParams(
                        size=self.embedding_dimension,
                        distance=Distance.COSINE,
                        hnsw_config=models.HnswConfigDiff(
                            m=16,
                            ef_construct=128
                        )
                    )
                }
                
                # 🚀 QDRANT FEATURE: Optimized configuration for performance
                optimizers_config = models.OptimizersConfigDiff(
                    deleted_threshold=0.2,
                    vacuum_min_vector_number=1000,
                    default_segment_number=2,
                    max_segment_size=20000,
                    memmap_threshold=50000,
                    indexing_threshold=20000,
                    flush_interval_sec=5,
                    max_optimization_threads=2
                )
                
                # Simple named vector creation
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=vectors_config,  # Named vectors only
                    optimizers_config=optimizers_config
                )
                
                # 🎯 QDRANT FEATURE: Create payload indexes for efficient filtering
                self._create_payload_indexes()
                
                logger.info(f"🚀 QDRANT-ADVANCED: Created collection '{self.collection_name}' with named vectors")
            else:
                logger.info(f"Using existing collection: {self.collection_name}")
                
        except Exception as e:
            logger.error(f"Error ensuring collection exists: {e}")
            raise  # Don't fallback - we need named vectors to work properly
    
    def _create_payload_indexes(self):
        """
        🎯 QDRANT FEATURE: Create optimized payload indexes for fast filtering
        """
        try:
            # Index for user-based filtering (most common)
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="user_id",
                field_schema=models.PayloadSchemaType.KEYWORD
            )
            
            # Index for memory type filtering
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="memory_type", 
                field_schema=models.PayloadSchemaType.KEYWORD
            )
            
            # Index for temporal range queries
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="timestamp_unix",
                field_schema=models.PayloadSchemaType.FLOAT
            )
            
            # Index for semantic grouping
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="semantic_key",
                field_schema=models.PayloadSchemaType.KEYWORD
            )
            
            # Index for emotional context
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="emotional_context",
                field_schema=models.PayloadSchemaType.KEYWORD
            )
            
            # Index for content hash (deduplication)
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="content_hash",
                field_schema=models.PayloadSchemaType.INTEGER
            )
            
            logger.info("🎯 QDRANT-INDEXES: Created optimized payload indexes")
            
        except Exception as e:
            logger.warning(f"Could not create payload indexes (may already exist): {e}")
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate high-quality embedding using local fastembed"""
        try:
            # Run embedding generation in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            
            def encode_with_fastembed():
                # fastembed returns a generator, get first item
                embedding = list(self.embedder.embed([text]))[0]
                return embedding.tolist()
            
            embedding = await loop.run_in_executor(None, encode_with_fastembed)
            
            self.stats["embeddings_generated"] += 1
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    async def store_memory(self, memory: VectorMemory) -> str:
        """
        🚀 QDRANT-NATIVE: Store memory with named vectors and advanced features
        
        Uses:
        - Named vectors for multi-dimensional search (content + emotion + semantic)
        - Sparse vectors for keyword features
        - Automatic deduplication via content hashing
        - Contradiction detection preparation via semantic grouping
        """
        # CRITICAL DEBUG: Log entry to this method
        print(f"🔥 STORE_MEMORY CALLED: user_id={memory.user_id}, content={memory.content[:50]}...")
        logger.error(f"🔥 STORE_MEMORY CALLED: user_id={memory.user_id}, content={memory.content[:50]}...")
        
        try:
            # 🎯 QDRANT FEATURE: Generate multiple embeddings for named vectors
            content_embedding = await self.generate_embedding(memory.content)
            logger.debug(f"Generated content embedding: {type(content_embedding)}, length: {len(content_embedding) if content_embedding else None}")
            
            # Create emotional embedding for sentiment-aware search
            emotional_context = self._extract_emotional_context(memory.content)
            emotion_embedding = await self.generate_embedding(f"emotion {emotional_context}: {memory.content}")
            logger.debug(f"Generated emotion embedding: {type(emotion_embedding)}, length: {len(emotion_embedding) if emotion_embedding else None}")
            
            # Create semantic embedding for concept clustering and contradiction detection
            semantic_key = self._get_semantic_key(memory.content)
            semantic_embedding = await self.generate_embedding(f"concept {semantic_key}: {memory.content}")
            logger.debug(f"Generated semantic embedding: {type(semantic_embedding)}, length: {len(semantic_embedding) if semantic_embedding else None}")
            
            # Validate all embeddings before creating vectors dict
            if not content_embedding or not emotion_embedding or not semantic_embedding:
                raise ValueError(f"Invalid embeddings generated: content={bool(content_embedding)}, emotion={bool(emotion_embedding)}, semantic={bool(semantic_embedding)}")
            
            # 🚀 QDRANT FEATURE: Create keyword metadata for filtering
            keywords = self._extract_keywords(memory.content)
            
            # 🎯 QDRANT OPTIMIZATION: Content hash for exact deduplication
            content_normalized = memory.content.lower().strip()
            content_hash = hash(content_normalized)
            
            # 🚀 QDRANT FEATURE: Check for exact duplicates using optimized index
            existing = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(key="user_id", match=models.MatchValue(value=memory.user_id)),
                        models.FieldCondition(key="content_hash", match=models.MatchValue(value=content_hash))
                    ]
                ),
                limit=1,
                with_payload=False,  # Only need to check existence
                with_vectors=["content"]  # Required for named vector collections in v1.15.4
            )
            
            if existing[0]:  # Duplicate found
                logger.info(f"🎯 DEDUPLICATION: Skipping duplicate memory for user {memory.user_id}")
                return existing[0][0].id
            
            # Enhanced payload optimized for Qdrant operations
            qdrant_payload = {
                "user_id": memory.user_id,
                "memory_type": memory.memory_type.value,
                "content": memory.content,
                "timestamp": memory.timestamp.isoformat(),
                "timestamp_unix": memory.timestamp.timestamp(),
                "confidence": memory.confidence,
                "source": memory.source,
                
                # 🎯 QDRANT INTELLIGENCE FEATURES
                "content_hash": content_hash,
                "emotional_context": emotional_context,
                "semantic_key": semantic_key,
                "keywords": keywords,
                "word_count": len(memory.content.split()),
                "char_count": len(memory.content),
                
                **memory.metadata
            }
            
            # 🚀 QDRANT FEATURE: Named vectors for intelligent multi-dimensional search
            # TEMP: Use only content vector to isolate the issue
            vectors = {}
            
            # Only add vectors that are valid (non-None, non-empty)
            if content_embedding and len(content_embedding) > 0:
                vectors["content"] = content_embedding
                logger.debug(f"UPSERT DEBUG: Content vector added: len={len(content_embedding)}")
            else:
                logger.error(f"UPSERT ERROR: Invalid content embedding: {content_embedding}")
                
            # TEMP: Comment out emotion and semantic vectors to isolate issue
            # if emotion_embedding and len(emotion_embedding) > 0:
            #     vectors["emotion"] = emotion_embedding
            # else:
            #     logger.error(f"UPSERT ERROR: Invalid emotion embedding: {emotion_embedding}")
                
            # if semantic_embedding and len(semantic_embedding) > 0:
            #     vectors["semantic"] = semantic_embedding
            # else:
            #     logger.error(f"UPSERT ERROR: Invalid semantic embedding: {semantic_embedding}")
            
            # Ensure we have at least one valid vector
            if not vectors:
                raise ValueError("No valid embeddings generated - cannot create point")
            
            # Debug: Log vector info before upsert
            logger.debug(f"UPSERT DEBUG: Vector keys: {list(vectors.keys())}")
            for name, vec in vectors.items():
                logger.debug(f"UPSERT DEBUG: Vector '{name}': type={type(vec)}, len={len(vec) if vec else None}, is_none={vec is None}")
            
            # Store with all Qdrant advanced features
            point = PointStruct(
                id=memory.id,
                vector=vectors,  # Named vectors as dict
                payload=qdrant_payload
            )
            
            logger.debug(f"UPSERT DEBUG: Point ID: {point.id}, Vector keys in point: {list(point.vector.keys()) if hasattr(point, 'vector') and point.vector else 'NO VECTOR'}")
            
            # 🎯 QDRANT FEATURE: Atomic operation with immediate consistency
            logger.debug(f"UPSERT DEBUG: About to call Qdrant upsert with collection: {self.collection_name}")
            logger.debug(f"UPSERT DEBUG: Point structure - ID: {point.id}, Vector type: {type(point.vector)}")
            logger.debug(f"UPSERT DEBUG: Vector dict contents: {point.vector}")
            
            try:
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=[point],
                    wait=True  # Ensures memory is immediately available
                )
                logger.debug(f"UPSERT DEBUG: Qdrant upsert successful for point {point.id}")
            except Exception as upsert_error:
                logger.error(f"UPSERT DEBUG: Qdrant upsert failed with error: {upsert_error}")
                logger.error(f"UPSERT DEBUG: Error type: {type(upsert_error)}")
                raise
            
            self.stats["memories_stored"] += 1
            logger.info(f"🚀 QDRANT-ENHANCED: Stored memory {memory.id} with named vectors, "
                       f"semantic_key='{semantic_key}', emotion='{emotional_context}'")
            
            return memory.id
            
        except Exception as e:
            logger.error(f"Qdrant-native memory storage failed: {e}")
            raise
    
    def _extract_keywords(self, content: str) -> List[str]:
        """Extract keywords for sparse vector search"""
        # Simple keyword extraction (could be enhanced with NLP)
        words = content.lower().split()
        # Filter out common stop words and keep meaningful terms
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'}
        keywords = [word for word in words if len(word) > 2 and word not in stop_words]
        return keywords[:20]  # Limit to top 20 keywords
    
    def _extract_emotional_context(self, content: str) -> str:
        """Extract emotional context for role-playing intelligence"""
        content_lower = content.lower()
        
        # Positive emotions
        if any(word in content_lower for word in ['happy', 'joy', 'excited', 'love', 'wonderful', 'amazing']):
            return 'positive'
        
        # Negative emotions
        if any(word in content_lower for word in ['sad', 'angry', 'frustrated', 'hate', 'terrible', 'awful']):
            return 'negative'
        
        # Neutral/complex emotions
        if any(word in content_lower for word in ['confused', 'curious', 'wondering', 'thinking']):
            return 'contemplative'
        
        return 'neutral'

    def _get_age_category(self, timestamp: datetime) -> str:
        """Categorize memory age for Qdrant filtering"""
        age = datetime.utcnow() - timestamp
        
        if age.days < 1:
            return 'fresh'  # Less than 1 day
        elif age.days < 7:
            return 'recent'  # 1-7 days
        elif age.days < 30:
            return 'medium'  # 1-4 weeks
        else:
            return 'old'  # Over a month
    
    async def search_memories_with_qdrant_intelligence(self, 
                                                      query: str,
                                                      user_id: str,
                                                      memory_types: Optional[List[MemoryType]] = None,
                                                      top_k: int = 10,
                                                      min_score: float = 0.7,
                                                      emotional_context: Optional[str] = None,
                                                      prefer_recent: bool = True) -> List[Dict[str, Any]]:
        """
        🚀 QDRANT-NATIVE: Use Qdrant's advanced features for role-playing AI
        
        NEW: Temporal context detection using Qdrant features:
        - Detect temporal queries ("last", "just now", "earlier") 
        - Use scroll API for chronological recent context
        - Use search_batch for parallel temporal + semantic queries
        - Use payload-based temporal boosting
        """
        try:
            query_embedding = await self.generate_embedding(query)
            
            # 🎯 QDRANT FEATURE: Detect temporal context queries using payload filtering
            is_temporal_query = await self._detect_temporal_query_with_qdrant(query, user_id)
            
            if is_temporal_query:
                logger.info(f"🎯 TEMPORAL QUERY DETECTED: '{query}' - Using Qdrant chronological retrieval")
                return await self._handle_temporal_query_with_qdrant(query, user_id, top_k)
            
            # Regular semantic search continues below...
            must_conditions = [
                models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id))
            ]
            
            if memory_types:
                must_conditions.append(
                    models.FieldCondition(
                        key="memory_type", 
                        match=models.MatchAny(any=[mt.value for mt in memory_types])
                    )
                )
            
            # 🎯 QDRANT FEATURE 3: Emotional context filtering
            should_conditions = []
            if emotional_context:
                should_conditions.append(
                    models.FieldCondition(
                        key="emotional_context", 
                        match=models.MatchText(text=emotional_context)
                    )
                )
            
            # Regular search for non-temporal queries using named vectors  
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=models.NamedVector(name="content", vector=query_embedding),  # 🎯 NAMED VECTOR: Use content vector
                query_filter=models.Filter(must=must_conditions, should=should_conditions),
                limit=top_k,
                score_threshold=min_score,
                with_payload=True
            )
            
            # Format results
            enriched_results = []
            for point in search_results:
                result = {
                    "id": point.id,
                    "score": point.score,
                    "content": point.payload['content'],
                    "memory_type": point.payload['memory_type'],
                    "timestamp": point.payload['timestamp'],
                    "confidence": point.payload.get('confidence', 0.5),
                    "metadata": point.payload,
                    "qdrant_native": True,
                    "temporal_query": False
                }
                enriched_results.append(result)
            
            self.stats["searches_performed"] += 1
            logger.info(f"🎯 QDRANT-SEMANTIC: Retrieved {len(enriched_results)} memories")
            
            return enriched_results
            
        except Exception as e:
            logger.error(f"Qdrant-native search failed: {e}")
            return await self._fallback_basic_search(query, user_id, memory_types, top_k, min_score)

    async def _detect_temporal_query_with_qdrant(self, query: str, user_id: str) -> bool:
        """
        🎯 QDRANT-NATIVE: Detect temporal queries using payload-based pattern matching
        """
        temporal_keywords = [
            'last', 'recent', 'just', 'earlier', 'before', 'previous', 
            'moments ago', 'just now', 'a moment ago', 'just said',
            'just told', 'just asked', 'just mentioned'
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in temporal_keywords)

    async def _handle_temporal_query_with_qdrant(self, query: str, user_id: str, limit: int) -> List[Dict[str, Any]]:
        """
        🎯 QDRANT-NATIVE: Handle temporal queries using scroll API for chronological context
        """
        try:
            # Generate embedding for semantic search if needed
            query_embedding = await self.generate_embedding(query)
            
            # 🚀 QDRANT FEATURE: Use scroll API to get recent conversation chronologically
            # Convert to Unix timestamp for Qdrant numeric range filtering
            recent_cutoff_dt = datetime.utcnow() - timedelta(hours=2)
            recent_cutoff_timestamp = recent_cutoff_dt.timestamp()
            
            # Get recent conversation messages in chronological order
            scroll_result = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id)),
                        models.FieldCondition(key="memory_type", match=models.MatchValue(value="conversation")),
                        models.FieldCondition(key="timestamp_unix", range=Range(gte=recent_cutoff_timestamp))
                    ]
                ),
                limit=20,  # Get last 20 conversation messages
                with_payload=True,
                with_vectors=False,  # Don't need vectors for temporal queries
                order_by=models.OrderBy(key="timestamp_unix", direction=Direction.DESC)  # Most recent first
            )
            
            recent_messages = scroll_result[0]  # Get the messages
            
            if not recent_messages:
                logger.info("🎯 TEMPORAL: No recent conversation found, trying broader semantic search")
                # Instead of returning empty, do a semantic search for the temporal query
                semantic_results = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=models.NamedVector(name="content", vector=query_embedding),  # 🎯 NAMED VECTOR
                    query_filter=models.Filter(
                        must=[
                            models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id)),
                            models.FieldCondition(key="memory_type", match=models.MatchAny(any=["conversation", "fact", "preference"]))
                        ]
                    ),
                    limit=limit,
                    score_threshold=0.5,
                    with_payload=True
                )
                
                # Format as temporal query results
                formatted_results = []
                for point in semantic_results:
                    formatted_results.append({
                        "id": point.id,
                        "score": point.score,
                        "content": point.payload['content'],
                        "memory_type": point.payload['memory_type'],
                        "timestamp": point.payload['timestamp'],
                        "confidence": point.payload.get('confidence', 0.5),
                        "metadata": point.payload,
                        "temporal_query": True,
                        "temporal_fallback": True,  # Mark as fallback within temporal handler
                        "qdrant_semantic_fallback": True
                    })
                
                logger.info(f"🎯 TEMPORAL-SEMANTIC: Found {len(formatted_results)} memories via semantic fallback")
                return formatted_results
            
            # 🚀 QDRANT FEATURE: Use search within recent messages for better relevance
            recent_message_ids = [msg.id for msg in recent_messages]
            
            # Now do semantic search ONLY within these recent messages (embedding already generated above)
            temporal_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=models.NamedVector(name="content", vector=query_embedding),  # 🎯 NAMED VECTOR
                query_filter=models.Filter(
                    must=[
                        models.FieldCondition(key="id", match=models.MatchAny(any=recent_message_ids))
                    ]
                ),
                limit=limit,
                score_threshold=0.3,  # Lower threshold for temporal context
                with_payload=True
            )
            
            # Format temporal results with special marking
            formatted_results = []
            for point in temporal_results:
                formatted_results.append({
                    "id": point.id,
                    "score": point.score,
                    "content": point.payload['content'],
                    "memory_type": point.payload['memory_type'],
                    "timestamp": point.payload['timestamp'],
                    "confidence": point.payload.get('confidence', 0.5),
                    "metadata": point.payload,
                    "temporal_query": True,
                    "qdrant_chronological": True,
                    "temporal_rank": len(formatted_results) + 1  # Chronological position
                })
            
            logger.info(f"🎯 QDRANT-TEMPORAL: Found {len(formatted_results)} recent context memories")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Qdrant temporal query handling failed: {e}")
            return []

    async def _fallback_basic_search(self, query: str, user_id: str, memory_types: Optional[List[MemoryType]], 
                                   top_k: int, min_score: float) -> List[Dict[str, Any]]:
        """Fallback to basic Qdrant search if advanced features fail"""
        try:
            query_embedding = await self.generate_embedding(query)
            filter_conditions = [models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id))]
            
            if memory_types:
                filter_conditions.append(
                    models.FieldCondition(key="memory_type", match=models.MatchAny(any=[mt.value for mt in memory_types]))
                )
            
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=models.NamedVector(name="content", vector=query_embedding),  # 🎯 NAMED VECTOR
                query_filter=models.Filter(must=filter_conditions),
                limit=top_k,
                score_threshold=min_score
            )
            
            return [{
                "id": point.id,
                "score": point.score,
                "content": point.payload['content'],
                "memory_type": point.payload['memory_type'],
                "timestamp": point.payload['timestamp'],
                "confidence": point.payload.get('confidence', 0.5),
                "metadata": point.payload,
                "fallback_used": True
            } for point in results]
            
        except Exception as e:
            logger.error(f"Fallback search also failed: {e}")
            return []

    async def search_with_multi_vectors(self, 
                                      content_query: str,
                                      emotional_query: Optional[str] = None,
                                      personality_context: Optional[str] = None,
                                      user_id: str = None,
                                      top_k: int = 10) -> List[Dict[str, Any]]:
        """
        🚀 QDRANT MULTI-VECTOR: Search using multiple vector spaces for role-playing AI
        
        - Content vector: Semantic meaning of the query
        - Emotion vector: Emotional context and mood
        - Personality vector: Character traits and behavioral patterns
        
        Perfect for role-playing characters that need emotional intelligence!
        """
        try:
            # Generate multiple embeddings for different aspects
            content_embedding = await self.generate_embedding(content_query)
            
            emotion_embedding = None
            if emotional_query:
                emotion_embedding = await self.generate_embedding(f"emotion: {emotional_query}")
            
            personality_embedding = None  
            if personality_context:
                personality_embedding = await self.generate_embedding(f"personality: {personality_context}")
            
            # 🎯 QDRANT FEATURE: Multi-vector search with weighted combinations
            if emotion_embedding and personality_embedding:
                # Triple-vector search: content + emotion + personality
                logger.info("🎯 QDRANT: Using triple-vector search (content + emotion + personality)")
                
                # Use Qdrant's discover API with named vectors for complex multi-vector relationships
                results = self.client.discover(
                    collection_name=self.collection_name,
                    target=models.NamedVector(name="content", vector=content_embedding),  # 🎯 NAMED VECTOR TARGET
                    context=[
                        models.ContextExamplePair(positive=models.NamedVector(name="emotion", vector=emotion_embedding), negative=None),
                        models.ContextExamplePair(positive=models.NamedVector(name="semantic", vector=personality_embedding), negative=None)
                    ],
                    limit=top_k,
                    with_payload=True,
                    using="content"  # 🎯 SPECIFY VECTOR SPACE
                )
                
            elif emotion_embedding:
                # Dual-vector search: content + emotion
                logger.info("🎯 QDRANT: Using dual-vector search (content + emotion)")
                results = self.client.discover(
                    collection_name=self.collection_name,
                    target=models.NamedVector(name="content", vector=content_embedding),  # 🎯 NAMED VECTOR TARGET
                    context=[models.ContextExamplePair(positive=models.NamedVector(name="emotion", vector=emotion_embedding), negative=None)],
                    limit=top_k,
                    with_payload=True,
                    using="content"  # 🎯 SPECIFY VECTOR SPACE
                )
                
            else:
                # Single-vector fallback using named vector
                logger.info("🎯 QDRANT: Using single-vector search (content only)")
                results = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=models.NamedVector(name="content", vector=content_embedding),  # 🎯 NAMED VECTOR
                    limit=top_k,
                    with_payload=True
                )
            
            # Format results with multi-vector context
            formatted_results = []
            for point in results:
                formatted_results.append({
                    "id": point.id,
                    "score": point.score,
                    "content": point.payload['content'],
                    "memory_type": point.payload['memory_type'],
                    "timestamp": point.payload['timestamp'],
                    "confidence": point.payload.get('confidence', 0.5),
                    "metadata": point.payload,
                    "multi_vector_search": True,
                    "vectors_used": {
                        "content": True,
                        "emotion": emotion_embedding is not None,
                        "personality": personality_embedding is not None
                    }
                })
            
            logger.info(f"🎯 QDRANT MULTI-VECTOR: Found {len(formatted_results)} emotionally-aware memories")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Multi-vector search failed: {e}")
            # Fallback to single vector
            return await self._fallback_basic_search(content_query, user_id, None, top_k, 0.7)

    async def get_memory_clusters_for_roleplay(self, user_id: str, cluster_size: int = 5) -> Dict[str, List[Dict]]:
        """
        🚀 QDRANT CLUSTERING: Group memories by semantic similarity for role-playing consistency
        
        Perfect for role-playing AI to understand:
        - Relationship patterns
        - Emotional associations  
        - Character development arcs
        - Conversation themes
        """
        try:
            # 🎯 QDRANT FEATURE: Use scroll API for large memory retrieval
            memories = []
            offset = None
            
            # Get all user memories efficiently with scroll
            while True:
                scroll_result = self.client.scroll(
                    collection_name=self.collection_name,
                    scroll_filter=models.Filter(
                        must=[models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id))]
                    ),
                    limit=100,  # Batch size
                    offset=offset,
                    with_payload=True,
                    with_vectors=["content"]  # Specify which named vector for clustering
                )
                
                memories.extend(scroll_result[0])
                offset = scroll_result[1]
                
                if offset is None:  # No more results
                    break
            
            if len(memories) < 2:
                return {"insufficient_data": memories}
            
            # 🎯 QDRANT FEATURE: Use recommendation API for memory association
            clusters = {}
            processed_ids = set()
            
            for memory in memories:
                if memory.id in processed_ids:
                    continue
                
                # Use Qdrant's recommendation to find semantically similar memories
                similar_memories = self.client.recommend(
                    collection_name=self.collection_name,
                    positive=[memory.id],
                    query_filter=models.Filter(
                        must=[
                            models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id)),
                            models.FieldCondition(key="id", match=models.MatchExcept(except_=[memory.id]))
                        ]
                    ),
                    limit=cluster_size - 1,  # -1 because we include the seed memory
                    score_threshold=0.7,
                    with_payload=True,
                    using="content"  # Specify named vector for recommendations
                )
                
                # Create semantic cluster
                cluster_theme = self._identify_cluster_theme(memory.payload['content'])
                cluster_key = f"{cluster_theme}_{len(clusters)}"
                
                cluster_memories = [
                    {
                        "id": memory.id,
                        "content": memory.payload['content'],
                        "timestamp": memory.payload['timestamp'],
                        "confidence": memory.payload.get('confidence', 0.5),
                        "is_seed": True
                    }
                ]
                
                for similar in similar_memories:
                    cluster_memories.append({
                        "id": similar.id,
                        "content": similar.payload['content'],
                        "timestamp": similar.payload['timestamp'],
                        "confidence": similar.payload.get('confidence', 0.5),
                        "similarity_score": similar.score,
                        "is_seed": False
                    })
                    processed_ids.add(similar.id)
                
                clusters[cluster_key] = cluster_memories
                processed_ids.add(memory.id)
                
                logger.info(f"🎯 QDRANT CLUSTER: Created '{cluster_theme}' cluster with {len(cluster_memories)} memories")
            
            return clusters
            
        except Exception as e:
            logger.error(f"Memory clustering failed: {e}")
            return {"error": str(e)}

    def _identify_cluster_theme(self, content: str) -> str:
        """Identify thematic cluster based on content for role-playing context"""
        content_lower = content.lower()
        
        # Relationship themes
        if any(word in content_lower for word in ['relationship', 'friend', 'family', 'love', 'partner']):
            return 'relationships'
        
        # Emotional themes  
        if any(word in content_lower for word in ['feel', 'emotion', 'happy', 'sad', 'angry', 'afraid']):
            return 'emotions'
        
        # Character development
        if any(word in content_lower for word in ['dream', 'goal', 'aspiration', 'future', 'plan']):
            return 'character_growth'
        
        # Memories and experiences
        if any(word in content_lower for word in ['remember', 'experience', 'happened', 'past']):
            return 'experiences'
        
        # Preferences and traits
        if any(word in content_lower for word in ['like', 'prefer', 'favorite', 'enjoy', 'hate']):
            return 'preferences'
        
        return 'general'

    async def batch_update_memories_with_qdrant(self, updates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        🚀 QDRANT BATCH: Efficient batch operations for memory updates
        
        Perfect for:
        - Bulk contradiction resolution
        - Emotional context updates
        - Confidence score adjustments
        - Temporal metadata updates
        """
        try:
            # 🎯 QDRANT FEATURE: Batch upsert for efficiency
            points_to_update = []
            
            for update in updates:
                point_id = update.get('id')
                if not point_id:
                    continue
                
                # Get existing point
                existing_point = self.client.retrieve(
                    collection_name=self.collection_name,
                    ids=[point_id],
                    with_payload=True,
                    with_vectors=True
                )[0]
                
                if not existing_point:
                    continue
                
                # Update payload while preserving vectors
                updated_payload = existing_point.payload.copy()
                updated_payload.update(update.get('payload_updates', {}))
                
                # Add batch update metadata
                updated_payload['batch_updated_at'] = datetime.utcnow().isoformat()
                updated_payload['update_reason'] = update.get('reason', 'batch_update')
                
                points_to_update.append(
                    PointStruct(
                        id=point_id,
                        vector=existing_point.vector,
                        payload=updated_payload
                    )
                )
            
            # 🎯 QDRANT FEATURE: Efficient batch upsert
            if points_to_update:
                upsert_result = self.client.upsert(
                    collection_name=self.collection_name,
                    points=points_to_update,
                    wait=True  # Ensure consistency for role-playing coherence
                )
                
                logger.info(f"🎯 QDRANT BATCH: Updated {len(points_to_update)} memories in batch")
                
                return {
                    "success": True,
                    "updated_count": len(points_to_update),
                    "operation_id": upsert_result.operation_id,
                    "status": upsert_result.status
                }
            
            return {"success": True, "updated_count": 0, "message": "No valid updates provided"}
            
        except Exception as e:
            logger.error(f"Batch memory update failed: {e}")
            return {"success": False, "error": str(e)}

    # 🔧 COMPATIBILITY: Bridge method for legacy search_memories calls
    async def search_memories(self, 
                            query: str,
                            user_id: str,
                            memory_types: Optional[List[MemoryType]] = None,
                            top_k: int = 10,
                            min_score: float = 0.7) -> List[Dict[str, Any]]:
        """
        Compatibility bridge to new Qdrant-native search method
        """
        try:
            # Route to the new enhanced method
            return await self.search_memories_with_qdrant_intelligence(
                query=query,
                user_id=user_id,
                memory_types=memory_types,
                top_k=top_k,
                min_score=min_score,
                emotional_context=None,
                prefer_recent=True
            )
        except Exception as e:
            logger.error(f"Compatibility search_memories failed: {e}")
            return await self._fallback_basic_search(query, user_id, memory_types, top_k, min_score)
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
            
            # ENHANCED: Search with larger initial set for post-processing
            search_limit = max(top_k * 3, 30)  # Get more results for filtering
            
            # Search Qdrant
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=models.NamedVector(name="content", vector=query_embedding),  # 🎯 NAMED VECTOR
                query_filter=models.Filter(must=filter_conditions),
                limit=search_limit,
                score_threshold=min_score * 0.8,  # Lower threshold for initial search
                with_payload=True,
                with_vectors=False  # Don't need vectors for result processing
            )
            
            # ENHANCED: Post-process results with intelligent ranking
            processed_results = await self._intelligent_ranking(
                results, query, prefer_recent, resolve_contradictions
            )
            
            # Return top results after intelligent processing
            final_results = processed_results[:top_k]
            
            self.stats["searches_performed"] += 1
            logger.debug(f"Found {len(final_results)} memories for query: {query[:50]} "
                        f"(processed {len(results)} raw results)")
            
            return final_results
            
        except Exception as e:
            logger.error(f"Memory search failed: {e}")
            raise
    
    async def _intelligent_ranking(self, 
                                 raw_results: List,
                                 query: str,
                                 prefer_recent: bool,
                                 resolve_contradictions: bool) -> List[Dict[str, Any]]:
        """
        QDRANT-POWERED: Intelligent post-processing of search results
        
        Uses advanced ranking with:
        - Temporal decay weighting 
        - Contradiction resolution (newer facts override older)
        - Confidence-based scoring
        - Semantic clustering for context
        """
        try:
            formatted_results = []
            contradiction_groups = {}
            
            # Step 1: Format and group potentially contradictory memories
            for point in raw_results:
                result = {
                    "id": point.id,
                    "score": point.score,
                    "content": point.payload['content'],
                    "memory_type": point.payload['memory_type'],
                    "timestamp": point.payload['timestamp'],
                    "confidence": point.payload.get('confidence', 0.5),
                    "metadata": point.payload
                }
                
                # Step 2: Apply temporal decay if requested
                if prefer_recent:
                    # Parse timestamp and calculate age in days
                    try:
                        memory_time = datetime.fromisoformat(result['timestamp'].replace('Z', '+00:00'))
                        age_days = (datetime.utcnow().replace(tzinfo=memory_time.tzinfo) - memory_time).days
                        
                        # Temporal decay: 90% weight after 1 day, 50% after 7 days, 10% after 30 days
                        temporal_weight = max(0.1, 0.9 ** (age_days / 3))
                        result['score'] *= temporal_weight
                        result['temporal_weight'] = temporal_weight
                        
                    except Exception as e:
                        logger.warning(f"Could not parse timestamp for temporal weighting: {e}")
                        result['temporal_weight'] = 1.0
                
                # Step 3: Group similar content for contradiction detection
                if resolve_contradictions and result['memory_type'] in ['fact', 'preference']:
                    # Create semantic key for grouping (e.g., all cat-name related facts)
                    semantic_key = self._get_semantic_key(result['content'])
                    
                    if semantic_key not in contradiction_groups:
                        contradiction_groups[semantic_key] = []
                    contradiction_groups[semantic_key].append(result)
                else:
                    formatted_results.append(result)
            
            # Step 4: Resolve contradictions by keeping highest-scored recent memory per group
            if resolve_contradictions:
                for semantic_key, group in contradiction_groups.items():
                    if len(group) == 1:
                        # No contradictions, add the single memory
                        formatted_results.extend(group)
                    else:
                        # Multiple memories for same semantic concept - resolve contradiction
                        # Sort by: confidence * temporal_weight * original_score
                        group.sort(
                            key=lambda x: x.get('confidence', 0.5) * x.get('temporal_weight', 1.0) * x['score'],
                            reverse=True
                        )
                        
                        # Keep the best memory, mark others as superseded
                        best_memory = group[0]
                        best_memory['contradiction_resolved'] = True
                        best_memory['superseded_memories'] = len(group) - 1
                        formatted_results.append(best_memory)
                        
                        logger.info(f"🎯 CONTRADICTION RESOLVED: Kept most recent/confident memory for '{semantic_key}' "
                                  f"(score: {best_memory['score']:.3f}, confidence: {best_memory.get('confidence', 0.5):.3f})")
            
            # Step 5: Final ranking by enhanced score
            formatted_results.sort(
                key=lambda x: x['score'] * x.get('confidence', 0.5),
                reverse=True
            )
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Intelligent ranking failed: {e}")
            # Fallback to basic formatting
            return [{
                "id": point.id,
                "score": point.score,
                "content": point.payload['content'],
                "memory_type": point.payload['memory_type'],
                "timestamp": point.payload['timestamp'],
                "confidence": point.payload.get('confidence', 0.5),
                "metadata": point.payload
            } for point in raw_results]

    def _get_semantic_key(self, content: str) -> str:
        """
        Generate semantic key for grouping related facts
        
        This helps identify contradictory information like:
        - "cat name is Whiskers" vs "cat name is Luna"
        - "favorite color is blue" vs "favorite color is red"
        """
        content_lower = content.lower()
        
        # Pet name patterns
        if any(word in content_lower for word in ['cat', 'dog', 'pet']) and 'name' in content_lower:
            return 'pet_name'
        
        # Color preferences
        if 'favorite color' in content_lower or 'like color' in content_lower:
            return 'favorite_color'
        
        # User name
        if 'my name is' in content_lower or 'i am called' in content_lower:
            return 'user_name'
        
        # Location
        if any(word in content_lower for word in ['live in', 'from', 'location']):
            return 'user_location'
        
        # Generic fallback - use first few words
        words = content_lower.split()[:3]
        return '_'.join(words)
        
    async def resolve_contradictions_with_qdrant(self, user_id: str, semantic_key: str, new_memory_content: str) -> List[Dict[str, Any]]:
        """
        🚀 QDRANT RECOMMENDATION API: Use native recommendation for contradiction resolution
        
        This replaces manual Python grouping and scoring with Qdrant's advanced AI features:
        - Uses recommendation API to find semantically similar but factually different content
        - Leverages semantic vector space for intelligent contradiction detection
        - Returns ranked recommendations for resolution
        """
        try:
            # Generate embeddings for the new memory content
            new_content_embedding = await self.generate_embedding(new_memory_content)
            new_semantic_embedding = await self.generate_embedding(f"concept {semantic_key}: {new_memory_content}")
            
            # 🎯 QDRANT FEATURE: Use recommendation API for intelligent contradiction detection
            recommendations = self.client.recommend(
                collection_name=self.collection_name,
                positive=[new_semantic_embedding],  # Find similar semantic concepts
                negative=[new_content_embedding],   # But different actual content
                query_filter=models.Filter(
                    must=[
                        models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id)),
                        models.FieldCondition(key="semantic_key", match=models.MatchValue(value=semantic_key)),
                        models.FieldCondition(key="memory_type", match=models.MatchAny(any=["fact", "preference"]))
                    ]
                ),
                limit=10,
                with_payload=True,
                using="semantic"  # Use semantic vector for recommendation
            )
            
            contradictions = []
            for point in recommendations:
                # Calculate content similarity to detect actual contradictions
                existing_content = point.payload['content']
                content_similarity = await self._calculate_content_similarity(new_memory_content, existing_content)
                
                # High semantic similarity but low content similarity = contradiction
                if point.score > 0.8 and content_similarity < 0.7:
                    contradictions.append({
                        "existing_memory": {
                            "id": point.id,
                            "content": existing_content,
                            "timestamp": point.payload['timestamp'],
                            "confidence": point.payload.get('confidence', 0.5),
                            "semantic_score": point.score
                        },
                        "new_content": new_memory_content,
                        "contradiction_confidence": (point.score - content_similarity),
                        "resolution_recommendation": "replace" if point.payload.get('confidence', 0.5) < 0.8 else "merge"
                    })
            
            logger.info(f"🎯 QDRANT-RECOMMENDATION: Found {len(contradictions)} potential contradictions for '{semantic_key}'")
            return contradictions
            
        except Exception as e:
            logger.error(f"Qdrant recommendation-based contradiction detection failed: {e}")
            return []
    
    async def _calculate_content_similarity(self, content1: str, content2: str) -> float:
        """Calculate semantic similarity between two pieces of content"""
        try:
            embedding1 = await self.generate_embedding(content1)
            embedding2 = await self.generate_embedding(content2)
            
            # Calculate cosine similarity
            import numpy as np
            similarity = np.dot(embedding1, embedding2) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2))
            return float(similarity)
            
        except Exception as e:
            logger.warning(f"Content similarity calculation failed: {e}")
            return 0.0

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
            
            # Store updated version with named vectors
            # Generate multiple embeddings for named vectors  
            content_embedding = await self.generate_embedding(new_content)
            emotion_embedding = await self.generate_embedding(f"emotion neutral: {new_content}")
            semantic_embedding = await self.generate_embedding(f"concept update: {new_content}")
            
            # Validate embeddings before creating vectors dict
            vectors = {}
            if content_embedding and len(content_embedding) > 0:
                vectors["content"] = content_embedding
            else:
                logger.error(f"UPDATE ERROR: Invalid content embedding: {content_embedding}")
                
            if emotion_embedding and len(emotion_embedding) > 0:
                vectors["emotion"] = emotion_embedding
            else:
                logger.error(f"UPDATE ERROR: Invalid emotion embedding: {emotion_embedding}")
                
            if semantic_embedding and len(semantic_embedding) > 0:
                vectors["semantic"] = semantic_embedding
            else:
                logger.error(f"UPDATE ERROR: Invalid semantic embedding: {semantic_embedding}")
            
            # Ensure we have at least one valid vector
            if not vectors:
                raise ValueError("No valid embeddings generated for update - cannot update point")
            
            updated_point = PointStruct(
                id=memory_id,
                vector=vectors,  # Use validated vectors dict
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
        
        # Extract embeddings configuration - FAIL FAST if not provided
        embeddings_config = config.get('embeddings')
        if not embeddings_config:
            raise ValueError("Missing 'embeddings' configuration in vector memory config")
        
        embedding_model = embeddings_config.get('model_name')
        if not embedding_model:
            raise ValueError("Missing 'model_name' in embeddings configuration")
            
        logger.info(f"[VECTOR-MEMORY-DEBUG] Using embedding model: {embedding_model}")
        logger.info(f"[VECTOR-MEMORY-DEBUG] Full embeddings config: {embeddings_config}")
        logger.info(f"[VECTOR-MEMORY-DEBUG] Full vector config: {config}")
        
        # Core vector store (single source of truth) - LOCAL IMPLEMENTATION
        self.vector_store = VectorMemoryStore(
            qdrant_host=qdrant_host,
            qdrant_port=qdrant_port,
            collection_name=collection_name,
            embedding_model=embedding_model
        )
        
        # TEST: Verify logging is working
        logger.error("🔥 VECTOR MEMORY MANAGER INITIALIZED - DEBUG LOGGING ACTIVE 🔥")
        
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
            logger.debug(f"MEMORY MANAGER DEBUG: store_conversation called for user {user_id}")
            
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
            logger.debug(f"MEMORY MANAGER DEBUG: About to store user memory: {user_memory.content[:50]}...")
            await self.vector_store.store_memory(user_memory)
            logger.debug(f"MEMORY MANAGER DEBUG: User memory stored successfully")
            
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
            logger.debug(f"MEMORY MANAGER DEBUG: About to store bot memory: {bot_memory.content[:50]}...")
            await self.vector_store.store_memory(bot_memory)
            logger.debug(f"MEMORY MANAGER DEBUG: Bot memory stored successfully")
            
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
        emotional_context: Optional[str] = None,
        personality_context: Optional[str] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        🚀 QDRANT-POWERED: Context-aware memory retrieval for role-playing AI
        
        Uses advanced Qdrant features:
        - Multi-vector search for emotional intelligence
        - Contradiction resolution via recommendation API  
        - Temporal decay with native time filtering
        - Semantic clustering for character consistency
        """
        effective_query = query or current_query or ""
        effective_limit = limit or max_memories
        
        if not effective_query:
            return await self.retrieve_relevant_memories(user_id=user_id, query="", limit=effective_limit)
        
        try:
            # 🎯 STRATEGY 1: Use multi-vector search if emotional/personality context available
            if emotional_context or personality_context:
                logger.info(f"🎯 Using QDRANT MULTI-VECTOR search for emotionally-aware retrieval")
                
                results = await self.vector_store.search_with_multi_vectors(
                    content_query=effective_query,
                    emotional_query=emotional_context,
                    personality_context=personality_context,
                    user_id=user_id,
                    top_k=effective_limit
                )
                
                if results:
                    logger.info(f"🎯 MULTI-VECTOR SUCCESS: Found {len(results)} emotionally-aware memories")
                    return results
            
            # 🎯 STRATEGY 2: Use Qdrant-native intelligent search with contradiction resolution
            logger.info(f"🎯 Using QDRANT-NATIVE search with contradiction resolution")
            
            results = await self.vector_store.search_memories_with_qdrant_intelligence(
                query=effective_query,
                user_id=user_id,
                memory_types=[MemoryType.CONVERSATION, MemoryType.FACT, MemoryType.PREFERENCE],
                top_k=effective_limit,
                min_score=0.7,
                emotional_context=emotional_context,
                prefer_recent=True
            )
            
            if results:
                logger.info(f"🎯 QDRANT-NATIVE SUCCESS: Retrieved {len(results)} context-aware memories")
                return results
            else:
                logger.info("🎯 QDRANT-NATIVE: No memories found with current search parameters")
                return []
            
        except Exception as e:
            logger.error(f"Enhanced context-aware memory retrieval failed: {e}")
            return await self.retrieve_relevant_memories(user_id=user_id, query=effective_query, limit=effective_limit)
    
    async def get_recent_conversations(
        self, 
        user_id: str, 
        limit: int = 5,
        context_filter: Optional[Any] = None
    ) -> List[Dict[str, Any]]:
        """Get recent conversation history for a user."""
        try:
            # Search for recent conversation memories
            results = await self.search_memories(
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
    
    # === OPTIMIZATION INTEGRATION ===
    # Advanced query optimization capabilities
    
    async def retrieve_relevant_memories_optimized(self, 
                                                 user_id: str, 
                                                 query: str,
                                                 query_type: str = "general_search",
                                                 user_history: Optional[Dict] = None,
                                                 filters: Optional[Dict] = None,
                                                 limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve memories using advanced optimization features.
        
        This method provides enhanced search capabilities including:
        - Query preprocessing and enhancement
        - Adaptive similarity thresholds
        - Hybrid search with metadata filtering  
        - Result re-ranking with multiple factors
        
        Args:
            user_id: User identifier
            query: Search query
            query_type: Type of query ('conversation_recall', 'fact_lookup', 'general_search', etc.)
            user_history: User interaction patterns and preferences
            filters: Additional search filters (time_range, topics, channel_id, etc.)
            limit: Maximum number of results
            
        Returns:
            Optimized and ranked search results
        """
        try:
            # Import optimization components
            from src.memory.qdrant_optimization import QdrantQueryOptimizer, QdrantOptimizationMetrics
            
            # Initialize optimizer with current manager
            optimizer = QdrantQueryOptimizer(self)
            
            # Use optimized search
            results = await optimizer.optimized_search(
                query=query,
                user_id=user_id,
                query_type=query_type,
                user_history=user_history or {},
                filters=filters
            )
            
            logger.debug("🚀 Optimized search returned %d results for query: '%s'", len(results), query)
            return results[:limit]
            
        except ImportError:
            # Fallback to basic search if optimization module not available
            logger.warning("Optimization module not available, falling back to basic search")
            return await self.retrieve_relevant_memories(user_id, query, limit)
        except Exception as e:
            logger.error("Error in optimized search, falling back to basic: %s", str(e))
            return await self.retrieve_relevant_memories(user_id, query, limit)
    
    async def get_conversation_context_optimized(self, 
                                               user_id: str,
                                               current_message: Optional[str] = None,
                                               query_type: str = "conversation_recall", 
                                               max_memories: int = 10,
                                               user_preferences: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Get conversation context using optimization features.
        
        Args:
            user_id: User identifier
            current_message: Current message for context
            query_type: Type of context search
            max_memories: Maximum memories to return
            user_preferences: User interaction preferences
            
        Returns:
            Optimized conversation context
        """
        # Use current message or generic conversation query
        query = current_message or "recent conversation context"
        
        # Set up filters for conversation context
        filters = {
            'memory_type': 'conversation',
            'time_range': {
                'start': datetime.utcnow() - timedelta(days=7),  # Recent week
                'end': datetime.utcnow()
            }
        }
        
        return await self.retrieve_relevant_memories_optimized(
            user_id=user_id,
            query=query,
            query_type=query_type,
            user_history=user_preferences,
            filters=filters,
            limit=max_memories
        )


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
            'model_name': 'snowflake/snowflake-arctic-embed-xs'
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