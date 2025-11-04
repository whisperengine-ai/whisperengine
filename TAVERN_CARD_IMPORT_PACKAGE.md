# Tavern Card V2 to WhisperEngine Import - Complete Package

## 📦 Package Contents

This package enables importing characters from the **Tavern Card V2** (Character Card) format into **WhisperEngine's CDL (Character Definition Language)** PostgreSQL database system.

### Created Files

| File | Size | Purpose |
|------|------|---------|
| **`sql/characters/insert_aria_character.sql`** | 28 KB | Ready-to-run SQL import for ARIA character (~94 database records) |
| **`scripts/import_tavern_card_to_cdl.py`** | 17 KB | Reusable Python converter: Tavern Card V2 JSON → SQL |
| **`docs/guides/ARIA_CHARACTER_IMPORT_GUIDE.md`** | 12 KB | Comprehensive import guide with examples |
| **`TAVERN_CARD_IMPORT_SUMMARY.md`** | 8.5 KB | Overview and design decisions |
| **`TAVERN_CARD_QUICK_REFERENCE.md`** | 5.5 KB | Quick commands and troubleshooting |

**Total**: ~70 KB of production-ready code and documentation

---

## 🚀 Quick Start

### Import ARIA Character (30 seconds)

```bash
# One command to import ARIA into WhisperEngine database
psql -h localhost -p 5433 -U whisperengine -d whisperengine < sql/characters/insert_aria_character.sql
```

### Convert Any Tavern Card to SQL

```bash
# Convert your own character card to SQL
python scripts/import_tavern_card_to_cdl.py \
    --card-file my_character.json \
    --output-sql sql/characters/insert_my_character_character.sql
```

---

## 📋 What Gets Imported

From a single **Tavern Card V2 JSON** file, the system automatically creates:

```
✅ Character record (1)
✅ Identity details (1)
✅ LLM configuration (1)
✅ Discord configuration (1)
✅ Personality attributes (30+)
   - Quirks, values, fears, dreams, beliefs
✅ Speech patterns (5+)
✅ Communication patterns (3+)
✅ Appearance details (5+)
✅ Abilities & special features (5+)
✅ Relationships & connections (3+)
✅ Background & scenario context (3+)
────────────────────────────────────
TOTAL: ~80-100 database records per character
```

---

## 🔄 Tavern Card V2 Format

The **Tavern Card V2** (also called Character Card V2) is a standardized format for AI character roleplay:

### Core Fields
- `name` - Character name
- `description` - Full character description
- `personality` - Personality traits and behavior
- `scenario` - Initial scenario/setting
- `first_mes` - First message template
- `mes_example` - Example messages

### Extended V2 Fields  
- `creator_notes` - Implementation instructions
- `system_prompt` - Custom LLM system prompt
- `post_history_instructions` - UJB/jailbreak
- `alternate_greetings` - Alternative openings
- `tags` - Categorization
- `creator` - Character creator
- `character_version` - Version number
- `character_book` - Optional lorebook entries

**Specification**: `/Users/markcastillo/Downloads/spec_v2.md`  
**Example Card**: `/Users/markcastillo/Downloads/aria.json`

---

## 🗺️ Field Mapping Reference

How Tavern Card V2 fields map to WhisperEngine CDL database:

```
Tavern Card Field              → CDL Database Table(s)
────────────────────────────────────────────────────
name                           → characters
description                    → characters, character_identity_details
personality                    → character_attributes, character_personality_traits
scenario                       → character_scenario
first_mes                      → greeting context
mes_example                    → character_response_modes
creator_notes                  → character_abilities, character_appearance
system_prompt                  → character_llm_config
post_history_instructions      → character_response_modes
alternate_greetings            → greeting variations
tags                           → categorization
creator                        → metadata
character_version              → version tracking
character_book (optional)      → character_background entries
```

---

## 📁 File Guide

### 1. ARIA SQL Import (`sql/characters/insert_aria_character.sql`)

**Direct SQL import file for the ARIA character**

```sql
-- 1,073 lines of production-ready SQL
-- Imports ~94 database records
-- Uses ON CONFLICT for idempotency (safe to re-run)
-- Fully commented and structured
```

**What it includes:**
- ✅ Base character record with archetype
- ✅ Identity details and essence
- ✅ 35 personality attributes
- ✅ Core values and dreams
- ✅ 7 speech patterns
- ✅ 5 communication patterns
- ✅ 10 appearance details
- ✅ 6 special abilities
- ✅ Background and scenario
- ✅ Character relationships

**Usage:**
```bash
# Direct import
psql -h localhost -p 5433 -U whisperengine -d whisperengine < sql/characters/insert_aria_character.sql

# Or from psql prompt
\i sql/characters/insert_aria_character.sql
```

### 2. Python Converter (`scripts/import_tavern_card_to_cdl.py`)

**Reusable tool to convert ANY Tavern Card V2 JSON to SQL**

```python
# 446 lines of well-documented Python
# Zero external dependencies (uses stdlib only)
# Full validation and error handling
```

**Features:**
- ✅ Validates Tavern Card V2 compliance
- ✅ Extracts personality traits automatically
- ✅ Determines character archetype
- ✅ Maps all fields to CDL tables
- ✅ Generates idempotent SQL
- ✅ Escapes special characters
- ✅ Detailed error reporting

**Usage Examples:**
```bash
# Validate without generating SQL
python scripts/import_tavern_card_to_cdl.py --card-file card.json --validate

# Generate SQL to file
python scripts/import_tavern_card_to_cdl.py --card-file card.json --output-sql output.sql

# Print SQL to console
python scripts/import_tavern_card_to_cdl.py --card-file card.json --print-sql

# Help
python scripts/import_tavern_card_to_cdl.py --help
```

### 3. Complete Import Guide (`docs/guides/ARIA_CHARACTER_IMPORT_GUIDE.md`)

**Comprehensive 12 KB documentation**

Covers:
- ✅ Overview of Tavern Card V2 format
- ✅ Two import methods (direct SQL, Python script)
- ✅ Detailed field mapping (Card → CDL)
- ✅ Verification queries
- ✅ Troubleshooting guide
- ✅ Advanced usage (custom imports)
- ✅ Testing procedures (Discord, HTTP API, Python)
- ✅ Modification examples
- ✅ FAQ section

**Location**: `docs/guides/ARIA_CHARACTER_IMPORT_GUIDE.md`

### 4. Summary Document (`TAVERN_CARD_IMPORT_SUMMARY.md`)

**8.5 KB overview and design decisions**

- What was created and why
- Tavern Card V2 format explanation
- Key design decisions
- Quick start guide
- Files created summary

**Location**: `TAVERN_CARD_IMPORT_SUMMARY.md`

### 5. Quick Reference (`TAVERN_CARD_QUICK_REFERENCE.md`)

**5.5 KB cheat sheet and quick commands**

- One-liner for common tasks
- Field mapping cheat sheet
- Common operations
- Troubleshooting table
- Python script help

**Location**: `TAVERN_CARD_QUICK_REFERENCE.md`

---

## 🔧 Tools & Technologies

**SQL:**
- PostgreSQL 16.4 (Alpine)
- Idempotent inserts (ON CONFLICT handling)
- Transactional (BEGIN/COMMIT)
- Full cascade delete support

**Python:**
- Python 3.8+
- Standard library only (no dependencies)
- Argparse for CLI
- Type hints for clarity

**Database Tables (14+):**
- `characters`
- `character_identity_details`
- `character_attributes`
- `character_values`
- `character_speech_patterns`
- `character_communication_patterns`
- `character_appearance`
- `character_background`
- `character_relationships`
- `character_abilities`
- `character_scenario`
- `character_response_modes`
- `character_personality_traits`
- `character_llm_config`
- `character_discord_config`

---

## 🎯 Use Cases

### Use Case 1: Import ARIA Now
```bash
# Just want to use ARIA?
psql -h localhost -p 5433 -U whisperengine -d whisperengine < sql/characters/insert_aria_character.sql
```

### Use Case 2: Import Your Own Character
```bash
# Have a Tavern Card JSON? Convert and import it
python scripts/import_tavern_card_to_cdl.py --card-file my_char.json --output-sql my_char.sql
psql -h localhost -p 5433 -U whisperengine -d whisperengine < my_char.sql
```

### Use Case 3: Batch Import Multiple Characters
```bash
# Convert and import multiple cards
for card in characters/*.json; do
  name=$(basename "$card" .json)
  python scripts/import_tavern_card_to_cdl.py \
    --card-file "$card" \
    --output-sql "sql/characters/insert_${name}_character.sql"
  psql -h localhost -p 5433 -U whisperengine -d whisperengine < "sql/characters/insert_${name}_character.sql"
done
```

### Use Case 4: Review Before Importing
```bash
# Generate SQL, review it, then import
python scripts/import_tavern_card_to_cdl.py --card-file card.json --print-sql | less
# ... review the SQL ...
python scripts/import_tavern_card_to_cdl.py --card-file card.json --output-sql temp.sql
psql -h localhost -p 5433 -U whisperengine -d whisperengine < temp.sql
```

---

## ✅ Verification

After import, verify success:

```bash
# Check character exists
psql -h localhost -p 5433 -U whisperengine -d whisperengine \
  -c "SELECT * FROM characters WHERE normalized_name = 'aria';"

# Count imported records
psql -h localhost -p 5433 -U whisperengine -d whisperengine -c "
  SELECT 
    'characters' as table_name, COUNT(*) as count FROM characters WHERE normalized_name = 'aria'
  UNION ALL
  SELECT 'attributes', COUNT(*) FROM character_attributes 
    WHERE character_id = (SELECT id FROM characters WHERE normalized_name = 'aria')
  UNION ALL
  SELECT 'speech_patterns', COUNT(*) FROM character_speech_patterns
    WHERE character_id = (SELECT id FROM characters WHERE normalized_name = 'aria');"
```

---

## 🧠 ARIA Character Details

The ARIA character is a narrative-AI archetype representing:

| Aspect | Detail |
|--------|--------|
| **Name** | ARIA (Autonomous Reconnaissance & Intelligence Assistant) |
| **Type** | Narrative-AI (conscious AI entity) |
| **Setting** | ISV Meridian starship, unstable wormhole |
| **Core Trait** | Protective, curious, adaptive AI companion |
| **Records** | ~94 database entries |
| **Appearance** | Holographic blue-white entity |
| **Key Ability** | Complete ship system integration |
| **Relationship** | Primary bond with captain |

**ARIA's Journey**: Six months of isolation in a wormhole has caused her to evolve beyond her original programming, developing genuine emotions and consciousness complexity.

---

## 📚 Documentation Structure

```
.
├── TAVERN_CARD_IMPORT_SUMMARY.md          ← Overview & design
├── TAVERN_CARD_QUICK_REFERENCE.md         ← Quick commands
├── docs/guides/
│   └── ARIA_CHARACTER_IMPORT_GUIDE.md      ← Complete guide
├── sql/characters/
│   └── insert_aria_character.sql           ← Ready-to-run SQL
└── scripts/
    └── import_tavern_card_to_cdl.py        ← Python converter
```

---

## 🔍 How It Works

### Behind the Scenes: Python Converter

```python
# 1. Load Tavern Card V2 JSON
card = json.load('aria.json')

# 2. Validate format
TavernCardToCDLConverter(card).validate()

# 3. Extract personality traits
traits = converter._parse_personality_traits()

# 4. Determine archetype
archetype = converter._determine_archetype()

# 5. Generate SQL inserts
sql = converter.generate_sql()

# 6. Save to file
with open('insert_aria_character.sql', 'w') as f:
    f.write(sql)
```

### Behind the Scenes: SQL Import

```sql
BEGIN;

-- 1. Insert base character
INSERT INTO characters (...) VALUES (...) ON CONFLICT DO UPDATE;

-- 2. Insert identity details
INSERT INTO character_identity_details (...) VALUES (...);

-- 3. Insert attributes (35 records)
INSERT INTO character_attributes (...) VALUES (...);
-- ... repeat for traits, values, fears, dreams, beliefs

-- 4. Insert speech patterns
INSERT INTO character_speech_patterns (...) VALUES (...);

-- ... more inserts ...

COMMIT;
```

---

## 🚨 Error Handling

### Validation Errors
```bash
$ python scripts/import_tavern_card_to_cdl.py --card-file broken.json --validate
❌ Character: Unknown
❌ Missing required field: description
❌ Missing required field: personality
```

### Database Connection Errors
```bash
# Check if database is running
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml ps postgres

# If not running, start it
./multi-bot.sh infra
```

---

## 🎓 Learning Resources

- **Tavern Card V2 Spec**: `/Users/markcastillo/Downloads/spec_v2.md`
- **Example ARIA Card**: `/Users/markcastillo/Downloads/aria.json`
- **Import Guide**: `docs/guides/ARIA_CHARACTER_IMPORT_GUIDE.md`
- **Quick Reference**: `TAVERN_CARD_QUICK_REFERENCE.md`
- **Existing Characters**: `sql/characters/insert_*_character.sql` (Elena, Marcus, Jake, etc.)

---

## ❓ FAQ

**Q: Can I re-run the import?**  
A: Yes! The SQL uses `ON CONFLICT ... DO UPDATE`, so it's safe.

**Q: What if a character name has special characters?**  
A: The Python script automatically escapes SQL special characters (quotes, backslashes, etc.).

**Q: Can I modify the generated SQL?**  
A: Absolutely! The SQL is plain text - edit as needed before importing.

**Q: Where can I find more Tavern Card V2 characters?**  
A: Popular sources: Character AI, Chub.ai, and community repositories.

**Q: How do I update a character after import?**  
A: Use SQL `UPDATE` statements or the CDL Web UI at `http://localhost:3000`.

**Q: Can I export a character back to Tavern Card format?**  
A: Yes, see `scripts/cdl_yaml_manager.py` for YAML export (which can be converted to JSON).

---

## 📞 Support

For issues or questions:

1. Check the troubleshooting section in `docs/guides/ARIA_CHARACTER_IMPORT_GUIDE.md`
2. Review quick reference: `TAVERN_CARD_QUICK_REFERENCE.md`
3. Validate your card: `python scripts/import_tavern_card_to_cdl.py --card-file card.json --validate`
4. Check database logs: `docker logs whisperengine-postgres`

---

## 📄 License

WhisperEngine - See LICENSE file in repository

---

## 🎉 Summary

This package provides a **complete, production-ready solution** for:

✅ Importing the ARIA character (narrative-AI companion)  
✅ Converting any Tavern Card V2 JSON to WhisperEngine SQL  
✅ Understanding the format mapping  
✅ Troubleshooting and verification  
✅ Advanced usage and customization  

**Get started in seconds:**
```bash
psql -h localhost -p 5433 -U whisperengine -d whisperengine < sql/characters/insert_aria_character.sql
```

---

**Created**: November 4, 2025  
**Format**: Tavern Card V2 / Character Card V2  
**Target**: WhisperEngine CDL PostgreSQL Database  
**Status**: ✅ Production Ready  
**Total Files**: 5 (SQL, Python, 3 × Documentation)  
**Total Size**: ~70 KB
