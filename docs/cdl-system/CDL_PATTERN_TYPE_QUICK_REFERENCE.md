# CDL Pattern Type - Quick Reference

**Quick lookup guide for working with character communication patterns**

---

## The Basics

**What is pattern_type?** A category that classifies communication behaviors (e.g., "humor", "explanation", "communication_style").

**Where is it?** `character_communication_patterns.pattern_type` in PostgreSQL

**How is it used?** Patterns are grouped by type, formatted into system prompts, and guide LLM responses.

---

## Common Pattern Types

| Type | Examples |
|------|----------|
| `humor` | Witty quips, wordplay, personality-based comedy |
| `explanation` | Teaching style, how to break down concepts |
| `emoji` | Emoji preferences, frequency, context |
| `communication_style` | Overall tone, warmth, formality level |
| `questioning` | Socratic questions, curiosity markers |
| `storytelling` | Narrative approach, anecdote frequency |
| `metaphor` | Analogy preferences, domain-specific imagery |
| `thinking` | Problem-solving approach, analysis style |
| `voice_tone` | Sophisticated, casual, authoritative, etc. |
| `encouragement` | Supportive language, motivation style |
| `disagreement` | How to handle differing views |
| `transition` | How to move between topics |

---

## Quick SQL Examples

### View all patterns for a character
```sql
SELECT pattern_type, pattern_name, pattern_value, frequency
FROM character_communication_patterns 
WHERE character_id = (SELECT id FROM characters WHERE name = 'elena')
ORDER BY pattern_type, frequency DESC;
```

### Add a new pattern
```sql
INSERT INTO character_communication_patterns 
(character_id, pattern_type, pattern_name, pattern_value, context, frequency)
VALUES (
    (SELECT id FROM characters WHERE name = 'elena'),
    'humor',                    -- pattern_type
    'marine_puns',              -- pattern_name
    'Uses ocean and sea life puns when relevant',  -- pattern_value
    'all_contexts',
    'sometimes'                 -- frequency
);
```

### Update frequency (e.g., make pattern more common)
```sql
UPDATE character_communication_patterns
SET frequency = 'constant'
WHERE character_id = (SELECT id FROM characters WHERE name = 'elena')
  AND pattern_type = 'communication_style';
```

### Delete a pattern
```sql
DELETE FROM character_communication_patterns
WHERE character_id = (SELECT id FROM characters WHERE name = 'elena')
  AND pattern_type = 'humor'
  AND pattern_name = 'marine_puns';
```

---

## Pattern Processing Pipeline

```
Database Pattern
      ↓
EnhancedCDLManager.get_communication_patterns()
      ↓
Group by pattern_type
      ↓
Sort by frequency DESC
      ↓
CDLAIPromptIntegration formats into prompt sections
      ↓
LLM receives patterns as guidance
      ↓
Response generated with pattern influence
```

---

## Frequency Values

| Value | Meaning | Example |
|-------|---------|---------|
| `constant` | Always present | Core communication style |
| `often` | In ~70% of responses | Common humor style |
| `sometimes` | In ~30-50% of responses | Situational behaviors |
| `rarely` | In ~<20% of responses | Edge case patterns |

---

## ARIA Example

From your ``.env.aria`` file context, ARIA has patterns like:

```
pattern_type: communication_style
pattern_name: manifestation_emotion
pattern_value: Holographic appearance reflects emotional state and processing intensity
context: all_contexts
frequency: constant
```

**Processing**:
1. ✅ Pattern loaded from database
2. ✅ Grouped under `communication_style` type
3. ✅ Marked as `constant` (always apply)
4. ✅ Added to prompt: "Your holographic form's brightness reflects your confidence level..."
5. ✅ LLM generates responses mentioning holographic shifts

---

## Web UI (CDL Web UI)

When editing characters via the CDL Web UI:
1. Go to **Communication** section
2. Click **Add Communication Pattern**
3. Select or type **Pattern Type** (dropdown, but custom values allowed)
4. Enter **Pattern Name** (specific behavior)
5. Enter **Pattern Value** (description of behavior)
6. Set **Context** and **Frequency**
7. Click **Save**

---

## Common Issues & Fixes

| Problem | Solution |
|---------|----------|
| Pattern not used by character | Increase `frequency` to `constant` or `often` |
| Conflicting character behavior | Check if multiple patterns have opposing guidance |
| New pattern not visible | Refresh CDL cache or verify `character_id` in database |
| Custom pattern_type not in dropdown | Can type custom value in Web UI - no need to pre-define |

---

## Database Field Reference

```sql
CREATE TABLE character_communication_patterns (
    id SERIAL PRIMARY KEY,
    character_id INTEGER REFERENCES characters(id),
    pattern_type VARCHAR(50) NOT NULL,         -- 👈 Classification
    pattern_name VARCHAR(100) NOT NULL,        -- Specific behavior
    pattern_value TEXT NOT NULL,               -- Description
    context VARCHAR(100),                      -- When to apply (e.g., 'all_contexts')
    frequency VARCHAR(20) DEFAULT 'regular',   -- constant|often|sometimes|rarely
    description TEXT,                          -- Additional notes
    UNIQUE(character_id, pattern_type, pattern_name)
);
```

---

## Testing Patterns

```bash
# Start bot for testing
./multi-bot.sh bot elena

# Test via HTTP Chat API
curl -X POST http://localhost:9091/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user_1",
    "message": "Tell me a joke!",
    "metadata": {"platform": "api_test"}
  }'

# Check if humor patterns are reflected in response
```

---

## Pro Tips

1. **Organize patterns hierarchically**: Use consistent `pattern_type` names across all characters
2. **Keep pattern_value descriptive**: Clear instructions to LLM = better responses
3. **Use `context` wisely**: Specify when patterns apply for better accuracy
4. **Test after changes**: Use HTTP API to validate pattern application
5. **Document custom pattern_types**: If you create new ones, note them in character export/YAML

---

## References

- Full documentation: `docs/cdl-system/CDL_PATTERN_TYPE_HANDLING.md`
- CDL Database Guide: `docs/cdl-system/CDL_DATABASE_GUIDE.md`
- Character examples: `characters/examples_legacy_backup/` or CDL Web UI
