# YAML Export/Import Field Mapping Audit
**Date**: October 21, 2025

## Summary

Audited YAML export and import routes to verify correct table/field names after recent database schema changes.

---

## Export Route Analysis (`/api/characters/[id]/export/route.ts`)

### ✅ CORRECT Mappings

1. **Background Entries** - `character_background` table
   ```typescript
   SELECT id, category, period, title, description, date_range, importance_level
   FROM character_background 
   WHERE character_id = $1
   ```
   - ✅ All fields match current schema

2. **Interests** - `character_interests` table
   ```typescript
   SELECT id, category, interest_text, proficiency_level, importance, created_at
   FROM character_interests
   WHERE character_id = $1
   ```
   - ✅ All fields match current schema

3. **Communication Patterns** - `character_communication_patterns` table
   ```typescript
   SELECT id, pattern_type, pattern_name, pattern_value, context, frequency
   FROM character_communication_patterns
   WHERE character_id = $1
   ```
   - ✅ All fields match current schema

4. **Speech Patterns** - `character_speech_patterns` table
   ```typescript
   SELECT id, pattern_type, pattern_value, usage_frequency, context, priority
   FROM character_speech_patterns
   WHERE character_id = $1
   ```
   - ✅ All fields match current schema

5. **Personality Traits** - `personality_traits` table
   ```typescript
   SELECT trait_name, trait_value, intensity, description
   FROM personality_traits 
   WHERE character_id = $1
   ```
   - ✅ All fields match current schema

6. **Character Values** - `character_values` table
   ```typescript
   SELECT value_key, value_description, importance_level, category
   FROM character_values 
   WHERE character_id = $1
   ```
   - ✅ All fields match current schema

### ⚠️ ISSUE: Response Style Mapping

**Current Code**:
```typescript
// Response style guidelines
client.query(`
  SELECT crg.id, crg.guideline_type as item_type, crg.guideline_content as item_text, 
         crg.priority as sort_order
  FROM character_response_guidelines crg
  WHERE crg.character_id = $1
  ORDER BY crg.priority DESC
`, [characterId])
```

**Problems**:
1. ❌ Only queries `character_response_guidelines` table
2. ❌ Does NOT query `character_response_modes` table (missing data!)
3. ❌ Aliases fields to legacy names (item_type, item_text) instead of proper names
4. ❌ Export YAML uses legacy format (`items`) instead of new format (`guidelines` + `modes`)

**Should Export**:
```yaml
response_style:
  guidelines:
    - id: 1
      guideline_type: "conversational"
      guideline_name: "Be friendly"
      guideline_content: "Always maintain a warm tone"
      priority: 1
      is_critical: true
  modes:
    - id: 1
      mode_name: "casual"
      mode_description: "Relaxed conversation mode"
      response_style: "informal"
      length_guideline: "medium"
      tone_adjustment: "friendly"
      conflict_resolution_priority: 1
```

**Currently Exports** (WRONG):
```yaml
response_style:
  items:  # ❌ Legacy format
    - id: 1
      item_type: "conversational"  # ❌ Aliased from guideline_type
      item_text: "Always maintain a warm tone"  # ❌ Aliased from guideline_content
      sort_order: 1  # ❌ Aliased from priority
```

### ⚠️ ISSUE: Transaction Handling

**Current Code**:
```typescript
const client = await pool.connect()
try {
  // ... queries ...
} finally {
  client.release()
}
```

**Problems**:
1. ❌ Creates own Pool instance instead of using shared pool from `db-pool.ts`
2. ❌ Doesn't use `withClient()` helper for automatic cleanup
3. ⚠️ No transaction needed for read-only operations, but should use helper

**Should Be**:
```typescript
import { getPool, withClient } from '@/lib/db-pool'

const pool = getPool()

// In GET handler:
const [backgroundRows, interestsRows, ...] = await withClient(pool, async (client) => {
  return await Promise.all([...queries...])
})
```

---

## Import Route Analysis (`/api/characters/import/route.ts`)

### ✅ CORRECT Mappings

1. **Background Import** - `character_background` table
   ```typescript
   INSERT INTO character_background (character_id, category, period, title, description, importance_level)
   VALUES ($1, $2, $3, $4, $5, $6)
   ```
   - ✅ Correct table name
   - ✅ Correct field names
   - ✅ Handles both `period` and `timeframe` from YAML (backward compatibility)
   - ✅ Handles both `description` and `content` from YAML (backward compatibility)

2. **Interests Import** - `character_interests` table
   ```typescript
   INSERT INTO character_interests (character_id, category, interest_text, proficiency_level, importance, display_order)
   VALUES ($1, $2, $3, $4, $5, $6)
   ```
   - ✅ Correct table name
   - ✅ Correct field names

3. **Speech Patterns Import** - `character_speech_patterns` table
   ```typescript
   INSERT INTO character_speech_patterns (character_id, pattern_type, pattern_value, usage_frequency, context, priority)
   VALUES ($1, $2, $3, $4, $5, $6)
   ```
   - ✅ Correct table name
   - ✅ Correct field names
   - ✅ Handles both `pattern_value` and `pattern` from YAML (backward compatibility)
   - ✅ Handles both `usage_frequency` and `frequency` from YAML (backward compatibility)

### ❌ MISSING: Communication Patterns Import

**Current Code**: Does NOT import communication patterns at all!

**Should Add**:
```typescript
// Import communication patterns
const communicationData = yamlData.communication_patterns as Record<string, unknown> | undefined
if (communicationData && Array.isArray(communicationData.patterns)) {
  for (const pattern of communicationData.patterns) {
    if (typeof pattern === 'object' && pattern !== null) {
      const commPattern = pattern as Record<string, unknown>
      await client.query(`
        INSERT INTO character_communication_patterns 
        (character_id, pattern_type, pattern_name, pattern_value, context, frequency)
        VALUES ($1, $2, $3, $4, $5, $6)
      `, [
        character.id,
        getString(commPattern, 'pattern_type') || 'General',
        getString(commPattern, 'pattern_name') || null,
        getString(commPattern, 'pattern_value') || null,
        getString(commPattern, 'context') || null,
        getString(commPattern, 'frequency') || 'Medium'
      ])
    }
  }
}
```

### ❌ MISSING: Response Style Import

**Current Code**: Does NOT import response style guidelines or modes at all!

**Should Add**:
```typescript
// Import response style guidelines
const responseStyleData = yamlData.response_style as Record<string, unknown> | undefined
if (responseStyleData) {
  // Import guidelines
  if (Array.isArray(responseStyleData.guidelines)) {
    for (const guideline of responseStyleData.guidelines) {
      if (typeof guideline === 'object' && guideline !== null) {
        const guidelineEntry = guideline as Record<string, unknown>
        await client.query(`
          INSERT INTO character_response_guidelines 
          (character_id, guideline_type, guideline_name, guideline_content, priority, context, is_critical)
          VALUES ($1, $2, $3, $4, $5, $6, $7)
        `, [
          character.id,
          getString(guidelineEntry, 'guideline_type') || 'general',
          getString(guidelineEntry, 'guideline_name') || null,
          getString(guidelineEntry, 'guideline_content') || null,
          typeof guidelineEntry.priority === 'number' ? guidelineEntry.priority : 1,
          getString(guidelineEntry, 'context') || null,
          getBoolean(guidelineEntry, 'is_critical') ?? false
        ])
      }
    }
  }
  
  // Import modes
  if (Array.isArray(responseStyleData.modes)) {
    for (const mode of responseStyleData.modes) {
      if (typeof mode === 'object' && mode !== null) {
        const modeEntry = mode as Record<string, unknown>
        await client.query(`
          INSERT INTO character_response_modes
          (character_id, mode_name, mode_description, response_style, length_guideline, tone_adjustment, conflict_resolution_priority, examples)
          VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        `, [
          character.id,
          getString(modeEntry, 'mode_name') || null,
          getString(modeEntry, 'mode_description') || null,
          getString(modeEntry, 'response_style') || null,
          getString(modeEntry, 'length_guideline') || null,
          getString(modeEntry, 'tone_adjustment') || null,
          typeof modeEntry.conflict_resolution_priority === 'number' ? modeEntry.conflict_resolution_priority : 1,
          getString(modeEntry, 'examples') || null
        ])
      }
    }
  }
  
  // BACKWARD COMPATIBILITY: Handle legacy 'items' format
  if (Array.isArray(responseStyleData.items) && !responseStyleData.guidelines) {
    for (const item of responseStyleData.items) {
      if (typeof item === 'object' && item !== null) {
        const itemEntry = item as Record<string, unknown>
        await client.query(`
          INSERT INTO character_response_guidelines 
          (character_id, guideline_type, guideline_name, guideline_content, priority, is_critical)
          VALUES ($1, $2, $3, $4, $5, $6)
        `, [
          character.id,
          getString(itemEntry, 'item_type') || 'general',
          'Imported Guideline',
          getString(itemEntry, 'item_text') || null,
          typeof itemEntry.sort_order === 'number' ? itemEntry.sort_order : 1,
          false
        ])
      }
    }
  }
}
```

### ⚠️ ISSUE: Transaction Handling

**Current Code**:
```typescript
const client = await pool.connect()
try {
  await client.query('BEGIN')
  // ... operations ...
  await client.query('COMMIT')
} catch (importError) {
  await client.query('ROLLBACK')
} finally {
  client.release()
}
```

**Problems**:
1. ❌ Creates own Pool instance instead of using shared pool from `db-pool.ts`
2. ❌ Doesn't use `withTransaction()` helper
3. ✅ At least has proper BEGIN/COMMIT/ROLLBACK/finally pattern

**Should Be**:
```typescript
import { getPool, withTransaction } from '@/lib/db-pool'

const pool = getPool()

// In POST handler:
const character = await withTransaction(pool, async (client) => {
  // Create character
  const newCharacter = await createCharacterWithinTransaction(client, characterData)
  
  // Import all related data
  // ... background, interests, speech, communication, response style ...
  
  return newCharacter
})
```

---

## Missing Personality Traits Import

**Current Code**: Does NOT import Big Five personality traits or character values!

**Export Has**:
```typescript
// Personality traits (for Big Five)
client.query(`
  SELECT trait_name, trait_value, intensity, description
  FROM personality_traits 
  WHERE character_id = $1
`, [characterId])

// Character values
client.query(`
  SELECT value_key, value_description, importance_level, category
  FROM character_values 
  WHERE character_id = $1
`, [characterId])
```

**Import Needs**:
```typescript
// Import personality traits (Big Five)
const personalityData = yamlData.personality as Record<string, unknown> | undefined
if (personalityData && typeof personalityData.big_five === 'object') {
  const bigFive = personalityData.big_five as Record<string, unknown>
  const traits = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']
  
  for (const trait of traits) {
    const value = bigFive[trait]
    if (typeof value === 'number') {
      await client.query(`
        INSERT INTO personality_traits (character_id, trait_name, trait_value, intensity)
        VALUES ($1, $2, $3, $4)
      `, [character.id, trait, value, Math.abs(value - 0.5) * 2]) // intensity based on distance from neutral
    }
  }
}

// Import character values
if (personalityData && Array.isArray(personalityData.values)) {
  for (let i = 0; i < personalityData.values.length; i++) {
    const value = personalityData.values[i]
    if (typeof value === 'string') {
      await client.query(`
        INSERT INTO character_values (character_id, value_key, value_description, importance_level, category)
        VALUES ($1, $2, $3, $4, $5)
      `, [character.id, value.toLowerCase().replace(/\s+/g, '_'), value, personalityData.values.length - i, 'core'])
    }
  }
}
```

---

## Summary of Issues

### Export Route (`/api/characters/[id]/export/route.ts`)

1. ❌ **Response Style Export is BROKEN** - Only exports guidelines in legacy format, missing modes
2. ⚠️ **Connection Pool** - Should use shared pool from `db-pool.ts`
3. ⚠️ **Helper Usage** - Should use `withClient()` for automatic cleanup

### Import Route (`/api/characters/import/route.ts`)

1. ❌ **Missing Communication Patterns** - Not imported at all
2. ❌ **Missing Response Style** - Guidelines and modes not imported at all
3. ❌ **Missing Personality Traits** - Big Five traits not imported at all
4. ❌ **Missing Character Values** - Core values not imported at all
5. ⚠️ **Connection Pool** - Should use shared pool from `db-pool.ts`
6. ⚠️ **Helper Usage** - Should use `withTransaction()` for cleaner code

---

## Recommended Fixes Priority

### HIGH PRIORITY
1. Fix export response style to include both guidelines AND modes
2. Add communication patterns import
3. Add response style (guidelines + modes) import
4. Add personality traits import
5. Add character values import

### MEDIUM PRIORITY
6. Migrate both routes to use shared pool from `db-pool.ts`
7. Use `withClient()` and `withTransaction()` helpers

### LOW PRIORITY
8. Add validation for imported YAML structure
9. Add progress/status reporting for long imports

---

## Testing Checklist

After fixes:

- [ ] Export character with all data populated
- [ ] Verify YAML contains: background, interests, communication_patterns, speech_patterns, response_style (guidelines + modes), personality (big_five + values)
- [ ] Import exported YAML as new character
- [ ] Verify all tabs in character edit form display imported data correctly
- [ ] Test backward compatibility with legacy YAML format (items instead of guidelines)
- [ ] Test import error handling (missing fields, invalid data types)
- [ ] Verify transaction rollback on import errors

---

**Status**: Found 9 critical issues across export/import routes. Both routes need significant fixes to match current database schema.
