# Conversation Flow Guidance Migration Guide

This guide covers the complete migration process from JSON text fields to normalized RDBMS tables for conversation flow guidance data.

## Overview

The migration transforms conversation flow guidance from JSON text fields to a normalized relational structure with 7 specialized tables, enabling proper web UI editing and eliminating JSON handling complexity.

## Migration Components

### 1. Schema Migration (Alembic)
**File**: `alembic/versions/20251013_0146_8b77eda62e71_normalize_conversation_flow_guidance_to_.py`

Creates the normalized table structure:
- `character_conversation_modes` - Character-specific conversation modes
- `character_mode_guidance` - Avoid/encourage guidance items
- `character_mode_examples` - Example responses for each mode
- `character_general_conversation` - General conversation settings
- `character_response_style` - Response style configuration
- `character_response_style_items` - Individual style rules
- `character_response_patterns` - Response pattern templates

### 2. Data Migration Script
**File**: `alembic/data_migrations/20251013_migrate_conversation_flow_data.py`

Migrates existing JSON data to the normalized tables with proper parsing and validation.

## Migration Process

### Step 1: Backup Database
```bash
# Create a backup before migration
pg_dump -h localhost -p 5433 -U whisperengine whisperengine > backup_before_conversation_flow_migration.sql
```

### Step 2: Apply Schema Migration
```bash
# Run the Alembic schema migration
alembic upgrade head
```

This creates the 7 new normalized tables with proper constraints and indexes.

### Step 3: Run Data Migration
```bash
# Execute the data migration script
python alembic/data_migrations/20251013_migrate_conversation_flow_data.py
```

Expected output:
```
🚀 Starting conversation flow guidance data migration
Database: localhost:5433/whisperengine
✅ Connected to database
Found 10 characters with conversation flow guidance
✅ Migrated elena: 3 modes, 12 guidance items, 8 examples
✅ Migrated marcus: 2 modes, 8 guidance items, 6 examples
... (continues for all characters)

📊 MIGRATION RESULTS:
  Characters Processed: 10
  Conversation Modes Created: 25
  Guidance Items Created: 96
  Examples Created: 58
  Errors: 0

✅ Migration completed successfully!
```

### Step 4: Validate Migration
```bash
# Test that characters load from normalized tables
export DISCORD_BOT_NAME=elena
python -c "
from src.characters.cdl.enhanced_cdl_manager import EnhancedCDLManager
import asyncio

async def test():
    manager = EnhancedCDLManager()
    await manager.initialize()
    guidance = await manager._load_conversation_flow_guidance(1)
    print(f'✅ Loaded {len(guidance)} conversation modes from RDBMS')

asyncio.run(test())
"
```

### Step 5: Clean Up (Optional)
After validating the migration, you can remove the old JSON fields:

```sql
-- Remove the old JSON text field (optional - keep for rollback safety initially)
-- ALTER TABLE characters DROP COLUMN conversation_flow_guidance;
```

## Rollback Process

If issues are discovered, you can rollback:

### 1. Rollback Alembic Migration
```bash
# Rollback the schema migration
alembic downgrade -1
```

### 2. Restore Database Backup
```bash
# If needed, restore from backup
psql -h localhost -p 5433 -U whisperengine whisperengine < backup_before_conversation_flow_migration.sql
```

## Benefits

### Before Migration
- Massive JSON structures (3847+ characters) dumped into LLM prompts
- Complex JSON parsing and error handling throughout codebase
- Impossible to create web UI for character editing
- No data validation or constraints on conversation flow data

### After Migration
- Clean, human-readable LLM prompts (463 characters vs 3847+)
- Proper relational data structure with constraints and indexes
- Web UI ready - no JSON handling complexity
- Proper data validation and referential integrity
- Optimized database queries instead of JSON parsing

## Database Schema Details

### Character Conversation Modes
```sql
CREATE TABLE character_conversation_modes (
    id SERIAL PRIMARY KEY,
    character_id INTEGER NOT NULL REFERENCES characters(id),
    mode_name VARCHAR(100) NOT NULL,
    energy_level TEXT,
    approach TEXT,
    transition_style TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(character_id, mode_name)
);
```

### Character Mode Guidance
```sql
CREATE TABLE character_mode_guidance (
    id SERIAL PRIMARY KEY,
    mode_id INTEGER NOT NULL REFERENCES character_conversation_modes(id) ON DELETE CASCADE,
    guidance_type VARCHAR(20) NOT NULL CHECK (guidance_type IN ('avoid', 'encourage')),
    guidance_text TEXT NOT NULL,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

*[Additional tables follow similar patterns - see migration file for complete schema]*

## Verification Queries

### Check Migration Results
```sql
-- Count migrated data
SELECT 
    (SELECT COUNT(*) FROM character_conversation_modes) as modes,
    (SELECT COUNT(*) FROM character_mode_guidance) as guidance_items,
    (SELECT COUNT(*) FROM character_mode_examples) as examples,
    (SELECT COUNT(*) FROM character_general_conversation) as general_configs,
    (SELECT COUNT(*) FROM character_response_style) as response_styles;
```

### View Character Modes
```sql
-- See all modes for a character
SELECT c.normalized_name, ccm.mode_name, ccm.energy_level, ccm.approach
FROM characters c
JOIN character_conversation_modes ccm ON c.id = ccm.character_id
WHERE c.normalized_name = 'elena'
ORDER BY ccm.mode_name;
```

### Check Guidance Items
```sql
-- See guidance for a specific mode
SELECT ccm.mode_name, cmg.guidance_type, cmg.guidance_text
FROM character_conversation_modes ccm
JOIN character_mode_guidance cmg ON ccm.id = cmg.mode_id
JOIN characters c ON ccm.character_id = c.id
WHERE c.normalized_name = 'elena' AND ccm.mode_name = 'creative'
ORDER BY cmg.guidance_type, cmg.sort_order;
```

## Integration Points

The Enhanced CDL Manager (`src/characters/cdl/enhanced_cdl_manager.py`) automatically uses the normalized tables via the `_load_conversation_flow_guidance()` method. No code changes required for existing character loading logic.

The CDL AI Integration (`src/prompts/cdl_ai_integration.py`) receives clean, formatted guidance data instead of raw JSON, resulting in much cleaner LLM prompts.

## Future Web UI Development

With this normalized structure, web UI development can now:

1. **Character Mode Management**: CRUD operations on conversation modes
2. **Guidance Editing**: Add/edit/remove avoid/encourage guidance items
3. **Example Management**: Manage example responses for each mode
4. **Response Style Configuration**: Edit core principles and formatting rules
5. **Validation**: Real-time validation using database constraints
6. **Preview**: Generate prompt previews showing how changes affect LLM input

The normalized structure eliminates all JSON handling complexity and provides a clean, type-safe API for web development.