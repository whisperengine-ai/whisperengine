"""
Vector Fusion Module for WhisperEngine

Implements Reciprocal Rank Fusion (RRF) for combining multiple vector search results
to create more comprehensive and balanced memory retrieval.

Key Features:
- Reciprocal Rank Fusion algorithm
- Score normalization and weighting
- Duplicate detection and merging
- Configurable fusion strategies
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class FusionConfig:
    """Configuration for vector fusion."""
    k: int = 60  # RRF constant (higher = less aggressive rank penalty)
    weights: Optional[Dict[str, float]] = None  # Vector type weights
    min_score: float = 0.0  # Minimum score threshold
    deduplicate: bool = True  # Remove duplicate results
    
    def __post_init__(self):
        """Set default weights if not provided."""
        if self.weights is None:
            self.weights = {
                'content': 0.5,   # Content vector (semantic meaning)
                'semantic': 0.3,  # Semantic vector (conceptual patterns)
                'emotion': 0.2    # Emotion vector (emotional context)
            }


class ReciprocalRankFusion:
    """
    Reciprocal Rank Fusion (RRF) algorithm for combining multiple ranked lists.
    
    RRF is a simple but effective method that combines rankings from different sources
    without needing score normalization. It uses the formula:
    
    RRF_score = Σ(1 / (k + rank_i))
    
    Where:
    - k is a constant (typically 60)
    - rank_i is the rank of the item in the i-th list (1-indexed)
    """
    
    def __init__(self, config: Optional[FusionConfig] = None):
        """Initialize RRF with configuration."""
        self.config = config or FusionConfig()
        logger.info("🔀 RRF initialized with k=%d, weights=%s", self.config.k, self.config.weights)
    
    def fuse(
        self,
        results_by_vector: Dict[str, List[Dict[str, Any]]],
        limit: int = 25
    ) -> List[Dict[str, Any]]:
        """
        Fuse multiple vector search results using Reciprocal Rank Fusion.
        
        Args:
            results_by_vector: Dict mapping vector type to search results
                              e.g., {'content': [...], 'semantic': [...]}
            limit: Maximum number of results to return
            
        Returns:
            Fused and ranked list of memories
        """
        if not results_by_vector:
            return []
        
        # If only one vector type, return as-is
        if len(results_by_vector) == 1:
            vector_type = list(results_by_vector.keys())[0]
            results = results_by_vector[vector_type]
            logger.debug("🔀 RRF: Single vector type '%s', returning %d results", vector_type, len(results))
            return results[:limit]
        
        logger.info("🔀 RRF: Fusing %d vector types: %s", len(results_by_vector), list(results_by_vector.keys()))
        
        # Calculate RRF scores for each unique memory
        memory_scores = {}  # content_hash -> {memory, rrf_score, sources}
        
        for vector_type, results in results_by_vector.items():
            weight = self.config.weights.get(vector_type, 1.0) if self.config.weights else 1.0
            
            for rank, memory in enumerate(results, start=1):
                # Use content as unique identifier
                content_hash = self._get_content_hash(memory)
                
                # Calculate RRF score for this result
                rrf_score = weight / (self.config.k + rank)
                
                if content_hash in memory_scores:
                    # Memory already seen from another vector - add score
                    memory_scores[content_hash]['rrf_score'] += rrf_score
                    memory_scores[content_hash]['sources'].append(vector_type)
                    memory_scores[content_hash]['ranks'][vector_type] = rank
                else:
                    # First time seeing this memory
                    memory_scores[content_hash] = {
                        'memory': memory,
                        'rrf_score': rrf_score,
                        'sources': [vector_type],
                        'ranks': {vector_type: rank}
                    }
        
        # Sort by RRF score (highest first)
        fused_results = sorted(
            memory_scores.values(),
            key=lambda x: x['rrf_score'],
            reverse=True
        )
        
        # Format results with fusion metadata
        formatted_results = []
        for item in fused_results[:limit]:
            memory = item['memory'].copy()
            memory['fusion_metadata'] = {
                'rrf_score': item['rrf_score'],
                'sources': item['sources'],
                'ranks': item['ranks'],
                'fusion_strategy': 'reciprocal_rank_fusion'
            }
            formatted_results.append(memory)
        
        logger.info("🔀 RRF: Fused %d unique memories → returning top %d", len(memory_scores), len(formatted_results))
        if formatted_results:
            logger.debug("🔀 RRF: Score range: %.4f - %.4f", 
                        formatted_results[0]['fusion_metadata']['rrf_score'],
                        formatted_results[-1]['fusion_metadata']['rrf_score'])
        
        return formatted_results
    
    def _get_content_hash(self, memory: Dict[str, Any]) -> str:
        """Generate unique identifier for memory based on content."""
        # Use first 100 chars of content + timestamp for uniqueness
        content = memory.get('content', '')[:100]
        timestamp = str(memory.get('timestamp', ''))
        return f"{content}_{timestamp}"


class VectorFusionCoordinator:
    """
    Coordinates multi-vector fusion for different query types.
    
    Determines when to use fusion, which vectors to combine,
    and how to weight them based on query characteristics.
    """
    
    def __init__(self):
        """Initialize fusion coordinator."""
        self.rrf = ReciprocalRankFusion()
        logger.info("🔀 VectorFusionCoordinator initialized")
    
    def should_use_fusion(self, query: str) -> bool:
        """
        Determine if multi-vector fusion should be used for this query.
        
        Fusion is beneficial for:
        - Conversational recall queries ("what did we discuss")
        - Pattern recognition queries ("relationship between")
        - Complex multi-faceted queries
        
        Fusion is NOT needed for:
        - Simple factual queries
        - Single-topic queries
        - Temporal queries (already use specific retrieval)
        """
        query_lower = query.lower()
        
        # Conversational recall indicators
        conversational_keywords = [
            'what did we', 'what we discussed', 'our conversation',
            'we talked about', 'between us', 'remember when we',
            'topics we', 'things we', 'what we said'
        ]
        
        # Pattern/relationship indicators
        pattern_keywords = [
            'pattern', 'relationship', 'connection', 'relate',
            'similar', 'connect', 'link', 'between'
        ]
        
        # Check for fusion-worthy queries
        is_conversational = any(kw in query_lower for kw in conversational_keywords)
        is_pattern = any(kw in query_lower for kw in pattern_keywords)
        
        should_fuse = is_conversational or is_pattern
        
        if should_fuse:
            logger.info("🔀 FUSION ENABLED for query: '%s...' (conversational=%s, pattern=%s)", 
                       query[:60], is_conversational, is_pattern)
        
        return should_fuse
    
    def get_fusion_vectors(self, query: str) -> List[str]:
        """
        Determine which vector types to combine for this query.
        
        Returns list of vector types to use, e.g., ['content', 'semantic']
        """
        query_lower = query.lower()
        vectors = ['content']  # Always include content vector
        
        # Add semantic for pattern/relationship queries
        pattern_keywords = ['pattern', 'relationship', 'connection', 'relate', 'similar', 'between']
        if any(kw in query_lower for kw in pattern_keywords):
            vectors.append('semantic')
        
        # Add emotion for emotional queries (if not already handled by emotion routing)
        emotion_keywords = ['feel', 'emotion', 'mood']
        if any(kw in query_lower for kw in emotion_keywords):
            vectors.append('emotion')
        
        logger.debug("🔀 Fusion vectors for query: %s", vectors)
        return vectors


def create_vector_fusion_coordinator() -> VectorFusionCoordinator:
    """Factory function to create fusion coordinator."""
    return VectorFusionCoordinator()
