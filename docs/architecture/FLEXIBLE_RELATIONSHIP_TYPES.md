# Flexible Relationship Types - Architectural Decision

**Date**: October 5, 2025  
**Status**: Implemented  
**Decision**: Remove strict CHECK constraints on `relationship_type` field

## Problem

The original `user_fact_relationships` table had an overly strict CHECK constraint:

```sql
CHECK(relationship_type IN ('likes', 'dislikes', 'knows', 'visited', 'wants', 'owns', 'prefers', 'interested_in'))
```

**Issues with this approach:**

1. **Code/Schema Synchronization Required** - Every new relationship type in Python code required a database migration
2. **Blocked Natural Language Evolution** - Semantically valid types like `'enjoys'`, `'loves'`, `'hates'` were arbitrarily rejected
3. **False Sense of Data Quality** - The constraint didn't improve data quality, just forced artificial mappings
4. **Maintenance Burden** - Two places to maintain (code + schema) = guaranteed drift and production errors
5. **Alpha Phase Rigidity** - During development, we should explore relationship types, not lock them down
6. **Production Errors** - Caused PostgreSQL constraint violations that crashed knowledge extraction

## Solution

**Replace strict enumeration with flexible validation:**

```sql
CHECK(LENGTH(relationship_type) > 0 AND LENGTH(relationship_type) <= 50)
```

**Benefits:**

- ✅ **Natural Language Friendly** - Any reasonable relationship type is accepted
- ✅ **No Code/Schema Drift** - Python code can evolve independently
- ✅ **Semantic Accuracy** - Use `'enjoys'` for hobbies, `'likes'` for preferences naturally
- ✅ **Future-Proof** - Easy to add new relationship types without migrations
- ✅ **Prevents Empty Strings** - Basic validation still ensures data quality
- ✅ **Alpha-Appropriate** - Flexible enough for experimentation and iteration

## Common Relationship Types

**Current usage in code:**

- `'likes'` - User likes something (food, drinks, general preferences)
- `'dislikes'` - User dislikes something
- `'enjoys'` - User enjoys an activity or hobby
- `'knows'` - User knows about something
- `'visited'` - User has visited a place
- `'wants'` - User wants something
- `'owns'` - User owns something
- `'prefers'` - User prefers one thing over another
- `'interested_in'` - User is interested in a topic
- `'loves'` - Stronger preference than likes
- `'hates'` - Stronger dislike

**Future possibilities:**
- `'fears'`, `'avoids'`, `'needs'`, `'collects'`, `'follows'`, `'practices'`, `'studies'`, etc.

## Implementation

**Migration Applied**: `sql/migrations/001_remove_relationship_type_constraint.sql`

```sql
ALTER TABLE user_fact_relationships 
DROP CONSTRAINT IF EXISTS user_fact_relationships_relationship_type_check;

ALTER TABLE user_fact_relationships 
ADD CONSTRAINT user_fact_relationships_relationship_type_check 
CHECK (LENGTH(relationship_type) > 0 AND LENGTH(relationship_type) <= 50);
```

**Schema Updated**: `sql/semantic_knowledge_graph_schema.sql` (line 97)

**Code Impact**: `src/core/message_processor.py` now uses semantically accurate `'enjoys'` for hobbies

## Validation Strategy

**Database Layer**: Length validation only (non-empty, max 50 chars)

**Application Layer**: Python code determines appropriate relationship types based on:
- Semantic analysis of user messages
- Context patterns (food, drinks, hobbies, places)
- Natural language understanding
- Character personality and domain expertise

**No centralized validation** - Each component can use relationship types that make semantic sense

## Design Philosophy

This follows WhisperEngine's **Fidelity-First Architecture** principle:
- Prioritize natural language authenticity over rigid categorization
- Allow semantic nuance in relationship modeling
- Avoid premature optimization that sacrifices flexibility
- Trust application-layer intelligence over database-layer restrictions

**Database constraints should prevent data corruption, not limit semantic expressiveness.**

## Related Systems

- **Semantic Knowledge Graph**: `src/knowledge/semantic_router.py`
- **Knowledge Extraction**: `src/core/message_processor.py` (lines 2280-2380)
- **PostgreSQL Schema**: `sql/semantic_knowledge_graph_schema.sql`
- **Phase 3 Knowledge Integration**: Uses flexible relationship types for user preference tracking

## Testing

**Validation**: Test that various relationship types work correctly:

```python
# All of these should work without database errors
await semantic_router.store_user_fact(
    user_id="test_user",
    entity_name="hiking",
    entity_type="hobby",
    relationship_type="enjoys"  # ✅ Works now
)

await semantic_router.store_user_fact(
    user_id="test_user",
    entity_name="horror movies",
    entity_type="entertainment",
    relationship_type="loves"  # ✅ Works now
)

await semantic_router.store_user_fact(
    user_id="test_user",
    entity_name="spiders",
    entity_type="animal",
    relationship_type="fears"  # ✅ Works now
)
```

## Future Considerations

**If strict validation becomes necessary:**
1. Implement in Python code, not database constraints
2. Use a configuration file (YAML/JSON) for valid types
3. Add logging for unexpected relationship types
4. Consider ML-based relationship type extraction
5. Allow character-specific relationship type vocabularies

**But for now**: Flexible validation is the right choice for alpha development.
