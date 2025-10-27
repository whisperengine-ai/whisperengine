# TODO: Knowledge Graph Quality Fixes

**Status**: 🔴 DEFERRED - Needs architectural re-design  
**Priority**: MEDIUM - Core functionality works, but quality/semantics need improvement  
**Created**: 2025-10-18  
**Last Updated**: 2025-10-26  
**Investigation Session**: Session with MarkAnthony testing Elena bot

---

## 📅 Update October 26, 2025

**Related improvements made but core issue remains unresolved:**

### ✅ Related Enhancements (Oct 18-25):

**Key Commits:**
- `64f6210` (Oct 25) - Phase 2-E NLP enhancements + critical bug fixes
- `9b4fa71` (Oct 24) - Enhance Dockerfile and requirements for spaCy integration
- `7bbab38` (Oct 23) - Add spaCy integration for NLP preprocessing

1. **Phase 2-E NLP Enhancements** (commit 64f6210, Oct 25):
   - ✅ Negation-aware SVO extraction (detects "don't like" vs "like")
   - ✅ Custom matcher patterns for preferences (NEGATED, STRONG, TEMPORAL, HEDGING, CONDITIONAL)
   - ✅ Better dependency parsing with negation markers
   - ❌ **BUT**: No adjective-noun/attribute extraction implemented

2. **spaCy Integration** (commits 7bbab38, 9b4fa71):
   - ✅ Shared spaCy instance for entity extraction (`src/nlp/spacy_manager.py`)
   - ✅ Dependency parsing infrastructure (`src/enrichment/nlp_preprocessor.py`)
   - ✅ Entity extraction with label mapping
   - ❌ **BUT**: Not using `amod` (adjectival modifier) or `compound` dependencies for attributes

3. **Fact Extraction Bug Fixes** (commit 64f6210):
   - ✅ Fixed zero results bug (better LLM prompts with positive examples)
   - ✅ Fixed shared timestamp marker bug (separate fact vs preference markers)
   - ✅ Improved confidence scoring
   - ❌ **BUT**: Didn't address semantic quality of entity splitting

### ❌ Core Issues Still Present:
- **Attribute-Entity Confusion**: "green car" still creates 2 disconnected entities
- **Nonsensical Relationships**: "The user none green" formatting still possible
- **Lost Semantic Context**: Bot can't naturally reference "your green car" as a coherent concept
- **No Composite Entities**: Multi-word entities not preserved (e.g., "green car" as single unit)

### 🔧 What Would Be Needed:
1. **Adjective-Noun Parsing**: Use spaCy's `amod` dependency to detect modifiers
2. **Attribute Storage**: Populate `fact_entities.attributes` JSONB field (e.g., `{"color": "green"}`)
3. **Entity Grouping**: Cluster related entities from same message via `related_entities` field
4. **Relationship Type Mapping**: Better formatting or filtering of "none" relationship types

**Conclusion**: The dependency parsing and spaCy infrastructure is now in place, but the specific logic for attribute extraction and composite entities has not been implemented. The TODO remains valid and DEFERRED.

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
5. **Infrastructure Ready**: spaCy integration (Oct 2025) provides the foundation, but implementing attribute extraction requires careful design to avoid breaking existing fact storage
6. **Low User Impact**: While semantically imperfect, current system successfully stores and retrieves facts - users haven't reported this as a blocking issue

---

## 📋 Next Steps When Resuming

### Infrastructure Now Available (as of Oct 2025):
- ✅ **spaCy Integration**: `src/nlp/spacy_manager.py` - Shared spaCy instance
- ✅ **Dependency Parsing**: `src/enrichment/nlp_preprocessor.py` - SVO extraction with negation
- ✅ **Entity Extraction**: `extract_entities()` method with label mapping
- ✅ **Database Schema**: `fact_entities.attributes` JSONB field ready for use
- ✅ **Relationship Storage**: `entity_relationships` table exists but unused

### Implementation Steps:

1. **Map Current Code**: Find where entity extraction happens
   - ✅ **Found**: `src/knowledge/semantic_router.py` - Main fact storage
   - ✅ **Found**: `src/enrichment/fact_extraction_engine.py` - LLM-based extraction
   - ✅ **Found**: `src/enrichment/nlp_preprocessor.py` - spaCy preprocessing
   - Search for "Stored fact" log messages to trace flow
   
2. **Review Extraction Logic**: Understand current parsing approach
   - ✅ **Confirmed**: Uses spaCy NLP for entity extraction
   - ✅ **Confirmed**: Uses LLM for relationship extraction
   - **TODO**: Where are entities split from relationships? (needs investigation)

3. **Design Solution**: Before coding, document the approach
   - **Key Decision**: How should "green car" be represented in database?
     - Option A: Single entity "car" with `attributes: {"color": "green"}`
     - Option B: Two entities with relationship "car" -[has_attribute]-> "green"
     - Option C: Composite entity "green car" as single entity_name
   - What changes to schema (if any)?
   - How to preserve backward compatibility with existing facts?

4. **Leverage spaCy Dependency Tags**: Use existing infrastructure
   - **TODO**: Extract `amod` dependencies (adjectival modifiers): "green" -> "car"
   - **TODO**: Extract `compound` dependencies: "ice" -> "cream" = "ice cream"
   - **TODO**: Extract `nmod` dependencies (noun modifiers): "cup" -> "coffee"
   - **Implementation Location**: Add to `nlp_preprocessor.py` or create new method

5. **Test-Driven Development**: Create test cases FIRST
   - "I have a green car" → Expected database state
   - "My son Logan is 5 years old" → Expected entity relationships
   - "I love Thai food" → Expected fact format
   - "I drive a red Tesla Model 3" → Complex multi-attribute entity

6. **Implement Incrementally**: Small, testable changes
   - Phase 1: Add attribute extraction to `nlp_preprocessor.py`
   - Phase 2: Update fact storage to populate `attributes` field
   - Phase 3: Improve prompt rendering to use attributes naturally
   - Phase 4: Add entity clustering for related entities

---

## 📚 Related Files

### Core Fact Storage:
- `src/knowledge/semantic_router.py` - Main fact storage and retrieval (1,753 lines)
  - `store_user_fact()` method - Stores entities to `fact_entities` table
  - `retrieve_user_facts()` method - Retrieves facts for prompt injection
  - Uses spaCy for entity type extraction

### Enrichment Pipeline:
- `src/enrichment/fact_extraction_engine.py` - LLM-based fact extraction
  - `extract_facts_from_conversation()` - Batch fact extraction
  - `build_knowledge_graph_relationships()` - Relationship building (unused)
  
### NLP Infrastructure (Added Oct 2025):
- `src/enrichment/nlp_preprocessor.py` - spaCy preprocessing (422 lines)
  - `extract_entities()` - Entity extraction with NER
  - `extract_dependency_relationships()` - SVO extraction with negation
  - `extract_preference_patterns()` - Custom matcher patterns
  - **TODO**: Add adjective-noun attribute extraction here

- `src/nlp/spacy_manager.py` - Shared spaCy instance manager
  - Singleton pattern for memory efficiency
  - Graceful fallback if model unavailable

### Prompt Building:
- `src/prompts/cdl_ai_integration.py` - Prompt building with facts
  - Injects stored facts into character prompts
  - **TODO**: Format relationships better (avoid "The user none green")

### Database Tables:
- `fact_entities` - Entity storage with JSONB `attributes` field
- `user_fact_relationships` - User-entity relationships
- `entity_relationships` - Entity-to-entity relationships (largely unused)

### Logs:
- `logs/prompts/*.json` - See how facts appear in prompts

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
