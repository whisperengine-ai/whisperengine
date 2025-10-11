"""
Qdrant query optimization and filtering.
"""
import logging
import os
import re
import numpy as np
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any, Set

logger = logging.getLogger(__name__)


def normalize_bot_name(bot_name: str) -> str:
    """
    Normalize bot name for consistent memory storage and retrieval.
    Duplicate of function in vector_memory_system.py to avoid circular imports.
    """
    if not bot_name or not isinstance(bot_name, str):
        return "unknown"
    
    # Step 1: Trim and lowercase
    normalized = bot_name.strip().lower()
    
    # Step 2: Replace spaces with underscores
    normalized = re.sub(r'\s+', '_', normalized)
    
    # Step 3: Remove special characters except underscore/hyphen/alphanumeric
    normalized = re.sub(r'[^a-z0-9_-]', '', normalized)
    
    # Step 4: Collapse multiple underscores/hyphens
    normalized = re.sub(r'[_-]+', '_', normalized)
    
    # Step 5: Remove leading/trailing underscores
    normalized = normalized.strip('_-')
    
    return normalized if normalized else "unknown"


def get_normalized_bot_name_from_env() -> str:
    """Get normalized bot name from environment variables with fallback"""
    raw_bot_name = (
        os.getenv("DISCORD_BOT_NAME") or 
        os.getenv("BOT_NAME") or 
        "unknown"
    )
    return normalize_bot_name(raw_bot_name.strip())


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

    async def _search_with_vector_store(self, query: str, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Adapter method to handle parameter conversion between limit and top_k.
        
        Args:
            query: Search query
            user_id: User ID
            limit: Number of results to return
            
        Returns:
            List of memory results
        """
        if not self.vector_manager:
            logger.error("Vector manager not initialized")
            return []
            
        try:
            # First check what type of object we're dealing with
            manager_class = self.vector_manager.__class__.__name__
            
            if manager_class == 'VectorMemoryManager':
                # For VectorMemoryManager, use search_memories with limit parameter
                return await self.vector_manager.search_memories(
                    user_id=user_id,
                    query=query,
                    limit=limit
                )
            elif hasattr(self.vector_manager, 'search_memories'):
                # For other objects with search_memories, use the standard signature
                return await self.vector_manager.search_memories(
                    user_id=user_id,
                    query=query,
                    limit=limit
                )
            else:
                # Object has no search_memories method
                logger.error(f"Vector manager of type {manager_class} has no search_memories method")
                return []
        except Exception as e:
            logger.error(f"Vector store search failed: {e}")
            return []
        
    async def optimized_search(self, query: str, user_id: str, query_type: str = "general_search",
                            user_history: Optional[Dict] = None, filters: Optional[Dict] = None,
                            limit: int = 15) -> List[Dict[str, Any]]:  # 🔧 HARMONIZED: Increased from 10 to 15 to match main API
        """
        Main entry point for optimized search - called by vector memory system.
        
        Args:
            query: Search query
            user_id: User ID
            query_type: Type of query for optimization strategies
            user_history: User's interaction history
            filters: Filter configuration
            limit: Number of results to return
            
        Returns:
            List of memory results
        """
        logger.info(f"🚀 QDRANT-OPTIMIZATION: Running optimized search for '{query}' (type: {query_type})")
        
        try:
            # Create context for query optimization
            context = QueryContext(
                query_type=query_type,
                user_history=user_history or {},
                channel_id=filters.get('channel_id') if filters else None,
                topics=filters.get('topics') if filters else None
            )
            
            # Optimize query for better semantic search
            optimized_query = self.preprocess_query(query, context)
            logger.debug(f"🔍 Query optimization: '{query}' → '{optimized_query}'")
            
            # Perform search with optimized filters
            results = await self.search_with_filters(
                query=optimized_query,
                user_id=user_id,
                filters=filters,
                limit=limit
            )
            
            # 🔧 TUNING: Add debug logging for zero results
            if not results:
                logger.warning(f"🔧 QDRANT-OPTIMIZATION: No results found for query '{query}' (optimized: '{optimized_query}') - user_id: {user_id}")
                # Try a broader search with no filters as diagnostic
                try:
                    diagnostic_results = await self._search_with_vector_store(query=query, user_id=user_id, limit=10)  # 🔧 INCREASED: From 5 to 10 for better diagnostics
                    logger.info(f"🔧 DIAGNOSTIC: Broader search found {len(diagnostic_results)} results")
                except Exception as diag_e:
                    logger.error(f"🔧 DIAGNOSTIC: Broader search also failed: {diag_e}")
            else:
                # Log similarity scores for debugging
                top_scores = [r.get('score', 0.0) for r in results[:3]]
                logger.debug(f"🔧 SEARCH SCORES: Top 3 similarity scores: {top_scores}")
            
            # Re-rank if user history available
            if user_history:
                results = self.rerank_results(results, user_history)
            
            # Limit to requested number
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Qdrant filtering failed: {e}")
            # Fallback to unfiltered search
            return await self._search_with_vector_store(query=query, user_id=user_id, limit=limit)
            
    def preprocess_query(self, query: str, context: Optional[QueryContext] = None) -> str:
        """
        Preprocess and enhance queries for better semantic search.
        
        Args:
            query: Raw user query
            context: Query context for optimization
            
        Returns:
            Optimized query string
        """
        # 🔧 TEMPORAL QUERY FIX: Don't remove stop words from temporal/memory queries
        # as they contain important contextual information
        temporal_indicators = ['what', 'have', 'we', 'talked', 'remember', 'recall', 'discussed']
        is_memory_query = any(indicator in query.lower() for indicator in temporal_indicators)
        
        if is_memory_query:
            # For memory/temporal queries, preserve original structure
            return query.strip()
        
        # Use centralized preprocessing for non-temporal queries
        from src.utils.stop_words import optimize_query
        processed_query = optimize_query(query, min_word_length=2)
        
        logger.debug("🔍 Query optimization: '%s' → '%s'", query, processed_query)
        return processed_query
        
    async def search_with_filters(self, query: str, user_id: str, filters: Optional[Dict] = None,
                                limit: int = 10) -> List[Dict]:
        """
        Execute a search with advanced filtering and query optimization.
        
        Args:
            query: Search query
            user_id: User ID
            filters: Filter configuration
            limit: Number of results
            
        Returns:
            Filtered and ranked results
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
            # 🎯 NORMALIZED Bot-specific filtering for multi-bot architecture
            models.FieldCondition(key="bot_name", match=models.MatchValue(value=get_normalized_bot_name_from_env()))
        ]
        
        # Content exclusion conditions (most important for our debugging contamination fix)
        must_not_conditions = []
        
        if filters and isinstance(filters, dict):
            # Time range filtering (if specified)
            time_range = filters.get('time_range')
            if time_range:
                if time_range.get('start'):
                    must_conditions.append(
                        models.FieldCondition(
                            key="timestamp",
                            range=models.Range(
                                gte=time_range['start'].isoformat()
                            )
                        )
                    )
                if time_range.get('end'):
                    must_conditions.append(
                        models.FieldCondition(
                            key="timestamp",
                            range=models.Range(
                                lte=time_range['end'].isoformat()
                            )
                        )
                    )
            
            # Topic filtering
            topics = filters.get('topics', [])
            if topics:
                topic_conditions = []
                for topic in topics:
                    topic_conditions.append(
                        models.FieldCondition(key="topics", match=models.MatchValue(value=topic))
                    )
                if topic_conditions:
                    must_conditions.append(models.HasIdFilter(should=topic_conditions))
            
            # Channel-specific filtering (for Discord integration)
            channel_id = filters.get('channel_id')
            if channel_id:
                must_conditions.append(
                    models.FieldCondition(key="channel_id", match=models.MatchValue(value=channel_id))
                )
            
            # Content exclusions (critical for debugging isolation)
            excluded_content = filters.get('exclude_content', [])
            if excluded_content:
                for content in excluded_content:
                    must_not_conditions.append(
                        models.FieldCondition(key="content", match=models.MatchText(text=content))
                    )
        
        return {
            "must": must_conditions,
            "must_not": must_not_conditions
        }
    
    async def _search_with_qdrant_filters(self, query: str, user_id: str,
                                        qdrant_filters: Dict, limit: int = 10) -> List[Dict]:
        """
        Execute search with Qdrant's native filtering capabilities.
        
        Args:
            query: Search query
            user_id: User identifier
            qdrant_filters: Prepared Qdrant filters
            limit: Maximum results to return
            
        Returns:
            List of filtered search results
        """
        try:
            # Use enhanced preprocessing
            optimized_query = self.preprocess_query(query)
            
            # Basic semantic search with the vector store
            semantic_results = await self._search_with_vector_store(
                query=optimized_query,
                user_id=user_id,
                limit=limit
            )
            
            # Post-process results to filter out unwanted items
            filtered_results = []
            for result in semantic_results:
                should_exclude = False
                
                # Check if content matches any exclusion patterns
                if 'must_not' in qdrant_filters:
                    for condition in qdrant_filters['must_not']:
                        if isinstance(condition, dict):
                            pattern = condition.get('match', {}).get('text', '')
                            if pattern and pattern.lower() in result.get('content', '').lower():
                                should_exclude = True
                                break
                
                if not should_exclude:
                    filtered_results.append(result)
            
            logger.debug(f"🛡️ Filtered {len(semantic_results) - len(filtered_results)} contaminated memories")
            return filtered_results
            
        except Exception as e:
            logger.error(f"Qdrant filtering failed: {e}")
            # Fallback to unfiltered search
            return await self._search_with_vector_store(query=query, user_id=user_id, limit=limit)
        
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
        """Calculate preference boost based on user context."""
        boost = 0.0
        content = result.get('content', '').lower()
        
        # Boost based on user's preferred topics
        preferred_topics = user_context.get('preferred_topics', [])
        for topic in preferred_topics:
            if topic.lower() in content:
                boost += 0.05
                
        # Adjust based on interaction history
        interaction_score = user_context.get('interaction_scores', {}).get(
            result.get('memory_id', ''), 0.0
        )
        boost += min(interaction_score * 0.1, 0.1)  # Cap at 0.1
        
        return min(boost, 0.2)  # Cap total boost at 0.2
        
    def _calculate_quality_boost(self, content: str) -> float:
        """Calculate content quality boost."""
        if not content:
            return 0.0
            
        # Length-based quality (moderate lengths preferred)
        word_count = len(content.split())
        if 20 <= word_count <= 200:
            length_score = 0.1
        elif 10 <= word_count < 20 or 200 < word_count <= 300:
            length_score = 0.05
        else:
            length_score = 0.0
            
        # Basic coherence check (proper sentences)
        has_proper_sentences = (
            content[0].isupper() and  # Starts with capital
            content.strip()[-1] in '.!?'  # Ends with punctuation
        )
        coherence_score = 0.1 if has_proper_sentences else 0.0
        
        return length_score + coherence_score
        
    def _calculate_diversity_penalty(self, result: Dict, all_results: List[Dict]) -> float:
        """Calculate diversity penalty to avoid redundant results."""
        penalty = 0.0
        current_content = result.get('content', '').lower()
        
        # Compare with other results
        for other in all_results:
            if other is result:
                continue
                
            other_content = other.get('content', '').lower()
            
            # Simple similarity check
            if len(current_content) > 20 and current_content in other_content:
                penalty += 0.1
            elif len(other_content) > 20 and other_content in current_content:
                penalty += 0.1
                
        return min(penalty, 0.2)  # Cap penalty at 0.2


class QdrantOptimizationMetrics:
    """Track and analyze optimization performance metrics."""
    
    def __init__(self):
        self.query_times = []
        self.result_counts = []
        self.optimization_gains = []
        
    def record_query(self, duration: float, results: int, optimization_gain: float):
        """Record metrics for a query."""
        self.query_times.append(duration)
        self.result_counts.append(results)
        self.optimization_gains.append(optimization_gain)
        
    def get_average_metrics(self) -> Dict[str, float]:
        """Calculate average performance metrics."""
        if not self.query_times:
            return {
                "avg_query_time": 0.0,
                "avg_results": 0.0,
                "avg_optimization_gain": 0.0
            }
            
        return {
            "avg_query_time": sum(self.query_times) / len(self.query_times),
            "avg_results": sum(self.result_counts) / len(self.result_counts),
            "avg_optimization_gain": sum(self.optimization_gains) / len(self.optimization_gains)
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
        Enhanced memory retrieval with query optimization.
        
        Args:
            user_id: User identifier
            query: Search query
            query_type: Type of query for optimization
            user_history: User's interaction history
            filters: Filter configuration
            limit: Maximum results to return
            
        Returns:
            List of relevant memories
        """
        try:
            context = QueryContext(
                query_type=query_type,
                user_history=user_history
            )
            
            # Apply query optimization
            optimized_query = self.optimizer.preprocess_query(query, context)
            
            # Perform filtered search
            results = await self.optimizer.search_with_filters(
                query=optimized_query,
                user_id=user_id,
                filters=filters,
                limit=limit
            )
            
            # Re-rank results if user context available
            if user_history:
                results = self.optimizer.rerank_results(results, user_history)
                
            # Trim to requested limit
            results = results[:limit]
            
            logger.info(f"🎯 Retrieved {len(results)} memories with optimization")
            return results
            
        except Exception as e:
            logger.error(f"Optimized retrieval failed: {e}")
            # Fallback to base retrieval
            # All memory managers should use the standard signature now
            return await self.base_manager.search_memories(
                user_id=user_id,
                query=query,
                limit=limit
            )