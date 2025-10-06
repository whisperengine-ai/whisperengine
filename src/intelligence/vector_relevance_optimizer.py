"""
MemoryBoost: Vector Relevance Optimizer

Optimizes vector search relevance through intelligent ranking and filtering.
Enhances WhisperEngine's vector memory system with dynamic relevance scoring,
memory tier-aware prioritization, and bot-specific relevance tuning.

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


class RelevanceOptimizationMode(Enum):
    """Optimization modes for different conversation types"""
    CONVERSATION = "conversation"    # General conversation optimization
    FACTUAL = "factual"             # Fact-focused queries
    EMOTIONAL = "emotional"         # Emotion-focused interactions
    RELATIONSHIP = "relationship"   # Relationship-building contexts
    TECHNICAL = "technical"         # Technical/specific queries


@dataclass
class RelevanceScore:
    """Enhanced relevance scoring with multiple factors"""
    memory_id: str
    base_similarity: float          # Original vector similarity
    enhanced_relevance: float       # Optimized relevance score
    tier_boost: float              # Memory tier adjustment
    recency_factor: float          # Temporal relevance
    emotional_alignment: float     # Emotional context matching
    relationship_fit: float        # Relationship appropriateness
    final_score: float             # Combined final relevance score
    optimization_factors: Dict[str, float]
    confidence: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for analysis"""
        return {
            'memory_id': self.memory_id,
            'base_similarity': self.base_similarity,
            'enhanced_relevance': self.enhanced_relevance,
            'tier_boost': self.tier_boost,
            'recency_factor': self.recency_factor,
            'emotional_alignment': self.emotional_alignment,
            'relationship_fit': self.relationship_fit,
            'final_score': self.final_score,
            'optimization_factors': self.optimization_factors,
            'confidence': self.confidence
        }


@dataclass
class OptimizationContext:
    """Context for relevance optimization"""
    user_id: str
    bot_name: str
    query: str
    conversation_history: List[Dict[str, Any]]
    optimization_mode: RelevanceOptimizationMode
    relationship_depth: Optional[str] = None
    emotional_state: Optional[str] = None
    character_preferences: Optional[Dict[str, Any]] = None


class VectorRelevanceOptimizer:
    """
    Optimizes vector search relevance through intelligent ranking and filtering.
    
    Core functionality:
    - Dynamic relevance scoring with multiple factors
    - Memory tier-aware prioritization (short/medium/long-term)
    - Semantic similarity enhancement
    - Bot-specific relevance tuning
    - Character personality-aware optimization
    """
    
    def __init__(self, memory_manager=None, postgres_pool=None):
        """
        Initialize vector relevance optimizer.
        
        Args:
            memory_manager: Vector memory system for similarity operations
            postgres_pool: PostgreSQL connection pool for optimization tracking
        """
        self.memory_manager = memory_manager
        self.postgres_pool = postgres_pool
        
        # Optimization factor weights (tunable per character/mode)
        self.default_factor_weights = {
            'semantic_similarity': 0.40,
            'emotional_alignment': 0.25,
            'relationship_appropriateness': 0.20,
            'temporal_relevance': 0.15
        }
        
        # Memory tier boost factors
        self.tier_boost_factors = {
            MemoryTier.LONG_TERM: 1.2,    # Boost important memories
            MemoryTier.MEDIUM_TERM: 1.0,  # Standard weighting
            MemoryTier.SHORT_TERM: 0.8    # Slight reduction for recent
        }
        
        # Optimization mode configurations
        self.mode_configurations = {
            RelevanceOptimizationMode.CONVERSATION: {
                'semantic_similarity': 0.35,
                'emotional_alignment': 0.30,
                'relationship_appropriateness': 0.20,
                'temporal_relevance': 0.15
            },
            RelevanceOptimizationMode.FACTUAL: {
                'semantic_similarity': 0.60,
                'emotional_alignment': 0.10,
                'relationship_appropriateness': 0.15,
                'temporal_relevance': 0.15
            },
            RelevanceOptimizationMode.EMOTIONAL: {
                'semantic_similarity': 0.25,
                'emotional_alignment': 0.50,
                'relationship_appropriateness': 0.15,
                'temporal_relevance': 0.10
            },
            RelevanceOptimizationMode.RELATIONSHIP: {
                'semantic_similarity': 0.30,
                'emotional_alignment': 0.25,
                'relationship_appropriateness': 0.35,
                'temporal_relevance': 0.10
            },
            RelevanceOptimizationMode.TECHNICAL: {
                'semantic_similarity': 0.70,
                'emotional_alignment': 0.05,
                'relationship_appropriateness': 0.10,
                'temporal_relevance': 0.15
            }
        }
        
        # Statistics tracking
        self.stats = {
            'optimizations_performed': 0,
            'relevance_improvements': 0,
            'tier_boosts_applied': 0,
            'mode_optimizations': {mode.value: 0 for mode in RelevanceOptimizationMode}
        }
        
        logger.info("VectorRelevanceOptimizer initialized with adaptive scoring system")
    
    @handle_errors(category=ErrorCategory.MEMORY_SYSTEM, severity=ErrorSeverity.MEDIUM)
    async def optimize_relevance_scores(
        self,
        memories: List[VectorMemory],
        base_similarities: List[float],
        context: OptimizationContext,
        factor_weights: Optional[Dict[str, float]] = None
    ) -> List[RelevanceScore]:
        """
        Optimize relevance scores for a list of memories.
        
        Args:
            memories: List of memories to optimize
            base_similarities: Original vector similarity scores
            context: Optimization context
            factor_weights: Custom factor weights (optional)
            
        Returns:
            List of RelevanceScore objects with optimized scores
        """
        if len(memories) != len(base_similarities):
            raise ValueError("Memories and similarities lists must have same length")
        
        # Get factor weights for optimization mode
        weights = factor_weights or self.mode_configurations.get(
            context.optimization_mode, 
            self.default_factor_weights
        )
        
        # Create optimization tasks for parallel execution
        optimization_tasks = [
            self._optimize_single_memory(memory, base_similarities[i], context, weights)
            for i, memory in enumerate(memories)
        ]
        
        # Execute optimizations in parallel
        relevance_scores = await asyncio.gather(*optimization_tasks, return_exceptions=True)
        
        # Filter out exceptions and log errors
        valid_scores = []
        for i, result in enumerate(relevance_scores):
            if isinstance(result, Exception):
                logger.error("Relevance optimization failed for %s: %s", memories[i].id, result)
                # Create fallback score
                fallback_score = RelevanceScore(
                    memory_id=memories[i].id,
                    base_similarity=base_similarities[i],
                    enhanced_relevance=base_similarities[i],
                    tier_boost=1.0,
                    recency_factor=1.0,
                    emotional_alignment=0.5,
                    relationship_fit=0.5,
                    final_score=base_similarities[i],
                    optimization_factors={},
                    confidence=0.5
                )
                valid_scores.append(fallback_score)
            else:
                valid_scores.append(result)
        
        # Update statistics
        self.stats['optimizations_performed'] += len(valid_scores)
        self.stats['mode_optimizations'][context.optimization_mode.value] += 1
        
        # Count relevance improvements (where final > base)
        improvements = sum(1 for score in valid_scores if score.final_score > score.base_similarity)
        self.stats['relevance_improvements'] += improvements
        
        logger.info("Relevance optimization complete: %d memories processed, %d improvements", 
                   len(valid_scores), improvements)
        
        return valid_scores
    
    async def _optimize_single_memory(
        self,
        memory: VectorMemory,
        base_similarity: float,
        context: OptimizationContext,
        weights: Dict[str, float]
    ) -> RelevanceScore:
        """
        Optimize relevance score for a single memory.
        
        Args:
            memory: Memory to optimize
            base_similarity: Original vector similarity
            context: Optimization context
            weights: Factor weights for optimization
            
        Returns:
            RelevanceScore with optimized scoring
        """
        # Calculate optimization factors
        tier_boost = self._calculate_tier_boost(memory, context)
        recency_factor = self._calculate_recency_factor(memory, context)
        emotional_alignment = await self._calculate_emotional_alignment(memory, context)
        relationship_fit = self._calculate_relationship_fit(memory, context)
        
        # Apply weighted optimization
        optimization_factors = {
            'tier_boost': tier_boost,
            'recency_factor': recency_factor,
            'emotional_alignment': emotional_alignment,
            'relationship_fit': relationship_fit
        }
        
        # Calculate enhanced relevance
        enhanced_relevance = (
            base_similarity * weights['semantic_similarity'] +
            emotional_alignment * weights['emotional_alignment'] +
            relationship_fit * weights['relationship_appropriateness'] +
            recency_factor * weights['temporal_relevance']
        )
        
        # Apply tier boost
        tier_boosted_score = enhanced_relevance * tier_boost
        
        # Calculate final score with normalization
        final_score = min(1.0, max(0.0, tier_boosted_score))
        
        # Calculate confidence based on factor consistency
        confidence = self._calculate_optimization_confidence(optimization_factors, weights)
        
        # Track tier boosts
        if tier_boost > 1.0:
            self.stats['tier_boosts_applied'] += 1
        
        return RelevanceScore(
            memory_id=memory.id,
            base_similarity=base_similarity,
            enhanced_relevance=enhanced_relevance,
            tier_boost=tier_boost,
            recency_factor=recency_factor,
            emotional_alignment=emotional_alignment,
            relationship_fit=relationship_fit,
            final_score=final_score,
            optimization_factors=optimization_factors,
            confidence=confidence
        )
    
    def _calculate_tier_boost(self, memory: VectorMemory, _context: OptimizationContext) -> float:
        """
        Calculate tier-based relevance boost.
        
        Long-term memories get higher priority for retrieval.
        """
        return self.tier_boost_factors.get(memory.memory_tier, 1.0)
    
    def _calculate_recency_factor(self, memory: VectorMemory, context: OptimizationContext) -> float:
        """
        Calculate recency-based relevance factor.
        
        Different optimization modes weight recency differently.
        """
        if not memory.timestamp:
            return 0.5  # Neutral for missing timestamp
        
        # Calculate age in days
        age_days = (datetime.utcnow() - memory.timestamp).total_seconds() / 86400
        
        # Mode-specific recency importance
        recency_importance = {
            RelevanceOptimizationMode.CONVERSATION: 0.8,  # Moderate recency importance
            RelevanceOptimizationMode.FACTUAL: 0.4,      # Low recency importance
            RelevanceOptimizationMode.EMOTIONAL: 0.9,    # High recency importance
            RelevanceOptimizationMode.RELATIONSHIP: 0.3, # Low recency importance
            RelevanceOptimizationMode.TECHNICAL: 0.6     # Moderate recency importance
        }
        
        importance = recency_importance.get(context.optimization_mode, 0.7)
        
        # Exponential decay with mode-specific half-life
        half_life_days = 30 if importance > 0.7 else 90  # Shorter half-life for recency-important modes
        recency_score = math.exp(-0.693 * age_days / half_life_days)
        
        # Blend with neutral (0.5) based on importance
        return 0.5 + (recency_score - 0.5) * importance
    
    async def _calculate_emotional_alignment(
        self, 
        memory: VectorMemory, 
        context: OptimizationContext
    ) -> float:
        """
        Calculate emotional alignment between memory and current context.
        
        Uses stored emotion data for matching.
        """
        # Extract emotional data from memory
        memory_emotion_data = memory.metadata.get('emotion_data', {}) if memory.metadata else {}
        memory_emotion = memory_emotion_data.get('primary_emotion', 'neutral')
        memory_intensity = memory_emotion_data.get('intensity', 0.5)
        
        # Current emotional state from context
        current_emotion = context.emotional_state or 'neutral'
        
        # Emotional compatibility matrix
        emotion_compatibility = {
            'joy': {'joy': 1.0, 'excitement': 0.8, 'contentment': 0.7, 'neutral': 0.5, 'sadness': 0.2},
            'sadness': {'sadness': 1.0, 'melancholy': 0.8, 'disappointment': 0.7, 'neutral': 0.5, 'joy': 0.2},
            'anger': {'anger': 1.0, 'frustration': 0.8, 'irritation': 0.7, 'neutral': 0.5, 'joy': 0.3},
            'fear': {'fear': 1.0, 'anxiety': 0.8, 'worry': 0.7, 'neutral': 0.5, 'confidence': 0.2},
            'surprise': {'surprise': 1.0, 'amazement': 0.8, 'curiosity': 0.7, 'neutral': 0.6},
            'neutral': {'neutral': 1.0, 'calm': 0.8}
        }
        
        # Get compatibility score
        memory_emotions = emotion_compatibility.get(memory_emotion, {})
        base_compatibility = memory_emotions.get(current_emotion, 0.5)
        
        # Adjust for emotional intensity
        intensity_factor = 0.5 + (memory_intensity * 0.5)
        
        # Mode-specific emotional weight
        mode_emotional_weights = {
            RelevanceOptimizationMode.EMOTIONAL: 1.0,    # Full emotional alignment
            RelevanceOptimizationMode.RELATIONSHIP: 0.8, # High emotional importance
            RelevanceOptimizationMode.CONVERSATION: 0.6, # Moderate emotional importance
            RelevanceOptimizationMode.FACTUAL: 0.2,     # Low emotional importance
            RelevanceOptimizationMode.TECHNICAL: 0.1    # Minimal emotional importance
        }
        
        mode_weight = mode_emotional_weights.get(context.optimization_mode, 0.5)
        
        # Calculate final emotional alignment
        alignment = base_compatibility * intensity_factor * mode_weight
        
        # Ensure neutral baseline for non-emotional modes
        if mode_weight < 0.3:
            alignment = 0.5 + (alignment - 0.5) * mode_weight * 2
        
        return max(0.0, min(1.0, alignment))
    
    def _calculate_relationship_fit(self, memory: VectorMemory, context: OptimizationContext) -> float:
        """
        Calculate how well memory fits current relationship context.
        
        Considers relationship depth and memory appropriateness.
        """
        # Default relationship depth if not provided
        relationship_depth = context.relationship_depth or "friend"
        
        # Memory relationship metadata
        memory_relationship_level = memory.metadata.get('relationship_level') if memory.metadata else None
        
        # Relationship appropriateness scoring
        relationship_scores = {
            'acquaintance': {'acquaintance': 1.0, 'friend': 0.8, 'close': 0.6, 'intimate': 0.4},
            'friend': {'acquaintance': 0.7, 'friend': 1.0, 'close': 0.9, 'intimate': 0.7},
            'close': {'acquaintance': 0.5, 'friend': 0.8, 'close': 1.0, 'intimate': 0.9},
            'intimate': {'acquaintance': 0.3, 'friend': 0.6, 'close': 0.9, 'intimate': 1.0}
        }
        
        if memory_relationship_level and memory_relationship_level in relationship_scores:
            base_fit = relationship_scores[relationship_depth].get(memory_relationship_level, 0.75)
        else:
            # Memory type relationship appropriateness as fallback
            type_relationship_scores = {
                MemoryType.CONVERSATION: 0.85,    # Generally appropriate
                MemoryType.RELATIONSHIP: 0.95,    # Highly relevant
                MemoryType.PREFERENCE: 0.80,      # Moderately relevant
                MemoryType.FACT: 0.70,           # Context dependent
                MemoryType.CONTEXT: 0.75,        # Context dependent
                MemoryType.CORRECTION: 0.90      # Important for accuracy
            }
            base_fit = type_relationship_scores.get(memory.memory_type, 0.75)
        
        # Mode-specific relationship importance
        mode_relationship_weights = {
            RelevanceOptimizationMode.RELATIONSHIP: 1.0, # Full relationship awareness
            RelevanceOptimizationMode.CONVERSATION: 0.8, # High relationship importance
            RelevanceOptimizationMode.EMOTIONAL: 0.7,    # Moderate relationship importance
            RelevanceOptimizationMode.FACTUAL: 0.3,     # Low relationship importance
            RelevanceOptimizationMode.TECHNICAL: 0.2    # Minimal relationship importance
        }
        
        mode_weight = mode_relationship_weights.get(context.optimization_mode, 0.6)
        
        # Apply mode weighting with neutral baseline
        relationship_fit = 0.5 + (base_fit - 0.5) * mode_weight
        
        return max(0.0, min(1.0, relationship_fit))
    
    def _calculate_optimization_confidence(
        self, 
        factors: Dict[str, float], 
        _weights: Dict[str, float]  # Reserved for weighted confidence calculation
    ) -> float:
        """
        Calculate confidence in the optimization based on factor consistency.
        """
        factor_values = list(factors.values())
        if not factor_values:
            return 0.5
        
        # Calculate variance in optimization factors
        mean_factor = sum(factor_values) / len(factor_values)
        variance = sum((factor - mean_factor) ** 2 for factor in factor_values) / len(factor_values)
        
        # Lower variance = higher confidence
        confidence = max(0.1, min(1.0, 1.0 - variance))
        
        return confidence
    
    @handle_errors(category=ErrorCategory.MEMORY_SYSTEM, severity=ErrorSeverity.LOW)
    async def rank_memories_by_relevance(
        self,
        relevance_scores: List[RelevanceScore],
        max_results: Optional[int] = None
    ) -> List[RelevanceScore]:
        """
        Rank memories by optimized relevance scores.
        
        Args:
            relevance_scores: List of relevance scores to rank
            max_results: Maximum number of results to return
            
        Returns:
            Ranked list of relevance scores
        """
        # Sort by final score (descending)
        ranked_scores = sorted(relevance_scores, key=lambda x: x.final_score, reverse=True)
        
        # Apply result limit if specified
        if max_results and max_results > 0:
            ranked_scores = ranked_scores[:max_results]
        
        logger.debug("Ranked %d memories by relevance score", len(ranked_scores))
        return ranked_scores
    
    def get_optimization_mode(self, query: str, _context: OptimizationContext) -> RelevanceOptimizationMode:
        """
        Automatically determine optimization mode based on query and context.
        
        Args:
            query: User query text
            context: Optimization context
            
        Returns:
            Appropriate RelevanceOptimizationMode
        """
        query_lower = query.lower()
        
        # Technical keywords
        technical_keywords = ['code', 'function', 'algorithm', 'debug', 'error', 'implement', 'syntax']
        if any(keyword in query_lower for keyword in technical_keywords):
            return RelevanceOptimizationMode.TECHNICAL
        
        # Emotional keywords
        emotional_keywords = ['feel', 'emotion', 'sad', 'happy', 'angry', 'excited', 'worried', 'love']
        if any(keyword in query_lower for keyword in emotional_keywords):
            return RelevanceOptimizationMode.EMOTIONAL
        
        # Factual keywords
        factual_keywords = ['what', 'when', 'where', 'who', 'how', 'explain', 'define', 'tell me about']
        if any(keyword in query_lower for keyword in factual_keywords):
            return RelevanceOptimizationMode.FACTUAL
        
        # Relationship keywords
        relationship_keywords = ['relationship', 'friend', 'together', 'bond', 'trust', 'close']
        if any(keyword in query_lower for keyword in relationship_keywords):
            return RelevanceOptimizationMode.RELATIONSHIP
        
        # Default to conversation mode
        return RelevanceOptimizationMode.CONVERSATION
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get optimizer statistics and performance metrics."""
        return {
            'component': 'VectorRelevanceOptimizer',
            'system': 'WhisperEngine Adaptive Learning',
            'statistics': self.stats.copy(),
            'factor_weights': self.default_factor_weights.copy(),
            'tier_boost_factors': {tier.value: factor for tier, factor in self.tier_boost_factors.items()},
            'mode_configurations': {mode.value: config for mode, config in self.mode_configurations.items()},
            'timestamp': datetime.utcnow().isoformat()
        }


# Factory function for creating optimizer instances
def create_vector_relevance_optimizer(memory_manager=None, postgres_pool=None) -> VectorRelevanceOptimizer:
    """
    Factory function to create VectorRelevanceOptimizer instance.
    
    Args:
        memory_manager: Vector memory system for similarity operations
        postgres_pool: PostgreSQL connection pool for optimization tracking
        
    Returns:
        VectorRelevanceOptimizer instance
    """
    return VectorRelevanceOptimizer(memory_manager=memory_manager, postgres_pool=postgres_pool)