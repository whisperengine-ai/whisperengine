# CDL YAML Export/Import Guide

This guide covers exporting and importing WhisperEngine character definitions (CDL) as YAML files.

## Overview

WhisperEngine stores character definitions in a PostgreSQL database using the CDL (Character Definition Language) format. The `cdl_yaml_manager.py` script provides unified tools for:

1. **Exporting** characters from the database to human-readable YAML files
2. **Importing** characters from YAML files back into the database

## Why YAML?

- **Human-readable**: Easy to edit and review character definitions
- **Version control friendly**: Clean diffs for character changes
- **Portable**: Share character definitions between systems
- **Backup-friendly**: Simple text files for archival

## Installation

The script is already included in WhisperEngine. Ensure you have the required dependencies:

```bash
# Activate virtual environment
source .venv/bin/activate

# Dependencies are already in requirements.txt
pip install -r requirements.txt
```

## Usage

### Export Characters

#### Export a Single Character

```bash
# Export by normalized name (e.g., 'elena', 'marcus', 'gabriel')
python scripts/cdl_yaml_manager.py export elena

# Export to custom location
python scripts/cdl_yaml_manager.py export elena --output my_characters/elena.yaml
```

#### Export All Characters

```bash
# Export all active characters to timestamped backup directory
python scripts/cdl_yaml_manager.py export --all

# Output: backups/characters_yaml/YYYY-MM-DD/*.yaml
```

### Import Characters

#### Import a Single Character

```bash
# Import from YAML file
python scripts/cdl_yaml_manager.py import backups/characters_yaml/2025-10-12/elena_rodriguez.yaml

# Overwrite existing character
python scripts/cdl_yaml_manager.py import elena.yaml --overwrite
```

#### Import All Characters from Directory

```bash
# Import all YAML files from directory
python scripts/cdl_yaml_manager.py import backups/characters_yaml/2025-10-12/ --all

# Overwrite existing characters
python scripts/cdl_yaml_manager.py import backups/characters_yaml/2025-10-12/ --all --overwrite
```

## YAML File Structure

The exported YAML follows the CDL specification with this structure:

```yaml
cdl_version: '1.0'
character:
  metadata:
    name: Elena Rodriguez
    database_id: 1
    normalized_name: elena
    export_date: '2025-10-13T12:00:00'
    schema_version: '1.0'
    source: whisperengine_postgresql
  
  identity:
    name: Elena Rodriguez
    occupation: Marine Biologist & Research Scientist
    description: Elena has weathered hands...
    archetype: real_world
    allow_full_roleplay_immersion: false
    age: 29
    gender: female
    location: San Diego, California
  
  values:
    - key: core_value_1
      description: Environmental conservation and marine protection
    - key: fear_1
      description: Coral reef collapse and ocean acidification
  
  interests:
    - marine biology
    - ocean conservation
    - diving
    - research
  
  personality:
    big_five:
      openness: 85
      conscientiousness: 80
      extraversion: 70
      agreeableness: 75
      neuroticism: 40
    traits:
      enthusiasm: high
      patience: moderate
  
  communication:
    typical_responses:
      greeting:
        - "Hey there! How's it going?"
      enthusiasm:
        - "That's so exciting!"
    emotional_expressions:
      joy: Bright smile, animated gestures
      concern: Furrowed brow, serious tone
  
  background:
    life_phases:
      - phase_name: Childhood
        age_range: 0-12
        key_events: Growing up near the ocean
        emotional_impact: Deep connection to marine life
  
  relationships:
    - person_name: Dr. Sarah Mitchell
      relationship_type: Mentor
      description: Research advisor at Scripps
      emotional_significance: High respect and gratitude
  
  behavioral_patterns:
    conversation_style:
      - Uses oceanic metaphors naturally
      - Asks follow-up questions
  
  speech_patterns:
    voice:
      tone: Warm and engaging
      pace: Moderate to fast when excited
      accent: Slight California inflection
    common_phrases:
      - phrase: "That's fascinating!"
        context: When discussing marine topics
  
  emotional_profile:
    emotional_patterns:
      - emotion_type: excitement
        intensity: high
        triggers: Marine conservation breakthroughs
        typical_response: Animated discussion
```

## Data Preservation

The export/import system preserves:

- ✅ **Character identity** (name, occupation, description, archetype)
- ✅ **Personality traits** (Big Five scores, custom traits)
- ✅ **Values and interests** (core values, fears, topic interests)
- ✅ **Communication patterns** (typical responses, emotional expressions)
- ✅ **Background/backstory** (life phases, formative experiences)
- ✅ **Relationships** (important people, emotional significance)
- ✅ **Behavioral patterns** (response patterns, habits)
- ✅ **Speech patterns** (voice characteristics, common phrases)
- ✅ **Emotional profile** (emotional patterns, triggers)

## Backup Strategy

### Regular Backups

```bash
# Daily backup of all characters
python scripts/cdl_yaml_manager.py export --all

# Output: backups/characters_yaml/YYYY-MM-DD/
```

### Pre-Update Backups

Before making major character updates:

```bash
# Export specific character before editing
python scripts/cdl_yaml_manager.py export elena
```

### Version Control

Add YAML backups to git for change tracking:

```bash
git add backups/characters_yaml/
git commit -m "Character backup: Elena Rodriguez v2.1"
```

## Advanced Usage

### Character Migration

Move characters between WhisperEngine instances:

```bash
# On source system
python scripts/cdl_yaml_manager.py export elena --output /tmp/elena.yaml

# Copy file to target system
scp /tmp/elena.yaml target-server:/tmp/

# On target system
python scripts/cdl_yaml_manager.py import /tmp/elena.yaml
```

### Character Versioning

Maintain multiple versions of a character:

```bash
# Export current version
python scripts/cdl_yaml_manager.py export elena --output elena_v2.1.yaml

# Make database changes...

# Export new version
python scripts/cdl_yaml_manager.py export elena --output elena_v2.2.yaml

# Restore previous version if needed
python scripts/cdl_yaml_manager.py import elena_v2.1.yaml --overwrite
```

### Bulk Character Updates

Edit multiple characters in YAML, then re-import:

```bash
# Export all
python scripts/cdl_yaml_manager.py export --all

# Edit YAML files in backups/characters_yaml/YYYY-MM-DD/

# Re-import all changes
python scripts/cdl_yaml_manager.py import backups/characters_yaml/YYYY-MM-DD/ --all --overwrite
```

## Safety Features

### Overwrite Protection

By default, import will **not** overwrite existing characters:

```bash
# This will fail if character exists
python scripts/cdl_yaml_manager.py import elena.yaml

# Use --overwrite to replace existing
python scripts/cdl_yaml_manager.py import elena.yaml --overwrite
```

### Data Validation

The import process:

1. Validates YAML structure
2. Checks for required fields
3. Clears old data before importing (when overwriting)
4. Maintains referential integrity
5. Reports detailed error messages

### Error Handling

If import fails:

```bash
❌ Failed to import character: Invalid YAML structure: missing 'character' section
```

The database remains unchanged - imports are atomic per character.

## Troubleshooting

### Database Connection Issues

```bash
# Check environment variables
echo $POSTGRES_HOST
echo $POSTGRES_PORT

# Test connection
psql -h localhost -p 5433 -U whisperengine -d whisperengine
```

### Character Not Found

```bash
# List available characters
psql -h localhost -p 5433 -U whisperengine -d whisperengine \
  -c "SELECT name, normalized_name FROM characters WHERE is_active = true;"
```

### YAML Parse Errors

```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('elena.yaml'))"
```

### Permission Issues

```bash
# Ensure backup directory is writable
mkdir -p backups/characters_yaml
chmod 755 backups/characters_yaml
```

## Integration with WhisperEngine

### Character Updates

After importing character changes, restart the bot to reload:

```bash
# Import updated character
python scripts/cdl_yaml_manager.py import elena_updated.yaml --overwrite

# Restart bot to reload character
./multi-bot.sh restart elena
```

### Development Workflow

1. **Export** current character for baseline
2. **Edit** YAML file with desired changes
3. **Import** with `--overwrite` flag
4. **Test** changes in Discord
5. **Commit** YAML to version control if satisfied

## Related Documentation

- [CDL Specification](../architecture/CDL_SPECIFICATION.md)
- [Character System Overview](../architecture/CHARACTER_SYSTEM.md)
- [Database Schema](../database/CDL_DATABASE_SCHEMA.md)

## Example Workflows

### Create New Character from Template

```bash
# Export existing character as template
python scripts/cdl_yaml_manager.py export elena --output templates/character_template.yaml

# Edit template (change name, traits, etc.)
vim templates/character_template.yaml

# Import as new character
python scripts/cdl_yaml_manager.py import templates/my_new_character.yaml
```

### Share Character with Community

```bash
# Export character
python scripts/cdl_yaml_manager.py export my_custom_character

# Share YAML file
# Others can import: python scripts/cdl_yaml_manager.py import shared_character.yaml
```

### Disaster Recovery

```bash
# Regular backups prevent data loss
python scripts/cdl_yaml_manager.py export --all

# After database issue, restore all characters
python scripts/cdl_yaml_manager.py import backups/characters_yaml/2025-10-12/ --all --overwrite
```

## Performance Notes

- **Export**: ~1-2 seconds per character
- **Import**: ~2-3 seconds per character (includes database writes)
- **Bulk operations**: Processes characters sequentially for data integrity

## Future Enhancements

Planned improvements:

- [ ] Character validation before import
- [ ] Diff tool for comparing character versions
- [ ] Selective import (specific sections only)
- [ ] JSON export support (in addition to YAML)
- [ ] Character migration assistant for schema changes
- [ ] Web UI for YAML editing

## Support

For issues or questions:

1. Check the [YAML file structure](#yaml-file-structure) section
2. Review [Troubleshooting](#troubleshooting) guide
3. Open issue on GitHub with error details
4. Include YAML file (redact sensitive info)
