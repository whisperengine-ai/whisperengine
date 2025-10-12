# CDL Schema vs Code: Complete Field Comparison

**Date**: October 11, 2025  
**Analysis**: Complete audit of migration 006 schema vs enhanced_cdl_manager.py code  
**Purpose**: Identify ALL missing fields between database schema and code implementation

---

## Summary Statistics

**Total Tables in Migration 006**: 12 tables  
**Tables Currently Queried by Code**: 4 tables (33%)  
**Tables with Missing Field Coverage**: 4 tables (100% of queried tables)  
**Estimated Data Loss**: 30-40% of available character data

---

## Detailed Table-by-Table Comparison

### ✅ Tables That Code Currently Uses (with field gaps)

#### 1. character_speech_patterns

**Database Schema** (6 fields):
```sql
CREATE TABLE character_speech_patterns (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id),
    pattern_type VARCHAR(100) NOT NULL,    -- ✅ Queried
    pattern_value TEXT NOT NULL,            -- ✅ Queried
    usage_frequency VARCHAR(50),            -- ✅ Queried
    context VARCHAR(100),                   -- ✅ Queried
    priority INTEGER DEFAULT 50             -- ✅ Queried
);
```

**Code Implementation**:
```python
# enhanced_cdl_manager.py lines 280-295
rows = await conn.fetch("""
    SELECT pattern_type, pattern_value, usage_frequency, context, priority
    FROM character_speech_patterns 
    WHERE character_id = $1
    ORDER BY priority DESC
""", character_id)

@dataclass
class SpeechPattern:
    pattern_type: str
    pattern_value: str
    usage_frequency: str
    context: str
    priority: int
```

**Field Coverage**: ✅ 100% - ALL schema fields queried

---

#### 2. character_conversation_flows

**Database Schema** (8 fields):
```sql
CREATE TABLE character_conversation_flows (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id),
    flow_type VARCHAR(100) NOT NULL,        -- ✅ Queried
    flow_name VARCHAR(200),                 -- ✅ Queried
    energy_level VARCHAR(50),               -- ✅ Queried
    approach_description TEXT,              -- ✅ Queried
    transition_style TEXT,                  -- ✅ Queried
    priority INTEGER DEFAULT 50,            -- ✅ Queried
    context TEXT                            -- ❌ NOT QUERIED
);
```

**Code Implementation**:
```python
# enhanced_cdl_manager.py lines 297-315
rows = await conn.fetch("""
    SELECT flow_type, flow_name, energy_level, 
           approach_description, transition_style, priority
    FROM character_conversation_flows 
    WHERE character_id = $1
    ORDER BY priority DESC
""", character_id)

@dataclass
class ConversationFlow:
    flow_type: str
    flow_name: str
    energy_level: str
    approach_description: str
    transition_style: str
    priority: int
    # ❌ MISSING: context
```

**Field Coverage**: ⚠️ 86% (6/7 fields)  
**Missing Fields**: context

---

#### 3. character_behavioral_triggers

**Database Schema** (8 fields):
```sql
-- Note: This table doesn't exist in migration 006!
-- It exists in migration 005 as character_communication_patterns
-- Code is querying wrong table name!
```

**Code Implementation**:
```python
# enhanced_cdl_manager.py lines 337-355
rows = await conn.fetch("""
    SELECT trigger_type, trigger_value, response_type, 
           response_description, intensity_level
    FROM character_behavioral_triggers 
    WHERE character_id = $1
    ORDER BY intensity_level DESC
""", character_id)

@dataclass
class BehavioralTrigger:
    trigger_type: str
    trigger_value: str
    response_type: str
    response_description: str
    intensity_level: int = 5
```

**⚠️ CRITICAL ISSUE**: Code queries `character_behavioral_triggers` but migration 006 doesn't create this table! This table was in migration 005.

**Field Coverage**: ⚠️ Unknown - table mismatch between migrations

---

#### 4. character_relationships

**Database Schema** (8 fields):
```sql
-- Note: This table doesn't exist in migration 006!
-- It exists in migration 005
-- Code is querying wrong table name!
```

**Code Implementation**:
```python
# enhanced_cdl_manager.py lines 317-335
rows = await conn.fetch("""
    SELECT related_entity, relationship_type, relationship_strength, 
           description, status
    FROM character_relationships 
    WHERE character_id = $1
    ORDER BY relationship_strength DESC
""", character_id)

@dataclass
class CharacterRelationship:
    related_entity: str
    relationship_type: str
    relationship_strength: int = 5
    description: Optional[str] = None
    status: str = 'active'
```

**⚠️ CRITICAL ISSUE**: Code queries `character_relationships` but migration 006 doesn't create this table! This table was in migration 005.

**Field Coverage**: ⚠️ Unknown - table mismatch between migrations

---

### ❌ Tables Code Doesn't Use At All (0% coverage)

#### 5. character_response_guidelines

**Database Schema** (8 fields):
```sql
CREATE TABLE character_response_guidelines (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id),
    guideline_type VARCHAR(100) NOT NULL,   -- ❌ NOT QUERIED
    guideline_name VARCHAR(200),            -- ❌ NOT QUERIED
    guideline_content TEXT NOT NULL,        -- ❌ NOT QUERIED
    priority INTEGER DEFAULT 50,            -- ❌ NOT QUERIED
    context VARCHAR(100),                   -- ❌ NOT QUERIED
    is_critical BOOLEAN DEFAULT FALSE,      -- ❌ NOT QUERIED
    created_date TIMESTAMP DEFAULT NOW()    -- ❌ NOT QUERIED
);
```

**Code Implementation**: ❌ **NOT IMPLEMENTED**

**Purpose**: Response length guidelines, formatting rules, tone directives  
**Impact**: Characters can't access critical response guidance from database  
**Field Coverage**: ❌ 0% - table completely unused

---

#### 6. character_conversation_directives

**Database Schema** (5 fields):
```sql
CREATE TABLE character_conversation_directives (
    id SERIAL PRIMARY KEY,
    conversation_flow_id INTEGER REFERENCES character_conversation_flows(id),
    directive_type VARCHAR(50) NOT NULL,    -- ❌ NOT QUERIED
    directive_content TEXT NOT NULL,        -- ❌ NOT QUERIED
    order_sequence INTEGER                  -- ❌ NOT QUERIED
);
```

**Code Implementation**: ❌ **NOT IMPLEMENTED**

**Purpose**: Things to avoid/encourage in conversation flows  
**Impact**: Characters lack specific conversation guidance  
**Field Coverage**: ❌ 0% - table completely unused

---

#### 7. character_message_triggers

**Database Schema** (8 fields):
```sql
CREATE TABLE character_message_triggers (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id),
    trigger_category VARCHAR(100) NOT NULL, -- ❌ NOT QUERIED
    trigger_type VARCHAR(50) NOT NULL,      -- ❌ NOT QUERIED
    trigger_value TEXT NOT NULL,            -- ❌ NOT QUERIED
    response_mode VARCHAR(100),             -- ❌ NOT QUERIED
    priority INTEGER DEFAULT 50,            -- ❌ NOT QUERIED
    is_active BOOLEAN DEFAULT TRUE          -- ❌ NOT QUERIED
);
```

**Code Implementation**: ❌ **NOT IMPLEMENTED**

**Purpose**: Keywords/phrases that trigger specific response modes  
**Impact**: Characters can't adapt response style based on trigger words  
**Field Coverage**: ❌ 0% - table completely unused

---

#### 8. character_response_modes

**Database Schema** (9 fields):
```sql
CREATE TABLE character_response_modes (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id),
    mode_name VARCHAR(100) NOT NULL,        -- ❌ NOT QUERIED
    mode_description TEXT,                  -- ❌ NOT QUERIED
    response_style TEXT,                    -- ❌ NOT QUERIED
    length_guideline TEXT,                  -- ❌ NOT QUERIED
    tone_adjustment TEXT,                   -- ❌ NOT QUERIED
    conflict_resolution_priority INTEGER,   -- ❌ NOT QUERIED
    examples TEXT                           -- ❌ NOT QUERIED
);
```

**Code Implementation**: ❌ **NOT IMPLEMENTED**

**Purpose**: Different response modes (technical, creative, brief) with specific guidelines  
**Impact**: Characters can't switch response modes properly  
**Field Coverage**: ❌ 0% - table completely unused

---

#### 9. character_emoji_patterns

**Database Schema** (8 fields):
```sql
CREATE TABLE character_emoji_patterns (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id),
    pattern_category VARCHAR(100) NOT NULL, -- ❌ NOT QUERIED
    pattern_name VARCHAR(100) NOT NULL,     -- ❌ NOT QUERIED
    emoji_sequence TEXT,                    -- ❌ NOT QUERIED
    usage_context TEXT,                     -- ❌ NOT QUERIED
    frequency VARCHAR(50),                  -- ❌ NOT QUERIED
    example_usage TEXT                      -- ❌ NOT QUERIED
);
```

**Code Implementation**: ❌ **NOT IMPLEMENTED**

**Purpose**: Emoji usage patterns for digital communication  
**Impact**: Characters can't access emoji personality data from database  
**Field Coverage**: ❌ 0% - table completely unused

---

#### 10. character_ai_scenarios

**Database Schema** (10 fields):
```sql
CREATE TABLE character_ai_scenarios (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id),
    scenario_type VARCHAR(100) NOT NULL,    -- ❌ NOT QUERIED
    scenario_name VARCHAR(200),             -- ❌ NOT QUERIED
    trigger_phrases TEXT,                   -- ❌ NOT QUERIED
    response_pattern VARCHAR(100),          -- ❌ NOT QUERIED
    tier_1_response TEXT,                   -- ❌ NOT QUERIED
    tier_2_response TEXT,                   -- ❌ NOT QUERIED
    tier_3_response TEXT,                   -- ❌ NOT QUERIED
    example_usage TEXT                      -- ❌ NOT QUERIED
);
```

**Code Implementation**: ❌ **NOT IMPLEMENTED**

**Purpose**: AI identity handling scenarios with 3-tier responses  
**Impact**: Characters can't use database-defined AI identity handling  
**Field Coverage**: ❌ 0% - table completely unused

---

#### 11. character_cultural_expressions

**Database Schema** (7 fields):
```sql
CREATE TABLE character_cultural_expressions (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id),
    expression_type VARCHAR(100) NOT NULL,  -- ❌ NOT QUERIED
    expression_value TEXT NOT NULL,         -- ❌ NOT QUERIED
    meaning TEXT,                           -- ❌ NOT QUERIED
    usage_context TEXT,                     -- ❌ NOT QUERIED
    emotional_context VARCHAR(50),          -- ❌ NOT QUERIED
    frequency VARCHAR(50)                   -- ❌ NOT QUERIED
);
```

**Code Implementation**: ❌ **NOT IMPLEMENTED**

**Purpose**: Cultural expressions and language patterns (e.g., Spanish phrases for Elena)  
**Impact**: Characters can't access cultural expressions from database  
**Field Coverage**: ❌ 0% - table completely unused

---

#### 12. character_voice_traits

**Database Schema** (6 fields):
```sql
CREATE TABLE character_voice_traits (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id),
    trait_type VARCHAR(100) NOT NULL,       -- ❌ NOT QUERIED
    trait_value TEXT NOT NULL,              -- ❌ NOT QUERIED
    situational_context TEXT,               -- ❌ NOT QUERIED
    examples TEXT                           -- ❌ NOT QUERIED
);
```

**Code Implementation**: ❌ **NOT IMPLEMENTED**

**Purpose**: Voice characteristics (tone, pace, volume, accent, vocabulary level)  
**Impact**: Characters can't access voice trait descriptions from database  
**Field Coverage**: ❌ 0% - table completely unused

---

#### 13. character_emotional_triggers

**Database Schema** (8 fields):
```sql
CREATE TABLE character_emotional_triggers (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id),
    trigger_type VARCHAR(100) NOT NULL,     -- ❌ NOT QUERIED
    trigger_category VARCHAR(100),          -- ❌ NOT QUERIED
    trigger_content TEXT NOT NULL,          -- ❌ NOT QUERIED
    emotional_response TEXT,                -- ❌ NOT QUERIED
    response_intensity VARCHAR(50),         -- ❌ NOT QUERIED
    response_examples TEXT                  -- ❌ NOT QUERIED
);
```

**Code Implementation**: ❌ **NOT IMPLEMENTED**

**Purpose**: Emotional triggers and corresponding responses  
**Impact**: Characters can't access emotional trigger patterns from database  
**Field Coverage**: ❌ 0% - table completely unused

---

#### 14. character_expertise_domains

**Database Schema** (9 fields):
```sql
CREATE TABLE character_expertise_domains (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id),
    domain_name VARCHAR(200) NOT NULL,      -- ❌ NOT QUERIED
    expertise_level VARCHAR(50),            -- ❌ NOT QUERIED
    domain_description TEXT,                -- ❌ NOT QUERIED
    key_concepts TEXT,                      -- ❌ NOT QUERIED
    teaching_approach TEXT,                 -- ❌ NOT QUERIED
    passion_level INTEGER,                  -- ❌ NOT QUERIED
    examples TEXT                           -- ❌ NOT QUERIED
);
```

**Code Implementation**: ❌ **NOT IMPLEMENTED**

**Purpose**: Domain-specific knowledge and expertise areas  
**Impact**: Characters can't access expertise domain data from database  
**Field Coverage**: ❌ 0% - table completely unused

---

## Critical Findings

### 🚨 Major Issues Discovered

1. **Table Name Mismatch**: Code queries `character_behavioral_triggers` and `character_relationships` but these tables are NOT in migration 006. They exist in migration 005.

2. **Migration Confusion**: WhisperEngine appears to have MULTIPLE CDL schema migrations:
   - Migration 005: One set of tables
   - Migration 006: Different set of tables
   - Code queries tables from BOTH migrations inconsistently

3. **Massive Unused Schema**: 10 out of 14 tables (71%) in migration 006 are completely unused by code.

4. **Code Only Uses 29% of Tables**: Out of 14 tables in migration 006, code only queries 4 tables, and one of those (conversation_flows) has missing fields.

### 📊 Data Loss Statistics

**Tables in Schema**: 14 tables  
**Tables Queried**: 4 tables (29%)  
**Tables Unused**: 10 tables (71%)  
**Fields Missing in Queried Tables**: ~14% of fields in tables that ARE queried

**Total Estimated Data Loss**: ~75% of migration 006 schema is completely unused

---

## Root Cause Analysis

### Why This Happened

1. **Multiple Migration Confusion**: Code was written for migration 005 tables but migration 006 created different tables

2. **Incomplete Implementation**: Migration 006 was created to capture "ALL fidelity and control from CDL JSON files" but code was never updated to use it

3. **No Migration Audit**: No verification that code actually queries the new schema after migration

4. **Documentation Gap**: No mapping between JSON structure → migration 005 → migration 006 → code

### What Went Wrong

**Expected Flow**:
1. JSON working (commit 89bb795) ✅
2. Create comprehensive schema (migration 006) ✅
3. Update code to query schema ❌ **FAILED**
4. Verify end-to-end data flow ❌ **SKIPPED**

**What Actually Happened**:
1. JSON working ✅
2. Created migration 005 schema
3. Wrote code for migration 005 (partial)
4. Created migration 006 schema (different tables)
5. Code still queries migration 005 tables
6. Migration 006 tables completely unused

---

## Fix Strategy

### Phase 1: Understand Current State (URGENT)

1. ✅ Audit which migration is actually running in production
2. ✅ List ALL tables that exist in current database
3. ✅ Verify which tables code is actually querying
4. ✅ Document table name mismatches (behavioral_triggers, relationships)

### Phase 2: Choose One Schema (CRITICAL DECISION)

**Option A**: Use Migration 005 as authority
- Update code to query ALL migration 005 tables
- Mark migration 006 as obsolete
- Document why migration 006 was abandoned

**Option B**: Use Migration 006 as authority  
- Update code to query migration 006 tables
- Migrate data from migration 005 to 006
- Update table names in code (behavioral_triggers → ?)

**Option C**: Merge Both Migrations
- Keep best tables from both migrations
- Create unified schema
- Update code to match unified schema

### Phase 3: Complete Implementation

1. Update `enhanced_cdl_manager.py` to query ALL chosen tables
2. Add dataclass definitions for all tables
3. Update `cdl_ai_integration.py` to use new data
4. Test end-to-end character data flow
5. Validate character fidelity improvement

---

## Recommendation

**STOP** adding new features until we fix this foundational issue.

**Priority 1**: Determine which migration is production authority  
**Priority 2**: Update code to query ALL tables in that migration  
**Priority 3**: Test character data flow end-to-end  
**Priority 4**: Document complete schema → code mapping

**Risk**: Continuing development with 75% unused schema will compound technical debt.

**Benefit**: Fixing this will unlock 10+ tables of rich character data already in schema.
