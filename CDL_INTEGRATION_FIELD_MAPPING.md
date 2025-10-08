# CDL Integration Field Mapping
**WhisperEngine CDL Database Schema to Integration Code Mapping**
**Date**: October 8, 2025

## Purpose
This document maps all Character object field accesses in `cdl_ai_integration.py` to their corresponding database tables/columns, ensuring all 10 characters have complete data for runtime operation.

---

## Character Object Structure (from parser.py)

The Character class from `src/characters/models/character.py` has these main sections:
- `character.metadata` - Character metadata (version, tags, created_date)
- `character.identity` - Core identity (name, occupation, description, appearance, voice)
- `character.personality` - Personality traits (Big Five, life phases)
- `character.backstory` - Background and history
- `character.current_life` - Current situation (projects, routine, occupation details)
- `character.communication` - Communication style and patterns

---

## Field Access Mapping (cdl_ai_integration.py → Database)

### **CRITICAL FIELDS** (Used in every prompt generation)

| Field Access | Usage Location | Database Table | Database Column | Status |
|-------------|----------------|----------------|----------------|--------|
| `character.identity.name` | Lines 92, 196, 204, 337, 383, etc. (15+ uses) | `characters` | `name` | ✅ All 10 characters |
| `character.identity.occupation` | Lines 196, 983 | `characters` | `occupation` | ✅ All 10 characters |
| `character.identity.description` | Lines 199-200 | `characters` | `description` | ✅ All 10 characters |
| `character.personality.big_five` | Lines 225-226 | `personality_traits` | `trait_name`, `trait_value`, `intensity` | ✅ All 10 characters (5 traits each) |
| `character.allow_full_roleplay_immersion` | Lines 869, 871 | `characters` | `allow_full_roleplay` | ✅ All 10 characters |

### **PERSONAL KNOWLEDGE FIELDS** (Used in contextual extraction)

These fields are queried in `_extract_cdl_personal_knowledge_sections()` method (lines 1059-1149):

| Field Access | Trigger Keywords | Database Mapping | Status |
|-------------|-----------------|-----------------|--------|
| `character.relationships` | 'relationship', 'partner', 'dating', 'married', 'family' | **NOT IMPLEMENTED** - Character object doesn't expose | ⚠️ NEEDS MAPPING |
| `character.relationships.status` | Same | N/A - needs implementation | ⚠️ NEEDS IMPLEMENTATION |
| `character.relationships.important_relationships` | Same | `character_relationships` table exists | ⚠️ NEEDS MAPPING |
| `character.current_life` | Multiple contexts | **NOT IMPLEMENTED** - Character object doesn't expose | ⚠️ NEEDS MAPPING |
| `character.current_life.family` | 'family' context | N/A - no direct field | ⚠️ NEEDS MAPPING |
| `character.current_life.occupation_details` | 'work', 'job', 'career' | N/A - no direct field | ⚠️ NEEDS MAPPING |
| `character.current_life.daily_routine` | 'work', 'interest' contexts | N/A - needs implementation | ⚠️ NEEDS MAPPING |
| `character.current_life.daily_routine.work_schedule` | 'work' context | N/A | ⚠️ NEEDS MAPPING |
| `character.current_life.daily_routine.weekend_activities` | 'hobby', 'interest' | N/A | ⚠️ NEEDS MAPPING |
| `character.current_life.daily_routine.evening_routine` | 'interest', 'free time' | N/A | ⚠️ NEEDS MAPPING |
| `character.backstory` | Multiple contexts | **NOT IMPLEMENTED** - Character object doesn't expose | ⚠️ NEEDS MAPPING |
| `character.backstory.family_background` | 'family', 'parents' | `character_background` (category='personal') | ⚠️ NEEDS MAPPING |
| `character.backstory.formative_experiences` | 'family', 'career' | `character_background` (importance_level) | ⚠️ NEEDS MAPPING |
| `character.backstory.career_background` | 'work', 'career' | `character_background` (category='career') | ⚠️ NEEDS MAPPING |
| `character.skills_and_expertise` | 'work', 'career', 'education' | **NOT IMPLEMENTED** - Character object doesn't expose | ⚠️ NEEDS MAPPING |
| `character.skills_and_expertise.education` | Same | `character_background` (category='education') | ⚠️ NEEDS MAPPING |
| `character.skills_and_expertise.professional_skills` | Same | `character_abilities` (category='professional') | ⚠️ NEEDS MAPPING |
| `character.interests_and_hobbies` | 'hobby', 'interest', 'fun' | **NOT IMPLEMENTED** - Character object doesn't expose | ⚠️ NEEDS MAPPING |

### **COMMUNICATION PATTERN FIELDS** (Used in scenario detection)

| Field Access | Usage | Database Mapping | Status |
|-------------|-------|-----------------|--------|
| `character.communication.message_pattern_triggers` | Line 1155+ | **HARDCODED** in SimpleCDLManager | ⚠️ Should use `character_message_triggers` |

---

## Problem Analysis

### **ISSUE 1: SimpleCharacter Object is Too Simple**

The `SimpleCDLManager.get_character_object()` (lines 200-276) creates a **minimal** Character object with only:
- `character.identity` (name, occupation, description, archetype)
- `character.personality` (big_five only)
- `character.communication` (hardcoded message_pattern_triggers)
- `character.allow_full_roleplay_immersion`

**Missing nested sections**:
- ❌ `character.relationships`
- ❌ `character.backstory`
- ❌ `character.current_life`
- ❌ `character.skills_and_expertise`
- ❌ `character.interests_and_hobbies`
- ❌ `character.metadata`
- ❌ `character.appearance`
- ❌ `character.key_memories`
- ❌ `character.abilities`
- ❌ `character.essence`

### **ISSUE 2: Enhanced Manager Queries Database But Doesn't Populate Character Object**

The `EnhancedCDLManager` (lines 1-713) queries **24 database tables**:
- ✅ Queries `character_relationships` table
- ✅ Queries `character_background` table  
- ✅ Queries `character_abilities` table
- ✅ Queries `character_memories` table
- ✅ Queries `character_appearance` table
- ✅ Queries `character_communication_patterns` table
- ✅ Queries `character_message_triggers` table
- ✅ Queries many more...

**BUT**: Returns flat dictionary, doesn't populate Character object structure!

### **ISSUE 3: Integration Code Expects Nested Object Structure**

The `cdl_ai_integration.py` code uses **hasattr() checks** and **nested attribute access**:
```python
if hasattr(character, 'backstory') and character.backstory:
    backstory = character.backstory
    if hasattr(backstory, 'family_background') and backstory.family_background:
        personal_sections.append(f"Family Background: {backstory.family_background}")
```

This expects a **hierarchical object structure**, not a flat dictionary.

---

## Solution Strategy

### **Option A: Enhance SimpleCDLManager to Create Complete Character Object**

**Approach**: Extend `SimpleCDLManager._create_*_object()` methods to populate ALL Character sections from enhanced manager data.

**Changes Needed**:
1. Add `_create_backstory_object()` method
2. Add `_create_current_life_object()` method  
3. Add `_create_relationships_object()` method
4. Add `_create_skills_and_expertise_object()` method
5. Add `_create_interests_and_hobbies_object()` method
6. Add `_create_metadata_object()` method
7. Add `_create_appearance_object()` method

**Pros**:
- Integration code works without changes
- Object-oriented structure maintained
- Type safety and IDE autocomplete

**Cons**:
- Significant development effort (7 new object builder methods)
- Potential data structure mismatches
- Complexity in nested object creation

### **Option B: Modify Integration Code to Access Dictionary Data**

**Approach**: Change `cdl_ai_integration.py` to check for dictionary structure vs object structure.

**Changes Needed**:
1. Replace `hasattr(character, 'backstory')` with dictionary checks
2. Change `character.backstory.family_background` to `character.get('backstory', {}).get('family_background')`

**Pros**:
- Enhanced manager already returns complete data
- Less code to write
- Flexible data access

**Cons**:
- Loses type safety
- Less IDE support
- Mixed data access patterns

### **Option C: RECOMMENDED - Hybrid Approach**

**Approach**: 
1. Keep SimpleCDLManager creating basic object structure
2. Add **property methods** that lazily access enhanced manager data
3. Integration code remains unchanged

**Example**:
```python
class SimpleCharacter:
    def __init__(self, data, enhanced_data):
        self.identity = self._create_identity_object(data.get('identity', {}))
        self.personality = self._create_personality_object(data.get('personality', {}))
        self._enhanced_data = enhanced_data  # Store rich data
        
    @property
    def backstory(self):
        """Lazy-load backstory from enhanced data"""
        if not hasattr(self, '_backstory'):
            self._backstory = self._create_backstory_from_enhanced()
        return self._backstory
    
    @property
    def relationships(self):
        """Lazy-load relationships from enhanced data"""
        if not hasattr(self, '_relationships'):
            self._relationships = self._create_relationships_from_enhanced()
        return self._relationships
```

**Pros**:
- ✅ Integration code unchanged
- ✅ Lazy loading = performance optimization
- ✅ Enhanced manager data fully utilized
- ✅ Type-safe object structure
- ✅ Minimal code changes

**Cons**:
- Requires careful property design
- Still need object builder methods (but simpler)

---

## Database Table Coverage

### **Tables Currently Queried by Enhanced Manager**:

✅ **Core Tables** (returned in backward-compatible structure):
- `characters` → `identity` section
- `personality_traits` → `personality.big_five` section
- `communication_styles` → `communication_style` section
- `character_values` → `values_and_beliefs` section

✅ **Rich Data Tables** (returned in `rich_data` dict):
- `character_metadata` → `metadata` dict
- `character_appearance` → `appearance` dict
- `character_background` → `background` dict
- `character_relationships` → `relationships` list
- `character_memories` → `key_memories` list
- `character_abilities` → `abilities` dict
- `character_communication_patterns` → `communication_patterns` dict
- `character_behavioral_triggers` → `behavioral_triggers` list
- `character_essence` → `essence` dict
- `character_instructions` → `custom_instructions` dict

✅ **Additional Tables with Methods**:
- `character_response_guidelines` → `get_response_guidelines()`
- `character_conversation_flows` → `get_conversation_flows()`
- `character_message_triggers` → `get_message_triggers()`
- `character_speech_patterns` → `get_speech_patterns()`

### **Tables NOT Currently Queried**:
❌ `character_attributes` (fears, dreams, quirks, beliefs, directives)
❌ `character_communication_triggers` 
❌ `character_vocabulary_usage`
❌ `character_emoji_patterns`
❌ `character_interests` (newly populated - 50 records!)
❌ `character_expertise_domains` (newly populated - 10 records!)
❌ `character_roleplay_config`
❌ `character_roleplay_scenarios_v2`

---

## Action Items

### **PHASE 1: Verify Data Completeness** ✅ (Current Task)

1. ✅ Map all field accesses in integration code
2. ⏳ Query database to verify all 10 characters have required fields
3. ⏳ Identify gaps in data coverage

### **PHASE 2: Fix Character Object Structure**

1. Choose approach (RECOMMENDED: Option C - Hybrid)
2. Implement property methods for missing sections:
   - `character.backstory`
   - `character.current_life`
   - `character.relationships`
   - `character.skills_and_expertise`
   - `character.interests_and_hobbies`
   - `character.metadata`
   - `character.appearance`

3. Update SimpleCDLManager to pass enhanced data to SimpleCharacter
4. Test all 10 characters load correctly

### **PHASE 3: Fill Data Gaps**

1. Generate any missing personal knowledge data
2. Ensure all characters have backstory, relationships, interests
3. Validate complete field coverage for all 10 characters

### **PHASE 4: Integration Testing**

1. Test personal knowledge extraction with real queries
2. Verify relationship/family/career questions return proper context
3. Validate all CDL features working end-to-end

---

## Database Query to Verify Character Data Coverage

```sql
-- Check which characters have data in each table
SELECT 
    c.name as character_name,
    COUNT(DISTINCT pa.id) as personality_traits,
    COUNT(DISTINCT cs.id) as communication_styles,
    COUNT(DISTINCT cv.id) as values,
    COUNT(DISTINCT cb.id) as background_entries,
    COUNT(DISTINCT cr.id) as relationships,
    COUNT(DISTINCT ca.id) as abilities,
    COUNT(DISTINCT cm.id) as memories,
    COUNT(DISTINCT cap.id) as appearance,
    COUNT(DISTINCT ci.id) as interests,
    COUNT(DISTINCT ced.id) as expertise_domains,
    COUNT(DISTINCT cep.id) as emoji_patterns,
    COUNT(DISTINCT csp.id) as speech_patterns,
    COUNT(DISTINCT cmt.id) as message_triggers
FROM characters c
LEFT JOIN personality_traits pa ON c.id = pa.character_id
LEFT JOIN communication_styles cs ON c.id = cs.character_id
LEFT JOIN character_values cv ON c.id = cv.character_id
LEFT JOIN character_background cb ON c.id = cb.character_id
LEFT JOIN character_relationships cr ON c.id = cr.character_id
LEFT JOIN character_abilities ca ON c.id = ca.character_id
LEFT JOIN character_memories cm ON c.id = cm.character_id
LEFT JOIN character_appearance cap ON c.id = cap.character_id
LEFT JOIN character_interests ci ON c.id = ci.character_id
LEFT JOIN character_expertise_domains ced ON c.id = ced.character_id
LEFT JOIN character_emoji_patterns cep ON c.id = cep.character_id
LEFT JOIN character_speech_patterns csp ON c.id = csp.character_id
LEFT JOIN character_message_triggers cmt ON c.id = cmt.character_id
GROUP BY c.name
ORDER BY c.name;
```

---

## Summary

**Current State**:
- ✅ Database has 664 total CDL records across 10 characters
- ✅ Enhanced manager queries 24 tables comprehensively
- ❌ SimpleCDLManager creates minimal Character object (missing 8+ sections)
- ❌ Integration code expects nested object structure that doesn't exist
- ❌ Personal knowledge extraction fails due to missing object properties

**Root Cause**:
SimpleCharacter object in `simple_cdl_manager.py` doesn't expose rich data from enhanced manager. Integration code does `hasattr()` checks that fail, causing personal knowledge extraction to return empty strings.

**Recommended Fix**:
Implement **Option C (Hybrid Approach)** - Add lazy-loading property methods to SimpleCharacter that construct nested objects from enhanced manager data. This maintains API compatibility while utilizing all database data.

**Next Step**:
Run database query to verify data coverage, then implement property methods for missing Character object sections.
