"""
MemoryBoost Integration Module

Integrates memory effectiveness analysis, vector relevance optimization,
and relationship intelligence into WhisperEngine's message processing pipeline.

Part of the WhisperEngine Adaptive Learning System.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# WhisperEngine core imports
from src.memory.vector_memory_system import VectorMemory
from src.utils.production_error_handler import handle_errors, ErrorCategory, ErrorSeverity

# Sprint 2 MemoryBoost components
from src.intelligence.memory_effectiveness_analyzer import (
    create_memory_effectiveness_analyzer,
    MemoryQualityScore,
    ConversationContext,
    MemoryQualityFactor
)
from src.intelligence.vector_relevance_optimizer import (
    create_vector_relevance_optimizer,
    RelevanceScore,
    OptimizationContext
)
from src.intelligence.relationship_intelligence_manager import (
    create_relationship_intelligence_manager,
    RelationshipMetrics,
    InteractionContext
)

logger = logging.getLogger(__name__)


@dataclass
class MemoryBoostResult:
    """Result of MemoryBoost processing with enhanced memory intelligence"""
    optimized_memories: List[VectorMemory]
    relevance_scores: List[RelevanceScore]
    quality_scores: List[MemoryQualityScore]
    relationship_metrics: Optional[RelationshipMetrics]
    optimization_summary: Dict[str, Any]
    processing_time_ms: float
    improvements_applied: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for analysis and logging"""
        return {
            'optimized_memory_count': len(self.optimized_memories),
            'avg_relevance_score': sum(score.final_score for score in self.relevance_scores) / len(self.relevance_scores) if self.relevance_scores else 0,
            'avg_quality_score': sum(score.overall_score for score in self.quality_scores) / len(self.quality_scores) if self.quality_scores else 0,
            'relationship_depth': self.relationship_metrics.relationship_depth.value if self.relationship_metrics else None,
            'relationship_score': self.relationship_metrics.depth_score if self.relationship_metrics else None,
            'optimization_summary': self.optimization_summary,
            'processing_time_ms': self.processing_time_ms,
            'improvements_applied': self.improvements_applied
        }


class MemoryBoostIntegrator:
    """
    Integrates MemoryBoost components for enhanced memory intelligence.
    
    Core functionality:
    - Memory effectiveness analysis and scoring
    - Vector relevance optimization with multiple factors
    - Relationship intelligence tracking and progression
    - Integrated memory retrieval with quality prioritization
    - Performance optimization and caching
    """
    
    def __init__(self, memory_manager=None, postgres_pool=None):
        """
        Initialize MemoryBoost integrator with all components.
        
        Args:
            memory_manager: Vector memory system for memory operations
            postgres_pool: PostgreSQL connection pool for intelligence storage
        """
        self.memory_manager = memory_manager
        self.postgres_pool = postgres_pool
        
        # Initialize MemoryBoost components
        self.effectiveness_analyzer = create_memory_effectiveness_analyzer(
            memory_manager=memory_manager,
            postgres_pool=postgres_pool
        )
        
        self.relevance_optimizer = create_vector_relevance_optimizer(
            memory_manager=memory_manager,
            postgres_pool=postgres_pool
        )
        
        self.relationship_manager = create_relationship_intelligence_manager(
            postgres_pool=postgres_pool,
            memory_manager=memory_manager
        )
        
        # Performance tracking
        self.stats = {
            'boost_operations': 0,
            'memory_improvements': 0,
            'relationship_progressions': 0,
            'optimization_cache_hits': 0,
            'total_processing_time_ms': 0
        }
        
        # Simple caching for optimization results
        self._optimization_cache = {}
        self._cache_max_size = 100
        
        logger.info("MemoryBoostIntegrator initialized with all components")
    
    @handle_errors(category=ErrorCategory.MEMORY_SYSTEM, severity=ErrorSeverity.MEDIUM)
    async def enhance_memory_retrieval(
        self,
        user_id: str,
        bot_name: str,
        query: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        max_memories: int = 10,
        quality_threshold: float = 50.0
    ) -> MemoryBoostResult:
        """
        Enhanced memory retrieval with MemoryBoost intelligence.
        
        Args:
            user_id: User identifier
            bot_name: Bot identifier
            query: Search query
            conversation_history: Recent conversation context
            max_memories: Maximum memories to return
            quality_threshold: Minimum quality score for inclusion
            
        Returns:
            MemoryBoostResult with optimized memories and intelligence
        """
        start_time = datetime.utcnow()
        
        # Step 1: Initial memory retrieval from vector system
        initial_memories = await self._retrieve_initial_memories(
            user_id, bot_name, query, max_memories * 2  # Get extra for filtering
        )
        
        if not initial_memories:
            return self._create_empty_result(start_time)
        
        # Step 2: Calculate base similarity scores
        base_similarities = await self._calculate_base_similarities(initial_memories, query)
        
        # Step 3: Analyze memory quality
        conversation_context = ConversationContext(
            current_message=query,
            conversation_history=conversation_history or [],
            user_id=user_id,
            bot_name=bot_name
        )
        
        quality_scores = await self.effectiveness_analyzer.batch_analyze_memories(
            initial_memories, conversation_context
        )
        
        # Step 4: Optimize relevance scores  
        from src.intelligence.vector_relevance_optimizer import RelevanceOptimizationMode
        optimization_mode = RelevanceOptimizationMode.CONVERSATION  # Default mode
        optimization_context = OptimizationContext(
            user_id=user_id,
            bot_name=bot_name,
            query=query,
            conversation_history=conversation_history or [],
            optimization_mode=optimization_mode
        )
        
        relevance_scores = await self.relevance_optimizer.optimize_relevance_scores(
            initial_memories, base_similarities, optimization_context
        )
        
        # Step 5: Update relationship intelligence
        interaction_context = InteractionContext(
            user_id=user_id,
            bot_name=bot_name,
            message_content=query
        )
        
        relationship_metrics = await self.relationship_manager.analyze_relationship_intelligence(
            interaction_context
        )
        
        # Step 6: Apply quality filtering and ranking
        optimized_memories, filtered_quality_scores, filtered_relevance_scores = (
            self._apply_quality_filtering_and_ranking(
                initial_memories, quality_scores, relevance_scores, 
                quality_threshold, max_memories
            )
        )
        
        # Step 7: Record optimization improvements
        improvements_applied = await self._record_optimization_improvements(
            user_id, bot_name, quality_scores, relevance_scores
        )
        
        # Step 8: Create comprehensive result
        end_time = datetime.utcnow()
        processing_time_ms = (end_time - start_time).total_seconds() * 1000
        
        optimization_summary = {
            'initial_memory_count': len(initial_memories),
            'final_memory_count': len(optimized_memories),
            'quality_filtered_count': len([qs for qs in quality_scores if qs.overall_score >= quality_threshold]),
            'optimization_mode': optimization_mode.value,
            'relationship_depth': relationship_metrics.relationship_depth.value,
            'avg_quality_improvement': self._calculate_avg_improvement(quality_scores),
            'avg_relevance_boost': self._calculate_avg_relevance_boost(relevance_scores)
        }
        
        result = MemoryBoostResult(
            optimized_memories=optimized_memories,
            relevance_scores=filtered_relevance_scores,
            quality_scores=filtered_quality_scores,
            relationship_metrics=relationship_metrics,
            optimization_summary=optimization_summary,
            processing_time_ms=processing_time_ms,
            improvements_applied=improvements_applied
        )
        
        # Update statistics
        self.stats['boost_operations'] += 1
        self.stats['memory_improvements'] += improvements_applied
        self.stats['total_processing_time_ms'] += int(processing_time_ms)
        
        logger.info("MemoryBoost enhancement complete: %d memories optimized, %.2f ms processing",
                   len(optimized_memories), processing_time_ms)
        
        return result
    
    async def _retrieve_initial_memories(
        self, 
        user_id: str, 
        bot_name: str, 
        query: str, 
        max_memories: int
    ) -> List[VectorMemory]:
        """Retrieve initial memories from vector system"""
        if not self.memory_manager:
            return []
        
        try:
            # Use vector memory system for semantic search
            memories = await self.memory_manager.retrieve_relevant_memories(
                user_id=user_id,
                query=query,
                limit=max_memories
            )
            return memories
        except (TypeError, ValueError, IndexError) as e:
            logger.error("Initial memory retrieval failed: %s", e)
            return []
    
    async def _calculate_base_similarities(
        self, 
        memories: List[VectorMemory], 
        query: str
    ) -> List[float]:
        """Calculate base similarity scores for memories"""
        if not self.memory_manager:
            return [0.5] * len(memories)  # Default similarity
        
        try:
            query_embedding = await self.memory_manager.generate_embedding(query)
            similarities = []
            
            for memory in memories:
                if memory.embedding and query_embedding:
                    similarity = self._cosine_similarity(memory.embedding, query_embedding)
                    similarities.append(max(0, (similarity + 1) / 2))  # Normalize to 0-1
                else:
                    similarities.append(0.5)  # Default for missing embeddings
            
            return similarities
        except Exception as e:
            logger.error("Base similarity calculation failed: %s", e)
            return [0.5] * len(memories)
    
    def _apply_quality_filtering_and_ranking(
        self,
        memories: List[VectorMemory],
        quality_scores: List[MemoryQualityScore],
        relevance_scores: List[RelevanceScore],
        quality_threshold: float,
        max_memories: int
    ) -> tuple[List[VectorMemory], List[MemoryQualityScore], List[RelevanceScore]]:
        """Apply quality filtering and ranking to memories"""
        
        # Create combined scoring data
        memory_data = []
        for i, memory in enumerate(memories):
            if i < len(quality_scores) and i < len(relevance_scores):
                quality_score = quality_scores[i]
                relevance_score = relevance_scores[i]
                
                # Only include memories above quality threshold
                if quality_score.overall_score >= quality_threshold:
                    combined_score = (quality_score.overall_score * 0.6) + (relevance_score.final_score * 100 * 0.4)
                    memory_data.append((memory, quality_score, relevance_score, combined_score))
        
        # Sort by combined score (descending)
        memory_data.sort(key=lambda x: x[3], reverse=True)
        
        # Apply maximum limit
        memory_data = memory_data[:max_memories]
        
        # Extract sorted components
        optimized_memories = [data[0] for data in memory_data]
        filtered_quality_scores = [data[1] for data in memory_data]
        filtered_relevance_scores = [data[2] for data in memory_data]
        
        return optimized_memories, filtered_quality_scores, filtered_relevance_scores
    
    async def _record_optimization_improvements(
        self,
        user_id: str,
        bot_name: str,
        quality_scores: List[MemoryQualityScore],
        relevance_scores: List[RelevanceScore]
    ) -> int:
        """Record optimization improvements in PostgreSQL"""
        if not self.postgres_pool:
            return 0
        
        improvements = 0
        
        try:
            async with self.postgres_pool.acquire() as conn:
                for quality_score in quality_scores:
                    # Record memory effectiveness
                    await conn.execute("""
                        INSERT INTO memory_effectiveness (
                            memory_id, user_id, bot_name, quality_score, 
                            relevance_score, freshness_score, effectiveness_metrics
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                        ON CONFLICT (memory_id, user_id, bot_name)
                        DO UPDATE SET
                            quality_score = EXCLUDED.quality_score,
                            relevance_score = EXCLUDED.relevance_score,
                            freshness_score = EXCLUDED.freshness_score,
                            effectiveness_metrics = EXCLUDED.effectiveness_metrics,
                            usage_count = memory_effectiveness.usage_count + 1,
                            updated_at = CURRENT_TIMESTAMP
                    """, 
                    quality_score.memory_id, user_id, bot_name,
                    quality_score.overall_score,
                    quality_score.factor_scores.get(MemoryQualityFactor.SEMANTIC_RELEVANCE, 0),
                    quality_score.factor_scores.get(MemoryQualityFactor.TEMPORAL_FRESHNESS, 0),
                    quality_score.to_dict()
                    )
                    improvements += 1
                
                # Log optimization attempt
                avg_quality = sum(qs.overall_score for qs in quality_scores) / len(quality_scores) if quality_scores else 0
                avg_relevance = sum(rs.final_score for rs in relevance_scores) / len(relevance_scores) if relevance_scores else 0
                
                await conn.execute("""
                    INSERT INTO memory_optimization_logs (
                        user_id, bot_name, optimization_type, after_score, optimization_details
                    ) VALUES ($1, $2, $3, $4, $5)
                """, 
                user_id, bot_name, "memoryboost_optimization",
                (avg_quality + avg_relevance * 100) / 2,
                {
                    'quality_count': len(quality_scores),
                    'relevance_count': len(relevance_scores),
                    'avg_quality_score': avg_quality,
                    'avg_relevance_score': avg_relevance,
                    'optimization_timestamp': datetime.utcnow().isoformat()
                }
                )
                
        except Exception as e:
            logger.error("Recording optimization improvements failed: %s", e)
        
        return improvements
    
    def _calculate_avg_improvement(self, quality_scores: List[MemoryQualityScore]) -> float:
        """Calculate average quality improvement percentage"""
        if not quality_scores:
            return 0.0
        
        improvements = []
        for score in quality_scores:
            # Simple improvement calculation based on tier recommendation
            if score.tier_recommendation.value != 'short_term':
                improvement = (score.overall_score - 50) / 50 * 100  # Improvement over baseline
                improvements.append(max(0, improvement))
        
        return sum(improvements) / len(improvements) if improvements else 0.0
    
    def _calculate_avg_relevance_boost(self, relevance_scores: List[RelevanceScore]) -> float:
        """Calculate average relevance boost from optimization"""
        if not relevance_scores:
            return 0.0
        
        boosts = []
        for score in relevance_scores:
            boost = score.final_score - score.base_similarity
            boosts.append(boost)
        
        return sum(boosts) / len(boosts) if boosts else 0.0
    
    def _create_empty_result(self, start_time: datetime) -> MemoryBoostResult:
        """Create empty result for cases with no memories"""
        processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return MemoryBoostResult(
            optimized_memories=[],
            relevance_scores=[],
            quality_scores=[],
            relationship_metrics=None,
            optimization_summary={'no_memories_found': True},
            processing_time_ms=processing_time_ms,
            improvements_applied=0
        )
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = (sum(a * a for a in vec1)) ** 0.5
        magnitude2 = (sum(b * b for b in vec2)) ** 0.5
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    @handle_errors(category=ErrorCategory.MEMORY_SYSTEM, severity=ErrorSeverity.LOW)
    async def get_relationship_insights(self, user_id: str, bot_name: str) -> Dict[str, Any]:
        """Get relationship insights for a user-bot pair"""
        return await self.relationship_manager.get_relationship_insights(user_id, bot_name)
    
    def get_comprehensive_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics from all MemoryBoost components"""
        return {
            'memoryboost_integrator': {
                'component': 'MemoryBoostIntegrator',
                'system': 'WhisperEngine Adaptive Learning',
                'statistics': self.stats.copy(),
                'timestamp': datetime.utcnow().isoformat()
            },
            'memory_effectiveness_analyzer': self.effectiveness_analyzer.get_statistics(),
            'vector_relevance_optimizer': self.relevance_optimizer.get_statistics(),
            'relationship_intelligence_manager': self.relationship_manager.get_statistics()
        }


# Factory function for creating integrator instances
def create_memory_boost_integrator(memory_manager=None, postgres_pool=None) -> MemoryBoostIntegrator:
    """
    Factory function to create MemoryBoostIntegrator instance.
    
    Args:
        memory_manager: Vector memory system for memory operations
        postgres_pool: PostgreSQL connection pool for intelligence storage
        
    Returns:
        MemoryBoostIntegrator instance with all MemoryBoost components
    """
    return MemoryBoostIntegrator(memory_manager=memory_manager, postgres_pool=postgres_pool)