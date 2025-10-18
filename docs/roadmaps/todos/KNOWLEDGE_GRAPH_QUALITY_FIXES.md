# TODO: Knowledge Graph Quality Fixes

**Status**: 🔴 DEFERRED - Needs architectural re-design  
**Priority**: MEDIUM - Core functionality works, but quality/semantics need improvement  
**Created**: 2025-10-18  
**Investigation Session**: Session with MarkAnthony testing Elena bot

---

## 🔍 Problem Summary

The knowledge graph fact extraction system successfully stores facts to PostgreSQL and retrieves them in prompts, BUT the semantic quality is poor - facts are being split into disconnected entities instead of preserving relationships.

### Example Issue:
**User Message**: "I have a car that is green"

**Current Behavior** (BROKEN):
```
Other:
  The user none green
  The user owns car
```

**Expected Behavior**:
```
Other:
  The user owns green car
  OR
  The user owns car (color: green)
```

---

## ✅ What's Working

1. **Fact Extraction**: System successfully detects entities from user messages
   - Logs confirm: `✅ Stored fact: car (other)` and `✅ Stored fact: green (other)`
   
2. **Database Storage**: PostgreSQL tables correctly store entities
   - `fact_entities` table: Both "car" and "green" entities created
   - `user_fact_relationships` table: Relationships stored with correct user_id
   - Entities have proper timestamps, confidence scores (0.9), emotional context (joy)

3. **Prompt Injection**: Facts ARE appearing in character prompts
   - `📊 KNOWN FACTS ABOUT MarkAnthony` section includes stored facts
   - Semantic router successfully retrieves facts for context injection

---

## ❌ What's Broken

### Issue 1: Attribute-Entity Confusion
**Problem**: "green" should be an **attribute** of "car", not a separate entity  
**Current**: Two disconnected entities with no semantic link  
**Root Cause**: Entity extraction treats all nouns/adjectives as independent entities

**Database Evidence**:
```sql
-- entity_relationships table shows NO link between car and green
SELECT * FROM entity_relationships 
WHERE (from_entity = 'car' OR to_entity = 'car') 
  AND (from_entity = 'green' OR to_entity = 'green');
-- Result: 0 rows
```

### Issue 2: Nonsensical Relationship Formatting
**Problem**: `The user none green` is grammatically meaningless  
**Expected**: Should not display OR should format as "The user mentioned green"  
**Root Cause**: Relationship type "none" being rendered directly in prompt text

### Issue 3: Lost Semantic Context
**Problem**: "Green car" as a concept is lost - can't be recalled meaningfully  
**Impact**: Bot can't naturally reference "your green car" in conversation  
**Example**: Bot might say "I know you own a car" but can't say "your green car"

---

## 🔧 Required Fixes

### Priority 1: Semantic Relationship Parsing
**Location**: Likely in `src/knowledge/semantic_router.py` or fact extraction logic  
**Goal**: Recognize adjective-noun pairs and attribute relationships

**Strategies to investigate**:
1. Use dependency parsing (spaCy) to identify modifier relationships
2. Implement entity grouping for "adjective + noun" patterns
3. Store attributes in `fact_entities.attributes` JSONB field
4. Link entities via `entity_relationships` with "describes" or "has_attribute" type

### Priority 2: Relationship Type Handling
**Location**: Prompt building in `src/prompts/cdl_ai_integration.py`  
**Goal**: Better formatting or filtering of relationship types

**Options**:
1. Filter out "none" relationship types from display
2. Map relationship types to natural language templates
3. Store relationship as structured data, render intelligently

### Priority 3: Entity Clustering
**Location**: Knowledge graph storage and retrieval  
**Goal**: Group related entities into coherent facts

**Approach**:
1. Implement composite entity support (multi-word entities)
2. Use temporal proximity - facts from same message should link
3. Leverage `related_entities` JSONB field in `user_fact_relationships`

---

## 📊 Investigation Commands

### Check Database Schema
```bash
# See fact_entities structure
docker exec -it postgres psql -U whisperengine -d whisperengine -c "\d fact_entities"

# See user_fact_relationships structure
docker exec -it postgres psql -U whisperengine -d whisperengine -c "\d user_fact_relationships"

# See entity_relationships structure
docker exec -it postgres psql -U whisperengine -d whisperengine -c "\d entity_relationships"
```

### Query Current Facts
```sql
-- Get all facts for user with entity details
SELECT 
    ufr.id,
    fe.entity_name,
    ufr.relationship_type,
    ufr.confidence,
    ufr.emotional_context,
    ufr.created_at
FROM user_fact_relationships ufr
JOIN fact_entities fe ON ufr.entity_id = fe.id
WHERE ufr.user_id = 'USER_ID'
ORDER BY ufr.created_at DESC;

-- Check entity relationships
SELECT 
    fe_from.entity_name as from_entity,
    er.relationship_type,
    fe_to.entity_name as to_entity,
    er.weight
FROM entity_relationships er
JOIN fact_entities fe_from ON er.from_entity_id = fe_from.id
JOIN fact_entities fe_to ON er.to_entity_id = fe_to.id;
```

### Check Logs
```bash
# Watch fact extraction in action
docker logs elena-bot 2>&1 | grep -E "Stored fact|KNOWLEDGE" | tail -20

# Check prompt injection
ls -lt logs/prompts/elena_*.json | head -1
# Then grep for "KNOWN FACTS"
```

---

## 🚧 Why Deferred

1. **Architectural Scope**: This requires rethinking entity extraction logic, not quick fixes
2. **Hunting and Pecking**: Previous session involved too much trial-and-error without strategy
3. **Core Works**: Facts ARE being stored and retrieved - quality improvement can wait
4. **Other Priorities**: Hallucination fixes and LLM spam reduction were higher priority

---

## 📋 Next Steps When Resuming

1. **Map Current Code**: Find where entity extraction happens
   - Search for "Stored fact" log messages
   - Trace from message → fact extraction → database storage
   
2. **Review Extraction Logic**: Understand current parsing approach
   - Is it using spaCy NLP?
   - Is it using LLM extraction?
   - Where are entities split from relationships?

3. **Design Solution**: Before coding, document the approach
   - How should "green car" be represented in database?
   - What changes to schema (if any)?
   - How to preserve backward compatibility with existing facts?

4. **Test-Driven Development**: Create test cases FIRST
   - "I have a green car" → Expected database state
   - "My son Logan is 5 years old" → Expected entity relationships
   - "I love Thai food" → Expected fact format

5. **Implement Incrementally**: Small, testable changes
   - Phase 1: Fix attribute detection
   - Phase 2: Improve relationship formatting
   - Phase 3: Add entity clustering

---

## 📚 Related Files

- `src/knowledge/semantic_router.py` - Likely contains fact extraction
- `src/prompts/cdl_ai_integration.py` - Prompt building with facts
- Database tables: `fact_entities`, `user_fact_relationships`, `entity_relationships`
- Logs: `logs/prompts/*.json` - See how facts appear in prompts

---

## 💡 Success Criteria

When this TODO is complete, the following should work:

**Test Input**: "I have a green car"  
**Expected Database**:
```sql
fact_entities:
  - entity_name: "car"
  - attributes: {"color": "green"}
  
user_fact_relationships:
  - relationship_type: "owns"
  - entity: "car"
```

**Expected Prompt**:
```
Other:
  The user owns green car
  OR
  The user owns car (color: green)
```

**Expected Bot Behavior**:
- Bot can reference "your green car" in conversation
- Fact retrieval returns coherent semantic unit
- No nonsensical "The user none green" text

---

**Status Check**: Re-assess priority after hallucination fixes are stable and vector memory optimization is complete.
