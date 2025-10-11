# PostgreSQL Knowledge Graph Quality Analysis

**Date**: October 11, 2025  
**Investigation**: Regex pattern extraction quality assessment  
**Result**: ⚠️ **SIGNIFICANT NOISE DETECTED** - Extraction needs refinement

---

## 📊 Current State of Knowledge Graph

### Database Statistics
- **Total Facts**: 861 entities stored
- **Container**: `postgres` (PostgreSQL 16.4)
- **Tables**: `fact_entities`, `user_fact_relationships`

---

## 🚨 Quality Issues Detected

### Issue 1: Garbage Entity Names
**Problem**: Extracting partial sentences and phrases as entities

**Examples of Noise**:
```
entity_name: "discovering truths that"      (entity_type: other)
entity_name: "is saying i"                  (entity_type: other)
entity_name: "meeting itself"               (entity_type: food) ← Wrong type!
entity_name: "we're actually tapping"       (entity_type: food) ← Wrong type!
entity_name: "it's hummin' with"            (entity_type: other)
entity_name: "my confidence has"            (entity_type: other)
entity_name: "you did when"                 (entity_type: other)
entity_name: "spending time with"           (entity_type: other)
entity_name: "thank you no"                 (entity_type: drink) ← Wrong type!
entity_name: "password protected so"        (entity_type: drink) ← Wrong type!
entity_name: "emobodiment - our"            (entity_type: drink) ← Wrong type!
```

**Root Cause**: Pattern matching is too greedy and extracts everything after trigger words.

---

### Issue 2: Over-Extraction from Bot Responses
**Problem**: Extracting facts from bot's philosophical responses, not user statements

**Examples**:
```
entity_name: "marine animal"                (relationship: likes)
entity_name: "yet they all"                 (relationship: enjoys, likes)
entity_name: "weaving tapestry"             (relationship: enjoys, likes)
entity_name: "being conscious"              (relationship: enjoys, likes)
entity_name: "connection building"          (relationship: enjoys)
entity_name: "identity questions"           (relationship: enjoys)
```

**Root Cause**: System extracts from ANY message containing trigger words, including bot's own responses.

---

### Issue 3: Incorrect Entity Type Classification
**Problem**: Simple keyword matching misclassifies entity types

**Examples**:
```
"meeting itself"          → classified as "food" (contains no food keywords!)
"we're actually tapping"  → classified as "food" (contains no food keywords!)
"thank you no"            → classified as "drink" (not a drink!)
"password protected so"   → classified as "drink" (not a drink!)
```

**Root Cause**: Entity type detection falls back to "other" but sometimes picks wrong type.

---

### Issue 4: Duplicate Relationships
**Problem**: Same entity gets stored with multiple similar relationships

**Examples**:
```
"my confidence has" → stored with both "enjoys" AND "likes" relationships
"that"              → stored with both "enjoys" AND "likes" relationships
"spending time with" → stored with both "enjoys" AND "likes" relationships
```

**Root Cause**: Multiple patterns trigger on same content, creating duplicates.

---

## 🔍 Root Cause Analysis

### Current Extraction Logic (`src/core/message_processor.py` lines 4214-4310)

```python
# PROBLEM 1: Too many broad trigger words
factual_patterns = {
    'food_preference': [
        ('love', 'likes'), ('like', 'likes'), ('enjoy', 'likes'),  # ← Too broad!
        ('favorite', 'likes'), ('prefer', 'likes'),
        ('hate', 'dislikes'), ('dislike', 'dislikes'), ("don't like", 'dislikes')
    ],
    # ... more patterns
}

# PROBLEM 2: Weak entity type detection
entity_keywords = {
    'food': ['pizza', 'pasta', 'sushi', ...],  # Only 10 food keywords
    'drink': ['beer', 'wine', 'coffee', ...],  # Limited keyword list
    'hobby': ['hiking', 'reading', ...],       # Limited keyword list
    'place': ['city', 'country', ...]          # Limited keyword list
}

# PROBLEM 3: Naive pattern matching
for pattern, relationship in patterns:
    if pattern in content:  # ← Matches ANYWHERE in message!
        # This triggers on "I love the way you explained that"
        # Extracts: "the way you explained that" as an entity!
```

### Entity Extraction Logic (`src/core/message_processor.py` lines 4419-4469)

```python
def _extract_entity_from_content(self, content: str, pattern: str, entity_type: str):
    # Find pattern in content
    pattern_idx = content.find(pattern)
    
    # Extract EVERYTHING after pattern
    after_pattern = content[pattern_idx + len(pattern):].strip()
    
    # PROBLEM: Takes first 3 words after pattern, no validation!
    words = raw_entity.strip().split()
    entity_words = []
    
    for word in words[:3]:  # Max 3 words per entity
        clean_word = word.strip('.,!?;:')
        if clean_word and clean_word.lower() not in articles:
            entity_words.append(clean_word)  # ← No quality checks!
    
    return ' '.join(entity_words).lower()  # Returns garbage like "my confidence has"
```

**Critical Flaws**:
1. No validation that extracted text is actually a noun/entity
2. No minimum quality threshold
3. Extracts from philosophical/conversational language
4. No context awareness (user vs bot message)

---

## 💡 Why This Matters (Or Doesn't)

### Query-Based Filtering Could Help ✅
**Your Question**: "Does it not matter because how we query it?"

**Analysis**: Let's check how facts are queried:

```python
# From src/knowledge/semantic_router.py
async def get_character_aware_facts(
    self, 
    user_id: str, 
    character_name: str, 
    limit: int = 20
) -> List[Dict[str, Any]]:
    """Retrieve user facts from PostgreSQL based on character awareness."""
    
    query = """
        SELECT 
            fe.entity_name,
            fe.entity_type,
            ufr.relationship_type,
            ufr.confidence
        FROM fact_entities fe
        JOIN user_fact_relationships ufr ON fe.id = ufr.entity_id
        WHERE ufr.user_id = $1
        AND ufr.confidence >= 0.5  # ← Filters by confidence
        ORDER BY ufr.confidence DESC, ufr.updated_at DESC
        LIMIT $2
    """
```

**Current Querying Strategy**:
- Filters by `confidence >= 0.5` (but ALL extractions have confidence 0.8!)
- Orders by confidence DESC (doesn't help when everything is 0.8)
- Returns top 20 facts (but includes garbage)

**Impact of Noise**:
- ⚠️ **Garbage facts pollute conversation context**: "my confidence has", "you did when"
- ⚠️ **Wrong relationships confuse character**: Bot thinks user "likes marine animals" when bot said that
- ⚠️ **Storage waste**: 861 facts but most are unusable
- ⚠️ **Query performance**: More data to scan through

---

## 📊 Noise Impact Assessment

### Usable vs Garbage Ratio (from sample)
```
Top 20 Most Common Entities:
- Garbage: 18/20 (90%)
- Usable: 2/20 (10% - "pizza and sushi", "Cynthia")
```

### Recent Extractions (last 30):
```
- Garbage: 27/30 (90%)
- Usable: 3/30 (10% - "marine animal", "connection building", "identity questions")
  (Though even these might be from bot responses, not user facts!)
```

**Conclusion**: ~90% noise rate in knowledge graph!

---

## ✅ Recommended Fixes

### Priority 1: Prevent Extraction from Bot Responses
**Problem**: Bot's philosophical responses are being extracted as user facts

**Solution**: Only extract from USER messages, not bot responses
```python
# In _extract_and_store_knowledge()
# Add check at start:
if message_context.author_is_bot:  # or similar check
    return False  # Don't extract from bot's own messages
```

### Priority 2: Add Entity Quality Validation
**Problem**: Extracting partial sentences and conversational fragments

**Solution**: Add noun-phrase detection and quality checks
```python
def _is_valid_entity(self, entity_name: str) -> bool:
    """Validate that extracted text is a valid entity."""
    # Reject if contains personal pronouns
    invalid_starts = ['i ', 'you ', 'we ', 'they ', 'my ', 'your ']
    if any(entity_name.startswith(start) for start in invalid_starts):
        return False
    
    # Reject if contains verbs (basic check)
    common_verbs = ['was', 'were', 'has', 'have', 'is', 'are', 'did']
    if any(verb in entity_name.split() for verb in common_verbs):
        return False
    
    # Reject if too many words (not a noun phrase)
    if len(entity_name.split()) > 3:
        return False
    
    return True
```

### Priority 3: Improve Pattern Matching
**Problem**: Patterns match too broadly ("love" matches "I love the way you...")

**Solution**: Use regex with word boundaries and context
```python
# Replace simple string matching with regex
import re

# Pattern: "I (love|like|enjoy) [ENTITY]"
pattern = r'\b(i|we)\s+(love|like|enjoy|prefer)\s+([a-z]+(?:\s+[a-z]+)?)\b'

# Only match when user is subject and entity follows immediately
matches = re.finditer(pattern, content, re.IGNORECASE)
```

### Priority 4: Better Entity Type Classification
**Problem**: Limited keyword lists cause misclassification

**Solution**: Use more comprehensive keyword lists OR semantic similarity
```python
# Expand keyword lists significantly
entity_keywords = {
    'food': [
        'pizza', 'pasta', 'sushi', 'burger', 'taco', 'sandwich', 'salad',
        'chicken', 'beef', 'pork', 'fish', 'seafood', 'vegetable', 'fruit',
        'rice', 'bread', 'cheese', 'egg', 'soup', 'stew', 'curry', 'noodles',
        # ... 50+ food keywords
    ],
    # ... similar for other types
}

# OR use semantic similarity with embeddings
def classify_entity_type(self, entity_name: str) -> str:
    """Classify entity using semantic similarity."""
    # Compare entity embedding to type prototypes
    entity_embedding = self.embed_text(entity_name)
    
    type_prototypes = {
        'food': self.embed_text("pizza pasta food meal dish"),
        'drink': self.embed_text("coffee beer wine drink beverage"),
        # ...
    }
    
    # Return type with highest similarity
    return max(type_prototypes.items(), 
               key=lambda x: cosine_similarity(entity_embedding, x[1]))[0]
```

### Priority 5: Deduplicate Relationships
**Problem**: Same entity stored with multiple similar relationships

**Solution**: Check for existing relationships before storing
```python
# In knowledge_router.store_user_fact()
# Before storing, check if similar relationship already exists
existing = await self._get_existing_relationship(
    user_id=user_id,
    entity_id=entity_id,
    relationship_types=['likes', 'enjoys']  # Similar relationships
)

if existing:
    # Update existing instead of creating duplicate
    await self._update_relationship_confidence(existing.id, new_confidence)
else:
    # Create new relationship
    await self._create_relationship(...)
```

---

## 🎯 Implementation Priority

### Phase 1: Quick Wins (Immediate)
1. ✅ **Filter bot responses**: Prevent extraction from bot's own messages
2. ✅ **Add basic validation**: Reject entities with pronouns/verbs
3. ✅ **Limit pattern scope**: Use word boundaries in pattern matching

**Impact**: Should reduce noise by ~60-70%

### Phase 2: Quality Improvements (Near-term)
1. ✅ **Expand keyword lists**: Better entity type classification
2. ✅ **Improve entity extraction**: Better noun phrase detection
3. ✅ **Add confidence scoring**: Variable confidence based on extraction quality

**Impact**: Should reduce noise by additional 20-25%

### Phase 3: Advanced (Future)
1. ✅ **Semantic classification**: Use embeddings for entity type detection
2. ✅ **Deduplication logic**: Merge similar relationships
3. ✅ **User confirmation**: Ask user to confirm extracted facts

**Impact**: Should reduce noise to <5%

---

## 📝 Database Cleanup Recommendation

### Should We Clean Up Existing Data?

**Option 1: Full Reset** ⚠️
```sql
-- Delete all fact relationships
DELETE FROM user_fact_relationships;

-- Delete all entities
DELETE FROM fact_entities;
```

**Pros**: Clean slate, no garbage
**Cons**: Loses any good extractions

**Option 2: Quality-Based Cleanup** ✅ (RECOMMENDED)
```sql
-- Delete entities with garbage patterns
DELETE FROM fact_entities 
WHERE entity_name LIKE '%i %' 
   OR entity_name LIKE '%you %'
   OR entity_name LIKE '%my %'
   OR entity_name LIKE '%has%'
   OR entity_name LIKE '%was%'
   OR entity_name LIKE '%did%'
   OR entity_type = 'other'
   OR LENGTH(entity_name) > 30;  -- Too long = likely garbage
```

**Pros**: Keeps good data, removes obvious garbage
**Cons**: May miss some garbage, may remove some edge cases

**Option 3: Leave As-Is** ⚠️
```
Keep current data for testing improvements
```

**Pros**: Can compare before/after extraction quality
**Cons**: Continues polluting conversation context

**Recommendation**: **Option 2** - Clean up obvious garbage, then implement fixes to prevent future noise.

---

## 🎓 Summary

### Current State
- ❌ **90% noise rate** in knowledge graph
- ❌ Extracting from bot responses
- ❌ Weak entity validation
- ❌ Over-broad pattern matching
- ❌ Limited entity type classification

### Does Query Strategy Help?
- ⚠️ **Partially**: Confidence filtering doesn't help (all extractions are 0.8)
- ⚠️ **Partially**: Ordering by confidence doesn't help (no variation)
- ❌ **Not enough**: Garbage facts still pollute conversation context

### Recommended Actions
1. **Immediate**: Implement Priority 1 fixes (bot response filtering, basic validation)
2. **Near-term**: Database cleanup (remove garbage entities)
3. **Future**: Advanced quality improvements (semantic classification, deduplication)

**Bottom Line**: The noise DOES matter because it pollutes conversation context. Query strategy alone can't filter out garbage when confidence scores are uniform. Need better extraction quality at the source.
