"""
RoBERTa-Enhanced Context Prioritizer for Memory Optimization

Replaces basic keyword emotion matching with sophisticated RoBERTa-based emotion analysis
for improved context prioritization and memory retrieval quality.
"""

import logging
import math
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

import numpy as np

# Import the enhanced emotion analyzer
from src.intelligence.enhanced_vector_emotion_analyzer import EnhancedVectorEmotionAnalyzer

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
    embedding_vector: list[float] | None = None
    semantic_score: float = 0.0
    temporal_score: float = 0.0
    frequency_score: float = 0.0
    interaction_score: float = 0.0
    emotional_score: float = 0.0
    topic_score: float = 0.0
    final_score: float = 0.0
    confidence: float = 0.0
    boost_factors: dict[str, float] | None = None


@dataclass
class PriorityConfig:
    """Configuration for context prioritization weights and parameters"""

    # Scoring weights (must sum to 1.0)
    semantic_weight: float = 0.35
    temporal_weight: float = 0.20
    frequency_weight: float = 0.15
    interaction_weight: float = 0.15
    emotional_weight: float = 0.10  # Enhanced with RoBERTa
    topic_weight: float = 0.05

    # Temporal parameters
    temporal_decay_days: float = 30.0
    recent_conversation_boost: float = 1.2

    # Boost factors
    high_emotion_boost: float = 1.3  # RoBERTa emotional intensity > 0.7
    multi_emotion_boost: float = 1.15  # Multiple RoBERTa emotions detected
    high_frequency_threshold: int = 5
    high_frequency_boost: float = 1.1
    user_interaction_boost: float = 1.2

    # Cache settings
    score_cache_ttl_minutes: float = 30.0


class EnhancedContextPrioritizer:
    """
    RoBERTa-Enhanced Context Prioritization System
    
    Replaces basic keyword emotional detection with sophisticated multi-emotion analysis
    using RoBERTa transformer models for improved context understanding.
    """

    def __init__(self, config: Optional[PriorityConfig] = None):
        """Initialize the context prioritizer with enhanced emotion analysis"""
        self.config = config or PriorityConfig()
        self.score_cache: dict[str, tuple[float, datetime]] = {}
        
        # Initialize RoBERTa-based emotion analyzer
        try:
            self.emotion_analyzer = EnhancedVectorEmotionAnalyzer()
            self.use_enhanced_emotions = True
            logger.info("✅ RoBERTa-Enhanced emotion analysis enabled for context prioritization")
        except (ImportError, RuntimeError, OSError) as e:
            logger.warning("⚠️ Could not initialize RoBERTa emotion analyzer: %s", e)
            logger.warning("Falling back to keyword-based emotion detection")
            self.emotion_analyzer = None
            self.use_enhanced_emotions = False

        # Validate configuration
        self._validate_config()

        logger.info("Enhanced Context Prioritizer initialized")
        logger.info("Scoring weights: %s", asdict(self.config))

    def _validate_config(self):
        """Validate that scoring weights sum to approximately 1.0"""
        total_weight = (
            self.config.semantic_weight
            + self.config.temporal_weight
            + self.config.frequency_weight
            + self.config.interaction_weight
            + self.config.emotional_weight
            + self.config.topic_weight
        )

        if abs(total_weight - 1.0) > 0.01:
            logger.warning("Scoring weights sum to %.3f, not 1.0. May affect scoring.", total_weight)

    async def prioritize_contexts(
        self,
        items: list[ContextItem],
        query: str,
        user_id: str,
        limit: int = 10,
        query_embedding: np.ndarray | None = None,
    ) -> list[ContextItem]:
        """
        Prioritize contexts using RoBERTa-enhanced emotional analysis
        
        Args:
            items: List of context items to prioritize
            query: User's query for context matching
            user_id: User ID for personalization
            limit: Maximum number of items to return
            query_embedding: Pre-computed embedding for the query
            
        Returns:
            Prioritized and scored list of context items
        """
        if not items:
            return []

        logger.info("Prioritizing %d contexts with enhanced emotion analysis", len(items))
        
        # Score all items
        scored_items = []
        for item in items:
            try:
                scores = await self._calculate_comprehensive_score(
                    item, query, user_id, query_embedding
                )
                # Update item with calculated scores
                for key, value in scores.items():
                    setattr(item, key, value)
                scored_items.append(item)
            except (ValueError, KeyError, TypeError) as e:
                logger.error("Error scoring item %s: %s", item.item_id, e)
                # Add item with zero score to avoid losing it
                item.final_score = 0.0
                item.confidence = 0.0
                scored_items.append(item)

        # Sort by final score (descending)
        scored_items.sort(key=lambda x: x.final_score, reverse=True)

        # Apply limit
        result = scored_items[:limit]

        logger.info("Returning top %d prioritized contexts", len(result))
        if result:
            logger.info("Score range: %.3f to %.3f", result[-1].final_score, result[0].final_score)

        return result

    async def _calculate_comprehensive_score(
        self,
        item: ContextItem,
        query: str,
        user_id: str,
        query_embedding: np.ndarray | None = None,
    ) -> dict[str, float]:
        """Calculate comprehensive relevance score with RoBERTa emotion analysis"""
        
        # Check cache first
        cache_key = f"{item.item_id}:{hash(query)}:{user_id}"
        if cache_key in self.score_cache:
            cached_score, cached_time = self.score_cache[cache_key]
            if datetime.now() - cached_time < timedelta(minutes=self.config.score_cache_ttl_minutes):
                return {"final_score": cached_score, "confidence": 0.8}

        scores = {}

        # 1. Semantic similarity score
        scores["semantic_score"] = await self._calculate_semantic_score(item, query, query_embedding)

        # 2. Temporal relevance score
        scores["temporal_score"] = self._calculate_temporal_score(item)

        # 3. Frequency score (how often this context appears)
        scores["frequency_score"] = await self._calculate_frequency_score(item, user_id)

        # 4. User interaction score
        scores["interaction_score"] = await self._calculate_interaction_score(item, user_id)

        # 5. Enhanced emotional significance score (RoBERTa-powered)
        scores["emotional_score"] = await self._calculate_enhanced_emotional_score(item, query)

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

        # Apply boost factors with RoBERTa emotional enhancements
        final_score = await self._apply_enhanced_boost_factors(final_score, item, scores, query)

        # Calculate confidence based on signal strength
        confidence = self._calculate_score_confidence(scores)

        scores["final_score"] = final_score
        scores["confidence"] = confidence

        # Cache the result
        self.score_cache[cache_key] = (final_score, datetime.now())

        return scores

    async def _calculate_enhanced_emotional_score(self, item: ContextItem, query: str) -> float:
        """
        Calculate emotional significance using RoBERTa transformer analysis
        
        Replaces basic keyword matching with sophisticated emotion detection that can:
        - Detect multiple emotions simultaneously
        - Measure emotional intensity accurately  
        - Handle complex/nuanced emotions
        - Consider emotional context and matching
        """
        if not self.use_enhanced_emotions or not self.emotion_analyzer:
            # Fallback to basic keyword analysis
            return self._calculate_basic_emotional_score(item, query)

        try:
            # Analyze emotional content of both item and query using the main analyze_emotion method
            item_emotion = await self.emotion_analyzer.analyze_emotion(
                content=item.content,
                user_id="context_prioritizer"  # Use a service user ID
            )
            query_emotion = await self.emotion_analyzer.analyze_emotion(
                content=query,
                user_id="context_prioritizer"
            )

            # Base emotional significance
            emotional_score = 0.0

            # Item has emotional content
            if item_emotion.all_emotions:
                emotional_score += 0.4
                
                # Boost for high emotional intensity
                if item_emotion.intensity > 0.7:
                    emotional_score += 0.3
                elif item_emotion.intensity > 0.5:
                    emotional_score += 0.2
                
                # Boost for multiple emotions (complex emotional state)
                if len(item_emotion.all_emotions) > 1:
                    emotional_score += 0.2

            # Query has emotional content  
            if query_emotion.all_emotions:
                emotional_score += 0.3
                
                # Emotional matching - do item and query share emotions?
                shared_emotions = set(item_emotion.all_emotions.keys()) & set(query_emotion.all_emotions.keys())
                if shared_emotions:
                    # Strong boost for matching emotions
                    emotional_score += 0.4
                    
                    # Extra boost if the matching emotions are intense
                    for emotion in shared_emotions:
                        item_intensity = item_emotion.all_emotions.get(emotion, 0.0)
                        query_intensity = query_emotion.all_emotions.get(emotion, 0.0)
                        if item_intensity > 0.6 and query_intensity > 0.6:
                            emotional_score += 0.2

            # Context type boost
            if item.context_type == ContextType.EMOTIONAL:
                emotional_score += 0.3

            # Cap at 1.0
            emotional_score = min(emotional_score, 1.0)

            logger.debug("Enhanced emotional score for '%.50s...': %.3f", item.content, emotional_score)
            return emotional_score

        except (ValueError, RuntimeError, TypeError) as e:
            logger.error("Error in enhanced emotional scoring: %s", e)
            # Fallback to basic keyword analysis
            return self._calculate_basic_emotional_score(item, query)

    def _calculate_basic_emotional_score(self, item: ContextItem, query: str) -> float:
        """Basic keyword-based emotional scoring as fallback"""
        emotional_keywords = [
            "feel", "emotion", "happy", "sad", "angry", "excited", "worried",
            "love", "hate", "frustrated", "calm", "stressed", "anxious"
        ]

        item_emotional = any(keyword in item.content.lower() for keyword in emotional_keywords)
        query_emotional = any(keyword in query.lower() for keyword in emotional_keywords)

        if item_emotional and query_emotional:
            return 1.0
        elif item_emotional or query_emotional:
            return 0.6
        elif item.context_type == ContextType.EMOTIONAL:
            return 0.8
        else:
            return 0.0

    async def _apply_enhanced_boost_factors(
        self, 
        base_score: float, 
        item: ContextItem, 
        scores: dict[str, float],
        query: str
    ) -> float:
        """Apply boost factors including RoBERTa emotional enhancements"""
        boosted_score = base_score
        boost_factors = {}

        # Enhanced emotional boosts using RoBERTa analysis
        if self.use_enhanced_emotions and self.emotion_analyzer:
            try:
                item_emotion = await self.emotion_analyzer.analyze_emotion(
                    content=item.content,
                    user_id="context_prioritizer"
                )
                
                # High emotional intensity boost
                if item_emotion.intensity > 0.7:
                    boost = self.config.high_emotion_boost
                    boosted_score *= boost
                    boost_factors["high_emotion"] = boost
                
                # Multi-emotion complexity boost
                if len(item_emotion.all_emotions) > 1:
                    boost = self.config.multi_emotion_boost  
                    boosted_score *= boost
                    boost_factors["multi_emotion"] = boost
                    
            except (ValueError, RuntimeError, TypeError) as e:
                logger.error("Error applying enhanced emotional boosts: %s", e)

        # Frequency boost
        if scores.get("frequency_score", 0) > 0.8:
            boost = self.config.high_frequency_boost
            boosted_score *= boost
            boost_factors["high_frequency"] = boost

        # User interaction boost
        if scores.get("interaction_score", 0) > 0.7:
            boost = self.config.user_interaction_boost
            boosted_score *= boost
            boost_factors["user_interaction"] = boost

        # Recent conversation boost
        if scores.get("temporal_score", 0) > 0.9:
            boost = self.config.recent_conversation_boost
            boosted_score *= boost
            boost_factors["recent_conversation"] = boost

        # Store boost factors for analysis
        item.boost_factors = boost_factors

        return boosted_score

    async def _calculate_semantic_score(
        self, item: ContextItem, query: str, query_embedding: np.ndarray | None
    ) -> float:
        """Calculate semantic similarity score"""
        if not query_embedding or not item.embedding_vector:
            # Fallback to keyword-based similarity
            return self._keyword_similarity(item.content, query)

        try:
            item_embedding = np.array(item.embedding_vector)
            similarity = self._cosine_similarity(query_embedding, item_embedding)
            return max(0.0, similarity)
        except (ValueError, TypeError):
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

            return max(0.0, min(1.0, decay_factor))

        except (ValueError, OverflowError):
            return 0.5  # Default temporal score

    async def _calculate_frequency_score(self, item: ContextItem, user_id: str) -> float:
        """Calculate frequency score based on how often this context appears"""
        # This would typically query the memory system for usage frequency
        # For now, return a placeholder based on context type
        # user_id parameter reserved for future frequency tracking implementation
        _ = user_id  # Acknowledge unused parameter
        frequency_map = {
            ContextType.CONVERSATION: 0.8,
            ContextType.EMOTIONAL: 0.7,
            ContextType.USER_PROFILE: 0.6,
            ContextType.FACT: 0.5,
            ContextType.TOPIC: 0.4,
            ContextType.SUMMARY: 0.3,
        }
        return frequency_map.get(item.context_type, 0.5)

    async def _calculate_interaction_score(self, item: ContextItem, user_id: str) -> float:
        """Calculate user interaction score"""
        # This would typically query interaction history
        # For now, return a score based on context type
        # user_id parameter reserved for future interaction tracking implementation
        _ = user_id  # Acknowledge unused parameter
        interaction_map = {
            ContextType.CONVERSATION: 0.9,
            ContextType.EMOTIONAL: 0.8,
            ContextType.USER_PROFILE: 0.7,
            ContextType.TOPIC: 0.6,
            ContextType.FACT: 0.5,
            ContextType.SUMMARY: 0.4,
        }
        return interaction_map.get(item.context_type, 0.5)

    async def _calculate_topic_score(self, item: ContextItem, query: str, user_id: str) -> float:
        """Calculate topic alignment score"""
        # user_id parameter reserved for future personalized topic scoring
        _ = user_id  # Acknowledge unused parameter
        
        # Simple topic scoring based on content overlap
        query_words = set(query.lower().split())
        item_words = set(item.content.lower().split())
        
        if not query_words:
            return 0.5

        overlap = len(query_words.intersection(item_words))
        return min(1.0, overlap / len(query_words))

    def _calculate_score_confidence(self, scores: dict[str, float]) -> float:
        """Calculate confidence in the scoring based on signal strength"""
        # Confidence based on how many signals are strong
        strong_signals = sum(1 for score in scores.values() if isinstance(score, float) and score > 0.7)
        total_signals = len([s for s in scores.values() if isinstance(s, float)])
        
        if total_signals == 0:
            return 0.0
            
        return strong_signals / total_signals

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            dot_product = np.dot(a, b)
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)
            
            if norm_a == 0 or norm_b == 0:
                return 0.0
                
            return dot_product / (norm_a * norm_b)
        except (ZeroDivisionError, ValueError):
            return 0.0

    def _keyword_similarity(self, text1: str, text2: str) -> float:
        """Fallback keyword-based similarity"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
            
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0