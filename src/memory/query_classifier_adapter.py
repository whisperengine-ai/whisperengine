"""
Compatibility Adapter - QueryClassifier API wrapping UnifiedQueryClassifier

This module provides backward compatibility by maintaining the old QueryClassifier
API while internally using UnifiedQueryClassifier.

This allows gradual migration - existing code continues to work while new code
uses the unified system directly.

## Transition Strategy

**Phase 1 (Now):** Adapter layer translates old API → unified system
**Phase 2 (Week 2):** Update callers to use unified API directly
**Phase 3 (Week 3):** Remove adapter layer, make unified system primary
"""

import logging
from typing import Dict, Any, Optional

from src.memory.unified_query_classification import (
    UnifiedQueryClassifier,
    UnifiedClassification,
    VectorStrategy,
)

logger = logging.getLogger(__name__)


class QueryCategory:
    """Enum-like class for backward compatibility with old QueryCategory API"""
    FACTUAL = "factual"
    EMOTIONAL = "emotional"
    CONVERSATIONAL = "conversational"
    TEMPORAL = "temporal"
    GENERAL = "general"


class QueryClassifierAdapter:
    """
    Backward-compatible QueryClassifier that wraps UnifiedQueryClassifier.
    
    Old API:
        classifier = QueryClassifier()
        category = await classifier.classify_query(query, emotion_data, is_temporal)
        strategy = classifier.get_vector_strategy(category)
    
    New API (internal):
        classifier = UnifiedQueryClassifier()
        result = await classifier.classify(query, emotion_data)
        # result.intent_type, result.vector_strategy, etc.
    
    This adapter translates between them:
    - QueryCategory.FACTUAL → VectorStrategy.CONTENT_ONLY
    - QueryCategory.EMOTIONAL → VectorStrategy.EMOTION_FUSION
    - QueryCategory.CONVERSATIONAL → VectorStrategy.SEMANTIC_FUSION
    - QueryCategory.TEMPORAL → VectorStrategy.TEMPORAL_CHRONOLOGICAL
    """
    
    def __init__(self, unified_classifier: UnifiedQueryClassifier):
        """
        Initialize adapter with underlying unified classifier.
        
        Args:
            unified_classifier: UnifiedQueryClassifier instance
        """
        self.unified = unified_classifier
        logger.info("✅ QueryClassifierAdapter initialized (backward compatibility mode)")
    
    async def classify_query(
        self,
        query: str,
        emotion_data: Optional[Dict[str, Any]] = None,
        is_temporal: bool = False,  # Deprecated - auto-detected in unified system
    ) -> str:
        """
        Old API: Classify query to category (backward compatible).
        
        Args:
            query: Query string
            emotion_data: Optional emotion data from RoBERTa
            is_temporal: Deprecated - temporal queries auto-detected (kept for API compatibility)
            
        Returns:
            Query category string (factual, emotional, conversational, temporal, general)
            
        DEPRECATION NOTE:
            Use UnifiedQueryClassifier.classify() instead.
            This method is provided for backward compatibility only.
        """
        # Use unified classifier
        classification = await self.unified.classify(
            query=query,
            emotion_data=emotion_data,
        )
        
        # Map vector strategy back to old QueryCategory
        category = self._map_strategy_to_category(classification.vector_strategy)
        
        logger.debug(
            "🔄 ADAPTER: Converted classification to old API: %s → %s",
            classification.reasoning, category
        )
        
        return category
    
    def get_vector_strategy(self, category: str) -> Dict[str, Any]:
        """
        Old API: Get vector strategy for category (backward compatible).
        
        Args:
            category: Query category (factual, emotional, conversational, etc.)
            
        Returns:
            Dictionary with vector routing configuration:
            - vectors: List of vector names
            - weights: List of weights
            - use_fusion: Boolean
            - description: Human-readable description
            
        DEPRECATION NOTE:
            Call UnifiedQueryClassifier.get_vector_weights() instead.
            This method is provided for backward compatibility only.
        """
        
        # Map old category to vector strategy
        strategy_map = {
            QueryCategory.FACTUAL: VectorStrategy.CONTENT_ONLY,
            QueryCategory.EMOTIONAL: VectorStrategy.EMOTION_FUSION,
            QueryCategory.CONVERSATIONAL: VectorStrategy.SEMANTIC_FUSION,
            QueryCategory.TEMPORAL: VectorStrategy.TEMPORAL_CHRONOLOGICAL,
            QueryCategory.GENERAL: VectorStrategy.CONTENT_ONLY,
        }
        
        strategy = strategy_map.get(category, VectorStrategy.CONTENT_ONLY)
        weights = self.unified.get_vector_weights(strategy)
        
        # Convert to old API format
        return {
            "vectors": list(weights.keys()),
            "weights": list(weights.values()),
            "use_fusion": len(weights) > 1,
            "description": f"Strategy: {strategy.value}",
        }
    
    def update_patterns(
        self,
        factual_patterns: Optional[list] = None,  # Ignored - for API compatibility
        conversational_patterns: Optional[list] = None,  # Ignored - for API compatibility
        emotion_threshold: Optional[float] = None,
    ):
        """
        Old API: Update patterns (backward compatible).
        
        Args:
            factual_patterns: Kept for compatibility, but ignored
            conversational_patterns: Kept for compatibility, but ignored
            emotion_threshold: Emotion intensity threshold to update
        
        DEPRECATION NOTE:
            Use UnifiedQueryClassifier directly instead.
            This method is provided for backward compatibility only.
        """
        if emotion_threshold is not None:
            self.unified.emotion_intensity_threshold = emotion_threshold
            logger.info("🔧 Updated emotion threshold via adapter: %.2f", emotion_threshold)
        
        # Note: Pattern updates would need more work - for now just log
        logger.warning(
            "⚠️  Pattern updates via adapter are limited. "
            "Use UnifiedQueryClassifier directly for full control."
        )
    
    def _map_strategy_to_category(self, strategy: VectorStrategy) -> str:
        """
        Map unified vector strategy back to old QueryCategory API.
        
        This is a lossy conversion since old API has fewer categories,
        but maintains functional backward compatibility.
        """
        
        if strategy == VectorStrategy.CONTENT_ONLY:
            return QueryCategory.FACTUAL
        elif strategy == VectorStrategy.EMOTION_FUSION:
            return QueryCategory.EMOTIONAL
        elif strategy == VectorStrategy.SEMANTIC_FUSION:
            return QueryCategory.CONVERSATIONAL
        elif strategy == VectorStrategy.TEMPORAL_CHRONOLOGICAL:
            return QueryCategory.TEMPORAL
        elif strategy in [VectorStrategy.BALANCED_FUSION, VectorStrategy.MULTI_CATEGORY]:
            # Multi-vector queries map to conversational (semantic + content)
            return QueryCategory.CONVERSATIONAL
        else:
            return QueryCategory.GENERAL
    
    async def get_unified_classification(self, query: str, emotion_data=None) -> UnifiedClassification:
        """
        NEW API: Direct access to unified classification.
        
        For new code, call this method or UnifiedQueryClassifier.classify() directly
        to get full classification information (not just category).
        
        Args:
            query: Query string
            emotion_data: Optional emotion data from RoBERTa
            
        Returns:
            UnifiedClassification with complete routing information
        """
        return await self.unified.classify(query, emotion_data)


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def create_query_classifier(unified_classifier: Optional[UnifiedQueryClassifier] = None) -> QueryClassifierAdapter:
    """
    Factory function for backward compatibility.
    
    Maintains old API while using unified classifier internally.
    
    Args:
        unified_classifier: Optional UnifiedQueryClassifier instance
                          If not provided, creates new one
        
    Returns:
        QueryClassifierAdapter instance
        
    DEPRECATION NOTE:
        New code should use create_unified_query_classifier() instead
        and call the new API directly.
    """
    if unified_classifier is None:
        from src.memory.unified_query_classification import create_unified_query_classifier
        unified_classifier = create_unified_query_classifier()
    
    return QueryClassifierAdapter(unified_classifier)


def create_query_classifier_adapter(
    postgres_pool=None,
    qdrant_client=None
) -> QueryClassifierAdapter:
    """
    Create adapter with new unified classifier.
    
    Args:
        postgres_pool: Optional PostgreSQL connection pool
        qdrant_client: Optional Qdrant client
        
    Returns:
        QueryClassifierAdapter for backward compatibility
    """
    from src.memory.unified_query_classification import create_unified_query_classifier
    
    unified = create_unified_query_classifier(postgres_pool, qdrant_client)
    return QueryClassifierAdapter(unified)
