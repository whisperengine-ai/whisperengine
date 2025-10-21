# PostgreSQL Fact Storage Error Fix - October 21, 2025

## Problem Summary

The enrichment worker was encountering two types of PostgreSQL constraint violations when storing facts:

### Error 1: Invalid `entity_relationships.relationship_type`
```
ERROR: new row for relation "entity_relationships" violates check constraint 
"entity_relationships_relationship_type_check"
```

**Root Cause**: Code was attempting to insert `relationship_type = 'semantic_link'` into the `entity_relationships` table, but the database CHECK constraint only allows:
- `'similar_to'`
- `'part_of'`
- `'category_of'`
- `'related_to'`
- `'opposite_of'`
- `'requires'`

**Location**: `src/enrichment/fact_extraction_engine.py` line 619 (in `_identify_relationship()` method)

### Error 2: Empty `user_fact_relationships.relationship_type`
```
ERROR: new row for relation "user_fact_relationships" violates check constraint 
"user_fact_relationships_relationship_type_check"
DETAIL: Failing row contains (..., relationship_type = '', reasoning = '', ...)
```

**Root Cause**: LLM sometimes returns facts without a `relationship_type` field, and the code used `.get('relationship_type', '')` which defaulted to an empty string. The database has a CHECK constraint: `CHECK(LENGTH(relationship_type) > 0 AND LENGTH(relationship_type) <= 50)`

**Location**: `src/enrichment/fact_extraction_engine.py` line 527 (in `_parse_fact_extraction_result()` method)

## Fixes Applied

### Fix 1: Change `'semantic_link'` to `'related_to'`
**File**: `src/enrichment/fact_extraction_engine.py`
**Line**: 619 (in `_identify_relationship()` method)

```python
# BEFORE:
return {
    'type': 'semantic_link',
    'confidence': 0.8,
    'reasoning': f"Related entities: {fact1.entity_name} and {fact2.entity_name}"
}

# AFTER:
return {
    'type': 'related_to',  # Changed from 'semantic_link' to match DB constraint
    'confidence': 0.8,
    'reasoning': f"Related entities: {fact1.entity_name} and {fact2.entity_name}"
}
```

### Fix 2: Validate and provide default relationship_type
**File**: `src/enrichment/fact_extraction_engine.py`
**Line**: 520-541 (in `_parse_fact_extraction_result()` method)

```python
# BEFORE:
fact = ExtractedFact(
    entity_name=fact_data.get('entity_name', ''),
    entity_type=fact_data.get('entity_type', 'other'),
    relationship_type=fact_data.get('relationship_type', ''),  # EMPTY STRING!
    # ...
)

# AFTER:
# CRITICAL: relationship_type MUST NOT be empty (DB CHECK constraint)
relationship_type = fact_data.get('relationship_type', '').strip()
if not relationship_type:
    relationship_type = 'related_to'  # Safe default that works for all entity types
    logger.warning(
        "Empty relationship_type for entity '%s' - defaulting to '%s'",
        fact_data.get('entity_name', 'unknown'), relationship_type
    )

fact = ExtractedFact(
    entity_name=fact_data.get('entity_name', ''),
    entity_type=fact_data.get('entity_type', 'other'),
    relationship_type=relationship_type,  # Now guaranteed to be non-empty
    # ...
)
```

### Fix 3: Update JSONB metadata field (consistency fix)
**File**: `src/enrichment/worker.py`
**Line**: 939

```python
# BEFORE:
related_entities_array.append({
    'entity_id': str(related_entity_id),
    'relation': 'semantic_link',  # Outdated value
    'weight': 0.8
})

# AFTER:
related_entities_array.append({
    'entity_id': str(related_entity_id),
    'relation': 'related_to',  # Updated for consistency
    'weight': 0.8
})
```

**Note**: This is in a JSONB field (`related_entities`), not a database column, so it doesn't violate constraints. However, we updated it for consistency with the valid relationship types.

## Database Schema Reference

### `entity_relationships` table
```sql
CHECK(relationship_type IN (
    'similar_to', 
    'part_of', 
    'category_of', 
    'related_to',      -- ✅ Our fix uses this
    'opposite_of', 
    'requires'
))
```

### `user_fact_relationships` table
```sql
CHECK(LENGTH(relationship_type) > 0 AND LENGTH(relationship_type) <= 50)
-- Requires non-empty string, max 50 characters
```

## Testing

To verify the fixes work:

1. **Rebuild the enrichment worker container**:
```bash
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml up -d --no-deps --build enrichment-worker
```

2. **Monitor PostgreSQL logs for errors**:
```bash
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml logs postgres --tail=50 -f
```

3. **Check enrichment worker logs for warnings**:
```bash
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml logs enrichment-worker --tail=50 -f
```

Look for the new warning message:
```
Empty relationship_type for entity 'XXX' - defaulting to 'related_to'
```

## Impact

✅ **No breaking changes** - Existing data is unaffected
✅ **Forward compatible** - New facts will store correctly
✅ **Defensive coding** - Validates LLM responses and provides safe defaults
✅ **Consistent terminology** - Uses valid DB constraint values throughout codebase

## Related Files

- `src/enrichment/fact_extraction_engine.py` - Fact extraction and relationship building
- `src/enrichment/worker.py` - Enrichment worker that stores facts in PostgreSQL
- `sql/semantic_knowledge_graph_schema.sql` - Database schema with CHECK constraints
- `alembic/versions/20251019_1858_27e207ded5a0_*.py` - Documentation of schema
