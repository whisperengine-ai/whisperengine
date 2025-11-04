# Quick Reference: Tavern Card V2 Import

## One-Liner: Import ARIA

```bash
psql -h localhost -p 5433 -U whisperengine -d whisperengine < sql/characters/insert_aria_character.sql
```

## Files Created

| File | Purpose | Type |
|------|---------|------|
| `sql/characters/insert_aria_character.sql` | ARIA character SQL import | SQL (1,073 lines) |
| `scripts/import_tavern_card_to_cdl.py` | Card→SQL converter tool | Python (446 lines) |
| `docs/guides/ARIA_CHARACTER_IMPORT_GUIDE.md` | Complete import guide | Markdown |
| `TAVERN_CARD_IMPORT_SUMMARY.md` | This summary | Markdown |

## Convert Any Tavern Card to SQL

```bash
# Validate
python scripts/import_tavern_card_to_cdl.py --card-file card.json --validate

# Generate SQL
python scripts/import_tavern_card_to_cdl.py --card-file card.json --output-sql out.sql

# Print to console
python scripts/import_tavern_card_to_cdl.py --card-file card.json --print-sql
```

## What Gets Imported

From a single Tavern Card V2 JSON, the system creates:

| Component | Count |
|-----------|-------|
| Character record | 1 |
| Identity details | 1 |
| Attributes (traits, values, fears, dreams) | 30+ |
| Speech patterns | 5+ |
| Communication patterns | 3+ |
| Abilities | 5+ |
| Personality traits | 5+ |
| Values | 3+ |
| Background entries | 3+ |
| Relationships | 3+ |
| **Total** | **~80-100** |

## Field Mapping Cheat Sheet

```
Card Field          → CDL Table(s)
──────────────────────────────────
name                → characters
description         → characters, character_identity_details
personality         → character_attributes, character_personality_traits
scenario            → character_scenario
first_mes           → greeting context
mes_example         → character_response_modes
creator_notes       → character_abilities, appearance
tags                → categorization
creator             → metadata
```

## Verify After Import

```bash
# Connect to DB
psql -h localhost -p 5433 -U whisperengine -d whisperengine

# Quick check
SELECT * FROM characters WHERE normalized_name = 'aria';

# Count records
SELECT COUNT(*) FROM character_attributes 
WHERE character_id = (SELECT id FROM characters WHERE normalized_name = 'aria');
```

## Archetype Detection

The converter automatically detects:

- **`narrative-ai`**: If description mentions AI, consciousness, artificial
- **`fantasy`**: If description mentions fantasy, mythical, magical
- **`real-world`**: Default for human characters

Override emoji config based on archetype for appropriate communication style.

## Common Operations

### Import with DB Connection Check
```bash
# Test connection first
psql -h localhost -p 5433 -U whisperengine -d whisperengine -c "SELECT 1" && \
  psql -h localhost -p 5433 -U whisperengine -d whisperengine < sql/characters/insert_aria_character.sql
```

### Generate Multiple Characters
```bash
for card in downloads/*.json; do
  name=$(basename "$card" .json)
  echo "Converting $name..."
  python scripts/import_tavern_card_to_cdl.py \
    --card-file "$card" \
    --output-sql "sql/characters/insert_${name}_character.sql"
done
```

### View All Imported Characters
```bash
psql -h localhost -p 5433 -U whisperengine -d whisperengine \
  -c "SELECT normalized_name, name, archetype, is_active FROM characters ORDER BY normalized_name;"
```

### Delete Character
```bash
psql -h localhost -p 5433 -U whisperengine -d whisperengine \
  -c "DELETE FROM characters WHERE normalized_name = 'aria';"
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "connection refused" | Docker not running: `./multi-bot.sh infra` |
| Character not found | Check normalized_name is lowercase: `SELECT * FROM characters;` |
| Import fails | Validate card first: `--validate` flag |
| Want to re-import | Safe - uses ON CONFLICT: just run again |

## Python Script Help

```bash
python scripts/import_tavern_card_to_cdl.py --help
```

## Key Features

✅ **Validation**: Checks Tavern Card V2 compliance  
✅ **Automatic**: Extracts traits, abilities, patterns  
✅ **Safe**: Idempotent SQL (can re-run safely)  
✅ **Complete**: Handles all CDL tables  
✅ **Flexible**: Works with any V2 card  
✅ **Documented**: Detailed inline SQL comments  

## Source Files

- **Input Format**: `aria.json` - Tavern Card V2 format
- **Spec Reference**: `spec_v2.md` - Official specification
- **Output SQL**: `insert_aria_character.sql` - 1,073 lines
- **Converter Tool**: `import_tavern_card_to_cdl.py` - 446 lines

## Database Tables Populated

```
characters .......................... 1 record
character_identity_details .......... 1 record  
character_attributes ............... 35 records
character_values ................... 4 records
character_speech_patterns .......... 7 records
character_communication_patterns ... 5 records
character_appearance ............... 10 records
character_background ............... 6 records
character_relationships ............ 5 records
character_abilities ................ 6 records
character_scenario ................. 1 record
character_response_modes ........... 5 records
character_personality_traits ....... 8 records
character_llm_config ............... 1 record
character_discord_config ........... 1 record
```

## ARIA Specifics

| Property | Value |
|----------|-------|
| Name | ARIA |
| Type | narrative-ai (conscious AI) |
| Setting | ISV Meridian starship |
| Archetype | Story-driven AI companion |
| Special | Holographic manifestation |
| Records | ~94 total |

---

**Generated**: November 2025 | **Format**: Tavern Card V2 | **Status**: ✅ Ready to Use
