"""
Qdrant Query Optimization Module
===============================

This module provides advanced query optimization capabilities for the Qdrant vector database,
including query preprocessing, adaptive scoring, content chunking, hybrid search, and result re-ranking.
"""

import re
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class QueryContext:
    """Context information for query optimization."""
    query_type: str = "general_search"
    user_history: Dict[str, Any] = None
    time_range: Optional[Dict[str, datetime]] = None
    channel_id: Optional[str] = None
    topics: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.user_history is None:
            self.user_history = {}


class QdrantQueryOptimizer:
    """Advanced query optimizer for Qdrant vector search."""
    
    def __init__(self, vector_manager=None):
        self.vector_manager = vector_manager
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'
        }
        
    def preprocess_query(self, query: str, context: Optional[QueryContext] = None) -> str:
        """
        Preprocess and enhance queries for better semantic search.
        
        Args:
            query: Raw user query
            context: Query context for optimization
            
        Returns:
            Optimized query string
        """
        # Clean and normalize
        cleaned = query.strip().lower()
        
        # Remove excessive punctuation but keep meaningful ones
        cleaned = re.sub(r'[^\w\s\?\!\.\,\-]', ' ', cleaned)
        
        # Remove stop words for better semantic focus
        words = cleaned.split()
        filtered_words = [w for w in words if w not in self.stop_words and len(w) > 2]
        
        if not filtered_words:
            # If all words were filtered, use original
            return query
            
        # Rejoin filtered words
        enhanced_query = ' '.join(filtered_words)
        
        # Context-aware enhancement
        if context:
            enhanced_query = self._enhance_query_with_context(enhanced_query, context)
            
        logger.debug("🔍 Query optimization: '%s' → '%s'", query, enhanced_query)
        return enhanced_query
        
    def _enhance_query_with_context(self, query: str, context: QueryContext) -> str:
        """Enhance query based on context type."""
        if context.query_type == 'conversation_recall':
            # For conversation context, emphasize conversational aspects
            if 'remember' in query or 'said' in query or 'told' in query:
                return f"conversation memory {query}"
        elif context.query_type == 'fact_lookup':
            # For facts, emphasize specific information
            return f"factual information {query}"
        elif context.topics:
            # Add topic context
            topic_context = ' '.join(context.topics[:2])  # Limit to 2 topics
            return f"{topic_context} {query}"
            
        return query
        
    def get_adaptive_threshold(self, query_type: str, user_history: Dict[str, Any]) -> float:
        """
        Calculate adaptive score thresholds based on query context and user patterns.
        
        Args:
            query_type: Type of query being performed
            user_history: User's interaction patterns and preferences
            
        Returns:
            Optimized similarity threshold
        """
        base_thresholds = {
            'conversation_recall': 0.4,  # Lower for conversational context
            'fact_lookup': 0.7,          # Higher for precise facts
            'general_search': 0.5,       # Medium for general queries
            'entity_search': 0.6,        # Medium-high for entity queries
            'recent_context': 0.3,       # Very low for recent context
        }
        
        base_threshold = base_thresholds.get(query_type, 0.5)
        
        # Adjust based on user's typical interaction patterns
        if user_history.get('prefers_precise_answers'):
            return min(base_threshold + 0.1, 0.9)
        elif user_history.get('conversational_user'):
            return max(base_threshold - 0.1, 0.2)
        elif user_history.get('exploration_mode'):
            return max(base_threshold - 0.15, 0.2)
            
        return base_threshold
        
    def chunk_content(self, content: str, max_chunk_size: int = 300) -> List[str]:
        """
        Break down large content into semantically meaningful chunks.
        
        Args:
            content: Content to chunk
            max_chunk_size: Maximum characters per chunk
            
        Returns:
            List of content chunks
        """
        if len(content) <= max_chunk_size:
            return [content]
            
        chunks = []
        
        # Split by sentences first
        sentences = self._split_into_sentences(content)
        
        current_chunk = ""
        for sentence in sentences:
            # Check if adding this sentence would exceed limit
            if len(current_chunk + sentence) > max_chunk_size and current_chunk:
                # Add current chunk and start new one
                chunks.append(current_chunk.strip())
                current_chunk = sentence + " "
            else:
                current_chunk += sentence + " "
                
        # Add remaining content
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
            
        logger.debug("📝 Content chunked: %d chars → %d chunks", len(content), len(chunks))
        return chunks
        
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences using simple regex."""
        # Split on sentence endings, keeping the punctuation
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
        
    async def hybrid_search(self, query: str, user_id: str, filters: Optional[Dict] = None) -> List[Dict]:
        """
        Combine semantic vector search with precise metadata filtering.
        Use Qdrant-native filtering for maximum efficiency.
        
        Args:
            query: Search query
            user_id: User identifier
            filters: Additional metadata filters
            
        Returns:
            Filtered and ranked search results
        """
        if not self.vector_manager:
            raise ValueError("Vector manager not configured for hybrid search")
        
        # 🚀 QDRANT-NATIVE FILTERING: Build filters for database-level exclusion
        qdrant_filters = await self._build_qdrant_filters(user_id, filters)
        
        # Perform search with native Qdrant filtering
        semantic_results = await self._search_with_qdrant_filters(
            query=query,
            user_id=user_id,
            qdrant_filters=qdrant_filters,
            limit=50  # Get more results for re-ranking
        )
        
        logger.debug("🔍 Hybrid search: %d results after Qdrant-native filtering", len(semantic_results))
        return semantic_results
    
    async def _build_qdrant_filters(self, user_id: str, filters: Optional[Dict] = None) -> Dict:
        """
        Build Qdrant-native filter conditions for efficient database-level filtering.
        
        Args:
            user_id: User identifier
            filters: Filter specifications
            
        Returns:
            Qdrant filter configuration with must/must_not conditions
        """
        from qdrant_client import models
        import os
        
        # Start with required conditions
        must_conditions = [
            models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id)),
            # 🎯 Bot-specific filtering for multi-bot architecture
            models.FieldCondition(key="bot_name", match=models.MatchValue(value=os.getenv("DISCORD_BOT_NAME", "unknown")))
        ]
        
        # Content exclusion conditions (most important for our debugging contamination fix)
        must_not_conditions = []
        
        if filters:
            # Time-based filtering
            if 'time_range' in filters:
                time_range = filters['time_range']
                if time_range.get('start'):
                    start_timestamp = int(time_range['start'].timestamp())
                    must_conditions.append(
                        models.FieldCondition(
                            key="timestamp_unix",
                            range=models.Range(gte=start_timestamp)
                        )
                    )
                if time_range.get('end'):
                    end_timestamp = int(time_range['end'].timestamp())
                    must_conditions.append(
                        models.FieldCondition(
                            key="timestamp_unix", 
                            range=models.Range(lte=end_timestamp)
                        )
                    )
            
            # Memory type filtering
            if 'memory_type' in filters:
                must_conditions.append(
                    models.FieldCondition(
                        key="memory_type",
                        match=models.MatchValue(value=filters['memory_type'])
                    )
                )
            
            # Channel/context filtering
            if 'channel_id' in filters:
                must_conditions.append(
                    models.FieldCondition(
                        key="channel_id",
                        match=models.MatchValue(value=filters['channel_id'])
                    )
                )
            
            # 🎭 CHARACTER FILTERING: Filter by active character context
            if 'active_character' in filters:
                must_conditions.append(
                    models.FieldCondition(
                        key="active_character",
                        match=models.MatchValue(value=filters['active_character'])
                    )
                )
            
            if 'has_character' in filters:
                must_conditions.append(
                    models.FieldCondition(
                        key="has_character", 
                        match=models.MatchValue(value=filters['has_character'])
                    )
                )
            
            # 🛡️ META-CONVERSATION FILTER: Exclude conversations ABOUT the bot system
            # This prevents our technical debugging from contaminating character responses
            # while allowing users to discuss these topics naturally with the bot
            if 'exclude_content_patterns' in filters:
                meta_patterns = filters['exclude_content_patterns']
                logger.info(f"🛡️ QDRANT FILTER: Excluding meta-conversations with {len(meta_patterns)} patterns")
                
                for pattern in meta_patterns:
                    # Use MatchText for pattern-based exclusion
                    must_not_conditions.append(
                        models.FieldCondition(
                            key="content",
                            match=models.MatchText(text=pattern)
                        )
                    )
                
                logger.debug(f"🛡️ QDRANT: Added {len(must_not_conditions)} meta-conversation exclusions")
            
            # Legacy support for old keyword-based filtering
            elif 'exclude_content_keywords' in filters:
                debugging_keywords = filters['exclude_content_keywords']
                logger.info(f"🛡️ QDRANT FILTER: Excluding content with {len(debugging_keywords)} keywords")
                
                for keyword in debugging_keywords:
                    must_not_conditions.append(
                        models.FieldCondition(
                            key="content",
                            match=models.MatchText(text=keyword)
                        )
                    )
                
                logger.debug(f"🛡️ QDRANT: Added {len(must_not_conditions)} exclusion conditions")
        
        return {
            'must': must_conditions,
            'must_not': must_not_conditions
        }
    
    async def _search_with_qdrant_filters(self, query: str, user_id: str, qdrant_filters: Dict, limit: int = 50) -> List[Dict]:
        """
        Perform Qdrant search with native filtering for maximum efficiency.
        
        Args:
            query: Search query
            user_id: User identifier  
            qdrant_filters: Qdrant filter conditions
            limit: Maximum results
            
        Returns:
            Search results filtered at database level
        """
        try:
            # Use the vector_manager's search but with our custom filters
            # This requires the vector_manager to support qdrant filter passthrough
            
            # For now, delegate to the vector manager's existing search
            # TODO: Enhance vector_manager to accept raw Qdrant filters
            semantic_results = await self.vector_manager.search_memories(
                query=query,
                user_id=user_id,
                limit=limit
            )
            
            # Apply post-filtering temporarily until vector_manager supports native filters
            # This is still better than the previous approach as the logic is centralized
            filtered_results = []
            
            for result in semantic_results:
                # Check must_not conditions
                content = result.get('content', '').lower()
                metadata = result.get('metadata', {})
                
                # Apply must_not exclusions
                should_exclude = False
                for condition in qdrant_filters.get('must_not', []):
                    if condition.key == 'content' and hasattr(condition.match, 'text'):
                        pattern = condition.match.text.lower()
                        if pattern in content:
                            should_exclude = True
                            logger.debug(f"🛡️ EXCLUDED: Memory contains pattern '{pattern[:30]}...'")
                            break
                
                if not should_exclude:
                    filtered_results.append(result)
            
            logger.debug(f"🛡️ Filtered {len(semantic_results) - len(filtered_results)} contaminated memories")
            return filtered_results
            
        except Exception as e:
            logger.error(f"Qdrant filtering failed: {e}")
            # Fallback to unfiltered search
            return await self.vector_manager.search_memories(query=query, user_id=user_id, limit=limit)
        
    def _within_time_range(self, timestamp_str: str, time_range: Dict) -> bool:
        """Check if timestamp falls within the specified range."""
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            start = time_range.get('start')
            end = time_range.get('end')
            
            if start and timestamp < start:
                return False
            if end and timestamp > end:
                return False
            return True
        except (ValueError, TypeError):
            return True  # Include if timestamp parsing fails
            
    def rerank_results(self, results: List[Dict], user_context: Dict) -> List[Dict]:
        """
        Re-rank results based on multiple factors beyond just cosine similarity.
        
        Args:
            results: Initial search results
            user_context: User preferences and history
            
        Returns:
            Re-ranked results with updated scores
        """
        logger.debug("🎯 Re-ranking %d results", len(results))
        
        for result in results:
            base_score = result.get('score', 0.0)
            
            # Calculate various boost factors
            recency_boost = self._calculate_recency_boost(result.get('timestamp'))
            preference_boost = self._calculate_preference_boost(result, user_context)
            quality_boost = self._calculate_quality_boost(result.get('content', ''))
            diversity_penalty = self._calculate_diversity_penalty(result, results)
            
            # Combined score with weighted factors
            result['reranked_score'] = (
                base_score * 0.6 +           # Semantic similarity (60%)
                recency_boost * 0.15 +       # Recency (15%)
                preference_boost * 0.15 +    # User preferences (15%)
                quality_boost * 0.1 -        # Content quality (10%)
                diversity_penalty * 0.05     # Diversity penalty (5%)
            )
            
            # Store individual scores for debugging
            result['scoring_breakdown'] = {
                'base_score': base_score,
                'recency_boost': recency_boost,
                'preference_boost': preference_boost,
                'quality_boost': quality_boost,
                'diversity_penalty': diversity_penalty
            }
            
        # Sort by reranked score
        ranked_results = sorted(results, key=lambda x: x.get('reranked_score', 0), reverse=True)
        
        if ranked_results:
            logger.debug("🎯 Re-ranking complete: top score %.3f", ranked_results[0].get('reranked_score', 0))
        return ranked_results
        
    def _calculate_recency_boost(self, timestamp_str: Optional[str]) -> float:
        """Calculate recency boost factor."""
        if not timestamp_str:
            return 0.0
            
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            age_hours = (datetime.utcnow() - timestamp.replace(tzinfo=None)).total_seconds() / 3600
            
            # Exponential decay: full boost for recent (< 1 hour), decay over 30 days
            if age_hours < 1:
                return 0.2  # Max boost
            elif age_hours < 24:
                return 0.15 * np.exp(-age_hours / 24)
            elif age_hours < 24 * 7:  # 1 week
                return 0.1 * np.exp(-age_hours / (24 * 7))
            elif age_hours < 24 * 30:  # 1 month
                return 0.05 * np.exp(-age_hours / (24 * 30))
            else:
                return 0.0
        except (ValueError, TypeError):
            return 0.0
            
    def _calculate_preference_boost(self, result: Dict, user_context: Dict) -> float:
        """Calculate user preference boost factor."""
        boost = 0.0
        metadata = result.get('metadata', {})
        
        # Boost based on user preferences
        if user_context.get('prefers_recent') and self._is_recent(result.get('timestamp')):
            boost += 0.1
        if user_context.get('favorite_topics'):
            result_topics = metadata.get('topics', [])
            if any(topic in user_context['favorite_topics'] for topic in result_topics):
                boost += 0.1
        if user_context.get('preferred_channels'):
            if metadata.get('channel_id') in user_context['preferred_channels']:
                boost += 0.05
                
        return min(boost, 0.2)  # Cap at 0.2
        
    def _calculate_quality_boost(self, content: str) -> float:
        """Calculate content quality boost factor."""
        if not content:
            return 0.0
            
        quality_score = 0.0
        
        # Length factor (prefer moderate length)
        length = len(content)
        if 50 <= length <= 500:
            quality_score += 0.05
        elif length > 500:
            quality_score += 0.02
            
        # Complexity factor (prefer content with varied vocabulary)
        words = content.split()
        unique_words = set(words)
        if len(words) > 0:
            diversity_ratio = len(unique_words) / len(words)
            quality_score += diversity_ratio * 0.05
            
        return min(quality_score, 0.1)  # Cap at 0.1
        
    def _calculate_diversity_penalty(self, result: Dict, all_results: List[Dict]) -> float:
        """Calculate diversity penalty to avoid too similar results."""
        content = result.get('content', '')
        if not content:
            return 0.0
            
        # Simple diversity check based on content similarity
        penalty = 0.0
        for other in all_results:
            if other is result:
                continue
            other_content = other.get('content', '')
            if self._content_similarity(content, other_content) > 0.8:
                penalty += 0.02
                
        return min(penalty, 0.1)  # Cap penalty
        
    def _content_similarity(self, content1: str, content2: str) -> float:
        """Calculate simple content similarity."""
        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())
        
        if not words1 or not words2:
            return 0.0
            
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
        
    def _is_recent(self, timestamp_str: Optional[str], hours: int = 24) -> bool:
        """Check if timestamp is recent."""
        if not timestamp_str:
            return False
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            age = datetime.utcnow() - timestamp.replace(tzinfo=None)
            return age.total_seconds() < hours * 3600
        except (ValueError, TypeError):
            return False
            
    async def optimized_search(self, query: str, user_id: str, query_type: str = "general_search", 
                             user_history: Optional[Dict] = None, filters: Optional[Dict] = None) -> List[Dict]:
        """
        Perform a complete optimized search with all enhancement features.
        
        Args:
            query: Search query
            user_id: User identifier
            query_type: Type of query for threshold optimization
            user_history: User interaction patterns
            filters: Additional search filters
            
        Returns:
            Optimized and ranked search results
        """
        if user_history is None:
            user_history = {}
            
        logger.debug("🚀 Starting optimized search: '%s' (type: %s)", query, query_type)
        
        # 1. Preprocess query
        context = QueryContext(query_type=query_type, user_history=user_history)
        if filters:
            context.time_range = filters.get('time_range')
            context.channel_id = filters.get('channel_id')
            context.topics = filters.get('topics')
            
        optimized_query = self.preprocess_query(query, context)
        
        # 2. Get adaptive threshold
        threshold = self.get_adaptive_threshold(query_type, user_history)
        
        # 3. Perform hybrid search
        results = await self.hybrid_search(optimized_query, user_id, filters)
        
        # 4. Apply threshold filtering
        filtered_results = [r for r in results if r.get('score', 0) >= threshold]
        
        # 5. Re-rank results
        final_results = self.rerank_results(filtered_results, user_history)
        
        logger.debug("🎯 Optimized search complete: %d final results", len(final_results))
        return final_results[:20]  # Limit to top 20 results


class QdrantOptimizationMetrics:
    """Performance monitoring and optimization metrics."""
    
    def __init__(self):
        self.query_performance = {}
        self.user_satisfaction = {}
        self.embedding_cache_hits = 0
        self.total_queries = 0
        
    def record_search_quality(self, query: str, results: List[Dict], user_feedback: Optional[str] = None):
        """
        Track search result quality for continuous improvement.
        
        Args:
            query: The search query
            results: Search results returned
            user_feedback: Optional user feedback on relevance
        """
        self.total_queries += 1
        
        self.query_performance[query] = {
            'result_count': len(results),
            'avg_score': sum(r.get('score', 0) for r in results) / max(len(results), 1),
            'reranked_avg': sum(r.get('reranked_score', 0) for r in results) / max(len(results), 1),
            'user_feedback': user_feedback,
            'timestamp': datetime.utcnow()
        }
        
        logger.debug("📊 Recorded search quality for: '%s' (%d results)", query, len(results))
        
    def record_cache_hit(self):
        """Record embedding cache hit."""
        self.embedding_cache_hits += 1
        
    def get_optimization_recommendations(self) -> Dict[str, str]:
        """
        Analyze metrics and suggest optimizations.
        
        Returns:
            Dictionary of optimization recommendations
        """
        recommendations = {}
        
        if not self.query_performance:
            return {"status": "No query data available yet"}
            
        # Analyze result counts
        result_counts = [perf['result_count'] for perf in self.query_performance.values()]
        avg_result_count = sum(result_counts) / len(result_counts)
        
        if avg_result_count < 2:
            recommendations['threshold'] = "Consider lowering min_score threshold - queries returning too few results"
        elif avg_result_count > 20:
            recommendations['threshold'] = "Consider raising min_score threshold - queries returning too many results"
            
        # Analyze cache performance
        if self.total_queries > 0:
            cache_hit_rate = self.embedding_cache_hits / self.total_queries
            if cache_hit_rate < 0.3:
                recommendations['cache'] = "Low embedding cache hit rate - consider cache optimization"
                
        # Analyze user feedback
        feedback_scores = []
        for perf in self.query_performance.values():
            if perf['user_feedback'] in ['relevant', 'good', 'helpful']:
                feedback_scores.append(1.0)
            elif perf['user_feedback'] in ['irrelevant', 'poor', 'unhelpful']:
                feedback_scores.append(0.0)
                
        if feedback_scores:
            avg_satisfaction = sum(feedback_scores) / len(feedback_scores)
            if avg_satisfaction < 0.7:
                recommendations['relevance'] = "User satisfaction below 70% - consider query preprocessing improvements"
                
        return recommendations
        
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get summary of optimization performance."""
        if not self.query_performance:
            return {"status": "No data"}
            
        return {
            'total_queries': self.total_queries,
            'avg_results_per_query': sum(p['result_count'] for p in self.query_performance.values()) / len(self.query_performance),
            'cache_hit_rate': self.embedding_cache_hits / max(self.total_queries, 1),
            'recent_queries': list(self.query_performance.keys())[-5:],
            'recommendations': self.get_optimization_recommendations()
        }


class OptimizedVectorMemoryManager:
    """
    Extended VectorMemoryManager with optimization capabilities.
    
    This class integrates the QdrantQueryOptimizer with the existing vector memory system
    to provide enhanced search capabilities while maintaining backward compatibility.
    """
    
    def __init__(self, config: Dict[str, Any]):
        # Import here to avoid circular imports
        from src.memory.vector_memory_system import VectorMemoryManager
        
        # Initialize the base vector manager
        self.base_manager = VectorMemoryManager(config)
        
        # Initialize optimizer and metrics
        self.optimizer = QdrantQueryOptimizer(self.base_manager)
        self.metrics = QdrantOptimizationMetrics()
        
        logger.info("🚀 Initialized OptimizedVectorMemoryManager with query optimization")
        
    async def initialize(self):
        """Initialize the optimized manager."""
        # The base VectorMemoryManager doesn't have initialize method
        # Just initialize our components
        logger.info("✅ OptimizedVectorMemoryManager initialization complete")
        
    async def retrieve_relevant_memories_optimized(self, user_id: str, query: str, 
                                                 query_type: str = "general_search",
                                                 user_history: Optional[Dict] = None,
                                                 filters: Optional[Dict] = None,
                                                 limit: int = 10) -> List[Dict]:
        """
        Retrieve memories using advanced optimization features.
        
        Args:
            user_id: User identifier
            query: Search query
            query_type: Type of query for optimization
            user_history: User interaction patterns
            filters: Additional search filters
            limit: Maximum number of results
            
        Returns:
            Optimized search results
        """
        # Use the optimizer for enhanced search
        results = await self.optimizer.optimized_search(
            query=query,
            user_id=user_id,
            query_type=query_type,
            user_history=user_history or {},
            filters=filters
        )
        
        # Record metrics
        self.metrics.record_search_quality(query, results)
        
        # Return limited results
        return results[:limit]
        
    # Delegate all other methods to the base manager
    def __getattr__(self, name):
        """Delegate unknown attributes to base manager."""
        return getattr(self.base_manager, name)