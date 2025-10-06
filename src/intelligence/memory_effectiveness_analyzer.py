"""
MemoryBoost: Memory Effectiveness Analyzer

Analyzes and scores memory quality for intelligent retrieval prioritization.
Builds on WhisperEngine's vector-native memory system to enhance memory selection
and conversation continuity through multi-factor quality scoring.

Part of the WhisperEngine Adaptive Learning System.
"""

import asyncio
import logging
import math
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

# WhisperEngine core imports
from src.memory.vector_memory_system import VectorMemory, MemoryType, MemoryTier
from src.utils.production_error_handler import handle_errors, ErrorCategory, ErrorSeverity

logger = logging.getLogger(__name__)


class MemoryQualityFactor(Enum):
    """Quality factors for memory effectiveness scoring"""
    SEMANTIC_RELEVANCE = "semantic_relevance"
    TEMPORAL_FRESHNESS = "temporal_freshness"
    INTERACTION_FREQUENCY = "interaction_frequency"
    EMOTIONAL_SIGNIFICANCE = "emotional_significance"
    RELATIONSHIP_CONTEXT = "relationship_context"


@dataclass
class MemoryQualityScore:
    """Comprehensive memory quality assessment"""
    memory_id: str
    overall_score: float  # 0-100 scale
    factor_scores: Dict[MemoryQualityFactor, float]
    tier_recommendation: MemoryTier
    confidence: float
    optimization_suggestions: List[str]
    analysis_timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/serialization"""
        return {
            'memory_id': self.memory_id,
            'overall_score': self.overall_score,
            'factor_scores': {factor.value: score for factor, score in self.factor_scores.items()},
            'tier_recommendation': self.tier_recommendation.value,
            'confidence': self.confidence,
            'optimization_suggestions': self.optimization_suggestions,
            'analysis_timestamp': self.analysis_timestamp.isoformat()
        }


@dataclass
class ConversationContext:
    """Context for memory effectiveness analysis"""
    current_message: str
    conversation_history: List[Dict[str, Any]]
    user_id: str
    bot_name: str
    relationship_depth: Optional[str] = None
    emotional_state: Optional[str] = None
    conversation_type: Optional[str] = None  # casual, deep, technical, etc.


class MemoryEffectivenessAnalyzer:
    """
    Analyzes memory quality and effectiveness for intelligent prioritization.
    
    Core functionality:
    - Multi-factor memory quality scoring (0-100 scale)
    - Conversation impact analysis
    - Memory freshness and relevance evaluation
    - Cross-conversation effectiveness tracking
    - Tier recommendation for memory promotion/demotion
    """
    
    def __init__(self, memory_manager=None, postgres_pool=None):
        """
        Initialize memory effectiveness analyzer.
        
        Args:
            memory_manager: Vector memory system for memory operations
            postgres_pool: PostgreSQL connection pool for effectiveness tracking
        """
        self.memory_manager = memory_manager
        self.postgres_pool = postgres_pool
        
        # Quality factor weights (tunable based on character and conversation type)
        self.default_factor_weights = {
            MemoryQualityFactor.SEMANTIC_RELEVANCE: 0.35,
            MemoryQualityFactor.TEMPORAL_FRESHNESS: 0.25,
            MemoryQualityFactor.INTERACTION_FREQUENCY: 0.20,
            MemoryQualityFactor.EMOTIONAL_SIGNIFICANCE: 0.15,
            MemoryQualityFactor.RELATIONSHIP_CONTEXT: 0.05
        }
        
        # Memory tier thresholds for recommendations
        self.tier_thresholds = {
            MemoryTier.LONG_TERM: 75.0,    # High-quality, significant memories
            MemoryTier.MEDIUM_TERM: 45.0,  # Moderate quality, useful memories
            MemoryTier.SHORT_TERM: 0.0     # Recent or low-quality memories
        }
        
        # Statistics tracking
        self.stats = {
            'analyses_performed': 0,
            'high_quality_memories': 0,
            'tier_promotions_suggested': 0,
            'tier_demotions_suggested': 0
        }
        
        logger.info("MemoryEffectivenessAnalyzer initialized with adaptive scoring system")
    
    @handle_errors(category=ErrorCategory.MEMORY_SYSTEM, severity=ErrorSeverity.MEDIUM)
    async def analyze_memory_quality(
        self, 
        memory: VectorMemory, 
        context: ConversationContext,
        factor_weights: Optional[Dict[MemoryQualityFactor, float]] = None
    ) -> MemoryQualityScore:
        """
        Analyze memory quality with multi-factor scoring.
        
        Args:
            memory: Memory to analyze
            context: Current conversation context
            factor_weights: Custom factor weights (optional)
            
        Returns:
            MemoryQualityScore with comprehensive analysis
        """
        weights = factor_weights or self.default_factor_weights
        factor_scores = {}
        
        # Calculate individual factor scores
        factor_scores[MemoryQualityFactor.SEMANTIC_RELEVANCE] = await self._calculate_semantic_relevance(
            memory, context
        )
        
        factor_scores[MemoryQualityFactor.TEMPORAL_FRESHNESS] = self._calculate_temporal_freshness(
            memory, context
        )
        
        factor_scores[MemoryQualityFactor.INTERACTION_FREQUENCY] = await self._calculate_interaction_frequency(
            memory, context
        )
        
        factor_scores[MemoryQualityFactor.EMOTIONAL_SIGNIFICANCE] = self._calculate_emotional_significance(
            memory, context
        )
        
        factor_scores[MemoryQualityFactor.RELATIONSHIP_CONTEXT] = self._calculate_relationship_context(
            memory, context
        )
        
        # Calculate weighted overall score
        overall_score = sum(
            factor_scores[factor] * weights[factor]
            for factor in MemoryQualityFactor
        )
        
        # Determine tier recommendation
        tier_recommendation = self._recommend_memory_tier(overall_score, memory)
        
        # Calculate confidence based on factor consistency
        confidence = self._calculate_confidence(factor_scores, weights)
        
        # Generate optimization suggestions
        optimization_suggestions = self._generate_optimization_suggestions(
            factor_scores, memory, context
        )
        
        # Create quality score object
        quality_score = MemoryQualityScore(
            memory_id=memory.id,
            overall_score=round(overall_score, 2),
            factor_scores=factor_scores,
            tier_recommendation=tier_recommendation,
            confidence=round(confidence, 3),
            optimization_suggestions=optimization_suggestions,
            analysis_timestamp=datetime.utcnow()
        )
        
        # Update statistics
        self.stats['analyses_performed'] += 1
        if overall_score >= 75.0:
            self.stats['high_quality_memories'] += 1
        
        if tier_recommendation != memory.memory_tier:
            if self._is_tier_promotion(memory.memory_tier, tier_recommendation):
                self.stats['tier_promotions_suggested'] += 1
            else:
                self.stats['tier_demotions_suggested'] += 1
        
        logger.debug("Memory quality analysis complete: %s scored %.2f", memory.id, overall_score)
        return quality_score
    
    @handle_errors(category=ErrorCategory.MEMORY_SYSTEM, severity=ErrorSeverity.MEDIUM)
    async def batch_analyze_memories(
        self,
        memories: List[VectorMemory],
        context: ConversationContext,
        factor_weights: Optional[Dict[MemoryQualityFactor, float]] = None
    ) -> List[MemoryQualityScore]:
        """
        Analyze multiple memories in parallel for efficiency.
        
        Args:
            memories: List of memories to analyze
            context: Current conversation context
            factor_weights: Custom factor weights (optional)
            
        Returns:
            List of MemoryQualityScore objects
        """
        # Create analysis tasks for parallel execution
        analysis_tasks = [
            self.analyze_memory_quality(memory, context, factor_weights)
            for memory in memories
        ]
        
        # Execute analyses in parallel
        quality_scores = await asyncio.gather(*analysis_tasks, return_exceptions=True)
        
        # Filter out exceptions and log errors
        valid_scores = []
        for i, result in enumerate(quality_scores):
            if isinstance(result, Exception):
                logger.error("Memory analysis failed for %s: %s", memories[i].id, result)
            else:
                valid_scores.append(result)
        
        logger.info("Batch analysis complete: %d/%d successful", len(valid_scores), len(memories))
        return valid_scores
    
    async def _calculate_semantic_relevance(
        self, 
        memory: VectorMemory, 
        context: ConversationContext
    ) -> float:
        """
        Calculate semantic relevance score (0-100).
        
        Uses vector similarity if memory manager available,
        falls back to text similarity.
        """
        if not self.memory_manager:
            # Fallback to basic text similarity
            return self._calculate_text_similarity(memory.content, context.current_message)
        
        try:
            # Use vector similarity for accurate semantic matching
            query_embedding = await self.memory_manager.generate_embedding(context.current_message)
            
            if memory.embedding and query_embedding:
                similarity = self._cosine_similarity(memory.embedding, query_embedding)
                # Convert similarity (-1 to 1) to score (0 to 100)
                return max(0, min(100, (similarity + 1) * 50))
            else:
                # Fall back to text similarity
                return self._calculate_text_similarity(memory.content, context.current_message)
                
        except (TypeError, ValueError, IndexError) as e:
            logger.warning("Vector similarity calculation failed: %s", e)
            return self._calculate_text_similarity(memory.content, context.current_message)
    
    def _calculate_temporal_freshness(
        self, 
        memory: VectorMemory, 
        _context: ConversationContext  # Context reserved for future enhancements
    ) -> float:
        """
        Calculate temporal freshness score (0-100).
        
        Recent memories score higher, with decay based on memory type and tier.
        """
        if not memory.timestamp:
            return 50.0  # Neutral score for missing timestamp
        
        # Calculate age in days
        age_days = (datetime.utcnow() - memory.timestamp).total_seconds() / 86400
        
        # Different decay rates based on memory type and tier
        if memory.memory_tier == MemoryTier.LONG_TERM:
            # Long-term memories decay slowly
            half_life_days = 365  # 1 year half-life
        elif memory.memory_tier == MemoryTier.MEDIUM_TERM:
            # Medium-term memories decay moderately
            half_life_days = 90   # 3 month half-life
        else:
            # Short-term memories decay quickly
            half_life_days = 30   # 1 month half-life
        
        # Different types have different freshness importance
        type_multipliers = {
            MemoryType.CONVERSATION: 1.0,
            MemoryType.FACT: 0.8,        # Facts less dependent on freshness
            MemoryType.RELATIONSHIP: 0.6, # Relationships evolve slowly
            MemoryType.PREFERENCE: 0.7,   # Preferences change gradually
            MemoryType.CONTEXT: 1.2,     # Context highly time-dependent
            MemoryType.CORRECTION: 1.1   # Corrections should be fresh
        }
        
        multiplier = type_multipliers.get(memory.memory_type, 1.0)
        effective_half_life = half_life_days * multiplier
        
        # Exponential decay function
        freshness_score = 100 * math.exp(-0.693 * age_days / effective_half_life)
        
        return max(0, min(100, freshness_score))
    
    async def _calculate_interaction_frequency(
        self, 
        memory: VectorMemory, 
        context: ConversationContext
    ) -> float:
        """
        Calculate interaction frequency score (0-100).
        
        Memories that are frequently accessed score higher.
        """
        if not self.postgres_pool:
            # Default score if no tracking available
            return 50.0
        
        try:
            async with self.postgres_pool.acquire() as conn:
                # Query memory effectiveness table for usage statistics
                result = await conn.fetchrow("""
                    SELECT usage_count, last_accessed, created_at
                    FROM memory_effectiveness 
                    WHERE memory_id = $1 AND user_id = $2 AND bot_name = $3
                """, memory.id, context.user_id, context.bot_name)
                
                if not result:
                    # New memory - neutral score
                    return 50.0
                
                usage_count = result['usage_count'] or 0
                last_accessed = result['last_accessed']
                created_at = result['created_at']
                
                # Calculate frequency score based on usage and recency
                if created_at:
                    age_days = (datetime.utcnow() - created_at).total_seconds() / 86400
                    frequency = usage_count / max(1, age_days) if age_days > 0 else usage_count
                else:
                    frequency = usage_count
                
                # Recency bonus if accessed recently
                recency_bonus = 0
                if last_accessed:
                    days_since_access = (datetime.utcnow() - last_accessed).total_seconds() / 86400
                    recency_bonus = max(0, 20 * math.exp(-days_since_access / 7))  # 7-day recency window
                
                # Logarithmic scaling for frequency score
                frequency_score = min(80, 20 * math.log(frequency + 1)) + recency_bonus
                
                return max(0, min(100, frequency_score))
                
        except (TypeError, ValueError, IndexError) as e:
            logger.warning("Interaction frequency calculation failed: %s", e)
            return 50.0
    
    def _calculate_emotional_significance(
        self, 
        memory: VectorMemory, 
        _context: ConversationContext  # Context reserved for future enhancements
    ) -> float:
        """
        Calculate emotional significance score (0-100).
        
        Memories with strong emotional content score higher.
        """
        # Extract emotional metadata from memory
        emotion_data = memory.metadata.get('emotion_data', {}) if memory.metadata else {}
        
        # Base emotional intensity
        emotional_intensity = emotion_data.get('intensity', 0.5)
        emotional_confidence = emotion_data.get('confidence', 0.5)
        
        # Multi-emotion bonus
        is_multi_emotion = emotion_data.get('is_multi_emotion', False)
        emotion_count = emotion_data.get('emotion_count', 1)
        
        # Emotional significance factors
        base_score = emotional_intensity * 100
        confidence_multiplier = 0.5 + (emotional_confidence * 0.5)  # 0.5 to 1.0 range
        complexity_bonus = min(20, emotion_count * 5) if is_multi_emotion else 0
        
        # Memory type emotional importance
        type_emotional_weights = {
            MemoryType.CONVERSATION: 1.0,
            MemoryType.RELATIONSHIP: 1.2,  # Relationships inherently emotional
            MemoryType.PREFERENCE: 0.8,
            MemoryType.FACT: 0.4,          # Facts less emotional
            MemoryType.CONTEXT: 0.6,
            MemoryType.CORRECTION: 0.7
        }
        
        type_weight = type_emotional_weights.get(memory.memory_type, 1.0)
        
        # Calculate final emotional significance score
        significance_score = (base_score * confidence_multiplier + complexity_bonus) * type_weight
        
        return max(0, min(100, significance_score))
    
    def _calculate_relationship_context(
        self, 
        memory: VectorMemory, 
        context: ConversationContext
    ) -> float:
        """
        Calculate relationship context score (0-100).
        
        Memories appropriate for current relationship depth score higher.
        """
        # Default relationship depth if not provided
        relationship_depth = context.relationship_depth or "friend"
        
        # Memory relationship metadata
        memory_relationship_level = memory.metadata.get('relationship_level') if memory.metadata else None
        
        # Relationship appropriateness scoring
        relationship_scores = {
            'acquaintance': {'acquaintance': 100, 'friend': 80, 'close': 60, 'intimate': 40},
            'friend': {'acquaintance': 70, 'friend': 100, 'close': 90, 'intimate': 70},
            'close': {'acquaintance': 50, 'friend': 80, 'close': 100, 'intimate': 90},
            'intimate': {'acquaintance': 30, 'friend': 60, 'close': 90, 'intimate': 100}
        }
        
        if memory_relationship_level and memory_relationship_level in relationship_scores:
            return relationship_scores[relationship_depth].get(memory_relationship_level, 75)
        
        # Memory type relationship appropriateness
        type_relationship_scores = {
            MemoryType.CONVERSATION: 85,    # Generally appropriate
            MemoryType.RELATIONSHIP: 95,    # Highly relevant
            MemoryType.PREFERENCE: 80,      # Moderately relevant
            MemoryType.FACT: 70,           # Context dependent
            MemoryType.CONTEXT: 75,        # Context dependent
            MemoryType.CORRECTION: 90      # Important for accuracy
        }
        
        return type_relationship_scores.get(memory.memory_type, 75)
    
    def _recommend_memory_tier(self, overall_score: float, _memory: VectorMemory) -> MemoryTier:
        """
        Recommend memory tier based on quality score and current tier.
        """
        if overall_score >= self.tier_thresholds[MemoryTier.LONG_TERM]:
            return MemoryTier.LONG_TERM
        elif overall_score >= self.tier_thresholds[MemoryTier.MEDIUM_TERM]:
            return MemoryTier.MEDIUM_TERM
        else:
            return MemoryTier.SHORT_TERM
    
    def _calculate_confidence(
        self, 
        factor_scores: Dict[MemoryQualityFactor, float], 
        _weights: Dict[MemoryQualityFactor, float]  # Reserved for weighted confidence calculation
    ) -> float:
        """
        Calculate confidence in the quality assessment based on factor consistency.
        """
        scores = list(factor_scores.values())
        if not scores:
            return 0.5
        
        # Calculate variance in factor scores
        mean_score = sum(scores) / len(scores)
        variance = sum((score - mean_score) ** 2 for score in scores) / len(scores)
        
        # Lower variance = higher confidence
        confidence = max(0.1, min(1.0, 1.0 - (variance / 2500)))  # Normalize to 0.1-1.0
        
        return confidence
    
    def _generate_optimization_suggestions(
        self, 
        factor_scores: Dict[MemoryQualityFactor, float], 
        memory: VectorMemory, 
        _context: ConversationContext  # Reserved for context-specific suggestions
    ) -> List[str]:
        """
        Generate optimization suggestions based on factor scores.
        """
        suggestions = []
        
        # Check for low-scoring factors
        for factor, score in factor_scores.items():
            if score < 30:
                if factor == MemoryQualityFactor.SEMANTIC_RELEVANCE:
                    suggestions.append("Consider improving memory content specificity")
                elif factor == MemoryQualityFactor.TEMPORAL_FRESHNESS:
                    suggestions.append("Memory may need refreshing or archival")
                elif factor == MemoryQualityFactor.INTERACTION_FREQUENCY:
                    suggestions.append("Memory rarely accessed - consider tier demotion")
                elif factor == MemoryQualityFactor.EMOTIONAL_SIGNIFICANCE:
                    suggestions.append("Consider enhancing emotional context")
                elif factor == MemoryQualityFactor.RELATIONSHIP_CONTEXT:
                    suggestions.append("Memory may not fit current relationship level")
        
        # Memory tier suggestions
        if memory.memory_tier == MemoryTier.SHORT_TERM and factor_scores[MemoryQualityFactor.SEMANTIC_RELEVANCE] > 80:
            suggestions.append("Consider promoting to medium-term tier")
        
        return suggestions
    
    def _is_tier_promotion(self, current_tier: MemoryTier, recommended_tier: MemoryTier) -> bool:
        """Check if recommendation is a tier promotion."""
        tier_hierarchy = {
            MemoryTier.SHORT_TERM: 0,
            MemoryTier.MEDIUM_TERM: 1,
            MemoryTier.LONG_TERM: 2
        }
        return tier_hierarchy[recommended_tier] > tier_hierarchy[current_tier]
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Simple text similarity calculation as fallback."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        jaccard_similarity = intersection / union if union > 0 else 0.0
        return jaccard_similarity * 100
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get analyzer statistics and performance metrics."""
        return {
            'component': 'MemoryEffectivenessAnalyzer',
            'system': 'WhisperEngine Adaptive Learning',
            'statistics': self.stats.copy(),
            'factor_weights': self.default_factor_weights.copy(),
            'tier_thresholds': {tier.value: threshold for tier, threshold in self.tier_thresholds.items()},
            'timestamp': datetime.utcnow().isoformat()
        }


# Factory function for creating analyzer instances
def create_memory_effectiveness_analyzer(memory_manager=None, postgres_pool=None) -> MemoryEffectivenessAnalyzer:
    """
    Factory function to create MemoryEffectivenessAnalyzer instance.
    
    Args:
        memory_manager: Vector memory system for memory operations
        postgres_pool: PostgreSQL connection pool for effectiveness tracking
        
    Returns:
        MemoryEffectivenessAnalyzer instance
    """
    return MemoryEffectivenessAnalyzer(memory_manager=memory_manager, postgres_pool=postgres_pool)