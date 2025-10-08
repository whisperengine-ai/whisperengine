# CDL JSON to Database Migration Guide

**WhisperEngine CDL Migration Documentation**  
*Migrating Legacy JSON Character Files to PostgreSQL Database*

Last Updated: October 8, 2025  
Version: 2.0

## Overview

WhisperEngine has migrated from JSON file-based character storage to a PostgreSQL database-based CDL (Character Definition Language) system. This guide covers how to migrate your existing JSON character files to the new database schema.

## Migration Scripts Available

### 1. `batch_import_characters.py` - Simple Migration
**Best for:** Basic character data migration with minimal complexity

**Features:**
- ✅ Imports core character data (identity, personality, communication style)
- ✅ Handles character archetype mapping
- ✅ Uses enhanced JSONB manager for database operations
- ✅ Pre-configured character mappings for common characters
- ✅ Simple success/failure reporting
- ✅ Database verification after import

**Supports:** Marcus, Gabriel, Jake, Ryan, Elena, and other core characters

### 2. `comprehensive_character_import.py` - Advanced Migration
**Best for:** Rich character data with detailed attributes

**Features:**
- ✅ Imports comprehensive character data (appearance, background, abilities)
- ✅ Handles communication patterns and custom instructions
- ✅ Supports multiple JSON formats (Elena format vs Marcus format)
- ✅ Merges multiple JSON files for the same character
- ✅ Conflict resolution with intelligent data merging
- ✅ Rich data categorization and importance weighting
- ✅ Enhanced CDL manager testing and validation

**Data Categories Imported:**
- Physical and digital appearance
- Education and career history
- Personal and cultural background
- Skills, abilities, and expertise
- Communication patterns and preferences
- Custom instructions and metadata

## Prerequisites

### Database Setup
```bash
# Ensure PostgreSQL is running with WhisperEngine schema
./multi-bot.sh start all  # This starts PostgreSQL container on port 5433

# Verify database connectivity
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5433
export POSTGRES_DB=whisperengine
export POSTGRES_USER=whisperengine
export POSTGRES_PASSWORD=whisperengine_password
```

### Python Environment
```bash
# Activate virtual environment
source .venv/bin/activate

# Ensure dependencies are installed
pip install -r requirements.txt
```

## Migration Workflows

### Quick Migration (Recommended for Most Users)

```bash
# 1. Verify your JSON files are in the legacy backup directory
ls characters/examples_legacy_backup/*.json

# 2. Run the simple batch import
python batch_import_characters.py

# 3. Verify import success
# Script will show summary of successful/failed imports
# Database verification is automatic
```

**Expected Output:**
```
📁 Processing marcus...
✅ marcus imported successfully (ID: 1)

📁 Processing elena...
✅ elena imported successfully (ID: 2)

📊 Batch Import Summary:
✅ Successfully imported: 5 characters
   - marcus
   - elena
   - jake
   - gabriel
   - ryan

🔍 Verifying all characters in database:
📚 Total characters in database: 5
   - Elena Rodriguez (elena) - Marine Biologist
   - Marcus Thompson (marcus) - AI Researcher
   - Jake Sterling (jake) - Adventure Photographer
   - Gabriel (gabriel) - British Gentleman AI companion
   - Ryan Chen (ryan) - Indie Game Developer

🎉 All characters successfully imported to enhanced JSONB database!
```

### Advanced Migration (For Rich Character Data)

```bash
# 1. Verify legacy JSON files
ls characters/examples_legacy_backup/*.json

# 2. Run comprehensive import for rich data
python comprehensive_character_import.py

# 3. Review detailed import results
# Script shows detailed data category imports
```

**Expected Output:**
```
🚀 Starting comprehensive character import...
Found 9 unique characters with 12 total files

Importing rich data from elena for character 'elena'...
✅ Successfully imported rich data from elena

Importing rich data from marcus for character 'marcus'...
✅ Successfully imported rich data from marcus

✅ Comprehensive character import complete!

🧪 Testing enhanced CDL manager...
✅ Enhanced manager test successful!
   Core CDL keys: ['identity', 'personality', 'communication_style', 'values', 'appearance', 'background', 'abilities', 'communication_patterns']
   🎭 Appearance categories: ['physical', 'digital']
   📚 Background categories: ['education', 'career', 'personal', 'cultural']
   💪 Abilities categories: ['skills', 'expertise', 'knowledge']
   💬 Communication patterns: ['style', 'preferences', 'tone']
   📋 Custom instructions: ['user_interaction', 'content_guidelines']
```

## JSON File Structure Support

### Supported JSON Formats

#### Elena Format (Direct Structure)
```json
{
    "character": {
        "identity": {
            "name": "Elena Rodriguez",
            "occupation": "Marine Biologist"
        },
        "personality": {
            "traits": ["curious", "patient", "analytical"]
        },
        "physical_appearance": {
            "hair": "Long, dark brown",
            "eyes": "Warm brown"
        },
        "background": {
            "education": ["Ph.D. in Marine Biology"],
            "career_history": ["Research Scientist at Ocean Institute"]
        }
    }
}
```

#### Marcus Format (Nested Structure)
```json
{
    "character": {
        "character": {
            "identity": {
                "name": "Marcus Thompson"
            }
        }
    }
}
```

### File Naming Conventions

**Supported patterns:**
- `elena.json` → Character: elena
- `marcus.json` → Character: marcus  
- `elena.backup_20251006_223336.json` → Character: elena (backup)
- `sophia_v2.json` → Character: sophia

**Skipped patterns:**
- `template.json` (templates)
- `example.json` (examples)
- `test.json` (test files)

## Database Schema Overview

### Core Tables

```sql
-- Main character table
characters_v2 (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    normalized_name VARCHAR(255) UNIQUE,
    bot_name VARCHAR(100),
    archetype VARCHAR(100),
    cdl_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Rich character data tables
character_appearance (
    character_id INTEGER REFERENCES characters_v2(id),
    category VARCHAR(50),  -- 'physical', 'digital'
    attribute VARCHAR(100),
    value TEXT
);

character_background (
    character_id INTEGER REFERENCES characters_v2(id),
    category VARCHAR(50),  -- 'education', 'career', 'personal', 'cultural'
    title VARCHAR(200),
    description TEXT,
    importance_level INTEGER DEFAULT 5
);

character_abilities (
    character_id INTEGER REFERENCES characters_v2(id),
    category VARCHAR(50),  -- 'skills', 'expertise', 'knowledge'
    title VARCHAR(200),
    description TEXT,
    proficiency_level INTEGER DEFAULT 5
);
```

### Data Migration Mapping

| JSON Field | Database Location | Migration Script |
|------------|------------------|------------------|
| `identity` | `characters_v2.cdl_data->identity` | Both scripts |
| `personality` | `characters_v2.cdl_data->personality` | Both scripts |
| `communication_style` | `characters_v2.cdl_data->communication_style` | Both scripts |
| `physical_appearance` | `character_appearance` table | Comprehensive only |
| `background.education` | `character_background` table | Comprehensive only |
| `background.career_history` | `character_background` table | Comprehensive only |
| `abilities` | `character_abilities` table | Comprehensive only |
| `digital_communication` | `character_appearance` table | Comprehensive only |

## Troubleshooting

### Common Issues

#### 1. Database Connection Errors
```bash
# Error: connection refused to localhost:5433
# Solution: Start the database container
./multi-bot.sh start all

# Verify containers are running
docker ps | grep postgres
```

#### 2. JSON Parse Errors
```bash
# Error: JSONDecodeError: Expecting value
# Solution: Check JSON file syntax
python -m json.tool characters/examples_legacy_backup/problematic_file.json
```

#### 3. Character Already Exists
```bash
# Warning: Character 'elena' already exists
# Solution: Migration scripts handle upserts automatically
# Existing data will be updated with new information
```

#### 4. Missing Character Files
```bash
# Error: Character file not found
# Solution: Check file paths and ensure files exist
ls characters/examples_legacy_backup/*.json
```

### Validation Commands

```bash
# Verify characters in database
python -c "
import asyncio
import asyncpg

async def check_chars():
    conn = await asyncpg.connect('postgresql://whisperengine:whisperengine_password@localhost:5433/whisperengine')
    chars = await conn.fetch('SELECT name, bot_name FROM characters_v2')
    for char in chars:
        print(f'{char[\"name\"]} ({char[\"bot_name\"]})')
    await conn.close()

asyncio.run(check_chars())
"

# Test enhanced CDL manager
python -c "
import asyncio
from src.characters.cdl.enhanced_cdl_manager import create_enhanced_cdl_manager
import asyncpg

async def test_manager():
    pool = await asyncpg.create_pool('postgresql://whisperengine:whisperengine_password@localhost:5433/whisperengine')
    manager = create_enhanced_cdl_manager(pool)
    elena = await manager.get_character_by_name('elena')
    print('Elena data keys:', list(elena.keys()) if elena else 'Not found')
    await pool.close()

asyncio.run(test_manager())
"
```

## Post-Migration Steps

### 1. Verify Character Availability
```bash
# Test character loading in bot environment
./multi-bot.sh start elena
docker logs whisperengine-elena-bot --tail 20

# Look for successful character loading messages
# "✅ Character loaded: Elena Rodriguez"
```

### 2. Test Character Responses
```bash
# Send a test message to verify CDL integration
curl -X POST http://localhost:9091/api/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user", "message": "Tell me about your marine biology background"}'
```

### 3. Validate Rich Data (Comprehensive Migration Only)
```bash
# Check that rich data was imported correctly
python -c "
import asyncio
import asyncpg

async def check_rich_data():
    conn = await asyncpg.connect('postgresql://whisperengine:whisperengine_password@localhost:5433/whisperengine')
    
    # Check appearance data
    appearances = await conn.fetch('SELECT * FROM character_appearance LIMIT 5')
    print('Appearance entries:', len(appearances))
    
    # Check background data  
    backgrounds = await conn.fetch('SELECT * FROM character_background LIMIT 5')
    print('Background entries:', len(backgrounds))
    
    # Check abilities data
    abilities = await conn.fetch('SELECT * FROM character_abilities LIMIT 5')
    print('Abilities entries:', len(abilities))
    
    await conn.close()

asyncio.run(check_rich_data())
"
```

## Migration Script Comparison

| Feature | batch_import_characters.py | comprehensive_character_import.py |
|---------|---------------------------|-----------------------------------|
| **Complexity** | Simple | Advanced |
| **Core CDL Data** | ✅ Yes | ✅ Yes |
| **Rich Appearance Data** | ❌ No | ✅ Yes |
| **Background History** | ❌ No | ✅ Yes |
| **Abilities & Skills** | ❌ No | ✅ Yes |
| **Multi-file Merging** | ❌ No | ✅ Yes |
| **Conflict Resolution** | Basic | Advanced |
| **Importance Weighting** | ❌ No | ✅ Yes |
| **Character Count** | Pre-configured list | Auto-discovery |
| **Format Support** | Single format | Multiple formats |
| **Testing Integration** | Basic verification | Enhanced manager testing |

## Best Practices

### 1. Backup Before Migration
```bash
# Export current database state before migration
pg_dump postgresql://whisperengine:whisperengine_password@localhost:5433/whisperengine > backup_before_migration.sql
```

### 2. Start with Simple Migration
- Use `batch_import_characters.py` first for core functionality
- Upgrade to `comprehensive_character_import.py` if you need rich data

### 3. Test Individual Characters
```bash
# Test one character at a time during migration
# Modify script to import single character for testing
```

### 4. Monitor Database Size
```bash
# Check database size after migration
python -c "
import asyncio
import asyncpg

async def check_size():
    conn = await asyncpg.connect('postgresql://whisperengine:whisperengine_password@localhost:5433/whisperengine')
    
    # Character count
    char_count = await conn.fetchval('SELECT COUNT(*) FROM characters_v2')
    print(f'Characters: {char_count}')
    
    # Rich data counts
    appearance_count = await conn.fetchval('SELECT COUNT(*) FROM character_appearance')
    background_count = await conn.fetchval('SELECT COUNT(*) FROM character_background') 
    abilities_count = await conn.fetchval('SELECT COUNT(*) FROM character_abilities')
    
    print(f'Appearance entries: {appearance_count}')
    print(f'Background entries: {background_count}')
    print(f'Abilities entries: {abilities_count}')
    
    await conn.close()

asyncio.run(check_size())
"
```

## Next Steps After Migration

1. **Character Testing**: Test each migrated character via Discord or HTTP API
2. **Rich Data Validation**: Verify that comprehensive data enhances character responses
3. **Performance Monitoring**: Monitor database query performance with rich data
4. **Backup Strategy**: Establish regular database backups
5. **Documentation Updates**: Update character documentation to reflect database storage

## Support

For migration issues or questions:
1. Check the troubleshooting section above
2. Review database logs: `docker logs whisperengine-postgres`
3. Verify JSON file structure matches supported formats
4. Test with individual character files first
5. Review the comprehensive character import output for detailed error information

---

*This guide covers WhisperEngine's CDL JSON to PostgreSQL database migration process. The migration preserves all character data while enabling enhanced database-driven features like importance weighting, rich categorization, and improved query performance.*