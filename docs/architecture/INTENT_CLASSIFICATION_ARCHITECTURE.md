# Intent Classification Architecture

## 🎯 Overview

WhisperEngine uses **pattern-based intent classification** with priority ordering and confidence scoring. This document clarifies the actual implementation (no LLM calls).

---

## 📋 System Components

### **UnifiedQueryClassifier** (`src/memory/unified_query_classification.py`)

**Purpose:** Single authoritative query classifier combining:
- Vector routing (query intent analysis)
- Intent classification (semantic routing)
- Temporal detection
- Emotion analysis

**Implementation:** Pure pattern matching with keyword detection - NO LLM calls

---

## 🧠 Classification Algorithm

### **Priority-Based Pattern Matching**

The classifier uses a **strict priority order** for determining intent:

```
PRIORITY 1: TEMPORAL patterns
  ↓ (if no match)
PRIORITY 2: CONVERSATIONAL patterns
  ↓ (if no match)
PRIORITY 3: EMOTIONAL patterns
  ↓ (if no match)
PRIORITY 4: FACTUAL patterns
  ↓ (if no match)
PRIORITY 5: ENTITY/RELATIONSHIP patterns
  ↓ (if no match)
DEFAULT: FACTUAL_RECALL (confidence: 0.5)
```

### **Pattern Dictionaries**

**1. Temporal Patterns (Highest Priority)**
```python
temporal_first_patterns = [
    'first', 'earliest', 'initial', 'very first',
    'when did we start', 'beginning', 'start'
]

temporal_last_patterns = [
    'last', 'latest', 'most recent', 'recently',
    'just now', 'moments ago', 'last time', 'just'
]

temporal_specific_patterns = [
    'yesterday', 'today', 'this morning', 'last week',
    'earlier', 'before', 'after', 'ago', 'since'
]
```

**2. Conversational Patterns**
```python
conversational_patterns = [
    'we talked', 'we discussed', 'our conversation',
    'remember when', 'you mentioned', 'you said',
    'what did we', 'last time we spoke'
]
```

**3. Emotional Patterns**
```python
emotional_keywords = [
    'feel', 'feeling', 'emotion', 'mood',
    'happy', 'sad', 'angry', 'excited', 'anxious',
    'how are you', 'how do you feel'
]
```

**4. Factual Patterns**
```python
factual_patterns = [
    'what is', 'what are', 'define', 'explain',
    'how to', 'how does', 'calculate', 'tell me about'
]
```

**5. Entity/Relationship Patterns**
```python
relationship_discovery_patterns = [
    'similar', 'like', 'related', 'connected',
    'recommend', 'suggest', 'compare'
]

entity_search_patterns = [
    'find', 'search', 'look for', 'information about',
    'know about', 'heard of'
]
```

---

## 🎯 Intent Types (7 Categories)

```python
class QueryIntent(Enum):
    FACTUAL_RECALL = "factual_recall"              # "What foods do I like?"
    CONVERSATION_STYLE = "conversation_style"       # "How did we talk about X?"
    TEMPORAL_ANALYSIS = "temporal_analysis"         # "How have preferences changed?"
    PERSONALITY_KNOWLEDGE = "personality_knowledge" # CDL character background
    RELATIONSHIP_DISCOVERY = "relationship_discovery" # "What's similar to X?"
    ENTITY_SEARCH = "entity_search"                 # "Find entities about Y"
    USER_ANALYTICS = "user_analytics"               # "What do you know about me?"
```

---

## 🔍 Vector Search Strategies (6 Types)

```python
class VectorStrategy(Enum):
    CONTENT_ONLY = "content_only"                  # Single content vector
    EMOTION_FUSION = "emotion_fusion"              # Content + emotion vectors
    SEMANTIC_FUSION = "semantic_fusion"            # Content + semantic vectors
    TEMPORAL_CHRONOLOGICAL = "temporal_chronological" # No vectors, chronological
    BALANCED_FUSION = "balanced_fusion"            # All three vectors balanced
    MULTI_CATEGORY = "multi_category"              # Multiple vector types
```

**Strategy Selection Logic:**
- **Temporal queries** → `TEMPORAL_CHRONOLOGICAL` (sort by timestamp)
- **Conversational + Emotional** → `MULTI_CATEGORY` (semantic + emotion vectors)
- **Conversational only** → `SEMANTIC_FUSION` (semantic understanding)
- **Emotional only** → `EMOTION_FUSION` (emotion-weighted search)
- **Factual queries** → `CONTENT_ONLY` (straightforward content matching)

---

## 📊 Data Sources (4 Types)

```python
class DataSource(Enum):
    QDRANT = "qdrant"          # Conversation memories (vector DB)
    POSTGRESQL = "postgresql"  # Structured facts (relational DB)
    INFLUXDB = "influxdb"      # Temporal metrics (time-series DB)
    CDL = "cdl"                # Character personality (database)
```

---

## 🎨 Classification Result Structure

```python
@dataclass
class UnifiedClassification:
    # Core classification
    intent_type: QueryIntent
    vector_strategy: VectorStrategy
    data_sources: Set[DataSource]
    
    # Confidence metrics
    intent_confidence: float        # 0-1 scale
    strategy_confidence: float      # 0-1 scale
    
    # Entity extraction
    entity_type: Optional[str]      # food, hobby, location, etc.
    relationship_type: Optional[str] # likes, dislikes, prefers, etc.
    
    # Temporal flags
    is_temporal: bool
    is_temporal_first: bool         # Sort ascending (earliest first)
    is_temporal_last: bool          # Sort descending (latest first)
    is_multi_category: bool
    
    # Debugging info
    matched_patterns: List[str]     # Which patterns matched
    keywords: List[str]             # Keywords extracted from query
    reasoning: str                  # Human-readable explanation
    classification_time_ms: float
```

---

## 🚀 Usage Example

```python
from src.memory.unified_query_classification import UnifiedQueryClassifier

# Initialize classifier
classifier = UnifiedQueryClassifier()

# Classify user query
query = "What did we talk about yesterday?"
result = await classifier.classify(query)

# Result:
# - intent_type: TEMPORAL_ANALYSIS
# - vector_strategy: TEMPORAL_CHRONOLOGICAL
# - is_temporal: True
# - is_temporal_last: True (sort descending)
# - matched_patterns: ['temporal']
# - keywords: ['yesterday']
# - intent_confidence: 0.95
```

---

## 🔄 Integration with SemanticKnowledgeRouter

**File:** `src/knowledge/semantic_router.py`

```python
class SemanticKnowledgeRouter:
    async def analyze_query_intent(self, query: str):
        # Use UnifiedQueryClassifier for intent analysis
        unified_result = await self._unified_query_classifier.classify(query)
        
        # Fuzzy matching fallback if confidence is low
        if unified_result.intent_confidence < 0.7:
            fuzzy_matches = self._fuzzy_match_intent(query)
            # Combine results with scoring
        
        return unified_result
```

**Fuzzy Matching Features:**
- Uses `rapidfuzz` library for string similarity
- Calculates similarity scores for intent keywords
- Fallback when pattern matching confidence is low
- Combines fuzzy scores with pattern confidence

---

## 🆚 Comparison: Pattern Matching vs LLM

### **Pattern-Based (Current Implementation)**

✅ **Advantages:**
- **Fast**: No API calls, instant classification
- **Deterministic**: Same input → same output
- **No cost**: No token usage
- **No rate limits**: Unlimited classifications
- **Offline capable**: Works without internet
- **Debuggable**: See exactly which patterns matched

❌ **Disadvantages:**
- **Pattern maintenance**: Need to update keyword lists
- **Limited flexibility**: May miss novel phrasings
- **False positives**: Keyword collisions possible

### **LLM-Based (NOT Used in WhisperEngine)**

✅ **Advantages:**
- **Semantic understanding**: Better handles novel phrasings
- **Context-aware**: Can understand nuanced intent
- **No pattern maintenance**: Model learns from data

❌ **Disadvantages:**
- **Latency**: API calls add 200-500ms
- **Cost**: Every classification costs tokens
- **Rate limits**: Can be throttled
- **Non-deterministic**: Same input may vary
- **Hard to debug**: "Black box" decisions

---

## 🧪 Testing & Validation

**Test File:** `tests/test_routing_improvement.py`

**Results (with spaCy entity extraction):**
- ✅ **55.6% improvement** in routing accuracy with entity extraction
- ✅ **69.2% entity extraction accuracy** (spaCy NER)
- ✅ **0.9+ confidence** for most classifications

---

## 📝 Key Takeaways

1. **NO LLM usage in intent classification** - pure pattern matching
2. **Priority-based classification** ensures consistent results
3. **Confidence scoring** enables fallback to fuzzy matching
4. **Fast and deterministic** - perfect for production use
5. **spaCy entity extraction** enhances pattern matching (added 10/25/2025)

---

## 🔍 Where LLMs ARE Used in WhisperEngine

**1. Response Generation** (obvious)
- `src/llm/llm_protocol.py` - LLM client for bot responses

**2. Enrichment Worker** (fact extraction)
- `src/enrichment/worker.py` - LLM extracts facts/preferences from conversations

**3. That's It!**
- Intent classification: Pattern matching
- Entity extraction: spaCy NER
- Memory retrieval: Qdrant vector search
- Mystical symbols: Custom detector

---

## 📚 Related Documentation

- **UnifiedQueryClassifier Implementation**: `src/memory/unified_query_classification.py` (562 lines)
- **SemanticKnowledgeRouter**: `src/knowledge/semantic_router.py` (lines 350-450)
- **spaCy Entity Extraction**: `src/knowledge/semantic_router.py` (enhanced entity mappings)
- **Testing Results**: `tests/test_routing_improvement.py`

---

**Last Updated:** October 25, 2025  
**Corrected:** Removed incorrect "LLM-powered" claims from previous documentation
