# Migration Fix: Emoji Columns Error

## Problem Description

When running the latest Docker image, you may encounter this error during database migration:

```
ERROR: column "emoji_frequency" of relation "characters" does not exist
ERROR: current transaction is aborted, commands ignored until end of transaction block
```

## Root Cause

This error occurs when:

1. **Docker Image Timing Issue**: The Docker image was built **before** the `emoji_personality_cols` migration was added to the codebase
2. **Migration Dependency Chain**: The comments migration (`a1b2c3d4e5f6`) tries to add comments to emoji columns that don't exist yet
3. **Transaction Abort**: PostgreSQL aborts the entire transaction when one COMMENT statement fails, causing all subsequent statements to fail with `InFailedSqlTransaction`

## Migration Chain

The correct migration sequence is:

```
baseline → ... → drop_legacy_roleplay → emoji_personality_cols → ... → 5891d5443712 → a1b2c3d4e5f6 (comments)
```

However, if the Docker image was built before `emoji_personality_cols` was added, the database won't have these columns:
- `emoji_frequency`
- `emoji_style`
- `emoji_combination`
- `emoji_placement`
- `emoji_age_demographic`
- `emoji_cultural_influence`

## Solution

### Immediate Fix (Applied)

The migration `20251015_1200_add_cdl_table_and_column_comments.py` has been updated to use **PostgreSQL SAVEPOINTs**:

```python
# Create savepoint before executing
connection.execute(sa.text(f"SAVEPOINT {savepoint_name}"))
connection.execute(sa.text(stmt))
# Release savepoint on success
connection.execute(sa.text(f"RELEASE SAVEPOINT {savepoint_name}"))
```

This allows the migration to:
1. Skip comments for missing columns gracefully
2. Continue processing remaining COMMENT statements
3. Complete successfully even if some columns don't exist

### What Happens Now

When you run migrations with the updated code:

1. ✅ **Comments for existing columns** are applied successfully
2. ⚠️ **Comments for missing emoji columns** are skipped with warning messages:
   ```
   ⚠️  Skipped comment for characters.emoji_frequency (column does not exist)
   ⚠️  Skipped comment for characters.emoji_style (column does not exist)
   ```
3. ✅ **Migration completes successfully** and your bots can start

### Future Behavior

When the `emoji_personality_cols` migration is eventually applied (in a future Docker image rebuild):
- The emoji columns will be created with proper defaults
- The comments migration can be re-run to add the missing comments
- OR you can manually add comments later if needed

## For Users: How to Resolve

### Option 1: Pull Latest Code (Recommended)

```bash
# Pull latest code with the SAVEPOINT fix
git pull origin main

# Rebuild your Docker image
docker compose build

# Run migrations - they will now complete successfully
docker compose up -d
```

### Option 2: Use Pre-Built Image with Fix

Wait for the next Docker Hub image release that includes the SAVEPOINT fix, then:

```bash
docker pull whisperengine/whisperengine:latest
docker compose up -d
```

### Option 3: Manual Database Fix (Advanced)

If you want to manually add the missing columns:

```sql
-- Connect to your PostgreSQL database
ALTER TABLE characters ADD COLUMN emoji_frequency VARCHAR(50) NOT NULL DEFAULT 'moderate';
ALTER TABLE characters ADD COLUMN emoji_style VARCHAR(100) NOT NULL DEFAULT 'general';
ALTER TABLE characters ADD COLUMN emoji_combination VARCHAR(50) NOT NULL DEFAULT 'text_with_accent_emoji';
ALTER TABLE characters ADD COLUMN emoji_placement VARCHAR(50) NOT NULL DEFAULT 'end_of_message';
ALTER TABLE characters ADD COLUMN emoji_age_demographic VARCHAR(50) NOT NULL DEFAULT 'millennial';
ALTER TABLE characters ADD COLUMN emoji_cultural_influence VARCHAR(100) NOT NULL DEFAULT 'general';

-- Add comments
COMMENT ON COLUMN characters.emoji_frequency IS 'How often character uses emojis';
COMMENT ON COLUMN characters.emoji_style IS 'Emoji style preference';
-- etc...
```

## Technical Details

### Why SAVEPOINTs?

PostgreSQL transactions have an important behavior:
- When **any** SQL statement fails, the entire transaction enters an "aborted" state
- All subsequent statements fail with `InFailedSqlTransaction`
- The transaction must be rolled back before continuing

SAVEPOINTs create **nested sub-transactions**:
```sql
SAVEPOINT my_savepoint;
-- Execute statement
-- If it fails, rollback to savepoint
ROLLBACK TO SAVEPOINT my_savepoint;
-- Continue with next statement
```

This allows each COMMENT statement to fail independently without aborting the main transaction.

### Migration Philosophy

WhisperEngine follows these migration principles:

1. **Resilient Migrations**: Migrations should handle schema variations gracefully
2. **Non-Destructive Comments**: COMMENT statements are optional metadata and shouldn't block deployments
3. **Forward Compatibility**: New migrations should work with older database schemas when possible
4. **Clear Warnings**: Users should see what was skipped and why

## Prevention for Future

### For Developers

When adding new columns that will have COMMENT statements added later:

1. Ensure the column-creating migration is properly sequenced
2. Use SAVEPOINTs in comment migrations for resilience
3. Document migration dependencies clearly
4. Test with both fresh databases AND databases at different migration points

### For CI/CD

1. Test migrations against multiple database states
2. Include rollback testing
3. Verify Docker images include all migrations before publishing

## Related Files

- **Migration**: `alembic/versions/20251015_1200_add_cdl_table_and_column_comments.py`
- **SQL Source**: `sql/add_cdl_table_comments.sql`
- **Emoji Columns Migration**: `alembic/versions/20251013_emoji_personality_columns.py`

## Status

✅ **FIXED** - The migration now uses SAVEPOINTs and handles missing columns gracefully.

Users should pull the latest code or wait for the next Docker image release.
