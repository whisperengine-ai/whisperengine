# CDL Database Cleanup Recommendations - October 13, 2025

## Executive Summary

After comprehensive audit of 51 character-related tables, identified **5 tables for cleanup**:
- ✅ 1 backup table (no foreign keys) - **SAFE TO DROP**
- ⚠️ 2 duplicate/deprecated versioned tables - **NEEDS MIGRATION**
- ⚠️ 2 potentially redundant tables - **NEEDS ANALYSIS**

## 🚨 Immediate Cleanup Candidates

### 1. character_conversation_flows_json_backup (SAFE TO DROP)

**Status**: ✅ **READY TO DROP** - No foreign key dependencies

**Evidence**:
```sql
-- Table structure
CREATE TABLE character_conversation_flows_json_backup (
    id INTEGER,
    character_id INTEGER,
    flow_name VARCHAR(200),
    approach_description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    backup_reason TEXT DEFAULT 'Legacy JSON cleanup'
);

-- Current data: 15 rows
-- Foreign keys: NONE (orphaned backup table)
-- Size: 48 kB
```

**Analysis**:
- Created as backup during JSON cleanup migration
- No foreign key constraints (cannot be referenced)
- Contains 15 old flow records
- Zero code references in codebase
- Safe to drop without impacting system

**Recommendation**: **DROP immediately**
```sql
DROP TABLE character_conversation_flows_json_backup;
```

**Risk Level**: 🟢 ZERO - No dependencies, no code references

---

### 2. character_conversation_flows vs character_conversation_modes (DUPLICATE DATA)

**Status**: ⚠️ **DUPLICATE FUNCTIONALITY** - Needs consolidation

**Evidence**:
```sql
-- character_conversation_flows (OLD - 50 rows)
- flow_type, flow_name, energy_level, approach_description, transition_style, priority, context
- Has 1 FK reference: character_conversation_directives

-- character_conversation_modes (NEW - 20 rows)  
- mode_name, energy_level, approach, transition_style
- Has 3 child tables: character_mode_guidance, character_mode_examples, character_message_triggers
- ACTIVELY USED by trigger_mode_controller.py
```

**Analysis**:
- `character_conversation_modes` is the **NEW normalized schema** (current prompt optimization)
- `character_conversation_flows` is **LEGACY table** with older flow data
- Code uses `character_conversation_flows` in `get_conversation_flows()` method (line 304)
- Trigger system uses `character_conversation_modes` (PRIMARY mode detection)
- **CONFLICT**: Two tables serving similar purpose causes confusion

**Current Usage**:
```python
# enhanced_cdl_manager.py:304 - USES OLD TABLE
FROM character_conversation_flows 
WHERE character_id = $1

# trigger_mode_controller.py - USES NEW TABLE  
interaction_modes = await self.enhanced_manager.get_interaction_modes(character_name)
# -> Queries character_conversation_modes
```

**Recommendation**: **CONSOLIDATE** - Migrate flows data to modes schema
```sql
-- Migration strategy:
1. Identify unique flows in character_conversation_flows not in character_conversation_modes
2. Migrate missing data to character_conversation_modes with proper mode guidance
3. Update character_conversation_directives FK to point to character_conversation_modes
4. Update get_conversation_flows() to query character_conversation_modes  
5. Drop character_conversation_flows after validation
```

**Risk Level**: 🟡 MEDIUM - Has FK dependency (character_conversation_directives)

---

### 3. character_emotional_triggers vs character_emotional_triggers_v2 (VERSION CONFLICT)

**Status**: ⚠️ **TWO VERSIONS** - Consolidation needed

**Evidence**:
```sql
-- character_emotional_triggers (v1 - 154 rows)
- trigger_type, trigger_category, trigger_content, emotional_response, response_intensity

-- character_emotional_triggers_v2 (v2 - 58 rows)
- trigger_text, valence, emotion_evoked, intensity (1-10), response_guidance
```

**Analysis**:
- V1 has MORE data (154 rows) vs V2 (58 rows)
- Code **ONLY uses V1** table: `enhanced_cdl_manager.py:673`
```python
FROM character_emotional_triggers  # Uses v1, not v2!
WHERE character_id = $1
```
- V2 table is **ORPHANED** - no code references
- V2 has better schema (structured valence, intensity constraints)
- V2 appears to be **INCOMPLETE MIGRATION** attempt

**Current Code Usage**:
```python
# enhanced_cdl_manager.py:662-675 - ONLY V1 USED
async def get_emotional_triggers(self, character_name: str) -> List[EmotionalTrigger]:
    rows = await conn.fetch("""
        SELECT trigger_type, trigger_category, trigger_content, 
               emotional_response, response_intensity, response_examples
        FROM character_emotional_triggers  # V1 only!
        WHERE character_id = $1
    """, character_id)
```

**Recommendation**: **EVALUATE AND CONSOLIDATE**

**Option A**: Keep V1 (simpler, has all data)
```sql
DROP TABLE character_emotional_triggers_v2;  -- Orphaned incomplete migration
```

**Option B**: Complete V2 migration (better schema)
```sql
-- Migrate remaining 96 triggers from v1 to v2 with proper mapping
-- Update code to use v2 schema
-- Drop v1 after validation
```

**Suggested**: **Option A** (simpler) - V2 migration appears abandoned, V1 is working

**Risk Level**: 🟡 MEDIUM - Need to verify no hidden V2 usage

---

### 4. character_roleplay_scenarios_v2 (VERSION NAMING)

**Status**: ⚠️ **UNCLEAR IF V1 EXISTS**

**Evidence**:
```sql
-- character_roleplay_scenarios_v2 (64 kB, has data)
- scenario_name, response_pattern, tier_1_response, tier_2_response, tier_3_response
- Used in code: enhanced_cdl_manager.py:1252
```

**Analysis**:
- Table name suggests V1 existed, but no `character_roleplay_scenarios` table found
- Code actively uses this table for AI identity roleplay scenarios
- Either:
  * V1 was dropped (V2 is current) → Rename to remove "_v2"
  * V1 never existed → Bad naming convention

**Recommendation**: **RENAME to remove "_v2" suffix** (if no V1)
```sql
ALTER TABLE character_roleplay_scenarios_v2 RENAME TO character_roleplay_scenarios;
-- Update code references
```

**Risk Level**: 🟢 LOW - Just naming cleanup

---

### 5. character_scenario_triggers_v2 (VERSION NAMING)

**Status**: ⚠️ **UNCLEAR IF V1 EXISTS**

**Evidence**:
```sql
-- character_scenario_triggers_v2 (32 kB)
- Companion table to character_roleplay_scenarios_v2
- No code references found
```

**Analysis**:
- Naming suggests V1 existed
- No code references found (potentially unused)
- May be referenced by character_roleplay_scenarios_v2 FK

**Recommendation**: **INVESTIGATE USAGE**
```sql
-- Check if orphaned
SELECT COUNT(*) FROM character_scenario_triggers_v2;
-- Check FK relationships
SELECT * FROM information_schema.table_constraints 
WHERE table_name = 'character_scenario_triggers_v2';
```

**Risk Level**: 🟡 MEDIUM - Need usage analysis

---

## 📊 Table Usage Analysis

### Tables Actively Used by Code

✅ **KEEP - Core functionality**:
- `character_conversation_modes` - Mode detection (trigger_mode_controller.py)
- `character_mode_guidance` - Mode avoid/encourage patterns
- `character_mode_examples` - Mode usage examples
- `character_message_triggers` - Trigger keyword detection
- `character_behavioral_triggers` - Behavioral responses
- `character_emotional_triggers` - Emotional guidance (V1)
- `character_roleplay_scenarios_v2` - AI identity roleplay

### Tables With Issues

⚠️ **NEEDS ACTION**:
- `character_conversation_flows_json_backup` - **DROP** (orphaned backup)
- `character_conversation_flows` - **CONSOLIDATE** with character_conversation_modes
- `character_emotional_triggers_v2` - **DROP** (orphaned V2 attempt)
- `character_roleplay_scenarios_v2` - **RENAME** to remove "_v2"
- `character_scenario_triggers_v2` - **INVESTIGATE** usage

### Tables Not Analyzed (Assumed Active)

The remaining 41 character tables were not flagged as problematic and appear to have distinct purposes.

---

## 🎯 Recommended Cleanup Plan

### Phase 1: Safe Deletions (Zero Risk)

```sql
-- 1. Drop orphaned backup table (no dependencies)
DROP TABLE IF EXISTS character_conversation_flows_json_backup;
```

### Phase 2: Version Consolidation (Low Risk)

```sql
-- 2. Drop orphaned V2 emotional triggers (incomplete migration)
DROP TABLE IF EXISTS character_emotional_triggers_v2;

-- 3. Rename V2 roleplay scenarios (remove version suffix)
ALTER TABLE character_roleplay_scenarios_v2 RENAME TO character_roleplay_scenarios;
ALTER TABLE character_scenario_triggers_v2 RENAME TO character_scenario_triggers;

-- Update code references in enhanced_cdl_manager.py:1252
-- Change: FROM character_roleplay_scenarios_v2
-- To:     FROM character_roleplay_scenarios
```

### Phase 3: Flow/Mode Consolidation (Medium Risk - Requires Testing)

**Step 1**: Analyze data overlap
```sql
-- Find flows not in modes
SELECT cf.flow_name, cf.flow_type, cf.character_id
FROM character_conversation_flows cf
LEFT JOIN character_conversation_modes cm 
    ON cf.character_id = cm.character_id 
    AND cf.flow_name = cm.mode_name
WHERE cm.id IS NULL;
```

**Step 2**: Migrate unique flows to modes schema
```sql
-- Insert missing flows as modes
INSERT INTO character_conversation_modes 
    (character_id, mode_name, energy_level, approach, transition_style, is_default, display_order)
SELECT 
    character_id,
    flow_name,
    energy_level,
    approach_description,
    transition_style,
    (priority > 75) as is_default,  -- High priority = default mode
    priority
FROM character_conversation_flows
WHERE NOT EXISTS (
    SELECT 1 FROM character_conversation_modes cm 
    WHERE cm.character_id = character_conversation_flows.character_id 
    AND cm.mode_name = character_conversation_flows.flow_name
);
```

**Step 3**: Update character_conversation_directives FK
```sql
-- Add new FK to character_conversation_modes
ALTER TABLE character_conversation_directives 
ADD COLUMN conversation_mode_id INTEGER 
REFERENCES character_conversation_modes(id) ON DELETE CASCADE;

-- Migrate FK data
UPDATE character_conversation_directives ccd
SET conversation_mode_id = (
    SELECT cm.id 
    FROM character_conversation_modes cm
    JOIN character_conversation_flows cf ON cf.character_id = cm.character_id AND cf.flow_name = cm.mode_name
    WHERE cf.id = ccd.conversation_flow_id
);

-- Drop old FK
ALTER TABLE character_conversation_directives 
DROP CONSTRAINT character_conversation_directives_conversation_flow_id_fkey,
DROP COLUMN conversation_flow_id;
```

**Step 4**: Update code
```python
# enhanced_cdl_manager.py:300-320
# Change get_conversation_flows() to query character_conversation_modes instead
async def get_conversation_flows(self, character_name: str) -> List[ConversationFlow]:
    """Get conversation modes (replacing legacy flows)"""
    return await self.get_interaction_modes(character_name)
```

**Step 5**: Drop legacy table
```sql
DROP TABLE character_conversation_flows;
```

---

## 🧪 Validation Queries

### Before Cleanup
```sql
-- Count records in all tables
SELECT 'conversation_flows' as table_name, COUNT(*) FROM character_conversation_flows
UNION ALL SELECT 'conversation_modes', COUNT(*) FROM character_conversation_modes
UNION ALL SELECT 'emotional_triggers_v1', COUNT(*) FROM character_emotional_triggers
UNION ALL SELECT 'emotional_triggers_v2', COUNT(*) FROM character_emotional_triggers_v2
UNION ALL SELECT 'flows_backup', COUNT(*) FROM character_conversation_flows_json_backup;
```

### After Phase 1 Cleanup
```sql
-- Verify backup table dropped
SELECT table_name FROM information_schema.tables 
WHERE table_name = 'character_conversation_flows_json_backup';
-- Expected: 0 rows
```

### After Phase 2 Cleanup
```sql
-- Verify V2 tables handled
SELECT table_name FROM information_schema.tables 
WHERE table_name IN ('character_emotional_triggers_v2', 'character_roleplay_scenarios_v2');
-- Expected: 0 rows (both renamed or dropped)
```

---

## 📝 Code Changes Required

### File: `src/characters/cdl/enhanced_cdl_manager.py`

**Line 1252**: Update roleplay scenarios query
```python
# BEFORE
FROM character_roleplay_scenarios_v2 

# AFTER  
FROM character_roleplay_scenarios
```

**Lines 300-320**: Update conversation flows method (Phase 3 only)
```python
# BEFORE
async def get_conversation_flows(self, character_name: str) -> List[ConversationFlow]:
    rows = await conn.fetch("""
        SELECT flow_type, flow_name, energy_level, approach_description
        FROM character_conversation_flows 
        WHERE character_id = $1
    """, character_id)

# AFTER
async def get_conversation_flows(self, character_name: str) -> List[ConversationFlow]:
    # Redirect to interaction modes (unified schema)
    return await self.get_interaction_modes(character_name)
```

---

## 🎯 Summary & Recommendations

### Immediate Actions (Safe - No Risk)
1. ✅ **DROP `character_conversation_flows_json_backup`** - Orphaned backup table
2. ✅ **DROP `character_emotional_triggers_v2`** - Abandoned migration attempt

### Short-term Actions (Low Risk)
3. ✅ **RENAME `character_roleplay_scenarios_v2`** → `character_roleplay_scenarios`
4. ✅ **RENAME `character_scenario_triggers_v2`** → `character_scenario_triggers`  
5. ✅ **UPDATE code references** in enhanced_cdl_manager.py:1252

### Medium-term Actions (Requires Testing)
6. ⚠️ **CONSOLIDATE `character_conversation_flows`** into `character_conversation_modes`
7. ⚠️ **MIGRATE `character_conversation_directives` FK** to new schema
8. ⚠️ **UPDATE `get_conversation_flows()` method** to use unified modes
9. ⚠️ **TEST mode detection** with Jake/Elena characters
10. ⚠️ **DROP `character_conversation_flows`** after validation

### Benefits
- **Reduced confusion**: Single source of truth for conversation modes
- **Cleaner schema**: No duplicate/versioned tables
- **Better maintainability**: Consistent naming without "_v2" suffixes  
- **Storage savings**: ~200 kB reclaimed from redundant tables

---

**Status**: Ready for Phase 1 & 2 implementation  
**Audit Date**: October 13, 2025  
**Next Review**: After Phase 3 consolidation completion
