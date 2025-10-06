"""
Vector Relevance Optimizer - Sprint 2: MemoryBoost

Optimizes vector memory retrieval by boosting effective memories and implementing
intelligent relevance scoring. Integrates with Memory Effectiveness Analyzer
to apply real-time optimizations based on conversation outcome analysis.

Core Features:
- Memory vector boosting/penalty system
- Dynamic relevance scoring
- Real-time vector weight adjustment
- Quality-based memory prioritization
- Integration with Qdrant vector operations

This component implements the "learning" aspect of MemoryBoost by dynamically
adjusting vector scores based on proven memory effectiveness patterns.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
from statistics import mean
import json

# Import Qdrant types for vector operations
from qdrant_client import models
from qdrant_client.http.models import PointStruct, NamedVector

# Import memory types from the main system
from src.memory.memory_effectiveness import (
    MemoryPattern, MemoryQualityScore, MemoryEffectivenessMetrics,
    ConversationOutcome
)

logger = logging.getLogger(__name__)


class OptimizationStrategy(Enum):
    """Vector optimization strategies"""
    BOOST_HIGH_PERFORMERS = "boost_high_performers"
    PENALIZE_LOW_PERFORMERS = "penalize_low_performers"
    BALANCED_OPTIMIZATION = "balanced_optimization"
    TEMPORAL_WEIGHTING = "temporal_weighting"
    CONTEXT_AWARE_BOOST = "context_aware_boost"


class VectorBoostType(Enum):
    """Types of vector boosts that can be applied"""
    SCORE_MULTIPLIER = "score_multiplier"        # Multiply similarity score
    RANKING_BOOST = "ranking_boost"              # Boost in final ranking
    THRESHOLD_ADJUSTMENT = "threshold_adjustment" # Adjust relevance threshold
    VECTOR_ENHANCEMENT = "vector_enhancement"     # Modify vector values directly


@dataclass
class VectorOptimization:
    """Vector optimization parameters"""
    memory_id: str
    boost_type: VectorBoostType
    boost_factor: float          # Multiplier (1.0 = no change, >1.0 = boost, <1.0 = penalty)
    confidence: float            # Confidence in optimization (0-1)
    reason: str                  # Human-readable reason
    pattern_match: MemoryPattern # Pattern that triggered optimization
    applied_at: datetime
    expires_at: Optional[datetime] = None


@dataclass
class RetrievalOptimization:
    """Optimization parameters for memory retrieval"""
    user_id: str
    bot_name: str
    boosted_patterns: List[MemoryPattern]
    penalized_patterns: List[MemoryPattern]
    quality_threshold: float
    max_results_adjustment: int  # Adjustment to default limit
    relevance_multipliers: Dict[str, float]  # memory_id -> multiplier
    temporal_decay_factor: float
    optimization_timestamp: datetime
    confidence: float


@dataclass
class OptimizationResult:
    """Result of applying vector optimizations"""
    original_results: List[Dict[str, Any]]
    optimized_results: List[Dict[str, Any]]
    optimizations_applied: List[VectorOptimization]
    performance_improvement: float  # Estimated improvement score
    optimization_count: int
    processing_time_ms: float


class VectorRelevanceOptimizer:
    """
    Optimizes vector memory retrieval by applying intelligent relevance scoring
    and memory boosting based on effectiveness analysis from MemoryEffectivenessAnalyzer.
    
    Implements real-time vector optimization without modifying stored vectors,
    using dynamic scoring adjustments during retrieval.
    """
    
    def __init__(self, memory_manager=None, effectiveness_analyzer=None):
        """
        Initialize vector relevance optimizer.
        
        Args:
            memory_manager: Vector memory system instance
            effectiveness_analyzer: MemoryEffectivenessAnalyzer instance
        """
        self.memory_manager = memory_manager
        self.effectiveness_analyzer = effectiveness_analyzer
        self.logger = logger
        
        # Optimization parameters
        self.max_boost_factor = 2.5
        self.max_penalty_factor = 0.3
        self.boost_threshold = 0.8
        self.penalty_threshold = 0.4
        self.optimization_cache_minutes = 30
        
        # Active optimizations cache
        self._optimization_cache = {}
        self._cache_timestamps = {}
        
        # Performance tracking
        self._optimization_stats = {
            'total_optimizations': 0,
            'successful_boosts': 0,
            'applied_penalties': 0,
            'avg_improvement': 0.0
        }
    
    async def optimize_memory_retrieval(
        self,
        user_id: str,
        bot_name: str,
        query: str,
        original_results: List[Dict[str, Any]],
        conversation_context: str = None
    ) -> OptimizationResult:
        """
        Apply intelligent optimizations to memory retrieval results.
        
        Args:
            user_id: User identifier
            bot_name: Bot name
            query: Search query
            original_results: Original memory retrieval results
            conversation_context: Current conversation context
            
        Returns:
            OptimizationResult with optimized memory rankings
        """
        start_time = datetime.now()
        
        try:
            self.logger.info("🎯 Applying memory retrieval optimizations for user %s", user_id)
            
            # Get optimization parameters
            optimization_params = await self._get_optimization_parameters(
                user_id, bot_name, conversation_context
            )
            
            # Apply various optimization strategies
            optimized_results = original_results.copy()
            applied_optimizations = []
            
            # 1. Quality-based boosting/penalties
            optimized_results, quality_opts = await self._apply_quality_optimizations(
                optimized_results, optimization_params
            )
            applied_optimizations.extend(quality_opts)
            
            # 2. Pattern-based boosting
            optimized_results, pattern_opts = await self._apply_pattern_optimizations(
                optimized_results, optimization_params, query
            )
            applied_optimizations.extend(pattern_opts)
            
            # 3. Temporal relevance adjustment
            optimized_results, temporal_opts = await self._apply_temporal_optimizations(
                optimized_results, optimization_params
            )
            applied_optimizations.extend(temporal_opts)
            
            # 4. Context-aware boosting
            optimized_results, context_opts = await self._apply_context_optimizations(
                optimized_results, optimization_params, conversation_context
            )
            applied_optimizations.extend(context_opts)
            
            # 5. Final ranking and filtering
            optimized_results = await self._apply_final_ranking(
                optimized_results, optimization_params
            )
            
            # Calculate performance metrics
            performance_improvement = self._calculate_performance_improvement(
                original_results, optimized_results, applied_optimizations
            )
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Update stats
            self._update_optimization_stats(applied_optimizations, performance_improvement)
            
            result = OptimizationResult(
                original_results=original_results,
                optimized_results=optimized_results,
                optimizations_applied=applied_optimizations,
                performance_improvement=performance_improvement,
                optimization_count=len(applied_optimizations),
                processing_time_ms=processing_time
            )
            
            self.logger.info("✅ Applied %d optimizations with %.2f%% improvement", 
                           len(applied_optimizations), performance_improvement * 100)
            
            return result
            
        except Exception as e:
            self.logger.error("Error optimizing memory retrieval: %s", str(e))
            return OptimizationResult(
                original_results=original_results,
                optimized_results=original_results,
                optimizations_applied=[],
                performance_improvement=0.0,
                optimization_count=0,
                processing_time_ms=0.0
            )
    
    async def boost_effective_memories(
        self,
        user_id: str,
        bot_name: str,
        pattern: MemoryPattern,
        boost_factor: float,
        reason: str = None
    ) -> List[VectorOptimization]:
        """
        Apply boost to memories matching specific effectiveness patterns.
        
        Args:
            user_id: User identifier
            bot_name: Bot name
            pattern: Memory pattern to boost
            boost_factor: Boost multiplier (>1.0 for boost, <1.0 for penalty)
            reason: Reason for optimization
            
        Returns:
            List of applied optimizations
        """
        try:
            if not self.effectiveness_analyzer:
                self.logger.warning("No effectiveness analyzer available for boosting")
                return []
            
            # Get memories matching pattern
            matching_memories = await self._get_memories_by_pattern(
                user_id, bot_name, pattern
            )
            
            optimizations = []
            for memory in matching_memories:
                optimization = VectorOptimization(
                    memory_id=memory['id'],
                    boost_type=VectorBoostType.SCORE_MULTIPLIER,
                    boost_factor=boost_factor,
                    confidence=0.8,
                    reason=reason or f"Pattern-based boost for {pattern.value}",
                    pattern_match=pattern,
                    applied_at=datetime.now(),
                    expires_at=datetime.now() + timedelta(hours=24)
                )
                optimizations.append(optimization)
            
            # Cache optimizations
            cache_key = f"{user_id}_{bot_name}_{pattern.value}"
            self._optimization_cache[cache_key] = optimizations
            self._cache_timestamps[cache_key] = datetime.now()
            
            self.logger.info("🚀 Boosted %d memories for pattern %s", 
                           len(optimizations), pattern.value)
            
            return optimizations
            
        except Exception as e:
            self.logger.error("Error boosting effective memories: %s", str(e))
            return []
    
    async def apply_quality_scoring(
        self,
        memory_results: List[Dict[str, Any]],
        user_id: str,
        bot_name: str
    ) -> List[Dict[str, Any]]:
        """
        Apply quality scoring to memory results using effectiveness analysis.
        
        Args:
            memory_results: List of memory retrieval results
            user_id: User identifier
            bot_name: Bot name
            
        Returns:
            Memory results with quality scores applied
        """
        try:
            if not self.effectiveness_analyzer or not memory_results:
                return memory_results
            
            scored_results = []
            
            for result in memory_results:
                # Get quality score for this memory
                quality_score = await self.effectiveness_analyzer.score_memory_quality(
                    memory_id=result.get('id', ''),
                    user_id=user_id,
                    bot_name=bot_name,
                    memory_content=result.get('content', ''),
                    memory_type=result.get('memory_type', 'conversation')
                )
                
                # Apply quality score to similarity score
                original_score = result.get('score', 0.0)
                quality_adjusted_score = original_score * quality_score.boost_factor
                
                # Add quality metadata
                enhanced_result = result.copy()
                enhanced_result.update({
                    'original_score': original_score,
                    'quality_score': quality_score.combined_score,
                    'boost_factor': quality_score.boost_factor,
                    'score': quality_adjusted_score,
                    'quality_metadata': {
                        'content_relevance': quality_score.content_relevance,
                        'outcome_correlation': quality_score.outcome_correlation,
                        'temporal_relevance': quality_score.temporal_relevance,
                        'emotional_impact': quality_score.emotional_impact
                    }
                })
                
                scored_results.append(enhanced_result)
            
            # Re-sort by adjusted scores
            scored_results.sort(key=lambda x: x.get('score', 0.0), reverse=True)
            
            return scored_results
            
        except Exception as e:
            self.logger.error("Error applying quality scoring: %s", str(e))
            return memory_results
    
    async def get_optimization_recommendations(
        self,
        user_id: str,
        bot_name: str,
        performance_window_days: int = 7
    ) -> Dict[str, Any]:
        """
        Get optimization recommendations based on recent performance analysis.
        
        Args:
            user_id: User identifier
            bot_name: Bot name
            performance_window_days: Days of performance data to analyze
            
        Returns:
            Dictionary with optimization recommendations
        """
        try:
            if not self.effectiveness_analyzer:
                return self._default_optimization_recommendations()
            
            # Get effectiveness metrics
            effectiveness_metrics = await self.effectiveness_analyzer.analyze_memory_performance(
                user_id, bot_name, performance_window_days
            )
            
            # Get memory optimization recommendations
            memory_recommendations = await self.effectiveness_analyzer.get_memory_optimization_recommendations(
                user_id, bot_name
            )
            
            # Generate vector-specific recommendations
            vector_recommendations = {
                'boost_strategies': self._generate_boost_strategies(effectiveness_metrics),
                'penalty_strategies': self._generate_penalty_strategies(effectiveness_metrics),
                'optimization_priorities': self._generate_optimization_priorities(effectiveness_metrics),
                'quality_thresholds': self._generate_quality_thresholds(effectiveness_metrics),
                'retrieval_adjustments': memory_recommendations.get('memory_limit_adjustment', 0),
                'temporal_settings': self._generate_temporal_settings(effectiveness_metrics),
                'confidence': memory_recommendations.get('confidence', 0.5),
                'last_updated': datetime.now()
            }
            
            return vector_recommendations
            
        except Exception as e:
            self.logger.error("Error getting optimization recommendations: %s", str(e))
            return self._default_optimization_recommendations()
    
    async def _get_optimization_parameters(
        self,
        user_id: str,
        bot_name: str,
        conversation_context: str
    ) -> RetrievalOptimization:
        """Get optimization parameters for current retrieval."""
        try:
            # Check cache first
            cache_key = f"{user_id}_{bot_name}"
            cached_params = self._get_cached_optimization_params(cache_key)
            if cached_params:
                return cached_params
            
            # Get fresh recommendations if no cache
            if self.effectiveness_analyzer:
                recommendations = await self.effectiveness_analyzer.get_memory_optimization_recommendations(
                    user_id, bot_name, conversation_context
                )
            else:
                recommendations = self._default_optimization_recommendations()
            
            # Convert to RetrievalOptimization
            params = RetrievalOptimization(
                user_id=user_id,
                bot_name=bot_name,
                boosted_patterns=recommendations.get('boost_patterns', []),
                penalized_patterns=recommendations.get('penalty_patterns', []),
                quality_threshold=recommendations.get('quality_threshold', 0.7),
                max_results_adjustment=recommendations.get('memory_limit_adjustment', 0),
                relevance_multipliers={},
                temporal_decay_factor=0.95,
                optimization_timestamp=datetime.now(),
                confidence=recommendations.get('confidence', 0.5)
            )
            
            # Cache params
            self._optimization_cache[cache_key] = params
            self._cache_timestamps[cache_key] = datetime.now()
            
            return params
            
        except Exception as e:
            self.logger.error("Error getting optimization parameters: %s", str(e))
            return self._default_retrieval_optimization(user_id, bot_name)
    
    async def _apply_quality_optimizations(
        self,
        results: List[Dict[str, Any]],
        params: RetrievalOptimization
    ) -> Tuple[List[Dict[str, Any]], List[VectorOptimization]]:
        """Apply quality-based optimizations."""
        try:
            optimizations = []
            
            for result in results:
                quality_metadata = result.get('quality_metadata', {})
                combined_score = quality_metadata.get('content_relevance', 0.5)
                
                boost_factor = 1.0
                reason = "Quality-based adjustment"
                
                if combined_score > self.boost_threshold:
                    boost_factor = min(self.max_boost_factor, 1.0 + (combined_score - self.boost_threshold) * 2.0)
                    reason = f"High quality boost (score: {combined_score:.2f})"
                elif combined_score < self.penalty_threshold:
                    boost_factor = max(self.max_penalty_factor, combined_score / self.penalty_threshold)
                    reason = f"Low quality penalty (score: {combined_score:.2f})"
                
                if boost_factor != 1.0:
                    result['score'] = result.get('score', 0.0) * boost_factor
                    
                    optimization = VectorOptimization(
                        memory_id=result.get('id', ''),
                        boost_type=VectorBoostType.SCORE_MULTIPLIER,
                        boost_factor=boost_factor,
                        confidence=0.8,
                        reason=reason,
                        pattern_match=MemoryPattern.CONVERSATION_HISTORY,  # Default
                        applied_at=datetime.now()
                    )
                    optimizations.append(optimization)
            
            return results, optimizations
            
        except Exception as e:
            self.logger.error("Error applying quality optimizations: %s", str(e))
            return results, []
    
    async def _apply_pattern_optimizations(
        self,
        results: List[Dict[str, Any]],
        params: RetrievalOptimization,
        query: str
    ) -> Tuple[List[Dict[str, Any]], List[VectorOptimization]]:
        """Apply pattern-based optimizations."""
        try:
            optimizations = []
            
            # Detect query patterns
            query_patterns = self._detect_query_patterns(query)
            
            for result in results:
                memory_type = result.get('memory_type', 'conversation')
                memory_pattern = self._map_memory_type_to_pattern(memory_type)
                
                boost_factor = 1.0
                reason = "Pattern-based adjustment"
                
                # Boost if pattern matches boosted patterns
                if memory_pattern in params.boosted_patterns:
                    boost_factor = 1.3
                    reason = f"Boosted pattern: {memory_pattern.value}"
                
                # Penalty if pattern matches penalized patterns
                elif memory_pattern in params.penalized_patterns:
                    boost_factor = 0.7
                    reason = f"Penalized pattern: {memory_pattern.value}"
                
                # Extra boost for query pattern match
                if memory_pattern in query_patterns:
                    boost_factor *= 1.2
                    reason += " + query pattern match"
                
                if boost_factor != 1.0:
                    result['score'] = result.get('score', 0.0) * boost_factor
                    
                    optimization = VectorOptimization(
                        memory_id=result.get('id', ''),
                        boost_type=VectorBoostType.SCORE_MULTIPLIER,
                        boost_factor=boost_factor,
                        confidence=0.7,
                        reason=reason,
                        pattern_match=memory_pattern,
                        applied_at=datetime.now()
                    )
                    optimizations.append(optimization)
            
            return results, optimizations
            
        except Exception as e:
            self.logger.error("Error applying pattern optimizations: %s", str(e))
            return results, []
    
    async def _apply_temporal_optimizations(
        self,
        results: List[Dict[str, Any]],
        params: RetrievalOptimization
    ) -> Tuple[List[Dict[str, Any]], List[VectorOptimization]]:
        """Apply temporal relevance optimizations."""
        try:
            optimizations = []
            current_time = datetime.now()
            
            for result in results:
                timestamp_str = result.get('timestamp')
                if not timestamp_str:
                    continue
                
                try:
                    memory_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    days_old = (current_time - memory_time).days
                    
                    # Apply temporal decay
                    temporal_factor = params.temporal_decay_factor ** days_old
                    
                    # Boost recent important memories
                    if days_old <= 1 and result.get('memory_type') in ['preference', 'relationship']:
                        temporal_factor *= 1.2
                    
                    if temporal_factor != 1.0:
                        result['score'] = result.get('score', 0.0) * temporal_factor
                        
                        optimization = VectorOptimization(
                            memory_id=result.get('id', ''),
                            boost_type=VectorBoostType.SCORE_MULTIPLIER,
                            boost_factor=temporal_factor,
                            confidence=0.9,
                            reason=f"Temporal adjustment ({days_old} days old)",
                            pattern_match=MemoryPattern.CONVERSATION_HISTORY,
                            applied_at=datetime.now()
                        )
                        optimizations.append(optimization)
                        
                except (ValueError, TypeError) as e:
                    self.logger.warning("Error parsing timestamp %s: %s", timestamp_str, str(e))
                    continue
            
            return results, optimizations
            
        except Exception as e:
            self.logger.error("Error applying temporal optimizations: %s", str(e))
            return results, []
    
    async def _apply_context_optimizations(
        self,
        results: List[Dict[str, Any]],
        params: RetrievalOptimization,
        conversation_context: str
    ) -> Tuple[List[Dict[str, Any]], List[VectorOptimization]]:
        """Apply context-aware optimizations."""
        try:
            optimizations = []
            
            if not conversation_context:
                return results, optimizations
            
            context_lower = conversation_context.lower()
            
            for result in results:
                content = result.get('content', '').lower()
                boost_factor = 1.0
                reason = "Context-aware adjustment"
                
                # Boost memories that match conversation context
                context_match_score = self._calculate_context_match(content, context_lower)
                
                if context_match_score > 0.7:
                    boost_factor = 1.0 + (context_match_score - 0.7) * 1.5
                    reason = f"High context match (score: {context_match_score:.2f})"
                
                if boost_factor != 1.0:
                    result['score'] = result.get('score', 0.0) * boost_factor
                    
                    optimization = VectorOptimization(
                        memory_id=result.get('id', ''),
                        boost_type=VectorBoostType.SCORE_MULTIPLIER,
                        boost_factor=boost_factor,
                        confidence=0.6,
                        reason=reason,
                        pattern_match=MemoryPattern.CONVERSATION_HISTORY,
                        applied_at=datetime.now()
                    )
                    optimizations.append(optimization)
            
            return results, optimizations
            
        except Exception as e:
            self.logger.error("Error applying context optimizations: %s", str(e))
            return results, []
    
    async def _apply_final_ranking(
        self,
        results: List[Dict[str, Any]],
        params: RetrievalOptimization
    ) -> List[Dict[str, Any]]:
        """Apply final ranking and filtering."""
        try:
            # Filter by quality threshold
            filtered_results = [
                result for result in results
                if result.get('score', 0.0) >= params.quality_threshold
            ]
            
            # Sort by final score
            filtered_results.sort(key=lambda x: x.get('score', 0.0), reverse=True)
            
            # Apply limit adjustment
            base_limit = len(results)
            adjusted_limit = max(1, base_limit + params.max_results_adjustment)
            
            return filtered_results[:adjusted_limit]
            
        except Exception as e:
            self.logger.error("Error applying final ranking: %s", str(e))
            return results
    
    def _calculate_performance_improvement(
        self,
        original_results: List[Dict[str, Any]],
        optimized_results: List[Dict[str, Any]],
        optimizations: List[VectorOptimization]
    ) -> float:
        """Calculate estimated performance improvement."""
        try:
            if not optimizations:
                return 0.0
            
            # Calculate score improvements
            original_scores = [r.get('score', 0.0) for r in original_results[:10]]
            optimized_scores = [r.get('score', 0.0) for r in optimized_results[:10]]
            
            if not original_scores or not optimized_scores:
                return 0.0
            
            original_avg = mean(original_scores)
            optimized_avg = mean(optimized_scores)
            
            if original_avg > 0:
                improvement = (optimized_avg - original_avg) / original_avg
            else:
                improvement = 0.0
            
            # Weight by optimization confidence
            confidence_weight = mean([opt.confidence for opt in optimizations])
            
            return improvement * confidence_weight
            
        except Exception as e:
            self.logger.error("Error calculating performance improvement: %s", str(e))
            return 0.0
    
    def _update_optimization_stats(
        self,
        optimizations: List[VectorOptimization],
        performance_improvement: float
    ) -> None:
        """Update optimization statistics."""
        try:
            self._optimization_stats['total_optimizations'] += len(optimizations)
            
            for opt in optimizations:
                if opt.boost_factor > 1.0:
                    self._optimization_stats['successful_boosts'] += 1
                elif opt.boost_factor < 1.0:
                    self._optimization_stats['applied_penalties'] += 1
            
            # Update average improvement (simple moving average)
            current_avg = self._optimization_stats['avg_improvement']
            total_opts = self._optimization_stats['total_optimizations']
            
            if total_opts > 0:
                self._optimization_stats['avg_improvement'] = (
                    (current_avg * (total_opts - len(optimizations)) + performance_improvement * len(optimizations)) / total_opts
                )
            
        except Exception as e:
            self.logger.error("Error updating optimization stats: %s", str(e))
    
    async def _get_memories_by_pattern(
        self,
        user_id: str,
        bot_name: str,
        pattern: MemoryPattern
    ) -> List[Dict[str, Any]]:
        """Get memories matching a specific pattern."""
        # This would integrate with the memory manager to find memories by pattern
        # For now, return empty list as placeholder
        return []
    
    def _get_cached_optimization_params(self, cache_key: str) -> Optional[RetrievalOptimization]:
        """Get cached optimization parameters if still valid."""
        try:
            if cache_key not in self._optimization_cache:
                return None
            
            cache_time = self._cache_timestamps.get(cache_key)
            if not cache_time:
                return None
            
            if (datetime.now() - cache_time).total_seconds() > (self.optimization_cache_minutes * 60):
                # Cache expired
                del self._optimization_cache[cache_key]
                del self._cache_timestamps[cache_key]
                return None
            
            return self._optimization_cache[cache_key]
            
        except Exception as e:
            self.logger.error("Error getting cached optimization params: %s", str(e))
            return None
    
    def _detect_query_patterns(self, query: str) -> List[MemoryPattern]:
        """Detect memory patterns relevant to the query."""
        patterns = []
        query_lower = query.lower()
        
        # Simple pattern detection based on keywords
        if any(word in query_lower for word in ['remember', 'recall', 'before', 'previously']):
            patterns.append(MemoryPattern.CONVERSATION_HISTORY)
        
        if any(word in query_lower for word in ['feel', 'emotion', 'mood', 'happy', 'sad']):
            patterns.append(MemoryPattern.EMOTIONAL_CONTEXT)
        
        if any(word in query_lower for word in ['like', 'prefer', 'favorite', 'enjoy']):
            patterns.append(MemoryPattern.PREFERENCE_MEMORY)
        
        if any(word in query_lower for word in ['relationship', 'friend', 'family', 'partner']):
            patterns.append(MemoryPattern.RELATIONSHIP_CONTEXT)
        
        if any(word in query_lower for word in ['fact', 'information', 'data', 'technical']):
            patterns.append(MemoryPattern.FACTUAL_RECALL)
        
        return patterns
    
    def _map_memory_type_to_pattern(self, memory_type: str) -> MemoryPattern:
        """Map memory type to memory pattern."""
        mapping = {
            'conversation': MemoryPattern.CONVERSATION_HISTORY,
            'fact': MemoryPattern.FACTUAL_RECALL,
            'preference': MemoryPattern.PREFERENCE_MEMORY,
            'relationship': MemoryPattern.RELATIONSHIP_CONTEXT,
            'context': MemoryPattern.EMOTIONAL_CONTEXT,
            'correction': MemoryPattern.FACTUAL_RECALL
        }
        
        return mapping.get(memory_type, MemoryPattern.CONVERSATION_HISTORY)
    
    def _calculate_context_match(self, content: str, context: str) -> float:
        """Calculate simple context match score."""
        try:
            content_words = set(content.split())
            context_words = set(context.split())
            
            if not context_words:
                return 0.0
            
            intersection = content_words & context_words
            return len(intersection) / len(context_words)
            
        except Exception as e:
            self.logger.error("Error calculating context match: %s", str(e))
            return 0.0
    
    def _generate_boost_strategies(
        self,
        effectiveness_metrics: Dict[MemoryPattern, MemoryEffectivenessMetrics]
    ) -> List[Dict[str, Any]]:
        """Generate boost strategies based on effectiveness metrics."""
        strategies = []
        
        for pattern, metrics in effectiveness_metrics.items():
            if metrics.success_rate > self.boost_threshold:
                strategies.append({
                    'pattern': pattern,
                    'boost_factor': min(self.max_boost_factor, 1.0 + metrics.improvement_factor * 0.5),
                    'confidence': metrics.success_rate,
                    'reason': f"High success rate: {metrics.success_rate:.2f}"
                })
        
        return strategies
    
    def _generate_penalty_strategies(
        self,
        effectiveness_metrics: Dict[MemoryPattern, MemoryEffectivenessMetrics]
    ) -> List[Dict[str, Any]]:
        """Generate penalty strategies based on effectiveness metrics."""
        strategies = []
        
        for pattern, metrics in effectiveness_metrics.items():
            if metrics.success_rate < self.penalty_threshold:
                strategies.append({
                    'pattern': pattern,
                    'penalty_factor': max(self.max_penalty_factor, metrics.success_rate),
                    'confidence': 1.0 - metrics.success_rate,
                    'reason': f"Low success rate: {metrics.success_rate:.2f}"
                })
        
        return strategies
    
    def _generate_optimization_priorities(
        self,
        effectiveness_metrics: Dict[MemoryPattern, MemoryEffectivenessMetrics]
    ) -> List[Dict[str, Any]]:
        """Generate optimization priorities."""
        priorities = []
        
        for pattern, metrics in effectiveness_metrics.items():
            priority_score = metrics.improvement_factor * metrics.success_rate
            priorities.append({
                'pattern': pattern,
                'priority_score': priority_score,
                'usage_count': metrics.usage_count,
                'improvement_potential': metrics.improvement_factor
            })
        
        priorities.sort(key=lambda x: x['priority_score'], reverse=True)
        return priorities
    
    def _generate_quality_thresholds(
        self,
        effectiveness_metrics: Dict[MemoryPattern, MemoryEffectivenessMetrics]
    ) -> Dict[str, float]:
        """Generate quality thresholds based on performance."""
        if not effectiveness_metrics:
            return {'default': 0.7}
        
        avg_success_rate = mean([m.success_rate for m in effectiveness_metrics.values()])
        
        return {
            'default': max(0.3, min(0.9, avg_success_rate * 0.8)),
            'high_performers': avg_success_rate * 0.6,
            'low_performers': avg_success_rate * 1.2
        }
    
    def _generate_temporal_settings(
        self,
        effectiveness_metrics: Dict[MemoryPattern, MemoryEffectivenessMetrics]
    ) -> Dict[str, float]:
        """Generate temporal optimization settings."""
        return {
            'decay_factor': 0.95,
            'recent_boost': 1.2,
            'recency_threshold_days': 3,
            'temporal_weight': 0.15
        }
    
    def _default_optimization_recommendations(self) -> Dict[str, Any]:
        """Return default optimization recommendations."""
        return {
            'boost_strategies': [],
            'penalty_strategies': [],
            'optimization_priorities': [],
            'quality_thresholds': {'default': 0.7},
            'retrieval_adjustments': 0,
            'temporal_settings': self._generate_temporal_settings({}),
            'confidence': 0.5,
            'last_updated': datetime.now()
        }
    
    def _default_retrieval_optimization(self, user_id: str, bot_name: str) -> RetrievalOptimization:
        """Return default retrieval optimization parameters."""
        return RetrievalOptimization(
            user_id=user_id,
            bot_name=bot_name,
            boosted_patterns=[MemoryPattern.CONVERSATION_HISTORY],
            penalized_patterns=[],
            quality_threshold=0.7,
            max_results_adjustment=0,
            relevance_multipliers={},
            temporal_decay_factor=0.95,
            optimization_timestamp=datetime.now(),
            confidence=0.5
        )


# Factory function for dependency injection
def create_vector_relevance_optimizer(
    memory_manager=None,
    effectiveness_analyzer=None
) -> VectorRelevanceOptimizer:
    """
    Factory function to create VectorRelevanceOptimizer instance.
    
    Args:
        memory_manager: Vector memory system instance
        effectiveness_analyzer: MemoryEffectivenessAnalyzer instance
        
    Returns:
        Configured VectorRelevanceOptimizer instance
    """
    return VectorRelevanceOptimizer(
        memory_manager=memory_manager,
        effectiveness_analyzer=effectiveness_analyzer
    )