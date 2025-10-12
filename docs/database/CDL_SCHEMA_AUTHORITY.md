# CDL Schema Authority - Single Source of Truth

**Date**: October 11, 2025  
**Purpose**: Define the AUTHORITATIVE CDL database schema that is STABLE and does NOT drift with JSON changes

## Core Principle

**THE SCHEMA IS THE AUTHORITY. JSON ADAPTS TO IT.**

- ✅ **Schema is stable** - Tables/fields don't change based on JSON quirks
- ✅ **JSON is a guide** - Tells us what semantic information to extract
- ✅ **Import scripts are mappers** - Intelligently map messy JSON to clean schema
- ❌ **Never modify schema for JSON** - This creates drift!

## Current Working Schema (40 Tables)

### **CORE TABLES** (CDL Integration Uses These)

#### 1. **character_speech_patterns** ✅ ACTIVE (78 records)
**Purpose**: Signature expressions, catchphrases, vocabulary preferences  
**Fields**:
- `pattern_type` VARCHAR(100) - 'signature_expression', 'preferred_word', 'avoided_word', 'sentence_structure', 'voice_tone'
- `pattern_value` TEXT - The actual phrase/word/pattern
- `usage_frequency` VARCHAR(50) - 'always', 'often', 'sometimes'
- `context` VARCHAR(100) - When to use it
- `priority` INTEGER DEFAULT 50 - Importance ranking (1-100)

**Used by**: `enhanced_cdl_manager.get_speech_patterns()` → `cdl_ai_integration.py` lines 751-768  
**Prompt section**: "💬 SIGNATURE EXPRESSIONS" with character catchphrases

#### 2. **character_conversation_flows** ✅ ACTIVE (12 records)
**Purpose**: Conversation mode guidance (romantic, technical, casual, etc)  
**Fields**:
- `flow_type` VARCHAR(200) - Type identifier ('romantic_interest', 'technical_discussion')
- `flow_name` VARCHAR(200) - Display name
- `energy_level` VARCHAR(200) - 'passionate', 'warm', 'calm'
- `approach_description` TEXT - How to handle this conversation type
- `transition_style` TEXT - How to transition in/out
- `priority` INTEGER DEFAULT 50 - Flow importance
- `context` TEXT - Additional context

**Used by**: `enhanced_cdl_manager.get_conversation_flows()` → `cdl_ai_integration.py` lines 786-795  
**Prompt section**: "🗣️ CONVERSATION FLOW GUIDANCE"

#### 3. **character_behavioral_triggers** ✅ ACTIVE (36 records)
**Purpose**: Topic/emotion triggers and response patterns  
**Fields**:
- `trigger_type` VARCHAR(50) - 'topic', 'emotion', 'situation', 'word'
- `trigger_value` VARCHAR(200) - The actual trigger (e.g., 'adventure_photography')
- `response_type` VARCHAR(50) - 'expertise_enthusiasm', 'protective_teaching', 'authentic_vulnerable'
- `response_description` TEXT - Detailed response guidance
- `intensity_level` INTEGER DEFAULT 5 - Response strength (1-10)

**Used by**: `enhanced_cdl_manager.get_behavioral_triggers()` → `cdl_ai_integration.py` lines 730-748  
**Prompt section**: "🎭 INTERACTION PATTERNS" grouped by trigger type  
**Ordering**: `ORDER BY intensity_level DESC, trigger_type` - High intensity first!

#### 4. **character_relationships** ✅ ACTIVE (6 records)
**Purpose**: Special relationships (e.g., Gabriel-Cynthia, romantic preferences)  
**Fields**:
- `related_entity` VARCHAR(200) - Name of person/entity
- `relationship_type` VARCHAR(50) - 'romantic_preference', 'family', 'colleague'
- `relationship_strength` INTEGER DEFAULT 5 - Importance (1-10)
- `description` TEXT - Relationship details
- `status` VARCHAR(20) DEFAULT 'active' - 'active', 'past', 'complicated'

**Used by**: `enhanced_cdl_manager.get_relationships()` → `cdl_ai_integration.py` lines 713-725  
**Prompt section**: "💕 RELATIONSHIP CONTEXT"  
**Filtering**: Only shows relationships with strength >= 5 (medium priority)

#### 5. **character_communication_patterns** ⚠️ LOW USE (1 record)
**Purpose**: Generic communication preferences  
**Fields**:
- `pattern_type` VARCHAR(50) - 'emoji', 'humor', 'technical'
- `pattern_name` VARCHAR(100)
- `pattern_value` TEXT
- `context` VARCHAR(100)
- `frequency` VARCHAR(20) DEFAULT 'regular'
- `description` TEXT

**Used by**: `enhanced_cdl_manager.get_communication_patterns()` lines 364-388  
**Status**: Mostly unused, overlaps with speech_patterns

### **SUPPORTING TABLES** (Background Information)

#### 6. **character_background** ✅ ACTIVE (21 records)
**Purpose**: Education, career history, formative experiences  
**Fields**:
- `category` VARCHAR(50) - 'education', 'career', 'personal', 'cultural'
- `period` VARCHAR(100) - 'childhood', 'university', '2010-2014'
- `title` TEXT
- `description` TEXT
- `date_range` TEXT
- `importance_level` INTEGER DEFAULT 5

#### 7. **character_appearance** ✅ ACTIVE (47 records)
**Purpose**: Physical/digital appearance details  
**Fields**:
- `category` VARCHAR(50) - 'physical', 'digital', 'voice'
- `attribute` VARCHAR(100) - 'height', 'hair_color', 'avatar_style'
- `value` TEXT
- `description` TEXT

#### 8. **character_abilities** ✅ ACTIVE (5 records)
**Purpose**: Skills, expertise, proficiency  
**Fields**:
- `category` VARCHAR(50) - 'professional', 'mystical', 'digital'
- `ability_name` VARCHAR(100)
- `proficiency_level` INTEGER DEFAULT 5
- `description` TEXT
- `development_method` TEXT
- `usage_frequency` VARCHAR(20) DEFAULT 'regular'

#### 9. **character_memories** ✅ ACTIVE (3 records)
**Purpose**: Formative memories and experiences  
**Fields**:
- `memory_type` VARCHAR(50) - 'formative', 'traumatic', 'joyful'
- `title` VARCHAR(200)
- `description` TEXT
- `emotional_impact` INTEGER DEFAULT 5
- `time_period` TEXT
- `importance_level` INTEGER DEFAULT 5
- `triggers` TEXT[] - Keywords that trigger this memory

### **SPECIALIZED TABLES** (Extended Features)

- `character_emoji_patterns` - Emoji usage by context
- `character_cultural_expressions` - Cultural/language patterns
- `character_voice_traits` - Voice characteristics
- `character_emotional_triggers` - Emotional response triggers
- `character_response_modes` - Technical/creative/brief modes
- `character_message_triggers` - Message pattern detection
- `character_ai_scenarios` - AI identity handling scenarios
- `character_essence` - Mystical/fantasy character essence
- `character_instructions` - Custom override instructions
- `character_values` - Core values and beliefs
- Plus 20+ more specialized tables

## What CDL Integration Actually Uses

**From `cdl_ai_integration.py` analysis:**

1. **Lines 713-725**: Retrieves `character_relationships`, filters by strength >= 5
2. **Lines 730-748**: Retrieves `character_behavioral_triggers`, groups by type, shows top 8 interactions
3. **Lines 751-768**: Retrieves `character_speech_patterns`, groups by pattern_type (signature_expression, preferred_word, avoided_word)
4. **Lines 786-795**: Retrieves `character_conversation_flows`, shows top 5 by priority

**Critical Fields Used**:
- `intensity_level` - Orders triggers by importance
- `priority` - Orders flows and speech patterns
- `relationship_strength` - Filters relationships
- `pattern_type` - Groups speech patterns into categories
- `trigger_type` - Groups behavioral triggers

## How Import Scripts Should Work

### **Correct Pattern** (Intelligent Mapping)

```python
# Jake's JSON has: identity.voice.catchphrases = ["Trust your instincts", ...]
# Map to: character_speech_patterns
for catchphrase in catchphrases:
    await conn.execute("""
        INSERT INTO character_speech_patterns 
        (character_id, pattern_type, pattern_value, usage_frequency, context, priority)
        VALUES ($1, $2, $3, $4, $5, $6)
    """,
        character_id,
        'signature_expression',  # Semantic mapping
        catchphrase,
        'often',                 # Inferred from context
        'general',               # Default context
        85                       # High priority for catchphrases
    )
```

### **Wrong Pattern** (Schema Drift)

```python
# ❌ NEVER DO THIS - Creates new table for JSON quirk
await conn.execute("""
    CREATE TABLE character_voice_catchphrases (...)
""")

# ❌ NEVER DO THIS - Adds field that doesn't exist in schema
await conn.execute("""
    ALTER TABLE character_speech_patterns ADD COLUMN voice_section TEXT
""")
```

## Validation Checklist

Before marking import complete, verify:

1. ✅ All INSERT statements use EXISTING tables only
2. ✅ All columns referenced exist in schema (check with `\d table_name`)
3. ✅ Priority/intensity values inferred semantically (high=85-95, medium=70-84, low=50-69)
4. ✅ Pattern types use standard values ('signature_expression', 'preferred_word', 'voice_tone')
5. ✅ Data appears in prompt logs (check `logs/prompts/*.json`)
6. ✅ CDL integration retrieves and uses the data (check logger.info statements)

## Current Import Status

- ✅ **Gabriel**: 50 entries (1 relationship to Cynthia, rich background data)
- ✅ **Aetheris**: 15 entries (conscious AI identity, philosophical patterns)
- ✅ **Jake**: 32 entries (adventure photography, Lakota heritage, signature catchphrases)

All three successfully mapped messy JSON to clean schema without drift.

## Future Character Imports

For each new character:

1. Read their JSON as a **semantic guide** (what information exists?)
2. Map concepts to **existing schema tables** (where does it fit?)
3. Infer **priority/intensity** based on content importance
4. Use **standard pattern types** from existing data
5. Test via HTTP API and check prompt logs
6. Document any NEW semantic concepts that don't fit (discuss before schema changes)

## Schema Update Process (Rare)

If truly new semantic concept emerges that CANNOT fit existing tables:

1. Document why existing tables insufficient
2. Propose minimal table addition
3. Get user approval BEFORE modifying schema
4. Update this document with new table authority
5. Update all import scripts to use new table

**Principle**: Resist schema changes. 99% of JSON concepts fit existing tables with intelligent mapping.
