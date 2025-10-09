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
import os
import re
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
from pydantic import BaseModel, Field

# Performance & Async (PostgreSQL for system data, Redis disabled for vector-native approach)
import asyncpg
# import redis.asyncio as redis  # DISABLED: Using vector-native memory only

# Import memory context classes for Discord context classification
from src.memory.context_aware_memory_security import (
    MemoryContext, 
    MemoryContextType, 
    ContextSecurity
)

# Import enhanced vector analysis components
from src.intelligence.enhanced_7d_vector_analyzer import Enhanced7DVectorAnalyzer

# Import multi-vector intelligence system for Sprint 2 enhancement
from src.memory.multi_vector_intelligence import (
    create_multi_vector_search_coordinator,
    MultiVectorSearchCoordinator,
    QueryType,
    VectorStrategy
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


class MemoryTier(Enum):
    """Three-tier memory architecture for intelligent memory management"""
    SHORT_TERM = "short_term"      # Recent conversations, temporary facts (1-7 days)
    MEDIUM_TERM = "medium_term"    # Important conversations, established facts (1-30 days)
    LONG_TERM = "long_term"        # Highly significant memories, core relationships (permanent)


def normalize_bot_name(bot_name: str) -> str:
    """
    Normalize bot name for consistent memory storage and retrieval.
    
    CRITICAL: This function prevents memory isolation failures due to:
    - Case sensitivity: "Elena" vs "elena" 
    - Space handling: "Marcus Chen" vs "marcus_chen"
    - Special characters and inconsistent formatting
    
    Rules:
    - Convert to lowercase for case-insensitive matching
    - Replace spaces with underscores for system compatibility
    - Remove special characters except underscore/hyphen/alphanumeric
    - Handle empty/None values gracefully
    
    Examples:
    - "Elena" -> "elena"
    - "Marcus Chen" -> "marcus_chen" 
    - "Dream of the Endless" -> "dream_of_the_endless"
    - None -> "unknown"
    """
    if not bot_name or not isinstance(bot_name, str):
        return "unknown"
    
    # Step 1: Trim and lowercase
    normalized = bot_name.strip().lower()
    
    # Step 2: Replace spaces with underscores
    normalized = re.sub(r'\s+', '_', normalized)
    
    # Step 3: Remove special characters except underscore/hyphen/alphanumeric
    normalized = re.sub(r'[^a-z0-9_-]', '', normalized)
    
    # Step 4: Collapse multiple underscores/hyphens
    normalized = re.sub(r'[_-]+', '_', normalized)
    
    # Step 5: Remove leading/trailing underscores
    normalized = normalized.strip('_-')
    
    return normalized if normalized else "unknown"


def get_normalized_bot_name_from_env() -> str:
    """Get normalized bot name from environment variables with fallback"""
    raw_bot_name = (
        os.getenv("DISCORD_BOT_NAME") or 
        os.getenv("BOT_NAME") or 
        "unknown"
    )
    return normalize_bot_name(raw_bot_name.strip())


@dataclass
class VectorMemory:
    """Unified memory object for vector storage with three-tier architecture"""
    id: str
    user_id: str
    memory_type: MemoryType
    content: str
    memory_tier: MemoryTier = MemoryTier.SHORT_TERM  # Default to short-term
    embedding: Optional[List[float]] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None
    confidence: float = 0.8
    source: str = "system"
    tier_promotion_date: Optional[datetime] = None  # When promoted to higher tier
    tier_demotion_date: Optional[datetime] = None   # When demoted to lower tier
    decay_protection: bool = False  # Protects from automatic decay
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}
    
    def get_tier_age_days(self) -> int:
        """Get age in days since last tier change or creation"""
        reference_date = self.tier_promotion_date or self.tier_demotion_date or self.timestamp
        if reference_date:
            return (datetime.utcnow() - reference_date).days
        return 0


class VectorMemoryStore:
    """
    Production vector memory store using LOCAL Qdrant + fastembed
    
    This is the single source of truth for all WhisperEngine memory.
    Replaces the problematic hierarchical Redis/PostgreSQL/legacy vector store system.
    Local-first deployment - no external API dependencies.
    """
    
    def __init__(self, 
                 qdrant_host: str = "localhost",
                 qdrant_port: int = 6333,
                 collection_name: str = "whisperengine_memory",
                 embedding_model: str = ""):  # Use sentence-transformers/all-MiniLM-L6-v2 (best 384D quality)
        
        # Initialize Qdrant (Local Vector DB in Docker)
        self.client = QdrantClient(host=qdrant_host, port=qdrant_port)
        self.collection_name = collection_name
        
        # Initialize fastembed (Local embedding model) with proper cache configuration
        cache_dir = os.environ.get('FASTEMBED_CACHE_PATH', '/root/.cache/fastembed')
        if embedding_model:
            self.embedder = TextEmbedding(model_name=embedding_model, cache_dir=cache_dir)
        else:
            # Use sentence-transformers/all-MiniLM-L6-v2 (best 384D quality) - excellent conversation understanding
            self.embedder = TextEmbedding(cache_dir=cache_dir)
        # Get embedding dimension from the model
        test_embedding = list(self.embedder.embed(["test"]))[0]
        self.embedding_dimension = len(test_embedding)
        
        # Initialize collection if it doesn't exist
        self._ensure_collection_exists()
        
        # Initialize enhanced emotion analyzer for consistent emotion detection
        self._enhanced_emotion_analyzer = None
        try:
            from src.intelligence.enhanced_vector_emotion_analyzer import create_enhanced_emotion_analyzer
            # Create self-referencing memory manager for emotion analysis
            self._enhanced_emotion_analyzer = create_enhanced_emotion_analyzer(None)
            logger.info("Enhanced emotion analyzer initialized for consistent emotion detection")
        except ImportError as e:
            logger.warning("Enhanced emotion analyzer not available: %s", e)
        
        # Enhanced vector analyzer DISABLED - using core 3D vectors only (content, emotion, semantic)
        # Design: Optimized 3D vector system provides sufficient intelligence with better performance
        self._vector_7d_analyzer = None
        logger.info("🎯 Using optimized 3D vector system (content, emotion, semantic)")
        
        # Initialize multi-vector intelligence coordinator for Sprint 2 enhancement
        try:
            self._multi_vector_coordinator = create_multi_vector_search_coordinator(
                vector_memory_system=self
            )
            logger.info("Multi-vector intelligence coordinator initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize multi-vector coordinator: {e}")
            self._multi_vector_coordinator = None
        
        # Performance tracking
        self.stats = {
            "embeddings_generated": 0,
            "searches_performed": 0,
            "memories_stored": 0,
            "contradictions_detected": 0
        }
        
        logger.info(f"VectorMemoryStore initialized: {qdrant_host}:{qdrant_port}, "
                   f"collection={collection_name}, embedding_dim={self.embedding_dimension}")
    
    def _extract_named_vector(self, point_vector, vector_name: str = "content"):
        """
        Extract a specific named vector from Qdrant point vector data.
        
        Args:
            point_vector: Vector data from Qdrant point (must be dict with named vectors)
            vector_name: Name of the vector to extract (default: "content")
            
        Returns:
            List of floats representing the vector, or None if not found
        """
        if point_vector is None:
            return None
            
        # Only handle named vectors format (current correct format)
        if isinstance(point_vector, dict):
            return point_vector.get(vector_name)
        
        # Log error for unexpected formats
        logger.error(f"Unexpected vector format: {type(point_vector)} - only dict format supported")
        return None
    
    def _create_named_vectors_dict(self, point_vector):
        """
        Create proper named vectors dict from point vector data.
        
        Args:
            point_vector: Vector data from existing point (must be dict with named vectors)
            
        Returns:
            Dict with named vectors structure, or empty dict if invalid
        """
        if isinstance(point_vector, dict):
            # Already in correct named vector format
            return point_vector
        else:
            logger.error(f"Cannot handle vector type {type(point_vector)} - only dict format supported")
            return {}
    
    def _get_multi_emotion_payload(self) -> Dict[str, Any]:
        """
        Extract multi-emotion payload from last RoBERTa analysis for storage
        
        Returns:
            Dictionary with multi-emotion data for Qdrant payload
        """
        if not hasattr(self, '_last_emotion_analysis') or not self._last_emotion_analysis:
            return {}
        
        analysis = self._last_emotion_analysis
        payload = {}
        
        # Store secondary emotions if multiple emotions detected
        if analysis.get('is_multi_emotion', False) and analysis.get('all_emotions'):
            all_emotions = analysis['all_emotions']
            primary = analysis['primary_emotion']
            
            # Store all emotions as separate fields for easy querying
            payload['all_emotions_json'] = str(all_emotions)  # JSON string for full data
            payload['emotion_count'] = len(all_emotions)
            payload['is_multi_emotion'] = True
            
            # Store top secondary emotions (up to 3)
            secondary_emotions = {k: v for k, v in all_emotions.items() if k != primary}
            if secondary_emotions:
                sorted_secondary = sorted(secondary_emotions.items(), key=lambda x: x[1], reverse=True)[:3]
                
                for i, (emotion, intensity) in enumerate(sorted_secondary):
                    payload[f'secondary_emotion_{i+1}'] = emotion
                    payload[f'secondary_intensity_{i+1}'] = intensity
            
            # Store emotion complexity metrics
            intensities = list(all_emotions.values())
            payload['emotion_variance'] = max(intensities) - min(intensities) if len(intensities) > 1 else 0.0
            payload['emotion_dominance'] = analysis['primary_intensity'] / sum(intensities) if sum(intensities) > 0 else 1.0
        else:
            payload['is_multi_emotion'] = False
            payload['emotion_count'] = 1
            
        # Store RoBERTa confidence
        payload['roberta_confidence'] = analysis.get('confidence', 0.0)
        
        return payload
    
    def _create_mixed_emotion_embedding_text(self, primary_emotion: str, content: str) -> str:
        """
        Create fidelity-preserving emotion embedding text from RoBERTa multi-emotion analysis
        
        This preserves mixed emotion fidelity that would otherwise be lost when embedding
        only the primary emotion. Uses the stored _last_emotion_analysis from RoBERTa.
        
        Args:
            primary_emotion: The primary emotion (fallback if no analysis available)
            content: The original content being embedded
            
        Returns:
            Enhanced emotion embedding text preserving multi-emotion context
            
        Examples:
            Single emotion: "emotion joy: content"
            Mixed emotions: "emotion joy with excitement: content"
            Complex mix: "emotion joy mixed with excitement and surprise: content"
        """
        # Check if we have multi-emotion analysis available
        if not hasattr(self, '_last_emotion_analysis') or not self._last_emotion_analysis:
            # Fallback to simple primary emotion
            return f"emotion {primary_emotion}: {content}"
        
        analysis = self._last_emotion_analysis
        all_emotions = analysis.get('all_emotions', {})
        
        # If no multi-emotion data or only one emotion, use simple format
        if not all_emotions or len(all_emotions) <= 1:
            return f"emotion {primary_emotion}: {content}"
        
        # Filter emotions above threshold (0.1 = 10% confidence) and sort by intensity
        emotion_threshold = 0.1
        significant_emotions = {
            emotion: score for emotion, score in all_emotions.items() 
            if score >= emotion_threshold
        }
        
        # Sort by intensity (highest first)
        sorted_emotions = sorted(significant_emotions.items(), key=lambda x: x[1], reverse=True)
        
        # Create composite emotion description preserving fidelity
        if len(sorted_emotions) == 1:
            # Single significant emotion
            emotion_desc = sorted_emotions[0][0]
        elif len(sorted_emotions) == 2:
            # Two emotions - use "with" pattern  
            emotion_desc = f"{sorted_emotions[0][0]} with {sorted_emotions[1][0]}"
        else:
            # Complex mix - use "mixed with" pattern (limit to top 3 for embedding efficiency)
            primary = sorted_emotions[0][0]
            secondary = [e[0] for e in sorted_emotions[1:3]]  # Top 2 secondary emotions
            emotion_desc = f"{primary} mixed with {' and '.join(secondary)}"
        
        # Create final embedding text
        embedding_text = f"emotion {emotion_desc}: {content}"
        
        # Log for debugging mixed emotion fidelity
        emotion_summary = {e: f"{s:.2f}" for e, s in sorted_emotions[:3]}
        logger.debug(f"🎭 MIXED EMOTION FIDELITY: '{emotion_desc}' from {emotion_summary}")
        
        return embedding_text
    
    def _ensure_collection_exists(self):
        """
        🚀 QDRANT-NATIVE: Create advanced collection with named vectors
        
        Features:
        - Named vectors for multi-dimensional search (7 dimensions: content, emotion, semantic, relationship, personality, interaction, temporal)
        - Optimized indexing for payload fields
        - Performance optimizations
        """
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]

            if self.collection_name not in collection_names:
                # 🎯 QDRANT FEATURE: 3D named vectors for multi-dimensional intelligence (CURRENT SYSTEM)
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
                    
                    # Semantic concept vector for concept/personality context
                    "semantic": VectorParams(
                        size=self.embedding_dimension,
                        distance=Distance.COSINE,
                        hnsw_config=models.HnswConfigDiff(
                            m=16,
                            ef_construct=128
                        )
                    )
                }                # 🚀 QDRANT FEATURE: Optimized configuration for performance
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
                logger.info(f"Found existing collection: {self.collection_name}")
                
                # 🚀 CRITICAL: Validate and upgrade existing collection
                self._validate_and_upgrade_collection()
                
        except Exception as e:
            logger.debug(f"Collection creation/connection issue: {e}")
            raise  # Don't fallback - we need named vectors to work properly

    def _validate_and_upgrade_collection(self):
        """
        🎯 CRITICAL: Validate existing collection has all required vectors and indexes
        
        This ensures that collections have the current 3-vector schema (content, emotion, semantic).
        """
        try:
            # Get current collection configuration
            collection_info = self.client.get_collection(self.collection_name)
            current_vectors = collection_info.config.params.vectors
            
            # Expected 3 named vectors (current system)
            expected_vectors = {
                "content", "emotion", "semantic"
            }
            
            if isinstance(current_vectors, dict):
                current_vector_names = set(current_vectors.keys())
                missing_vectors = expected_vectors - current_vector_names
                extra_vectors = current_vector_names - expected_vectors
                
                if missing_vectors:
                    logger.warning(f"🚨 COLLECTION SCHEMA: Missing vectors {missing_vectors}")
                    logger.warning(f"🚨 Current vectors: {current_vector_names}")
                    logger.warning(f"🚨 This collection needs to be recreated with 3-vector schema")
                    
                    # For now, log the issue but don't auto-recreate to avoid data loss
                    logger.error(f"❌ CRITICAL: Collection '{self.collection_name}' has incomplete vector schema!")
                    logger.error(f"❌ Please recreate collection or run migration script")
                elif extra_vectors:
                    logger.info(f"📊 Collection has legacy vectors {extra_vectors} - will use current 3-vector subset")
                    logger.info(f"✅ Collection has required 3 vectors: {expected_vectors}")
                else:
                    logger.info(f"✅ Collection has correct 3-vector schema: {current_vector_names}")
            else:
                logger.warning(f"🚨 LEGACY COLLECTION: Single vector detected, needs 3-vector upgrade")
                logger.error(f"❌ CRITICAL: Collection '{self.collection_name}' uses legacy single-vector schema!")
            
            # Always ensure payload indexes exist (safe to call multiple times)
            self._create_payload_indexes()
            
        except Exception as e:
            logger.error(f"Failed to validate collection: {e}")
            # Don't raise - let the system continue but log the issue
    
    def _create_payload_indexes(self):
        """
        🎯 QDRANT FEATURE: Create optimized payload indexes for fast filtering
        
        This method is safe to call multiple times - Qdrant will ignore
        duplicate index creation attempts.
        """
        required_indexes = [
            ("user_id", models.PayloadSchemaType.KEYWORD, "User-based filtering (most common)"),
            ("memory_type", models.PayloadSchemaType.KEYWORD, "Memory type filtering"),
            ("timestamp_unix", models.PayloadSchemaType.FLOAT, "Temporal range queries and ordering"),
            ("semantic_key", models.PayloadSchemaType.KEYWORD, "Semantic grouping"),
            ("emotional_context", models.PayloadSchemaType.KEYWORD, "Emotional context"),
            ("content_hash", models.PayloadSchemaType.INTEGER, "Content hash (deduplication)"),
            # 🎯 REMOVED: bot_name index - collection isolation makes this redundant
        ]
        
        created_count = 0
        for field_name, field_type, description in required_indexes:
            try:
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name=field_name,
                    field_schema=field_type
                )
                logger.debug(f"✅ Created index: {field_name} ({description})")
                created_count += 1
            except Exception as e:
                # Index probably already exists - this is normal
                logger.debug(f"⚠️ Index {field_name} already exists or failed: {e}")
        
        if created_count > 0:
            logger.info(f"🎯 QDRANT-INDEXES: Created {created_count} payload indexes")
        else:
            logger.info(f"🎯 QDRANT-INDEXES: All payload indexes already exist")
    
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
        - Intelligent chunking for long messages (QUICK FIX)
        - Sparse vectors for keyword features
        - Automatic deduplication via content hashing
        - Contradiction detection preparation via semantic grouping
        """
        # DEBUG: Log entry to this method for memory storage tracking
        logger.debug(f"🔥 STORE_MEMORY CALLED: user_id={memory.user_id}, content={memory.content[:50]}...")
        
        # 🔄 QUICK FIX: Check if content should be chunked for better vector quality
        if self._should_chunk_content(memory.content):
            return await self._store_memory_with_chunking(memory)
        
        # Original storage logic for short/simple content
        return await self._store_memory_original(memory)

    async def _store_memory_with_chunking(self, memory: VectorMemory) -> str:
        """Store long content as multiple optimized chunks"""
        try:
            chunks = self._create_content_chunks(memory.content)
            stored_ids = []
            
            logger.info(f"🔄 CHUNKING: Processing {len(chunks)} chunks for user {memory.user_id}")
            
            for i, chunk_content in enumerate(chunks):
                # Generate proper UUID for chunk to avoid Qdrant point ID format errors
                import uuid
                chunk_id = str(uuid.uuid4())
                
                # Create chunk memory with enhanced metadata
                chunk_memory = VectorMemory(
                    id=chunk_id,
                    user_id=memory.user_id,
                    memory_type=memory.memory_type,
                    content=chunk_content,
                    source=f"{memory.source}_chunked",
                    confidence=memory.confidence,
                    timestamp=memory.timestamp,
                    memory_tier=memory.memory_tier,
                    tier_promotion_date=memory.tier_promotion_date,
                    tier_demotion_date=memory.tier_demotion_date,
                    decay_protection=memory.decay_protection,
                    metadata={
                        **memory.metadata,
                        "original_message_id": memory.id,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "is_chunked": True,
                        "original_length": len(memory.content),
                        "chunk_length": len(chunk_content)
                    }
                )
                
                chunk_id = await self._store_memory_original(chunk_memory)
                stored_ids.append(chunk_id)
            
            logger.info(f"✅ CHUNKING: Stored {len(stored_ids)} chunks for memory {memory.id}")
            return stored_ids[0]  # Return first chunk ID as primary reference
            
        except Exception as e:
            logger.error(f"❌ CHUNKING: Failed to store chunked memory: {e}")
            # Fallback to original storage
            return await self._store_memory_original(memory)

    async def _store_memory_original(self, memory: VectorMemory) -> str:
        """Original memory storage logic (renamed for chunking integration)"""
        
        try:
            import time
            embedding_start = time.perf_counter()
            
            # 🎭 PHASE 1.2: Extract emotional context BEFORE embeddings (needed for emotion embedding)
            emotional_context, emotional_intensity = await self._extract_emotional_context(
                memory.content, 
                memory.user_id,
                memory_metadata=memory.metadata  # 🎯 Pass metadata to check for pre-analyzed emotion
            )
            logger.info(f"🎭 DEBUG: Storing memory with emotion '{emotional_context}' (intensity: {emotional_intensity:.3f}) for user {memory.user_id}")
            logger.info(f"🎭 DEBUG: Content being stored: '{memory.content[:100]}...'")
            
            # 🎭 PHASE 1.2: Track emotional trajectory for conversation memories
            trajectory_data = {}
            if memory.memory_type == MemoryType.CONVERSATION:
                trajectory_data = await self.track_emotional_trajectory(memory.user_id, emotional_context)
                logger.debug(f"🎭 TRAJECTORY: Generated trajectory data for {memory.user_id}: {trajectory_data.get('trajectory_direction', 'unknown')}")
            
            # Get semantic key for concept clustering
            semantic_key = self._get_semantic_key(memory.content)
            
            # 🎯 NEW: Analyze 7D dimensions BEFORE embeddings (needed for dimension embeddings)
            dimension_analysis = None
            dimension_contexts = {}
            
            if self._vector_7d_analyzer:
                try:
                    dimension_analysis = await self._vector_7d_analyzer.analyze_all_dimensions(
                        content=memory.content,
                        user_id=memory.user_id,
                        character_name=get_normalized_bot_name_from_env(),
                        conversation_history=None  # TODO: Add conversation history support
                    )
                    
                    # Store dimension contexts for payload
                    dimension_contexts = {
                        'relationship_context': dimension_analysis['relationship_key'],
                        'personality_context': dimension_analysis['personality_key'],
                        'interaction_context': dimension_analysis['interaction_key'],
                        'temporal_context': dimension_analysis['temporal_key']
                    }
                    
                    logger.debug(f"🎯 3D CONTEXTS: {dimension_contexts}")
                    
                except Exception as e:
                    logger.warning(f"🎯 3D VECTORS: Failed to analyze dimensions, falling back to basic: {e}")
            
            # 🚀 CONCURRENCY OPTIMIZATION: Generate ALL embeddings in parallel!
            # This achieves ~7x speedup: 210ms sequential → 30ms parallel
            logger.info(f"🚀 PARALLEL EMBEDDINGS: Starting parallel generation of {'3'} embeddings")
            
            # 🎭 FIDELITY-FIRST: Create mixed emotion embedding text preserving RoBERTa multi-emotion data
            emotion_embedding_text = self._create_mixed_emotion_embedding_text(emotional_context, memory.content)
            logger.info(f"🎭 MIXED EMOTION: Generated fidelity-preserving emotion embedding text: '{emotion_embedding_text[:100]}...'")
            
            embedding_tasks = [
                # Core embeddings (always generated)
                asyncio.create_task(self.generate_embedding(memory.content)),  # content
                asyncio.create_task(self.generate_embedding(emotion_embedding_text)),  # emotion - ENHANCED for mixed emotions
                asyncio.create_task(self.generate_embedding(f"concept {semantic_key}: {memory.content}"))  # semantic
            ]
            
            # 7D dimension embeddings (if analyzer available)
            if dimension_analysis:
                embedding_tasks.extend([
                    asyncio.create_task(self.generate_embedding(f"{dimension_analysis['relationship_key']}: {memory.content}")),  # relationship
                    asyncio.create_task(self.generate_embedding(f"{dimension_analysis['personality_key']}: {memory.content}")),  # personality
                    asyncio.create_task(self.generate_embedding(f"{dimension_analysis['interaction_key']}: {memory.content}")),  # interaction
                    asyncio.create_task(self.generate_embedding(f"{dimension_analysis['temporal_key']}: {memory.content}"))  # temporal
                ])
            
            # Execute all embeddings concurrently
            embeddings = await asyncio.gather(*embedding_tasks, return_exceptions=True)
            
            # Extract results with error handling
            content_embedding = embeddings[0] if not isinstance(embeddings[0], Exception) else None
            emotion_embedding = embeddings[1] if not isinstance(embeddings[1], Exception) else None
            semantic_embedding = embeddings[2] if not isinstance(embeddings[2], Exception) else None
            
            relationship_embedding = None
            personality_embedding = None
            interaction_embedding = None
            temporal_embedding = None
            
            if dimension_analysis and len(embeddings) == 7:
                relationship_embedding = embeddings[3] if not isinstance(embeddings[3], Exception) else None
                personality_embedding = embeddings[4] if not isinstance(embeddings[4], Exception) else None
                interaction_embedding = embeddings[5] if not isinstance(embeddings[5], Exception) else None
                temporal_embedding = embeddings[6] if not isinstance(embeddings[6], Exception) else None
                
                logger.info(f"🎯 3D VECTORS: Generated enhanced dimensional embeddings for memory {memory.id}")
            
            embedding_time = (time.perf_counter() - embedding_start) * 1000
            logger.info(f"🚀 PARALLEL EMBEDDINGS: Generated {len(embeddings)} embeddings in {embedding_time:.1f}ms (parallel)")
            
            logger.debug(f"Generated content embedding: {type(content_embedding)}, length: {len(content_embedding) if content_embedding and not isinstance(content_embedding, Exception) else None}")
            logger.debug(f"Generated emotion embedding: {type(emotion_embedding)}, length: {len(emotion_embedding) if emotion_embedding and not isinstance(emotion_embedding, Exception) else None}")
            logger.debug(f"Generated semantic embedding: {type(semantic_embedding)}, length: {len(semantic_embedding) if semantic_embedding and not isinstance(semantic_embedding, Exception) else None}")
            
            # Validate core embeddings (content, emotion, semantic are required)
            if not content_embedding or not emotion_embedding or not semantic_embedding:
                raise ValueError(f"Invalid core embeddings generated: content={bool(content_embedding)}, emotion={bool(emotion_embedding)}, semantic={bool(semantic_embedding)}")
            
            # 🚀 QDRANT FEATURE: Create keyword metadata for filtering
            keywords = self._extract_keywords(memory.content)
            
            # 🎯 QDRANT OPTIMIZATION: Content hash for exact deduplication
            content_normalized = memory.content.lower().strip()
            content_hash = hash(content_normalized)
            
            # 🚀 QDRANT FEATURE: Check for exact duplicates using optimized index
            # 🎯 COLLECTION ISOLATION: No bot_name filter needed - each collection is bot-specific
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
            
            # 🎭 PHASE 1.2: Emotional trajectory tracking
            trajectory_data = await self.track_emotional_trajectory(memory.user_id, emotional_context)
            
            # 🎯 PHASE 1.3: Memory significance scoring
            significance_data = await self.calculate_memory_significance(memory, memory.user_id)
            
            # Enhanced payload optimized for Qdrant operations
            qdrant_payload = {
                "user_id": memory.user_id,
                # 🎯 REMOVED: bot_name field - collection isolation makes this redundant
                "memory_type": memory.memory_type.value,
                "content": memory.content,
                "timestamp": memory.timestamp.isoformat(),
                "timestamp_unix": memory.timestamp.timestamp(),
                "confidence": memory.confidence,
                "source": memory.source,
                
                # 🎯 PHASE 2.1: Three-tier memory architecture
                "memory_tier": memory.memory_tier.value,
                "tier_promotion_date": memory.tier_promotion_date.isoformat() if memory.tier_promotion_date else None,
                "tier_demotion_date": memory.tier_demotion_date.isoformat() if memory.tier_demotion_date else None,
                "decay_protection": memory.decay_protection,
                "tier_age_days": memory.get_tier_age_days(),
                
                # 🎯 QDRANT INTELLIGENCE FEATURES
                "content_hash": content_hash,
                "emotional_context": emotional_context,
                "emotional_intensity": emotional_intensity,  # 🎭 PHASE 1.1: Add intensity
                "semantic_key": semantic_key,
                "keywords": keywords,
                "word_count": len(memory.content.split()),
                "char_count": len(memory.content),
                
                # 🎭 ENHANCED: Multi-emotion RoBERTa storage
                **self._get_multi_emotion_payload(),
                
                # 🎭 PHASE 1.2: Emotional trajectory tracking
                **trajectory_data,
                
                # 🎯 PHASE 1.3: Memory significance scoring
                **significance_data,
                
                # 🎯 NEW: 3D Vector contexts
                **dimension_contexts,
                
                # Handle metadata safely
                **(memory.metadata if memory.metadata else {})
            }
            
            # 🧠 AUDIT: Check if metadata contains emotion_data and add to payload
            if memory.metadata and 'emotion_data' in memory.metadata:
                emotion_data = memory.metadata['emotion_data']
                logger.info(f"🧠 EMOTION AUDIT: Found emotion_data in metadata: {list(emotion_data.keys()) if emotion_data else 'null'}")
                if emotion_data:
                    qdrant_payload.update({
                        'pre_analyzed_primary_emotion': emotion_data.get('primary_emotion'),
                        'pre_analyzed_mixed_emotions': emotion_data.get('mixed_emotions'),
                        'pre_analyzed_emotion_description': emotion_data.get('emotion_description'),
                        'pre_analyzed_context_provided': emotion_data.get('context_provided', False)
                    })
                    logger.info(f"🧠 EMOTION AUDIT: Added pre-analyzed fields to payload")
            else:
                logger.info(f"🧠 EMOTION AUDIT: No emotion_data found in memory metadata")
            
            logger.info(f"🎭 DEBUG: Payload emotional_context set to: '{qdrant_payload['emotional_context']}' for memory {memory.id}")
            logger.info(f"🎭 DEBUG: Full payload keys: {list(qdrant_payload.keys())}")            # 🚀 QDRANT FEATURE: Named vectors for intelligent multi-dimensional search
            vectors = {}
            
            # Only add vectors that are valid (non-None, non-empty)
            if content_embedding and len(content_embedding) > 0:
                vectors["content"] = content_embedding
                logger.debug("UPSERT DEBUG: Content vector added: len=%d", len(content_embedding))
            else:
                logger.error("UPSERT ERROR: Invalid content embedding: %s", content_embedding)
                
            # 🎭 EMOTION VECTOR: Enable emotion-aware search
            if emotion_embedding and len(emotion_embedding) > 0:
                vectors["emotion"] = emotion_embedding
                logger.debug("UPSERT DEBUG: Emotion vector added: len=%d", len(emotion_embedding))
            else:
                logger.debug("UPSERT DEBUG: No emotion embedding generated")
                
            # 🧠 SEMANTIC VECTOR: Enable contradiction detection and concept clustering  
            if semantic_embedding and len(semantic_embedding) > 0:
                vectors["semantic"] = semantic_embedding
                logger.debug("UPSERT DEBUG: Semantic vector added: len=%d", len(semantic_embedding))
            else:
                logger.debug("UPSERT DEBUG: No semantic embedding generated")
            
            # 🎯 NEW: RELATIONSHIP VECTOR: Enable bond-appropriate responses
            if relationship_embedding and len(relationship_embedding) > 0:
                vectors["relationship"] = relationship_embedding
                logger.debug("UPSERT DEBUG: Relationship vector added: len=%d", len(relationship_embedding))
            else:
                logger.debug("UPSERT DEBUG: No relationship embedding generated")
            
            # 🎯 NEW: PERSONALITY VECTOR: Enable character consistency
            if personality_embedding and len(personality_embedding) > 0:
                vectors["personality"] = personality_embedding
                logger.debug("UPSERT DEBUG: Personality vector added: len=%d", len(personality_embedding))
            else:
                logger.debug("UPSERT DEBUG: No personality embedding generated")
                
            # 🎯 NEW: INTERACTION VECTOR: Enable communication style patterns
            if interaction_embedding and len(interaction_embedding) > 0:
                vectors["interaction"] = interaction_embedding
                logger.debug("UPSERT DEBUG: Interaction vector added: len=%d", len(interaction_embedding))
            else:
                logger.debug("UPSERT DEBUG: No interaction embedding generated")
                
            # 🎯 NEW: TEMPORAL VECTOR: Enable conversation flow intelligence
            if temporal_embedding and len(temporal_embedding) > 0:
                vectors["temporal"] = temporal_embedding
                logger.debug("UPSERT DEBUG: Temporal vector added: len=%d", len(temporal_embedding))
            else:
                logger.debug("UPSERT DEBUG: No temporal embedding generated")
            
            # Ensure we have at least one valid vector
            if not vectors:
                raise ValueError("No valid embeddings generated - cannot create point")
            
            # Store with all Qdrant advanced features
            point = PointStruct(
                id=memory.id,
                vector=vectors,  # Named vectors as dict
                payload=qdrant_payload
            )
            
            logger.debug("UPSERT DEBUG: Point ID: %s, Vector keys: %s", point.id, list(vectors.keys()))
            
            # 🎯 QDRANT FEATURE: Atomic operation with immediate consistency
            logger.debug("UPSERT DEBUG: About to call Qdrant upsert with collection: %s", self.collection_name)
            logger.debug("UPSERT DEBUG: Point structure - ID: %s, Vector type: %s", point.id, type(point.vector).__name__)
            
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

    def _should_chunk_content(self, content: str) -> bool:
        """Determine if content should be chunked for better vector quality
        
        DISABLED: Chunking hurts conversation fidelity and context continuity.
        Modern embedding models (384D) can handle longer content without quality loss.
        Keeping full conversations intact preserves emotional context and narrative flow.
        """
        # Always return False to preserve conversation fidelity
        return False
        
        # Original chunking criteria (DISABLED for better conversation continuity):
        # return (
        #     len(content) > 300 or  # Long messages
        #     content.count('.') > 2 or  # Multiple sentences
        #     content.count('!') > 1 or  # Multiple exclamations
        #     content.count('?') > 1     # Multiple questions
        # )

    def _create_content_chunks(self, content: str) -> List[str]:
        """Split content into semantic chunks for better vector quality"""
        import re
        
        # Split into sentences using multiple delimiters
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
        
        if len(sentences) <= 1:
            return [content]  # Can't chunk meaningfully
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            # Add sentence if it fits in current chunk
            if current_length + len(sentence) <= 250 and len(current_chunk) < 3:
                current_chunk.append(sentence)
                current_length += len(sentence)
            else:
                # Save current chunk and start new one
                if current_chunk:
                    chunks.append('. '.join(current_chunk) + '.')
                current_chunk = [sentence]
                current_length = len(sentence)
        
        # Add final chunk
        if current_chunk:
            chunks.append('. '.join(current_chunk) + '.')
        
        # If chunking didn't help much, return original
        if len(chunks) == 1:
            return [content]
        
        logger.debug(f"🔄 CHUNKING: Split {len(content)} chars into {len(chunks)} chunks")
        return chunks
    
    async def _extract_emotional_context(self, content: str, user_id: str = "unknown", memory_metadata: Optional[Dict] = None) -> tuple[str, float]:
        """Extract emotional context using Enhanced Vector Emotion Analyzer for superior accuracy
        
        Args:
            content: Message content to analyze
            user_id: User identifier
            memory_metadata: Optional metadata that may contain pre-analyzed emotion data
            
        Returns:
            Tuple of (emotion_name, intensity_score)
        """
        try:
            logger.debug(f"🎭 DEBUG: Extracting emotion from content: '{content[:100]}...' for user {user_id}")
            
            # 🎯 PRIORITY 1: Use pre-analyzed emotion data if available (MOST ACCURATE)
            # This prevents emotion data pollution and preserves accurate emotion analysis from Phase 2
            if memory_metadata and 'emotion_data' in memory_metadata:
                emotion_data = memory_metadata['emotion_data']
                if emotion_data and isinstance(emotion_data, dict):
                    # Check for primary_emotion in the emotion_data
                    primary_emotion = emotion_data.get('primary_emotion')
                    
                    # Also check in nested emotional_intelligence structure (Phase 2 format)
                    if not primary_emotion and 'emotional_intelligence' in emotion_data:
                        emotional_intelligence = emotion_data['emotional_intelligence']
                        if isinstance(emotional_intelligence, dict):
                            primary_emotion = emotional_intelligence.get('primary_emotion')
                    
                    if primary_emotion and isinstance(primary_emotion, str):
                        # Get intensity from multiple possible locations
                        intensity = emotion_data.get('intensity')
                        if intensity is None and 'emotion_analysis' in emotion_data:
                            intensity = emotion_data['emotion_analysis'].get('intensity')
                        if intensity is None:
                            intensity = 0.5  # Default if not provided
                        
                        intensity = float(intensity)
                        
                        logger.info(f"🎯 PRE-ANALYZED EMOTION: Using '{primary_emotion}' (intensity: {intensity:.3f}) from metadata for user {user_id}")
                        logger.debug(f"🎯 Skipping re-analysis - pre-analyzed emotion data available and valid")
                        
                        # Store for multi-emotion tracking
                        self._last_emotion_analysis = {
                            "primary_emotion": primary_emotion,
                            "primary_intensity": intensity,
                            "all_emotions": emotion_data.get('all_emotions', {}),
                            "confidence": emotion_data.get('confidence', 1.0),
                            "is_multi_emotion": len(emotion_data.get('mixed_emotions', [])) > 0
                        }
                        
                        return primary_emotion, intensity
                    else:
                        logger.debug(f"🎯 Pre-analyzed emotion data exists but primary_emotion is invalid: {primary_emotion}")
                else:
                    logger.debug(f"🎯 emotion_data in metadata is not a valid dict: {type(emotion_data)}")
            else:
                logger.debug(f"🎭 DEBUG: No pre-analyzed emotion data in metadata, will analyze content")
            
            # 🎯 PRIORITY 2: Try to use Enhanced Vector Emotion Analyzer (much better than keywords)
            if self._enhanced_emotion_analyzer:
                try:
                    logger.debug(f"🎭 DEBUG: Using Enhanced Vector Emotion Analyzer")
                    analysis_result = await self._enhanced_emotion_analyzer.analyze_emotion(
                        content=content,
                        user_id=user_id
                    )
                    
                    # Store multi-emotion data for future use
                    self._last_emotion_analysis = {
                        "primary_emotion": analysis_result.primary_emotion,
                        "primary_intensity": analysis_result.intensity,
                        "all_emotions": analysis_result.all_emotions,
                        "confidence": analysis_result.confidence,
                        "is_multi_emotion": len(analysis_result.all_emotions) > 1
                    }
                    
                    logger.info(f"🎭 DEBUG: Enhanced analyzer result: {analysis_result.primary_emotion} "
                               f"(intensity: {analysis_result.intensity:.3f}, confidence: {analysis_result.confidence:.3f})")
                    
                    # Return primary emotion and intensity (backward compatibility)
                    return analysis_result.primary_emotion, analysis_result.intensity
                    
                except Exception as e:
                    logger.warning(f"🎭 DEBUG: Enhanced emotion analyzer failed, falling back to keywords: {e}")
                    self._last_emotion_analysis = None
            else:
                logger.debug(f"🎭 DEBUG: Enhanced Vector Emotion Analyzer not available, using keyword analysis")
            
            # Fallback to keyword analysis if Enhanced Vector Emotion Analyzer unavailable
            content_lower = content.lower()
            
            # Use comprehensive emotion keywords (same as Enhanced Vector Emotion Analyzer)
            emotion_patterns = {
                "joy": ["happy", "joy", "delighted", "pleased", "cheerful", "elated", "ecstatic", 
                       "thrilled", "excited", "wonderful", "amazing", "fantastic", "great", "awesome", 
                       "brilliant", "perfect", "love", "adore", "celebration", "bliss", "euphoric",
                       "overjoyed", "gleeful", "jubilant", "radiant", "beaming", "yay"],
                "sadness": ["sad", "unhappy", "depressed", "melancholy", "sorrowful", "grief", 
                           "disappointed", "heartbroken", "down", "blue", "gloomy", "miserable", "crying",
                           "tragedy", "loss", "tears", "devastated", "crushed", "despair", "desolate",
                           "mournful", "dejected", "forlorn", "disheartened", "crestfallen", "woeful"],
                "anger": ["angry", "mad", "furious", "rage", "irritated", "annoyed", "frustrated", 
                         "outraged", "livid", "incensed", "hostile", "aggressive", "hate", "disgusted",
                         "appalled", "infuriated", "upset", "bothered", "irate", "enraged", "seething",
                         "wrathful", "indignant", "resentful", "bitter", "raging"],
                "fear": ["afraid", "scared", "frightened", "terrified", "worried", "anxious", 
                        "nervous", "panic", "dread", "horror", "alarmed", "startled", "intimidated",
                        "threatened", "concerned", "uneasy", "apprehensive", "petrified", "horrified",
                        "panicked", "fearful", "timid", "trembling", "shaking"],
                "excitement": ["excited", "thrilled", "energetic", "enthusiastic", "pumped", 
                              "eager", "anticipation", "can't wait", "hyped", "electrified", "exhilarated",
                              "animated", "spirited", "vivacious", "dynamic", "charged"],
                "gratitude": ["grateful", "thankful", "appreciate", "blessed", "fortunate", 
                             "thank you", "thanks", "indebted", "obliged", "recognition", "appreciative",
                             "beholden", "grateful for", "much appreciated"],
                "curiosity": ["curious", "wondering", "interested", "intrigued", "questioning", 
                             "exploring", "learning", "discovery", "fascinated", "inquisitive", "puzzled",
                             "perplexed", "bewildered", "inquiring", "investigative"],
                "surprise": ["surprised", "shocked", "amazed", "astonished", "bewildered", 
                            "stunned", "confused", "puzzled", "unexpected", "wow", "incredible", 
                            "unbelievable", "startling", "remarkable", "astounded", "flabbergasted",
                            "dumbfounded", "taken aback"],
                "anxiety": ["anxious", "stressed", "overwhelmed", "pressure", "tension",
                           "worried", "nervous", "uneasy", "restless", "troubled", "distressed",
                           "frazzled", "agitated", "jittery", "on edge", "wound up"],
                "contentment": ["content", "satisfied", "peaceful", "calm", "serene", "relaxed",
                               "comfortable", "at ease", "tranquil", "balanced", "fulfilled", "placid",
                               "composed", "untroubled", "at peace", "mellow"],
                "disgust": ["disgusted", "gross", "eww", "revolting", "nauseating", "repulsive",
                           "sickening", "appalling", "repugnant", "loathsome", "abhorrent"],
                "shame": ["ashamed", "embarrassed", "humiliated", "mortified", "shameful", "guilty",
                         "regretful", "remorseful", "sheepish", "chagrined", "red-faced"],
                "pride": ["proud", "accomplished", "achievement", "triumphant", "victorious", "successful",
                         "accomplished", "pleased with", "satisfied with", "boastful"],
                "loneliness": ["lonely", "isolated", "alone", "solitary", "abandoned", "forsaken",
                              "desolate", "friendless", "cut off", "estranged"]
            }
            
            # Score each emotion based on keyword matches
            emotion_scores = {}
            for emotion, keywords in emotion_patterns.items():
                matches = sum(1 for keyword in keywords if keyword in content_lower)
                if matches > 0:
                    emotion_scores[emotion] = matches
            
            # Return the highest scoring emotion
            if emotion_scores:
                best_emotion = max(emotion_scores.items(), key=lambda x: x[1])
                intensity = min(best_emotion[1] * 0.3, 1.0)  # Scale intensity
                logger.info(f"🎭 DEBUG: Keyword analysis result: {best_emotion[0]} "
                           f"(matches: {best_emotion[1]}, intensity: {intensity:.3f})")
                return best_emotion[0], intensity
            else:
                logger.info(f"🎭 DEBUG: Keyword analysis found no emotional keywords, defaulting to neutral")
                return 'neutral', 0.1
                
        except Exception as e:
            logger.error("Error in emotional context extraction: %s", e)
            return 'neutral', 0.1
    
    # Phase 1.2: Emotional Trajectory Tracking
    async def track_emotional_trajectory(self, user_id: str, current_emotion: str) -> Dict[str, Any]:
        """
        🎭 PHASE 1.2: Track emotional momentum and velocity over time
        
        Features:
        - Emotional momentum calculation (direction of change)
        - Emotional velocity (rate of change)
        - Stability analysis (consistency over time)
        - Pattern detection for emotional cycles
        """
        try:
            # Get recent emotional states from last 10 conversation memories
            recent_emotions = await self.get_recent_emotional_states(user_id, limit=10)
            
            if len(recent_emotions) < 1:
                # No recent emotional data at all
                logger.info(f"🎭 TRAJECTORY INFO: User {user_id} has no recent emotions in last 7 days. "
                           f"Returning stable default values.")
                return {
                    "emotional_trajectory": [current_emotion],
                    "emotional_velocity": 0.0,
                    "emotional_stability": 1.0,
                    "trajectory_direction": "stable",
                    "emotional_momentum": "neutral",
                    "pattern_detected": None
                }
            elif len(recent_emotions) == 1:
                # Only one recent emotion - compare with current
                single_emotion = recent_emotions[0]
                logger.info(f"🎭 TRAJECTORY INFO: User {user_id} has only 1 recent emotion: '{single_emotion}'. "
                           f"Current emotion: '{current_emotion}'. Computing limited trajectory.")
                
                # Simple comparison between single past emotion and current
                if single_emotion == current_emotion:
                    direction = "stable"
                    velocity = 0.0
                    momentum = "neutral"
                    stability = 1.0
                else:
                    direction = "changing"
                    velocity = 0.3  # Moderate change
                    momentum = "shifting"
                    stability = 0.7  # Less stable due to change
                
                return {
                    "emotional_trajectory": [single_emotion, current_emotion],
                    "emotional_velocity": velocity,
                    "emotional_stability": stability,
                    "trajectory_direction": direction,
                    "emotional_momentum": momentum,
                    "pattern_detected": None
                }
            
            # Calculate emotional momentum and velocity
            logger.info(f"🎭 TRAJECTORY INFO: User {user_id} has {len(recent_emotions)} recent emotions. "
                       f"Performing full trajectory analysis. Emotions: {recent_emotions[:5]}...")
            emotional_velocity = self.calculate_emotional_momentum(recent_emotions)
            emotional_stability = self.calculate_emotional_stability(recent_emotions)
            trajectory_direction = self.determine_trajectory_direction(recent_emotions)
            emotional_momentum = self.analyze_emotional_momentum(recent_emotions)
            pattern_detected = self.detect_emotional_patterns(recent_emotions)
            
            emotional_metadata = {
                "emotional_trajectory": recent_emotions,
                "emotional_velocity": emotional_velocity,
                "emotional_stability": emotional_stability,
                "trajectory_direction": trajectory_direction,
                "emotional_momentum": emotional_momentum,
                "pattern_detected": pattern_detected,
                "trajectory_analysis_timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"🎭 EMOTIONAL TRAJECTORY: User {user_id} - "
                       f"velocity={emotional_velocity:.2f}, stability={emotional_stability:.2f}, "
                       f"direction={trajectory_direction}, momentum={emotional_momentum}")
            
            return emotional_metadata
            
        except Exception as e:
            logger.error(f"Error tracking emotional trajectory for {user_id}: {e}")
            return {"emotional_trajectory": [current_emotion], "error": str(e)}
    
    async def get_recent_emotional_states(self, user_id: str, limit: int = 10) -> List[str]:
        """Get recent emotional states from conversation memories"""
        try:
            # Use Qdrant to get recent conversation memories with emotional context
            # 🔧 FIX: Extended time window from 24 hours to 7 days for better trajectory analysis
            recent_cutoff = datetime.utcnow() - timedelta(days=7)  # Last 7 days instead of 24 hours
            recent_timestamp = recent_cutoff.timestamp()
            
            logger.info(f"🔍 DEBUG: Getting recent emotional states for user {user_id}")
            logger.info(f"🔍 DEBUG: Time window: {recent_cutoff.isoformat()} to now ({recent_timestamp})")
            logger.info(f"🔍 DEBUG: Collection: {self.collection_name}")
            
            # Show what bot name is being used for filtering
            # 🎯 COLLECTION ISOLATION: No bot_name filter needed - each collection is bot-specific
            logger.info(f"🔍 DEBUG: Collection-based filtering (no bot_name needed): '{self.collection_name}'")
            
            scroll_result = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id)),
                        # 🎯 REMOVED: bot_name filter - collection isolation makes this redundant
                        models.FieldCondition(key="memory_type", match=models.MatchValue(value="conversation")),
                        models.FieldCondition(key="timestamp_unix", range=Range(gte=recent_timestamp))
                    ]
                ),
                limit=limit,
                with_payload=True,
                with_vectors=False,
                order_by=models.OrderBy(key="timestamp_unix", direction=Direction.DESC)
            )
            
            logger.info(f"🔍 DEBUG: Qdrant query conditions:")
            logger.info(f"  - user_id: {user_id}")
            logger.info(f"  - collection: {self.collection_name} (bot-specific)")
            logger.info(f"  - memory_type: conversation")
            logger.info(f"  - timestamp_unix >= {recent_timestamp}")
            logger.info(f"🔍 DEBUG: Found {len(scroll_result[0])} conversation memories")
            
            emotions = []
            for i, point in enumerate(scroll_result[0]):
                emotion = point.payload.get('emotional_context', 'neutral')
                content_preview = point.payload.get('content', 'NO CONTENT')[:50]
                timestamp = point.payload.get('timestamp', 'NO TIMESTAMP')
                role = point.payload.get('role', 'UNKNOWN')
                
                logger.info(f"🔍 DEBUG: Memory {i+1}: emotion='{emotion}', role='{role}', "
                           f"content='{content_preview}...', timestamp={timestamp}")
                emotions.append(emotion)
            
            final_emotions = emotions if emotions else ['neutral']
            logger.info(f"🔍 DEBUG: Final emotions list: {final_emotions}")
            return final_emotions
            
        except Exception as e:
            logger.error(f"Error getting recent emotional states: {e}")
            return ['neutral']
    
    def calculate_emotional_momentum(self, emotions: List[str]) -> float:
        """Calculate emotional momentum (rate of emotional change)"""
        logger.info(f"🎭 DEBUG: Calculating momentum for emotions: {emotions}")
        
        if len(emotions) < 2:
            logger.info(f"🎭 DEBUG: Less than 2 emotions, returning momentum = 0.0")
            return 0.0
        
        # Map emotions to numerical values for momentum calculation
        emotion_values = {
            'very_positive': 2.0,
            'positive': 1.0,
            'mildly_positive': 0.5,
            'neutral': 0.0,
            'mildly_negative': -0.5,
            'negative': -1.0,
            'very_negative': -2.0,
            'contemplative': 0.2,
            'anxious': -0.8
        }
        
        # Calculate velocity as change over time
        changes = []
        for i in range(1, len(emotions)):
            prev_val = emotion_values.get(emotions[i-1], 0.0)
            curr_val = emotion_values.get(emotions[i], 0.0)
            change = curr_val - prev_val
            changes.append(change)
        
        # Average change rate (momentum)
        return sum(changes) / len(changes) if changes else 0.0
    
    def calculate_emotional_stability(self, emotions: List[str]) -> float:
        """Calculate emotional stability (consistency over time)"""
        logger.info(f"🎭 DEBUG: Calculating stability for emotions: {emotions}")
        
        if len(emotions) < 2:
            logger.info(f"🎭 DEBUG: Less than 2 emotions, returning stability = 1.0")
            return 1.0
        
        # Map emotions to values and calculate variance
        emotion_values = {
            'very_positive': 2.0, 'positive': 1.0, 'mildly_positive': 0.5,
            'neutral': 0.0, 'mildly_negative': -0.5, 'negative': -1.0,
            'very_negative': -2.0, 'contemplative': 0.2, 'anxious': -0.8
        }
        
        values = [emotion_values.get(emotion, 0.0) for emotion in emotions]
        logger.info(f"🎭 DEBUG: Emotion values: {values}")
        
        # Calculate standard deviation as measure of stability
        mean_val = sum(values) / len(values)
        variance = sum((x - mean_val) ** 2 for x in values) / len(values)
        std_dev = variance ** 0.5
        
        # Convert to stability score (0-1, higher = more stable)
        max_possible_std = 2.0  # Max possible standard deviation
        stability = max(0.0, 1.0 - (std_dev / max_possible_std))
        
        return stability
    
    def determine_trajectory_direction(self, emotions: List[str]) -> str:
        """Determine overall direction of emotional trajectory"""
        if len(emotions) < 3:
            return "stable"
        
        emotion_values = {
            'very_positive': 2.0, 'positive': 1.0, 'mildly_positive': 0.5,
            'neutral': 0.0, 'mildly_negative': -0.5, 'negative': -1.0,
            'very_negative': -2.0, 'contemplative': 0.2, 'anxious': -0.8
        }
        
        recent_avg = sum(emotion_values.get(emotions[i], 0.0) for i in range(3)) / 3
        older_avg = sum(emotion_values.get(emotions[i], 0.0) for i in range(3, len(emotions))) / max(1, len(emotions) - 3)
        
        difference = recent_avg - older_avg
        
        if difference > 0.3:
            return "improving"
        elif difference < -0.3:
            return "declining"
        else:
            return "stable"
    
    def analyze_emotional_momentum(self, emotions: List[str]) -> str:
        """Analyze the type of emotional momentum"""
        velocity = self.calculate_emotional_momentum(emotions)
        
        if velocity > 0.5:
            return "positive_momentum"
        elif velocity < -0.5:
            return "negative_momentum"
        elif abs(velocity) < 0.1:
            return "neutral"
        else:
            return "mixed"
    
    def detect_emotional_patterns(self, emotions: List[str]) -> Optional[str]:
        """Detect emotional patterns in the trajectory"""
        if len(emotions) < 4:
            return None
        
        # Check for oscillating pattern (back and forth)
        positive_emotions = {'very_positive', 'positive', 'mildly_positive'}
        negative_emotions = {'very_negative', 'negative', 'mildly_negative'}
        
        changes = 0
        for i in range(1, len(emotions)):
            prev_positive = emotions[i-1] in positive_emotions
            curr_positive = emotions[i] in positive_emotions
            prev_negative = emotions[i-1] in negative_emotions
            curr_negative = emotions[i] in negative_emotions
            
            if (prev_positive and curr_negative) or (prev_negative and curr_positive):
                changes += 1
        
        if changes >= len(emotions) // 2:
            return "oscillating"
        
        # Check for consistent trend
        recent_emotions = emotions[:3]
        if all(e in positive_emotions for e in recent_emotions):
            return "consistently_positive"
        elif all(e in negative_emotions for e in recent_emotions):
            return "consistently_negative"
        elif all(e == 'contemplative' for e in recent_emotions):
            return "deep_thinking"
        elif all(e == 'anxious' for e in recent_emotions):
            return "escalating_anxiety"
        
        return None

    # Phase 1.3: Memory Significance Scoring
    async def calculate_memory_significance(self, memory: VectorMemory, user_id: str) -> Dict[str, Any]:
        """
        🎯 PHASE 1.3: Calculate comprehensive significance scoring for memories
        
        Features:
        - Multi-factor significance calculation
        - Emotional impact scoring
        - Personal relevance assessment  
        - Temporal importance weighting
        - Decay resistance for important memories
        """
        try:
            # Get user's recent memory context for comparison
            recent_memories = await self.get_recent_memories(user_id, limit=20)
            user_patterns = await self.get_user_emotional_patterns(user_id)
            
            # Calculate base significance factors
            significance_factors = {
                'emotional_intensity': self.calculate_emotional_significance(memory),
                'personal_relevance': self.calculate_personal_relevance(memory, recent_memories),
                'uniqueness_score': self.calculate_uniqueness_score(memory, recent_memories),
                'temporal_importance': self.calculate_temporal_importance(memory),
                'interaction_value': self.calculate_interaction_value(memory),
                'pattern_significance': self.calculate_pattern_significance(memory, user_patterns)
            }
            
            # Calculate weighted overall significance
            overall_significance = self.calculate_weighted_significance(significance_factors)
            
            # Determine decay resistance based on significance
            decay_resistance = self.calculate_decay_resistance(overall_significance, significance_factors)
            
            # Calculate significance tier for indexing
            significance_tier = self.determine_significance_tier(overall_significance)
            
            significance_data = {
                'overall_significance': overall_significance,
                'significance_factors': significance_factors,
                'decay_resistance': decay_resistance,
                'significance_tier': significance_tier,
                'calculated_at': datetime.utcnow().isoformat(),
                'significance_version': '1.3'
            }
            
            logger.debug(f"Memory significance calculated: {overall_significance:.3f} (tier: {significance_tier})")
            return significance_data
            
        except Exception as e:
            logger.error(f"Error calculating memory significance: {e}")
            # Return default values on error
            return {
                'overall_significance': 0.5,
                'significance_factors': {},
                'decay_resistance': 1.0,
                'significance_tier': 'standard',
                'calculated_at': datetime.utcnow().isoformat(),
                'significance_version': '1.3'
            }
    
    def calculate_emotional_significance(self, memory: VectorMemory) -> float:
        """Calculate significance based on emotional content"""
        metadata = memory.metadata or {}
        emotional_context = metadata.get('emotional_context', 'neutral')
        emotional_intensity = metadata.get('emotional_intensity', 0.5)
        
        # High-intensity emotions are more significant
        intensity_factor = emotional_intensity
        
        # Certain emotions have higher baseline significance
        emotion_weights = {
            'very_positive': 0.9,
            'very_negative': 0.9,
            'anxious': 0.8,
            'positive': 0.7,
            'negative': 0.7,
            'contemplative': 0.6,
            'mildly_positive': 0.5,
            'mildly_negative': 0.5,
            'neutral': 0.3
        }
        
        emotion_weight = emotion_weights.get(emotional_context, 0.3)
        return min(1.0, intensity_factor * emotion_weight)
    
    def calculate_personal_relevance(self, memory: VectorMemory, recent_memories: List[Dict]) -> float:
        """Calculate personal relevance based on user's conversation patterns"""
        if not recent_memories:
            return 0.5
        
        content_words = set(memory.content.lower().split())
        
        # Find common themes in recent memories
        theme_counts = {}
        for mem in recent_memories:
            words = set(mem.get('content', '').lower().split())
            common_words = content_words.intersection(words)
            for word in common_words:
                if len(word) > 3:  # Filter out short words
                    theme_counts[word] = theme_counts.get(word, 0) + 1
        
        # Calculate relevance based on theme overlap
        if not theme_counts:
            return 0.3
        
        max_overlap = max(theme_counts.values())
        relevance = min(1.0, max_overlap / 5.0)  # Normalize to 0-1
        return relevance
    
    def calculate_uniqueness_score(self, memory: VectorMemory, recent_memories: List[Dict]) -> float:
        """Calculate uniqueness compared to recent memories"""
        if not recent_memories:
            return 1.0
        
        content_words = set(memory.content.lower().split())
        
        # Calculate similarity with recent memories
        similarities = []
        for mem in recent_memories:
            mem_words = set(mem.get('content', '').lower().split())
            if content_words and mem_words:
                intersection = len(content_words.intersection(mem_words))
                union = len(content_words.union(mem_words))
                similarity = intersection / union if union > 0 else 0
                similarities.append(similarity)
        
        if not similarities:
            return 1.0
        
        # Higher uniqueness = lower average similarity
        avg_similarity = sum(similarities) / len(similarities)
        uniqueness = 1.0 - avg_similarity
        return max(0.1, uniqueness)  # Minimum uniqueness of 0.1
    
    def calculate_temporal_importance(self, memory: VectorMemory) -> float:
        """Calculate importance based on timing and recency"""
        if not memory.timestamp:
            return 0.5
        
        # More recent memories have higher temporal importance
        age_hours = (datetime.utcnow() - memory.timestamp).total_seconds() / 3600
        
        # Decay function: recent memories more important
        if age_hours < 1:
            return 1.0
        elif age_hours < 24:
            return 0.9
        elif age_hours < 168:  # 1 week
            return 0.7
        elif age_hours < 720:  # 1 month
            return 0.5
        else:
            return 0.3
    
    def calculate_interaction_value(self, memory: VectorMemory) -> float:
        """Calculate value based on interaction quality"""
        # Check for question marks (questions are often significant)
        has_question = '?' in memory.content
        
        # Check for personal pronouns (more personal engagement)
        personal_words = ['i', 'me', 'my', 'myself', 'you', 'your', 'we', 'us', 'our']
        content_words = memory.content.lower().split()
        personal_count = sum(1 for word in content_words if word in personal_words)
        
        # Check for simple/basic questions that shouldn't be highly significant
        simple_question_patterns = [
            'what time', 'what day', 'what date', 'how are you', 'hello', 'hi there',
            'good morning', 'good night', 'thanks', 'thank you', 'okay', 'ok', 'yes', 'no'
        ]
        
        content_lower = memory.content.lower()
        is_simple_question = any(pattern in content_lower for pattern in simple_question_patterns)
        
        # Check memory type significance with adjustments for simple queries
        base_type_weights = {
            MemoryType.CONVERSATION: 0.5,  # Reduced from 0.8
            MemoryType.FACT: 0.4,          # Reduced from 0.6
            MemoryType.PREFERENCE: 0.6     # Reduced from 0.7
        }
        
        type_score = base_type_weights.get(memory.memory_type, 0.3)
        
        # Questions get a boost, but simple questions get penalized
        if has_question:
            if is_simple_question:
                question_boost = -0.2  # Reduce significance for simple questions
            else:
                question_boost = 0.2   # Boost for meaningful questions
        else:
            question_boost = 0.0
        
        personal_score = min(0.2, personal_count * 0.05)  # Reduced impact
        
        final_score = type_score + question_boost + personal_score
        return max(0.1, min(1.0, final_score))  # Ensure minimum of 0.1
    
    def calculate_pattern_significance(self, memory: VectorMemory, user_patterns: Dict) -> float:
        """Calculate significance based on user's behavioral patterns"""
        if not user_patterns:
            return 0.5
        
        # Check if memory relates to user's emotional patterns
        metadata = memory.metadata or {}
        emotional_context = metadata.get('emotional_context', 'neutral')
        
        # High significance if memory represents emotional pattern change
        recent_pattern = user_patterns.get('recent_emotional_pattern')
        if recent_pattern and emotional_context != recent_pattern:
            return 0.9  # Pattern change is significant
        
        # Check for recurring themes
        frequent_themes = user_patterns.get('frequent_themes', [])
        content_lower = memory.content.lower()
        theme_matches = sum(1 for theme in frequent_themes if theme in content_lower)
        
        return min(1.0, 0.3 + (theme_matches * 0.2))
    
    def calculate_weighted_significance(self, factors: Dict[str, float]) -> float:
        """Calculate overall significance with weighted factors"""
        weights = {
            'emotional_intensity': 0.25,
            'personal_relevance': 0.20,
            'uniqueness_score': 0.15,
            'temporal_importance': 0.15,
            'interaction_value': 0.15,
            'pattern_significance': 0.10
        }
        
        weighted_sum = sum(factors.get(factor, 0) * weight for factor, weight in weights.items())
        return min(1.0, max(0.0, weighted_sum))
    
    def calculate_decay_resistance(self, overall_significance: float, factors: Dict[str, float]) -> float:
        """Calculate how resistant this memory should be to decay/deletion"""
        # High significance memories should be more resistant to decay
        base_resistance = overall_significance
        
        # Extra resistance for highly emotional or unique memories
        emotional_boost = factors.get('emotional_intensity', 0) * 0.2
        uniqueness_boost = factors.get('uniqueness_score', 0) * 0.15
        
        total_resistance = base_resistance + emotional_boost + uniqueness_boost
        return min(1.0, total_resistance)
    
    def determine_significance_tier(self, overall_significance: float) -> str:
        """Determine significance tier for indexing and retrieval optimization"""
        if overall_significance >= 0.8:
            return 'critical'
        elif overall_significance >= 0.6:
            return 'high'
        elif overall_significance >= 0.4:
            return 'standard'
        elif overall_significance >= 0.2:
            return 'low'
        else:
            return 'minimal'
    
    # Phase 2.1: Three-Tier Memory Architecture
    def determine_memory_tier_from_significance(self, significance_score: float, emotional_intensity: float = 0.0) -> MemoryTier:
        """Determine initial memory tier based on significance and emotional intensity"""
        # High significance or high emotional intensity → LONG_TERM
        if significance_score >= 0.75 or emotional_intensity >= 0.8:
            return MemoryTier.LONG_TERM
        
        # Medium significance or medium emotional intensity → MEDIUM_TERM  
        elif significance_score >= 0.45 or emotional_intensity >= 0.5:
            return MemoryTier.MEDIUM_TERM
        
        # Low significance → SHORT_TERM
        else:
            return MemoryTier.SHORT_TERM
    
    async def promote_memory_tier(self, memory_id: str, new_tier: MemoryTier, reason: str = "automatic") -> bool:
        """Promote a memory to a higher tier"""
        try:
            # Get current memory
            search_result = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[memory_id],
                with_payload=True
            )
            
            if not search_result:
                logger.warning(f"Memory {memory_id} not found for tier promotion")
                return False
            
            current_payload = search_result[0].payload
            current_tier = MemoryTier(current_payload.get('memory_tier', 'short_term'))
            
            # Only promote to higher tiers
            tier_hierarchy = [MemoryTier.SHORT_TERM, MemoryTier.MEDIUM_TERM, MemoryTier.LONG_TERM]
            if tier_hierarchy.index(new_tier) <= tier_hierarchy.index(current_tier):
                logger.debug(f"Cannot promote memory {memory_id} from {current_tier} to {new_tier}")
                return False
            
            # Update memory tier
            updated_payload = {
                **current_payload,
                "memory_tier": new_tier.value,
                "tier_promotion_date": datetime.utcnow().isoformat(),
                "tier_promotion_reason": reason,
                "decay_protection": new_tier == MemoryTier.LONG_TERM  # Protect long-term memories
            }
            
            # Use set_payload instead of update_payload
            self.client.set_payload(
                collection_name=self.collection_name,
                payload=updated_payload,
                points=[memory_id]
            )
            
            logger.info(f"🎯 TIER PROMOTION: Memory {memory_id} promoted from {current_tier.value} to {new_tier.value} ({reason})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to promote memory tier: {e}")
            return False
    
    async def demote_memory_tier(self, memory_id: str, new_tier: MemoryTier, reason: str = "automatic") -> bool:
        """Demote a memory to a lower tier"""
        try:
            # Get current memory
            search_result = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[memory_id],
                with_payload=True
            )
            
            if not search_result:
                logger.warning(f"Memory {memory_id} not found for tier demotion")
                return False
            
            current_payload = search_result[0].payload
            if not current_payload:
                logger.warning(f"Memory {memory_id} has no payload for tier demotion")
                return False
                
            current_tier = MemoryTier(current_payload.get('memory_tier', 'short_term'))
            
            # Don't demote protected memories
            if current_payload.get('decay_protection', False):
                logger.debug(f"Memory {memory_id} protected from demotion")
                return False
            
            # Only demote to lower tiers
            tier_hierarchy = [MemoryTier.SHORT_TERM, MemoryTier.MEDIUM_TERM, MemoryTier.LONG_TERM]
            if tier_hierarchy.index(new_tier) >= tier_hierarchy.index(current_tier):
                logger.debug(f"Cannot demote memory {memory_id} from {current_tier} to {new_tier}")
                return False
            
            # Update memory tier
            updated_payload = {
                **current_payload,
                "memory_tier": new_tier.value,
                "tier_demotion_date": datetime.utcnow().isoformat(),
                "tier_demotion_reason": reason
            }
            
            # Use set_payload instead of update_payload
            self.client.set_payload(
                collection_name=self.collection_name,
                payload=updated_payload,
                points=[memory_id]
            )
            
            logger.info(f"📉 TIER DEMOTION: Memory {memory_id} demoted from {current_tier.value} to {new_tier.value} ({reason})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to demote memory tier: {e}")
            return False
    
    async def auto_manage_memory_tiers(self, user_id: str) -> Dict[str, int]:
        """Automatically manage memory tiers based on age and significance"""
        try:
            # Get all user memories with tier and age information
            all_memories, _ = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=models.Filter(
                    must=[models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id))]
                ),
                limit=100,  # 🔧 REDUCED: From 1000 to 100 to prevent timeouts in batch processing
                with_payload=True
            )
            
            stats = {
                "promoted": 0,
                "demoted": 0,
                "protected": 0,
                "expired": 0
            }
            
            current_time = datetime.utcnow()
            
            for memory_point in all_memories:
                payload = memory_point.payload
                if not payload:
                    continue
                
                # Calculate memory age
                timestamp_str = payload.get('timestamp')
                if not timestamp_str:
                    continue
                
                memory_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00').replace('+00:00', ''))
                age_days = (current_time - memory_time).days
                
                current_tier = MemoryTier(payload.get('memory_tier', 'short_term'))
                significance = payload.get('overall_significance', 0.5)
                emotional_intensity = payload.get('emotional_intensity', 0.0)
                is_protected = payload.get('decay_protection', False)
                
                memory_id = str(memory_point.id)
                
                # Skip protected memories
                if is_protected:
                    stats["protected"] += 1
                    continue
                
                # Tier management logic based on age and significance
                if current_tier == MemoryTier.SHORT_TERM:
                    # Promote short-term memories that have proven significant
                    if age_days >= 3 and (significance >= 0.6 or emotional_intensity >= 0.7):
                        await self.promote_memory_tier(memory_id, MemoryTier.MEDIUM_TERM, "age_significance")
                        stats["promoted"] += 1
                    # Delete very old, low-significance short-term memories
                    elif age_days >= 7 and significance < 0.3:
                        await self.delete_memory(memory_id)
                        stats["expired"] += 1
                
                elif current_tier == MemoryTier.MEDIUM_TERM:
                    # Promote medium-term memories to long-term if highly significant
                    if age_days >= 7 and (significance >= 0.8 or emotional_intensity >= 0.9):
                        await self.promote_memory_tier(memory_id, MemoryTier.LONG_TERM, "high_significance")
                        stats["promoted"] += 1
                    # Demote medium-term memories that lost relevance
                    elif age_days >= 14 and significance < 0.4:
                        await self.demote_memory_tier(memory_id, MemoryTier.SHORT_TERM, "lost_relevance")
                        stats["demoted"] += 1
                
                # Note: LONG_TERM memories are generally protected from automatic demotion
            
            logger.info(f"🎯 AUTO TIER MANAGEMENT: User {user_id} - "
                       f"Promoted: {stats['promoted']}, Demoted: {stats['demoted']}, "
                       f"Protected: {stats['protected']}, Expired: {stats['expired']}")
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to auto-manage memory tiers: {e}")
            return {"error": 1}
    
    async def get_memories_by_tier(self, user_id: str, tier: MemoryTier, limit: int = 50) -> List[Dict]:
        """Get memories from a specific tier"""
        try:
            results, _ = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id)),
                        models.FieldCondition(key="memory_tier", match=models.MatchValue(value=tier.value))
                    ]
                ),
                limit=limit,
                with_payload=True
            )
            
            memories = []
            for point in results:
                if point.payload:
                    memories.append({
                        "id": str(point.id),
                        "content": point.payload.get('content', ''),
                        "memory_type": point.payload.get('memory_type', ''),
                        "timestamp": point.payload.get('timestamp', ''),
                        "memory_tier": point.payload.get('memory_tier', ''),
                        "significance": point.payload.get('overall_significance', 0.0),
                        "decay_protection": point.payload.get('decay_protection', False)
                    })
            
            # Sort by significance and timestamp
            memories.sort(key=lambda x: (x['significance'], x['timestamp']), reverse=True)
            
            return memories
            
        except Exception as e:
            logger.error(f"Failed to get memories by tier: {e}")
            return []
    
    async def apply_memory_decay(self, user_id: str, decay_rate: float = 0.1) -> Dict[str, int]:
        """
        Apply memory decay mechanism with significance protection
        
        Args:
            user_id: User to apply decay to
            decay_rate: Rate of decay (0.0-1.0, default 0.1 = 10% decay)
            
        Returns:
            Dictionary with decay statistics
        """
        try:
            # Get all user memories for decay processing
            all_memories, _ = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=models.Filter(
                    must=[models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id))]
                ),
                limit=1000,
                with_payload=True
            )
            
            stats = {
                "processed": 0,
                "decayed": 0,
                "protected": 0,
                "deleted": 0,
                "errors": 0
            }
            
            current_time = datetime.utcnow()
            
            for memory_point in all_memories:
                payload = memory_point.payload
                if not payload:
                    continue
                
                memory_id = str(memory_point.id)
                stats["processed"] += 1
                
                try:
                    # Skip protected memories
                    if payload.get('decay_protection', False):
                        stats["protected"] += 1
                        continue
                    
                    # Calculate current significance and age factors
                    current_significance = payload.get('overall_significance', 0.5)
                    memory_tier = MemoryTier(payload.get('memory_tier', 'short_term'))
                    
                    # Calculate memory age in days
                    timestamp_str = payload.get('timestamp')
                    if timestamp_str:
                        memory_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00').replace('+00:00', ''))
                        age_days = (current_time - memory_time).days
                    else:
                        age_days = 0
                    
                    # Calculate decay based on tier and age
                    tier_decay_multiplier = {
                        MemoryTier.SHORT_TERM: 1.0,    # Normal decay
                        MemoryTier.MEDIUM_TERM: 0.5,   # 50% slower decay
                        MemoryTier.LONG_TERM: 0.1      # 90% slower decay
                    }
                    
                    # Age acceleration factor (older memories decay faster)
                    age_multiplier = min(1.0 + (age_days / 30.0), 3.0)  # Max 3x decay for very old memories
                    
                    # Calculate effective decay rate
                    effective_decay = decay_rate * tier_decay_multiplier[memory_tier] * age_multiplier
                    
                    # Apply significance protection
                    if current_significance >= 0.8:
                        effective_decay *= 0.1  # 90% protection for highly significant memories
                    elif current_significance >= 0.6:
                        effective_decay *= 0.3  # 70% protection for moderately significant memories
                    
                    # Apply decay to significance
                    new_significance = max(0.0, current_significance - effective_decay)
                    
                    # Delete memories with very low significance
                    if new_significance < 0.05 and memory_tier == MemoryTier.SHORT_TERM:
                        await self.delete_memory(memory_id)
                        stats["deleted"] += 1
                        continue
                    
                    # Update memory with new significance
                    if new_significance != current_significance:
                        # Update payload with new significance
                        updated_payload = dict(payload)
                        updated_payload['overall_significance'] = new_significance
                        updated_payload['last_decay_update'] = current_time.isoformat()
                        
                        # Set payload in Qdrant
                        self.client.set_payload(
                            collection_name=self.collection_name,
                            points=[memory_id],
                            payload=updated_payload,
                            wait=True
                        )
                        
                        stats["decayed"] += 1
                        
                        logger.debug(f"Applied decay to memory {memory_id}: {current_significance:.3f} → {new_significance:.3f}")
                        
                except Exception as e:
                    logger.error(f"Failed to apply decay to memory {memory_id}: {e}")
                    stats["errors"] += 1
                    continue
            
            logger.info(f"🕰️ MEMORY DECAY: User {user_id} - "
                       f"Processed: {stats['processed']}, Decayed: {stats['decayed']}, "
                       f"Protected: {stats['protected']}, Deleted: {stats['deleted']}, "
                       f"Errors: {stats['errors']}")
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to apply memory decay: {e}")
            return {"error": 1}

    async def get_memory_decay_candidates(self, user_id: str, threshold: float = 0.2) -> List[Dict]:
        """
        Get memories that are candidates for decay (low significance, old)
        
        Args:
            user_id: User to check
            threshold: Significance threshold below which memories are candidates
            
        Returns:
            List of memory dictionaries that are decay candidates
        """
        try:
            # Get all user memories
            all_memories, _ = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=models.Filter(
                    must=[models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id))]
                ),
                limit=1000,
                with_payload=True
            )
            
            candidates = []
            current_time = datetime.utcnow()
            
            for memory_point in all_memories:
                payload = memory_point.payload
                if not payload:
                    continue
                
                # Skip protected memories
                if payload.get('decay_protection', False):
                    continue
                
                significance = payload.get('overall_significance', 0.5)
                
                # Check if below threshold
                if significance <= threshold:
                    # Calculate age
                    timestamp_str = payload.get('timestamp')
                    age_days = 0
                    if timestamp_str:
                        try:
                            memory_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00').replace('+00:00', ''))
                            age_days = (current_time - memory_time).days
                        except ValueError:
                            age_days = 0
                    
                    candidates.append({
                        "id": str(memory_point.id),
                        "content": payload.get('content', '')[:100] + "..." if len(payload.get('content', '')) > 100 else payload.get('content', ''),
                        "significance": significance,
                        "age_days": age_days,
                        "memory_tier": payload.get('memory_tier', 'short_term'),
                        "decay_protection": payload.get('decay_protection', False)
                    })
            
            # Sort by significance (lowest first) and age (oldest first)
            candidates.sort(key=lambda x: (x['significance'], -x['age_days']))
            
            logger.debug(f"Found {len(candidates)} decay candidates for user {user_id} (threshold: {threshold})")
            return candidates
            
        except Exception as e:
            logger.error(f"Failed to get decay candidates: {e}")
            return []

    async def protect_memory_from_decay(self, memory_id: str, protection_reason: str = "manual_protection") -> bool:
        """
        Protect a specific memory from decay
        
        Args:
            memory_id: ID of memory to protect
            protection_reason: Reason for protection
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get current memory
            memory_points = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[memory_id],
                with_payload=True
            )
            
            if not memory_points or not memory_points[0].payload:
                logger.error(f"Memory {memory_id} not found for decay protection")
                return False
            
            # Update with decay protection
            updated_payload = dict(memory_points[0].payload)
            updated_payload['decay_protection'] = True
            updated_payload['protection_reason'] = protection_reason
            updated_payload['protection_date'] = datetime.utcnow().isoformat()
            
            # Set payload in Qdrant
            self.client.set_payload(
                collection_name=self.collection_name,
                points=[memory_id],
                payload=updated_payload,
                wait=True
            )
            
            logger.info(f"🛡️ DECAY PROTECTION: Memory {memory_id} protected from decay ({protection_reason})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to protect memory from decay: {e}")
            return False

    async def remove_memory_decay_protection(self, memory_id: str, removal_reason: str = "manual_removal") -> bool:
        """
        Remove decay protection from a specific memory
        
        Args:
            memory_id: ID of memory to unprotect
            removal_reason: Reason for removing protection
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get current memory
            memory_points = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[memory_id],
                with_payload=True
            )
            
            if not memory_points or not memory_points[0].payload:
                logger.error(f"Memory {memory_id} not found for protection removal")
                return False
            
            # Update to remove decay protection
            updated_payload = dict(memory_points[0].payload)
            updated_payload['decay_protection'] = False
            updated_payload['protection_removal_reason'] = removal_reason
            updated_payload['protection_removal_date'] = datetime.utcnow().isoformat()
            
            # Remove protection-related fields
            updated_payload.pop('protection_reason', None)
            updated_payload.pop('protection_date', None)
            
            # Set payload in Qdrant
            self.client.set_payload(
                collection_name=self.collection_name,
                points=[memory_id],
                payload=updated_payload,
                wait=True
            )
            
            logger.info(f"🔓 DECAY PROTECTION REMOVED: Memory {memory_id} unprotected ({removal_reason})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove memory decay protection: {e}")
            return False

    async def get_protected_memories(self, user_id: str) -> List[Dict]:
        """
        Get all memories with decay protection for a user
        
        Args:
            user_id: User to check
            
        Returns:
            List of protected memory dictionaries
        """
        try:
            # Get all protected memories for user
            protected_memories, _ = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id)),
                        models.FieldCondition(key="decay_protection", match=models.MatchValue(value=True))
                    ]
                ),
                limit=100,
                with_payload=True
            )
            
            memories = []
            for memory_point in protected_memories:
                if memory_point.payload:
                    memories.append({
                        "id": str(memory_point.id),
                        "content": memory_point.payload.get('content', ''),
                        "memory_tier": memory_point.payload.get('memory_tier', 'short_term'),
                        "significance": memory_point.payload.get('overall_significance', 0.5),
                        "protection_reason": memory_point.payload.get('protection_reason', 'unknown'),
                        "protection_date": memory_point.payload.get('protection_date', ''),
                        "timestamp": memory_point.payload.get('timestamp', '')
                    })
            
            # Sort by protection date (most recent first)
            memories.sort(key=lambda x: x['protection_date'], reverse=True)
            
            logger.debug(f"Found {len(memories)} protected memories for user {user_id}")
            return memories
            
        except Exception as e:
            logger.error(f"Failed to get protected memories: {e}")
            return []

    async def get_recent_memories(self, user_id: str, limit: int = 20) -> List[Dict]:
        """Get recent memories for significance calculation"""
        try:
            # Use direct Qdrant search since we're in VectorMemoryStore
            filter_conditions = [
                models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id))
                # 🎯 REMOVED: bot_name filter - collection isolation makes this redundant
            ]

            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=models.NamedVector(name="content", vector=[0.0] * 384),  # Dummy vector for recent search
                query_filter=models.Filter(must=filter_conditions),
                limit=limit,
                with_payload=True
            )

            memories = []
            for point in results:
                if point.payload:
                    memories.append({
                        "id": str(point.id),
                        "content": point.payload.get('content', ''),
                        "memory_type": point.payload.get('memory_type', ''),
                        "timestamp": point.payload.get('timestamp', ''),
                        "confidence": point.payload.get('confidence', 0.5),
                    })
            
            return memories
            
        except Exception as e:
            logger.error(f"Failed to get recent memories: {e}")
            return []

    async def get_user_emotional_patterns(self, user_id: str) -> Dict:
        """Get user's emotional patterns for significance calculation"""
        try:
            # This would integrate with the emotional trajectory tracking
            recent_emotions = await self.get_recent_emotional_states(user_id, limit=10)
            
            if not recent_emotions:
                return {}
            
            # Find most frequent recent emotion
            emotion_counts = {}
            for emotion in recent_emotions:
                emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
            
            most_frequent = max(emotion_counts, key=emotion_counts.get) if emotion_counts else 'neutral'
            
            return {
                'recent_emotional_pattern': most_frequent,
                'frequent_themes': []  # Could be enhanced with more analysis
            }
        except Exception as e:
            logger.error(f"Error getting user emotional patterns: {e}")
            return {}

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
                                                      memory_types: Optional[List[str]] = None,
                                                      top_k: int = 10,
                                                      min_score: float = 0.3,  # 🔧 TUNING: Lowered from 0.7 to 0.3 for better recall
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
            # 🎯 COLLECTION ISOLATION: No bot_name filter needed - each collection is bot-specific
            must_conditions = [
                models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id))
                # 🎯 REMOVED: bot_name filter - collection isolation makes this redundant
            ]
            
            if memory_types:
                must_conditions.append(
                    models.FieldCondition(
                        key="memory_type", 
                        match=models.MatchAny(any=memory_types)  # memory_types is already a list of strings
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
        
        ENHANCED: Now detects both "recent/last" AND "first/earliest" temporal patterns
        """
        temporal_keywords = [
            # Recent/Last patterns (existing)
            'last', 'recent', 'just', 'earlier', 'before', 'previous', 
            'moments ago', 'just now', 'a moment ago', 'just said',
            'just told', 'just asked', 'just mentioned', 'recently',
            'talked about', 'discussed', 'remember', 'recall',
            'what have we', 'what did we', 'our conversation',
            'we were talking', 'we chatted', 'we spoke',
            # First/Earliest patterns (NEW - Bug Fix #2)
            'first', 'earliest', 'initial', 'started with', 'began',
            'first thing', 'very first', 'initially', 'at first',
            'when did', 'how long ago', 'since when', 'start of',
            'beginning of', 'opening', 'first time'
        ]
        
        query_lower = query.lower()
        is_temporal = any(keyword in query_lower for keyword in temporal_keywords)
        
        if is_temporal:
            logger.debug(f"🎯 TEMPORAL DETECTION: Query '{query}' matched temporal pattern")
        
        return is_temporal

    async def _handle_temporal_query_with_qdrant(self, query: str, user_id: str, limit: int) -> List[Dict[str, Any]]:
        """
        🎯 QDRANT-NATIVE: Handle temporal queries using scroll API for chronological context
        
        ENHANCED (Bug Fix #2): Now detects "first" vs "last" queries and orders accordingly
        """
        try:
            # 🎯 NEW: Detect query direction (first/earliest vs last/recent)
            query_lower = query.lower()
            first_keywords = ['first', 'earliest', 'initial', 'started', 'began', 'opening', 'very first']
            is_first_query = any(keyword in query_lower for keyword in first_keywords)
            
            # Determine temporal direction
            direction = Direction.ASC if is_first_query else Direction.DESC  # ASC = oldest first, DESC = newest first
            direction_label = "FIRST/EARLIEST" if is_first_query else "LAST/RECENT"
            
            logger.info(f"🎯 TEMPORAL DIRECTION: Detected '{direction_label}' query pattern")
            
            # Generate embedding for semantic search if needed
            query_embedding = await self.generate_embedding(query)
            
            # 🚀 QDRANT FEATURE: Use scroll API to get recent conversation chronologically
            # Convert to Unix timestamp for Qdrant numeric range filtering
            # 🎯 SMART SESSION DETECTION: Context-aware time windows
            if "today" in query_lower or "this morning" in query_lower or "this afternoon" in query_lower:
                # "Today" means current session (last 4 hours is typical active session)
                recent_cutoff_dt = datetime.utcnow() - timedelta(hours=4)
                logger.info(f"🎯 SESSION SCOPE: Detected 'today' - using 4-hour session window")
            elif direction_label == "FIRST/EARLIEST":
                # 🎯 BUG FIX: "First" questions should default to current session (4 hours)
                # Without session context, "first" queries return chronologically oldest memories
                # from the entire 24-hour window, not the first in current conversation
                recent_cutoff_dt = datetime.utcnow() - timedelta(hours=4)
                logger.info(f"🎯 SESSION SCOPE: 'First' query - defaulting to 4-hour session window to avoid historical bleed")
            else:
                # General temporal queries use 24-hour window
                recent_cutoff_dt = datetime.utcnow() - timedelta(hours=24)
                logger.info(f"🎯 SESSION SCOPE: General temporal query - using 24-hour window")
            
            recent_cutoff_timestamp = recent_cutoff_dt.timestamp()
            
            # Get recent conversation messages in chronological order
            # 🎯 COLLECTION ISOLATION: No bot_name filter needed - each collection is bot-specific
            scroll_result = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id)),
                        # 🎯 REMOVED: bot_name filter - collection isolation makes this redundant
                        models.FieldCondition(key="memory_type", match=models.MatchValue(value="conversation")),
                        models.FieldCondition(key="timestamp_unix", range=Range(gte=recent_cutoff_timestamp))
                    ]
                ),
                limit=50,  # 🔧 INCREASED: Get more context for rich conversations (was 20)
                with_payload=True,
                with_vectors=False,  # Don't need vectors for temporal queries
                order_by=models.OrderBy(key="timestamp_unix", direction=direction)  # 🎯 DIRECTION-AWARE ordering
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
                            # 🎯 REMOVED: bot_name filter - collection isolation makes this redundant
                            models.FieldCondition(key="memory_type", match=models.MatchAny(any=["conversation", "fact", "preference"]))
                        ]
                    ),
                    limit=limit,
                    score_threshold=0.25,  # 🔧 LOWERED: From 0.5 to 0.25 for better temporal query recall
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
            
            # 🚀 FIX: Return chronological context regardless of semantic similarity
            # For conversation continuity, recent messages should be included even if not semantically related
            # 🎯 SMART LIMITING: For "first" queries, return only first 1-3 messages (not all context)
            if is_first_query:
                # When asking "what was the first thing", return JUST the first message(s)
                actual_limit = min(3, limit)  # Maximum 3 messages for "first" queries
                logger.info(f"🎯 FIRST QUERY LIMIT: Reducing from {limit} to {actual_limit} for precise recall")
            else:
                # "Last/recent" queries can return more context
                actual_limit = limit
            
            formatted_results = []
            for i, point in enumerate(recent_messages[:actual_limit]):  # Use smart limit
                # Handle payload safely
                payload = getattr(point, 'payload', {}) or {}
                formatted_results.append({
                    "id": str(point.id),
                    "score": 1.0,  # Give temporal context high relevance score
                    "content": payload.get('content', ''),
                    "memory_type": payload.get('memory_type', ''),
                    "timestamp": payload.get('timestamp', ''),
                    "confidence": payload.get('confidence', 0.5),
                    "metadata": payload,
                    "temporal_query": True,
                    "temporal_direction": direction_label,  # 🎯 NEW: Indicate query direction
                    "qdrant_chronological": True,
                    "temporal_rank": i + 1  # Chronological position (first/most recent = 1)
                })
            
            logger.info(f"🎯 QDRANT-TEMPORAL ({direction_label}): Found {len(formatted_results)} chronologically ordered memories")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Qdrant temporal query handling failed: {e}")
            return []

    async def _fallback_basic_search(self, query: str, user_id: str, memory_types: Optional[List[str]], 
                                   top_k: int, min_score: float) -> List[Dict[str, Any]]:
        """Fallback to basic Qdrant search if advanced features fail with progressive threshold lowering"""
        try:
            query_embedding = await self.generate_embedding(query)
            filter_conditions = [models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id))]
            
            if memory_types:
                filter_conditions.append(
                    models.FieldCondition(key="memory_type", match=models.MatchAny(any=memory_types))  # memory_types is already a list of strings
                )
            
            # 🔧 TUNING: Progressive threshold lowering for better recall
            thresholds_to_try = [min_score, 0.2, 0.1, 0.05]  # Try progressively lower thresholds
            
            for threshold in thresholds_to_try:
                results = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=models.NamedVector(name="content", vector=query_embedding),  # 🎯 NAMED VECTOR
                    query_filter=models.Filter(must=filter_conditions),
                    limit=top_k,
                    score_threshold=threshold
                )
                
                if results:  # If we got results, return them
                    logger.info(f"🔧 FALLBACK: Retrieved {len(results)} memories with threshold {threshold}")
                    return [{
                        "id": point.id,
                        "score": point.score,
                        "content": point.payload['content'],
                        "memory_type": point.payload['memory_type'],
                        "timestamp": point.payload['timestamp'],
                        "confidence": point.payload.get('confidence', 0.5),
                        "metadata": point.payload,
                        "fallback_used": True,
                        "threshold_used": threshold
                    } for point in results]
            
            # If no results with any threshold, log warning
            logger.warning(f"🔧 FALLBACK: No memories found for user {user_id} with query '{query}' even with lowest threshold")
            return []
            
        except Exception as e:
            logger.error(f"Fallback search also failed: {e}")
            return []

    async def search_with_multi_vectors(self, 
                                      content_query: str,
                                      emotional_query: Optional[str] = None,
                                      personality_context: Optional[str] = None,
                                      user_id: str = None,
                                      memory_types: Optional[List[str]] = None,
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
            # 🎯 COLLECTION ISOLATION: No bot_name filter needed - each collection is bot-specific
            base_filter_conditions: List[models.Condition] = [
                models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id))
                # 🎯 REMOVED: bot_name filter - collection isolation makes this redundant
            ]
            
            if memory_types:
                base_filter_conditions.append(
                    models.FieldCondition(key="memory_type", match=models.MatchAny(any=memory_types))
                )

            if emotion_embedding and personality_embedding:
                # 🚀 TRIPLE-VECTOR: Use emotion vector for emotional intelligence
                logger.info("🎯 QDRANT: Using triple-vector search (content + emotion + personality)")
                
                # Primary search with emotion vector for emotional context
                emotion_results = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=models.NamedVector(name="emotion", vector=emotion_embedding),  # 🎭 Use emotion vector
                    query_filter=models.Filter(must=base_filter_conditions),
                    limit=top_k // 2,  # Get half results from emotion vector
                    with_payload=True
                )
                
                # Secondary search with content vector for semantic meaning  
                content_results = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=models.NamedVector(name="content", vector=content_embedding),  # 🧠 Use content vector
                    query_filter=models.Filter(must=base_filter_conditions),
                    limit=top_k // 2,  # Get half results from content vector
                    with_payload=True
                )
                
                # Combine and deduplicate results
                results = list(emotion_results) + [r for r in content_results if r.id not in [e.id for e in emotion_results]]
                
            elif emotion_embedding:
                # 🎭 DUAL-VECTOR: Prioritize emotion vector for emotional intelligence
                logger.info("🎯 QDRANT: Using dual-vector search (emotion + content)")
                results = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=models.NamedVector(name="emotion", vector=emotion_embedding),  # 🎭 Use emotion vector
                    query_filter=models.Filter(must=base_filter_conditions),
                    limit=top_k,
                    with_payload=True
                )
                
            else:
                # 🧠 SINGLE-VECTOR: Content-only fallback
                logger.info("🎯 QDRANT: Using single-vector search (content only)")
                results = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=models.NamedVector(name="content", vector=content_embedding),  # 🧠 Use content vector
                    query_filter=models.Filter(must=base_filter_conditions),
                    limit=top_k,
                    with_payload=True
                )
            
            # Format results with multi-vector context
            formatted_results = []
            for point in results:
                if point.payload:  # 🎯 SAFETY: Check payload exists
                    formatted_results.append({
                        "id": point.id,
                        "score": point.score,
                        "content": point.payload.get('content', ''),
                        "memory_type": point.payload.get('memory_type', 'unknown'),
                        "timestamp": point.payload.get('timestamp', ''),
                        "confidence": point.payload.get('confidence', 0.5),
                        "metadata": point.payload,
                        "multi_vector_search": True,
                        "vectors_used": {
                            "content": True,
                            "emotion": emotion_embedding is not None,
                            "personality": personality_embedding is not None
                        }
                    })
                else:
                    logger.warning(f"🚨 QDRANT: Point {point.id} has no payload, skipping")
            
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
                        must_not=[
                            models.FieldCondition(key="id", match=models.MatchValue(value=memory.id))
                        ],
                        must=[
                            models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id))
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
                    if similar.payload:  # 🎯 SAFETY: Check payload exists
                        cluster_memories.append({
                            "id": similar.id,
                            "content": similar.payload.get('content', ''),
                            "timestamp": similar.payload.get('timestamp', ''),
                            "confidence": similar.payload.get('confidence', 0.5),
                            "similarity_score": similar.score,
                            "is_seed": False
                        })
                        processed_ids.add(similar.id)
                    else:
                        logger.warning(f"🚨 QDRANT: Similar memory {similar.id} has no payload, skipping")
                
                clusters[cluster_key] = cluster_memories
                processed_ids.add(memory.id)
                
                logger.info(f"🎯 QDRANT CLUSTER: Created '{cluster_theme}' cluster with {len(cluster_memories)} memories")
            
            return clusters
            
        except Exception as e:
            logger.error(f"Memory clustering failed: {e}")
            return {"error": [{"error": str(e)}]}  # 🎯 FIXED: Return proper type structure

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

    async def get_conversation_summary_with_recommendations(
        self, 
        user_id: str, 
        conversation_history: List[Dict[str, Any]], 
        limit: int = 5
    ) -> Dict[str, str]:
        """
        🚀 QDRANT RECOMMENDATION: Zero-LLM conversation summarization using vector similarity
        
        Benefits:
        - 100% LLM call reduction vs traditional summarization
        - Uses semantic vector relationships for topic detection
        - Leverages existing recommendation API infrastructure
        - Provides thematic conversation context without AI generation costs
        
        Args:
            user_id: User identifier for bot-specific filtering
            conversation_history: Recent conversation messages
            limit: Number of related conversations to analyze for patterns
            
        Returns:
            Dict with 'topic_summary' and 'conversation_themes' keys
        """
        try:
            if not conversation_history:
                return {
                    "topic_summary": "Starting new conversation",
                    "conversation_themes": "initial_contact",
                    "recommendation_method": "empty_history"
                }
            
            # Extract the most recent meaningful message for pattern matching
            recent_content = ""
            recent_message_id = None
            
            for msg in reversed(conversation_history):
                content = msg.get('content', '').strip()
                if content and len(content) > 10:  # Skip very short messages
                    recent_content = content
                    recent_message_id = msg.get('id')
                    break
            
            if not recent_content:
                return {
                    "topic_summary": "Continuing conversation",
                    "conversation_themes": "general",
                    "recommendation_method": "no_meaningful_content"
                }
            
            # 🎯 QDRANT RECOMMENDATION: Find semantically similar conversations
            # 🎯 COLLECTION ISOLATION: No bot_name needed - each collection is bot-specific
            
            if recent_message_id:
                # Use existing message ID for recommendation
                try:
                    related_conversations = self.client.recommend(
                        collection_name=self.collection_name,
                        positive=[recent_message_id],
                        query_filter=models.Filter(
                            must=[
                                models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id)),
                                # 🎯 REMOVED: bot_name filter - collection isolation makes this redundant
                                models.FieldCondition(key="memory_type", match=models.MatchValue(value="conversation"))
                            ]
                        ),
                        limit=limit,
                        score_threshold=0.5,  # Lower threshold for broader topic detection
                        with_payload=True,
                        using="semantic"  # Use semantic vector for topic similarity
                    )
                except Exception as e:
                    logger.debug("Recommendation by ID failed, falling back to content search: %s", str(e))
                    related_conversations = []
            else:
                related_conversations = []
            
            # Fallback: Search by content if recommendation by ID fails
            if not related_conversations:
                content_embedding = await self.generate_embedding(recent_content)
                related_conversations = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=models.NamedVector(name="semantic", vector=content_embedding),
                    query_filter=models.Filter(
                        must=[
                            models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id)),
                            # 🎯 REMOVED: bot_name filter - collection isolation makes this redundant
                            models.FieldCondition(key="memory_type", match=models.MatchValue(value="conversation"))
                        ]
                    ),
                    limit=limit,
                    score_threshold=0.4,
                    with_payload=True
                )
            
            # 🎯 ZERO-LLM ANALYSIS: Extract themes using pattern recognition
            themes = set()
            topic_keywords = set()
            
            # Analyze current message
            current_theme = self._identify_cluster_theme(recent_content)
            themes.add(current_theme)
            
            # Extract keywords from current content (simple but effective)
            content_words = recent_content.lower().split()
            meaningful_words = [word for word in content_words 
                             if len(word) > 3 and word not in self._get_stop_words()]
            topic_keywords.update(meaningful_words[:3])  # Top 3 meaningful words
            
            # Analyze related conversations for patterns
            for point in related_conversations:
                if hasattr(point, 'payload') and point.payload:
                    content = point.payload.get('content', '')
                    if content:
                        # Extract theme using existing method
                        theme = self._identify_cluster_theme(content)
                        themes.add(theme)
                        
                        # Extract additional keywords
                        words = content.lower().split()
                        keywords = [word for word in words 
                                  if len(word) > 3 and word not in self._get_stop_words()]
                        topic_keywords.update(keywords[:2])  # Top 2 from each related conversation
            
            # 🎯 TEMPLATE-BASED SUMMARY: Generate summary without LLM
            if len(themes) > 1:
                themes.discard('general')  # Remove generic theme if we have specific ones
            
            theme_list = list(themes)[:3]  # Top 3 themes
            keyword_list = list(topic_keywords)[:5]  # Top 5 keywords
            
            # Create natural summary using templates
            if theme_list:
                primary_theme = theme_list[0]
                if len(theme_list) > 1:
                    topic_summary = f"Discussing {primary_theme} and {', '.join(theme_list[1:])}"
                else:
                    topic_summary = f"Focused on {primary_theme}"
            else:
                topic_summary = "General conversation"
            
            # Add keyword context if available
            if keyword_list:
                topic_summary += f" (topics: {', '.join(keyword_list[:3])})"
            
            return {
                "topic_summary": topic_summary,
                "conversation_themes": ", ".join(theme_list) if theme_list else "general",
                "recommendation_method": "qdrant_semantic",
                "related_conversations_found": len(related_conversations),
                "themes_detected": len(themes)
            }
            
        except Exception as e:
            logger.error("Recommendation-based conversation summary failed: %s", str(e))
            # Graceful fallback
            return {
                "topic_summary": "Continuing previous conversation",
                "conversation_themes": "general",
                "recommendation_method": "error_fallback",
                "error": str(e)
            }
    
    def _get_stop_words(self) -> set:
        """Get common stop words for keyword extraction"""
        return {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
            'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their'
        }

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
                    with_vectors=["content", "emotion", "semantic"]  # ✅ FIXED: Specify named vectors to retrieve
                )[0]
                
                if not existing_point:
                    continue
                
                # Update payload while preserving vectors 🎯 SAFETY: Check payload exists
                if existing_point.payload:
                    updated_payload = existing_point.payload.copy()
                    updated_payload.update(update.get('payload_updates', {}))
                else:
                    updated_payload = update.get('payload_updates', {})
                    logger.warning(f"🚨 QDRANT: Point {point_id} has no payload, using updates only")
                
                # Add batch update metadata
                updated_payload['batch_updated_at'] = datetime.utcnow().isoformat()
                updated_payload['update_reason'] = update.get('reason', 'batch_update')
                
                # Create point with proper named vector handling
                if existing_point.vector:
                    # Extract and reconstruct named vectors properly
                    named_vectors = self._create_named_vectors_dict(existing_point.vector)
                    
                    points_to_update.append(
                        PointStruct(
                            id=point_id,
                            vector=named_vectors,  # type: ignore # ✅ FIXED: Proper named vector structure
                            payload=updated_payload
                        )
                    )
                else:
                    # Skip points without vectors - they can't be properly updated
                    logger.warning(f"🚨 QDRANT: Point {point_id} has no vector, skipping update")
            
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
                if not point.payload:  # 🎯 SAFETY: Check payload exists
                    logger.warning(f"🚨 QDRANT: Recommendation point {point.id} has no payload, skipping")
                    continue
                    
                # Calculate content similarity to detect actual contradictions
                existing_content = point.payload.get('content', '')
                if not existing_content:
                    continue
                    
                content_similarity = await self._calculate_content_similarity(new_memory_content, existing_content)
                
                # High semantic similarity but low content similarity = contradiction
                if point.score > 0.8 and content_similarity < 0.7:
                    contradictions.append({
                        "existing_memory": {
                            "id": point.id,
                            "content": existing_content,
                            "timestamp": point.payload.get('timestamp', ''),
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
                memory_types=[MemoryType.FACT.value, MemoryType.PREFERENCE.value],  # Convert enums to strings
                limit=20  # Fixed: interface contract violation - use 'limit' not 'top_k'
            )
            
            contradictions = []
            new_embedding = await self.generate_embedding(new_content)
            
            for memory in similar_memories:
                # High semantic similarity but different content suggests contradiction
                memory_embedding = await self.generate_embedding(memory['content'])
                
                # Calculate similarity using numpy dot product
                def cosine_similarity_np(a, b):
                    """Numpy-based cosine similarity calculation"""
                    a, b = np.array(a), np.array(b)
                    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
                
                content_similarity = cosine_similarity_np(new_embedding, memory_embedding)
                
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
            
            # Update payload 🎯 SAFETY: Check payload exists
            existing_point = existing_points[0]
            if existing_point.payload:
                existing_payload = existing_point.payload.copy()
                existing_payload.update({
                    "content": new_content,
                    "updated_at": datetime.utcnow().isoformat(),
                    "update_reason": reason,
                    "corrected": True
                })
            else:
                existing_payload = {
                    "content": new_content,
                    "updated_at": datetime.utcnow().isoformat(),
                    "update_reason": reason,
                    "corrected": True
                }
                logger.warning(f"🚨 QDRANT: Point {memory_id} has no payload, creating new one")
            
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
    
    async def search_memories(self, 
                             user_id: str,
                             query: str,
                             memory_types: Optional[List[str]] = None,
                             limit: int = 10) -> List[Dict[str, Any]]:
        """
        Protocol-compliant search method for VectorMemoryStore.
        
        STANDARDIZED INTERFACE - matches MemoryManagerProtocol:
        - user_id: str (required)
        - query: str (required) 
        - memory_types: Optional[List[str]] (protocol standard - strings, not enums)
        - limit: int (protocol standard - not top_k)
        """
        # Convert string memory types back to strings for internal method (protocol compliance)
        vector_memory_types = memory_types  # Keep as strings - protocol compliant
        
        return await self.search_memories_with_qdrant_intelligence(
            query=query,
            user_id=user_id,
            memory_types=vector_memory_types,  # Already strings, no conversion needed
            top_k=limit,  # Convert limit to top_k for internal method
            min_score=0.3,  # 🔧 TUNING: Lowered from 0.7 to 0.3 for better recall
            prefer_recent=True
        )


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
        
        # 🎯 TYPE SAFETY: Validate required parameters
        if not all([user_id, subject, old_value, new_value]):
            return "Error: Missing required parameters (user_id, subject, old_value, new_value)"
        
        # Convert to strings for type safety
        user_id = str(user_id)
        subject = str(subject)
        old_value = str(old_value)
        new_value = str(new_value)
        reason = str(reason)
        
        try:
            # Find existing fact
            existing_memories = await self.vector_store.search_memories(
                query=f"{subject} {old_value}",
                user_id=user_id,
                memory_types=[MemoryType.FACT.value]
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
                    id=str(uuid4()),  # Pure UUID for Qdrant compatibility
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
        
        # 🎯 TYPE SAFETY: Validate required parameters
        if not all([user_id, query]):
            return "Error: Missing required parameters (user_id, query)"
        
        # Convert to strings for type safety
        user_id = str(user_id)
        query = str(query)
        
        try:
            memory_types = None
            if memory_type:
                memory_types = [MemoryType(memory_type).value]  # Convert to string for protocol compliance
            
            results = await self.vector_store.search_memories(
                query=query,
                user_id=user_id,
                memory_types=memory_types,
                limit=5  # Fixed: interface contract violation - use 'limit' not 'top_k'
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
        
        # 🎯 TYPE SAFETY: Validate required parameters
        if not all([user_id, content]):
            return "Error: Missing required parameters (user_id, content_to_delete)"
        
        # Convert to strings for type safety
        user_id = str(user_id)
        content = str(content)
        reason = str(reason)
        
        try:
            # Find memories to delete
            memories = await self.vector_store.search_memories(
                query=content,
                user_id=user_id,
                limit=5  # Use protocol-compliant parameters only
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
        
        embedding_model = embeddings_config.get('model_name', '')
        # Empty string means use sentence-transformers/all-MiniLM-L6-v2 (best 384D model)
        if embedding_model is None:
            raise ValueError("Missing 'model_name' in embeddings configuration")
            
        logger.info(f"[VECTOR-MEMORY-DEBUG] Using embedding model: '{embedding_model}' (empty = FastEmbed default)")
        logger.info(f"[VECTOR-MEMORY-DEBUG] Full embeddings config: {embeddings_config}")
        logger.info(f"[VECTOR-MEMORY-DEBUG] Full vector config: {config}")
        
        # Core vector store (single source of truth) - LOCAL IMPLEMENTATION
        self.vector_store = VectorMemoryStore(
            qdrant_host=qdrant_host,
            qdrant_port=qdrant_port,
            collection_name=collection_name,
            embedding_model=embedding_model
        )
        
        # Initialize temporal intelligence client for metrics recording
        self.temporal_client = None
        try:
            from src.temporal.temporal_intelligence_client import TemporalIntelligenceClient
            self.temporal_client = TemporalIntelligenceClient()
        except ImportError:
            logger.warning("TemporalIntelligenceClient not available - metrics recording disabled")
        
        # DEBUG: Verify logging is working
        logger.debug("🔥 VECTOR MEMORY MANAGER INITIALIZED - DEBUG LOGGING ACTIVE 🔥")
        
        # Store config for other services (PostgreSQL for user data, Redis for session cache)
        self.config = config
        
        # LLM-callable memory tools
        self.memory_tools = MemoryTools(self.vector_store)
        
        # Session cache for performance (Redis for hot data only)
        self.session_cache = None  # Will be initialized if Redis available
        
        # 🚀 SPRINT 2: Initialize MemoryBoost components for enhanced memory optimization
        try:
            self.initialize_memoryboost_components()
            logger.info("🚀 MEMORYBOOST: Advanced memory optimization components initialized")
        except Exception as e:
            logger.warning("🚀 MEMORYBOOST: Component initialization failed, continuing without MemoryBoost: %s", str(e))
        
        # 🎯 SPRINT 2 ENHANCEMENT: Initialize multi-vector intelligence coordinator
        try:
            self._multi_vector_coordinator = create_multi_vector_search_coordinator(
                vector_memory_system=self.vector_store
            )
            logger.info("🎯 Multi-vector intelligence coordinator initialized for enhanced search")
        except Exception as e:
            logger.warning(f"🎯 Multi-vector coordinator initialization failed: {e}")
            self._multi_vector_coordinator = None
        
        logger.info("VectorMemoryManager initialized - local-first single source of truth ready")
    
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
                    MemoryType.CONVERSATION.value,
                    MemoryType.FACT.value,
                    MemoryType.PREFERENCE.value
                ],
                limit=20
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
            
            # 🧠 AUDIT: Log emotional data being stored
            if pre_analyzed_emotion_data:
                logger.info(f"🧠 EMOTION AUDIT: Storing conversation with pre-analyzed emotion data: {list(pre_analyzed_emotion_data.keys())}")
                logger.info(f"🧠 EMOTION AUDIT: Primary emotion: {pre_analyzed_emotion_data.get('primary_emotion', 'unknown')}")
                logger.info(f"🧠 EMOTION AUDIT: Mixed emotions: {pre_analyzed_emotion_data.get('mixed_emotions', 'none')}")
            else:
                logger.info(f"🧠 EMOTION AUDIT: No pre-analyzed emotion data provided for user {user_id}")
            
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
        limit: int = 25  # 🔧 ENHANCED: Increased from 15 to 25 for chunked conversation reassembly
    ) -> List[Dict[str, Any]]:
        """
        Retrieve memories relevant to the given query using intelligent vector selection.
        
        🚀 MULTI-VECTOR INTELLIGENCE: Automatically selects appropriate named vector based on query intent:
        - Emotional queries → emotion vector (feelings, mood, emotional state)
        - Pattern queries → semantic vector (relationship patterns, behavioral trends)
        - Content queries → content vector (semantic meaning, topics, facts)
        """
        import time
        
        start_time = time.time()
        try:
            # 🎯 CRITICAL FIX: Add temporal query detection BEFORE semantic search
            # This fixes Test 5 temporal intelligence where "first question today" was failing
            is_temporal_query = await self.vector_store._detect_temporal_query_with_qdrant(query, user_id)
            
            if is_temporal_query:
                logger.info(f"🎯 TEMPORAL QUERY DETECTED: '{query}' - Using chronological retrieval")
                temporal_results = await self.vector_store._handle_temporal_query_with_qdrant(query, user_id, limit)
                
                # Format temporal results to match expected structure
                formatted_results = []
                for r in temporal_results:
                    formatted_results.append({
                        "content": r.get("content", ""),
                        "score": r.get("score", 1.0),  # High score for temporal matches
                        "timestamp": r.get("timestamp", ""),
                        "metadata": r.get("metadata", {}),
                        "memory_type": r.get("memory_type", "conversation"),
                        "temporal": True,
                        "search_type": "temporal_chronological"
                    })
                
                logger.debug(f"🎯 TEMPORAL SEARCH: Retrieved {len(formatted_results)} memories in {(time.time() - start_time)*1000:.1f}ms")
                return formatted_results
            
            # 🎭 INTELLIGENT VECTOR SELECTION: Route to appropriate named vector based on query intent
            query_lower = query.lower()
            
            # Emotional queries → use emotion vector for better emotional context matching
            emotional_keywords = ['feel', 'feeling', 'felt', 'mood', 'emotion', 'emotional', 
                                 'happy', 'sad', 'angry', 'excited', 'worried', 'anxious',
                                 'joyful', 'depressed', 'upset', 'frustrated', 'content']
            if any(keyword in query_lower for keyword in emotional_keywords):
                logger.info(f"🎭 EMOTIONAL QUERY DETECTED: '{query}' - Using emotion vector search")
                try:
                    emotion_results = await self.vector_store.search_memories_with_qdrant_intelligence(
                        query=query,
                        user_id=user_id,
                        top_k=limit,
                        emotional_context=query  # Use same query for emotion matching
                    )
                    
                    if emotion_results:
                        formatted_results = []
                        for r in emotion_results:
                            formatted_results.append({
                                "content": r.get("content", ""),
                                "score": r.get("score", 0.0),
                                "timestamp": r.get("timestamp", ""),
                                "metadata": r.get("metadata", {}),
                                "memory_type": r.get("memory_type", "conversation"),
                                "emotional": True,
                                "search_type": "emotion_vector"
                            })
                        
                        logger.debug(f"🎭 EMOTION VECTOR: Retrieved {len(formatted_results)} memories in {(time.time() - start_time)*1000:.1f}ms")
                        return formatted_results
                except Exception as e:
                    logger.warning(f"Emotion vector search failed, falling back to content: {e}")
            
            # Default: Content vector for semantic meaning and topics
            # NOTE: Pattern/semantic vector routing disabled due to infinite recursion
            # get_memory_clusters_for_roleplay() internally calls retrieve_relevant_memories()
            # TODO: Refactor to prevent recursion before re-enabling pattern routing
            logger.debug(f"🧠 CONTENT QUERY: '{query}' - Using content vector (default)")
            
            # 🚀 SIMPLIFIED: Trust vector embeddings for semantic search
            # RoBERTa-enhanced emotional metadata from storage provides the intelligence
            # No need for query-time emotion analysis - embeddings capture meaning naturally
            
            # 🎯 SPRINT 2 ENHANCEMENT: Multi-vector intelligence for emotion/semantic vectors
            if self._multi_vector_coordinator:
                try:
                    logger.debug(f"🎯 Using multi-vector intelligence for query: '{query}'")
                    multi_vector_result = await self._multi_vector_coordinator.intelligent_multi_vector_search(
                        query=query,
                        user_id=user_id,
                        limit=limit
                    )
                    
                    if multi_vector_result.memories:
                        logger.debug(f"🎯 MULTI-VECTOR: Retrieved {len(multi_vector_result.memories)} memories using {multi_vector_result.fusion_strategy} strategy")
                        return multi_vector_result.memories
                        
                except Exception as e:
                    logger.warning(f"Multi-vector search failed, falling back to standard search: {e}")
            
            # 🚀 PERFORMANCE: Use optimized search if query optimizer available
            try:
                from src.memory.qdrant_optimization import QdrantQueryOptimizer
                optimizer = QdrantQueryOptimizer(self.vector_store)
                
                # Use standard optimized search without emotion filtering
                results = await optimizer.optimized_search(
                    query=query,
                    user_id=user_id,
                    query_type="semantic_search", 
                    user_history={},
                    filters={}  # No emotion filters - trust embeddings
                )
                
                # Convert to expected format and limit results
                formatted_results = []
                for r in results[:limit]:
                    formatted_results.append({
                        "content": r.get("content", ""),
                        "score": r.get("score", 0.0), 
                        "timestamp": r.get("timestamp", ""),
                        "metadata": r.get("metadata", {}),
                        "memory_type": r.get("memory_type", "unknown"),
                        "optimized": True,
                        "search_type": "semantic_similarity"
                    })
                
                logger.debug(f"🚀 SEMANTIC SEARCH: Retrieved {len(formatted_results)} memories in {(time.time() - start_time)*1000:.1f}ms")
                return formatted_results
                
            except (ImportError, Exception) as e:
                logger.debug(f"QdrantQueryOptimizer not available, using emotion-enhanced standard search: {e}")
                
            # 🎭 ENHANCED FALLBACK: Use protocol-compliant search method
            results = await self.vector_store.search_memories(
                user_id=user_id,
                query=query,
                limit=limit
            )
            
            formatted_results = [
                {
                    "content": r.get("content", ""),
                    "score": r.get("score", 0.0),
                    "timestamp": r.get("timestamp", ""),
                    "metadata": r.get("metadata", {}),
                    "memory_type": r.get("memory_type", "unknown"),
                    "optimized": False
                }
                for r in results
            ]
            
            # 📊 TEMPORAL METRICS: Record vector memory performance
            try:
                query_time_ms = int((time.time() - start_time) * 1000)
                avg_relevance = sum(r.get("score", 0.0) for r in formatted_results) / len(formatted_results) if formatted_results else 0.0
                bot_name = get_normalized_bot_name_from_env()
                await self._record_vector_memory_metrics(
                    bot_name=bot_name,
                    user_id=user_id,
                    operation="retrieve_memories",
                    query_time_ms=query_time_ms,
                    memory_count=len(formatted_results),
                    relevance_score=avg_relevance
                )
            except Exception as e:
                logger.debug(f"Could not record vector memory metrics: {e}")
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Failed to retrieve memories: {e}")
            return []
    
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
        🎯 FIDELITY-FIRST: Memory retrieval with character authenticity preservation
        
        This method implements the fidelity-first approach to memory retrieval:
        1. Start with full context preservation
        2. Use intelligent semantic ranking instead of arbitrary truncation
        3. Apply graduated filtering only when context limits are exceeded
        4. Preserve character-specific memory nuance throughout
        
        Args:
            user_id: User identifier for memory segmentation
            query: Search query for semantic similarity
            limit: Maximum number of memories to return
            full_fidelity: Start with complete context preservation
            intelligent_ranking: Use semantic similarity for prioritization
            graduated_filtering: Only filter if context exceeds limits
            preserve_character_nuance: Maintain personality-specific memories
            
        Returns:
            List of memories with fidelity-first optimization applied
        """
        import time
        start_time = time.time()
        
        try:
            # 🎯 CRITICAL FIX: Add temporal query detection for fidelity-first as well
            # This ensures consistent temporal handling across all memory retrieval methods
            is_temporal_query = await self.vector_store._detect_temporal_query_with_qdrant(query, user_id)
            
            if is_temporal_query:
                logger.info(f"🎯 TEMPORAL QUERY (FIDELITY-FIRST): '{query}' - Using chronological retrieval")
                temporal_results = await self.vector_store._handle_temporal_query_with_qdrant(query, user_id, limit)
                
                # Format temporal results with fidelity-first metadata
                formatted_results = []
                for r in temporal_results:
                    formatted_results.append({
                        "content": r.get("content", ""),
                        "score": r.get("score", 1.0),  # High score for temporal matches
                        "timestamp": r.get("timestamp", ""),
                        "metadata": r.get("metadata", {}),
                        "memory_type": r.get("memory_type", "conversation"),
                        "temporal": True,
                        "fidelity_first": True,
                        "search_type": "temporal_chronological_fidelity_first"
                    })
                
                logger.debug(f"🎯 TEMPORAL FIDELITY-FIRST: Retrieved {len(formatted_results)} memories in {(time.time() - start_time)*1000:.1f}ms")
                return formatted_results
            
            # Phase 1: Full Fidelity Assembly - Get complete context first
            if full_fidelity:
                # Retrieve more memories initially for intelligent filtering
                expanded_limit = min(limit * 3, 50)  # Get 3x more for intelligent selection
                logger.debug(f"🎯 FIDELITY-FIRST: Retrieving {expanded_limit} memories for intelligent filtering")
            else:
                expanded_limit = limit
            
            # Use existing optimized search with expanded scope
            try:
                from src.memory.qdrant_optimization import QdrantQueryOptimizer
                optimizer = QdrantQueryOptimizer(self.vector_store)
                
                raw_memories = await optimizer.optimized_search(
                    query=query,
                    user_id=user_id,
                    query_type="fidelity_first_search",
                    user_history={},
                    filters={}
                )
                
            except (ImportError, Exception):
                # Fallback to standard vector search
                raw_memories = await self.vector_store.search_memories(
                    user_id=user_id,
                    query=query,
                    limit=expanded_limit
                )
            
            if not raw_memories:
                return []
            
            # Phase 2: Intelligent Ranking - Character-aware prioritization
            if intelligent_ranking and preserve_character_nuance:
                ranked_memories = await self._apply_character_aware_ranking(
                    memories=raw_memories,
                    query=query,
                    user_id=user_id
                )
            else:
                ranked_memories = raw_memories
            
            # Phase 3: Graduated Filtering - Only compress if necessary
            if graduated_filtering and len(ranked_memories) > limit:
                filtered_memories = await self._apply_graduated_filtering(
                    memories=ranked_memories,
                    target_limit=limit,
                    preserve_character=preserve_character_nuance
                )
            else:
                filtered_memories = ranked_memories[:limit]
            
            # Format results with fidelity metrics
            formatted_results = []
            for i, memory in enumerate(filtered_memories):
                formatted_memory = {
                    "content": memory.get("content", ""),
                    "score": memory.get("score", 0.0),
                    "timestamp": memory.get("timestamp", ""),
                    "metadata": memory.get("metadata", {}),
                    "memory_type": memory.get("memory_type", "unknown"),
                    "fidelity_preserved": True,
                    "ranking_position": i + 1,
                    "search_type": "fidelity_first"
                }
                
                # Add character-specific metadata if available
                if preserve_character_nuance:
                    formatted_memory["character_relevance"] = memory.get("character_relevance", 0.0)
                    formatted_memory["personality_alignment"] = memory.get("personality_alignment", 0.0)
                
                formatted_results.append(formatted_memory)
            
            processing_time = (time.time() - start_time) * 1000
            logger.info(f"🎯 FIDELITY-FIRST: Retrieved {len(formatted_results)} memories "
                       f"(from {len(raw_memories)} candidates) in {processing_time:.1f}ms")
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Failed to retrieve fidelity-first memories: {e}")
            # Graceful fallback to standard retrieval
            return await self.retrieve_relevant_memories(user_id, query, limit)
    
    async def _apply_character_aware_ranking(
        self,
        memories: List[Dict[str, Any]],
        query: str,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """
        Apply character-aware ranking to preserve personality nuance.
        
        This method uses vector similarity to score memories based on:
        - Semantic relevance to current query
        - Character consistency and personality alignment
        - Conversation context and emotional continuity
        """
        try:
            # Get current bot's character profile for consistency scoring
            bot_name = get_normalized_bot_name_from_env()
            
            # Score each memory for character relevance
            scored_memories = []
            for memory in memories:
                base_score = memory.get("score", 0.0)
                
                # Character relevance scoring
                character_score = await self._calculate_character_relevance(
                    memory=memory,
                    bot_name=bot_name,
                    query=query
                )
                
                # Combine scores with character preservation weighting
                combined_score = (base_score * 0.7) + (character_score * 0.3)
                
                memory["character_relevance"] = character_score
                memory["personality_alignment"] = combined_score
                memory["score"] = combined_score
                
                scored_memories.append(memory)
            
            # Sort by combined score (semantic + character relevance)
            ranked_memories = sorted(scored_memories, key=lambda x: x.get("score", 0), reverse=True)
            
            return ranked_memories
            
        except Exception as e:
            logger.warning(f"Character-aware ranking failed: {e}, using original order")
            return memories
    
    async def _apply_graduated_filtering(
        self,
        memories: List[Dict[str, Any]],
        target_limit: int,
        preserve_character: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Apply graduated filtering to reduce memory count while preserving character nuance.
        
        Filtering strategy:
        1. Keep highest-scoring character-relevant memories
        2. Preserve recent conversation context
        3. Maintain emotional continuity
        4. Emergency fallback with core personality intact
        """
        if len(memories) <= target_limit:
            return memories
        
        try:
            # Memory tier prioritization
            recent_memories = []
            character_memories = []
            general_memories = []
            
            # Categorize memories by importance and character relevance
            for memory in memories:
                timestamp = memory.get("timestamp", "")
                character_relevance = memory.get("character_relevance", 0.0)
                
                # Recent memories (last 24 hours) - high priority
                if self._is_recent_memory(timestamp, hours=24):
                    recent_memories.append(memory)
                # Character-relevant memories - medium priority
                elif character_relevance > 0.5:
                    character_memories.append(memory)
                # General memories - lower priority
                else:
                    general_memories.append(memory)
            
            # Graduated selection with character preservation
            filtered_memories = []
            remaining_slots = target_limit
            
            # Tier 1: Always include recent memories (up to 50% of limit)
            recent_slots = min(len(recent_memories), remaining_slots // 2)
            filtered_memories.extend(recent_memories[:recent_slots])
            remaining_slots -= recent_slots
            
            # Tier 2: Character-relevant memories (remaining slots)
            if remaining_slots > 0:
                character_slots = min(len(character_memories), remaining_slots)
                filtered_memories.extend(character_memories[:character_slots])
                remaining_slots -= character_slots
            
            # Tier 3: General memories if slots remain
            if remaining_slots > 0:
                filtered_memories.extend(general_memories[:remaining_slots])
            
            logger.debug(f"🎯 GRADUATED FILTERING: Selected {len(filtered_memories)} memories "
                        f"(recent: {recent_slots}, character: {character_slots})")
            
            return filtered_memories
            
        except Exception as e:
            logger.warning(f"Graduated filtering failed: {e}, using simple truncation")
            return memories[:target_limit]
    
    async def _calculate_character_relevance(
        self,
        memory: Dict[str, Any],
        bot_name: str,
        query: str
    ) -> float:
        """Calculate character relevance score for a memory."""
        try:
            # Base character relevance from metadata
            metadata = memory.get("metadata", {})
            
            # Check if memory involves character-specific topics
            content = memory.get("content", "").lower()
            character_keywords = self._get_character_keywords(bot_name)
            
            # Keyword matching score
            keyword_score = sum(1 for keyword in character_keywords if keyword in content)
            keyword_score = min(keyword_score / len(character_keywords), 1.0) if character_keywords else 0.0
            
            # Memory type relevance
            memory_type = memory.get("memory_type", "")
            type_score = 1.0 if memory_type in ["conversation", "relationship"] else 0.5
            
            # Combine scores
            relevance_score = (keyword_score * 0.6) + (type_score * 0.4)
            
            return relevance_score
            
        except Exception as e:
            logger.debug(f"Character relevance calculation failed: {e}")
            return 0.5  # Neutral score
    
    def _get_character_keywords(self, bot_name: str) -> List[str]:
        """Get character-specific keywords for relevance scoring."""
        # Basic character-specific keywords (could be enhanced with CDL integration)
        character_keywords = {
            "elena": ["marine", "ocean", "biology", "research", "conservation", "sea"],
            "marcus": ["ai", "technology", "research", "artificial", "intelligence", "development"],
            "jake": ["adventure", "photography", "travel", "exploration", "wildlife", "nature"],
            "dream": ["dream", "endless", "realm", "nightmare", "mythology", "story"],
            "aethys": ["omnipotent", "cosmic", "universe", "reality", "existence", "divine"],
            "ryan": ["game", "development", "indie", "programming", "design", "creative"],
            "gabriel": ["british", "gentleman", "refined", "philosophical", "literature", "culture"],
            "sophia": ["marketing", "executive", "business", "strategy", "brand", "professional"]
        }
        
        return character_keywords.get(bot_name.lower(), [])
    
    def _is_recent_memory(self, timestamp: str, hours: int = 24) -> bool:
        """Check if memory is within recent time window."""
        try:
            if not timestamp:
                return False
            
            # Parse timestamp (handle various formats)
            memory_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            return memory_time > cutoff_time
            
        except Exception:
            return False  # Assume not recent if parsing fails
    
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
                memory_types=[MemoryType.CONVERSATION.value, MemoryType.FACT.value, MemoryType.PREFERENCE.value],  # These are strings now, which matches the protocol
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
                memory_types=["conversation"],  # Convert MemoryType.CONVERSATION to string
                limit=limit * 2  # Get more to filter properly
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
                            abs(r.get("timestamp", 0) - result.get("timestamp", 0)) < 86400):  # Within 24 hours - much more reasonable for conversation context
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
                id=str(uuid4()),  # Pure UUID for Qdrant compatibility
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
                memory_types=[MemoryType.FACT.value],
                limit=limit
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
                    id=str(uuid4()),  # Pure UUID for Qdrant compatibility
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
                memory_types=[MemoryType.PREFERENCE.value],
                limit=50
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
        """
        Get conversation history for the user in chronological order.
        
        🚨 CRITICAL FIX: Use scroll/filter instead of search to get ACTUAL recent conversations.
        search_memories() with empty query does vector search which returns semantically similar 
        (but potentially OLD) conversations, not chronologically recent ones.
        """
        try:
            # 🚨 FIX: Use direct Qdrant scroll with timestamp-based filtering
            # This gets the ACTUAL most recent conversations, not semantically similar ones
            from datetime import datetime, timedelta
            from qdrant_client import models
            
            # Get conversations from the last 24 hours for current conversation thread
            # Previous 1 hour was too restrictive and was cutting off bot responses
            time_window_hours = 24
            cutoff_timestamp = datetime.now() - timedelta(hours=time_window_hours)
            cutoff_unix = cutoff_timestamp.timestamp()
            
            logger.info(f"🕒 DEBUG: Retrieving conversations newer than {cutoff_timestamp} for user {user_id}")
            
            # Build filter for recent conversations
            must_conditions = [
                models.FieldCondition(
                    key="user_id",
                    match=models.MatchValue(value=user_id)
                ),
                models.FieldCondition(
                    key="memory_type",
                    match=models.MatchValue(value="conversation")
                ),
                models.FieldCondition(
                    key="timestamp_unix",
                    range=models.Range(gte=cutoff_unix)
                )
            ]
            
            # 🎯 COLLECTION ISOLATION: No bot_name filter needed - each collection is bot-specific
            # 🎯 REMOVED: bot_name filtering since collections are already bot-specific
            
            # Scroll through recent conversations (no vector search needed)
            scroll_result = self.vector_store.client.scroll(
                collection_name=self.vector_store.collection_name,
                scroll_filter=models.Filter(must=must_conditions),
                limit=limit * 2,  # Get extra in case some are filtered
                with_payload=True,
                with_vectors=False  # Don't need vectors for history retrieval
            )
            
            # Extract and format results
            results = []
            for point in scroll_result[0]:  # scroll returns (points, next_offset)
                payload = point.payload
                
                # 🚨 FIX: role is at top level of payload (from metadata spread), not nested in metadata dict
                role = payload.get("role", "unknown")
                source = payload.get("source", "unknown")
                content = payload.get("content", "")
                
                # Debug log for role detection
                logger.debug(f"🕒 ROLE DEBUG: Found message with role='{role}', source='{source}', content='{content[:50]}...'")
                
                results.append({
                    "content": content,
                    "timestamp": payload.get("timestamp", ""),
                    "role": role,
                    "metadata": payload.get("metadata", {})
                })
            
            # First sort by timestamp descending to get the most recent conversations
            recent_results = sorted(results, key=lambda x: x["timestamp"], reverse=True)[:limit]
            
            # Then reverse to chronological order for proper LLM conversation flow
            # This ensures user/assistant messages are properly interleaved in time order
            sorted_results = list(reversed(recent_results))
            
            print(f"🔥🔥🔥 MEMORY SYSTEM TEST PRINT: Retrieved {len(sorted_results)} conversations", flush=True)
            logger.info(f"🕒 CONVERSATION HISTORY: Retrieved {len(sorted_results)} most recent conversations in chronological order for user {user_id}")
            
            return sorted_results
            
        except Exception as e:
            logger.error(f"Failed to get conversation history: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
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
            # Pass memory_types directly as strings (protocol-compliant)
            results = await self.vector_store.search_memories(
                query=query,
                user_id=user_id,
                memory_types=memory_types,  # Already strings, no conversion needed
                limit=limit
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
                id=str(uuid4()),  # Pure UUID for Qdrant compatibility
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
                memory_types=["CONTEXT"],  # Fixed: Convert enum to string for protocol compliance
                limit=10
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

    def initialize_memoryboost_components(
        self,
        trend_analyzer=None,
        temporal_client=None
    ) -> None:
        """
        Initialize MemoryBoost components for enhanced memory optimization.
        
        Args:
            trend_analyzer: TrendWise InfluxDB analyzer instance
            temporal_client: InfluxDB client for metrics storage
        """
        try:
            # Set up logger if not already available
            if not hasattr(self, 'logger'):
                import logging
                self.logger = logging.getLogger(__name__)
                
            # Initialize Memory Effectiveness Analyzer
            from src.memory.memory_effectiveness import create_memory_effectiveness_analyzer
            self._effectiveness_analyzer = create_memory_effectiveness_analyzer(
                memory_manager=self,
                trend_analyzer=trend_analyzer,
                temporal_client=temporal_client
            )
            
            # Initialize Vector Relevance Optimizer
            from src.memory.relevance_optimizer import create_vector_relevance_optimizer
            self._relevance_optimizer = create_vector_relevance_optimizer(
                memory_manager=self,
                effectiveness_analyzer=self._effectiveness_analyzer
            )
            
            self.logger.info("✅ MemoryBoost components initialized successfully")
            
        except Exception as e:
            # Set up logger if not already available for error logging
            if not hasattr(self, 'logger'):
                import logging
                self.logger = logging.getLogger(__name__)
            self.logger.error("Failed to initialize MemoryBoost components: %s", str(e))
            self._effectiveness_analyzer = None
            self._relevance_optimizer = None

    def _get_bot_name(self) -> str:
        """Get bot name from environment for MemoryBoost operations."""
        try:
            from src.utils.helpers import get_normalized_bot_name_from_env
            return get_normalized_bot_name_from_env()
        except Exception:
            # Fallback to environment variable
            return os.getenv('DISCORD_BOT_NAME', 'unknown')

    async def analyze_memory_effectiveness(
        self,
        user_id: str,
        days_back: int = 14
    ) -> Dict[str, Any]:
        """
        Analyze memory effectiveness for a user using MemoryBoost analytics.
        
        Args:
            user_id: User identifier
            days_back: Days of history to analyze
            
        Returns:
            Dictionary with effectiveness analysis results
        """
        try:
            if not hasattr(self, '_effectiveness_analyzer') or not self._effectiveness_analyzer:
                return {'error': 'MemoryBoost effectiveness analyzer not initialized'}
            
            bot_name = self._get_bot_name()
            
            # Get effectiveness metrics
            effectiveness_metrics = await self._effectiveness_analyzer.analyze_memory_performance(
                user_id=user_id,
                bot_name=bot_name,
                days_back=days_back
            )
            
            # Get optimization recommendations
            recommendations = await self._effectiveness_analyzer.get_memory_optimization_recommendations(
                user_id=user_id,
                bot_name=bot_name
            )
            
            return {
                'effectiveness_metrics': {
                    pattern.value: {
                        'success_rate': metrics.success_rate,
                        'usage_count': metrics.usage_count,
                        'improvement_factor': metrics.improvement_factor,
                        'confidence_boost': metrics.confidence_boost
                    }
                    for pattern, metrics in effectiveness_metrics.items()
                },
                'recommendations': recommendations,
                'analysis_confidence': recommendations.get('confidence', 0.5),
                'last_updated': recommendations.get('analysis_timestamp')
            }
            
        except Exception as e:
            self.logger.error("Error analyzing memory effectiveness: %s", str(e))
            return {'error': str(e)}

    async def get_memory_optimization_stats(self) -> Dict[str, Any]:
        """
        Get MemoryBoost optimization statistics and performance metrics.
        
        Returns:
            Dictionary with optimization statistics
        """
        try:
            stats = {
                'memoryboost_enabled': hasattr(self, '_effectiveness_analyzer') and self._effectiveness_analyzer is not None,
                'components_initialized': {
                    'effectiveness_analyzer': hasattr(self, '_effectiveness_analyzer') and self._effectiveness_analyzer is not None,
                    'relevance_optimizer': hasattr(self, '_relevance_optimizer') and self._relevance_optimizer is not None
                }
            }
            
            # Get optimizer statistics if available
            if hasattr(self, '_relevance_optimizer') and self._relevance_optimizer:
                optimizer_stats = getattr(self._relevance_optimizer, '_optimization_stats', {})
                stats['optimization_performance'] = optimizer_stats
            
            return stats
            
        except Exception as e:
            self.logger.error("Error getting MemoryBoost stats: %s", str(e))
            return {'error': str(e)}


if __name__ == "__main__":
    asyncio.run(test_vector_memory_system())
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
            'model_name': 'BAAI/bge-small-en-v1.5'
        }
    }
    
    memory_manager = VectorMemoryManager(config)
    
    user_id = "test_user_123"
    
    async def retrieve_relevant_memories_with_memoryboost(
        self,
        user_id: str,
        query: str,
        limit: int = 25,
        conversation_context: str = None,
        apply_quality_scoring: bool = True,
        apply_optimizations: bool = True
    ) -> Dict[str, Any]:
        """
        🚀 SPRINT 2: MemoryBoost Enhanced Memory Retrieval
        
        Retrieves memories with intelligent quality scoring and optimization
        based on conversation outcome analysis. Integrates MemoryEffectivenessAnalyzer
        and VectorRelevanceOptimizer for adaptive learning.
        
        Args:
            user_id: User identifier for memory segmentation
            query: Search query for semantic similarity
            limit: Maximum number of memories to return
            conversation_context: Current conversation context for optimization
            apply_quality_scoring: Whether to apply quality scoring analysis
            apply_optimizations: Whether to apply vector optimizations
            
        Returns:
            Dictionary containing:
            - memories: Optimized memory list
            - optimization_metadata: Details about applied optimizations
            - performance_metrics: Analysis performance data
        """
        import time
        start_time = time.time()
        
        try:
            self.logger.info("🚀 MEMORYBOOST: Enhanced memory retrieval for user %s", user_id)
            
            # Step 1: Get base memory results using existing method
            base_memories = await self.retrieve_relevant_memories(
                user_id=user_id,
                query=query,
                limit=limit * 2  # Get more for intelligent filtering
            )
            
            result = {
                'memories': base_memories,
                'optimization_metadata': {
                    'quality_scoring_applied': False,
                    'optimizations_applied': False,
                    'optimizations_count': 0,
                    'performance_improvement': 0.0
                },
                'performance_metrics': {
                    'base_retrieval_time_ms': 0.0,
                    'quality_scoring_time_ms': 0.0,
                    'optimization_time_ms': 0.0,
                    'total_time_ms': 0.0
                }
            }
            
            base_time = time.time()
            result['performance_metrics']['base_retrieval_time_ms'] = (base_time - start_time) * 1000
            
            # Step 2: Apply quality scoring if enabled
            if apply_quality_scoring and hasattr(self, '_effectiveness_analyzer'):
                quality_start = time.time()
                
                try:
                    # Import and create relevance optimizer
                    from src.memory.relevance_optimizer import create_vector_relevance_optimizer
                    optimizer = create_vector_relevance_optimizer(
                        memory_manager=self,
                        effectiveness_analyzer=self._effectiveness_analyzer
                    )
                    
                    # Apply quality scoring
                    scored_memories = await optimizer.apply_quality_scoring(
                        memory_results=base_memories,
                        user_id=user_id,
                        bot_name=self._get_bot_name()
                    )
                    
                    result['memories'] = scored_memories
                    result['optimization_metadata']['quality_scoring_applied'] = True
                    
                    quality_time = time.time()
                    result['performance_metrics']['quality_scoring_time_ms'] = (quality_time - quality_start) * 1000
                    
                except Exception as e:
                    self.logger.warning("Quality scoring failed, using base memories: %s", str(e))
            
            # Step 3: Apply vector optimizations if enabled
            if apply_optimizations and hasattr(self, '_relevance_optimizer'):
                opt_start = time.time()
                
                try:
                    # Apply full optimization suite
                    optimization_result = await self._relevance_optimizer.optimize_memory_retrieval(
                        user_id=user_id,
                        bot_name=self._get_bot_name(),
                        query=query,
                        original_results=result['memories'],
                        conversation_context=conversation_context
                    )
                    
                    result['memories'] = optimization_result.optimized_results[:limit]
                    result['optimization_metadata'].update({
                        'optimizations_applied': True,
                        'optimizations_count': optimization_result.optimization_count,
                        'performance_improvement': optimization_result.performance_improvement,
                        'optimizations_details': [
                            {
                                'memory_id': opt.memory_id,
                                'boost_factor': opt.boost_factor,
                                'reason': opt.reason,
                                'pattern': opt.pattern_match.value
                            }
                            for opt in optimization_result.optimizations_applied[:5]  # Top 5 for metadata
                        ]
                    })
                    
                    opt_time = time.time()
                    result['performance_metrics']['optimization_time_ms'] = (opt_time - opt_start) * 1000
                    
                except Exception as e:
                    self.logger.warning("Vector optimization failed, using scored memories: %s", str(e))
            
            # Apply final limit
            result['memories'] = result['memories'][:limit]
            
            total_time = time.time()
            result['performance_metrics']['total_time_ms'] = (total_time - start_time) * 1000
            
            self.logger.info("✅ MEMORYBOOST: Retrieved %d memories with %d optimizations in %.1fms", 
                           len(result['memories']), 
                           result['optimization_metadata']['optimizations_count'],
                           result['performance_metrics']['total_time_ms'])
            
            return result
            
        except Exception as e:
            self.logger.error("Error in MemoryBoost enhanced retrieval: %s", str(e))
            # Fallback to standard retrieval
            base_memories = await self.retrieve_relevant_memories(user_id, query, limit)
            return {
                'memories': base_memories,
                'optimization_metadata': {
                    'quality_scoring_applied': False,
                    'optimizations_applied': False,
                    'optimizations_count': 0,
                    'performance_improvement': 0.0,
                    'error': str(e)
                },
                'performance_metrics': {
                    'total_time_ms': (time.time() - start_time) * 1000
                }
            }

    async def _record_vector_memory_metrics(self, 
                                           bot_name: str,
                                           user_id: str, 
                                           operation: str,
                                           query_time_ms: int,
                                           memory_count: int,
                                           relevance_score: float = 0.0,
                                           vector_dimension: int = 384):
        """Record vector memory performance metrics to InfluxDB"""
        if not self.temporal_client:
            return
            
        try:
            await self.temporal_client.record_vector_memory_performance(
                bot_name=bot_name,
                user_id=user_id,
                operation_type=operation,
                query_time_ms=query_time_ms,
                memory_count=memory_count,
                relevance_score=relevance_score,
                vector_dimension=vector_dimension
            )
            logger.debug(f"📊 TEMPORAL: Recorded vector memory metrics for {bot_name}/{user_id}")
        except Exception as e:
            logger.error(f"Failed to record vector memory metrics: {e}")
            
