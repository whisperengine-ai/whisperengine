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
    
    # Meta-query detection (NEW: queries about conversation history itself)
    is_meta_query: bool = False
    """Whether query is about conversation history itself (creates circular retrieval)"""
    
    meta_query_patterns: List[str] = field(default_factory=list)
    """Patterns detected for meta-query classification"""
    
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
        # Tool calling removed - use deterministic spaCy routing instead
        
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
    
    def _detect_meta_query_with_spacy(self, query_doc) -> tuple[bool, List[str]]:
        """
        Detect meta-queries using spaCy dependency parsing and linguistic analysis.
        
        Meta-queries are queries ABOUT the conversation history itself, not about
        specific topics. They create circular retrieval patterns where semantic
        search returns OTHER meta-queries instead of substantive content.
        
        Detection Strategy:
        1. **Keyword patterns**: Direct matches for common meta-query phrases
        2. **Dependency parsing**: Analyze subject-verb-object relationships
           - "What do you know" → ROOT:know, OBJ:what, SUBJ:you
           - "Tell me everything" → ROOT:tell, DOBJ:everything
        3. **Semantic matching**: Find semantically similar meta-query language
        
        Examples of meta-queries:
        - "Based on everything you know about me..."
        - "What have you learned about my interests?"
        - "Summarize our relationship"
        - "What patterns have you noticed?"
        - "Tell me about our conversations"
        
        Args:
            query_doc: spaCy Doc object
            
        Returns:
            Tuple of (is_meta: bool, detected_patterns: List[str])
        """
        # Early return if spaCy unavailable
        if not self.nlp:
            return False, []
        
        detected_patterns = []
        query_text = query_doc.text.lower()
        
        # =====================================================================
        # 1. KEYWORD PATTERN MATCHING (exact + lemmatized)
        # =====================================================================
        # Check exact multi-word patterns
        for pattern in self.meta_query_patterns:
            if pattern in query_text:
                detected_patterns.append(f"pattern:{pattern[:30]}")
        
        # Check lemmatized forms (catches "knowing"→"know", "learned"→"learn")
        has_meta_lemma = False
        meta_lemmas = []
        if query_doc:
            # Combine meta-query verbs and subjects for lemmatization
            meta_keywords = list(self.meta_query_verbs) + list(self.meta_query_subjects)
            has_meta_lemma, meta_lemmas = self._check_lemmatized_patterns(
                query_doc,
                meta_keywords
            )
            if has_meta_lemma:
                detected_patterns.append(f"lemma:{','.join(meta_lemmas[:3])}")
                logger.debug(
                    "🔍 META-QUERY LEMMA: Found lemmatized forms: %s",
                    meta_lemmas[:5]
                )
        
        # =====================================================================
        # 2. DEPENDENCY PARSING ANALYSIS
        # =====================================================================
        for token in query_doc:
            # Check for meta-query ROOT verbs (know, learn, remember, recall)
            if token.dep_ == "ROOT" and token.lemma_ in self.meta_query_verbs:
                # Check if subject is "you" (asking what bot knows)
                for child in token.children:
                    if child.dep_ in ("nsubj", "nsubjpass") and child.lemma_ in ("you", "we"):
                        detected_patterns.append(f"dep:ROOT={token.lemma_}+SUBJ={child.lemma_}")
                        logger.debug(
                            "🔍 META-QUERY DEP: ROOT verb '%s' with subject '%s'",
                            token.lemma_, child.lemma_
                        )
                    
                    # Check for "everything/all" as object
                    if child.dep_ in ("dobj", "pobj") and child.lemma_ in ("everything", "all", "anything"):
                        detected_patterns.append(f"dep:ROOT={token.lemma_}+OBJ={child.lemma_}")
                        logger.debug(
                            "🔍 META-QUERY DEP: ROOT verb '%s' with object '%s'",
                            token.lemma_, child.lemma_
                        )
            
            # Check for self-referential noun phrases (our relationship, our history)
            if token.pos_ == "PRON" and token.lemma_ in ("our", "we"):
                for child in token.head.children:
                    if child.lemma_ in ("relationship", "history", "conversation", "conversations", "chat", "discussion"):
                        detected_patterns.append(f"dep:self_ref=our+{child.lemma_}")
                        logger.debug(
                            "🔍 META-QUERY DEP: Self-referential phrase 'our %s'",
                            child.lemma_
                        )
        
        # =====================================================================
        # 3. SEMANTIC MATCHING (if vectors available)
        # =====================================================================
        if self.has_vectors:
            # Check for semantic similarity to meta-query concepts
            meta_concepts = ["knowledge", "information", "understanding", "history"]
            
            for token in query_doc:
                # Skip stop words, punctuation, and tokens without vectors
                if token.is_stop or token.is_punct or not token.has_vector:
                    continue
                
                for concept in meta_concepts:
                    # Get cached keyword token
                    concept_token = self._get_keyword_token(concept)
                    if concept_token is None:
                        continue
                    
                    # Compute similarity with error handling
                    try:
                        similarity = token.similarity(concept_token)
                        
                        if similarity >= 0.70:  # High threshold for meta-concepts
                            detected_patterns.append(f"semantic:{token.text}≈{concept}")
                            logger.debug(
                                "🔍 META-QUERY SEMANTIC: '%s' ≈ '%s' (%.3f)",
                                token.text, concept, similarity
                            )
                    
                    except Exception as e:
                        # Gracefully handle similarity computation errors
                        logger.debug(
                            "⚠️ Similarity computation failed for '%s' ≈ '%s': %s",
                            token.text, concept, str(e)
                        )
                        continue
        
        # Build result
        is_meta = len(detected_patterns) > 0
        
        if is_meta:
            logger.info(
                "🔍 META-QUERY DETECTED: '%s' → patterns: %s",
                query_doc.text[:60], detected_patterns[:3]
            )
        
        return is_meta, detected_patterns
    
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
        
        # META-QUERY patterns (STRICT: Queries about conversation history itself)
        # REDUCED FALSE POSITIVES: Only clear cases of querying about conversation/relationship
        # 
        # Why we removed overly-broad patterns:
        # - "what do you know" → False positive for "What do you know about X?" (factual queries)
        # - "our relationship" → False positive for "About our relationship..." (normal conversation)
        # - "based on what you know" → False positive for context-setting statements
        # - "what topics should we" → False positive for conversation planning (not history analysis)
        # 
        # True meta-queries have:
        # 1. Explicit conversation/history keywords (not generic topic words)
        # 2. Meta-reflective verbs (summarize, analyze, tell me about)
        # 3. User-specific context (about me, not generic)
        self.meta_query_patterns = [
            # Explicit conversation history queries
            'tell me about our conversations',
            'recall our conversations',
            'remember our conversations',
            'what have we talked about',
            'what did we talk about',
            'what have we discussed',
            'what did we discuss',
            
            # Explicit relationship analysis (with verbs)
            'summarize our relationship',
            'analyze our relationship',
            'tell me about our relationship',
            
            # Explicit patterns about user (not generic)
            'everything you know about me',
            'what you know about me',
            'what have you learned about me',
            'patterns in our conversations',
            'what patterns have you noticed about me',
            
            # Explicit meta-reflection with relationship context
            'based on everything you know about me',
            'based on our conversations',
            'based on our history',
            'based on what i\'ve told you',
        ]
        
        # Self-referential verbs (indicate meta-query via dependency parsing)
        # STRICT: Only verbs that clearly indicate meta-reflection
        self.meta_query_verbs = ['summarize', 'analyze', 'recall', 'remember', 'tell me about']
        
        # Self-referential subjects (asking about the relationship/history itself)
        self.meta_query_subjects = ['our history', 'our conversations', 'our relationship']
    
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
        # PRIORITY 0: META-QUERY DETECTION (highest priority - breaks circular patterns)
        # =====================================================================
        # Queries ABOUT conversation history itself create circular retrieval
        # where semantic search returns OTHER meta-queries instead of substantive content
        
        is_meta_query = False
        meta_query_patterns = []
        
        if query_doc:
            is_meta_query, meta_query_patterns = self._detect_meta_query_with_spacy(query_doc)
        else:
            # Fallback to keyword matching if spaCy unavailable
            is_meta_query = any(p in query_lower for p in self.meta_query_patterns)
            if is_meta_query:
                meta_query_patterns = [p for p in self.meta_query_patterns if p in query_lower]
        
        if is_meta_query:
            keywords.extend(meta_query_patterns)
            matched_patterns.append("meta_query")
            logger.info("🔍 META-QUERY: '%s' → Diverse sampling will be used", query[:60])
        
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
        # PRIORITY 2: CONVERSATIONAL PATTERNS (exact + lemmatized)
        # =====================================================================
        
        # Check exact keyword matching
        is_conversational = any(p in query_lower for p in self.conversational_patterns)
        
        # Check lemmatized forms (catches "we've discussed"→"we have discussed", "we're talking"→"we are talking")
        has_conversational_lemma = False
        conversational_lemmas = []
        if query_doc:
            has_conversational_lemma, conversational_lemmas = self._check_lemmatized_patterns(
                query_doc,
                self.conversational_patterns
            )
        
        # Combine both signals
        is_conversational = is_conversational or has_conversational_lemma
        
        if is_conversational:
            keywords.extend([p for p in self.conversational_patterns if p in query_lower])
            if has_conversational_lemma:
                keywords.extend(conversational_lemmas)
                matched_patterns.append("conversational_lemma")
                logger.debug(
                    "🗣️ CONVERSATIONAL LEMMA: Found lemmatized forms: %s",
                    conversational_lemmas[:5]
                )
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
        # SEMANTIC FUSION: When both temporal and conversational match, analyze semantic intent
        # because context matters more than just presence of keywords
        if is_temporal and is_conversational:
            # Both match - use semantic analysis to determine which is primary intent
            # Check if temporal keywords are dominant (first/last words, multiple temporal terms)
            temporal_count = sum(1 for p in self.temporal_first_patterns if p in query_lower)
            temporal_count += sum(1 for p in self.temporal_last_patterns if p in query_lower)
            temporal_count += sum(1 for p in self.temporal_specific_patterns if p in query_lower)
            
            # If multiple temporal patterns, temporal takes priority
            if temporal_count >= 2:
                intent_type = QueryIntent.TEMPORAL_ANALYSIS
                intent_confidence = 0.92
            else:
                # Single temporal match + conversational = conversational intent primary
                intent_type = QueryIntent.CONVERSATION_STYLE
                intent_confidence = 0.88
            is_multi_category = is_emotional or is_factual
        elif is_temporal:
            # TEMPORAL_ANALYSIS has priority for pure temporal queries
            intent_type = QueryIntent.TEMPORAL_ANALYSIS
            intent_confidence = 0.95
            is_multi_category = is_conversational or is_emotional or is_factual
        elif is_conversational:
            intent_type = QueryIntent.CONVERSATION_STYLE
            intent_confidence = 0.9
        elif is_emotional:
            # IMPROVED: Use RoBERTa emotional intensity to determine routing
            # High emotion intensity (>0.6) = Emotional support needed, lower confidence for strict factual
            # Low intensity (<0.4) = Emotional mention but informational intent, higher confidence for factual
            emotional_intensity = 0.0
            if emotion_data and has_high_emotion_intensity:
                emotional_intensity = emotion_data.get('emotional_intensity', 0.0)
            
            if emotional_intensity > 0.65:
                # Strong emotional content - prioritize conversation style over pure facts
                intent_type = QueryIntent.CONVERSATION_STYLE
                intent_confidence = 0.85  # High confidence in emotional routing
            else:
                # Mild emotional content or emotional keywords in factual query
                intent_type = QueryIntent.FACTUAL_RECALL
                intent_confidence = 0.75  # Use factual intent but emotional routing in strategy
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
        # PHASE 3: DETERMINISTIC SPACY ROUTING
        # =====================================================================
        # Replaces removed tool complexity scoring with deterministic
        # linguistic analysis for improved intent classification accuracy
        # =====================================================================
        
        # Detect analytical queries (comparative, trend, statistical, causal)
        analytical_analysis = self._detect_analytical_query(query_doc) if query_doc else {}
        is_analytical = analytical_analysis.get("is_analytical", False)
        analytical_type = analytical_analysis.get("analytical_type")
        analytical_confidence = analytical_analysis.get("confidence", 0.0)
        
        # Detect aggregation requests (summary, totals, counts, lists)
        aggregation_analysis = self._detect_aggregation_request(query_doc) if query_doc else {}
        is_aggregation = aggregation_analysis.get("is_aggregation", False)
        aggregation_type = aggregation_analysis.get("aggregation_type")
        aggregation_confidence = aggregation_analysis.get("confidence", 0.0)
        
        # Detect explicit temporal bounds (dates, date ranges)
        temporal_bounds = self._detect_temporal_bounds(query_doc) if query_doc else {}
        has_temporal_bound = temporal_bounds.get("has_temporal_bound", False)
        temporal_bound_type = temporal_bounds.get("bound_type")
        
        # Advanced emotional routing (RoBERTa + linguistic stress markers)
        emotion_routing = self._advanced_emotion_routing(emotion_data, query_doc)
        needs_emotional_support = emotion_routing.get("needs_emotional_support", False)
        support_level = emotion_routing.get("support_level")
        
        # =====================================================================
        # APPLY DETERMINISTIC ROUTING ADJUSTMENTS
        # =====================================================================
        # Override intent/strategy based on deterministic spaCy analysis
        # Only override if confidence is high enough (>0.75)
        # =====================================================================
        
        # ANALYTICAL QUERIES: Route to appropriate analytical intent
        if is_analytical and analytical_confidence > 0.75:
            if analytical_type == "comparative":
                # Comparative queries need semantic similarity analysis
                vector_strategy = VectorStrategy.SEMANTIC_FUSION
                strategy_confidence = min(strategy_confidence, analytical_confidence)
                matched_patterns.append(f"analytical:{analytical_type}")
                logger.info(
                    "🔬 ANALYTICAL ROUTING: comparative query → SEMANTIC_FUSION (%.2f confidence)",
                    analytical_confidence
                )
            
            elif analytical_type == "trend":
                # Trend analysis requires temporal ordering
                if not is_temporal:  # Don't override existing temporal intent
                    intent_type = QueryIntent.TEMPORAL_ANALYSIS
                    intent_confidence = analytical_confidence
                vector_strategy = VectorStrategy.TEMPORAL_CHRONOLOGICAL
                strategy_confidence = analytical_confidence
                matched_patterns.append(f"analytical:{analytical_type}")
                logger.info(
                    "🔬 ANALYTICAL ROUTING: trend query → TEMPORAL_ANALYSIS (%.2f confidence)",
                    analytical_confidence
                )
            
            elif analytical_type in ["statistical", "causal"]:
                # Statistical/causal queries benefit from semantic fusion
                vector_strategy = VectorStrategy.SEMANTIC_FUSION
                strategy_confidence = min(strategy_confidence, analytical_confidence)
                matched_patterns.append(f"analytical:{analytical_type}")
                logger.info(
                    "🔬 ANALYTICAL ROUTING: %s query → SEMANTIC_FUSION (%.2f confidence)",
                    analytical_type, analytical_confidence
                )
        
        # AGGREGATION REQUESTS: Route to appropriate aggregation strategy
        if is_aggregation and aggregation_confidence > 0.80:
            if aggregation_type == "summary":
                # Summaries need diverse content sampling
                vector_strategy = VectorStrategy.BALANCED_FUSION
                strategy_confidence = aggregation_confidence
                matched_patterns.append(f"aggregation:{aggregation_type}")
                logger.info(
                    "📊 AGGREGATION ROUTING: summary → BALANCED_FUSION (%.2f confidence)",
                    aggregation_confidence
                )
            
            elif aggregation_type in ["count", "list", "total"]:
                # Counts/lists need comprehensive retrieval
                # Keep existing intent but note the aggregation need
                matched_patterns.append(f"aggregation:{aggregation_type}")
                logger.info(
                    "📊 AGGREGATION DETECTED: %s request (%.2f confidence)",
                    aggregation_type, aggregation_confidence
                )
        
        # TEMPORAL BOUNDS: Enhance temporal queries with explicit date constraints
        if has_temporal_bound and temporal_bound_type:
            # If temporal bound detected, ensure temporal analysis is used
            if temporal_bound_type == "date_range":
                intent_type = QueryIntent.TEMPORAL_ANALYSIS
                vector_strategy = VectorStrategy.TEMPORAL_CHRONOLOGICAL
                intent_confidence = 0.95
                strategy_confidence = 0.95
                matched_patterns.append(f"temporal_bound:{temporal_bound_type}")
                logger.info(
                    "📅 TEMPORAL BOUND: date_range detected → TEMPORAL_ANALYSIS"
                )
            else:
                # Specific dates or relative time still need temporal ordering
                if not is_temporal:
                    vector_strategy = VectorStrategy.TEMPORAL_CHRONOLOGICAL
                    strategy_confidence = 0.85
                matched_patterns.append(f"temporal_bound:{temporal_bound_type}")
        
        # EMOTIONAL SUPPORT: Override intent for high emotional support needs
        if needs_emotional_support and support_level:
            if support_level == "high":
                # High support needs override other intents
                intent_type = QueryIntent.CONVERSATION_STYLE
                intent_confidence = 0.95
                vector_strategy = VectorStrategy.EMOTION_FUSION
                strategy_confidence = 0.90
                matched_patterns.append(f"emotional_support:{support_level}")
                logger.info(
                    "💙 EMOTIONAL SUPPORT ROUTING: high support → CONVERSATION_STYLE + EMOTION_FUSION"
                )
            
            elif support_level == "medium":
                # Medium support: use emotional fusion strategy
                vector_strategy = VectorStrategy.EMOTION_FUSION
                strategy_confidence = 0.85
                matched_patterns.append(f"emotional_support:{support_level}")
                logger.info(
                    "💙 EMOTIONAL SUPPORT ROUTING: medium support → EMOTION_FUSION"
                )
            
            elif support_level == "low":
                # Low support: note in patterns but don't override
                matched_patterns.append(f"emotional_support:{support_level}")
        
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
            is_meta_query=is_meta_query,  # NEW: Meta-query detection
            meta_query_patterns=meta_query_patterns,  # NEW: Detected meta-query patterns
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
    
    # =========================================================================
    # PHASE 3: DETERMINISTIC SPACY ROUTING
    # =========================================================================
    # These methods replace the removed tool complexity scoring system with
    # deterministic linguistic analysis for improved intent classification.
    # =========================================================================
    
    def _detect_analytical_query(self, query_doc) -> Dict[str, Any]:
        """
        Detect analytical queries using spaCy linguistic features.
        
        Analytical queries include:
        - Comparative questions: "better than", "worse than", "compared to"
        - Trend analysis: "trend", "pattern", "over time", "changes"
        - Statistical: "average", "typical", "usually", "normally"
        - Causal: "why", "because", "reason", "cause", "effect"
        
        Args:
            query_doc: spaCy Doc object
            
        Returns:
            Dict with:
                - is_analytical: bool
                - analytical_type: str (comparative, trend, statistical, causal, or None)
                - confidence: float (0.0-1.0)
                - indicators: List[str] (matched patterns)
        """
        if not query_doc:
            return {"is_analytical": False, "analytical_type": None, "confidence": 0.0, "indicators": []}
        
        indicators = []
        analytical_type = None
        confidence = 0.0
        
        # Comparative patterns (JJR = comparative adjective, RBR = comparative adverb)
        comparative_adjectives = [token for token in query_doc if token.tag_ in ['JJR', 'RBR']]
        if comparative_adjectives:
            indicators.extend([token.text for token in comparative_adjectives])
            analytical_type = "comparative"
            confidence = 0.85
        
        # Comparative keywords
        comparative_keywords = ['better', 'worse', 'more', 'less', 'compared', 'versus', 'vs', 'than']
        for token in query_doc:
            if token.lemma_ in comparative_keywords:
                indicators.append(token.text)
                analytical_type = "comparative"
                confidence = max(confidence, 0.80)
        
        # Trend analysis patterns
        trend_keywords = ['trend', 'pattern', 'change', 'evolve', 'shift', 'progression', 'development']
        temporal_context = ['over time', 'lately', 'recently', 'historically']
        
        for token in query_doc:
            if token.lemma_ in trend_keywords:
                indicators.append(token.text)
                analytical_type = "trend"
                confidence = max(confidence, 0.75)
        
        query_text = query_doc.text.lower()
        for phrase in temporal_context:
            if phrase in query_text:
                indicators.append(phrase)
                if analytical_type != "comparative":  # Don't override comparative
                    analytical_type = "trend"
                confidence = max(confidence, 0.70)
        
        # Statistical patterns
        statistical_keywords = ['average', 'typical', 'usually', 'normally', 'generally', 'tend', 'often']
        for token in query_doc:
            if token.lemma_ in statistical_keywords:
                indicators.append(token.text)
                if not analytical_type:  # Only set if not already set
                    analytical_type = "statistical"
                confidence = max(confidence, 0.70)
        
        # Causal patterns (WHY questions are highly analytical)
        if any(token.lemma_ == 'why' for token in query_doc):
            indicators.append('why')
            if not analytical_type or analytical_type == "statistical":
                analytical_type = "causal"
            confidence = max(confidence, 0.80)
        
        causal_keywords = ['because', 'reason', 'cause', 'effect', 'result', 'lead', 'impact']
        for token in query_doc:
            if token.lemma_ in causal_keywords:
                indicators.append(token.text)
                if not analytical_type:
                    analytical_type = "causal"
                confidence = max(confidence, 0.65)
        
        is_analytical = len(indicators) > 0
        
        if is_analytical:
            logger.debug(
                "🔬 ANALYTICAL QUERY: type=%s, confidence=%.2f, indicators=%s",
                analytical_type, confidence, indicators[:5]
            )
        
        return {
            "is_analytical": is_analytical,
            "analytical_type": analytical_type,
            "confidence": confidence,
            "indicators": indicators
        }
    
    def _detect_aggregation_request(self, query_doc) -> Dict[str, Any]:
        """
        Detect aggregation requests using spaCy linguistic features.
        
        Aggregation requests include:
        - Summary: "summarize", "overview", "recap", "summary"
        - Totals: "total", "all", "everything", "entire"
        - Counts: "how many", "number of", "count"
        - Lists: "list all", "show me all", "what are all"
        
        Args:
            query_doc: spaCy Doc object
            
        Returns:
            Dict with:
                - is_aggregation: bool
                - aggregation_type: str (summary, total, count, list, or None)
                - confidence: float (0.0-1.0)
                - indicators: List[str]
        """
        if not query_doc:
            return {"is_aggregation": False, "aggregation_type": None, "confidence": 0.0, "indicators": []}
        
        indicators = []
        aggregation_type = None
        confidence = 0.0
        
        query_text = query_doc.text.lower()
        
        # Summary requests (VB = verb base form)
        summary_verbs = ['summarize', 'recap', 'overview', 'review', 'outline']
        for token in query_doc:
            if token.lemma_ in summary_verbs:
                indicators.append(token.text)
                aggregation_type = "summary"
                confidence = 0.90
        
        # Total/entire keywords
        total_keywords = ['total', 'all', 'everything', 'entire', 'whole', 'complete']
        for token in query_doc:
            if token.lemma_ in total_keywords:
                indicators.append(token.text)
                if not aggregation_type:
                    aggregation_type = "total"
                confidence = max(confidence, 0.75)
        
        # Count requests (detect "how many" pattern)
        if 'how many' in query_text or 'how much' in query_text:
            indicators.append('how many/much')
            aggregation_type = "count"
            confidence = 0.95
        
        count_keywords = ['count', 'number', 'quantity', 'amount']
        for token in query_doc:
            if token.lemma_ in count_keywords:
                indicators.append(token.text)
                if not aggregation_type or aggregation_type == "total":
                    aggregation_type = "count"
                confidence = max(confidence, 0.80)
        
        # List requests
        if any(phrase in query_text for phrase in ['list all', 'show me all', 'what are all', 'give me all']):
            indicators.append('list all')
            aggregation_type = "list"
            confidence = 0.85
        
        is_aggregation = len(indicators) > 0
        
        if is_aggregation:
            logger.debug(
                "📊 AGGREGATION REQUEST: type=%s, confidence=%.2f, indicators=%s",
                aggregation_type, confidence, indicators[:5]
            )
        
        return {
            "is_aggregation": is_aggregation,
            "aggregation_type": aggregation_type,
            "confidence": confidence,
            "indicators": indicators
        }
    
    def _detect_temporal_bounds(self, query_doc) -> Dict[str, Any]:
        """
        Detect explicit temporal bounds using spaCy DATE entity recognition.
        
        Temporal bounds include:
        - Specific dates: "January 2024", "last Tuesday", "yesterday"
        - Date ranges: "between X and Y", "from X to Y"
        - Relative time: "in the past week", "over the last month"
        
        Args:
            query_doc: spaCy Doc object
            
        Returns:
            Dict with:
                - has_temporal_bound: bool
                - bound_type: str (specific_date, date_range, relative_time, or None)
                - entities: List[str] (detected DATE entities)
                - confidence: float (0.0-1.0)
        """
        if not query_doc:
            return {"has_temporal_bound": False, "bound_type": None, "entities": [], "confidence": 0.0}
        
        # Extract DATE entities using spaCy NER
        date_entities = [ent.text for ent in query_doc.ents if ent.label_ == 'DATE']
        
        if not date_entities:
            return {"has_temporal_bound": False, "bound_type": None, "entities": [], "confidence": 0.0}
        
        bound_type = None
        confidence = 0.0
        query_text = query_doc.text.lower()
        
        # Date range detection
        range_indicators = ['between', 'from', 'to', 'until', 'through', 'since']
        has_range_indicator = any(word in query_text for word in range_indicators)
        
        if len(date_entities) >= 2 or (len(date_entities) == 1 and has_range_indicator):
            bound_type = "date_range"
            confidence = 0.90
        elif len(date_entities) == 1:
            # Single date entity
            # Check if it's relative ("last week") vs specific ("January 2024")
            relative_terms = ['last', 'past', 'recent', 'previous', 'ago']
            is_relative = any(term in date_entities[0].lower() for term in relative_terms)
            
            if is_relative:
                bound_type = "relative_time"
                confidence = 0.85
            else:
                bound_type = "specific_date"
                confidence = 0.85
        
        has_temporal_bound = len(date_entities) > 0
        
        if has_temporal_bound:
            logger.debug(
                "📅 TEMPORAL BOUND: type=%s, entities=%s, confidence=%.2f",
                bound_type, date_entities, confidence
            )
        
        return {
            "has_temporal_bound": has_temporal_bound,
            "bound_type": bound_type,
            "entities": date_entities,
            "confidence": confidence
        }
    
    def _advanced_emotion_routing(self, emotion_data: Optional[Dict], query_doc) -> Dict[str, Any]:
        """
        Advanced emotional routing using RoBERTa data and linguistic features.
        
        Provides alternative emotional routing paths based on:
        - RoBERTa emotional intensity (already used in Fix 3)
        - Emotional trajectory (stable, escalating, declining)
        - Support indicators (help-seeking language)
        - Stress markers (linguistic patterns indicating distress)
        
        Args:
            emotion_data: Pre-computed RoBERTa emotion analysis
            query_doc: spaCy Doc object
            
        Returns:
            Dict with:
                - needs_emotional_support: bool
                - support_level: str (high, medium, low, or None)
                - stress_indicators: List[str]
                - trajectory: str (stable, escalating, declining, or unknown)
                - confidence: float (0.0-1.0)
        """
        result = {
            "needs_emotional_support": False,
            "support_level": None,
            "stress_indicators": [],
            "trajectory": "unknown",
            "confidence": 0.0
        }
        
        if not emotion_data:
            return result
        
        stress_indicators = []
        
        # Extract RoBERTa emotional intensity (from Fix 3)
        emotional_intensity = emotion_data.get('emotional_intensity', 0.0)
        primary_emotion = emotion_data.get('primary_emotion', '')
        
        # Negative emotions that indicate support needed
        support_needed_emotions = ['sadness', 'fear', 'anger', 'disgust', 'anxiety', 'stress']
        
        # Check if primary emotion indicates distress
        if primary_emotion in support_needed_emotions:
            stress_indicators.append(f"emotion:{primary_emotion}")
        
        # Analyze linguistic stress markers using spaCy
        if query_doc:
            stress_keywords = ['struggling', 'worried', 'anxious', 'stressed', 'overwhelmed', 
                             'difficult', 'hard', 'scared', 'afraid', 'confused', 'lost']
            
            for token in query_doc:
                if token.lemma_ in stress_keywords:
                    stress_indicators.append(token.text)
            
            # Help-seeking language
            help_patterns = ['help', 'advice', 'guidance', 'support', 'what should i do']
            for token in query_doc:
                if token.lemma_ in help_patterns:
                    stress_indicators.append(f"help-seeking:{token.text}")
            
            # Intensifiers (very, really, extremely) amplify stress
            intensifiers = [token for token in query_doc if token.lemma_ in ['very', 'really', 'extremely', 'so']]
            if intensifiers:
                stress_indicators.append(f"intensified:{len(intensifiers)}x")
        
        # Emotional trajectory analysis (if available)
        emotional_trajectory = emotion_data.get('emotional_trajectory', [])
        if emotional_trajectory:
            if 'escalating' in emotional_trajectory:
                result["trajectory"] = "escalating"
            elif 'declining' in emotional_trajectory:
                result["trajectory"] = "declining"
            else:
                result["trajectory"] = "stable"
        
        # Determine support level based on intensity and indicators
        needs_support = False
        support_level = None
        confidence = 0.0
        
        if emotional_intensity > 0.75 and len(stress_indicators) >= 3:
            # High intensity + multiple stress markers = high support needed
            needs_support = True
            support_level = "high"
            confidence = 0.95
        elif emotional_intensity > 0.65 and len(stress_indicators) >= 2:
            # Medium-high intensity + some stress markers = medium support
            needs_support = True
            support_level = "medium"
            confidence = 0.85
        elif emotional_intensity > 0.50 and len(stress_indicators) >= 1:
            # Moderate intensity + at least one stress marker = low support
            needs_support = True
            support_level = "low"
            confidence = 0.70
        elif len(stress_indicators) >= 3:
            # Multiple stress indicators even without high intensity
            needs_support = True
            support_level = "medium"
            confidence = 0.75
        
        if needs_support:
            logger.debug(
                "💙 EMOTIONAL SUPPORT NEEDED: level=%s, intensity=%.2f, indicators=%s, trajectory=%s",
                support_level, emotional_intensity, stress_indicators[:5], result["trajectory"]
            )
        
        result.update({
            "needs_emotional_support": needs_support,
            "support_level": support_level,
            "stress_indicators": stress_indicators,
            "confidence": confidence
        })
        
        return result


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def create_unified_query_classifier(postgres_pool=None, qdrant_client=None):
    """
    Factory function to create UnifiedQueryClassifier instance.
    
    PERFORMANCE NOTE: UnifiedQueryClassifier adds significant overhead (~2x processing time)
    due to spaCy NLP analysis on every query. Disabled by default in production.
    
    Args:
        postgres_pool: Optional PostgreSQL connection pool
        qdrant_client: Optional Qdrant client
        
    Returns:
        Configured UnifiedQueryClassifier instance, or None if disabled
        
    Environment Variables:
        ENABLE_LLM_TOOL_CALLING: Set to 'true' to enable (default: 'false')
    """
    import os
    
    enable_tool_calling = os.getenv('ENABLE_LLM_TOOL_CALLING', 'false').lower() == 'true'
    
    if not enable_tool_calling:
        # Return None - callers must check for None before using
        logger.info("UNIFIED disabled (ENABLE_LLM_TOOL_CALLING=false) - returning None")
        return None
    
    return UnifiedQueryClassifier(postgres_pool, qdrant_client)


