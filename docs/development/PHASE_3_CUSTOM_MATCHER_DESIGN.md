# Phase 3: Custom Matcher Architecture Design

**Implementation Date**: January 20, 2025  
**Estimated Time**: 5 hours  
**Goal**: Add spaCy's `Matcher` for sophisticated token-level pattern detection

---

## 🎯 Design Overview

### **What We're Adding**
spaCy's `Matcher` allows us to define complex token-level patterns that go beyond simple keyword matching. This enables detection of sophisticated linguistic patterns like:
- Negated preferences ("don't like", "doesn't enjoy")
- Strong preferences ("really love", "absolutely hate")
- Temporal changes ("used to like", "no longer enjoy")
- Hedging language ("maybe like", "kind of prefer")
- Conditional statements ("if I could", "would prefer")

### **Integration Points**
1. **Initialization**: Build matcher in `__init__()` after spaCy initialization
2. **Pattern Extraction**: Add `_extract_matcher_patterns()` method
3. **Classification**: Integrate into `classify()` workflow after POS tagging
4. **Dataclass**: Add 4 new fields for matcher results

---

## 📋 Pattern Categories

### **1. Negated Preferences** (Priority: HIGH)
```python
# Pattern: do/does/did + not/n't + like/love/enjoy/prefer
# Examples:
# - "I don't like spicy food"
# - "She doesn't enjoy hiking"
# - "We didn't love that restaurant"

[
    {"LEMMA": {"IN": ["do", "does", "did"]}},
    {"LOWER": {"IN": ["not", "n't"]}},
    {"LEMMA": {"IN": ["like", "love", "enjoy", "prefer", "want"]}}
]
```

**Routing Impact**: HIGH - Changes "like" to "dislike" for fact extraction

### **2. Strong Preferences** (Priority: MEDIUM)
```python
# Pattern: really/absolutely/definitely + like/love/enjoy
# Examples:
# - "I really love pizza"
# - "She absolutely hates seafood"
# - "We definitely prefer Italian"

[
    {"LOWER": {"IN": ["really", "absolutely", "definitely", "totally", "completely"]}},
    {"LEMMA": {"IN": ["like", "love", "enjoy", "prefer", "hate", "dislike"]}}
]
```

**Routing Impact**: MEDIUM - Boosts confidence for factual recall

### **3. Temporal Changes** (Priority: HIGH)
```python
# Pattern: used to + verb
# Examples:
# - "I used to like sushi"
# - "She used to enjoy running"
# - "We used to prefer tea"

[
    {"LOWER": "used"},
    {"LOWER": "to"},
    {"POS": "VERB"}
]
```

**Routing Impact**: HIGH - Routes to temporal analysis (InfluxDB)

### **4. Hedging Language** (Priority: MEDIUM)
```python
# Pattern: maybe/perhaps/might/kind of + verb
# Examples:
# - "I maybe like chocolate"
# - "She might prefer coffee"
# - "I kind of enjoy hiking"

[
    {"LOWER": {"IN": ["maybe", "perhaps", "possibly", "might", "kind", "sort"]}},
    {"LOWER": {"IN": ["of"]}, "OP": "?"},  # Optional "of"
    {"POS": "VERB"}
]
```

**Routing Impact**: MEDIUM - Reduces confidence for fact storage

### **5. Conditional Statements** (Priority: LOW)
```python
# Pattern: if + subject + could/would + verb
# Examples:
# - "If I could, I would try sushi"
# - "If possible, I'd prefer coffee"

[
    {"LOWER": "if"},
    {"POS": "PRON", "OP": "?"},  # Optional pronoun
    {"LEMMA": {"IN": ["could", "would", "should", "can"]}},
    {"POS": "VERB"}
]
```

**Routing Impact**: LOW - Routes to hypothetical reasoning (LLM)

---

## 🏗️ Implementation Plan

### **Step 1: Add spaCy Matcher Import**
```python
# At top of file with other imports
from spacy.matcher import Matcher
```

### **Step 2: Initialize Matcher in __init__()**
```python
def __init__(self, postgres_pool=None, qdrant_client=None):
    """Initialize unified classifier with optional data store connections."""
    self.postgres = postgres_pool
    self.qdrant = qdrant_client
    
    # Build pattern dictionaries
    self._build_patterns()
    
    # Configuration
    self.emotion_intensity_threshold = 0.3
    
    # Initialize spaCy with word vectors
    self._init_spacy_vectors()
    
    # Initialize custom matcher (NEW)
    self._init_custom_matcher()
    
    # Cache for keyword vectors
    self._keyword_vector_cache = {}
    
    logger.info("✅ UnifiedQueryClassifier initialized")

def _init_custom_matcher(self):
    """
    Initialize spaCy Matcher with custom token-level patterns.
    
    Falls back gracefully if spaCy unavailable.
    """
    if not self.nlp:
        self.matcher = None
        logger.warning("⚠️ Custom matcher disabled (spaCy unavailable)")
        return
    
    self.matcher = Matcher(self.nlp.vocab)
    self._register_matcher_patterns()
    
    logger.info(f"✅ Custom matcher initialized ({len(self.matcher)} patterns)")
```

### **Step 3: Register All Patterns**
```python
def _register_matcher_patterns(self):
    """Register all custom token-level patterns with matcher."""
    if not self.matcher:
        return
    
    # 1. Negated Preferences
    self.matcher.add("NEGATED_PREFERENCE", [[
        {"LEMMA": {"IN": ["do", "does", "did"]}},
        {"LOWER": {"IN": ["not", "n't"]}},
        {"LEMMA": {"IN": ["like", "love", "enjoy", "prefer", "want"]}}
    ]])
    
    # 2. Strong Preferences
    self.matcher.add("STRONG_PREFERENCE", [[
        {"LOWER": {"IN": ["really", "absolutely", "definitely", "totally", "completely"]}},
        {"LEMMA": {"IN": ["like", "love", "enjoy", "prefer", "hate", "dislike"]}}
    ]])
    
    # 3. Temporal Changes
    self.matcher.add("TEMPORAL_CHANGE", [[
        {"LOWER": "used"},
        {"LOWER": "to"},
        {"POS": "VERB"}
    ]])
    
    # 4. Hedging Language
    self.matcher.add("HEDGING", [
        [  # Pattern 1: maybe/perhaps + verb
            {"LOWER": {"IN": ["maybe", "perhaps", "possibly", "might"]}},
            {"POS": "VERB"}
        ],
        [  # Pattern 2: kind/sort + of + verb
            {"LOWER": {"IN": ["kind", "sort"]}},
            {"LOWER": "of"},
            {"POS": "VERB"}
        ]
    ])
    
    # 5. Conditional Statements
    self.matcher.add("CONDITIONAL", [[
        {"LOWER": "if"},
        {"POS": "PRON", "OP": "?"},
        {"LEMMA": {"IN": ["could", "would", "should", "can"]}},
        {"POS": "VERB"}
    ]])
    
    logger.debug("🎯 Registered 5 custom matcher pattern categories")
```

### **Step 4: Extract Matched Patterns**
```python
def _extract_matcher_patterns(self, query_doc) -> Dict[str, List[Dict[str, str]]]:
    """
    Extract custom matcher patterns from query.
    
    Args:
        query_doc: spaCy Doc object
        
    Returns:
        Dict mapping pattern names to list of matched spans:
        {
            "NEGATED_PREFERENCE": [
                {"text": "don't like", "start": 2, "end": 4}
            ],
            "STRONG_PREFERENCE": [],
            ...
        }
    """
    if not self.matcher or not query_doc:
        return {}
    
    # Run matcher
    matches = self.matcher(query_doc)
    
    # Group matches by pattern name
    pattern_matches = {}
    
    for match_id, start, end in matches:
        pattern_name = self.nlp.vocab.strings[match_id]
        span = query_doc[start:end]
        
        if pattern_name not in pattern_matches:
            pattern_matches[pattern_name] = []
        
        pattern_matches[pattern_name].append({
            "text": span.text,
            "lemma": span.lemma_,
            "start": start,
            "end": end,
            "root": span.root.text  # Main token in span
        })
        
        logger.debug(
            f"🎯 MATCHER: Found {pattern_name} → '{span.text}' (tokens {start}-{end})"
        )
    
    return pattern_matches
```

### **Step 5: Update Dataclass**
```python
@dataclass
class UnifiedClassification:
    """Complete query classification result."""
    
    # ... existing fields ...
    
    # Task 2.2: POS Tagging fields
    is_preference_question: bool = False
    is_comparison_question: bool = False
    is_hypothetical_question: bool = False
    question_complexity: int = 0
    
    # Task 3.1: Custom Matcher fields (NEW)
    matched_advanced_patterns: List[Dict[str, Any]] = field(default_factory=list)
    """List of matched advanced patterns from spaCy Matcher"""
    
    has_hedging: bool = False
    """Whether query contains hedging language (maybe, perhaps, kind of)"""
    
    has_temporal_change: bool = False
    """Whether query contains temporal change pattern (used to)"""
    
    has_strong_preference: bool = False
    """Whether query contains strong preference modifiers (really, absolutely)"""
    
    classification_time_ms: float = 0.0
```

### **Step 6: Integrate into classify() Workflow**
```python
async def classify(
    self, 
    query: str,
    emotion_data: Optional[Dict] = None,
    user_id: Optional[str] = None
) -> UnifiedClassification:
    """Classify query intent, vector strategy, and data sources."""
    start_time = time.time()
    
    # ... existing code ...
    
    # Process with spaCy
    query_doc = self.nlp(query) if self.nlp else None
    
    # Extract grammatical features
    negation_info = self._detect_negation(query_doc) if query_doc else {}
    svo_relationships = self._extract_svo_relationships(query_doc) if query_doc else []
    question_sophistication = self._analyze_question_sophistication(query_doc) if query_doc else {}
    
    # Extract custom matcher patterns (NEW)
    matcher_patterns = self._extract_matcher_patterns(query_doc) if query_doc else {}
    
    # Analyze matcher results (NEW)
    has_hedging = "HEDGING" in matcher_patterns and len(matcher_patterns["HEDGING"]) > 0
    has_temporal_change = "TEMPORAL_CHANGE" in matcher_patterns and len(matcher_patterns["TEMPORAL_CHANGE"]) > 0
    has_strong_preference = "STRONG_PREFERENCE" in matcher_patterns and len(matcher_patterns["STRONG_PREFERENCE"]) > 0
    has_negated_preference = "NEGATED_PREFERENCE" in matcher_patterns and len(matcher_patterns["NEGATED_PREFERENCE"]) > 0
    has_conditional = "CONDITIONAL" in matcher_patterns and len(matcher_patterns["CONDITIONAL"]) > 0
    
    # ... continue with existing classification logic ...
    
    # Build result
    result = UnifiedClassification(
        # ... existing fields ...
        
        # Task 3.1: Matcher patterns
        matched_advanced_patterns=matcher_patterns,
        has_hedging=has_hedging,
        has_temporal_change=has_temporal_change,
        has_strong_preference=has_strong_preference,
        
        classification_time_ms=(time.time() - start_time) * 1000
    )
    
    logger.info(
        "🎯 UNIFIED CLASSIFICATION: query='%s...' → intent=%s, strategy=%s"
        "%s%s%s",
        query[:40], result.intent_type.value, result.vector_strategy.value,
        f" [hedging]" if has_hedging else "",
        f" [temporal_change]" if has_temporal_change else "",
        f" [strong_pref]" if has_strong_preference else ""
    )
    
    return result
```

---

## 📊 Expected Outcomes

### **Performance Targets**
- **Matcher Overhead**: <2ms per query (compiled patterns are fast)
- **Total Classification**: <35ms (including all spaCy analysis)
- **Memory**: +~5MB for matcher patterns (negligible)

### **Accuracy Improvements**
- **Negation Detection**: 100% accuracy on "don't like" patterns
- **Temporal Changes**: 95%+ detection of "used to" patterns
- **Strong Preferences**: 90%+ detection of intensity modifiers

### **Use Cases**
1. **User Says**: "I don't like spicy food"
   - **Detected**: NEGATED_PREFERENCE
   - **Routing**: Store as "dislikes" relationship (not "likes")

2. **User Says**: "I really love pizza"
   - **Detected**: STRONG_PREFERENCE
   - **Routing**: High confidence factual recall

3. **User Says**: "I used to enjoy hiking"
   - **Detected**: TEMPORAL_CHANGE
   - **Routing**: Temporal analysis (InfluxDB)

4. **User Says**: "I maybe like chocolate"
   - **Detected**: HEDGING
   - **Routing**: Low confidence fact storage

---

## ✅ Acceptance Criteria

1. ✅ spaCy Matcher initialized in __init__()
2. ✅ 5 pattern categories registered
3. ✅ _extract_matcher_patterns() returns structured results
4. ✅ 4 new fields added to UnifiedClassification dataclass
5. ✅ Matcher integrated into classify() workflow
6. ✅ 25+ unit tests with 100% pass rate
7. ✅ Performance <35ms total classification time
8. ✅ Logging shows matched patterns with 🎯 emoji
9. ✅ Graceful fallback if spaCy unavailable
10. ✅ Documentation updated

---

## 🚀 Next Steps

1. Implement _init_custom_matcher() and _register_matcher_patterns()
2. Implement _extract_matcher_patterns()
3. Update UnifiedClassification dataclass
4. Integrate into classify() workflow
5. Create comprehensive test suite
6. Update documentation and mark Phase 3 complete

---

**Design Status**: ✅ APPROVED  
**Ready for Implementation**: YES  
**Estimated Completion**: 5 hours
