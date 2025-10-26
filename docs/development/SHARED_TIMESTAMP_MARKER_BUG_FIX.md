# Shared Timestamp Marker Bug Fix - October 2025

## 🐛 Bug Description

**Critical Bug**: Preference extraction was being skipped because facts and preferences shared the same timestamp marker (`_enrichment_progress_marker`), causing preferences to see "no new messages" after fact extraction updated the shared marker.

## 📊 Impact Analysis

**Affected Users**: ALL users in production
**Discovery Date**: October 25, 2025
**Test Case**: User `enrichment_test_1761429358` had 12 messages with clear biographical facts and preferences, but 0 preferences were extracted

## 🔍 Root Cause

### Timeline of Bug Manifestation
```
22:01:33-22:02:47: Fact extraction runs
                   - Processes 12 messages
                   - Updates shared _enrichment_progress_marker with latest timestamp
                   
22:02:57:          Preference extraction runs
                   - Checks _enrichment_progress_marker 
                   - Finds timestamp already at latest message
                   - Logs: "⏭️ [NO LLM CALL] No new messages for preference extraction"
                   - SKIPS extraction completely
                   
All subsequent cycles: Both fact and preference extraction skip (marker already set)
```

### Technical Root Cause

Both fact and preference extraction used the **same marker system**:
- **Entity Name**: `{bot_name}_{user_id}` (no type differentiation)
- **Relationship Type**: `_enrichment_progress_marker` (shared)
- **Result**: Whichever ran first would update the marker, causing the second to skip

## ✅ Solution Implemented

### Separate Timestamp Markers

Created **independent markers** for facts and preferences:

**Fact Marker**:
- Entity Name: `{bot_name}_{user_id}_fact`
- Relationship Type: `_enrichment_fact_marker`

**Preference Marker**:
- Entity Name: `{bot_name}_{user_id}_preference`
- Relationship Type: `_enrichment_preference_marker`

### Code Changes

#### 1. Modified `_store_last_processed_timestamp()` Method
**File**: `src/enrichment/worker.py` (Lines 827-905)

Added `marker_type` parameter to support separate tracking:

```python
async def _store_last_processed_timestamp(
    self,
    user_id: str,
    bot_name: str,
    latest_message_timestamp: datetime,
    marker_type: str = 'fact'  # NEW: 'fact' or 'preference'
):
    """
    Store the last processed message timestamp for incremental processing.
    
    CRITICAL FIX (Oct 2025): Separate markers for facts and preferences.
    Previously, both used same marker, causing preferences to skip if facts processed first.
    """
    # Generate marker-specific entity name and relationship type
    marker_entity_name = f"{bot_name}_{user_id}_{marker_type}"
    marker_relationship_type = f'_enrichment_{marker_type}_marker'
    
    # Store marker with type-specific metadata
    context_metadata = {
        'latest_message_timestamp': ts_to_store.isoformat(),
        'bot_name': bot_name,
        'marker_type': f'enrichment_{marker_type}_progress'
    }
```

#### 2. Updated `_get_last_preference_extraction()` Method
**File**: `src/enrichment/worker.py` (Lines 1482-1509)

Changed query to use preference-specific marker:

```python
# OLD: Queried shared marker
WHERE ufr.relationship_type = '_enrichment_progress_marker'

# NEW: Queries preference-specific marker
WHERE ufr.relationship_type = '_enrichment_preference_marker'
```

#### 3. Updated All Caller Sites

**Fact Extraction Calls** (Lines 726-730, 772-776):
```python
await self._store_last_processed_timestamp(
    user_id=user_id,
    bot_name=bot_name,
    latest_message_timestamp=latest_message_timestamp,
    marker_type='fact'  # Added
)
```

**Preference Extraction Calls** (Lines 1445-1449, 1465-1469):
```python
await self._store_last_processed_timestamp(
    user_id=user_id,
    bot_name=bot_name,
    latest_message_timestamp=latest_message_timestamp,
    marker_type='preference'  # Added
)
```

## 🧪 Testing & Validation

### Pre-Fix Database State (Test User: enrichment_test_1761429358)
```sql
-- 1 shared marker (used by both facts and preferences)
SELECT fe.entity_name, fe.entity_type, ufr.relationship_type
FROM user_fact_relationships ufr
JOIN fact_entities fe ON ufr.entity_id = fe.id
WHERE ufr.user_id = 'enrichment_test_1761429358'
  AND fe.entity_type = '_processing_marker';

-- Result:
-- entity_name: jake_enrichment_test_1761429358
-- entity_type: _processing_marker
-- relationship_type: _enrichment_progress_marker
```

### Expected Post-Fix Database State
```sql
-- 2 separate markers (independent tracking)
-- Fact marker:
-- entity_name: jake_enrichment_test_1761429358_fact
-- relationship_type: _enrichment_fact_marker

-- Preference marker:
-- entity_name: jake_enrichment_test_1761429358_preference
-- relationship_type: _enrichment_preference_marker
```

### Validation Queries

**Check Marker Separation**:
```sql
SELECT 
    fe.entity_name,
    fe.entity_type,
    ufr.relationship_type,
    ufr.context_metadata->'marker_type' as marker_type,
    ufr.updated_at
FROM user_fact_relationships ufr
JOIN fact_entities fe ON ufr.entity_id = fe.id
WHERE ufr.user_id = 'enrichment_test_1761429358'
  AND fe.entity_type = '_processing_marker'
ORDER BY ufr.updated_at DESC;
```

**Check Preference Extraction**:
```sql
SELECT 
    preference_type,
    preference_value,
    confidence,
    source,
    created_at
FROM universal_users
WHERE user_id = 'enrichment_test_1761429358'
  AND preferences IS NOT NULL;
```

### Expected Behavior After Fix

1. **First Enrichment Cycle**:
   - Fact extraction processes messages → Creates `_enrichment_fact_marker`
   - Preference extraction processes SAME messages → Creates `_enrichment_preference_marker`
   - Both extract successfully from same message window

2. **Subsequent Cycles**:
   - Each extraction type checks its OWN marker
   - No interference between fact and preference tracking
   - Both can process independently

## 📈 Expected Impact

### Before Fix
- **Facts**: Extracted normally ✅
- **Preferences**: Skipped after facts processed ❌
- **Result**: 0 preferences extracted for ALL users

### After Fix
- **Facts**: Continue extracting normally ✅
- **Preferences**: Now extract independently ✅
- **Result**: Both extraction types work as designed

## 🚀 Deployment Status

- **Fix Implemented**: October 25, 2025
- **Container Rebuilt**: `enrichment-worker` (docker-compose.multi-bot.yml)
- **Syntax Validated**: ✅ py_compile passed
- **Container Status**: ✅ Running without errors
- **Next Enrichment Cycle**: ~12 minutes from rebuild

## 📝 Related Documentation

- **Fact Extraction Bug Fix**: `FACT_EXTRACTION_ZERO_RESULTS_BUG_FIX.md`
- **Phase 2-E Design**: `docs/roadmaps/MEMORY_INTELLIGENCE_CONVERGENCE_ROADMAP.md`
- **Enrichment Architecture**: `ENRICHMENT_QUICKSTART.md`

## 🔗 Database Schema Impact

### New Marker Patterns

**Fact Markers**:
```
fact_entities:
  - entity_type: '_processing_marker'
  - entity_name: '{bot}_{user}_fact'
  - category: '_marker'
  - attributes: {"type": "enrichment_fact_progress"}

user_fact_relationships:
  - relationship_type: '_enrichment_fact_marker'
  - context_metadata: {
      "latest_message_timestamp": "2025-10-25T...",
      "bot_name": "jake",
      "marker_type": "enrichment_fact_progress"
    }
```

**Preference Markers**:
```
fact_entities:
  - entity_type: '_processing_marker'
  - entity_name: '{bot}_{user}_preference'
  - category: '_marker'
  - attributes: {"type": "enrichment_preference_progress"}

user_fact_relationships:
  - relationship_type: '_enrichment_preference_marker'
  - context_metadata: {
      "latest_message_timestamp": "2025-10-25T...",
      "bot_name": "jake",
      "marker_type": "enrichment_preference_progress"
    }
```

## 🎯 Success Metrics

Monitor these metrics to validate fix effectiveness:

1. **Preference Extraction Rate**: Should increase from 0% to expected baseline
2. **LLM Calls for Preferences**: Should start appearing in logs
3. **universal_users.preferences**: Should populate for users with preference-expressing messages
4. **Marker Count**: Should see 2 markers per user (fact + preference) instead of 1 shared marker

## ⚠️ Migration Notes

### Legacy Markers
- Old shared markers (`_enrichment_progress_marker`) remain in database
- New markers (`_enrichment_fact_marker`, `_enrichment_preference_marker`) created on next cycle
- No data migration required - system naturally transitions to new markers
- Old markers become orphaned but harmless (can be cleaned up later)

### Backward Compatibility
- Default marker_type='fact' ensures backward compatibility
- If marker_type not specified, defaults to fact extraction behavior
- Preference extraction explicitly passes marker_type='preference'
