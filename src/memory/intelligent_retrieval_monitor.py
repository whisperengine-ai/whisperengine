"""
Intelligent Memory Retrieval Monitoring.

Tracks query classification, vector routing decisions, and performance metrics
to InfluxDB for analysis and optimization. Monitors the query-aware intelligent
memory retrieval system that uses classification to select optimal vector strategies.

Usage:
    from src.memory.intelligent_retrieval_monitor import IntelligentRetrievalMonitor
    
    monitor = IntelligentRetrievalMonitor()
    
    # Track classification decision
    await monitor.track_classification(
        user_id="user123",
        query="How are you feeling?",
        category=QueryCategory.EMOTIONAL,
        emotion_intensity=0.65,
        classification_time_ms=2
    )
    
    # Track routing decision
    await monitor.track_routing(
        user_id="user123",
        query_category=QueryCategory.EMOTIONAL,
        search_type="multi_vector_fusion",
        vectors_used=["content", "emotion"],
        memory_count=10,
        search_time_ms=25
    )
"""

import logging
import time
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from src.memory.query_classifier import QueryCategory

logger = logging.getLogger(__name__)


class IntelligentRetrievalMonitor:
    """
    Monitor intelligent query-aware memory retrieval system.
    
    Tracks classification-driven routing decisions for semantic memory retrieval.
    
    Sends metrics to InfluxDB for tracking:
    - Query classification accuracy
    - Vector usage distribution
    - Performance metrics (latency)
    - Routing decision patterns
    """
    
    def __init__(self):
        """Initialize Phase 2 monitoring."""
        self.enabled = False
        self.temporal_client = None
        
        # Try to get TemporalIntelligenceClient (which handles InfluxDB)
        try:
            from src.temporal.temporal_intelligence_client import TemporalIntelligenceClient
            self.temporal_client = TemporalIntelligenceClient()
            
            # Check if InfluxDB is available
            if self.temporal_client and self.temporal_client.enabled:
                self.enabled = True
                logger.info("📊 Phase 2 monitoring enabled (InfluxDB available)")
            else:
                logger.info("📊 Phase 2 monitoring disabled (InfluxDB not configured)")
                
        except Exception as e:
            logger.warning("📊 Phase 2 monitoring disabled: %s", str(e))
    
    async def track_classification(
        self,
        user_id: str,
        query: str,
        category: QueryCategory,
        emotion_intensity: Optional[float] = None,
        is_temporal: bool = False,
        pattern_matched: Optional[str] = None,
        classification_time_ms: Optional[float] = None
    ):
        """
        Track a query classification decision.
        
        Args:
            user_id: User identifier
            query: The query text
            category: Classified category
            emotion_intensity: Emotional intensity (if available)
            is_temporal: Whether temporal query was detected
            pattern_matched: Which pattern triggered classification
            classification_time_ms: Time taken to classify
            
        Example:
            >>> await monitor.track_classification(
            ...     user_id="user123",
            ...     query="How are you feeling?",
            ...     category=QueryCategory.EMOTIONAL,
            ...     emotion_intensity=0.65,
            ...     pattern_matched="feeling",
            ...     classification_time_ms=2.5
            ... )
        """
        if not self.enabled or not self.temporal_client:
            return
        
        try:
            # Get bot name for tagging
            from src.utils.helpers import get_normalized_bot_name_from_env
            bot_name = get_normalized_bot_name_from_env()
            
            # Build tags
            tags = {
                "bot_name": bot_name,
                "category": category.value,
                "is_temporal": str(is_temporal).lower()
            }
            
            if pattern_matched:
                tags["pattern_matched"] = pattern_matched
            
            # Build fields
            fields = {
                "query_length": len(query),
                "classification_count": 1  # For counting classifications
            }
            
            if emotion_intensity is not None:
                fields["emotion_intensity"] = emotion_intensity
            
            if classification_time_ms is not None:
                fields["classification_time_ms"] = classification_time_ms
            
            # Write to InfluxDB
            await self.temporal_client.write_point(
                measurement="query_classification",
                tags=tags,
                fields=fields
            )
            
            logger.debug(
                "📊 Tracked classification: category=%s, pattern=%s",
                category.value, pattern_matched
            )
            
        except Exception as e:
            logger.warning("Failed to track classification: %s", str(e))
    
    async def track_routing(
        self,
        user_id: str,
        query_category: QueryCategory,
        search_type: str,
        vectors_used: List[str],
        memory_count: int,
        search_time_ms: float,
        fusion_enabled: bool = False,
        retrieval_score: Optional[float] = None
    ):
        """
        Track a vector routing decision.
        
        Args:
            user_id: User identifier
            query_category: Query category that determined routing
            search_type: Type of search performed (e.g., "multi_vector_fusion")
            vectors_used: List of vectors used (e.g., ["content", "emotion"])
            memory_count: Number of memories retrieved
            search_time_ms: Time taken for vector search
            fusion_enabled: Whether RRF fusion was used
            retrieval_score: Average relevance score (if available)
            
        Example:
            >>> await monitor.track_routing(
            ...     user_id="user123",
            ...     query_category=QueryCategory.EMOTIONAL,
            ...     search_type="multi_vector_fusion",
            ...     vectors_used=["content", "emotion"],
            ...     memory_count=10,
            ...     search_time_ms=25.3,
            ...     fusion_enabled=True
            ... )
        """
        if not self.enabled or not self.temporal_client:
            return
        
        try:
            # Get bot name for tagging
            from src.utils.helpers import get_normalized_bot_name_from_env
            bot_name = get_normalized_bot_name_from_env()
            
            # Build tags
            tags = {
                "bot_name": bot_name,
                "query_category": query_category.value,
                "search_type": search_type,
                "fusion_enabled": str(fusion_enabled).lower()
            }
            
            # Add vector usage tags (for filtering in Grafana)
            if "content" in vectors_used:
                tags["uses_content"] = "true"
            if "emotion" in vectors_used:
                tags["uses_emotion"] = "true"
            if "semantic" in vectors_used:
                tags["uses_semantic"] = "true"
            
            # Build fields
            fields = {
                "memory_count": memory_count,
                "search_time_ms": search_time_ms,
                "vector_count": len(vectors_used),
                "routing_count": 1  # For counting routing decisions
            }
            
            if retrieval_score is not None:
                fields["avg_retrieval_score"] = retrieval_score
            
            # Write to InfluxDB
            await self.temporal_client.write_point(
                measurement="phase2_vector_routing",
                tags=tags,
                fields=fields
            )
            
            logger.debug(
                "📊 Tracked routing: category=%s, search_type=%s, vectors=%s, time=%.1fms",
                query_category.value, search_type, vectors_used, search_time_ms
            )
            
        except Exception as e:
            logger.warning("Failed to track routing: %s", str(e))
    
    async def track_retrieval_performance(
        self,
        user_id: str,
        total_time_ms: float,
        classification_time_ms: float,
        search_time_ms: float,
        fusion_time_ms: Optional[float] = None,
        intelligent_routing_used: bool = True
    ):
        """
        Track overall intelligent retrieval performance metrics.
        
        Args:
            user_id: User identifier
            total_time_ms: Total retrieval time (end-to-end)
            classification_time_ms: Time spent in QueryClassifier
            search_time_ms: Time spent in vector search
            fusion_time_ms: Time spent in RRF fusion (if applicable)
            intelligent_routing_used: Whether intelligent routing was used vs legacy
            
        Example:
            >>> await monitor.track_retrieval_performance(
            ...     user_id="user123",
            ...     total_time_ms=30.5,
            ...     classification_time_ms=2.0,
            ...     search_time_ms=23.5,
            ...     fusion_time_ms=5.0,
            ...     intelligent_routing_used=True
            ... )
        """
        if not self.enabled or not self.temporal_client:
            return
        
        try:
            # Get bot name for tagging
            from src.utils.helpers import get_normalized_bot_name_from_env
            bot_name = get_normalized_bot_name_from_env()
            
            # Build tags
            tags = {
                "bot_name": bot_name,
                "method": "intelligent_routing" if intelligent_routing_used else "legacy_routing"
            }
            
            # Build fields
            fields = {
                "total_time_ms": total_time_ms,
                "classification_time_ms": classification_time_ms,
                "search_time_ms": search_time_ms,
                "performance_count": 1  # For counting measurements
            }
            
            if fusion_time_ms is not None:
                fields["fusion_time_ms"] = fusion_time_ms
                fields["overhead_ms"] = classification_time_ms + fusion_time_ms
            else:
                fields["overhead_ms"] = classification_time_ms
            
            # Calculate overhead percentage
            if total_time_ms > 0:
                overhead_pct = (fields["overhead_ms"] / total_time_ms) * 100
                fields["overhead_percentage"] = overhead_pct
            
            # Write to InfluxDB
            await self.temporal_client.write_point(
                measurement="intelligent_retrieval_performance",
                tags=tags,
                fields=fields
            )
            
            logger.debug(
                "📊 Tracked performance: total=%.1fms, classification=%.1fms, search=%.1fms",
                total_time_ms, classification_time_ms, search_time_ms
            )
            
        except Exception as e:
            logger.warning("Failed to track performance: %s", str(e))
    
    async def track_ab_test_result(
        self,
        user_id: str,
        query: str,
        variant: str,  # "phase2" or "legacy"
        query_category: Optional[QueryCategory] = None,
        memory_relevance_score: Optional[float] = None,
        response_quality_score: Optional[float] = None,
        user_reaction: Optional[str] = None  # "positive", "negative", "neutral"
    ):
        """
        Track A/B testing results for Phase 2 vs legacy routing.
        
        Args:
            user_id: User identifier
            query: The query text
            variant: Which variant was used ("phase2" or "legacy")
            query_category: Classified category (Phase 2 only)
            memory_relevance_score: How relevant retrieved memories were
            response_quality_score: Quality of bot response
            user_reaction: User's reaction (from Discord reactions/feedback)
            
        Example:
            >>> await monitor.track_ab_test_result(
            ...     user_id="user123",
            ...     query="How are you feeling?",
            ...     variant="phase2",
            ...     query_category=QueryCategory.EMOTIONAL,
            ...     memory_relevance_score=0.82,
            ...     response_quality_score=0.90,
            ...     user_reaction="positive"
            ... )
        """
        if not self.enabled or not self.temporal_client:
            return
        
        try:
            # Get bot name for tagging
            from src.utils.helpers import get_normalized_bot_name_from_env
            bot_name = get_normalized_bot_name_from_env()
            
            # Build tags
            tags = {
                "bot_name": bot_name,
                "variant": variant
            }
            
            if query_category:
                tags["query_category"] = query_category.value
            
            if user_reaction:
                tags["user_reaction"] = user_reaction
            
            # Build fields
            fields = {
                "query_length": len(query),
                "ab_test_count": 1  # For counting A/B tests
            }
            
            if memory_relevance_score is not None:
                fields["memory_relevance_score"] = memory_relevance_score
            
            if response_quality_score is not None:
                fields["response_quality_score"] = response_quality_score
            
            # User satisfaction (1.0 for positive, 0.0 for negative, 0.5 for neutral)
            if user_reaction == "positive":
                fields["user_satisfaction"] = 1.0
            elif user_reaction == "negative":
                fields["user_satisfaction"] = 0.0
            elif user_reaction == "neutral":
                fields["user_satisfaction"] = 0.5
            
            # Write to InfluxDB
            await self.temporal_client.write_point(
                measurement="retrieval_method_comparison",
                tags=tags,
                fields=fields
            )
            
            logger.debug(
                "📊 Tracked A/B test: variant=%s, category=%s, reaction=%s",
                variant, query_category.value if query_category else "N/A", user_reaction
            )
            
        except Exception as e:
            logger.warning("Failed to track A/B test result: %s", str(e))


# Global singleton instance
_retrieval_monitor: Optional[IntelligentRetrievalMonitor] = None


def get_intelligent_retrieval_monitor() -> IntelligentRetrievalMonitor:
    """
    Get or create global IntelligentRetrievalMonitor instance.
    
    Returns:
        Global IntelligentRetrievalMonitor singleton
        
    Example:
        >>> monitor = get_intelligent_retrieval_monitor()
        >>> await monitor.track_classification(...)
    """
    global _retrieval_monitor
    
    if _retrieval_monitor is None:
        _retrieval_monitor = IntelligentRetrievalMonitor()
    
    return _retrieval_monitor
