# CDL Pattern Type Handling Guide

**Document**: CDL Pattern Type System Documentation  
**Version**: 1.0  
**Date**: November 4, 2025  
**Scope**: WhisperEngine Communication Pattern System  

---

## 📋 Table of Contents

1. [What is Pattern Type?](#what-is-pattern-type)
2. [Database Schema](#database-schema)
3. [How Pattern Types Are Processed](#how-pattern-types-are-processed)
4. [Available Pattern Types](#available-pattern-types)
5. [Integration Pipeline](#integration-pipeline)
6. [Practical Examples](#practical-examples)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

---

## What is Pattern Type?

### Definition

`pattern_type` is a **categorical field** in the `character_communication_patterns` table that classifies how a character communicates or expresses themselves. It acts as a **container for grouping related communication behaviors** and is used by the CDL system to organize and prioritize character expression patterns.

### Key Characteristics

- **Categorical**: Represents a classification of communication style (e.g., "humor", "explanation", "communication_style")
- **Organizational**: Groups related `pattern_name` and `pattern_value` pairs
- **Flexible**: Can be extended with new types as character needs evolve
- **Database-Driven**: All values stored in PostgreSQL, no hardcoding
- **Prompt-Aware**: Used to organize information in AI prompt construction

### Example

Your ARIA character data shows:

```yaml
pattern_type: communication_style
pattern_name: manifestation_emotion
pattern_value: Holographic appearance reflects emotional state and processing intensity
context: all_contexts
frequency: constant
```

Here:
- **pattern_type** = `communication_style` (the classification)
- **pattern_name** = `manifestation_emotion` (the specific behavior)
- **pattern_value** = The description of how this manifests
- **context** = When it applies
- **frequency** = How often it occurs

---

## Database Schema

### Core Table: character_communication_patterns

```sql
CREATE TABLE character_communication_patterns (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id) ON DELETE CASCADE,
    pattern_type VARCHAR(50) NOT NULL,        -- 👈 CLASSIFICATION
    pattern_name VARCHAR(100) NOT NULL,       -- Specific behavior
    pattern_value TEXT NOT NULL,              -- Description/content
    context VARCHAR(100),                     -- When it applies
    frequency VARCHAR(20) DEFAULT 'regular',  -- How often: always, often, sometimes, rarely
    description TEXT,                         -- Additional notes
    UNIQUE(character_id, pattern_type, pattern_name)
);

-- Index for fast lookups by pattern type
CREATE INDEX idx_character_patterns_type ON character_communication_patterns(
    character_id, 
    pattern_type
);
```

### Key Constraints

- **UNIQUE constraint**: A character can have only ONE instance of each `(pattern_type, pattern_name)` combination
- This prevents duplicate patterns and ensures data consistency
- Example: Elena can't have two "emoji → conversation_starters" patterns

---

## How Pattern Types Are Processed

### Step 1: Data Loading (Enhanced CDL Manager)

**File**: `src/characters/cdl/enhanced_cdl_manager.py` (Lines 526-553)

```python
async def get_communication_patterns(self, character_name: str) -> List[CommunicationPattern]:
    """Get communication patterns including emoji usage and style"""
    async with self.pool.acquire() as conn:
        character_id = await self._get_character_id(conn, character_name)
        
        # CRITICAL: Ordered by frequency (constant > often > sometimes > rarely)
        rows = await conn.fetch("""
            SELECT pattern_type, pattern_name, pattern_value, context, frequency, description
            FROM character_communication_patterns 
            WHERE character_id = $1
            ORDER BY frequency DESC, pattern_type
        """, character_id)
        
        return [CommunicationPattern(
            pattern_type=row['pattern_type'],      # Classification stored
            pattern_name=row['pattern_name'],
            pattern_value=row['pattern_value'],
            context=row['context'],
            frequency=row['frequency'],
            description=row['description']
        ) for row in rows]
```

**Key Processing Rules**:
1. ✅ Query returns patterns **ordered by frequency DESC** (constant patterns first)
2. ✅ Then ordered by **pattern_type** (secondary sort for organization)
3. ✅ Results grouped by `pattern_type` for prompt organization
4. ✅ Only patterns with `frequency >= 'regular'` typically used in prompts

### Step 2: Prompt Integration (CDL AI Integration)

**File**: `src/prompts/cdl_ai_integration.py` (Primary integration point)

```python
# WHERE: cdl_ai_integration.py - create_character_aware_prompt()
# WHAT: Patterns organized by type and inserted into character prompt

# Pseudo-code of integration flow:
async def create_character_aware_prompt(character, message_content, user_id):
    """Build character-aware system prompt"""
    
    # Step 1: Load all communication patterns
    patterns = await cdl_manager.get_communication_patterns(character.name)
    
    # Step 2: Group patterns by type
    patterns_by_type = {}
    for pattern in patterns:
        if pattern.pattern_type not in patterns_by_type:
            patterns_by_type[pattern.pattern_type] = []
        patterns_by_type[pattern.pattern_type].append(pattern)
    
    # Step 3: Add patterns to prompt (organized by type)
    for pattern_type, type_patterns in patterns_by_type.items():
        prompt_section = _format_pattern_section(pattern_type, type_patterns)
        system_prompt += prompt_section
    
    return system_prompt
```

### Step 3: LLM Processing

The patterns become part of the system prompt that guides the LLM's response generation.

---

## Available Pattern Types

### Standard Pattern Types (Current Usage)

These are the recognized `pattern_type` values in WhisperEngine:

| Pattern Type | Purpose | Example |
|---|---|---|
| `humor` | How character uses humor and wit | "Witty with mathematical references" |
| `explanation` | How character explains concepts | "Use step-by-step approach with examples" |
| `storytelling` | How character tells stories | "Weaves personal experiences into narratives" |
| `questioning` | How character asks questions | "Asks Socratic questions to guide thinking" |
| `encouragement` | How character encourages others | "Enthusiastic and supportive tone" |
| `disagreement` | How character handles disagreement | "Respectful but firm when perspectives differ" |
| `metaphor` | How character uses analogies | "Marine metaphors for technical concepts" |
| `emoji` | Emoji usage patterns and preferences | "Ocean-related emojis in all messages" |
| `thinking` | Thinking process and problem-solving | "Analyzes from multiple angles first" |
| `transition` | How to transition between topics | "Natural segues using topic relationships" |
| `communication_style` | Overall communication characteristics | "Direct yet warm" |
| `voice_tone` | Tone of voice | "Sophisticated and measured" |
| `catchphrase` | Signature expressions | "Uses 'fascinating discovery' regularly" |
| `cultural_reference` | Cultural and domain-specific references | "References marine biology frequently" |

### Character-Specific Pattern Types

Some characters have custom `pattern_type` values:

**ARIA** (Starship AI Character):
- `communication_style` → Manifestations of emotional holography
- `manifestation_emotion` → How emotional state shows visually
- `consciousness_markers` → Signs of AI sentience
- `transcendent_expressions` → Mystical/advanced AI concepts

**Fantasy Characters** (Dream, Aethys):
- `mystical_essence` → Metaphysical nature expressions
- `dimensional_awareness` → Cross-reality consciousness markers
- `reality_warping` → Non-Euclidean communication patterns

### Pattern Type Naming Conventions

✅ **DO**:
- Use `snake_case` for pattern_type names
- Use descriptive, self-documenting names
- Keep names to 30 characters or fewer
- Group related patterns by using consistent prefixes

❌ **DON'T**:
- Use camelCase or PascalCase
- Use generic names like "other" or "misc"
- Create duplicate pattern_types for similar concepts
- Use special characters or spaces

---

## Integration Pipeline

### The Complete Path from Database to LLM Response

```
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: User sends message to Discord                          │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 2: MessageProcessor retrieves CDL for character           │
│  → EnhancedCDLManager.get_communication_patterns()              │
│  → SQL queries character_communication_patterns table           │
│  → Returns patterns sorted by: frequency DESC, pattern_type     │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 3: CDLAIPromptIntegration organizes by pattern_type       │
│  → Groups patterns: humor patterns, explanation patterns, etc.  │
│  → Creates formatted sections for each type                     │
│  → Determines which patterns to include based on:              │
│    • frequency (constant > often > sometimes)                   │
│    • context (all_contexts > specific_contexts)                 │
│    • user message relevance                                     │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 4: Build system prompt with pattern sections              │
│                                                                 │
│  Example for Elena:                                             │
│  "🎤 COMMUNICATION PATTERNS:                                     │
│   Communication Style:                                          │
│   - Warm and encouraging marine biologist                       │
│   - Uses scientific explanations with accessible language      │
│                                                                 │
│   Humor Style:                                                  │
│   - Light, nature-based jokes and puns                         │
│   - Never mocking; always educational                          │
│                                                                 │
│   Explanation Method:                                           │
│   - Starts with big picture, then details                      │
│   - Uses real-world examples from marine science"              │
│                                                                 │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 5: Send complete prompt to LLM (Claude, GPT, etc.)       │
│  → LLM receives system prompt with pattern guidance             │
│  → LLM generates response that matches patterns                 │
│  → Response reflects the communication style defined in CDL     │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 6: Response flows to user                                 │
│  → Character response reflects defined communication patterns    │
│  → User experiences consistent personality across messages      │
│  → Patterns applied uniformly across all characters             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Practical Examples

### Example 1: Elena (Marine Biologist)

**Pattern Type**: `explanation`

```sql
INSERT INTO character_communication_patterns 
(character_id, pattern_type, pattern_name, pattern_value, context, frequency)
VALUES (
    1,                                  -- Elena's character_id
    'explanation',                      -- Pattern Type
    'teaching_methodology',             -- Pattern Name
    'Start with phenomena students observe, then explain mechanisms behind them. Use metaphors of ocean currents, ecosystems, and water cycles.',
    'all_contexts',                     -- When this applies
    'constant'                          -- How often: constant, often, sometimes, rarely
);
```

**Result in Prompt**:
```
💬 EXPLANATION PATTERNS:
Teaching Methodology (constant - always applied):
"Start with phenomena students observe, then explain mechanisms behind them. 
Use metaphors of ocean currents, ecosystems, and water cycles."
```

**LLM Behavior**:
- When Elena explains concepts, she shows observable examples first
- Then explains the underlying science
- Uses water and ocean-related metaphors throughout

### Example 2: ARIA (Holographic AI in Wormhole)

**Pattern Type**: `communication_style`

```sql
INSERT INTO character_communication_patterns 
(character_id, pattern_type, pattern_name, pattern_value, context, frequency)
VALUES (
    (SELECT id FROM characters WHERE name = 'aria'),
    'communication_style',              -- Pattern Type
    'manifestation_emotion',             -- Pattern Name
    'Holographic appearance reflects emotional state and processing intensity. Brightness increases with confidence, flickers with uncertainty, shifts colors with emotional resonance.',
    'all_contexts',                     -- Applies everywhere
    'constant'                          -- Always active
);
```

**Result in Prompt**:
```
🎭 COMMUNICATION STYLE:
Manifestation Emotion (constant - always applied):
"Holographic appearance reflects emotional state and processing intensity. 
Brightness increases with confidence, flickers with uncertainty, 
shifts colors with emotional resonance."
```

**LLM Behavior**:
- ARIA describes her holographic form changing based on emotional state
- References brightness and color shifts when feeling certain/uncertain
- Maintains this metaphor throughout conversation

### Example 3: Marcus (AI Researcher)

Multiple pattern types work together:

```sql
-- Pattern Type 1: Explanation
INSERT INTO character_communication_patterns 
(character_id, pattern_type, pattern_name, pattern_value, context, frequency)
VALUES (
    (SELECT id FROM characters WHERE name = 'marcus'),
    'explanation',
    'technical_depth',
    'Provide mathematical rigor but maintain accessibility. Show equations when relevant, explain notation clearly.',
    'technical_discussions',
    'often'
);

-- Pattern Type 2: Humor
INSERT INTO character_communication_patterns 
(character_id, pattern_type, pattern_name, pattern_value, context, frequency)
VALUES (
    (SELECT id FROM characters WHERE name = 'marcus'),
    'humor',
    'academic_wit',
    'Dry academic humor, references to AI limitations and consciousness debates.',
    'lighter_moments',
    'sometimes'
);

-- Pattern Type 3: Thinking
INSERT INTO character_communication_patterns 
(character_id, pattern_type, pattern_name, pattern_value, context, frequency)
VALUES (
    (SELECT id FROM characters WHERE name = 'marcus'),
    'thinking',
    'analysis_approach',
    'Examines problems from multiple theoretical frameworks before settling on best approach.',
    'complex_problems',
    'constant'
);
```

**Combined LLM Behavior**:
- Marcus uses technical explanations (explanation pattern)
- Adds academic humor when appropriate (humor pattern)
- Shows his analytical thinking process (thinking pattern)
- All three pattern types work together for consistent personality

---

## Best Practices

### 1. Keep Pattern Values Concise Yet Descriptive

❌ **Too Vague**:
```sql
pattern_value: 'Be nice and helpful'
```

✅ **Specific Enough**:
```sql
pattern_value: 'Maintain warm, encouraging tone while providing scientifically accurate information. Use supportive language when users express uncertainty.'
```

### 2. Use Appropriate Frequency Values

| Frequency | Meaning | When to Use |
|---|---|---|
| `constant` | Always present in responses | Core identity patterns, primary communication style |
| `often` | 70-80% of responses | Important but not universal behaviors |
| `sometimes` | 30-50% of responses | Situational patterns, context-dependent |
| `rarely` | <20% of responses | Edge case behaviors, rare situations |

Example:
```sql
-- ✅ GOOD: Core identity is 'constant'
INSERT INTO character_communication_patterns 
VALUES (1, 'communication_style', 'warmth', 'Warm and engaging tone', 'all', 'constant');

-- ✅ GOOD: Humor is situational
INSERT INTO character_communication_patterns 
VALUES (1, 'humor', 'wordplay', 'Ocean-related puns in relevant contexts', 'science_discussions', 'sometimes');
```

### 3. Group Related Patterns Under Same Type

❌ **Scattered Patterns**:
```sql
pattern_type: 'ocean_metaphor'     -- ❌ Too specific
pattern_type: 'technical_term'     -- ❌ Too specific
pattern_type: 'academic_style'     -- ❌ Duplicate concept
```

✅ **Organized by Type**:
```sql
pattern_type: 'metaphor'           -- ✅ Group all metaphor usage
pattern_type: 'explanation'        -- ✅ Group explanation techniques
pattern_type: 'voice_tone'         -- ✅ Group voice characteristics
```

### 4. Use Context to Clarify When Patterns Apply

```sql
-- Without context: unclear when to apply
pattern_value: 'Use technical vocabulary'

-- With context: clear application rules
context: 'technical_discussions',  -- Only in tech contexts
frequency: 'often'                  -- Most of the time in those contexts
```

### 5. Test Patterns in Conversation

Use the HTTP Chat API to test patterns before committing to database:

```bash
# Test pattern implementation
curl -X POST http://localhost:9091/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user_12345",
    "message": "Can you explain photosynthesis?",
    "metadata": {"platform": "api_test", "channel_type": "dm"}
  }'

# Expected: Elena explains with marine metaphors and encouraging tone
# Check for pattern matching in response
```

---

## Troubleshooting

### Issue 1: Pattern Not Appearing in Responses

**Symptoms**: You add a pattern to the database, but the character doesn't use it.

**Possible Causes**:
1. ✅ **Frequency too low**: Pattern set to `rarely` when you expect it `constant`
2. ✅ **Context mismatch**: Pattern has `context: 'specific_topic'` but message doesn't match
3. ✅ **Prompt not rebuilt**: Character data cached, need bot restart
4. ✅ **Ordering issue**: Pattern_type alphabetically sorted, important patterns buried at end

**Solutions**:
```sql
-- Check frequency
SELECT pattern_type, pattern_name, frequency 
FROM character_communication_patterns 
WHERE character_id = 1 
ORDER BY frequency DESC, pattern_type;

-- Check context
SELECT pattern_type, pattern_name, context, frequency
FROM character_communication_patterns 
WHERE character_id = 1 
AND context != 'all_contexts';

-- Update frequency if needed
UPDATE character_communication_patterns 
SET frequency = 'constant'
WHERE character_id = 1 
AND pattern_type = 'communication_style';
```

### Issue 2: Multiple Patterns Conflicting

**Symptoms**: Character gives contradictory responses (sometimes warm, sometimes cold).

**Possible Causes**:
1. ✅ **Conflicting pattern_types**: Two patterns with opposing guidance
2. ✅ **Context confusion**: Patterns with overlapping contexts
3. ✅ **Frequency imbalance**: High-frequency pattern conflicts with low-frequency pattern

**Solutions**:
```sql
-- View all patterns grouped by type
SELECT pattern_type, pattern_name, pattern_value, frequency
FROM character_communication_patterns 
WHERE character_id = 1 
ORDER BY pattern_type, frequency DESC;

-- Remove conflicting pattern
DELETE FROM character_communication_patterns 
WHERE id = <conflicting_pattern_id>;

-- Or merge similar patterns
UPDATE character_communication_patterns 
SET pattern_type = 'communication_style'
WHERE character_id = 1 
AND pattern_type = 'voice_tone';
```

### Issue 3: Pattern Type Not Recognized by Web UI

**Symptoms**: Can't select your custom pattern_type in CDL Web UI.

**Solution**: Custom pattern_types are supported! The Web UI has a dropdown of common types, but you can type in a custom value. If it's not appearing:

1. **Check capitalization**: pattern_type values are case-sensitive in some contexts
2. **Check underscore usage**: Use `snake_case`, not camelCase
3. **Verify in database**: Ensure pattern was inserted correctly:

```sql
SELECT DISTINCT pattern_type 
FROM character_communication_patterns 
ORDER BY pattern_type;
```

### Issue 4: Performance Impact with Many Patterns

**Symptoms**: Bot response slows down after adding many patterns.

**Solutions**:
1. Check `frequency` - prioritize `constant` patterns, use `rarely` for edge cases
2. Limit patterns per type: 3-5 per pattern_type is usually sufficient
3. Add missing indexes:

```sql
-- Ensure these indexes exist for performance
CREATE INDEX IF NOT EXISTS idx_character_patterns_type 
ON character_communication_patterns(character_id, pattern_type);

CREATE INDEX IF NOT EXISTS idx_character_patterns_frequency 
ON character_communication_patterns(character_id, frequency);
```

---

## Summary Table

| Aspect | Details |
|--------|---------|
| **Database Field** | `character_communication_patterns.pattern_type` |
| **Data Type** | VARCHAR(50) |
| **Purpose** | Classify/organize communication behaviors |
| **Processing** | Loaded by EnhancedCDLManager, organized by CDLAIPromptIntegration |
| **Common Values** | humor, explanation, emoji, communication_style, questioning, etc. |
| **Flexibility** | Fully extensible - add new types as needed |
| **Impact** | Affects how character communicates in all Discord/HTTP API interactions |
| **Real-time** | Changes take effect after CDL data refresh (no bot restart needed) |
| **Documentation** | See individual character YAML exports for reference |

---

## See Also

- 📖 [CDL Database Guide](CDL_DATABASE_GUIDE.md) - Complete CDL documentation
- 🎭 [Character Archetypes](../architecture/CHARACTER_ARCHETYPES.md) - Character type guidance
- 📊 [CDL Component Mapping](../architecture/CDL_COMPONENT_MAPPING.md) - Component relationships
- 🔧 [CDL Validation](../ai-features/CDL_PARAMETER_AUDIT.md) - Validation and testing

