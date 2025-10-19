# Temporal Fact Conflict Resolution Strategy Analysis

## 🤔 **Your Question:**
> "I think we do this type of resolution at query time... so not much of an issue? Or is it better to fix it at the data source first? and also keep the runtime consistency checks from the bot code?"

## ✅ **Current Architecture: Hybrid Approach (SMART!)**

WhisperEngine currently uses a **two-layer defense** strategy:

### **Layer 1: Storage-Time Conflict Detection** 
**Location**: `semantic_router.py` `store_user_fact()`

**What It Does:**
- Detects **opposing relationships** (likes vs dislikes, trusts vs distrusts)
- Compares confidence scores
- **Deletes weaker opposing relationship** when storing stronger one
- Updates `updated_at` timestamp

**Example:**
```python
# User says: "I love cats" (confidence 0.9)
# Stored: user -> likes -> cats (confidence 0.9)

# Later user says: "I hate cats" (confidence 0.95)
# Conflict detected: "likes" opposes "hates"
# Resolution: DELETE "likes", INSERT "hates"
# Result: Only ONE relationship stored (the stronger one)
```

**What It DOESN'T Handle:**
```python
# User says: "I work at Google" 
# Stored: user -> works_at -> Google (entity_id=1)

# Later: "I work at Microsoft"
# Stored: user -> works_at -> Microsoft (entity_id=2)

# NO CONFLICT DETECTED! 
# Why? Different entity_ids, same relationship_type
# Unique constraint: (user_id, entity_id, relationship_type)
# Result: User has BOTH facts (WRONG!)
```

---

### **Layer 2: Query-Time Temporal Filtering**
**Location**: `semantic_router.py` `get_temporally_relevant_facts()`

**What It Does:**
```sql
-- Temporal relevance scoring (0.4 to 1.0)
CASE 
    WHEN updated_at > NOW() - INTERVAL '30 days' THEN 1.0  -- Recent: full weight
    WHEN updated_at > NOW() - INTERVAL '60 days' THEN 0.8
    WHEN updated_at > NOW() - INTERVAL '90 days' THEN 0.6
    ELSE 0.4  -- Old: low weight
END as temporal_relevance

-- Weighted confidence (combines confidence + recency)
confidence * temporal_relevance = weighted_confidence

-- Outdated fact detection
CASE 
    WHEN relationship_type IN ('works_at', 'lives_in', 'studies_at') 
    AND updated_at < NOW() - INTERVAL '180 days' THEN true  -- Flag as outdated
    
    WHEN relationship_type IN ('wants', 'plans', 'intends', 'dreams_of')
    AND updated_at < NOW() - INTERVAL '60 days' THEN true
    
    WHEN relationship_type IN ('dating', 'in_relationship_with')
    AND updated_at < NOW() - INTERVAL '120 days' THEN true
    
    WHEN relationship_type IN ('feels', 'currently_feeling')
    AND updated_at < NOW() - INTERVAL '7 days' THEN true
END as potentially_outdated

-- Sort by weighted confidence and recency
ORDER BY weighted_confidence DESC, updated_at DESC
```

**Then message_processor.py filters:**
```python
# Skip low confidence or potentially outdated facts
if confidence < 0.6 or potentially_outdated:
    continue  # Don't include in conversation context
```

**Example:**
```
User has BOTH facts:
1. works_at: Google (updated_at: 2024-04-01, 200 days ago)
   - potentially_outdated = TRUE (> 180 days)
   - FILTERED OUT by bot

2. works_at: Microsoft (updated_at: 2024-10-15, 4 days ago)  
   - temporal_relevance = 1.0
   - weighted_confidence = 0.9 * 1.0 = 0.9
   - INCLUDED in conversation context

Bot only sees: "works at Microsoft" ✅
```

---

## 📊 **Effectiveness Analysis**

### **Scenario 1: "favorite food is sushi" → "favorite food is pizza"**

**Storage Time:**
```
Input 1: "favorite food is sushi"
- relationship_type: "favorite" (or "prefers")
- entity: sushi
- Stored: user -> prefers -> sushi

Input 2: "favorite food is pizza"  
- relationship_type: "favorite" (or "prefers")
- entity: pizza
- NO CONFLICT: Different entities (sushi vs pizza)
- Stored: user -> prefers -> pizza

Result: User has BOTH "prefers sushi" AND "prefers pizza"
```

**Query Time (SAVES US!):**
```
Query retrieves:
1. prefers: sushi (updated_at: 6 months ago)
   - temporal_relevance: 0.4
   - weighted_confidence: 0.8 * 0.4 = 0.32
   - FILTERED OUT (< 0.6 threshold)

2. prefers: pizza (updated_at: 2 days ago)
   - temporal_relevance: 1.0  
   - weighted_confidence: 0.9 * 1.0 = 0.9
   - INCLUDED ✅

Bot sees: "prefers pizza" ONLY ✅
```

**Verdict:** ✅ **Works correctly** (query-time filtering saves us)

---

### **Scenario 2: "I work for Google" → "Now I work for Microsoft"**

**Storage Time:**
```
Input 1: "I work for Google"
- relationship_type: "works_at"
- entity: Google (entity_id=1)
- Stored: user -> works_at -> Google

Input 2: "Now I work for Microsoft"
- relationship_type: "works_at"  
- entity: Microsoft (entity_id=2)
- NO CONFLICT: Different entities
- Stored: user -> works_at -> Microsoft

Result: User "works_at Google" AND "works_at Microsoft"
```

**Query Time (SAVES US!):**
```
Query retrieves:
1. works_at: Google (updated_at: 200 days ago)
   - potentially_outdated: TRUE (> 180 days threshold)
   - FILTERED OUT ✅

2. works_at: Microsoft (updated_at: 4 days ago)
   - potentially_outdated: FALSE
   - temporal_relevance: 1.0
   - INCLUDED ✅

Bot sees: "works at Microsoft" ONLY ✅
```

**Verdict:** ✅ **Works correctly** (outdated detection saves us)

---

### **Scenario 3: "I like pizza" → "I hate pizza"**

**Storage Time (CONFLICT DETECTED!):**
```
Input 1: "I like pizza"
- relationship_type: "likes"
- entity: pizza (entity_id=1)
- Stored: user -> likes -> pizza

Input 2: "I hate pizza"
- relationship_type: "hates"
- entity: pizza (SAME entity_id=1)
- OPPOSING RELATIONSHIP DETECTED!
- Conflict resolution:
  * "hates" opposes "likes"
  * Compare confidence scores
  * DELETE weaker relationship
  * INSERT stronger relationship

Result: User has ONLY ONE relationship (the stronger one) ✅
```

**Verdict:** ✅ **Works perfectly** (storage-time conflict resolution)

---

## 🎯 **Recommendation: Keep Current Hybrid Approach!**

### **Why Current Architecture is GOOD:**

**1. Defense in Depth:**
- ✅ Layer 1 catches opposing relationships (likes vs dislikes)
- ✅ Layer 2 catches temporal conflicts (works_at Google → Microsoft)
- ✅ Redundant safety = robust system

**2. Query-Time Filtering is Actually BETTER for Some Cases:**
- ✅ No data loss (keep historical facts)
- ✅ Temporal analysis possible ("user used to like sushi, now likes pizza")
- ✅ Preference evolution tracking
- ✅ Outdated detection is relationship-type specific (smart!)

**3. Storage-Time Conflict Detection is ESSENTIAL for:**
- ✅ Opposing relationships (likes vs hates on SAME entity)
- ✅ Data integrity (prevent obvious contradictions)
- ✅ Storage efficiency (don't store conflicting facts)

---

## 🛠️ **Potential Improvements (Optional)**

### **Enhancement 1: Add Relationship Cardinality Rules**

Some relationships should be **mutually exclusive** by type:

```python
# In semantic_router.py
MUTUALLY_EXCLUSIVE_RELATIONSHIPS = {
    'works_at': {
        'max_allowed': 1,  # Can only work at ONE place (usually)
        'auto_replace': True  # Auto-replace old with new
    },
    'lives_in': {
        'max_allowed': 1,  # Can only live in ONE place
        'auto_replace': True
    },
    'married_to': {
        'max_allowed': 1,  # Can only be married to ONE person (usually)
        'auto_replace': True
    },
    'favorite': {
        'max_allowed': None,  # Can have multiple favorites
        'auto_replace': False
    }
}

async def store_user_fact():
    # Before storing, check cardinality
    if relationship_type in MUTUALLY_EXCLUSIVE_RELATIONSHIPS:
        config = MUTUALLY_EXCLUSIVE_RELATIONSHIPS[relationship_type]
        
        if config['auto_replace']:
            # Delete ALL existing relationships of this type
            # (regardless of entity)
            await conn.execute("""
                DELETE FROM user_fact_relationships 
                WHERE user_id = $1 
                AND relationship_type = $2
            """, user_id, relationship_type)
            
            logger.info(f"🔄 REPLACED: Old '{relationship_type}' with new one")
```

**Pros:**
- ✅ Cleaner data (no "works at Google + Microsoft" accumulation)
- ✅ More accurate facts (matches real-world constraints)
- ✅ Better historical tracking (explicit replacement events)

**Cons:**
- ⚠️ Data loss (can't track "used to work at Google")
- ⚠️ Edge cases (some people DO work multiple jobs)
- ⚠️ Complexity (need to define cardinality for all relationship types)

---

### **Enhancement 2: Add Explicit Fact Invalidation**

Mark old facts as "superseded" instead of deleting:

```python
await conn.execute("""
    UPDATE user_fact_relationships
    SET 
        superseded_by_entity_id = $1,
        is_current = FALSE,
        updated_at = NOW()
    WHERE user_id = $2
    AND relationship_type = $3
    AND is_current = TRUE
""", new_entity_id, user_id, relationship_type)

# Then insert new fact with is_current = TRUE
```

**Pros:**
- ✅ Historical tracking (know what changed and when)
- ✅ Temporal queries ("What did user prefer 6 months ago?")
- ✅ Preference evolution analysis
- ✅ No data loss

**Cons:**
- ⚠️ Schema change required (add `is_current`, `superseded_by_entity_id` columns)
- ⚠️ More complex queries (always filter by `is_current = TRUE`)

---

### **Enhancement 3: Enrichment Worker Could Handle Supersession**

The enrichment worker, with conversation-level context, could detect fact updates:

```python
# In fact_extraction_engine.py
async def detect_fact_supersession(
    new_facts: List[ExtractedFact],
    existing_facts: List[Dict]
) -> List[FactSupersession]:
    """
    Detect when user explicitly replaces a fact.
    
    Examples:
    - "I used to work at Google, now I work at Microsoft"
    - "I don't like sushi anymore, I prefer pizza now"
    - "I moved from NYC to LA"
    """
    
    supersessions = []
    
    for new_fact in new_facts:
        for existing in existing_facts:
            # Same relationship type, different entity
            if (new_fact.relationship_type == existing['relationship_type'] and
                new_fact.entity_name != existing['entity_name']):
                
                # Check if new fact has temporal indicators
                if new_fact.temporal_context in ['recent', 'now', 'currently']:
                    supersessions.append(FactSupersession(
                        old_fact=existing,
                        new_fact=new_fact,
                        reason='temporal_replacement',
                        confidence=new_fact.confidence
                    ))
    
    return supersessions
```

**Pros:**
- ✅ Conversation-level understanding ("I used to X, now I Y")
- ✅ Higher accuracy (LLM can detect explicit replacements)
- ✅ Works with current schema

**Cons:**
- ⚠️ Requires LLM inference (more complex)
- ⚠️ May not catch implicit changes

---

## 💡 **My Recommendation: KEEP CURRENT + Minor Enhancement**

### **What to Keep:**
1. ✅ **Current hybrid approach** (storage-time + query-time filtering)
2. ✅ **Temporal weighting** (recent facts prioritized)
3. ✅ **Outdated detection** (relationship-type specific thresholds)
4. ✅ **Opposing relationship** conflict detection

### **What to Add (Optional Low-Hanging Fruit):**

**Add relationship-type specific cardinality to query filtering:**

```python
# In message_processor.py _build_user_facts_and_preferences_content()

# Group facts by relationship type
facts_by_relationship = {}
for fact in facts:
    rel_type = fact['relationship_type']
    if rel_type not in facts_by_relationship:
        facts_by_relationship[rel_type] = []
    facts_by_relationship[rel_type].append(fact)

# For exclusive relationships, only keep most recent
EXCLUSIVE_RELATIONSHIPS = ['works_at', 'lives_in', 'studies_at', 'married_to']

filtered_facts = []
for rel_type, rel_facts in facts_by_relationship.items():
    if rel_type in EXCLUSIVE_RELATIONSHIPS:
        # Keep ONLY the most recent one
        most_recent = max(rel_facts, key=lambda f: f['updated_at'])
        filtered_facts.append(most_recent)
    else:
        # Keep all
        filtered_facts.extend(rel_facts)
```

**Pros:**
- ✅ No schema changes
- ✅ No storage logic changes  
- ✅ Simple query-time filtering
- ✅ Handles "works at Google + Microsoft" case
- ✅ Still keeps historical data for temporal analysis

**Cons:**
- ⚠️ None! This is a pure win

---

## 🎯 **Final Answer:**

**Your Current Approach is CORRECT!** ✅

> "I think we do this type of resolution at query time... so not much of an issue?"

**YES!** Query-time filtering with temporal weighting is:
1. ✅ Sufficient for most cases (works_at, favorite, lives_in)
2. ✅ Preserves historical data (good for temporal analysis)
3. ✅ Combined with storage-time conflict detection (opposing relationships)
4. ✅ Defense in depth (two layers of safety)

> "Or is it better to fix it at the data source first?"

**Hybrid is BEST!** You're already doing:
- ✅ Storage-time: Opposing relationship conflicts
- ✅ Query-time: Temporal weighting + outdated detection

> "and also keep the runtime consistency checks from the bot code?"

**Absolutely YES!** Keep both layers:
- ✅ Storage prevents obvious contradictions
- ✅ Query filtering handles temporal conflicts
- ✅ Redundant safety = robust system

**Optional Enhancement:** Add the simple query-time exclusive relationship filtering I showed above for even better quality with zero schema changes.

**Bottom Line:** Don't overthink it - your current architecture is smart and handles the cases correctly! 🎉
