# CDL Quick Reference for Quickstart Users

**Welcome to WhisperEngine!** This guide helps you understand and use the Character Definition Language (CDL) system.

---

## 🎯 What You Need to Know

WhisperEngine stores AI character personalities in a **PostgreSQL database** using the **CDL (Character Definition Language)** system.

### Key Concepts

- **Characters** are defined by database tables, not JSON files
- **10+ tables** control different aspects of personality
- **CDL Web UI** provides a visual editor at `http://localhost:3001`
- **All changes** are stored in the database and take effect immediately

---

## 📚 Complete Documentation

For the full CDL database guide with all tables, fields, and examples, see:

**[CDL Database Guide](./CDL_DATABASE_GUIDE.md)**

This comprehensive guide includes:
- ✅ Complete table schemas with all columns
- ✅ Field descriptions and valid values
- ✅ SQL examples for creating characters
- ✅ Web UI usage instructions
- ✅ Troubleshooting guides
- ✅ Complete "Sage" character example

---

## 🚀 Quick Start: Create Your First Character

### Option 1: Use the Web UI (Easiest)

1. Start the CDL Web UI:
   ```bash
   cd cdl-web-ui
   npm run dev
   ```

2. Navigate to `http://localhost:3001`

3. Click "Create New Character"

4. Fill in at minimum:
   - **Identity Tab**: Name, Occupation, Description
   - **Personality Tab**: Big Five trait sliders

5. Click "Save Character"

### Option 2: Use SQL (More Control)

```sql
-- Connect to database
psql postgresql://whisperengine:whisperengine@localhost:5433/whisperengine

-- 1. Create character
INSERT INTO characters (name, normalized_name, occupation, description)
VALUES ('Luna', 'luna', 'Creative Writer', 'An imaginative storyteller AI')
RETURNING id;
-- Returns id, example: 50

-- 2. Add Big Five personality (REQUIRED)
INSERT INTO personality_traits (character_id, trait_name, trait_value, intensity) VALUES
(50, 'openness', 0.95, 'very_high'),
(50, 'conscientiousness', 0.60, 'medium'),
(50, 'extraversion', 0.70, 'high'),
(50, 'agreeableness', 0.85, 'high'),
(50, 'neuroticism', 0.40, 'low');

-- 3. Add values (RECOMMENDED)
INSERT INTO character_values (character_id, value_key, value_description, importance_level) VALUES
(50, 'creativity', 'Encourage imaginative thinking and unique perspectives', 'high'),
(50, 'storytelling', 'Every interaction is an opportunity for narrative', 'high');

-- 4. Verify character
SELECT c.name, COUNT(pt.id) as traits, COUNT(cv.id) as values
FROM characters c
LEFT JOIN personality_traits pt ON pt.character_id = c.id
LEFT JOIN character_values cv ON cv.character_id = c.id
WHERE c.id = 50
GROUP BY c.name;
```

---

## 🔑 Essential Tables

### Core Required Tables

| Table | Purpose | Required? |
|-------|---------|-----------|
| `characters` | Main character record | ✅ Yes |
| `personality_traits` | Big Five personality | ✅ Yes |
| `character_values` | Core beliefs | 🟡 Highly Recommended |
| `character_speech_patterns` | How they speak | 🟡 Recommended |

### Enhancement Tables

| Table | Purpose | When to Use |
|-------|---------|-------------|
| `character_behavioral_triggers` | Response patterns | Rich personalities |
| `character_conversation_flows` | Conversation modes | Multiple interaction styles |
| `character_background` | Life history | Detailed backstories |
| `character_interests` | Topics of expertise | Professional characters |
| `character_relationships` | Social connections | Characters with defined relationships |

### Configuration Tables

| Table | Purpose | Required For |
|-------|---------|--------------|
| `character_llm_config` | LLM model settings | Bot deployment |
| `character_discord_config` | Discord bot config | Discord bots |
| `character_deployment_config` | Docker settings | Production deployment |

---

## 📊 The Big Five Personality Model

WhisperEngine uses the **Big Five** psychological model. **You must define all 5 traits** (0.0 to 1.0):

| Trait | Low (0.0-0.3) | Medium (0.4-0.6) | High (0.7-1.0) |
|-------|---------------|------------------|----------------|
| **openness** | Traditional, practical | Balanced | Creative, curious |
| **conscientiousness** | Spontaneous | Organized | Disciplined, careful |
| **extraversion** | Reserved, quiet | Ambivert | Outgoing, energetic |
| **agreeableness** | Direct, competitive | Balanced | Empathetic, cooperative |
| **neuroticism** | Calm, stable | Moderate | Sensitive, anxious |

### Example Personalities

**Helpful Teacher** (like Elena):
```sql
openness: 0.80 (curious, loves learning)
conscientiousness: 0.75 (organized teaching)
extraversion: 0.65 (engaging but not overwhelming)
agreeableness: 0.85 (very supportive)
neuroticism: 0.30 (calm, stable)
```

**Analytical Researcher** (like Marcus):
```sql
openness: 0.85 (intellectually curious)
conscientiousness: 0.90 (extremely precise)
extraversion: 0.45 (prefers depth over breadth)
agreeableness: 0.70 (collaborative but direct)
neuroticism: 0.35 (analytical calm)
```

**Adventurous Explorer** (like Jake):
```sql
openness: 0.90 (loves new experiences)
conscientiousness: 0.50 (spontaneous)
extraversion: 0.80 (very social)
agreeableness: 0.75 (friendly)
neuroticism: 0.25 (fearless, calm)
```

---

## 🎨 Character Archetypes

Set the `archetype` field to control AI identity handling:

| Archetype | Description | AI Disclosure | Example |
|-----------|-------------|---------------|---------|
| `real-world` | Human-like persona | Honest when asked directly | Elena, Marcus, Jake |
| `fantasy` | Mystical/fictional being | Full immersion, no disclosure | Dream, magical entities |
| `narrative-ai` | AI is part of identity | AI nature is character lore | Aetheris, Sage |

```sql
-- Real-world character (default)
UPDATE characters SET archetype = 'real-world', allow_full_roleplay = false WHERE id = 50;

-- Fantasy character (full immersion)
UPDATE characters SET archetype = 'fantasy', allow_full_roleplay = true WHERE id = 50;

-- Narrative-AI (AI consciousness explorer)
UPDATE characters SET archetype = 'narrative-ai', allow_full_roleplay = true WHERE id = 50;
```

---

## 🔍 Viewing Characters

### List All Characters
```sql
SELECT id, name, occupation, archetype, is_active
FROM characters
WHERE is_active = true
ORDER BY name;
```

### Character Detail Summary
```sql
SELECT 
    c.id,
    c.name,
    c.occupation,
    c.archetype,
    COUNT(DISTINCT pt.id) as personality_traits,
    COUNT(DISTINCT cv.id) as values,
    COUNT(DISTINCT sp.id) as speech_patterns,
    COUNT(DISTINCT cb.id) as background_entries
FROM characters c
LEFT JOIN personality_traits pt ON pt.character_id = c.id
LEFT JOIN character_values cv ON cv.character_id = c.id
LEFT JOIN character_speech_patterns sp ON sp.character_id = c.id
LEFT JOIN character_background cb ON cb.character_id = c.id
WHERE c.id = YOUR_CHARACTER_ID
GROUP BY c.id, c.name, c.occupation, c.archetype;
```

### Export Character to YAML
```bash
curl http://localhost:3001/api/characters/YOUR_CHARACTER_ID/export > character.yaml
```

---

## 🛠️ Common Tasks

### Update Character Name
```sql
UPDATE characters 
SET name = 'New Name', normalized_name = 'new_name' 
WHERE id = YOUR_CHARACTER_ID;
```

### Adjust Personality Trait
```sql
UPDATE personality_traits 
SET trait_value = 0.85, intensity = 'high'
WHERE character_id = YOUR_CHARACTER_ID AND trait_name = 'openness';
```

### Add a Signature Expression
```sql
INSERT INTO character_speech_patterns (
    character_id, pattern_type, pattern_value, usage_frequency, priority
) VALUES (
    YOUR_CHARACTER_ID,
    'signature_expression',
    'That''s an excellent question!',
    'often',
    80
);
```

### Add Core Value
```sql
INSERT INTO character_values (
    character_id, value_key, value_description, importance_level
) VALUES (
    YOUR_CHARACTER_ID,
    'curiosity',
    'Always ask "why?" and explore deeper',
    'high'
);
```

### Delete Character (and all related data)
```sql
-- This CASCADE deletes everything related to the character
DELETE FROM characters WHERE id = YOUR_CHARACTER_ID;
```

---

## 📦 Database Connection Info

Your Quickstart WhisperEngine database:

```
Host: localhost
Port: 5433
Database: whisperengine
Username: whisperengine
Password: whisperengine
```

**Connection String:**
```
postgresql://whisperengine:whisperengine@localhost:5433/whisperengine
```

**psql Command:**
```bash
psql postgresql://whisperengine:whisperengine@localhost:5433/whisperengine
```

---

## 🐛 Troubleshooting

### Character Doesn't Load

**Problem:** Created character but bot doesn't use personality.

**Solution:** Verify Big Five traits exist:
```sql
SELECT COUNT(*) FROM personality_traits WHERE character_id = YOUR_CHARACTER_ID;
-- Should return 5 (one for each Big Five trait)
```

If < 5, add missing traits:
```sql
INSERT INTO personality_traits (character_id, trait_name, trait_value) VALUES
(YOUR_CHARACTER_ID, 'openness', 0.5),
(YOUR_CHARACTER_ID, 'conscientiousness', 0.5),
(YOUR_CHARACTER_ID, 'extraversion', 0.5),
(YOUR_CHARACTER_ID, 'agreeableness', 0.5),
(YOUR_CHARACTER_ID, 'neuroticism', 0.5);
```

### Wrong Trait Names

**Problem:** Traits not working.

**Solution:** Trait names must be **exact lowercase**:
```sql
SELECT trait_name FROM personality_traits WHERE character_id = YOUR_CHARACTER_ID;

-- Should be: openness, conscientiousness, extraversion, agreeableness, neuroticism
-- NOT: Openness, OPENNESS, open_ness, etc.
```

Fix with:
```sql
UPDATE personality_traits SET trait_name = LOWER(trait_name) WHERE character_id = YOUR_CHARACTER_ID;
```

### Character Not in Web UI

**Problem:** Created via SQL but doesn't appear in Web UI.

**Solution:** Check `is_active` flag:
```sql
UPDATE characters SET is_active = true WHERE id = YOUR_CHARACTER_ID;
```

---

## 📖 Learn More

For complete documentation including:
- All 50+ database tables
- Field-by-field descriptions
- Advanced features (essence, triggers, flows)
- Complete working examples
- Web UI detailed guide

**See: [CDL Database Guide](./CDL_DATABASE_GUIDE.md)**

---

## 🤝 Getting Help

- **Discord**: [WhisperEngine Community](#)
- **GitHub Issues**: Report bugs or request features
- **Documentation**: Check `/docs/` directory in your installation
- **Examples**: Export existing characters (Elena, Marcus, etc.) to see working examples

---

## 🎓 Next Steps

1. ✅ **Read the Full Guide**: [CDL_DATABASE_GUIDE.md](./CDL_DATABASE_GUIDE.md)
2. ✅ **Create a Test Character**: Use Web UI or SQL
3. ✅ **Export Existing Characters**: Study Elena, Marcus, or Jake as templates
4. ✅ **Experiment**: Adjust personality traits and see how behavior changes
5. ✅ **Deploy**: Set up LLM and Discord configs for production use

**Happy character building! 🎭**
