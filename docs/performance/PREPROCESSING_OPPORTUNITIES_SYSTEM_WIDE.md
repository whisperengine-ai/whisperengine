# Preprocessing Pattern: System-Wide Opportunities

## 🎯 The Pattern We Discovered

**User Insight**: "Strip out common grammar first... that level of stripping handles a lot"

**Applied To**: `enhanced_query_processor.py` - Moved stop word removal to preprocessing stage

**Result**: 50% code reduction, eliminated 50+ word whitelist, simpler logic

## 🔍 System-Wide Scan Results

I found **7 major areas** where this preprocessing pattern could help:

---

## 📊 Opportunity #1: Duplicate Stop Word Definitions (HIGH PRIORITY)

### Problem: Same Stop Words Defined in 6+ Files

**Files with duplicate stop word sets**:
1. `src/utils/enhanced_query_processor.py` - 60+ words ✅ Already uses preprocessing
2. `src/memory/vector_memory_system.py` line 920 - 30+ words
3. `src/characters/learning/enhanced_memory_surprise_trigger.py` line 294 - 25+ words
4. `src/characters/learning/enhanced_memory_surprise_trigger.py` line 416 - 20+ words (different set!)
5. `src/utils/human_like_llm_processor.py` line 300+ - 30+ words
6. `src/memory/performance_optimizer.py` line 730+ - 20+ words

**Impact**: Maintenance nightmare - updating stop words requires changing 6+ files!

### Solution: Centralized Stop Words Module

```python
# NEW FILE: src/utils/stop_words.py
"""
Centralized stop word definitions for WhisperEngine.
Single source of truth for all text preprocessing.
"""

# Standard English stop words (grammar words that are never meaningful entities)
STOP_WORDS = {
    # Pronouns
    "i", "me", "my", "mine", "myself", "you", "your", "yours", 
    "he", "him", "his", "she", "her", "it", "its", "we", "us", 
    "our", "they", "them", "their",
    
    # Articles
    "a", "an", "the",
    
    # Prepositions
    "in", "on", "at", "to", "for", "of", "with", "by", "from", 
    "about", "into", "through", "during", "before", "after",
    
    # Conjunctions
    "and", "or", "but", "if", "then", "else",
    
    # Auxiliaries
    "is", "are", "was", "were", "be", "been", "being", 
    "have", "has", "had", "do", "does", "did",
    "will", "would", "could", "should", "may", "might",
    
    # Demonstratives
    "this", "that", "these", "those",
    
    # Question words
    "what", "when", "where", "how", "why", "which", "who",
    
    # Common fillers
    "very", "really", "just", "so", "too", "now", "then"
}

def clean_text(text: str, remove_stop_words: bool = True) -> str:
    """
    Centralized text cleaning function.
    
    Args:
        text: Raw text to clean
        remove_stop_words: Whether to remove stop words
        
    Returns:
        Cleaned text
    """
    # Lowercase and strip
    cleaned = text.lower().strip()
    
    # Remove punctuation except apostrophes
    import re
    cleaned = re.sub(r"[^\w\s\']", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    
    if remove_stop_words:
        words = cleaned.split()
        words = [w for w in words if w not in STOP_WORDS]
        cleaned = " ".join(words)
    
    return cleaned

def extract_content_words(text: str, min_length: int = 3) -> list[str]:
    """
    Extract content words (non-stop words) from text.
    
    Args:
        text: Input text
        min_length: Minimum word length to keep
        
    Returns:
        List of content words
    """
    cleaned = clean_text(text, remove_stop_words=True)
    words = cleaned.split()
    return [w for w in words if len(w) >= min_length]
```

**Then update all 6+ files to use centralized module**:
```python
from src.utils.stop_words import STOP_WORDS, clean_text, extract_content_words

# Instead of:
stop_words = {'the', 'a', 'an', ...}  # ❌ Duplicate definition
words = [w for w in text.split() if w not in stop_words]

# Use:
words = extract_content_words(text)  # ✅ Centralized preprocessing
```

**Benefits**:
- ✅ Single source of truth
- ✅ Consistent stop word handling across all systems
- ✅ One place to add/remove stop words
- ✅ Easier testing and validation
- ✅ ~200 lines of duplicate code eliminated

---

## 📊 Opportunity #2: Inline Keyword Matching (MEDIUM PRIORITY)

### Problem: Repetitive `sum(1 for word in words if word in keywords)` Pattern

**Found in 10+ files**:
- `src/prompts/hybrid_context_detector.py` - 4 occurrences (lines 324, 329, 334, 341)
- `src/prompts/cdl_ai_integration.py` - keyword matching (line 2112)
- `src/intelligence/hybrid_emotion_analyzer.py` - emotion keywords (line 301)
- `src/utils/human_like_llm_processor.py` - emotional/relationship scoring (lines 245, 276)
- And 5+ more files

**Current Pattern**:
```python
# Repeated in every file that needs keyword matching
personal_count = sum(1 for word in words if word in self.personal_pronouns)
temporal_count = sum(1 for word in words if word in self.temporal_indicators)
question_count = sum(1 for word in words if word in self.question_words)
```

### Solution: Preprocessing with Keyword Tagging

```python
# NEW: src/utils/text_analyzer.py
"""Preprocessing utilities for keyword-based analysis."""

from dataclasses import dataclass
from typing import Dict, List, Set
from src.utils.stop_words import clean_text

@dataclass
class TextAnalysis:
    """Preprocessed text with keyword matches already computed."""
    original: str
    cleaned: str
    words: List[str]
    keyword_matches: Dict[str, int]  # category -> count
    keyword_words: Dict[str, Set[str]]  # category -> matched words

def analyze_text(text: str, keyword_sets: Dict[str, Set[str]]) -> TextAnalysis:
    """
    Preprocess text and compute all keyword matches upfront.
    
    Args:
        text: Input text
        keyword_sets: Dictionary of {category_name: set_of_keywords}
        
    Returns:
        TextAnalysis with all keyword matches computed
        
    Example:
        keyword_sets = {
            'personal': {'i', 'me', 'my', 'mine'},
            'temporal': {'yesterday', 'today', 'tomorrow'},
            'question': {'what', 'when', 'where', 'why'}
        }
        analysis = analyze_text("What did I do yesterday?", keyword_sets)
        # analysis.keyword_matches = {'personal': 1, 'temporal': 1, 'question': 1}
    """
    cleaned = clean_text(text, remove_stop_words=False)  # Keep all words for matching
    words = cleaned.split()
    word_set = set(words)
    
    keyword_matches = {}
    keyword_words = {}
    
    for category, keywords in keyword_sets.items():
        matches = word_set & keywords  # Set intersection
        keyword_matches[category] = len(matches)
        keyword_words[category] = matches
    
    return TextAnalysis(
        original=text,
        cleaned=cleaned,
        words=words,
        keyword_matches=keyword_matches,
        keyword_words=keyword_words
    )
```

**Usage**:
```python
# Before: Repetitive inline matching
personal_count = sum(1 for word in words if word in self.personal_pronouns)
temporal_count = sum(1 for word in words if word in self.temporal_indicators)
question_count = sum(1 for word in words if word in self.question_words)

# After: One preprocessing call
keyword_sets = {
    'personal': self.personal_pronouns,
    'temporal': self.temporal_indicators,
    'question': self.question_words
}
analysis = analyze_text(message, keyword_sets)
personal_count = analysis.keyword_matches['personal']
temporal_count = analysis.keyword_matches['temporal']
question_count = analysis.keyword_matches['question']
```

**Benefits**:
- ✅ Single text scan instead of N scans (N = number of keyword sets)
- ✅ Cleaner, more declarative code
- ✅ Easier to add new keyword categories
- ✅ Testable preprocessing layer

---

## 📊 Opportunity #3: Message Lowercasing (LOW PRIORITY but COMMON)

### Problem: `.lower()` Called Multiple Times on Same Text

**Pattern appears 50+ times across codebase**:
```python
content_lower = content.lower()  # Called once
# ... 50 lines later ...
if 'feel' in memory_content.lower():  # Called again on same text
    # ...
elif 'learn' in memory_content.lower():  # Called yet again
```

**Files with this pattern**:
- `src/conversation/proactive_engagement_engine.py` - 10+ occurrences
- `src/intelligence/hybrid_emotion_analyzer.py` - 5+ occurrences
- `src/prompts/cdl_ai_integration.py` - 3+ occurrences

### Solution: Preprocessing Function or TextAnalysis Dataclass

**Option A: Simple preprocessing helper**:
```python
def preprocess_for_matching(text: str) -> tuple[str, str]:
    """
    Return both original and lowercase for common patterns.
    
    Returns:
        (original_text, lowercased_text)
    """
    return text, text.lower()

# Usage:
original, text_lower = preprocess_for_matching(message)
if 'feel' in text_lower:  # No redundant .lower() calls
    # ...
elif 'learn' in text_lower:
    # ...
```

**Option B: Use TextAnalysis from Opportunity #2**:
```python
analysis = analyze_text(message, keyword_sets)
# analysis.cleaned is already lowercased
if 'feel' in analysis.cleaned:
    # ...
```

**Benefits**:
- ✅ Avoid redundant `.lower()` calls
- ✅ Clearer separation: preprocessing vs. analysis
- ✅ Easier to optimize (e.g., caching)

---

## 📊 Opportunity #4: Query Optimization Duplication (MEDIUM PRIORITY)

### Problem: Multiple Query Optimization Functions Doing Same Thing

**Files with query optimization logic**:
1. `src/memory/qdrant_optimization.py` - `_optimize_query_text()` (line 206)
2. `src/prompts/optimized_prompt_builder.py` - stop word filtering (line 513)
3. `src/memory/performance_optimizer.py` - `_optimize_query_text()` (line 746)
4. `src/memory/vector_memory_system.py` - `_extract_keywords()` (line 920)

**All doing similar operations**:
```python
# Variation 1 (qdrant_optimization.py):
words = query.lower().split()
words = [w for w in words if w not in self.stop_words]

# Variation 2 (performance_optimizer.py):
words = query_text.lower().split()
optimized_words = [word for word in words if word not in stop_words and len(word) > 2]

# Variation 3 (vector_memory_system.py):
words = content.lower().split()
keywords = [word for word in words if len(word) > 2 and word not in stop_words]

# Variation 4 (optimized_prompt_builder.py):
meaningful_words = [word for word in words if len(word) > 3 and word not in self._get_stop_words()]
```

### Solution: Unified Query Preprocessing

```python
# In src/utils/stop_words.py
def optimize_query(query: str, 
                  remove_stop_words: bool = True,
                  min_word_length: int = 3,
                  max_words: int = None) -> str:
    """
    Optimize query text for semantic search.
    
    Args:
        query: Raw query text
        remove_stop_words: Whether to remove stop words
        min_word_length: Minimum word length to keep
        max_words: Optional limit on number of words
        
    Returns:
        Optimized query string
    """
    cleaned = clean_text(query, remove_stop_words=remove_stop_words)
    words = cleaned.split()
    words = [w for w in words if len(w) >= min_word_length]
    
    if max_words:
        words = words[:max_words]
    
    return " ".join(words)

# Usage across all 4 files:
optimized = optimize_query(query, min_word_length=3)  # Consistent behavior
```

**Benefits**:
- ✅ Consistent query optimization across all memory systems
- ✅ Eliminates duplicate logic
- ✅ Single place to improve query preprocessing
- ✅ Easier A/B testing of optimization strategies

---

## 📊 Opportunity #5: enhanced_memory_surprise_trigger.py (HIGH PRIORITY)

### Problem: Two Different Stop Word Sets in Same File!

**File**: `src/characters/learning/enhanced_memory_surprise_trigger.py`

**Line 294**: One stop word set (25 words)
**Line 416**: Different stop word set (20 words)

**Why is this bad?**:
- Different parts of the same file filter text differently
- Inconsistent behavior in same feature
- No clear reason why they differ

### Solution: Use Centralized Stop Words

```python
# Replace both with:
from src.utils.stop_words import extract_content_words

# Line 294 area:
content_words = extract_content_words(text)  # Uses centralized STOP_WORDS

# Line 416 area:
content_words = extract_content_words(text)  # Same centralized STOP_WORDS
```

**Benefits**:
- ✅ Consistent behavior within same feature
- ✅ Eliminates confusing inconsistency
- ✅ Easier to maintain

---

## 📊 Opportunity #6: Conditional Chains (MEDIUM PRIORITY)

### Problem: Long Chains of `if keyword in text.lower()` Checks

**Example from `src/conversation/proactive_engagement_engine.py` (lines 1120-1125)**:
```python
if 'feel' in memory_content.lower() or 'emotion' in memory_content.lower():
    context_type = 'emotional'
elif 'learn' in memory_content.lower() or 'understand' in memory_content.lower():
    context_type = 'learning'
elif 'remember' in memory_content.lower() or 'recall' in memory_content.lower():
    context_type = 'memory'
# ... more chains
```

### Solution: Preprocessing with Keyword Categorization

```python
# Preprocessing:
keyword_categories = {
    'emotional': {'feel', 'emotion', 'happy', 'sad'},
    'learning': {'learn', 'understand', 'teach', 'study'},
    'memory': {'remember', 'recall', 'forgot', 'memory'}
}
analysis = analyze_text(memory_content, keyword_categories)

# Analysis (much cleaner):
if analysis.keyword_matches['emotional'] > 0:
    context_type = 'emotional'
elif analysis.keyword_matches['learning'] > 0:
    context_type = 'learning'
elif analysis.keyword_matches['memory'] > 0:
    context_type = 'memory'
```

**Or even simpler**:
```python
# Get dominant category
context_type = max(analysis.keyword_matches, key=analysis.keyword_matches.get)
```

**Benefits**:
- ✅ No redundant `.lower()` calls
- ✅ Cleaner, more declarative code
- ✅ Easier to add new categories
- ✅ Single text scan vs. N scans

---

## 📊 Opportunity #7: _get_stop_words() Method Calls (LOW PRIORITY)

### Problem: Stop Words as Method Instead of Constant

**Files calling `_get_stop_words()` method**:
- `src/prompts/optimized_prompt_builder.py` (line 513, 2945, 2960)
- `src/memory/vector_memory_system.py` (line 2945, 2960)

**Current pattern**:
```python
meaningful_words = [word for word in words 
                   if len(word) > 3 and word not in self._get_stop_words()]
```

**Problem**: Method call overhead in list comprehension (called for every word!)

### Solution: Store as Class Attribute

```python
# In __init__:
from src.utils.stop_words import STOP_WORDS
self.stop_words = STOP_WORDS  # Reference, not copy

# In code:
meaningful_words = [word for word in words 
                   if len(word) > 3 and word not in self.stop_words]
```

**Benefits**:
- ✅ No method call overhead
- ✅ Faster execution (especially in tight loops)
- ✅ Uses centralized stop words
- ✅ Simple refactor

---

## 🎯 Implementation Priority

### Phase 1: High ROI, Low Risk ✅
1. **Create centralized stop words module** (`src/utils/stop_words.py`)
   - Single source of truth
   - Eliminates 6+ duplicate definitions
   - Foundation for other improvements

2. **Fix enhanced_memory_surprise_trigger.py**
   - Fixes inconsistency within same file
   - Uses new centralized module

### Phase 2: High ROI, Medium Effort 🟡
3. **Create TextAnalysis preprocessing utility** (`src/utils/text_analyzer.py`)
   - Eliminates keyword matching duplication
   - Single text scan vs. N scans
   - Used by 10+ files

4. **Unify query optimization**
   - Consolidate 4 different implementations
   - Consistent behavior across memory systems

### Phase 3: Polish, Low Priority 🔵
5. **Replace _get_stop_words() method calls with constants**
6. **Clean up redundant .lower() calls**
7. **Refactor conditional keyword chains**

---

## 📊 Expected Impact

### Code Reduction:
- **~300-400 lines** of duplicate stop word definitions eliminated
- **~100-150 lines** of keyword matching logic simplified
- **~50+ redundant** `.lower()` calls removed

### Performance Improvement:
- **70-80% reduction** in text preprocessing operations
- **Single scan** vs. multiple scans for keyword matching
- **Method call overhead** eliminated in tight loops

### Maintainability:
- **Single source of truth** for stop words (currently 6+ definitions)
- **Consistent behavior** across all text processing
- **Easier to test** preprocessing logic in isolation
- **Simpler to add** new keyword categories or stop words

---

## 🎓 The Pattern

**User's Insight Applied System-Wide**:
> "Strip out common grammar first... that level of stripping handles a lot"

**Architectural Principle**:
- **Preprocess structural transformations** (stop word removal, lowercasing)
- **Simplify downstream logic** (keyword matching, entity extraction)
- **Centralize common operations** (no duplicate definitions)
- **Single scan, multiple uses** (analyze once, use many times)

This is the same pattern that simplified `enhanced_query_processor.py` by 50%, now applied to 7+ areas across the codebase for system-wide improvement!
