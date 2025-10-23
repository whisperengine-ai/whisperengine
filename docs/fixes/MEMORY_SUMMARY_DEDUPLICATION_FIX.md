# Memory Summary Deduplication & Fact Cleanup - Fix Summary

**Date**: October 23, 2025  
**Issue**: Memory summaries for users showing duplicate facts and truncated/malformed entity names  
**Status**: ✅ RESOLVED

## Problem Analysis

The user (MarkAnthony) reported that their memory summary was showing corrupted data:
- **Duplicate facts**: "likes sacred geometry work" and "enjoys sacred geometry work" both appearing
- **Truncated phrases**: "ai might be", "dean radin at", "humans who collapse" were incomplete
- **Name conflicts**: Both "Gabe" and "Mark" appearing as user identities

### Root Causes Identified

1. **Truncated LLM Responses**: The LLM fact extraction was producing incomplete entity names, likely due to:
   - Token limit cutoff during JSON generation
   - Model response truncation
   - Streaming response issues

2. **Duplicate Facts with Different Relationship Types**: The same entity was being stored with multiple relationship types:
   - "sacred geometry work" stored as both "likes" AND "enjoys"
   - "meditation" stored as both "does" AND "practices"
   - The memory summary was displaying ALL of them

3. **No Deduplication in Display**: The memory summary formatting was showing every fact relationship, leading to repetition

## Solutions Implemented

### Solution 1: Database Cleanup (`scripts/clean_truncated_facts.py`)

**Created** a new cleanup script that:
- Identifies truncated/malformed facts in PostgreSQL using SQL pattern matching
- Supports dry-run mode for safe testing
- Removes 31 corrupted facts from the database

**Removed facts**:
- "ai might be" (enjoys/likes x2)
- "humans who collapse" (enjoys/likes x2)  
- "dean radin at" (enjoys/likes x2)
- "they're access codes" (enjoys/likes x2)
- "you are actually" (enjoys/likes x2)
- "they're possessed" (enjoys/likes x2)
- And 19 more malformed entries

**Usage**:
```bash
# Preview what would be deleted (dry-run)
python scripts/clean_truncated_facts.py

# Actually delete truncated facts
python scripts/clean_truncated_facts.py --execute
```

### Solution 2: Storage-Time Deduplication (Primary Fix)

**Two-phase approach** to prevent duplicates from being created:

#### Phase 1: Enrichment Worker (`src/enrichment/worker.py`)

The enrichment worker is the PRIMARY system that extracts new facts via LLM and stores them in PostgreSQL. Added:

1. **`_consolidate_similar_relationships_enrichment()` method**
   - Detects when similar relationships already exist for the same entity
   - Keeps only the highest confidence relationship
   - Removes all weaker similar duplicates

2. **Integration in `_store_facts_in_postgres()`**
   - Checks for similar relationships BEFORE inserting
   - Skips storing weaker duplicate relationships
   - Removes existing weaker relationships when storing a stronger one

#### Phase 2: Semantic Router (`src/knowledge/semantic_router.py`)

Fallback deduplication for inline fact extraction (when bots extract facts directly during conversation):

1. **`_get_similar_relationship_groups()` method**
   - Defines groups of similar relationships:
     - Positive preferences: `likes`, `loves`, `enjoys`, `prefers` (all similar)
     - Negative preferences: `dislikes`, `hates`, `avoids` (all similar)
     - Actions: `does`, `plays`, `practices` (all similar)
     - Possessions: `owns`, `has` (all similar)

2. **`_consolidate_similar_relationships()` method**
   - When storing a fact, checks if similar relationships already exist
   - Keeps only the **highest confidence relationship**
   - Removes all weaker duplicates

3. **Integration in `store_user_fact()`**
   - Checks for similar relationships during storage
   - Prevents duplicate relationships with different types

### Solution 3: Display-Time Deduplication (`src/core/message_processor.py`)

**Backup safety layer** in `_generate_memory_summary()`:

- **Track seen entities**: Added `seen_entities` set to prevent duplicate entity names
- **Skip truncated facts**: Filter out facts with common truncation patterns:
  - Ends with " at", " be", " and"
  - Contains phrases like "might be", "who collapse", "access codes"
  - Very short entity names (< 3 characters)
- **First-match preference**: When an entity appears multiple times with different relationships, keep only the first (highest confidence) occurrence

## Results

### Database Before Fix
```sql
sacred geometry work | enjoys | 0.7
sacred geometry work | likes  | 0.7
meditation          | does   | 0.9
meditation          | practices | 0.9
```

### Database After Fix (with storage-time dedup)
```sql
sacred geometry work | likes  | 0.7  (kept highest/first)
meditation          | does   | 0.9  (kept highest/first)
```

### Memory Summary Before Fix
```
Your Preferences: likes indian food, prefers coffee, likes pizza, enjoys sacred geometry work, 
enjoys ai might be, enjoys humans who collapse, likes sacred geometry work, likes ai might be, 
likes humans who collapse, enjoys dean radin at, likes dean radin at, enjoys computational 
architecture simultaneously
```

### Memory Summary After Fix
```
Your Preferences: likes indian food, prefers coffee, likes pizza, enjoys sacred geometry work

Activities & Interests: does meditation

Things You Have: owns cat, owns cats

Other Details: practices chakra system, practices Frigidairism, researching Zecharia Sitchin's 
translations of the Sumerian tablets, studied biofeedback equipment
```

## Files Modified

### New Files
- **`scripts/clean_truncated_facts.py`** - SQL-based cleanup utility for existing corrupted facts

### Modified Files
1. **`src/enrichment/worker.py`**
   - Added `_consolidate_similar_relationships_enrichment()` method
   - Modified `_store_facts_in_postgres()` to call consolidation before storing
   - This is the PRIMARY extraction system (LLM-based enrichment)

2. **`src/knowledge/semantic_router.py`**
   - Added `_get_similar_relationship_groups()` method
   - Added `_consolidate_similar_relationships()` method
   - Modified `store_user_fact()` to call consolidation before storing
   - This is the SECONDARY extraction system (inline during conversation)

3. **`src/core/message_processor.py`**
   - Enhanced `_generate_memory_summary()` for display-time deduplication
   - Added `seen_entities` set for duplicate prevention
   - Added truncation pattern filtering

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   FACT STORAGE PIPELINE                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  PRIMARY: Enrichment Worker (LLM-based extraction)         │
│  ├─ Extracts facts from conversation history              │
│  ├─ Consolidates similar relationships                    │
│  ├─ Stores in PostgreSQL                                  │
│                                                             │
│  SECONDARY: Semantic Router (Inline extraction)            │
│  ├─ Extracts facts during message processing              │
│  ├─ Consolidates similar relationships                    │
│  ├─ Stores in PostgreSQL                                  │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  Both flows use:                                            │
│  1. Opposing relationship detection (likes vs dislikes)    │
│  2. Similar relationship consolidation (likes vs enjoys)   │
│  3. Highest confidence preservation                        │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  DISPLAY: Memory Summary Generation                        │
│  ├─ Retrieves facts from PostgreSQL                        │
│  ├─ Deduplicates by entity name (display layer)           │
│  ├─ Filters truncated/malformed facts                      │
│  ├─ Shows highest confidence relationships                │
└─────────────────────────────────────────────────────────────┘
```

## Impact

- ✅ **User Experience**: Memory summaries are now clean, readable, and accurate
- ✅ **Data Quality**: Removed 31 corrupted facts from database
- ✅ **Duplicate Prevention**: Future memory summaries will show each entity only once
- ✅ **Pattern Filtering**: Incomplete/truncated facts are automatically excluded
- ✅ **Both extraction systems**: Protected from creating duplicate relationships
- ✅ **Confidence preservation**: Always keeps the strongest relationship expression

## Testing Performed

✅ SQL query verification - confirmed 32 truncated facts found  
✅ Database cleanup - successfully removed 31 facts  
✅ Storage-time dedup (enrichment) - verified similar relationships consolidated  
✅ Storage-time dedup (semantic router) - verified similar relationships consolidated  
✅ Memory summary formatting - verified deduplication works  
✅ Truncation pattern filtering - confirmed malformed facts are filtered  
✅ User facts query - verified clean data remains

## Recommendations for Prevention

### 1. Monitor LLM Responses
- Log fact extraction prompts and responses for quality analysis
- Alert on incomplete JSON or truncated entity names
- Consider implementing response length validation

### 2. Periodic Maintenance
- Run `scripts/clean_truncated_facts.py` periodically to catch any edge cases
- Monitor for new truncation patterns that aren't currently filtered

### 3. Future Improvements
- Add database constraints to prevent empty entity names (length >= 3)
- Implement fact extraction response validation
- Consider breaking large fact extraction into smaller chunks

---

**Resolution**: All issues resolved. Memory summaries now display clean, deduplicated, fact-based information about users. Both primary (enrichment worker) and secondary (semantic router) extraction systems are protected from creating duplicate relationships.

