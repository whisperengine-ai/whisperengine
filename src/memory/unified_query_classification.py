"""
Unified Query Classification System - Single Source of Truth

Merges QueryClassifier (vector routing) and SemanticKnowledgeRouter.analyze_query_intent
(high-level intent analysis) into single authoritative classification system.

This eliminates duplicate classification logic and ensures consistent routing decisions
across the entire query processing pipeline.

## Design

UnifiedQueryClassification provides:
1. **High-level intent** (what user wants): FACTUAL_RECALL, CONVERSATION_STYLE, etc.
2. **Vector strategy** (how to search): single, fusion, temporal, etc.
3. **Data sources** (where to look): QDRANT, POSTGRESQL, INFLUXDB, CDL
4. **Confidence metrics**: intent_confidence, strategy_confidence

## Classification Priority

1. Temporal patterns (first/last/yesterday) → TEMPORAL_CHRONOLOGICAL strategy
2. Conversational patterns (we talked/discussed) → SEMANTIC_FUSION strategy
3. Emotional patterns (keyword + RoBERTa) → EMOTION_FUSION strategy
4. Factual patterns (define/explain) → CONTENT_ONLY strategy
5. Entity/relationship queries → route to PostgreSQL
6. Default → CONTENT_ONLY strategy

## Usage

```python
classifier = UnifiedQueryClassifier(postgres_pool, qdrant_client)

# Classify query
classification = await classifier.classify(
    query="What did we talk about yesterday?",
    emotion_data=roberta_emotion,
    user_id="user123"
)

# Access results
print(classification.intent_type)        # CONVERSATION_STYLE
print(classification.vector_strategy)    # SEMANTIC_FUSION
print(classification.data_sources)       # [QDRANT, POSTGRESQL]
print(classification.intent_confidence)  # 0.85
```
"""

import logging
from enum import Enum
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
import time

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS - Unified Classification Types
# ============================================================================

class QueryIntent(Enum):
    """High-level query intentions (what user wants)"""
    # Factual knowledge
    FACTUAL_RECALL = "factual_recall"              # "What foods do I like?"
    
    # Conversational memory
    CONVERSATION_STYLE = "conversation_style"     # "How did we talk about X?"
    
    # Temporal analysis
    TEMPORAL_ANALYSIS = "temporal_analysis"        # "How have preferences changed?"
    
    # Character personality
    PERSONALITY_KNOWLEDGE = "personality_knowledge"  # CDL character background
    
    # Relationships and entities
    RELATIONSHIP_DISCOVERY = "relationship_discovery"  # "What's similar to X?"
    ENTITY_SEARCH = "entity_search"                # "Find entities about Y"
    
    # User analytics
    USER_ANALYTICS = "user_analytics"              # "What do you know about me?"


class VectorStrategy(Enum):
    """Vector search strategies (how to search)"""
    CONTENT_ONLY = "content_only"                  # Single content vector
    EMOTION_FUSION = "emotion_fusion"              # Content + emotion vectors
    SEMANTIC_FUSION = "semantic_fusion"            # Content + semantic vectors
    TEMPORAL_CHRONOLOGICAL = "temporal_chronological"  # No vectors, chronological
    BALANCED_FUSION = "balanced_fusion"            # All three vectors balanced
    MULTI_CATEGORY = "multi_category"              # Multiple vector types


class DataSource(Enum):
    """Data sources for fact/knowledge retrieval"""
    QDRANT = "qdrant"                              # Conversation memories
    POSTGRESQL = "postgresql"                      # Structured facts
    INFLUXDB = "influxdb"                          # Temporal metrics
    CDL = "cdl"                                    # Character personality


# ============================================================================
# DATACLASSES - Classification Result
# ============================================================================

@dataclass
class UnifiedClassification:
    """
    Complete query classification result combining intent + vector strategy.
    
    Attributes:
        intent_type: High-level intent (FACTUAL_RECALL, CONVERSATION_STYLE, etc.)
        vector_strategy: Vector search strategy (EMOTION_FUSION, SEMANTIC_FUSION, etc.)
        data_sources: Set of data sources to query (QDRANT, POSTGRESQL, etc.)
        
        intent_confidence: 0-1 confidence in intent classification
        strategy_confidence: 0-1 confidence in vector strategy choice
        
        entity_type: Optional entity type extracted from query (food, hobby, etc.)
        relationship_type: Optional relationship type (likes, dislikes, etc.)
        
        is_temporal: Whether query detected as temporal
        is_temporal_first: Whether query asks for FIRST/EARLIEST (sort ascending)
        is_temporal_last: Whether query asks for LAST/LATEST (sort descending)
        is_multi_category: Whether query matches multiple categories
        
        matched_patterns: List of patterns that matched for debugging
        keywords: Keywords extracted from query
        
        reasoning: Human-readable explanation of classification
    """
    intent_type: QueryIntent
    vector_strategy: VectorStrategy
    data_sources: Set[DataSource] = field(default_factory=lambda: {DataSource.QDRANT})
    
    intent_confidence: float = 0.0
    strategy_confidence: float = 0.0
    
    entity_type: Optional[str] = None
    relationship_type: Optional[str] = None
    
    is_temporal: bool = False
    is_temporal_first: bool = False  # TEMPORAL_FIRST: return oldest memories
    is_temporal_last: bool = False   # TEMPORAL_LAST: return newest memories
    is_multi_category: bool = False
    
    matched_patterns: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    
    reasoning: str = ""
    
    # For debugging and monitoring
    classification_time_ms: float = 0.0


# ============================================================================
# MAIN CLASSIFIER
# ============================================================================

class UnifiedQueryClassifier:
    """
    Single, authoritative query classifier combining:
    - Vector routing (QueryClassifier logic)
    - Intent analysis (SemanticKnowledgeRouter logic)
    - Temporal detection
    - Emotion analysis
    
    Design Philosophy:
    - One classification system, not two
    - Consistent results across all code paths
    - Clear priority ordering
    - Extensible pattern system
    """
    
    def __init__(self, postgres_pool=None, qdrant_client=None):
        """Initialize unified classifier with optional data store connections."""
        self.postgres = postgres_pool
        self.qdrant = qdrant_client
        
        # Build pattern dictionaries
        self._build_patterns()
        
        # Configuration
        self.emotion_intensity_threshold = 0.3  # Below = non-emotional
        
        logger.info("✅ UnifiedQueryClassifier initialized (single source of truth)")
    
    def _build_patterns(self):
        """Build all pattern dictionaries for classification."""
        
        # TEMPORAL patterns (first priority - highest specificity)
        self.temporal_first_patterns = [
            'first', 'earliest', 'initial', 'very first', 'when did we start',
            'beginning', 'start', 'started', 'started talking'
        ]
        
        self.temporal_last_patterns = [
            'last', 'latest', 'most recent', 'recently', 'just now', 'moments ago',
            'last time', 'end', 'just'  # Task #2: Added 'just' to detect "What did we just talk about?"
        ]
        
        self.temporal_specific_patterns = [
            'yesterday', 'today', '2 hours ago', 'this morning', 'last week',
            'last month', 'earlier', 'before', 'after', 'ago', 'since'
        ]
        
        # CONVERSATIONAL patterns (second priority)
        self.conversational_patterns = [
            'we talked', 'we discussed', 'we were talking',
            'our conversation', 'our chat', 'our discussion',
            'remember when', 'recall when', 'remember our',
            'you mentioned', 'you said', 'you told me',
            'earlier you', 'before you',
            'what did we', 'what have we', 'what were we',
            'last time we', 'when we spoke',
            'in our conversation', 'during our chat',
            'you and i', 'we were discussing',
            'what have you', 'what did you tell',
            'remind me about our', 'remind me what we',
        ]
        
        # EMOTIONAL patterns (third priority)
        self.emotional_keywords = [
            'feel', 'feeling', 'felt', 'emotion', 'emotional', 'mood',
            'happy', 'sad', 'angry', 'excited', 'anxious', 'worried', 'scared',
            'how are you', "how're you", 'how do you feel', 'are you okay',
            'love', 'hate', 'fear', 'passion', 'joy', 'sorrow'
        ]
        
        # FACTUAL patterns (fourth priority - lower specificity)
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
        
        # ENTITY/RELATIONSHIP patterns
        self.relationship_discovery_patterns = [
            'similar', 'like', 'related', 'connected', 'alternative', 'recommend',
            'suggest', 'compare', 'other', 'else', 'also', 'too', 'as well'
        ]
        
        self.entity_search_patterns = [
            'find', 'search', 'look for', 'about', 'information', 'details',
            'anything about', 'know about', 'heard of', 'familiar with'
        ]
    
    async def classify(
        self,
        query: str,
        emotion_data: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        character_name: Optional[str] = None,
    ) -> UnifiedClassification:
        """
        Unified query classification - single call, complete results.
        
        Args:
            query: User query string
            emotion_data: Pre-analyzed RoBERTa emotion data (optional)
            user_id: User identifier for context (optional, reserved for future use)
            character_name: Character name for CDL context (optional, reserved for future use)
            
        Returns:
            UnifiedClassification with complete routing information
        """
        start_time = time.time()
        
        query_lower = query.lower().strip()
        matched_patterns = []
        keywords = []
        
        # =====================================================================
        # PRIORITY 1: TEMPORAL PATTERNS (most specific)
        # =====================================================================
        
        is_temporal_first = any(p in query_lower for p in self.temporal_first_patterns)
        is_temporal_last = any(p in query_lower for p in self.temporal_last_patterns)
        is_temporal_specific = any(p in query_lower for p in self.temporal_specific_patterns)
        is_temporal = is_temporal_first or is_temporal_last or is_temporal_specific
        
        if is_temporal:
            keywords.extend([p for p in self.temporal_first_patterns if p in query_lower])
            keywords.extend([p for p in self.temporal_last_patterns if p in query_lower])
            keywords.extend([p for p in self.temporal_specific_patterns if p in query_lower])
            matched_patterns.append("temporal")
        
        # =====================================================================
        # PRIORITY 2: CONVERSATIONAL PATTERNS
        # =====================================================================
        
        is_conversational = any(p in query_lower for p in self.conversational_patterns)
        if is_conversational:
            keywords.extend([p for p in self.conversational_patterns if p in query_lower])
            matched_patterns.append("conversational")
        
        # =====================================================================
        # PRIORITY 3: EMOTIONAL PATTERNS
        # =====================================================================
        
        is_emotional = False
        has_emotional_keyword = any(kw in query_lower for kw in self.emotional_keywords)
        
        has_high_emotion_intensity = False
        if emotion_data:
            emotional_intensity = emotion_data.get('emotional_intensity', 0.0)
            has_high_emotion_intensity = emotional_intensity > self.emotion_intensity_threshold
        
        is_emotional = has_emotional_keyword or has_high_emotion_intensity
        
        if is_emotional:
            keywords.extend([kw for kw in self.emotional_keywords if kw in query_lower])
            matched_patterns.append("emotional")
        
        # =====================================================================
        # PRIORITY 4: FACTUAL PATTERNS
        # =====================================================================
        
        is_factual = any(p in query_lower for p in self.factual_patterns)
        if is_factual:
            keywords.extend([p for p in self.factual_patterns if p in query_lower])
            matched_patterns.append("factual")
        
        # =====================================================================
        # PRIORITY 5: ENTITY/RELATIONSHIP PATTERNS
        # =====================================================================
        
        is_relationship_discovery = any(p in query_lower for p in self.relationship_discovery_patterns)
        is_entity_search = any(p in query_lower for p in self.entity_search_patterns)
        
        if is_relationship_discovery:
            keywords.extend([p for p in self.relationship_discovery_patterns if p in query_lower])
            matched_patterns.append("relationship_discovery")
        
        if is_entity_search:
            keywords.extend([p for p in self.entity_search_patterns if p in query_lower])
            matched_patterns.append("entity_search")
        
        # =====================================================================
        # DETERMINE INTENT AND STRATEGY
        # =====================================================================
        
        # Determine primary intent based on matched patterns
        intent_confidence = 0.0
        intent_type = QueryIntent.FACTUAL_RECALL  # Default
        
        # Priority order for intent determination
        # Task #2: TEMPORAL queries should ALWAYS get TEMPORAL_ANALYSIS intent
        # because the temporal sorting direction is what matters most
        if is_temporal:
            # TEMPORAL_ANALYSIS has highest priority for routing
            intent_type = QueryIntent.TEMPORAL_ANALYSIS
            intent_confidence = 0.95
            is_multi_category = is_conversational or is_emotional or is_factual
        elif is_conversational:
            intent_type = QueryIntent.CONVERSATION_STYLE
            intent_confidence = 0.9
        elif is_emotional:
            intent_type = QueryIntent.FACTUAL_RECALL  # Keep factual as intent
            intent_confidence = 0.8  # But emotional routing in strategy
        elif is_relationship_discovery:
            intent_type = QueryIntent.RELATIONSHIP_DISCOVERY
            intent_confidence = 0.85
        elif is_entity_search:
            intent_type = QueryIntent.ENTITY_SEARCH
            intent_confidence = 0.85
        elif is_factual:
            intent_type = QueryIntent.FACTUAL_RECALL
            intent_confidence = 0.9
        else:
            # Default: factual recall with lower confidence
            intent_type = QueryIntent.FACTUAL_RECALL
            intent_confidence = 0.5
        
        # =====================================================================
        # DETERMINE VECTOR STRATEGY
        # =====================================================================
        
        is_multi_category = sum([is_conversational, is_temporal, is_emotional, is_factual]) > 1
        
        # Strategy selection based on query characteristics
        if is_temporal:
            vector_strategy = VectorStrategy.TEMPORAL_CHRONOLOGICAL
            strategy_confidence = 0.95
        elif is_conversational and is_emotional:
            vector_strategy = VectorStrategy.MULTI_CATEGORY  # Both semantic + emotion
            strategy_confidence = 0.85
        elif is_conversational:
            vector_strategy = VectorStrategy.SEMANTIC_FUSION
            strategy_confidence = 0.9
        elif is_emotional:
            vector_strategy = VectorStrategy.EMOTION_FUSION
            strategy_confidence = 0.85
        elif is_factual:
            vector_strategy = VectorStrategy.CONTENT_ONLY
            strategy_confidence = 0.9
        elif is_multi_category:
            vector_strategy = VectorStrategy.BALANCED_FUSION
            strategy_confidence = 0.7
        else:
            vector_strategy = VectorStrategy.CONTENT_ONLY
            strategy_confidence = 0.5
        
        # =====================================================================
        # DETERMINE DATA SOURCES
        # =====================================================================
        
        data_sources: Set[DataSource] = set()
        
        # All searches use Qdrant for memory
        data_sources.add(DataSource.QDRANT)
        
        # Some queries need PostgreSQL for facts
        if intent_type in [QueryIntent.FACTUAL_RECALL, QueryIntent.RELATIONSHIP_DISCOVERY, 
                           QueryIntent.ENTITY_SEARCH, QueryIntent.USER_ANALYTICS]:
            data_sources.add(DataSource.POSTGRESQL)
        
        # Temporal analysis might need InfluxDB
        if intent_type == QueryIntent.TEMPORAL_ANALYSIS:
            data_sources.add(DataSource.INFLUXDB)
        
        # Personality knowledge uses CDL
        if intent_type == QueryIntent.PERSONALITY_KNOWLEDGE:
            data_sources.add(DataSource.CDL)
        
        # =====================================================================
        # EXTRACT ENTITY AND RELATIONSHIP INFO
        # =====================================================================
        
        entity_type = self._extract_entity_type(query_lower)
        relationship_type = self._extract_relationship_type(query_lower)
        
        # =====================================================================
        # GENERATE REASONING
        # =====================================================================
        
        reasoning = self._generate_reasoning(
            matched_patterns, intent_type, vector_strategy, 
            intent_confidence, strategy_confidence
        )
        
        # =====================================================================
        # BUILD RESULT
        # =====================================================================
        
        classification_time_ms = (time.time() - start_time) * 1000
        
        result = UnifiedClassification(
            intent_type=intent_type,
            vector_strategy=vector_strategy,
            data_sources=data_sources,
            intent_confidence=intent_confidence,
            strategy_confidence=strategy_confidence,
            entity_type=entity_type,
            relationship_type=relationship_type,
            is_temporal=is_temporal,
            is_temporal_first=is_temporal_first,  # Task #2: Track temporal direction
            is_temporal_last=is_temporal_last,    # Task #2: Track temporal direction
            is_multi_category=is_multi_category,
            matched_patterns=matched_patterns,
            keywords=keywords,
            reasoning=reasoning,
            classification_time_ms=classification_time_ms,
        )
        
        logger.info(
            "🎯 UNIFIED CLASSIFICATION: query='%s...' → intent=%s, strategy=%s (conf: %.2f/%.2f)",
            query[:40], intent_type.value, vector_strategy.value,
            intent_confidence, strategy_confidence
        )
        
        return result
    
    def _extract_entity_type(self, query_lower: str) -> Optional[str]:
        """Extract entity type from query (food, hobby, person, etc.)"""
        entity_keywords = {
            'food': ['food', 'eat', 'meal', 'dish', 'cuisine', 'restaurant', 'recipe'],
            'hobby': ['hobby', 'hobby', 'interest', 'pastime', 'activity', 'play', 'practice'],
            'person': ['person', 'friend', 'family', 'person', 'people', 'someone', 'who', 'guy', 'girl'],
            'place': ['place', 'location', 'city', 'country', 'visit', 'travel', 'where'],
            'book': ['book', 'read', 'author', 'novel', 'story', 'title'],
            'music': ['music', 'song', 'artist', 'album', 'listen', 'band'],
            'movie': ['movie', 'film', 'watch', 'cinema', 'actor', 'show'],
            'art': ['art', 'artist', 'painting', 'draw', 'create', 'sculpture'],
            'technology': ['tech', 'technology', 'coding', 'programming', 'software', 'computer'],
        }
        
        for entity_type, keywords in entity_keywords.items():
            if any(kw in query_lower for kw in keywords):
                return entity_type
        
        return None
    
    def _extract_relationship_type(self, query_lower: str) -> Optional[str]:
        """Extract relationship type from query (likes, dislikes, knows, etc.)"""
        relationship_keywords = {
            'likes': ['like', 'love', 'enjoy', 'prefer'],
            'dislikes': ['dislike', 'hate', 'avoid', 'don\'t like'],
            'knows': ['know', 'familiar', 'heard of', 'aware of'],
            'wants': ['want', 'need', 'desire', 'wish for'],
            'fears': ['fear', 'afraid of', 'scared of'],
        }
        
        for rel_type, keywords in relationship_keywords.items():
            if any(kw in query_lower for kw in keywords):
                return rel_type
        
        return None
    
    def _generate_reasoning(
        self,
        matched_patterns: List[str],
        intent_type: QueryIntent,
        strategy: VectorStrategy,
        intent_conf: float,
        strategy_conf: float,
    ) -> str:
        """Generate human-readable explanation of classification."""
        
        reasoning = f"Matched: {', '.join(matched_patterns)} → "
        reasoning += f"Intent: {intent_type.value} ({intent_conf:.0%}) → "
        reasoning += f"Strategy: {strategy.value} ({strategy_conf:.0%})"
        
        return reasoning
    
    def get_vector_weights(self, strategy: VectorStrategy) -> Dict[str, float]:
        """Get vector weights for multi-vector fusion."""
        
        weights_map = {
            VectorStrategy.CONTENT_ONLY: {"content": 1.0},
            VectorStrategy.EMOTION_FUSION: {"content": 0.4, "emotion": 0.6},
            VectorStrategy.SEMANTIC_FUSION: {"content": 0.5, "semantic": 0.5},
            VectorStrategy.BALANCED_FUSION: {"content": 0.33, "emotion": 0.33, "semantic": 0.34},
            VectorStrategy.MULTI_CATEGORY: {"content": 0.4, "emotion": 0.3, "semantic": 0.3},
            VectorStrategy.TEMPORAL_CHRONOLOGICAL: {},  # No vectors
        }
        
        return weights_map.get(strategy, {"content": 1.0})


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def create_unified_query_classifier(postgres_pool=None, qdrant_client=None) -> UnifiedQueryClassifier:
    """
    Factory function to create UnifiedQueryClassifier instance.
    
    Args:
        postgres_pool: Optional PostgreSQL connection pool
        qdrant_client: Optional Qdrant client
        
    Returns:
        Configured UnifiedQueryClassifier instance
    """
    return UnifiedQueryClassifier(postgres_pool, qdrant_client)
