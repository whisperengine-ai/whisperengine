"""
Intelligent Context Prioritization System for Memory Optimization
Prioritizes memory retrieval based on relevance, recency, and importance scores
"""

import logging
import math
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict
from enum import Enum

logger = logging.getLogger(__name__)


class ContextType(Enum):
    """Types of context for prioritization"""

    CONVERSATION = "conversation"
    FACT = "fact"
    SUMMARY = "summary"
    EMOTIONAL = "emotional"
    TOPIC = "topic"
    USER_PROFILE = "user_profile"


class RelevanceSignal(Enum):
    """Different signals that indicate relevance"""

    SEMANTIC_SIMILARITY = "semantic_similarity"
    TEMPORAL_PROXIMITY = "temporal_proximity"
    FREQUENCY_USAGE = "frequency_usage"
    USER_INTERACTION = "user_interaction"
    EMOTIONAL_SIGNIFICANCE = "emotional_significance"
    TOPIC_ALIGNMENT = "topic_alignment"
    RECENCY_BOOST = "recency_boost"


@dataclass
class ContextItem:
    """Represents a single context item with prioritization metadata"""

    item_id: str
    content: str
    context_type: ContextType
    user_id: str
    timestamp: str

    # Scoring components
    base_relevance: float = 0.0
    temporal_score: float = 0.0
    frequency_score: float = 0.0
    interaction_score: float = 0.0
    emotional_score: float = 0.0
    topic_score: float = 0.0

    # Composite scores
    final_score: float = 0.0
    confidence_level: float = 0.0

    # Metadata
    access_count: int = 0
    last_accessed: Optional[str] = None
    keywords: Optional[List[str]] = None
    embedding_vector: Optional[List[float]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PrioritizationConfig:
    """Configuration for context prioritization"""

    # Weight factors for different signals
    semantic_weight: float = 0.35
    temporal_weight: float = 0.20
    frequency_weight: float = 0.15
    interaction_weight: float = 0.10
    emotional_weight: float = 0.10
    topic_weight: float = 0.10

    # Decay parameters
    temporal_decay_days: float = 30.0
    frequency_decay_rate: float = 0.1

    # Thresholds
    min_relevance_threshold: float = 0.3
    max_context_items: int = 20
    diversity_factor: float = 0.2

    # Boost factors
    recent_conversation_boost: float = 1.5
    high_emotion_boost: float = 1.3
    frequent_topic_boost: float = 1.2


class IntelligentContextPrioritizer:
    """
    Advanced context prioritization system that intelligently ranks and selects
    the most relevant context for memory retrieval and conversation generation
    """

    def __init__(self, embedding_manager=None, config: Optional[PrioritizationConfig] = None):
        self.embedding_manager = embedding_manager
        self.config = config or PrioritizationConfig()
        self.logger = logging.getLogger(__name__)

        # Storage for context items and metadata
        self.context_items: Dict[str, ContextItem] = {}
        self.user_interaction_history: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.topic_frequency_cache: Dict[str, Dict[str, int]] = defaultdict(dict)

        # Performance tracking
        self.stats = {
            "prioritizations_performed": 0,
            "items_processed": 0,
            "cache_hits": 0,
            "diversity_adjustments": 0,
        }

        # Caching for performance
        self.score_cache: Dict[str, Tuple[float, datetime]] = {}
        self.cache_ttl = timedelta(minutes=30)

    async def prioritize_context(
        self,
        query: str,
        user_id: str,
        available_context: List[Dict[str, Any]],
        context_limit: Optional[int] = None,
    ) -> List[ContextItem]:
        """
        Prioritize and select the most relevant context items for a given query

        Args:
            query: The user's current query/message
            user_id: ID of the user making the query
            available_context: List of available context items
            context_limit: Maximum number of context items to return

        Returns:
            List of prioritized ContextItem objects
        """
        self.logger.debug(
            "Prioritizing %d context items for user %s", len(available_context), user_id
        )

        limit = context_limit or self.config.max_context_items

        # Convert available context to ContextItem objects
        context_items = await self._convert_to_context_items(available_context, user_id)

        if not context_items:
            return []

        # Generate query embedding for semantic similarity
        query_embedding = await self._get_query_embedding(query)

        # Score all context items
        scored_items = []
        for item in context_items:
            score_data = await self._calculate_comprehensive_score(
                item, query, query_embedding, user_id
            )
            item.final_score = score_data["final_score"]
            item.confidence_level = score_data["confidence"]

            # Update individual score components
            item.base_relevance = score_data.get("semantic_score", 0.0)
            item.temporal_score = score_data.get("temporal_score", 0.0)
            item.frequency_score = score_data.get("frequency_score", 0.0)
            item.interaction_score = score_data.get("interaction_score", 0.0)
            item.emotional_score = score_data.get("emotional_score", 0.0)
            item.topic_score = score_data.get("topic_score", 0.0)

            scored_items.append(item)

        # Sort by final score
        scored_items.sort(key=lambda x: x.final_score, reverse=True)

        # Apply diversity filtering to avoid redundant context
        diversified_items = await self._apply_diversity_filtering(scored_items, query_embedding)

        # Select top items within limit
        selected_items = diversified_items[:limit]

        # Update access tracking
        await self._update_access_tracking(selected_items, user_id)

        # Update stats
        self.stats["prioritizations_performed"] += 1
        self.stats["items_processed"] += len(context_items)

        self.logger.debug(
            "Selected %d context items with scores: %s",
            len(selected_items),
            [f"{item.item_id}:{item.final_score:.3f}" for item in selected_items[:5]],
        )

        return selected_items

    async def get_context_recommendations(
        self, user_id: str, recent_topics: List[str], limit: int = 10
    ) -> List[ContextItem]:
        """
        Get proactive context recommendations based on user's recent activity
        """
        recommendations = []

        # Get user's context items
        user_items = [item for item in self.context_items.values() if item.user_id == user_id]

        # Score items based on recent topics and usage patterns
        for item in user_items:
            relevance_score = await self._calculate_proactive_relevance(
                item, recent_topics, user_id
            )

            if relevance_score > self.config.min_relevance_threshold:
                item.final_score = relevance_score
                recommendations.append(item)

        # Sort and limit
        recommendations.sort(key=lambda x: x.final_score, reverse=True)
        return recommendations[:limit]

    async def analyze_context_gaps(self, user_id: str, query: str) -> Dict[str, Any]:
        """
        Analyze what types of context are missing or underrepresented
        """
        analysis = {
            "missing_context_types": [],
            "weak_signals": [],
            "recommendations": [],
            "coverage_score": 0.0,
        }

        # Get current user context
        user_items = [item for item in self.context_items.values() if item.user_id == user_id]

        # Analyze coverage by context type
        type_coverage = defaultdict(int)
        for item in user_items:
            type_coverage[item.context_type] += 1

        # Identify missing or weak areas
        expected_types = [ContextType.CONVERSATION, ContextType.FACT, ContextType.EMOTIONAL]
        for context_type in expected_types:
            if type_coverage[context_type] == 0:
                analysis["missing_context_types"].append(context_type.value)
            elif type_coverage[context_type] < 3:
                analysis["weak_signals"].append(
                    {
                        "type": context_type.value,
                        "count": type_coverage[context_type],
                        "recommendation": f"Need more {context_type.value} context",
                    }
                )

        # Calculate overall coverage score
        total_expected = len(expected_types) * 5  # Target 5 items per type
        total_actual = sum(type_coverage.values())
        analysis["coverage_score"] = min(1.0, total_actual / total_expected)

        # Generate recommendations
        if analysis["coverage_score"] < 0.7:
            analysis["recommendations"].append("Increase context collection")
        if len(analysis["missing_context_types"]) > 0:
            analysis["recommendations"].append("Collect missing context types")

        return analysis

    async def optimize_context_retrieval(
        self, user_id: str, performance_metrics: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Optimize context retrieval based on performance feedback
        """
        optimization = {"adjustments_made": [], "new_weights": {}, "performance_improvement": 0.0}

        # Analyze performance metrics
        response_quality = performance_metrics.get("response_quality", 0.5)
        relevance_score = performance_metrics.get("relevance_score", 0.5)
        user_satisfaction = performance_metrics.get("user_satisfaction", 0.5)

        # Adjust weights based on performance
        if response_quality < 0.6:
            # Increase semantic weight for better relevance
            self.config.semantic_weight = min(0.5, self.config.semantic_weight + 0.05)
            optimization["adjustments_made"].append("Increased semantic weight")

        if relevance_score < 0.5:
            # Increase topic alignment weight
            self.config.topic_weight = min(0.2, self.config.topic_weight + 0.02)
            optimization["adjustments_made"].append("Increased topic weight")

        if user_satisfaction < 0.6:
            # Increase recency and interaction weights
            self.config.temporal_weight = min(0.3, self.config.temporal_weight + 0.03)
            self.config.interaction_weight = min(0.15, self.config.interaction_weight + 0.02)
            optimization["adjustments_made"].append("Increased temporal and interaction weights")

        # Store new weights
        optimization["new_weights"] = {
            "semantic": self.config.semantic_weight,
            "temporal": self.config.temporal_weight,
            "frequency": self.config.frequency_weight,
            "interaction": self.config.interaction_weight,
            "emotional": self.config.emotional_weight,
            "topic": self.config.topic_weight,
        }

        return optimization

    # Private methods

    async def _convert_to_context_items(
        self, available_context: List[Dict[str, Any]], user_id: str
    ) -> List[ContextItem]:
        """Convert raw context data to ContextItem objects"""
        context_items = []

        for ctx_data in available_context:
            # Determine context type
            context_type = self._infer_context_type(ctx_data)

            # Extract content
            content = self._extract_content(ctx_data)
            if not content:
                continue

            # Create ContextItem
            item_id = ctx_data.get("id", f"ctx_{len(context_items)}")
            timestamp = ctx_data.get("timestamp", datetime.now().isoformat())

            item = ContextItem(
                item_id=item_id,
                content=content,
                context_type=context_type,
                user_id=user_id,
                timestamp=timestamp,
                keywords=ctx_data.get("keywords", []),
                embedding_vector=ctx_data.get("embedding", []),
            )

            # Load existing metadata if available
            if item_id in self.context_items:
                existing = self.context_items[item_id]
                item.access_count = existing.access_count
                item.last_accessed = existing.last_accessed

            context_items.append(item)
            self.context_items[item_id] = item

        return context_items

    def _infer_context_type(self, ctx_data: Dict[str, Any]) -> ContextType:
        """Infer the context type from context data"""
        if "type" in ctx_data:
            type_str = ctx_data["type"].lower()
            if type_str in ["conversation", "message"]:
                return ContextType.CONVERSATION
            elif type_str in ["fact", "knowledge"]:
                return ContextType.FACT
            elif type_str in ["summary"]:
                return ContextType.SUMMARY
            elif type_str in ["emotion", "emotional"]:
                return ContextType.EMOTIONAL
            elif type_str in ["topic"]:
                return ContextType.TOPIC
            elif type_str in ["profile", "user"]:
                return ContextType.USER_PROFILE

        # Fallback inference based on content
        content = self._extract_content(ctx_data)
        if any(word in content.lower() for word in ["feels", "emotion", "mood"]):
            return ContextType.EMOTIONAL
        elif any(word in content.lower() for word in ["summary", "overview"]):
            return ContextType.SUMMARY
        else:
            return ContextType.CONVERSATION

    def _extract_content(self, ctx_data: Dict[str, Any]) -> str:
        """Extract text content from context data"""
        if "content" in ctx_data:
            return str(ctx_data["content"])
        elif "text" in ctx_data:
            return str(ctx_data["text"])
        elif "message" in ctx_data:
            return str(ctx_data["message"])
        elif "fact" in ctx_data:
            return str(ctx_data["fact"])
        else:
            return str(ctx_data)

    async def _get_query_embedding(self, query: str) -> Optional[np.ndarray]:
        """Get embedding for the query"""
        if not self.embedding_manager:
            return None

        try:
            embedding = self.embedding_manager.generate_embedding(query)
            return embedding
        except Exception as e:
            self.logger.debug("Failed to generate query embedding: %s", str(e))
            return None

    async def _calculate_comprehensive_score(
        self, item: ContextItem, query: str, query_embedding: Optional[np.ndarray], user_id: str
    ) -> Dict[str, float]:
        """Calculate comprehensive relevance score for a context item"""

        # Check cache first
        cache_key = f"{item.item_id}_{hash(query)}_{user_id}"
        if cache_key in self.score_cache:
            cached_score, cached_time = self.score_cache[cache_key]
            if datetime.now() - cached_time < self.cache_ttl:
                self.stats["cache_hits"] += 1
                return {"final_score": cached_score, "confidence": 0.8}

        scores = {}

        # 1. Semantic similarity score
        scores["semantic_score"] = await self._calculate_semantic_score(
            item, query, query_embedding
        )

        # 2. Temporal relevance score
        scores["temporal_score"] = self._calculate_temporal_score(item)

        # 3. Frequency/usage score
        scores["frequency_score"] = self._calculate_frequency_score(item, user_id)

        # 4. User interaction score
        scores["interaction_score"] = self._calculate_interaction_score(item, user_id)

        # 5. Emotional significance score
        scores["emotional_score"] = self._calculate_emotional_score(item, query)

        # 6. Topic alignment score
        scores["topic_score"] = await self._calculate_topic_score(item, query, user_id)

        # Calculate weighted final score
        final_score = (
            scores["semantic_score"] * self.config.semantic_weight
            + scores["temporal_score"] * self.config.temporal_weight
            + scores["frequency_score"] * self.config.frequency_weight
            + scores["interaction_score"] * self.config.interaction_weight
            + scores["emotional_score"] * self.config.emotional_weight
            + scores["topic_score"] * self.config.topic_weight
        )

        # Apply boost factors
        final_score = self._apply_boost_factors(final_score, item, scores)

        # Calculate confidence based on signal strength
        confidence = self._calculate_score_confidence(scores)

        scores["final_score"] = final_score
        scores["confidence"] = confidence

        # Cache the result
        self.score_cache[cache_key] = (final_score, datetime.now())

        return scores

    async def _calculate_semantic_score(
        self, item: ContextItem, query: str, query_embedding: Optional[np.ndarray]
    ) -> float:
        """Calculate semantic similarity score"""
        if not query_embedding or not item.embedding_vector:
            # Fallback to keyword-based similarity
            return self._keyword_similarity(item.content, query)

        try:
            item_embedding = np.array(item.embedding_vector)
            similarity = self._cosine_similarity(query_embedding, item_embedding)
            return max(0.0, similarity)
        except Exception:
            return self._keyword_similarity(item.content, query)

    def _calculate_temporal_score(self, item: ContextItem) -> float:
        """Calculate temporal relevance score with decay"""
        try:
            item_time = datetime.fromisoformat(item.timestamp)
            current_time = datetime.now()

            # Calculate days since creation
            days_diff = (current_time - item_time).total_seconds() / (24 * 3600)

            # Apply exponential decay
            decay_factor = math.exp(-days_diff / self.config.temporal_decay_days)

            # Recent items get a boost
            if days_diff < 1:  # Less than 1 day old
                decay_factor *= self.config.recent_conversation_boost

            return min(1.0, decay_factor)

        except (ValueError, TypeError):
            return 0.5  # Default score for invalid timestamps

    def _calculate_frequency_score(self, item: ContextItem, user_id: str) -> float:
        """Calculate frequency/usage score"""
        access_count = item.access_count

        # Normalize access count (assumes typical range 0-20)
        normalized_count = min(1.0, access_count / 20.0)

        # Apply frequency decay (more recent accesses count more)
        if item.last_accessed:
            try:
                last_access = datetime.fromisoformat(item.last_accessed)
                days_since_access = (datetime.now() - last_access).total_seconds() / (24 * 3600)
                decay = math.exp(-days_since_access * self.config.frequency_decay_rate)
                normalized_count *= decay
            except (ValueError, TypeError):
                pass

        return normalized_count

    def _calculate_interaction_score(self, item: ContextItem, user_id: str) -> float:
        """Calculate user interaction score"""
        if user_id not in self.user_interaction_history:
            return 0.0

        user_history = self.user_interaction_history[user_id]

        # Check if this item type is frequently accessed by user
        context_type_key = f"access_{item.context_type.value}"
        type_access_count = user_history.get(context_type_key, 0)

        # Normalize (assumes typical range 0-50 for type access)
        type_score = min(1.0, type_access_count / 50.0)

        # Check specific item interactions
        item_interactions = user_history.get(f"item_{item.item_id}", 0)
        item_score = min(1.0, item_interactions / 10.0)

        # Combine scores
        return type_score * 0.7 + item_score * 0.3

    def _calculate_emotional_score(self, item: ContextItem, query: str) -> float:
        """Calculate emotional significance score"""
        # Check if the item or query contains emotional indicators
        emotional_keywords = [
            "feel",
            "emotion",
            "happy",
            "sad",
            "angry",
            "excited",
            "worried",
            "love",
            "hate",
            "frustrated",
            "calm",
            "stressed",
            "anxious",
        ]

        item_emotional = any(keyword in item.content.lower() for keyword in emotional_keywords)
        query_emotional = any(keyword in query.lower() for keyword in emotional_keywords)

        # Both emotional
        if item_emotional and query_emotional:
            return 1.0
        # One emotional
        elif item_emotional or query_emotional:
            return 0.6
        # Check for emotional context type
        elif item.context_type == ContextType.EMOTIONAL:
            return 0.8
        else:
            return 0.0

    async def _calculate_topic_score(self, item: ContextItem, query: str, user_id: str) -> float:
        """Calculate topic alignment score"""
        # Extract topics from query and item
        query_topics = self._extract_simple_topics(query)
        item_topics = self._extract_simple_topics(item.content)

        if not query_topics or not item_topics:
            return 0.0

        # Calculate topic overlap
        overlap = len(set(query_topics).intersection(set(item_topics)))
        total_topics = len(set(query_topics).union(set(item_topics)))

        if total_topics == 0:
            return 0.0

        base_score = overlap / total_topics

        # Boost if this topic is frequently discussed by user
        topic_frequency = self.topic_frequency_cache.get(user_id, {})
        for topic in query_topics:
            if topic in topic_frequency and topic_frequency[topic] > 5:
                base_score *= self.config.frequent_topic_boost
                break

        return min(1.0, base_score)

    def _apply_boost_factors(
        self, base_score: float, item: ContextItem, scores: Dict[str, float]
    ) -> float:
        """Apply various boost factors to the base score"""
        boosted_score = base_score

        # Recent conversation boost
        if scores.get("temporal_score", 0) > 0.8:
            boosted_score *= self.config.recent_conversation_boost

        # High emotional significance boost
        if scores.get("emotional_score", 0) > 0.7:
            boosted_score *= self.config.high_emotion_boost

        # Context type specific boosts
        if item.context_type == ContextType.FACT and scores.get("semantic_score", 0) > 0.7:
            boosted_score *= 1.1  # Slight boost for relevant facts

        return min(1.0, boosted_score)

    def _calculate_score_confidence(self, scores: Dict[str, float]) -> float:
        """Calculate confidence in the scoring based on signal strength"""
        # Count strong signals (> 0.5)
        strong_signals = sum(1 for score in scores.values() if score > 0.5)
        total_signals = len(scores)

        # Base confidence on proportion of strong signals
        base_confidence = strong_signals / total_signals if total_signals > 0 else 0.0

        # Boost confidence if we have very strong signals (> 0.8)
        very_strong_signals = sum(1 for score in scores.values() if score > 0.8)
        if very_strong_signals > 0:
            base_confidence = min(1.0, base_confidence + 0.2)

        return base_confidence

    async def _apply_diversity_filtering(
        self, scored_items: List[ContextItem], query_embedding: Optional[np.ndarray]
    ) -> List[ContextItem]:
        """Apply diversity filtering to avoid redundant context"""
        if len(scored_items) <= 5:  # No need to diversify small lists
            return scored_items

        diversified = []
        selected_embeddings = []

        for item in scored_items:
            # Always include the highest scored item
            if not diversified:
                diversified.append(item)
                if item.embedding_vector:
                    selected_embeddings.append(np.array(item.embedding_vector))
                continue

            # Check diversity with already selected items
            is_diverse = True
            if item.embedding_vector:
                item_embedding = np.array(item.embedding_vector)

                for selected_embedding in selected_embeddings:
                    similarity = self._cosine_similarity(item_embedding, selected_embedding)
                    if similarity > (1.0 - self.config.diversity_factor):  # Too similar
                        is_diverse = False
                        break

                if is_diverse:
                    diversified.append(item)
                    selected_embeddings.append(item_embedding)
                    self.stats["diversity_adjustments"] += 1
            else:
                # If no embedding, use content-based diversity check
                content_diverse = True
                for selected_item in diversified[-3:]:  # Check last 3 items
                    content_similarity = self._keyword_similarity(
                        item.content, selected_item.content
                    )
                    if content_similarity > 0.8:
                        content_diverse = False
                        break

                if content_diverse:
                    diversified.append(item)

        return diversified

    async def _update_access_tracking(self, selected_items: List[ContextItem], user_id: str):
        """Update access tracking for selected items"""
        current_time = datetime.now().isoformat()

        for item in selected_items:
            # Update item access count
            item.access_count += 1
            item.last_accessed = current_time

            # Update user interaction history
            user_history = self.user_interaction_history[user_id]

            # Track context type access
            type_key = f"access_{item.context_type.value}"
            user_history[type_key] = user_history.get(type_key, 0) + 1

            # Track specific item access
            item_key = f"item_{item.item_id}"
            user_history[item_key] = user_history.get(item_key, 0) + 1

            # Update topic frequency if keywords available
            if item.keywords:
                topic_freq = self.topic_frequency_cache[user_id]
                for keyword in item.keywords:
                    topic_freq[keyword] = topic_freq.get(keyword, 0) + 1

    async def _calculate_proactive_relevance(
        self, item: ContextItem, recent_topics: List[str], user_id: str
    ) -> float:
        """Calculate relevance for proactive recommendations"""
        scores = []

        # Topic alignment with recent topics
        if recent_topics and item.keywords:
            topic_overlap = len(set(recent_topics).intersection(set(item.keywords)))
            topic_score = topic_overlap / max(len(recent_topics), len(item.keywords))
            scores.append(topic_score * 0.4)

        # Usage frequency
        freq_score = self._calculate_frequency_score(item, user_id)
        scores.append(freq_score * 0.3)

        # Recency
        temporal_score = self._calculate_temporal_score(item)
        scores.append(temporal_score * 0.2)

        # Context type relevance
        type_preference = self.user_interaction_history.get(user_id, {}).get(
            f"access_{item.context_type.value}", 0
        )
        type_score = min(1.0, type_preference / 20.0)
        scores.append(type_score * 0.1)

        return sum(scores) / len(scores) if scores else 0.0

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            return float(dot_product / (norm1 * norm2))
        except Exception:
            return 0.0

    def _keyword_similarity(self, text1: str, text2: str) -> float:
        """Calculate keyword-based similarity as fallback"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))

        return intersection / union if union > 0 else 0.0

    def _extract_simple_topics(self, text: str) -> List[str]:
        """Extract simple topics from text"""
        import re

        # Clean and tokenize
        text_clean = re.sub(r"[^\w\s]", " ", text.lower())
        words = text_clean.split()

        # Filter for potential topic words (longer than 3 chars)
        topic_words = [word for word in words if len(word) > 3]

        # Return most frequent words as topics
        from collections import Counter

        word_counts = Counter(topic_words)
        return [word for word, count in word_counts.most_common(5)]

    def get_prioritization_stats(self) -> Dict[str, Any]:
        """Get comprehensive prioritization statistics"""
        return {
            "total_context_items": len(self.context_items),
            "prioritizations_performed": self.stats["prioritizations_performed"],
            "items_processed": self.stats["items_processed"],
            "cache_hits": self.stats["cache_hits"],
            "cache_hit_rate": (
                self.stats["cache_hits"] / max(self.stats["prioritizations_performed"], 1)
            ),
            "diversity_adjustments": self.stats["diversity_adjustments"],
            "current_weights": {
                "semantic": self.config.semantic_weight,
                "temporal": self.config.temporal_weight,
                "frequency": self.config.frequency_weight,
                "interaction": self.config.interaction_weight,
                "emotional": self.config.emotional_weight,
                "topic": self.config.topic_weight,
            },
            "cache_size": len(self.score_cache),
            "user_interaction_profiles": len(self.user_interaction_history),
        }
