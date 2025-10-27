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
    
    # LLM-assisted structured retrieval (NEW: Week 1 hybrid routing)
    TOOL_ASSISTED = "tool_assisted"                # "Tell me everything about my relationship with you"


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
    LLM_TOOLS = "llm_tools"                        # LLM-assisted structured retrieval (NEW: Week 1 hybrid routing)


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
    
    # Semantic matching results (spaCy word vector similarity)
    semantic_matches: List[Dict[str, Any]] = field(default_factory=list)
    """List of semantic matches with similarity scores and matched keywords"""
    
    # Dependency parsing results (negation & SVO extraction)
    has_negation: bool = False
    """Whether negation was detected in the query"""
    
    svo_relationships: List[Dict[str, Any]] = field(default_factory=list)
    """List of subject-verb-object triples extracted from query"""
    
    # POS tagging analysis (question sophistication)
    is_preference_question: bool = False
    """Whether query is a preference question (favorite, best, etc.)"""
    
    is_comparison_question: bool = False
    """Whether query is a comparison question (better than, worse than, etc.)"""
    
    is_hypothetical_question: bool = False
    """Whether query is a hypothetical question (would, could, should, etc.)"""
    
    question_complexity: int = 0
    """Question complexity score (0-10)"""
    
    # Custom matcher patterns (Task 3.1: advanced pattern detection)
    matched_advanced_patterns: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    """Dict mapping pattern names to list of matched spans from spaCy Matcher"""
    
    has_hedging: bool = False
    """Whether query contains hedging language (maybe, perhaps, kind of)"""
    
    has_temporal_change: bool = False
    """Whether query contains temporal change pattern (used to)"""
    
    has_strong_preference: bool = False
    """Whether query contains strong preference modifiers (really, absolutely)"""
    
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
        self.tool_complexity_threshold = 0.3  # Above = use LLM tool calling
        
        # Initialize spaCy with word vectors for semantic matching
        self._init_spacy_vectors()
        
        # Initialize custom matcher for advanced patterns (Task 3.1)
        self._init_custom_matcher()
        
        # Cache for keyword vectors (performance optimization)
        self._keyword_vector_cache = {}
        
        logger.info("✅ UnifiedQueryClassifier initialized (single source of truth)")
    
    def _init_spacy_vectors(self):
        """
        Initialize spaCy with word vectors for semantic pattern matching.
        
        Uses shared spaCy singleton to avoid loading model multiple times.
        Falls back gracefully if spaCy unavailable.
        """
        from src.nlp.spacy_manager import get_spacy_nlp, has_word_vectors
        
        # Get shared spaCy instance (singleton)
        self.nlp = get_spacy_nlp()
        self.has_vectors = has_word_vectors()
        
        if self.nlp and self.has_vectors:
            logger.info("✅ UnifiedQueryClassifier using shared spaCy instance (semantic matching enabled)")
        elif self.nlp:
            logger.info("✅ UnifiedQueryClassifier using shared spaCy instance (no word vectors)")
        else:
            logger.info("⚠️ UnifiedQueryClassifier: spaCy unavailable (keyword matching only)")
    
    def _init_custom_matcher(self):
        """
        Initialize spaCy Matcher with custom token-level patterns (Task 3.1: Custom Matcher).
        
        The Matcher allows sophisticated pattern detection beyond simple keyword matching:
        - Negated preferences: "don't like", "doesn't enjoy"
        - Strong preferences: "really love", "absolutely hate"
        - Temporal changes: "used to like", "no longer enjoy"
        - Hedging language: "maybe like", "kind of prefer"
        - Conditional statements: "if I could", "would prefer"
        
        Falls back gracefully if spaCy unavailable.
        """
        if not self.nlp:
            self.matcher = None
            logger.info("⚠️ Custom matcher disabled (spaCy unavailable)")
            return
        
        try:
            from spacy.matcher import Matcher
            
            self.matcher = Matcher(self.nlp.vocab)
            self._register_matcher_patterns()
            
            pattern_count = len(self.matcher)
            logger.info(f"✅ Custom matcher initialized ({pattern_count} pattern categories)")
            
        except ImportError as e:
            self.matcher = None
            logger.warning(f"⚠️ Custom matcher disabled (spaCy Matcher not available): {e}")
        except Exception as e:
            self.matcher = None
            logger.warning(f"⚠️ Custom matcher initialization failed: {e}")
    
    def _register_matcher_patterns(self):
        """
        Register all custom token-level patterns with matcher (Task 3.1).
        
        Pattern Categories:
        1. NEGATED_PREFERENCE: do/does/did + not + like/love/enjoy
        2. STRONG_PREFERENCE: really/absolutely + like/love/hate
        3. TEMPORAL_CHANGE: used to + verb
        4. HEDGING: maybe/perhaps/might + verb
        5. CONDITIONAL: if + pronoun + could/would + verb
        """
        if self.matcher is None:  # FIX: Empty Matcher evaluates to False, use 'is None'
            return
        
        # =====================================================================
        # 1. NEGATED PREFERENCES - HIGH PRIORITY
        # =====================================================================
        # Detects: "don't like", "doesn't enjoy", "didn't love"
        # Impact: Changes "like" → "dislike" for fact extraction
        
        self.matcher.add("NEGATED_PREFERENCE", [[
            {"LEMMA": {"IN": ["do"]}},  # do/does/did
            {"LOWER": {"IN": ["not", "n't"]}},  # not/n't
            {"LEMMA": {"IN": ["like", "love", "enjoy", "prefer", "want"]}}
        ]])
        
        # =====================================================================
        # 2. STRONG PREFERENCES - MEDIUM PRIORITY
        # =====================================================================
        # Detects: "really love", "absolutely hate", "definitely prefer"
        # Impact: Boosts confidence for factual recall
        
        self.matcher.add("STRONG_PREFERENCE", [[
            {"LOWER": {"IN": ["really", "absolutely", "definitely", "totally", "completely"]}},
            {"LEMMA": {"IN": ["like", "love", "enjoy", "prefer", "hate", "dislike"]}}
        ]])
        
        # =====================================================================
        # 3. TEMPORAL CHANGES - HIGH PRIORITY
        # =====================================================================
        # Detects: "used to like", "used to enjoy", "used to prefer"
        # Impact: Routes to temporal analysis (InfluxDB)
        
        self.matcher.add("TEMPORAL_CHANGE", [[
            {"LOWER": "used"},
            {"LOWER": "to"},
            {"POS": "ADV", "OP": "*"},  # Optional adverbs (really, never, etc.)
            {"POS": "VERB"}
        ]])
        
        # =====================================================================
        # 4. HEDGING LANGUAGE - MEDIUM PRIORITY
        # =====================================================================
        # Detects: "maybe like", "kind of prefer", "might enjoy"
        # Impact: Reduces confidence for fact storage
        
        self.matcher.add("HEDGING", [
            [  # Pattern 1: maybe/perhaps/possibly/might + verb
                {"LOWER": {"IN": ["maybe", "perhaps", "possibly", "might"]}},
                {"POS": "VERB"}
            ],
            [  # Pattern 2: kind/sort + of + verb
                {"LOWER": {"IN": ["kind", "sort"]}},
                {"LOWER": "of"},
                {"POS": "VERB"}
            ]
        ])
        
        # =====================================================================
        # 5. CONDITIONAL STATEMENTS - LOW PRIORITY
        # =====================================================================
        # Detects: "if I could", "if possible, I would"
        # Impact: Routes to hypothetical reasoning (LLM)
        
        self.matcher.add("CONDITIONAL", [[
            {"LOWER": "if"},
            {"POS": "PRON", "OP": "?"},  # Optional pronoun
            {"LEMMA": {"IN": ["could", "would", "should", "can"]}},
            {"POS": "VERB"}
        ]])
        
        logger.debug("🎯 Registered 5 custom matcher pattern categories")
    
    def _get_keyword_token(self, keyword: str):
        """
        Get cached spaCy token for a keyword.
        
        Performance optimization: Keywords are processed once and cached,
        avoiding repeated nlp() calls for the same keywords.
        
        Args:
            keyword: Single-word keyword to get token for
            
        Returns:
            spaCy Token object or None if unavailable/invalid
        """
        # Return None if spaCy not available
        if not self.nlp:
            return None
        
        # Check cache first
        if keyword in self._keyword_vector_cache:
            return self._keyword_vector_cache[keyword]
        
        # Skip multi-word phrases (they don't work well with word-level similarity)
        if ' ' in keyword:
            self._keyword_vector_cache[keyword] = None
            return None
        
        # Process keyword and cache result
        try:
            keyword_doc = self.nlp(keyword)
            if len(keyword_doc) == 0:
                self._keyword_vector_cache[keyword] = None
                return None
            
            keyword_token = keyword_doc[0]
            
            # Only cache if token has vectors
            if keyword_token.has_vector:
                self._keyword_vector_cache[keyword] = keyword_token
                return keyword_token
            else:
                self._keyword_vector_cache[keyword] = None
                return None
        except Exception as e:
            logger.debug("Failed to process keyword '%s': %s", keyword, str(e))
            self._keyword_vector_cache[keyword] = None
            return None
    
    def _check_lemmatized_patterns(
        self,
        query_doc,
        pattern_keywords: List[str]
    ) -> tuple[bool, List[str]]:
        """
        Check patterns against both raw text and lemmatized forms.
        
        Normalizes word forms (running→run, loved→love, recently→recent)
        to catch variations without maintaining exhaustive pattern lists.
        
        Args:
            query_doc: spaCy Doc object (or string for fallback)
            pattern_keywords: Keywords to match (will be lemmatized)
        
        Returns:
            Tuple of (matched: bool, matched_lemmas: List[str])
            
        Examples:
            "I'm running late" → lemma "run" matches "run" pattern
            "I loved that movie" → lemma "love" matches "love" pattern
            "most recently" → lemma "recent" matches "recent" pattern
        """
        matched_lemmas = []
        
        # Fallback to exact string matching if no spaCy
        if not self.nlp:
            query_text = query_doc.text.lower() if hasattr(query_doc, 'text') else str(query_doc).lower()
            for keyword in pattern_keywords:
                if keyword.lower() in query_text:
                    matched_lemmas.append(keyword)
            return len(matched_lemmas) > 0, matched_lemmas
        
        # Create lemmatized versions of pattern keywords (with caching)
        pattern_lemmas = set()
        for keyword in pattern_keywords:
            # Skip multi-word phrases (process them later)
            if ' ' in keyword:
                pattern_lemmas.add(keyword.lower())
            else:
                # Get lemma of keyword
                keyword_token = self._get_keyword_token(keyword)
                if keyword_token:
                    pattern_lemmas.add(keyword_token.lemma_.lower())
                else:
                    # Fallback to raw keyword
                    pattern_lemmas.add(keyword.lower())
        
        # Check query tokens against lemmatized patterns
        for token in query_doc:
            # Skip stop words and punctuation (but keep important words like 'love', 'like')
            if token.is_punct:
                continue
            
            # Check both lemma and raw text (covers edge cases)
            token_lemma = token.lemma_.lower()
            token_text = token.text.lower()
            
            if token_lemma in pattern_lemmas or token_text in pattern_lemmas:
                matched_lemmas.append(token.text)
        
        # Also check for multi-word phrases in original text
        query_text = query_doc.text.lower()
        for keyword in pattern_keywords:
            if ' ' in keyword and keyword.lower() in query_text:
                if keyword not in matched_lemmas:
                    matched_lemmas.append(keyword)
        
        return len(matched_lemmas) > 0, matched_lemmas
    
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
    
    def _semantic_pattern_match(
        self,
        query_doc,
        pattern_keywords: List[str],
        similarity_threshold: float = 0.65
    ) -> tuple[bool, List[Dict[str, Any]]]:
        """
        Check if any token in query is semantically similar to pattern keywords.
        
        Uses spaCy's 300D word vectors (en_core_web_md) to find semantic matches
        beyond exact keyword matching.
        
        Args:
            query_doc: spaCy Doc object (or string for fallback)
            pattern_keywords: List of keywords to match against
            similarity_threshold: Minimum cosine similarity score (0-1, default 0.65)
        
        Returns:
            Tuple of (matched: bool, matches: List[Dict])
            
        Examples:
            "joyful" matches "happy" with ~0.72 similarity
            "furious" matches "angry" with ~0.68 similarity
            "automobile" matches "car" with ~0.85 similarity
        """
        # Fallback to exact keyword matching if no vectors available
        if not self.has_vectors or not self.nlp:
            query_text = query_doc.text.lower() if hasattr(query_doc, 'text') else str(query_doc).lower()
            matched = any(kw in query_text for kw in pattern_keywords)
            return matched, []
        
        # Create set of keywords for fast exact match checking
        keyword_set = set(kw.lower() for kw in pattern_keywords)
        
        # Collect all potential matches with their similarity scores
        potential_matches = []
        
        for token in query_doc:
            # Skip stop words, punctuation, and very short tokens
            if token.is_stop or token.is_punct or len(token.text) < 3:
                continue
            
            # Skip if token has no vector
            if not token.has_vector:
                continue
            
            # Skip if token is already an exact keyword match (prevent false positives)
            if token.text.lower() in keyword_set or token.lemma_.lower() in keyword_set:
                continue
            
            for keyword in pattern_keywords:
                # Get cached keyword token (performance optimization)
                keyword_token = self._get_keyword_token(keyword)
                
                # Skip if keyword has no vector or is multi-word
                if keyword_token is None:
                    continue
                
                # Compute cosine similarity between word vectors
                try:
                    similarity = token.similarity(keyword_token)
                    
                    if similarity >= similarity_threshold:
                        potential_matches.append({
                            "query_token": token.text,
                            "matched_keyword": keyword,
                            "similarity": round(similarity, 3),
                            "context": token.sent.text[:100] if token.sent else token.text
                        })
                
                except Exception as e:
                    # Gracefully handle similarity computation errors
                    logger.debug("⚠️ Similarity computation failed for '%s' ≈ '%s': %s", 
                               token.text, keyword, str(e))
                    continue
        
        # If we found matches, return the best one (highest similarity)
        if potential_matches:
            # Sort by similarity (descending)
            potential_matches.sort(key=lambda x: x['similarity'], reverse=True)
            best_match = potential_matches[0]
            
            logger.debug(
                "🎯 SEMANTIC MATCH: '%s' ≈ '%s' (similarity: %.3f)",
                best_match['query_token'], best_match['matched_keyword'], best_match['similarity']
            )
            
            return True, [best_match]  # Return only the best match
        
        return False, []
    
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
        semantic_matches = []  # Track semantic similarity matches
        
        # Process with spaCy if available for semantic matching
        query_doc = self.nlp(query) if self.nlp else None
        
        # =====================================================================
        # PRIORITY 1: TEMPORAL PATTERNS (most specific)
        # =====================================================================
        
        # Check exact keyword matching
        is_temporal_first = any(p in query_lower for p in self.temporal_first_patterns)
        is_temporal_last = any(p in query_lower for p in self.temporal_last_patterns)
        is_temporal_specific = any(p in query_lower for p in self.temporal_specific_patterns)
        
        # NEW: Check lemmatized forms (catches "recently"→"recent", "starting"→"start")
        has_temporal_lemma = False
        temporal_lemmas = []
        if query_doc:
            # Combine all temporal patterns for lemmatization check
            all_temporal = (
                self.temporal_first_patterns + 
                self.temporal_last_patterns + 
                self.temporal_specific_patterns
            )
            has_temporal_lemma, temporal_lemmas = self._check_lemmatized_patterns(
                query_doc, 
                all_temporal
            )
        
        is_temporal = is_temporal_first or is_temporal_last or is_temporal_specific or has_temporal_lemma
        
        if is_temporal:
            keywords.extend([p for p in self.temporal_first_patterns if p in query_lower])
            keywords.extend([p for p in self.temporal_last_patterns if p in query_lower])
            keywords.extend([p for p in self.temporal_specific_patterns if p in query_lower])
            if has_temporal_lemma:
                keywords.extend(temporal_lemmas)
                matched_patterns.append("temporal_lemma")
            matched_patterns.append("temporal")
        
        # =====================================================================
        # PRIORITY 2: CONVERSATIONAL PATTERNS
        # =====================================================================
        
        is_conversational = any(p in query_lower for p in self.conversational_patterns)
        if is_conversational:
            keywords.extend([p for p in self.conversational_patterns if p in query_lower])
            matched_patterns.append("conversational")
        
        # =====================================================================
        # PRIORITY 3: EMOTIONAL PATTERNS (Enhanced with semantic matching)
        # =====================================================================
        
        is_emotional = False
        has_emotional_keyword = any(kw in query_lower for kw in self.emotional_keywords)
        
        # NEW: Check semantic similarity to emotional keywords
        has_semantic_emotion_match = False
        if query_doc and self.has_vectors:
            has_semantic_emotion_match, emotion_matches = self._semantic_pattern_match(
                query_doc,
                self.emotional_keywords,
                similarity_threshold=0.68  # 68% similarity threshold (balanced - catches variations, prevents false positives)
            )
            if has_semantic_emotion_match:
                semantic_matches.extend(emotion_matches)
                keywords.extend([m["query_token"] for m in emotion_matches])
                logger.info(
                    "🎯 SEMANTIC EMOTION: Found %d semantic matches for emotional patterns",
                    len(emotion_matches)
                )
        
        # NEW: Check lemmatized forms (catches "loving"→"love", "hated"→"hate")
        has_emotion_lemma = False
        emotion_lemmas = []
        if query_doc:
            has_emotion_lemma, emotion_lemmas = self._check_lemmatized_patterns(
                query_doc,
                self.emotional_keywords
            )
        
        has_high_emotion_intensity = False
        if emotion_data:
            emotional_intensity = emotion_data.get('emotional_intensity', 0.0)
            has_high_emotion_intensity = emotional_intensity > self.emotion_intensity_threshold
        
        # Combine all emotional signals
        is_emotional = has_emotional_keyword or has_semantic_emotion_match or has_high_emotion_intensity or has_emotion_lemma
        
        if is_emotional:
            if has_semantic_emotion_match:
                matched_patterns.append("emotional_semantic")
            if has_emotion_lemma:
                keywords.extend(emotion_lemmas)
                matched_patterns.append("emotional_lemma")
            if has_emotional_keyword:
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
        # DEPENDENCY PARSING - Negation & SVO Extraction
        # =====================================================================
        
        # Extract grammatical structure if spaCy available
        negation_info = self._detect_negation(query_doc) if query_doc else {}
        svo_relationships = self._extract_svo_relationships(query_doc) if query_doc else []
        
        # =====================================================================
        # POS TAGGING - Question Sophistication Analysis
        # =====================================================================
        
        # Analyze question patterns using POS tags
        question_sophistication = self._analyze_question_sophistication(query_doc) if query_doc else {}
        
        # =====================================================================
        # CUSTOM MATCHER - Advanced Pattern Extraction (Task 3.1)
        # =====================================================================
        
        # Extract sophisticated token-level patterns
        matcher_patterns = self._extract_matcher_patterns(query_doc) if query_doc else {}
        
        # Analyze matcher results
        has_hedging = "HEDGING" in matcher_patterns and len(matcher_patterns["HEDGING"]) > 0
        has_temporal_change = "TEMPORAL_CHANGE" in matcher_patterns and len(matcher_patterns["TEMPORAL_CHANGE"]) > 0
        has_strong_preference = "STRONG_PREFERENCE" in matcher_patterns and len(matcher_patterns["STRONG_PREFERENCE"]) > 0
        has_negated_preference = "NEGATED_PREFERENCE" in matcher_patterns and len(matcher_patterns["NEGATED_PREFERENCE"]) > 0
        has_conditional = "CONDITIONAL" in matcher_patterns and len(matcher_patterns["CONDITIONAL"]) > 0
        
        # =====================================================================
        # EXTRACT ENTITY AND RELATIONSHIP INFO
        # =====================================================================
        
        entity_type = self._extract_entity_type(query_lower)
        relationship_type = self._extract_relationship_type(
            query_lower,
            negation_info=negation_info,
            svo_relationships=svo_relationships
        )
        
        # =====================================================================
        # ASSESS TOOL COMPLEXITY (NEW: Week 1 hybrid routing)
        # =====================================================================
        
        tool_complexity = self._assess_tool_complexity(
            query=query,
            query_doc=query_doc,
            matched_patterns=matched_patterns,
            question_complexity=question_sophistication.get("complexity_score", 0)
        )
        
        # Override intent and add LLM_TOOLS data source if complexity threshold met
        if tool_complexity > self.tool_complexity_threshold:
            intent_type = QueryIntent.TOOL_ASSISTED
            data_sources.add(DataSource.LLM_TOOLS)
            matched_patterns.append("tool_assisted")
            logger.info(
                "🔧 TOOL ASSISTED: complexity=%.2f (threshold=%.2f) → using LLM tool calling",
                tool_complexity, self.tool_complexity_threshold
            )
        
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
            semantic_matches=semantic_matches,  # Semantic similarity matches
            has_negation=negation_info.get("has_negation", False),  # Task 2.1: Negation detection
            svo_relationships=svo_relationships,  # Task 2.1: SVO extraction
            is_preference_question=question_sophistication.get("is_preference", False),  # Task 2.2: Preference questions
            is_comparison_question=question_sophistication.get("is_comparison", False),  # Task 2.2: Comparison questions
            is_hypothetical_question=question_sophistication.get("is_hypothetical", False),  # Task 2.2: Hypothetical questions
            question_complexity=question_sophistication.get("complexity_score", 0),  # Task 2.2: Complexity scoring
            matched_advanced_patterns=matcher_patterns,  # Task 3.1: Custom matcher patterns
            has_hedging=has_hedging,  # Task 3.1: Hedging language detection
            has_temporal_change=has_temporal_change,  # Task 3.1: Temporal change detection
            has_strong_preference=has_strong_preference,  # Task 3.1: Strong preference detection
            classification_time_ms=classification_time_ms,
        )
        
        logger.info(
            "🎯 UNIFIED CLASSIFICATION: query='%s...' → intent=%s, strategy=%s (conf: %.2f/%.2f)%s%s%s%s%s%s",
            query[:40], intent_type.value, vector_strategy.value,
            intent_confidence, strategy_confidence,
            f" [+{len(semantic_matches)} semantic]" if semantic_matches else "",
            " [negation]" if negation_info.get("has_negation") else "",
            f" [complexity={question_sophistication.get('complexity_score', 0)}]" if question_sophistication.get('complexity_score', 0) > 0 else "",
            " [hedging]" if has_hedging else "",
            " [temporal_change]" if has_temporal_change else "",
            " [strong_pref]" if has_strong_preference else ""
        )
        
        return result
    
    # ========================================================================
    # DEPENDENCY PARSING - Negation & SVO Extraction
    # ========================================================================
    
    def _detect_negation(self, query_doc) -> Dict[str, Any]:
        """
        Detect negation in query using dependency parsing.
        
        Args:
            query_doc: spaCy Doc object
        
        Returns:
            Dict with negation info: {
                "has_negation": bool,
                "negated_verbs": List[str],
                "negation_tokens": List[str]
            }
        """
        if not self.nlp:
            return {"has_negation": False, "negated_verbs": [], "negation_tokens": []}
        
        negated_verbs = []
        negation_tokens = []
        
        for token in query_doc:
            # Check if token is negated (has 'neg' dependency)
            for child in token.children:
                if child.dep_ == "neg":
                    negated_verbs.append(token.lemma_)
                    negation_tokens.append(child.text)
                    
                    logger.debug(
                        "🚫 NEGATION DETECTED: '%s' negates '%s'",
                        child.text, token.text
                    )
        
        return {
            "has_negation": len(negated_verbs) > 0,
            "negated_verbs": negated_verbs,
            "negation_tokens": negation_tokens
        }
    
    def _extract_svo_relationships(self, query_doc) -> List[Dict[str, Any]]:
        """
        Extract subject-verb-object triples using dependency parsing.
        
        Args:
            query_doc: spaCy Doc object
        
        Returns:
            List of SVO dicts: {
                "subject": str,
                "verb": str (lemmatized),
                "object": str,
                "negated": bool,
                "confidence": float,
                "sentence": str
            }
        """
        if not self.nlp:
            return []
        
        relationships = []
        
        for token in query_doc:
            # Find ROOT verb (main verb of sentence)
            if token.dep_ == "ROOT" and token.pos_ == "VERB":
                subject = None
                obj = None
                is_negated = False
                
                # Extract subject and object from verb's children
                for child in token.children:
                    # Subject (who/what does the action)
                    if child.dep_ in ["nsubj", "nsubjpass"]:
                        subject = child.text
                    
                    # Object (who/what receives the action)
                    elif child.dep_ in ["dobj", "pobj", "attr"]:
                        obj = child.text
                    
                    # Negation
                    elif child.dep_ == "neg":
                        is_negated = True
                
                # Only add if we found both subject and object
                if subject and obj:
                    relationships.append({
                        "subject": subject,
                        "verb": token.lemma_,
                        "object": obj,
                        "negated": is_negated,
                        "confidence": 0.9,  # High confidence for clear SVO
                        "sentence": token.sent.text
                    })
                    
                    logger.debug(
                        "🎯 SVO EXTRACTED: %s %s %s %s",
                        subject, "NOT" if is_negated else "", token.lemma_, obj
                    )
        
        return relationships
    
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
    
    def _extract_relationship_type(
        self,
        query_lower: str,
        negation_info: Optional[Dict] = None,
        svo_relationships: Optional[List[Dict]] = None
    ) -> Optional[str]:
        """
        Extract relationship type from query with negation awareness.
        
        Args:
            query_lower: Lowercase query string
            negation_info: Optional negation detection results
            svo_relationships: Optional SVO extraction results
        
        Returns:
            Relationship type: likes, dislikes, knows, wants, fears, or None
        """
        # Check for negated preferences first
        if negation_info and negation_info.get("has_negation"):
            negated_verbs = negation_info.get("negated_verbs", [])
            
            # If "like", "love", "enjoy" are negated → dislikes
            if any(verb in ['like', 'love', 'enjoy', 'prefer'] for verb in negated_verbs):
                logger.debug("🚫 Negated positive verb → dislikes")
                return 'dislikes'
            
            # If "dislike", "hate" are negated → likes (double negative)
            if any(verb in ['dislike', 'hate', 'avoid'] for verb in negated_verbs):
                logger.debug("🚫 Negated negative verb → likes (double negative)")
                return 'likes'
        
        # Use SVO relationships if available
        if svo_relationships:
            for svo in svo_relationships:
                verb = svo['verb']
                negated = svo['negated']
                
                # Map verb to relationship type
                if verb in ['like', 'love', 'enjoy', 'prefer']:
                    result = 'dislikes' if negated else 'likes'
                    logger.debug("🎯 SVO relationship: %s → %s", verb, result)
                    return result
                elif verb in ['dislike', 'hate', 'avoid']:
                    result = 'likes' if negated else 'dislikes'  # Double negative
                    logger.debug("🎯 SVO relationship: %s (negated=%s) → %s", verb, negated, result)
                    return result
                elif verb in ['know', 'familiar', 'aware']:
                    return 'knows'
                elif verb in ['want', 'need', 'desire', 'wish']:
                    return 'wants'
                elif verb in ['fear', 'afraid', 'scared']:
                    return 'fears'
        
        # Fallback to keyword matching (existing implementation)
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
    
    def _analyze_question_sophistication(self, query_doc) -> Dict[str, Any]:
        """
        Analyze question sophistication using POS tagging patterns.
        
        Detects:
        - Preference questions (favorite, best, preferred)
        - Comparison questions (better than, worse than)
        - Hypothetical questions (would, could, should)
        - Question complexity score
        
        Args:
            query_doc: spaCy Doc object
            
        Returns:
            Dict with keys:
            - is_preference: bool
            - is_comparison: bool
            - is_hypothetical: bool
            - complexity_score: int (0-10)
            - detected_patterns: List[str]
        """
        if not self.nlp or not query_doc:
            return {
                "is_preference": False,
                "is_comparison": False,
                "is_hypothetical": False,
                "complexity_score": 0,
                "detected_patterns": []
            }
        
        is_preference = False
        is_comparison = False
        is_hypothetical = False
        detected_patterns = []
        
        # Count POS types for complexity
        pos_counts = {}
        for token in query_doc:
            pos_counts[token.pos_] = pos_counts.get(token.pos_, 0) + 1
        
        # Detect preference questions (adjectives: favorite, best, preferred, etc.)
        preference_adjectives = {
            'favorite', 'favourite', 'best', 'preferred', 'ideal', 
            'top', 'primary', 'main', 'go-to'
        }
        
        for token in query_doc:
            if token.pos_ == "ADJ" and token.lemma_.lower() in preference_adjectives:
                is_preference = True
                detected_patterns.append(f"preference_adj:{token.text}")
                logger.debug("🎯 PREFERENCE QUESTION: Found adjective '%s'", token.text)
        
        # Detect comparison questions (adjective + "than")
        for token in query_doc:
            if token.pos_ == "ADJ":
                # Check if any child is "than"
                for child in token.children:
                    if child.text.lower() == "than":
                        is_comparison = True
                        detected_patterns.append(f"comparison:{token.text}_than")
                        logger.debug("🎯 COMPARISON QUESTION: Found '%s than'", token.text)
                        break
                
                # Also check siblings/context for "than" (more flexible)
                for other_token in query_doc:
                    if other_token.text.lower() == "than" and abs(other_token.i - token.i) <= 3:
                        if token.pos_ == "ADJ":
                            is_comparison = True
                            detected_patterns.append(f"comparison_context:{token.text}")
                            logger.debug("🎯 COMPARISON QUESTION: Context '%s ... than'", token.text)
                            break
        
        # Detect hypothetical questions (modal verbs: would, could, should, might)
        hypothetical_modals = {'would', 'could', 'should', 'might', 'may'}
        
        for token in query_doc:
            if token.pos_ == "AUX" and token.text.lower() in hypothetical_modals:
                is_hypothetical = True
                detected_patterns.append(f"hypothetical_modal:{token.text}")
                logger.debug("🎯 HYPOTHETICAL QUESTION: Found modal '%s'", token.text)
        
        # Calculate complexity score (0-10)
        complexity_score = 0
        
        # More POS types = more complex (max 5 points)
        complexity_score += min(len(pos_counts), 5)
        
        # Preference questions are moderately complex (+2)
        if is_preference:
            complexity_score += 2
        
        # Comparison questions are more complex (+3)
        if is_comparison:
            complexity_score += 3
        
        # Hypothetical questions are most complex (+4)
        if is_hypothetical:
            complexity_score += 4
        
        # Cap at 10
        complexity_score = min(complexity_score, 10)
        
        logger.debug(
            "🎯 QUESTION SOPHISTICATION: preference=%s, comparison=%s, hypothetical=%s, complexity=%d",
            is_preference, is_comparison, is_hypothetical, complexity_score
        )
        
        return {
            "is_preference": is_preference,
            "is_comparison": is_comparison,
            "is_hypothetical": is_hypothetical,
            "complexity_score": complexity_score,
            "detected_patterns": detected_patterns
        }
    
    # ========================================================================
    # CUSTOM MATCHER - Advanced Pattern Extraction (Task 3.1)
    # ========================================================================
    
    def _extract_matcher_patterns(self, query_doc) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract custom matcher patterns from query (Task 3.1: Custom Matcher).
        
        Uses spaCy Matcher to detect sophisticated token-level patterns:
        - NEGATED_PREFERENCE: "don't like", "doesn't enjoy"
        - STRONG_PREFERENCE: "really love", "absolutely hate"
        - TEMPORAL_CHANGE: "used to like", "no longer enjoy"
        - HEDGING: "maybe like", "kind of prefer"
        - CONDITIONAL: "if I could", "would prefer"
        
        Args:
            query_doc: spaCy Doc object
            
        Returns:
            Dict mapping pattern names to list of matched spans:
            {
                "NEGATED_PREFERENCE": [
                    {"text": "don't like", "lemma": "do not like", "start": 2, "end": 4, "root": "like"}
                ],
                "STRONG_PREFERENCE": [],
                ...
            }
        """
        if self.matcher is None or query_doc is None:  # FIX: Empty Matcher evaluates to False
            return {}
        
        # Run matcher on query
        matches = self.matcher(query_doc)
        
        # Group matches by pattern name
        pattern_matches = {}
        
        for match_id, start, end in matches:
            # Get pattern name from match ID
            pattern_name = self.nlp.vocab.strings[match_id]
            span = query_doc[start:end]
            
            # Initialize list for this pattern if not exists
            if pattern_name not in pattern_matches:
                pattern_matches[pattern_name] = []
            
            # Add match details
            pattern_matches[pattern_name].append({
                "text": span.text,          # Original matched text
                "lemma": span.lemma_,       # Lemmatized form
                "start": start,             # Start token index
                "end": end,                 # End token index (exclusive)
                "root": span.root.text      # Root/main token in span
            })
            
            logger.debug(
                "🎯 MATCHER: Found %s → '%s' (tokens %d-%d)",
                pattern_name, span.text, start, end
            )
        
        return pattern_matches
    
    def _assess_tool_complexity(
        self,
        query: str,
        query_doc,
        matched_patterns: List[str],
        question_complexity: int
    ) -> float:
        """
        Assess whether query requires LLM tool calling for structured data retrieval.
        
        Tool calling is recommended for queries that need:
        - Multi-source data aggregation (facts + conversations + temporal)
        - Complex relationship traversal
        - Temporal trend analysis
        - Entity-relationship discovery
        
        Args:
            query: User query string
            query_doc: spaCy Doc object (or None)
            matched_patterns: List of matched classification patterns
            question_complexity: Question complexity score (0-10)
        
        Returns:
            Complexity score (0.0-1.0). Above self.tool_complexity_threshold → use tools.
        """
        complexity = 0.0
        query_lower = query.lower()
        
        # Multi-source requirements (facts + conversations + temporal)
        multi_source_keywords = [
            "everything", "all", "complete", "comprehensive", "full",
            "relationship", "history", "timeline", "journey", "story"
        ]
        if any(word in query_lower for word in multi_source_keywords):
            complexity += 0.25
        
        # Temporal analysis needs (trends, changes, evolution)
        temporal_analysis_keywords = [
            "trend", "change", "over time", "evolution", "progress",
            "how have", "how has", "compared to", "before and after"
        ]
        if any(word in query_lower for word in temporal_analysis_keywords):
            complexity += 0.3
        
        # Entity references via spaCy NER (indicates structured data needs)
        if query_doc and len(query_doc.ents) > 0:
            complexity += 0.2
        
        # Complex question structure (multiple question words or clauses)
        question_words = ["what", "where", "when", "why", "how", "which", "who"]
        question_word_count = sum(1 for word in question_words if word in query_lower)
        if question_word_count >= 2:
            complexity += 0.2
        elif question_word_count >= 1:
            complexity += 0.1
        
        # High question complexity from POS tagging
        if question_complexity >= 5:
            complexity += 0.15
        
        # Long queries often need structured retrieval
        word_count = len(query.split())
        if word_count > 15:
            complexity += 0.15
        elif word_count > 10:
            complexity += 0.1
        
        # Aggregation keywords (summarize, tell me about, what do you know)
        aggregation_keywords = [
            "summarize", "summary", "tell me about", "what do you know",
            "give me", "show me", "list", "enumerate"
        ]
        if any(word in query_lower for word in aggregation_keywords):
            complexity += 0.2
        
        return min(complexity, 1.0)
    
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
