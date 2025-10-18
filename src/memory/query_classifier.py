"""
Query classification for intelligent vector routing in WhisperEngine.

This module provides query classification to enable smart multi-vector routing:
- Factual queries → content vector only (fast, accurate)
- Emotional queries → content + emotion vectors (fusion)
- Conversational queries → content + semantic vectors (fusion)
- Temporal queries → chronological scroll (no vectors)
- General queries → content vector (default)

Part of Phase 2: Multi-Vector Intelligence Roadmap
"""
from enum import Enum
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class QueryCategory(Enum):
    """
    Query categories for optimal vector routing.
    
    Each category maps to a specific vector search strategy:
    - FACTUAL: Single content vector (fast path for definitions, facts)
    - EMOTIONAL: Multi-vector fusion (content + emotion)
    - CONVERSATIONAL: Multi-vector fusion (content + semantic)
    - TEMPORAL: Chronological scroll (bypasses vector search)
    - GENERAL: Single content vector (default fallback)
    """
    FACTUAL = "factual"           # "What's 2+2?", "Define X"
    EMOTIONAL = "emotional"       # "How are you?", "I'm excited!"
    CONVERSATIONAL = "conversational"  # "What did we discuss?"
    TEMPORAL = "temporal"         # "What was the first thing?"
    GENERAL = "general"           # Default fallback


class QueryClassifier:
    """
    Classify queries for optimal vector routing.
    
    Uses pattern matching and pre-analyzed emotion data to determine
    the best vector search strategy for each query type.
    
    Design Philosophy:
    - High-precision patterns for factual queries (avoid false positives)
    - RoBERTa emotion data for emotional detection (no keywords)
    - Conversational patterns for relationship memory queries
    - Temporal detection already exists in vector_memory_system
    
    Example Usage:
        classifier = QueryClassifier()
        category = await classifier.classify_query(
            query="What did we talk about yesterday?",
            emotion_data={'emotional_intensity': 0.2},
            is_temporal=False
        )
        # Returns: QueryCategory.CONVERSATIONAL
    """
    
    def __init__(self):
        """Initialize query classifier with pattern matching rules."""
        
        # Factual query indicators (high-precision patterns)
        # These should trigger single content vector search (fast path)
        self.factual_patterns = [
            'what is', 'what are', 'what was', 'what were',
            'define', 'definition of',
            'explain', 'explanation of',
            'how to', 'how do', 'how does',
            'calculate', 'compute', 'solve',
            'formula', 'equation',
            'meaning of', 'means',
            'tell me about',  # Factual information request
            'information about',
            'description of',
        ]
        
        # Conversational query indicators (relationship memory queries)
        # These should trigger content + semantic vector fusion
        self.conversational_patterns = [
            'we talked', 'we discussed', 'we were talking',
            'our conversation', 'our chat', 'our discussion',
            'remember when', 'recall when',
            'you mentioned', 'you said', 'you told me',
            'earlier you', 'before you',
            'what did we', 'what have we', 'what were we',
            'last time we', 'when we spoke',
            'in our conversation', 'during our chat',
            'you and i', 'we were discussing',
            'what have you', 'what did you tell',
            'remind me about our', 'remind me what we',
        ]
        
        # Emotional intensity threshold for emotion vector routing
        # Below this threshold, treat as non-emotional query
        self.emotion_intensity_threshold = 0.3
        
        logger.info("🎯 QueryClassifier initialized with pattern matching rules")
    
    async def classify_query(
        self, 
        query: str, 
        emotion_data: Optional[Dict[str, Any]] = None,
        is_temporal: bool = False
    ) -> QueryCategory:
        """
        Classify query into category for vector routing decision.
        
        Args:
            query: User query string to classify
            emotion_data: Pre-analyzed emotion data from RoBERTa (optional)
                         Expected keys: emotional_intensity, dominant_emotion
            is_temporal: Whether query already detected as temporal
                        (from existing temporal detection system)
            
        Returns:
            QueryCategory enum indicating optimal routing strategy
            
        Classification Priority:
            1. Factual (high-precision patterns) → content vector only
            2. Conversational (relationship patterns) → content + semantic
            3. Emotional (keyword + RoBERTa data) → content + emotion
            4. Temporal (if is_temporal=True) → chronological scroll
            5. General (default fallback) → content vector only
        
        Note: Conversational queries are checked BEFORE temporal to handle cases
              like "What did we talk about yesterday?" which has both conversational
              intent ("what did we talk about") and temporal markers ("yesterday").
              The conversational aspect is more important for routing decisions.
            
        Example:
            >>> emotion_data = {'emotional_intensity': 0.45, 'dominant_emotion': 'joy'}
            >>> category = await classifier.classify_query(
            ...     query="How are you feeling?",
            ...     emotion_data=emotion_data
            ... )
            >>> category == QueryCategory.EMOTIONAL
            True
        """
        query_lower = query.lower().strip()
        
        # Priority 1: Factual queries (high-precision patterns)
        # These use single content vector for fast, accurate retrieval
        if any(pattern in query_lower for pattern in self.factual_patterns):
            logger.debug("🎯 CLASSIFIED: FACTUAL query: '%s...'", query[:50])
            return QueryCategory.FACTUAL
        
        # Priority 2: Conversational queries (relationship memory patterns)
        # These use content + semantic vector fusion
        # Checked BEFORE temporal to handle "What did we talk about yesterday?"
        if any(pattern in query_lower for pattern in self.conversational_patterns):
            logger.debug("🎯 CLASSIFIED: CONVERSATIONAL query: '%s...'", query[:50])
            return QueryCategory.CONVERSATIONAL
        
        # Priority 3: Emotional queries (keyword patterns + RoBERTa data)
        # These use content + emotion vector fusion
        # Check BOTH keyword patterns AND RoBERTa emotion intensity
        emotional_keywords = [
            'feel', 'feeling', 'felt', 'emotion', 'emotional', 'mood',
            'how are you', "how're you", 'how do you feel', 'are you okay',
            'happy', 'sad', 'angry', 'excited', 'anxious', 'worried', 'scared'
        ]
        has_emotional_keyword = any(kw in query_lower for kw in emotional_keywords)
        
        # Check RoBERTa emotion data if available
        has_high_emotion_intensity = False
        if emotion_data:
            emotional_intensity = emotion_data.get('emotional_intensity', 0.0)
            dominant_emotion = emotion_data.get('dominant_emotion', 'neutral')
            has_high_emotion_intensity = emotional_intensity > self.emotion_intensity_threshold
        
        # Classify as EMOTIONAL if EITHER keyword match OR high RoBERTa intensity
        if has_emotional_keyword or has_high_emotion_intensity:
            logger.debug(
                "🎯 CLASSIFIED: EMOTIONAL query: '%s...' (keyword: %s, roberta_intensity: %.2f)",
                query[:50], has_emotional_keyword, 
                emotion_data.get('emotional_intensity', 0.0) if emotion_data else 0.0
            )
            return QueryCategory.EMOTIONAL
        
        # Priority 4: Temporal queries (fallback for pure temporal queries)
        # These bypass vector search entirely, use chronological scroll
        # Note: Checked AFTER conversational to avoid misclassifying
        # "What did we talk about yesterday?" as pure temporal
        if is_temporal:
            logger.debug("🎯 CLASSIFIED: TEMPORAL query: '%s...'", query[:50])
            return QueryCategory.TEMPORAL
        
        # Priority 5: General queries (default fallback)
        # These use single content vector (same as factual, but lower confidence)
        logger.debug("🎯 CLASSIFIED: GENERAL query: '%s...'", query[:50])
        return QueryCategory.GENERAL
    
    def get_vector_strategy(self, category: QueryCategory) -> Dict[str, Any]:
        """
        Get the vector search strategy for a given query category.
        
        This method provides the mapping between query categories and
        the optimal vector search configuration.
        
        Args:
            category: QueryCategory enum value
            
        Returns:
            Dictionary with vector strategy configuration:
            - vectors: List of vector names to search
            - weights: List of weights for multi-vector fusion
            - use_fusion: Whether to use multi-vector fusion
            - description: Human-readable strategy description
            
        Example:
            >>> strategy = classifier.get_vector_strategy(QueryCategory.EMOTIONAL)
            >>> strategy['vectors']
            ['content', 'emotion']
            >>> strategy['weights']
            [0.4, 0.6]  # Prioritize emotion vector
        """
        strategies = {
            QueryCategory.FACTUAL: {
                'vectors': ['content'],
                'weights': [1.0],
                'use_fusion': False,
                'description': 'Single content vector (fast path for facts)',
            },
            QueryCategory.EMOTIONAL: {
                'vectors': ['content', 'emotion'],
                'weights': [0.4, 0.6],  # Prioritize emotion
                'use_fusion': True,
                'description': 'Multi-vector fusion (content + emotion)',
            },
            QueryCategory.CONVERSATIONAL: {
                'vectors': ['content', 'semantic'],
                'weights': [0.5, 0.5],  # Balanced
                'use_fusion': True,
                'description': 'Multi-vector fusion (content + semantic)',
            },
            QueryCategory.TEMPORAL: {
                'vectors': [],
                'weights': [],
                'use_fusion': False,
                'description': 'Chronological scroll (no vectors)',
            },
            QueryCategory.GENERAL: {
                'vectors': ['content'],
                'weights': [1.0],
                'use_fusion': False,
                'description': 'Single content vector (default)',
            },
        }
        
        return strategies.get(category, strategies[QueryCategory.GENERAL])
    
    def update_patterns(
        self,
        factual_patterns: Optional[list] = None,
        conversational_patterns: Optional[list] = None,
        emotion_threshold: Optional[float] = None,
    ):
        """
        Update classification patterns (for tuning/optimization).
        
        This method allows runtime adjustment of classification rules
        based on A/B testing results or performance metrics.
        
        Args:
            factual_patterns: New list of factual query patterns (optional)
            conversational_patterns: New list of conversational patterns (optional)
            emotion_threshold: New emotion intensity threshold (optional)
            
        Example:
            >>> classifier.update_patterns(
            ...     emotion_threshold=0.35  # Increase sensitivity
            ... )
        """
        if factual_patterns is not None:
            self.factual_patterns = factual_patterns
            logger.info("🔧 Updated factual patterns: %d rules", len(factual_patterns))
        
        if conversational_patterns is not None:
            self.conversational_patterns = conversational_patterns
            logger.info("🔧 Updated conversational patterns: %d rules", len(conversational_patterns))
        
        if emotion_threshold is not None:
            old_threshold = self.emotion_intensity_threshold
            self.emotion_intensity_threshold = emotion_threshold
            logger.info(
                "🔧 Updated emotion threshold: %.2f → %.2f",
                old_threshold, emotion_threshold
            )


# Factory function for easy instantiation
def create_query_classifier() -> QueryClassifier:
    """
    Factory function to create QueryClassifier instance.
    
    Returns:
        Configured QueryClassifier instance
        
    Example:
        >>> from src.memory.query_classifier import create_query_classifier
        >>> classifier = create_query_classifier()
    """
    return QueryClassifier()
