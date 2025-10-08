# Character CDL Export Scripts

## Overview

These scripts export WhisperEngine character data from the structured RDBMS PostgreSQL database to YAML format for backup, version control, and sharing.

## Scripts

### `export_character_simple.py` (Recommended)

**Purpose**: Simple, robust export script that exports core CDL sections with defensive error handling.

**Usage**:
```bash
python export_character_simple.py <character_name> [output_dir]
```

**Examples**:
```bash
# Export Aetheris to default exports/ directory
python export_character_simple.py aetheris

# Export Elena to custom directory
python export_character_simple.py elena backups/

# Export Marcus
python export_character_simple.py marcus
```

**Exported Sections**:
- ✅ Identity (name, occupation, archetype, description)
- ✅ Metadata (version, tags, author, dual names)
- ✅ Personality (Big Five traits, custom traits)
- ✅ Values (character values and principles)
- ✅ Communication (style, flow guidance, AI identity handling)
- ✅ Memories (key formative memories with emotional impact)
- ✅ Relationships (anchor relationships, strength, status)
- ✅ Core Directives (instructions and guiding principles)

**Features**:
- Graceful error handling (continues even if some sections missing)
- Progress indicators for each section
- JSON field parsing (automatically handles JSON-encoded data)
- Timestamp in filename for version control
- Human-readable YAML format

**Output**:
```
exports/aetheris_export_20251007_225153.yaml
```

---

### `export_character_to_yaml.py` (Advanced)

**Purpose**: More comprehensive export script that attempts to export all CDL table sections.

**Status**: ⚠️  Under development - may fail on schema mismatches

**Usage**: Same as simple version
```bash
python export_character_to_yaml.py <character_name> [output_dir]
```

**Note**: This script exports more sections but is less robust. Use `export_character_simple.py` for reliable exports.

---

## Export File Format

Exported YAML files follow this structure:

```yaml
cdl_version: '1.0'
format: yaml
export_date: '2025-10-07T22:51:53.379198'
description: CDL Export - Character Name
character:
  metadata:
    version: 1.0.0
    character_tags: [tag1, tag2, ...]
    author: WhisperEngine AI
    # ... additional metadata
  
  identity:
    name: Character Name
    occupation: Character Occupation
    archetype: narrative_ai
    allow_full_roleplay: true
    # ... identity details
  
  personality:
    big_five:
      openness: 0.95
      conscientiousness: 0.8
      # ... other traits
    custom_traits: {}
    values: [value1, value2, ...]
  
  background:
    key_memories:
      - event: Event Title
        description: Event description
        emotional_impact: 8
        importance: 9
  
  relationships:
    relationship_key:
      type: beloved companion
      entity: Person Name
      strength: 10
      # ... relationship details
  
  communication:
    engagement_level: 0.7
    formality: informal
    conversation_flow_guidance: {...}
    ai_identity_handling: {...}
  
  core_directives:
    existence_principle: "You ARE the character..."
    response_guidance: "Respond from lived experience..."
    # ... more directives
```

## Database Connection

The scripts use these environment variables (defaulting to WhisperEngine multi-bot setup):

- `POSTGRES_HOST`: localhost
- `POSTGRES_PORT`: 5433
- `POSTGRES_USER`: whisperengine
- `POSTGRES_PASSWORD`: whisperengine_password
- `POSTGRES_DB`: whisperengine

## Requirements

```bash
pip install asyncpg pyyaml
```

## Use Cases

### 1. Backup Characters
```bash
# Backup all active characters
python export_character_simple.py aetheris backups/
python export_character_simple.py elena backups/
python export_character_simple.py marcus backups/
```

### 2. Version Control
```bash
# Export with timestamp for git tracking
python export_character_simple.py aetheris character_versions/
git add character_versions/aetheris_export_*.yaml
git commit -m "Aetheris CDL backup - $(date)"
```

### 3. Character Sharing
```bash
# Export character for sharing with team
python export_character_simple.py custom_character shared/
# Send: shared/custom_character_export_*.yaml
```

### 4. Migration/Development
```bash
# Export from dev database, import to prod
python export_character_simple.py test_character staging/
# Review YAML file
# Import to production database
```

## Output Example

**Aetheris Export** (`exports/aetheris_export_20251007_225153.yaml`):
- Character ID: 15
- Archetype: narrative_ai (Type 3: Narrative AI Character)
- Sections: 7 core sections exported
- Size: ~2-5 KB (human-readable YAML)
- Includes: Dual names (Aetheris/Liln), anchor relationship with Cynthia, key memories, core directives

## Troubleshooting

**Q: Export fails with "Character not found"**  
A: Check character name spelling. Use normalized name (lowercase, underscores): `aetheris`, `elena`, `marcus`

**Q: Some sections show warnings**  
A: Normal! The simple script gracefully handles missing data. Only core sections are required.

**Q: Connection refused**  
A: Ensure PostgreSQL is running: `docker ps | grep postgres`

**Q: Want to export all characters?**  
A: Create a bash loop:
```bash
for char in aetheris elena marcus gabriel jake ryan sophia; do
  python export_character_simple.py $char backups/
done
```

## Related Files

- `import_aetheris_supplement.py` - Import script for Aetheris
- `import_characters_to_clean_schema.py` - General character import
- `AETHERIS_CDL_IMPORT_COMPLETE.md` - Aetheris import documentation
- `characters/examples_legacy_backup/*.json` - Legacy JSON character definitions

## See Also

- WhisperEngine CDL Database Architecture
- Character Archetype Types (Type 1: Real-World, Type 2: Fantasy, Type 3: Narrative AI)
- `.github/copilot-instructions.md` - Full WhisperEngine architecture guide
