# CDL System Fix: Complete Action Plan

**Date**: October 11, 2025  
**Status**: READY TO EXECUTE  
**Priority**: CRITICAL - Foundation issue blocking character fidelity

---

## 🎯 Core Principles (ABSOLUTE REQUIREMENTS)

### 1. **Schema is Authority**
- ✅ Current schema in database is CORRECT
- ✅ NO schema changes unless absolutely necessary
- ✅ NO "CREATE TABLE IF NOT EXISTS" that breaks existing schema
- ✅ Code must adapt to schema, not vice versa

### 2. **NO JSON Anywhere**
- ❌ NO JSONB fields
- ❌ NO JSON embedded in TEXT fields
- ❌ NO JSON parsing in application code
- ✅ Pure RDBMS relational structure ONLY
- ✅ Arrays should use proper array types (TEXT[]) not JSON

### 3. **Full Fidelity Imports**
- ✅ Import ALL data from JSON files
- ✅ NO truncated fields
- ✅ NO data loss during import
- ✅ Semantic mapping: JSON structure → proper RDBMS tables
- ✅ Validate import completeness

### 4. **Code Follows Schema**
- ✅ `enhanced_cdl_manager.py` must query ALL schema fields
- ✅ Dataclasses must match schema exactly
- ✅ `cdl_ai_integration.py` must use all available data
- ✅ NO hardcoded table creation in code

---

## 📋 Phase 1: Schema Audit (COMPLETE)

**Status**: ✅ DONE

**Findings**:
- Database has 37 character_* tables in production
- Migration 006 created 14 comprehensive tables
- Schema is well-designed with proper relational structure
- NO JSONB fields needed - schema has proper columns

**Documentation Created**:
- ✅ `CDL_FIELD_LOSS_ROOT_CAUSE_ANALYSIS.md`
- ✅ `CDL_SCHEMA_VS_CODE_FIELD_COMPARISON.md`
- ✅ `CDL_SCHEMA_AUTHORITY.md` (existing)

---

## 📋 Phase 2: Code Audit - Find Missing Queries

**Status**: ✅ DONE

**Current Code Coverage**:
- `enhanced_cdl_manager.py` queries **4 tables** out of 14 in migration 006
- **10 tables completely unused** (71% of schema)
- Even the 4 queried tables have missing fields

**Tables Code Currently Uses**:
1. ✅ `character_speech_patterns` (100% coverage)
2. ⚠️ `character_conversation_flows` (86% coverage - missing `context`)
3. ✅ `character_behavioral_triggers` (appears complete)
4. ✅ `character_relationships` (appears complete)

**Tables Code Completely Ignores** (need implementation):
1. ❌ `character_response_guidelines`
2. ❌ `character_conversation_directives`
3. ❌ `character_message_triggers`
4. ❌ `character_response_modes`
5. ❌ `character_emoji_patterns`
6. ❌ `character_ai_scenarios`
7. ❌ `character_cultural_expressions`
8. ❌ `character_voice_traits`
9. ❌ `character_emotional_triggers`
10. ❌ `character_expertise_domains`

---

## 📋 Phase 3: Check for Schema Violations (NEXT)

**Goal**: Find any JSONB fields or JSON text that violates RDBMS purity

**Tasks**:
1. [ ] Audit schema for JSONB columns
2. [ ] Audit schema for TEXT columns containing JSON
3. [ ] Identify tables that need schema changes to eliminate JSON
4. [ ] Document required schema fixes (if any)

**Command to Run**:
```bash
# Find all JSONB columns
docker exec postgres psql -U whisperengine -d whisperengine -c "
SELECT table_name, column_name, data_type 
FROM information_schema.columns 
WHERE table_schema = 'public' 
  AND table_name LIKE 'character_%' 
  AND data_type = 'jsonb'
ORDER BY table_name, column_name;
"

# Find TEXT columns that might contain JSON
docker exec postgres psql -U whisperengine -d whisperengine -c "
SELECT table_name, column_name, data_type 
FROM information_schema.columns 
WHERE table_schema = 'public' 
  AND table_name LIKE 'character_%' 
  AND data_type = 'text'
  AND column_name LIKE '%json%'
ORDER BY table_name, column_name;
"
```

---

## 📋 Phase 4: Fix Import Scripts for Full Fidelity

**Goal**: Ensure import scripts map JSON → RDBMS with zero data loss

**Current Import Scripts** (need audit):
- `batch_import_characters.py`
- `comprehensive_cdl_import.py`
- `comprehensive_character_import.py`
- `import_characters_to_clean_schema.py`

**Requirements for Import Scripts**:
1. ✅ Import ALL JSON fields
2. ✅ Map JSON structure semantically to proper tables
3. ✅ NO field truncation
4. ✅ NO JSON embedding in TEXT fields
5. ✅ Validate import completeness
6. ✅ Report any unmapped JSON data

**Tasks**:
1. [ ] Audit each import script for JSON → RDBMS mapping
2. [ ] Identify missing mappings (JSON fields not imported)
3. [ ] Fix import scripts to achieve 100% fidelity
4. [ ] Add validation: compare JSON vs DB after import
5. [ ] Create import verification script

**Example Semantic Mapping**:
```python
# ❌ WRONG: Embedding JSON in TEXT
character_data = {
    'voice_data': json.dumps(voice_dict)  # BAD!
}

# ✅ CORRECT: Proper relational structure
for trait_type, trait_value in voice_dict.items():
    await conn.execute("""
        INSERT INTO character_voice_traits 
        (character_id, trait_type, trait_value, situational_context, examples)
        VALUES ($1, $2, $3, $4, $5)
    """, character_id, trait_type, trait_value, context, examples)
```

---

## 📋 Phase 5: Fix enhanced_cdl_manager.py (CRITICAL)

**Goal**: Update ALL query methods to retrieve complete schema fields

### Step 5.1: Fix Existing Query Methods

**Fix `get_conversation_flows()`** - Add missing `context` field:
```python
# BEFORE (missing context)
rows = await conn.fetch("""
    SELECT flow_type, flow_name, energy_level, 
           approach_description, transition_style, priority
    FROM character_conversation_flows 
    WHERE character_id = $1
    ORDER BY priority DESC
""", character_id)

# AFTER (complete)
rows = await conn.fetch("""
    SELECT flow_type, flow_name, energy_level, 
           approach_description, transition_style, priority, context
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
    context: Optional[str] = None  # ADD THIS
```

### Step 5.2: Implement Missing Query Methods

**Add 10 new query methods for unused tables**:

1. `get_response_guidelines(character_name: str) -> List[ResponseGuideline]`
2. `get_conversation_directives(flow_id: int) -> List[ConversationDirective]`
3. `get_message_triggers(character_name: str) -> List[MessageTrigger]`
4. `get_response_modes(character_name: str) -> List[ResponseMode]`
5. `get_emoji_patterns(character_name: str) -> List[EmojiPattern]`
6. `get_ai_scenarios(character_name: str) -> List[AIScenario]`
7. `get_cultural_expressions(character_name: str) -> List[CulturalExpression]`
8. `get_voice_traits(character_name: str) -> List[VoiceTrait]`
9. `get_emotional_triggers(character_name: str) -> List[EmotionalTrigger]`
10. `get_expertise_domains(character_name: str) -> List[ExpertiseDomain]`

**Requirements**:
- ✅ Query ALL fields from schema (no missing columns)
- ✅ Dataclasses match schema exactly
- ✅ NO hardcoded defaults that differ from schema
- ✅ Proper error handling
- ✅ Use existing connection pool

---

## 📋 Phase 6: Update cdl_ai_integration.py

**Goal**: Use newly available data in prompt building

**Tasks**:
1. [ ] Update `_build_unified_prompt()` to call new query methods
2. [ ] Integrate response guidelines into prompt structure
3. [ ] Use message triggers for mode detection
4. [ ] Apply response modes to prompt formatting
5. [ ] Include emoji patterns in digital communication
6. [ ] Use AI scenarios for identity handling
7. [ ] Include cultural expressions in character voice
8. [ ] Apply voice traits to communication style
9. [ ] Use emotional triggers for empathy responses
10. [ ] Include expertise domains in knowledge sections

**Example Integration**:
```python
# Get response guidelines
guidelines = await enhanced_cdl_manager.get_response_guidelines(character_name)
critical_guidelines = [g for g in guidelines if g.is_critical]
prompt += "\n\n🎯 CRITICAL RESPONSE GUIDELINES:\n"
for guideline in critical_guidelines:
    prompt += f"- {guideline.guideline_content}\n"

# Get emoji patterns
emoji_patterns = await enhanced_cdl_manager.get_emoji_patterns(character_name)
high_excitement = [p for p in emoji_patterns if p.frequency == 'high']
prompt += "\n\n😊 EMOJI USAGE:\n"
for pattern in high_excitement:
    prompt += f"- {pattern.pattern_name}: {pattern.emoji_sequence}\n"
```

---

## 📋 Phase 7: Validation & Testing

**Goal**: Verify complete data flow from JSON → DB → Code → Prompt

**Tasks**:
1. [ ] Create validation script comparing JSON vs DB
2. [ ] Test character import completeness
3. [ ] Verify all schema fields are queryable
4. [ ] Test prompt generation with all data sources
5. [ ] Compare character responses before/after fix
6. [ ] Document character fidelity improvements

**Validation Script Requirements**:
```python
async def validate_import_completeness(character_name: str, json_path: str):
    """
    Compare JSON file vs database to ensure 100% import fidelity
    
    Returns:
    - fields_in_json: count
    - fields_in_db: count
    - missing_fields: list
    - extra_fields: list
    - fidelity_score: percentage
    """
    pass
```

---

## 🚫 Anti-Patterns to AVOID

### ❌ Don't Do This:

```python
# ❌ Creating tables in code
CREATE TABLE IF NOT EXISTS character_new_table (...)

# ❌ Using JSONB fields
character_data JSONB

# ❌ Embedding JSON in TEXT
metadata TEXT  # containing JSON.stringify()

# ❌ Partial field queries
SELECT id, name FROM character_relationships  # Missing other fields

# ❌ Hardcoded defaults that differ from schema
@dataclass
class Thing:
    priority: int = 99  # Schema says DEFAULT 50

# ❌ Truncating data during import
if len(description) > 1000:
    description = description[:1000]  # Data loss!
```

### ✅ Do This Instead:

```python
# ✅ Query existing schema
await conn.fetch("SELECT * FROM character_relationships WHERE ...")

# ✅ Pure relational structure
INSERT INTO character_voice_traits (trait_type, trait_value, ...)

# ✅ Full field queries matching schema
SELECT related_entity, relationship_type, relationship_strength, 
       description, status, communication_style, connection_nature, recognition_pattern
FROM character_relationships

# ✅ Dataclass matches schema defaults
@dataclass
class Thing:
    priority: int = 50  # Matches schema DEFAULT

# ✅ Import all data with validation
if len(description) > column_max_length:
    raise ValueError(f"Description too long: {len(description)} > {column_max_length}")
```

---

## 📊 Success Metrics

### How We'll Know It's Fixed:

1. **Schema Coverage**: 100% of schema tables have query methods
2. **Field Coverage**: 100% of schema fields are in SELECT statements
3. **Import Fidelity**: 100% of JSON data imported to database
4. **Code Usage**: All 14 migration 006 tables used by `enhanced_cdl_manager.py`
5. **Prompt Integration**: All data sources appear in character prompts
6. **Character Quality**: Measurable improvement in character response fidelity

### Key Metrics:

**Before Fix**:
- Tables queried: 4/14 (29%)
- Field coverage: ~85% (missing context, etc.)
- Unused tables: 10 (71%)
- Import fidelity: Unknown (not validated)

**After Fix** (Target):
- Tables queried: 14/14 (100%)
- Field coverage: 100% (all schema fields)
- Unused tables: 0 (0%)
- Import fidelity: 100% (validated)

---

## 🎯 Execution Order

### Priority 1: Foundation (URGENT)
1. ✅ Phase 1: Schema Audit (COMPLETE)
2. ✅ Phase 2: Code Audit (COMPLETE)
3. ⏭️ Phase 3: Check for Schema Violations (NEXT)

### Priority 2: Fix Data Flow (HIGH)
4. Phase 4: Fix Import Scripts
5. Phase 5: Fix enhanced_cdl_manager.py

### Priority 3: Integration (MEDIUM)
6. Phase 6: Update cdl_ai_integration.py
7. Phase 7: Validation & Testing

---

## 📝 Documentation Updates Needed

1. Update `CDL_SCHEMA_AUTHORITY.md` with:
   - Complete field lists for all 37 tables
   - Dataclass definitions matching schema
   - Import mapping (JSON → table.column)

2. Create `CDL_IMPORT_VALIDATION.md`:
   - Import validation checklist
   - JSON → DB field mapping reference
   - Completeness verification procedures

3. Update `.github/copilot-instructions.md`:
   - NO JSON in RDBMS (JSONB forbidden)
   - Schema is authority (no CREATE IF NOT EXISTS)
   - Full fidelity imports required
   - Code follows schema, not vice versa

---

## 🚀 Ready to Execute

**Current Status**: Analysis complete, action plan defined  
**Next Step**: Phase 3 - Check for schema violations  
**Blocker**: None  
**ETA**: 1-2 days for complete fix

**User Approval Required**: Schema change recommendations (if any JSONB found)  
**User Decision**: Which import script to use as canonical?
