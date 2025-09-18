"""
Semantic Memory Clustering System
================================

Advanced memory clustering system that creates semantic clusters of related memories
for improved contextual understanding and retrieval.

Phase 3: Multi-Dimensional Memory Networks
"""

import asyncio
import logging
import os
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any

import numpy as np
from sklearn.cluster import DBSCAN, AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_similarity

# Historical: ExternalEmbeddingManager removed Sept 2025. All embedding is now local.

logger = logging.getLogger(__name__)


class ClusterType(Enum):
    TOPIC_BASED = "topic_based"
    EMOTIONAL_CONTEXT = "emotional_context"
    TEMPORAL_PERIOD = "temporal_period"
    INTERACTION_PATTERN = "interaction_pattern"
    COMPLEXITY_LEVEL = "complexity_level"


@dataclass
class MemoryCluster:
    """Represents a cluster of related memories"""

    cluster_id: str
    cluster_type: ClusterType
    memories: list[str]  # memory IDs
    centroid_embedding: list[float] | None
    topic_keywords: list[str]
    emotional_signature: dict[str, float]
    temporal_span: dict[str, str]  # start_date, end_date
    importance_score: float
    cluster_summary: str
    last_updated: datetime


@dataclass
class ClusteringMetrics:
    """Metrics for cluster quality assessment"""

    silhouette_score: float
    intra_cluster_similarity: float
    inter_cluster_diversity: float
    optimal_cluster_count: int
    cluster_stability: float


class SemanticMemoryClusterer:
    """Advanced semantic memory clustering system"""

    def __init__(self, embedding_manager=None):
        """Initialize semantic memory clusterer with local embedding support"""
        # Use provided embedding manager or create a local one
        if embedding_manager:
            self.embedding_manager = embedding_manager
        else:
            try:
                from src.utils.embedding_manager import LocalEmbeddingManager
                self.embedding_manager = LocalEmbeddingManager()
                # Note: initialize() should be called separately in async context
                logger.info("Created LocalEmbeddingManager (initialization needed)")
            except ImportError:
                logger.warning("LocalEmbeddingManager not available - clustering disabled")
                self.embedding_manager = None

        # Clustering configuration
        self.clustering_algorithm = "hierarchical"
        self.similarity_threshold = 0.8
        self.max_cluster_size = 50
        self.min_cluster_size = 2
        self.clusters_cache = {}
        self.embeddings_cache = {}

        # Performance limits to prevent blocking
        self.max_memories_per_batch = int(os.getenv("SEMANTIC_CLUSTERING_MAX_MEMORIES", "20"))
        self.embedding_timeout = int(os.getenv("SEMANTIC_CLUSTERING_TIMEOUT", "30"))  # seconds

        # Clustering parameters
        self.clustering_params = {
            "dbscan": {"eps": 0.3, "min_samples": 2, "metric": "cosine"},
            "hierarchical": {"n_clusters": None, "distance_threshold": 0.4, "linkage": "ward"},
        }

        if self.embedding_manager:
            logger.info("Semantic Memory Clusterer initialized with local embedding support")
        else:
            logger.info("Semantic Memory Clusterer initialized with clustering disabled")

    @property
    def embedding_model(self):
        """Compatibility property - no longer used with external embeddings"""
        logger.warning("embedding_model property deprecated - external embedding removed Sept 2025")
        return None

    async def create_memory_clusters(self, user_id: str, memory_manager) -> dict[str, Any]:
        """
        Create comprehensive semantic clusters of user memories

        Args:
            user_id: User identifier
            memory_manager: Memory manager instance for data access

        Returns:
            Dictionary containing different types of memory clusters
        """
        logger.info(f"Creating memory clusters for user {user_id}")

        try:
            # Fetch all user memories
            memories = await self._fetch_user_memories(user_id, memory_manager)

            if len(memories) < self.min_cluster_size:
                logger.warning(f"Insufficient memories for clustering: {len(memories)}")
                return self._create_empty_cluster_result()

            # Generate embeddings for all memories
            memory_embeddings = await self._generate_memory_embeddings(memories)

            # Create different types of clusters
            cluster_results = {
                "topic_clusters": await self._cluster_by_topics(
                    user_id, memories, memory_embeddings
                ),
                "emotional_clusters": await self._cluster_by_emotions(user_id, memories),
                "temporal_clusters": await self._cluster_by_time_periods(user_id, memories),
                "interaction_clusters": await self._cluster_by_interaction_patterns(
                    user_id, memories
                ),
                "complexity_clusters": await self._cluster_by_complexity(user_id, memories),
                "clustering_metadata": {
                    "total_memories": len(memories),
                    "clustering_timestamp": datetime.now(UTC),
                    "algorithm_used": self.clustering_algorithm,
                    "similarity_threshold": self.similarity_threshold,
                },
            }

            # Cache results
            self.clusters_cache[user_id] = cluster_results

            logger.info(f"Memory clustering completed for user {user_id}")
            return cluster_results

        except Exception as e:
            logger.error(f"Error creating memory clusters for user {user_id}: {e}")
            return self._create_empty_cluster_result()

    async def _fetch_user_memories(self, user_id: str, memory_manager) -> list[dict]:
        """Fetch all memories for a user"""
        try:
            # Get memories from the memory manager
            memories = await memory_manager.get_memories_by_user(user_id)

            # Filter out invalid memories and format
            valid_memories = []
            for memory in memories:
                if self._is_valid_memory(memory):
                    formatted_memory = {
                        "memory_id": memory.get("id", ""),
                        "content": memory.get("content", ""),
                        "topic": memory.get("topic", ""),
                        "emotional_context": memory.get("emotional_context", {}),
                        "timestamp": memory.get("timestamp", datetime.now(UTC)),
                        "importance_score": memory.get("importance_score", 0.5),
                        "metadata": memory.get("metadata", {}),
                    }
                    valid_memories.append(formatted_memory)

            logger.debug(f"Fetched {len(valid_memories)} valid memories for user {user_id}")
            return valid_memories

        except Exception as e:
            logger.error(f"Error fetching memories for user {user_id}: {e}")
            return []

    def _is_valid_memory(self, memory: dict) -> bool:
        """Check if memory is valid for clustering"""
        content = memory.get("content", "")
        memory_id = memory.get("id", "")
        return bool(content) and len(content.strip()) > 10 and bool(memory_id)

    async def _generate_memory_embeddings(self, memories: list[dict]) -> dict[str, np.ndarray]:
        """Generate embeddings for memory contents using external API"""
        total_memories = len(memories)
        logger.debug(f"Generating embeddings for {total_memories} memories using external API")

        # Limit the number of memories to prevent excessive processing
        if total_memories > self.max_memories_per_batch:
            logger.warning(
                f"Limiting memory processing from {total_memories} to {self.max_memories_per_batch} for performance"
            )
            # Take the most recent memories
            memories = memories[-self.max_memories_per_batch :]

        embeddings = {}
        texts = []
        memory_ids = []

        for memory in memories:
            # Check embeddings cache first
            memory_id = memory["memory_id"]
            if memory_id in self.embeddings_cache:
                embeddings[memory_id] = self.embeddings_cache[memory_id]
                continue

            # Combine content and topic for richer embedding
            text = f"{memory['content']} {memory.get('topic', '')}"
            texts.append(text)
            memory_ids.append(memory_id)

        if not texts:
            logger.debug("All embeddings found in cache")
            return embeddings

        try:
            logger.debug(f"Computing embeddings for {len(texts)} new memories using local embedding manager")

            # Check if embedding manager is available
            if not self.embedding_manager:
                logger.debug("No embedding manager available - skipping embedding generation")
                return {}

            # Ensure embedding manager is initialized
            if hasattr(self.embedding_manager, '_is_initialized') and not self.embedding_manager._is_initialized:
                logger.debug("Initializing embedding manager...")
                await self.embedding_manager.initialize()

            # Generate embeddings using local embedding manager
            batch_embeddings = await self.embedding_manager.get_embeddings(texts)
            
            if not batch_embeddings:
                logger.warning("Failed to generate embeddings - empty result from embedding manager")
                return {}

            # Store results and cache them
            for i, memory_id in enumerate(memory_ids):
                if i < len(batch_embeddings):
                    embedding = np.array(batch_embeddings[i])  # Convert to numpy array
                    embeddings[memory_id] = embedding
                    self.embeddings_cache[memory_id] = embedding

            logger.debug(
                f"Generated embeddings for {len(batch_embeddings)} memories via local embedding manager, total {len(embeddings)} available"
            )
            return embeddings

        except TimeoutError:
            logger.error(f"Embedding generation timed out after {self.embedding_timeout} seconds")
            return {}
        except Exception as e:
            logger.error(f"Error generating embeddings via external API: {e}")
            return {}

    async def _cluster_by_topics(
        self, user_id: str, memories: list[dict], embeddings: dict[str, np.ndarray]
    ) -> list[MemoryCluster]:
        """Group memories by semantic topic similarity"""
        logger.debug(f"Clustering {len(memories)} memories by topics")

        if len(memories) < self.min_cluster_size:
            return []

        # Check if embeddings are available
        if not embeddings:
            logger.debug("No embeddings available for topic clustering - skipping")
            return []

        try:
            # Prepare embedding matrix
            memory_ids = list(embeddings.keys())
            embedding_matrix = np.array([embeddings[mid] for mid in memory_ids])

            # Validate embedding matrix
            if embedding_matrix.size == 0:
                logger.debug("Empty embedding matrix - skipping topic clustering")
                return []

            # Ensure we have a 2D array
            if embedding_matrix.ndim == 1:
                logger.debug("1D embedding matrix detected - reshaping or skipping")
                if len(memory_ids) == 1:
                    # Single memory, no clustering needed
                    return []
                else:
                    # Unexpected case - log and skip
                    logger.warning(f"Unexpected 1D array for {len(memory_ids)} memories")
                    return []

            # Perform clustering
            if self.clustering_algorithm == "dbscan":
                clusterer = DBSCAN(**self.clustering_params["dbscan"])
                cluster_labels = clusterer.fit_predict(embedding_matrix)
            else:  # hierarchical
                clusterer = AgglomerativeClustering(**self.clustering_params["hierarchical"])
                cluster_labels = clusterer.fit_predict(embedding_matrix)

            # Group memories by cluster
            clusters = defaultdict(list)
            for i, label in enumerate(cluster_labels):
                if label != -1:  # Ignore noise points in DBSCAN
                    clusters[label].append(memory_ids[i])

            # Create cluster objects
            topic_clusters = []
            for cluster_id, memory_ids_in_cluster in clusters.items():
                if len(memory_ids_in_cluster) >= self.min_cluster_size:
                    cluster = await self._create_topic_cluster(
                        f"topic_{user_id}_{cluster_id}", memory_ids_in_cluster, memories, embeddings
                    )
                    topic_clusters.append(cluster)

            logger.debug(f"Created {len(topic_clusters)} topic clusters")
            return topic_clusters

        except Exception as e:
            logger.error(f"Error in topic clustering: {e}")
            return []

    async def _create_topic_cluster(
        self,
        cluster_id: str,
        memory_ids: list[str],
        memories: list[dict],
        embeddings: dict[str, np.ndarray],
    ) -> MemoryCluster:
        """Create a topic-based memory cluster"""

        # Get memories in this cluster
        cluster_memories = [m for m in memories if m["memory_id"] in memory_ids]

        # Calculate centroid embedding
        cluster_embeddings = [embeddings[mid] for mid in memory_ids]
        centroid_embedding = np.mean(cluster_embeddings, axis=0).tolist()

        # Extract topic keywords
        topic_keywords = self._extract_cluster_keywords(cluster_memories)

        # Calculate emotional signature
        emotional_signature = self._calculate_emotional_signature(cluster_memories)

        # Determine temporal span
        temporal_span = self._calculate_temporal_span(cluster_memories)

        # Calculate importance score
        importance_score = self._calculate_cluster_importance(cluster_memories)

        # Generate cluster summary
        cluster_summary = self._generate_cluster_summary(cluster_memories, topic_keywords)

        return MemoryCluster(
            cluster_id=cluster_id,
            cluster_type=ClusterType.TOPIC_BASED,
            memories=memory_ids,
            centroid_embedding=centroid_embedding,
            topic_keywords=topic_keywords,
            emotional_signature=emotional_signature,
            temporal_span=temporal_span,
            importance_score=importance_score,
            cluster_summary=cluster_summary,
            last_updated=datetime.now(UTC),
        )

    async def _cluster_by_emotions(self, user_id: str, memories: list[dict]) -> list[MemoryCluster]:
        """Group memories by emotional context similarity"""
        logger.debug("Clustering memories by emotional context")

        # Group memories by emotional categories
        emotional_groups = defaultdict(list)

        for memory in memories:
            emotional_context = memory.get("emotional_context", {})

            # Handle case where emotional_context might be a string (JSON)
            if isinstance(emotional_context, str):
                try:
                    import json

                    emotional_context = json.loads(emotional_context)
                except (json.JSONDecodeError, TypeError):
                    # If parsing fails, create a default dict
                    emotional_context = {"primary_emotion": "neutral"}
            elif not isinstance(emotional_context, dict):
                # If it's neither string nor dict, create default
                emotional_context = {"primary_emotion": "neutral"}

            primary_emotion = emotional_context.get("primary_emotion", "neutral")

            # Could also cluster by emotional intensity, valence, etc.
            emotional_groups[primary_emotion].append(memory["memory_id"])

        # Create clusters for each emotional group
        emotional_clusters = []
        for emotion, memory_ids in emotional_groups.items():
            if len(memory_ids) >= self.min_cluster_size:
                cluster = await self._create_emotional_cluster(
                    f"emotion_{user_id}_{emotion}", memory_ids, memories, emotion
                )
                emotional_clusters.append(cluster)

        logger.debug(f"Created {len(emotional_clusters)} emotional clusters")
        return emotional_clusters

    async def _create_emotional_cluster(
        self, cluster_id: str, memory_ids: list[str], memories: list[dict], primary_emotion: str
    ) -> MemoryCluster:
        """Create an emotion-based memory cluster"""

        cluster_memories = [m for m in memories if m["memory_id"] in memory_ids]

        # Topic keywords from emotional memories
        topic_keywords = self._extract_cluster_keywords(cluster_memories)

        # Emotional signature (should be dominated by primary emotion)
        emotional_signature = {primary_emotion: 1.0}

        # Temporal span
        temporal_span = self._calculate_temporal_span(cluster_memories)

        # Importance score
        importance_score = self._calculate_cluster_importance(cluster_memories)

        # Cluster summary
        cluster_summary = (
            f"Memories with {primary_emotion} emotional context: {', '.join(topic_keywords[:5])}"
        )

        return MemoryCluster(
            cluster_id=cluster_id,
            cluster_type=ClusterType.EMOTIONAL_CONTEXT,
            memories=memory_ids,
            centroid_embedding=None,  # Could add emotion-based embeddings
            topic_keywords=topic_keywords,
            emotional_signature=emotional_signature,
            temporal_span=temporal_span,
            importance_score=importance_score,
            cluster_summary=cluster_summary,
            last_updated=datetime.now(UTC),
        )

    async def _cluster_by_time_periods(
        self, user_id: str, memories: list[dict]
    ) -> list[MemoryCluster]:
        """Group memories by temporal periods"""
        logger.debug("Clustering memories by time periods")

        # Convert timestamps to datetime objects for proper sorting
        for memory in memories:
            timestamp = memory.get("timestamp", datetime.now(UTC))
            if isinstance(timestamp, str):
                try:
                    memory["timestamp"] = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    memory["timestamp"] = datetime.now(UTC)
            elif not isinstance(timestamp, datetime):
                memory["timestamp"] = datetime.now(UTC)

        # Sort memories by timestamp
        sorted_memories = sorted(memories, key=lambda m: m["timestamp"])

        # Group by time periods (could be days, weeks, months)
        temporal_groups = self._group_by_temporal_periods(sorted_memories)

        # Create temporal clusters
        temporal_clusters = []
        for period, memory_list in temporal_groups.items():
            if len(memory_list) >= self.min_cluster_size:
                memory_ids = [m["memory_id"] for m in memory_list]
                cluster = await self._create_temporal_cluster(
                    f"temporal_{user_id}_{period}", memory_ids, memory_list, period
                )
                temporal_clusters.append(cluster)

        logger.debug(f"Created {len(temporal_clusters)} temporal clusters")
        return temporal_clusters

    def _group_by_temporal_periods(self, sorted_memories: list[dict]) -> dict[str, list[dict]]:
        """Group memories by temporal periods"""
        groups = defaultdict(list)

        for memory in sorted_memories:
            timestamp = memory["timestamp"]
            # At this point timestamp should already be a datetime object from the calling method
            if isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    timestamp = datetime.now(UTC)
            elif not isinstance(timestamp, datetime):
                timestamp = datetime.now(UTC)

            # Group by week (could be adjusted to different periods)
            year_week = f"{timestamp.year}_W{timestamp.isocalendar()[1]}"
            groups[year_week].append(memory)

        return dict(groups)

    async def _create_temporal_cluster(
        self, cluster_id: str, memory_ids: list[str], memories: list[dict], period: str
    ) -> MemoryCluster:
        """Create a temporal-based memory cluster"""

        # Topic keywords from temporal memories
        topic_keywords = self._extract_cluster_keywords(memories)

        # Emotional signature
        emotional_signature = self._calculate_emotional_signature(memories)

        # Temporal span (should be the period itself)
        temporal_span = self._calculate_temporal_span(memories)

        # Importance score
        importance_score = self._calculate_cluster_importance(memories)

        # Cluster summary
        cluster_summary = f"Memories from {period}: {', '.join(topic_keywords[:5])}"

        return MemoryCluster(
            cluster_id=cluster_id,
            cluster_type=ClusterType.TEMPORAL_PERIOD,
            memories=memory_ids,
            centroid_embedding=None,
            topic_keywords=topic_keywords,
            emotional_signature=emotional_signature,
            temporal_span=temporal_span,
            importance_score=importance_score,
            cluster_summary=cluster_summary,
            last_updated=datetime.now(UTC),
        )

    async def _cluster_by_interaction_patterns(
        self, user_id: str, memories: list[dict]
    ) -> list[MemoryCluster]:
        """Group memories by interaction patterns"""
        logger.debug("Clustering memories by interaction patterns")

        # This is a placeholder for more sophisticated interaction pattern analysis
        # Could analyze conversation length, response times, question types, etc.

        pattern_groups = defaultdict(list)

        for memory in memories:
            # Simple pattern classification based on content length and complexity
            content_length = len(memory["content"])

            if content_length < 50:
                pattern = "brief_interaction"
            elif content_length < 200:
                pattern = "moderate_interaction"
            else:
                pattern = "detailed_interaction"

            pattern_groups[pattern].append(memory["memory_id"])

        # Create interaction pattern clusters
        interaction_clusters = []
        for pattern, memory_ids in pattern_groups.items():
            if len(memory_ids) >= self.min_cluster_size:
                cluster_memories = [m for m in memories if m["memory_id"] in memory_ids]
                cluster = await self._create_interaction_cluster(
                    f"interaction_{user_id}_{pattern}", memory_ids, cluster_memories, pattern
                )
                interaction_clusters.append(cluster)

        logger.debug(f"Created {len(interaction_clusters)} interaction pattern clusters")
        return interaction_clusters

    async def _create_interaction_cluster(
        self, cluster_id: str, memory_ids: list[str], memories: list[dict], pattern: str
    ) -> MemoryCluster:
        """Create an interaction pattern-based memory cluster"""

        # Topic keywords
        topic_keywords = self._extract_cluster_keywords(memories)

        # Emotional signature
        emotional_signature = self._calculate_emotional_signature(memories)

        # Temporal span
        temporal_span = self._calculate_temporal_span(memories)

        # Importance score
        importance_score = self._calculate_cluster_importance(memories)

        # Cluster summary
        cluster_summary = (
            f"{pattern.replace('_', ' ').title()} memories: {', '.join(topic_keywords[:5])}"
        )

        return MemoryCluster(
            cluster_id=cluster_id,
            cluster_type=ClusterType.INTERACTION_PATTERN,
            memories=memory_ids,
            centroid_embedding=None,
            topic_keywords=topic_keywords,
            emotional_signature=emotional_signature,
            temporal_span=temporal_span,
            importance_score=importance_score,
            cluster_summary=cluster_summary,
            last_updated=datetime.now(UTC),
        )

    async def _cluster_by_complexity(
        self, user_id: str, memories: list[dict]
    ) -> list[MemoryCluster]:
        """Group memories by complexity levels"""
        logger.debug("Clustering memories by complexity")

        complexity_groups = defaultdict(list)

        for memory in memories:
            complexity_score = self._calculate_complexity_score(memory)

            if complexity_score < 0.3:
                complexity_level = "simple"
            elif complexity_score < 0.7:
                complexity_level = "moderate"
            else:
                complexity_level = "complex"

            complexity_groups[complexity_level].append(memory["memory_id"])

        # Create complexity clusters
        complexity_clusters = []
        for level, memory_ids in complexity_groups.items():
            if len(memory_ids) >= self.min_cluster_size:
                cluster_memories = [m for m in memories if m["memory_id"] in memory_ids]
                cluster = await self._create_complexity_cluster(
                    f"complexity_{user_id}_{level}", memory_ids, cluster_memories, level
                )
                complexity_clusters.append(cluster)

        logger.debug(f"Created {len(complexity_clusters)} complexity clusters")
        return complexity_clusters

    def _calculate_complexity_score(self, memory: dict) -> float:
        """Calculate complexity score for a memory"""
        content = memory["content"]

        # Simple complexity metrics
        word_count = len(content.split())
        sentence_count = len([s for s in content.split(".") if s.strip()])
        avg_word_length = np.mean([len(word) for word in content.split()])

        # Normalize and combine metrics
        word_score = min(word_count / 100, 1.0)  # Normalized to 0-1
        sentence_score = min(sentence_count / 10, 1.0)
        length_score = min(float(avg_word_length) / 10, 1.0)

        return (word_score + sentence_score + length_score) / 3

    async def _create_complexity_cluster(
        self, cluster_id: str, memory_ids: list[str], memories: list[dict], complexity_level: str
    ) -> MemoryCluster:
        """Create a complexity-based memory cluster"""

        # Topic keywords
        topic_keywords = self._extract_cluster_keywords(memories)

        # Emotional signature
        emotional_signature = self._calculate_emotional_signature(memories)

        # Temporal span
        temporal_span = self._calculate_temporal_span(memories)

        # Importance score
        importance_score = self._calculate_cluster_importance(memories)

        # Cluster summary
        cluster_summary = (
            f"{complexity_level.title()} complexity memories: {', '.join(topic_keywords[:5])}"
        )

        return MemoryCluster(
            cluster_id=cluster_id,
            cluster_type=ClusterType.COMPLEXITY_LEVEL,
            memories=memory_ids,
            centroid_embedding=None,
            topic_keywords=topic_keywords,
            emotional_signature=emotional_signature,
            temporal_span=temporal_span,
            importance_score=importance_score,
            cluster_summary=cluster_summary,
            last_updated=datetime.now(UTC),
        )

    def _extract_cluster_keywords(self, memories: list[dict]) -> list[str]:
        """Extract topic keywords from cluster memories"""
        # Combine all topics and content
        all_text = " ".join(
            [f"{memory.get('topic', '')} {memory.get('content', '')}" for memory in memories]
        )

        # Simple keyword extraction (could be enhanced with NLP)
        words = all_text.lower().split()
        word_freq = Counter(words)

        # Filter out common words and get top keywords
        stopwords = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "can",
            "cannot",
            "i",
            "you",
            "he",
            "she",
            "it",
            "we",
            "they",
            "this",
            "that",
            "these",
            "those",
        }

        keywords = [
            word
            for word, freq in word_freq.most_common(20)
            if word not in stopwords and len(word) > 2
        ]

        return keywords[:10]  # Return top 10 keywords

    def _calculate_emotional_signature(self, memories: list[dict]) -> dict[str, float]:
        """Calculate emotional signature for cluster"""
        emotion_counts = Counter()

        for memory in memories:
            emotional_context = memory.get("emotional_context", {})

            # Handle case where emotional_context might be a string (JSON)
            if isinstance(emotional_context, str):
                try:
                    import json

                    emotional_context = json.loads(emotional_context)
                except (json.JSONDecodeError, TypeError):
                    # If parsing fails, create a default dict
                    emotional_context = {"primary_emotion": "neutral"}
            elif not isinstance(emotional_context, dict):
                # If it's neither string nor dict, create default
                emotional_context = {"primary_emotion": "neutral"}

            primary_emotion = emotional_context.get("primary_emotion", "neutral")
            emotion_counts[primary_emotion] += 1

        # Normalize to create signature
        total = sum(emotion_counts.values())
        if total == 0:
            return {"neutral": 1.0}

        return {emotion: count / total for emotion, count in emotion_counts.items()}

    def _calculate_temporal_span(self, memories: list[dict]) -> dict[str, str]:
        """Calculate temporal span of cluster"""
        timestamps = []

        for memory in memories:
            timestamp = memory["timestamp"]
            if isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    timestamp = datetime.now(UTC)
            elif not isinstance(timestamp, datetime):
                timestamp = datetime.now(UTC)
            timestamps.append(timestamp)

        if not timestamps:
            now = datetime.now(UTC)
            return {"start_date": now.isoformat(), "end_date": now.isoformat()}

        return {"start_date": min(timestamps).isoformat(), "end_date": max(timestamps).isoformat()}

    def _calculate_cluster_importance(self, memories: list[dict]) -> float:
        """Calculate importance score for cluster"""
        if not memories:
            return 0.0

        # Average importance of memories in cluster
        importance_scores = [memory.get("importance_score", 0.5) for memory in memories]
        base_importance = np.mean(importance_scores)

        # Boost based on cluster size (but with diminishing returns)
        size_boost = min(len(memories) / 10, 1.0) * 0.2

        return min(float(base_importance + size_boost), 1.0)

    def _generate_cluster_summary(self, memories: list[dict], keywords: list[str]) -> str:
        """Generate human-readable cluster summary"""
        memory_count = len(memories)
        top_keywords = ", ".join(keywords[:5])

        return f"Cluster of {memory_count} memories related to: {top_keywords}"

    async def find_related_memories(
        self, memory_id: str, user_id: str, similarity_threshold: float = 0.7, memory_manager=None
    ) -> list[dict]:
        """
        Find memories related to a specific memory

        Args:
            memory_id: Target memory ID
            user_id: User identifier
            similarity_threshold: Minimum similarity score
            memory_manager: Memory manager instance

        Returns:
            List of related memory dictionaries with similarity scores
        """
        logger.debug(f"Finding memories related to {memory_id}")

        try:
            # Get target memory
            if memory_manager is None:
                logger.error("Memory manager is required")
                return []

            target_memory = await memory_manager.get_memory_by_id(memory_id)
            if not target_memory:
                logger.warning(f"Memory {memory_id} not found")
                return []

            # Get all user memories
            all_memories = await self._fetch_user_memories(user_id, memory_manager)

            # Generate embeddings
            memory_embeddings = await self._generate_memory_embeddings(all_memories)

            if memory_id not in memory_embeddings:
                logger.warning(f"No embedding found for memory {memory_id}")
                return []

            target_embedding = memory_embeddings[memory_id]
            related_memories = []

            # Calculate similarities
            for memory in all_memories:
                if memory["memory_id"] == memory_id:
                    continue

                if memory["memory_id"] in memory_embeddings:
                    other_embedding = memory_embeddings[memory["memory_id"]]
                    similarity = cosine_similarity(
                        target_embedding.reshape(1, -1), other_embedding.reshape(1, -1)
                    )[0][0]

                    if similarity >= similarity_threshold:
                        related_memories.append(
                            {
                                "memory": memory,
                                "similarity_score": float(similarity),
                                "relation_type": self._determine_relation_type(similarity),
                            }
                        )

            # Sort by similarity
            related_memories.sort(key=lambda x: x["similarity_score"], reverse=True)

            logger.debug(f"Found {len(related_memories)} related memories")
            return related_memories

        except Exception as e:
            logger.error(f"Error finding related memories: {e}")
            return []

    def _determine_relation_type(self, similarity: float) -> str:
        """Determine type of relation based on similarity score"""
        if similarity >= 0.9:
            return "highly_related"
        elif similarity >= 0.8:
            return "strongly_related"
        elif similarity >= 0.7:
            return "moderately_related"
        else:
            return "weakly_related"

    async def update_cluster_relationships(self, user_id: str, memory_manager=None):
        """Update cluster relationships as new memories are added"""
        logger.info(f"Updating cluster relationships for user {user_id}")

        try:
            # Regenerate clusters with updated memory set
            updated_clusters = await self.create_memory_clusters(user_id, memory_manager)

            # Update cache
            self.clusters_cache[user_id] = updated_clusters

            logger.info(f"Cluster relationships updated for user {user_id}")

        except Exception as e:
            logger.error(f"Error updating cluster relationships: {e}")

    def _create_empty_cluster_result(self) -> dict[str, Any]:
        """Create empty cluster result structure"""
        return {
            "topic_clusters": [],
            "emotional_clusters": [],
            "temporal_clusters": [],
            "interaction_clusters": [],
            "complexity_clusters": [],
            "clustering_metadata": {
                "total_memories": 0,
                "clustering_timestamp": datetime.now(UTC),
                "algorithm_used": self.clustering_algorithm,
                "similarity_threshold": self.similarity_threshold,
            },
        }

    async def get_cluster_by_id(self, user_id: str, cluster_id: str) -> MemoryCluster | None:
        """Get specific cluster by ID"""
        if user_id not in self.clusters_cache:
            return None

        clusters = self.clusters_cache[user_id]
        for cluster_type, cluster_list in clusters.items():
            if cluster_type != "clustering_metadata":
                for cluster in cluster_list:
                    if cluster.cluster_id == cluster_id:
                        return cluster

        return None

    async def get_clusters_by_type(
        self, user_id: str, cluster_type: ClusterType
    ) -> list[MemoryCluster]:
        """Get all clusters of specific type for user"""
        if user_id not in self.clusters_cache:
            return []

        clusters = self.clusters_cache[user_id]
        type_mapping = {
            ClusterType.TOPIC_BASED: "topic_clusters",
            ClusterType.EMOTIONAL_CONTEXT: "emotional_clusters",
            ClusterType.TEMPORAL_PERIOD: "temporal_clusters",
            ClusterType.INTERACTION_PATTERN: "interaction_clusters",
            ClusterType.COMPLEXITY_LEVEL: "complexity_clusters",
        }

        cluster_key = type_mapping.get(cluster_type, "topic_clusters")
        return clusters.get(cluster_key, [])

    def get_clustering_statistics(self, user_id: str) -> dict[str, Any]:
        """Get clustering statistics for user"""
        if user_id not in self.clusters_cache:
            return {}

        clusters = self.clusters_cache[user_id]
        stats = {
            "total_clusters": sum(
                len(cluster_list)
                for key, cluster_list in clusters.items()
                if key != "clustering_metadata"
            ),
            "clusters_by_type": {
                cluster_type: len(cluster_list)
                for cluster_type, cluster_list in clusters.items()
                if cluster_type != "clustering_metadata"
            },
            "metadata": clusters.get("clustering_metadata", {}),
        }

        return stats

    def cleanup(self):
        """Cleanup resources"""
        # No longer using thread/process pools with external API
        logger.debug("Semantic clusterer cleanup completed (using external API)")
