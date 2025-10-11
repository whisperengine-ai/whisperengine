"""
Multi-Vector Intelligence System - Sprint 2 Enhancement

Intelligent query classification and multi-vector retrieval system that leverages
all 3 named vectors (content, emotion, semantic) based on query context and intent.

This system transforms WhisperEngine from single-vector content search to
comprehensive multi-dimensional intelligence using emotional and semantic context.

Core Features:
- Intelligent query classification (content, emotional, semantic, hybrid)
- Dynamic vector selection based on query intent
- Multi-vector fusion for complex queries
- Emotional intelligence enhancement
- Semantic relationship detection
- Performance optimization with vector prioritization

Integration Points:
- Sprint 1 TrendWise: Multi-vector confidence analysis
- Sprint 2 MemoryBoost: Enhanced memory optimization
- Vector Memory System: Intelligent retrieval strategies
"""

import logging
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class QueryType(Enum):
    """Types of queries for intelligent vector selection"""
    CONTENT_SEMANTIC = "content_semantic"      # Facts, information, technical content
    EMOTIONAL_CONTEXT = "emotional_context"    # Feelings, emotions, mood, sentiment
    SEMANTIC_CONCEPTUAL = "semantic_conceptual" # Concepts, relationships, abstract ideas
    HYBRID_MULTI = "hybrid_multi"             # Complex queries needing multiple vectors
    TEMPORAL_CHRONOLOGICAL = "temporal_chronological" # Time-based queries


class VectorStrategy(Enum):
    """Vector usage strategies"""
    CONTENT_PRIMARY = "content_primary"        # Content vector with semantic backup
    EMOTION_PRIMARY = "emotion_primary"        # Emotion vector with content backup
    SEMANTIC_PRIMARY = "semantic_primary"      # Semantic vector with content backup
    BALANCED_FUSION = "balanced_fusion"        # Equal weight all 3 vectors
    WEIGHTED_COMBINATION = "weighted_combination" # Custom weights per vector
    SEQUENTIAL_SEARCH = "sequential_search"    # Search each vector sequentially


@dataclass
class QueryClassification:
    """Classification result for intelligent vector selection"""
    query_type: QueryType
    primary_vector: str                        # "content", "emotion", or "semantic"
    secondary_vectors: List[str]               # Additional vectors to use
    strategy: VectorStrategy
    confidence: float                          # Classification confidence (0-1)
    reasoning: str                            # Human-readable explanation
    vector_weights: Dict[str, float]          # Weights for each vector
    emotional_indicators: List[str]           # Detected emotional keywords
    semantic_indicators: List[str]            # Detected conceptual keywords
    content_indicators: List[str]             # Detected factual keywords


@dataclass
class MultiVectorResult:
    """Result from multi-vector search"""
    memories: List[Dict[str, Any]]
    vector_contributions: Dict[str, int]      # How many results from each vector
    fusion_strategy: str                      # Strategy used for combination
    performance_metrics: Dict[str, float]     # Search performance data
    classification: QueryClassification       # Original query classification


class MultiVectorIntelligence:
    """
    Intelligent multi-vector query classification and retrieval system.
    
    Analyzes queries to determine optimal vector usage strategy, then coordinates
    multi-vector searches for maximum intelligence from all 3 named vectors.
    """
    
    def __init__(self, temporal_client=None):
        """Initialize multi-vector intelligence system
        
        Args:
            temporal_client: Optional InfluxDB temporal client for classification accuracy logging
        """
        self.logger = logger
        self.temporal_client = temporal_client
        
        # Emotional indicators for emotion vector selection
        self.emotional_keywords = {
            'positive': ['happy', 'joy', 'excited', 'love', 'wonderful', 'amazing', 'great', 'fantastic', 'awesome'],
            'negative': ['sad', 'angry', 'frustrated', 'upset', 'worried', 'anxious', 'disappointed', 'hurt'],
            'neutral': ['calm', 'peaceful', 'relaxed', 'content', 'satisfied'],
            'emotional_queries': ['feel', 'feeling', 'emotion', 'mood', 'sentiment', 'emotional', 'emotionally'],
            'relationship': ['relationship', 'friendship', 'connection', 'bond', 'trust', 'intimacy', 'closeness']
        }
        
        # Semantic/conceptual indicators for semantic vector selection  
        self.semantic_keywords = {
            'concepts': ['concept', 'idea', 'theory', 'principle', 'philosophy', 'belief', 'meaning', 'significance'],
            'relationships': ['connection', 'relationship', 'correlation', 'association', 'link', 'pattern'],
            'abstract': ['abstract', 'metaphor', 'symbol', 'representation', 'essence', 'nature', 'characteristic'],
            'learning': ['learn', 'understand', 'comprehend', 'grasp', 'insight', 'realization', 'awareness'],
            'personality': ['personality', 'character', 'trait', 'behavior', 'style', 'approach', 'tendency']
        }
        
        # Content/factual indicators for content vector selection
        self.content_keywords = {
            'factual': ['fact', 'information', 'data', 'detail', 'specific', 'exactly', 'precisely', 'literally'],
            'technical': ['technical', 'specification', 'parameter', 'configuration', 'setting', 'code', 'algorithm'],
            'instructional': ['how', 'what', 'when', 'where', 'why', 'step', 'process', 'method', 'procedure'],
            'descriptive': ['describe', 'explain', 'detail', 'elaborate', 'clarify', 'specify', 'define']
        }
        
        # Temporal indicators (handled separately by existing temporal detection)
        self.temporal_keywords = ['yesterday', 'today', 'tomorrow', 'last', 'first', 'recent', 'earlier', 'later', 'ago', 'since']
        
        # Performance tracking
        self.classification_stats = {
            'total_classifications': 0,
            'content_queries': 0,
            'emotional_queries': 0,
            'semantic_queries': 0,
            'hybrid_queries': 0,
            'temporal_queries': 0
        }
    
    async def classify_query(self, query: str, user_context: Optional[str] = None) -> QueryClassification:
        """
        Classify query to determine optimal vector usage strategy.
        
        Args:
            query: Search query to classify
            user_context: Optional conversation context for better classification
            
        Returns:
            QueryClassification with recommended vector strategy
        """
        try:
            self.logger.info("🎯 MULTI-VECTOR: Classifying query: '%s'", query[:50] + "..." if len(query) > 50 else query)
            
            query_lower = query.lower()
            context_lower = user_context.lower() if user_context else ""
            combined_text = f"{query_lower} {context_lower}"
            
            # Initialize scoring
            content_score = 0.0
            emotion_score = 0.0
            semantic_score = 0.0
            
            emotional_indicators = []
            semantic_indicators = []
            content_indicators = []
            
            # Score emotional indicators (FIXED: Higher weight for emotional keywords)
            # Emotional queries should be prioritized as they're more nuanced
            for _, keywords in self.emotional_keywords.items():
                matches = [kw for kw in keywords if kw in combined_text]
                if matches:
                    emotion_score += len(matches) * 1.5  # INCREASED from 1.0 to 1.5
                    emotional_indicators.extend(matches)
            
            # Score semantic/conceptual indicators
            for _, keywords in self.semantic_keywords.items():
                matches = [kw for kw in keywords if kw in combined_text]
                if matches:
                    semantic_score += len(matches) * 1.2  # INCREASED from 1.0 to 1.2
                    semantic_indicators.extend(matches)
            
            # Score content/factual indicators (keep at 1.0 as baseline)
            for _, keywords in self.content_keywords.items():
                matches = [kw for kw in keywords if kw in combined_text]
                if matches:
                    content_score += len(matches) * 1.0
                    content_indicators.extend(matches)
            
            # Check for temporal queries (delegate to existing system)
            temporal_matches = [kw for kw in self.temporal_keywords if kw in query_lower]
            if temporal_matches:
                return self._create_temporal_classification(temporal_matches)
            
            # Determine primary vector and strategy
            scores = {
                'content': content_score,
                'emotion': emotion_score, 
                'semantic': semantic_score
            }
            
            # Normalize scores
            total_score = sum(scores.values())
            if total_score > 0:
                normalized_scores = {k: v / total_score for k, v in scores.items()}
            else:
                # Default to balanced if no clear indicators
                normalized_scores = {'content': 0.5, 'emotion': 0.25, 'semantic': 0.25}
            
            # Determine strategy based on score distribution
            max_score = max(normalized_scores.values())
            primary_vector = max(normalized_scores.keys(), key=lambda k: normalized_scores[k])
            
            # FIXED: More aggressive thresholds for clearer classification
            # 0.45 threshold allows single strong indicator to dominate
            # This improves emotional query detection when mixed with content words
            if max_score > 0.45:
                # Clear primary vector (lowered from 0.6 to 0.45)
                strategy = self._get_primary_strategy(primary_vector)
                query_type = self._get_query_type(primary_vector)
                secondary_vectors = [v for v in ['content', 'emotion', 'semantic'] if v != primary_vector]
                confidence = max_score
            elif max_score > 0.35:
                # Moderate preference - use weighted combination (lowered from 0.4 to 0.35)
                strategy = VectorStrategy.WEIGHTED_COMBINATION
                query_type = QueryType.HYBRID_MULTI
                secondary_vectors = [v for v in ['content', 'emotion', 'semantic'] if v != primary_vector]
                confidence = max_score * 0.8  # Lower confidence for hybrid
            else:
                # No clear preference - use balanced fusion
                strategy = VectorStrategy.BALANCED_FUSION
                query_type = QueryType.HYBRID_MULTI
                primary_vector = 'content'  # Default primary
                secondary_vectors = ['emotion', 'semantic']
                confidence = 0.5
            
            # Generate reasoning
            reasoning = self._generate_reasoning(
                emotional_indicators, semantic_indicators, content_indicators
            )
            
            classification = QueryClassification(
                query_type=query_type,
                primary_vector=primary_vector,
                secondary_vectors=secondary_vectors,
                strategy=strategy,
                confidence=confidence,
                reasoning=reasoning,
                vector_weights=normalized_scores,
                emotional_indicators=emotional_indicators,
                semantic_indicators=semantic_indicators,
                content_indicators=content_indicators
            )
            
            # Update stats
            self.classification_stats['total_classifications'] += 1
            if query_type == QueryType.CONTENT_SEMANTIC:
                self.classification_stats['content_queries'] += 1
            elif query_type == QueryType.EMOTIONAL_CONTEXT:
                self.classification_stats['emotional_queries'] += 1
            elif query_type == QueryType.SEMANTIC_CONCEPTUAL:
                self.classification_stats['semantic_queries'] += 1
            elif query_type == QueryType.HYBRID_MULTI:
                self.classification_stats['hybrid_queries'] += 1
            
            self.logger.info("🎯 CLASSIFICATION: %s primary (%.2f confidence) - %s", primary_vector, confidence, reasoning)
            return classification
            
        except (ValueError, KeyError, AttributeError) as e:
            self.logger.error("Query classification failed: %s", str(e))
            # Fallback to content-primary
            return self._create_fallback_classification()
    
    def _create_temporal_classification(self, temporal_matches: List[str]) -> QueryClassification:
        """Create classification for temporal queries"""
        return QueryClassification(
            query_type=QueryType.TEMPORAL_CHRONOLOGICAL,
            primary_vector='content',  # Temporal uses existing content-based temporal system
            secondary_vectors=[],
            strategy=VectorStrategy.CONTENT_PRIMARY,
            confidence=0.9,
            reasoning=f"Temporal query detected: {', '.join(temporal_matches)}",
            vector_weights={'content': 1.0, 'emotion': 0.0, 'semantic': 0.0},
            emotional_indicators=[],
            semantic_indicators=[],
            content_indicators=temporal_matches
        )
    
    def _get_primary_strategy(self, primary_vector: str) -> VectorStrategy:
        """Get strategy for primary vector"""
        strategy_map = {
            'content': VectorStrategy.CONTENT_PRIMARY,
            'emotion': VectorStrategy.EMOTION_PRIMARY,
            'semantic': VectorStrategy.SEMANTIC_PRIMARY
        }
        return strategy_map.get(primary_vector, VectorStrategy.CONTENT_PRIMARY)
    
    def _get_query_type(self, primary_vector: str) -> QueryType:
        """Get query type for primary vector"""
        type_map = {
            'content': QueryType.CONTENT_SEMANTIC,
            'emotion': QueryType.EMOTIONAL_CONTEXT,
            'semantic': QueryType.SEMANTIC_CONCEPTUAL
        }
        return type_map.get(primary_vector, QueryType.CONTENT_SEMANTIC)
    
    def _generate_reasoning(self, emotional_indicators: List[str], semantic_indicators: List[str],
                          content_indicators: List[str]) -> str:
        """Generate human-readable reasoning for classification"""
        reasons = []
        
        if emotional_indicators:
            reasons.append(f"emotional keywords: {', '.join(emotional_indicators[:3])}")
        if semantic_indicators:
            reasons.append(f"conceptual keywords: {', '.join(semantic_indicators[:3])}")
        if content_indicators:
            reasons.append(f"factual keywords: {', '.join(content_indicators[:3])}")
            
        if not reasons:
            return "Default content vector selection"
        
        return f"Detected {', '.join(reasons)}"
    
    def _create_fallback_classification(self) -> QueryClassification:
        """Create fallback classification for errors"""
        return QueryClassification(
            query_type=QueryType.CONTENT_SEMANTIC,
            primary_vector='content',
            secondary_vectors=['emotion', 'semantic'],
            strategy=VectorStrategy.CONTENT_PRIMARY,
            confidence=0.3,
            reasoning="Fallback classification due to analysis error",
            vector_weights={'content': 0.6, 'emotion': 0.2, 'semantic': 0.2},
            emotional_indicators=[],
            semantic_indicators=[],
            content_indicators=[]
        )
    
    def get_classification_stats(self) -> Dict[str, Any]:
        """Get classification statistics"""
        total = self.classification_stats['total_classifications']
        if total == 0:
            return self.classification_stats
            
        return {
            **self.classification_stats,
            'content_percentage': (self.classification_stats['content_queries'] / total) * 100,
            'emotional_percentage': (self.classification_stats['emotional_queries'] / total) * 100,
            'semantic_percentage': (self.classification_stats['semantic_queries'] / total) * 100,
            'hybrid_percentage': (self.classification_stats['hybrid_queries'] / total) * 100,
            'temporal_percentage': (self.classification_stats['temporal_queries'] / total) * 100
        }
    
    async def log_classification_to_influxdb(
        self,
        bot_name: str,
        user_id: str,
        query: str,
        classification: QueryClassification,
        actual_results_quality: Optional[float] = None,
        session_id: Optional[str] = None
    ) -> bool:
        """
        Log classification decision and accuracy to InfluxDB for monitoring and optimization.
        
        This enables us to:
        - Track keyword-based classification accuracy over time
        - Identify queries where classification fails (low result quality)
        - Detect patterns that need new keywords or better strategies
        - Monitor emotional/semantic/content query distributions
        - Validate that our classification approach is sufficient
        
        Args:
            bot_name: Name of the bot
            user_id: User identifier
            query: Original search query
            classification: Classification result from classify_query()
            actual_results_quality: Optional quality score (0-1) based on result relevance
                                   Can be computed from result scores or user feedback
            session_id: Optional session identifier
            
        Returns:
            bool: Success status
        """
        if not self.temporal_client or not self.temporal_client.enabled:
            return False
        
        try:
            from influxdb_client.client.write.point import Point
            
            # Create InfluxDB point for vector classification
            point = Point("vector_classification") \
                .tag("bot", bot_name) \
                .tag("user_id", user_id) \
                .tag("query_type", classification.query_type.value) \
                .tag("primary_vector", classification.primary_vector) \
                .tag("strategy", classification.strategy.value)
            
            if session_id:
                point = point.tag("session_id", session_id)
            
            # Store classification metrics
            point = point \
                .field("confidence", classification.confidence) \
                .field("content_weight", classification.vector_weights.get('content', 0.0)) \
                .field("emotion_weight", classification.vector_weights.get('emotion', 0.0)) \
                .field("semantic_weight", classification.vector_weights.get('semantic', 0.0)) \
                .field("emotional_indicators_count", len(classification.emotional_indicators)) \
                .field("semantic_indicators_count", len(classification.semantic_indicators)) \
                .field("content_indicators_count", len(classification.content_indicators)) \
                .field("query_length", len(query))
            
            # Store actual results quality if available (for accuracy tracking)
            if actual_results_quality is not None:
                point = point.field("results_quality", actual_results_quality)
                # Compute accuracy: high confidence + high quality = accurate classification
                accuracy = 1.0 if (classification.confidence > 0.6 and actual_results_quality > 0.6) else 0.0
                point = point.field("classification_accurate", accuracy)
            
            # Write to InfluxDB
            self.temporal_client.write_api.write(
                bucket=os.getenv('INFLUXDB_BUCKET', 'whisperengine'),
                record=point
            )
            
            self.logger.debug(
                "📊 CLASSIFICATION LOGGED: %s vector for '%s' (%.2f confidence, quality: %s)",
                classification.primary_vector,
                query[:30] + "..." if len(query) > 30 else query,
                classification.confidence,
                f"{actual_results_quality:.2f}" if actual_results_quality is not None else "N/A"
            )
            return True
            
        except (ImportError, AttributeError, ConnectionError, KeyError) as e:
            self.logger.error("Failed to log classification to InfluxDB: %s", e)
            return False


class MultiVectorSearchCoordinator:
    """
    Coordinates multi-vector searches based on query classification.
    
    Uses intelligent vector selection to execute optimal search strategies
    across content, emotion, and semantic vectors for maximum intelligence.
    """
    
    def __init__(self, vector_memory_system, multi_vector_intelligence=None):
        """Initialize multi-vector search coordinator"""
        self.vector_memory_system = vector_memory_system
        self.intelligence = multi_vector_intelligence or create_multi_vector_intelligence()
        self.logger = logger
        
        # Performance tracking
        self.search_stats = {
            'total_searches': 0,
            'content_searches': 0,
            'emotion_searches': 0,
            'semantic_searches': 0,
            'hybrid_searches': 0,
            'avg_improvement': 0.0
        }
    
    async def intelligent_multi_vector_search(
        self,
        query: str,
        user_id: str,
        limit: int = 25,
        conversation_context: Optional[str] = None,
        memory_types: Optional[List[str]] = None
    ) -> MultiVectorResult:
        """
        Execute intelligent multi-vector search based on query classification.
        
        Args:
            query: Search query
            user_id: User identifier
            limit: Maximum results to return
            conversation_context: Optional conversation context
            memory_types: Optional memory type filters
            
        Returns:
            MultiVectorResult with memories and metadata
        """
        import time
        start_time = time.time()
        
        try:
            # Step 1: Classify query to determine vector strategy
            classification = await self.intelligence.classify_query(query, conversation_context)
            
            self.logger.info("🎯 MULTI-VECTOR SEARCH: %s strategy for query", classification.strategy.value)
            
            # Step 2: Execute search based on classification
            if classification.query_type == QueryType.TEMPORAL_CHRONOLOGICAL:
                memories = await self._execute_temporal_search(query, user_id, limit)
                fusion_strategy = "temporal_chronological"
                vector_contributions = {"content": len(memories)}
                
            elif classification.strategy == VectorStrategy.CONTENT_PRIMARY:
                memories = await self._execute_content_primary_search(
                    query, user_id, limit, classification, memory_types
                )
                fusion_strategy = "content_primary"
                vector_contributions = {"content": len(memories)}
                
            elif classification.strategy == VectorStrategy.EMOTION_PRIMARY:
                memories = await self._execute_emotion_primary_search(
                    query, user_id, limit, classification, memory_types
                )
                fusion_strategy = "emotion_primary" 
                vector_contributions = {"emotion": len(memories)}
                
            elif classification.strategy == VectorStrategy.SEMANTIC_PRIMARY:
                memories = await self._execute_semantic_primary_search(
                    query, user_id, limit, classification, memory_types
                )
                fusion_strategy = "semantic_primary"
                vector_contributions = {"semantic": len(memories)}
                
            elif classification.strategy == VectorStrategy.BALANCED_FUSION:
                memories, vector_contributions = await self._execute_balanced_fusion_search(
                    query, user_id, limit, classification, memory_types
                )
                fusion_strategy = "balanced_fusion"
                
            elif classification.strategy == VectorStrategy.WEIGHTED_COMBINATION:
                memories, vector_contributions = await self._execute_weighted_combination_search(
                    query, user_id, limit, classification, memory_types
                )
                fusion_strategy = "weighted_combination"
                
            else:
                # Fallback to content search
                memories = await self._execute_content_primary_search(
                    query, user_id, limit, classification, memory_types
                )
                fusion_strategy = "content_fallback"
                vector_contributions = {"content": len(memories)}
            
            # Step 3: Calculate performance metrics
            processing_time = (time.time() - start_time) * 1000
            performance_metrics = {
                'processing_time_ms': processing_time,
                'classification_time_ms': 0.0,  # Would need to measure separately
                'search_time_ms': processing_time,
                'memories_retrieved': len(memories),
                'vector_efficiency': len(vector_contributions)
            }
            
            # Update stats
            self.search_stats['total_searches'] += 1
            if 'content' in vector_contributions:
                self.search_stats['content_searches'] += 1
            if 'emotion' in vector_contributions:
                self.search_stats['emotion_searches'] += 1
            if 'semantic' in vector_contributions:
                self.search_stats['semantic_searches'] += 1
            if len(vector_contributions) > 1:
                self.search_stats['hybrid_searches'] += 1
            
            result = MultiVectorResult(
                memories=memories,
                vector_contributions=vector_contributions,
                fusion_strategy=fusion_strategy,
                performance_metrics=performance_metrics,
                classification=classification
            )
            
            # 🆕 LOG CLASSIFICATION TO INFLUXDB (for monitoring/analytics)
            if self.intelligence.temporal_client:
                try:
                    # Compute results quality from search scores
                    results_quality = None
                    if result.memories:
                        # Average score of top results (0-1 scale)
                        avg_score = sum(m.get('score', 0.0) for m in result.memories) / len(result.memories)
                        results_quality = min(avg_score, 1.0)  # Normalize to 0-1
                    
                    # Get bot name for logging
                    from src.memory.vector_memory_system import get_normalized_bot_name_from_env
                    bot_name = get_normalized_bot_name_from_env()
                    
                    # Log classification decision to InfluxDB
                    await self.intelligence.log_classification_to_influxdb(
                        bot_name=bot_name,
                        user_id=user_id,
                        query=query,
                        classification=classification,
                        actual_results_quality=results_quality,
                        session_id=None  # Could extract from conversation_context if needed
                    )
                    
                    self.logger.debug("📊 Classification logged to InfluxDB: %s vector (quality: %.2f)",
                                    classification.primary_vector,
                                    results_quality if results_quality else 0.0)
                    
                except Exception as e:
                    # Don't fail the search if logging fails
                    self.logger.warning("Failed to log classification to InfluxDB: %s", e)
            
            self.logger.info("🎯 MULTI-VECTOR COMPLETE: %d memories via %s in %.1fms", 
                           len(memories), fusion_strategy, processing_time)
            
            return result
            
        except (ValueError, KeyError, AttributeError) as e:
            self.logger.error("Multi-vector search failed: %s", str(e))
            # Fallback to simple content search
            return await self._fallback_content_search(query, user_id, limit)
    
    async def _execute_temporal_search(self, query: str, user_id: str, limit: int) -> List[Dict[str, Any]]:
        """Execute temporal search using existing temporal detection"""
        # Use retrieve_relevant_memories which handles temporal detection internally
        if hasattr(self.vector_memory_system, 'retrieve_relevant_memories'):
            temporal_results = await self.vector_memory_system.retrieve_relevant_memories(
                user_id=user_id, query=query, limit=limit
            )
            return temporal_results
        return []
    
    async def _execute_content_primary_search(
        self, query: str, user_id: str, limit: int, 
        classification: QueryClassification, memory_types: Optional[List[str]]
    ) -> List[Dict[str, Any]]:
        """Execute content-primary search with semantic backup"""
        # Use existing content vector search
        if hasattr(self.vector_memory_system, 'vector_store'):
            results = await self.vector_memory_system.vector_store.search_memories_with_qdrant_intelligence(
                query=query, user_id=user_id, memory_types=memory_types, top_k=limit
            )
            return results
        return []
    
    async def _execute_emotion_primary_search(
        self, query: str, user_id: str, limit: int,
        classification: QueryClassification, memory_types: Optional[List[str]]
    ) -> List[Dict[str, Any]]:
        """Execute emotion-primary search"""
        # Use multi-vector search with emotion priority
        if hasattr(self.vector_memory_system, 'vector_store'):
            # Extract emotional context from classification
            emotional_query = " ".join(classification.emotional_indicators)
            results = await self.vector_memory_system.vector_store.search_memories_with_emotional_intelligence(
                content_query=query,
                emotional_query=emotional_query,
                user_id=user_id,
                memory_types=memory_types,
                top_k=limit
            )
            return results
        return []
    
    async def _execute_semantic_primary_search(
        self, query: str, user_id: str, limit: int,
        classification: QueryClassification, memory_types: Optional[List[str]]
    ) -> List[Dict[str, Any]]:
        """Execute semantic-primary search"""
        # Use semantic vector for conceptual queries
        if hasattr(self.vector_memory_system, 'vector_store'):
            # Create semantic-enhanced query
            semantic_context = " ".join(classification.semantic_indicators)
            results = await self.vector_memory_system.vector_store.search_memories_with_emotional_intelligence(
                content_query=query,
                personality_context=semantic_context,  # Use personality field for semantic concepts
                user_id=user_id,
                memory_types=memory_types,
                top_k=limit
            )
            return results
        return []
    
    async def _execute_balanced_fusion_search(
        self, query: str, user_id: str, limit: int,
        classification: QueryClassification, memory_types: Optional[List[str]]
    ) -> tuple[List[Dict[str, Any]], Dict[str, int]]:
        """Execute balanced fusion across all 3 vectors"""
        # Get results from all 3 vectors with equal weighting
        per_vector_limit = limit // 3
        
        # Content vector results
        content_results = await self._execute_content_primary_search(
            query, user_id, per_vector_limit, classification, memory_types
        )
        
        # Emotion vector results  
        emotion_results = await self._execute_emotion_primary_search(
            query, user_id, per_vector_limit, classification, memory_types
        )
        
        # Semantic vector results
        semantic_results = await self._execute_semantic_primary_search(
            query, user_id, per_vector_limit, classification, memory_types
        )
        
        # Combine and deduplicate results
        all_results = content_results + emotion_results + semantic_results
        seen_ids = set()
        unique_results = []
        for result in all_results:
            result_id = result.get('id')
            if result_id and result_id not in seen_ids:
                seen_ids.add(result_id)
                unique_results.append(result)
                
        # Limit to requested count
        final_results = unique_results[:limit]
        
        vector_contributions = {
            'content': len([r for r in final_results if r in content_results]),
            'emotion': len([r for r in final_results if r in emotion_results]),
            'semantic': len([r for r in final_results if r in semantic_results])
        }
        
        return final_results, vector_contributions
    
    async def _execute_weighted_combination_search(
        self, query: str, user_id: str, limit: int,
        classification: QueryClassification, memory_types: Optional[List[str]]
    ) -> tuple[List[Dict[str, Any]], Dict[str, int]]:
        """Execute weighted combination based on classification scores"""
        # Calculate per-vector limits based on weights
        weights = classification.vector_weights
        content_limit = int(limit * weights.get('content', 0.33))
        emotion_limit = int(limit * weights.get('emotion', 0.33))
        semantic_limit = int(limit * weights.get('semantic', 0.33))
        
        # Ensure we get at least some results from each vector
        content_limit = max(1, content_limit)
        emotion_limit = max(1, emotion_limit)
        semantic_limit = max(1, semantic_limit)
        
        # Get weighted results
        content_results = await self._execute_content_primary_search(
            query, user_id, content_limit, classification, memory_types
        )
        
        emotion_results = await self._execute_emotion_primary_search(
            query, user_id, emotion_limit, classification, memory_types
        )
        
        semantic_results = await self._execute_semantic_primary_search(
            query, user_id, semantic_limit, classification, memory_types
        )
        
        # Combine with weight-based prioritization
        all_results = []
        # Add content results with high priority
        all_results.extend(content_results)
        # Add emotion results, avoiding duplicates
        all_results.extend([r for r in emotion_results if r.get('id') not in [cr.get('id') for cr in content_results]])
        # Add semantic results, avoiding duplicates
        existing_ids = [r.get('id') for r in all_results]
        all_results.extend([r for r in semantic_results if r.get('id') not in existing_ids])
        
        # Limit to requested count
        final_results = all_results[:limit]
        
        vector_contributions = {
            'content': len([r for r in final_results if r in content_results]),
            'emotion': len([r for r in final_results if r in emotion_results and r not in content_results]),
            'semantic': len([r for r in final_results if r in semantic_results and r not in content_results and r not in emotion_results])
        }
        
        return final_results, vector_contributions
    
    async def _fallback_content_search(self, query: str, user_id: str, limit: int) -> MultiVectorResult:
        """Fallback to simple content search on error"""
        try:
            fallback_classification = QueryClassification(
                query_type=QueryType.CONTENT_SEMANTIC,
                primary_vector='content',
                secondary_vectors=[],
                strategy=VectorStrategy.CONTENT_PRIMARY,
                confidence=0.3,
                reasoning="Fallback classification",
                vector_weights={'content': 1.0, 'emotion': 0.0, 'semantic': 0.0},
                emotional_indicators=[],
                semantic_indicators=[],
                content_indicators=[]
            )
            
            memories = await self._execute_content_primary_search(query, user_id, limit, fallback_classification, None)
            return MultiVectorResult(
                memories=memories,
                vector_contributions={"content": len(memories)},
                fusion_strategy="content_fallback",
                performance_metrics={"error": True},
                classification=fallback_classification
            )
        except (ValueError, KeyError, AttributeError):
            return MultiVectorResult(
                memories=[],
                vector_contributions={},
                fusion_strategy="error_fallback",
                performance_metrics={"error": True},
                classification=fallback_classification
            )


# Factory functions for dependency injection
def create_multi_vector_intelligence(temporal_client=None) -> MultiVectorIntelligence:
    """Create MultiVectorIntelligence instance with optional InfluxDB logging
    
    Args:
        temporal_client: Optional TemporalIntelligenceClient for classification accuracy logging
        
    Returns:
        MultiVectorIntelligence instance
    """
    return MultiVectorIntelligence(temporal_client=temporal_client)


def create_multi_vector_search_coordinator(vector_memory_system, intelligence=None) -> MultiVectorSearchCoordinator:
    """Create MultiVectorSearchCoordinator instance"""
    return MultiVectorSearchCoordinator(vector_memory_system, intelligence)
