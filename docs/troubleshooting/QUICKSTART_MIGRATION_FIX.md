# Quickstart Migration Fix: Missing Emoji Columns

## Problem Summary

The quickstart Docker deployment fails with:
```
ERROR: column "emoji_frequency" of relation "characters" does not exist
```

## Root Cause Analysis

WhisperEngine has **three deployment scenarios** with different migration strategies:

### 1. Legacy v1.0.6 Users (Pre-Alembic)
- **Status**: Databases exist with full schema from manual SQL
- **Solution**: Run `docker exec whisperengine-assistant alembic stamp head` to mark as current
- **Documentation**: See `docs/database/MIGRATIONS.md`

### 2. New Quickstart Users (Current Issue) ⚠️
- **Process**: 
  1. Fresh database created
  2. `00_init.sql` applied (SQL dump from before emoji columns were added)
  3. Script **does NOT** create `alembic_version` table or stamp revision
  4. Next container restart detects tables exist but NO `alembic_version` table
  5. Script assumes Alembic-managed database and runs `alembic upgrade head`
  6. Comments migration tries to add comments to emoji columns that don't exist → **FAILS**

### 3. Developers Using Alembic from Start
- **Process**: Full migration chain runs from baseline → emoji columns → comments
- **Status**: ✅ Works correctly

## Why This Happened

The `00_init.sql` file is a PostgreSQL dump that was generated **before** the emoji personality columns were added (Oct 13, 2025). When new quickstart users deploy:

1. ✅ Database created with `00_init.sql` (old schema, no emoji columns)
2. ❌ No `alembic_version` table created
3. ❌ Next run detects tables exist, assumes Alembic-managed
4. ❌ Tries to run ALL Alembic migrations from start
5. ❌ Comments migration fails on missing emoji columns

## Solutions

### Solution 1: Update `run_migrations.py` to Stamp After Init (Recommended)

After applying `00_init.sql`, the script should create `alembic_version` and stamp with the revision that matches the dump:

```python
# After applying 00_init.sql successfully
if await apply_sql_file(conn, init_schema_path, migration_name):
    await record_migration(conn, migration_name)
    print("✅ Comprehensive schema applied - 73 tables + AI Assistant character ready!")
    
    # NEW: Stamp with Alembic revision matching the dump
    print("🏷️  Stamping database with Alembic revision...")
    database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    env = os.environ.copy()
    env['DATABASE_URL'] = database_url
    
    # Determine which revision the dump corresponds to
    # For 00_init.sql generated on Oct 12, 2025: revision before emoji columns
    INIT_SQL_REVISION = "phase1_2_cleanup"  # Last revision before emoji columns
    
    result = subprocess.run([
        'alembic', 'stamp', INIT_SQL_REVISION
    ], cwd='/app', env=env, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✅ Database stamped with Alembic revision: {INIT_SQL_REVISION}")
        print("ℹ️  Future Alembic migrations will now run incrementally")
    else:
        print(f"⚠️  Failed to stamp Alembic revision: {result.stderr}")
```

### Solution 2: Regenerate `00_init.sql` with Latest Schema (Temporary Fix)

Regenerate the SQL dump to include emoji columns:

```bash
# From a database with all migrations applied
docker exec whisperengine-containerized-postgres pg_dump \
  -U whisperengine \
  -d whisperengine \
  --schema-only \
  --no-owner \
  --no-acl \
  > sql/00_init.sql.new

# Add comment at top noting the Alembic revision this corresponds to
# Replace old file
mv sql/00_init.sql.new sql/00_init.sql
```

### Solution 3: Make Comments Migration More Resilient (Already Done)

The comments migration now uses SAVEPOINTs to gracefully skip missing columns. This is a **defense-in-depth** approach that prevents the error from blocking deployments.

## Recommended Action Plan

### Immediate (For Next Docker Release)

1. ✅ **Already Fixed**: Comments migration uses SAVEPOINTs (gracefully skips missing columns)
2. **Update `run_migrations.py`**: Add Alembic stamping after `00_init.sql` (Solution 1)
3. **Document**: Update quickstart docs to explain the migration strategy

### Medium Term

1. **Regenerate `00_init.sql`**: Include all current schema changes including emoji columns
2. **Add version tracking**: Document which Alembic revision each `00_init.sql` corresponds to
3. **Automated testing**: Test migration path for all three scenarios (legacy, quickstart, developer)

### Long Term

1. **Unified migration strategy**: Consider moving entirely to Alembic for all deployments
2. **Migration testing CI**: Automated tests for migration paths
3. **Database schema versioning**: Track schema version in a dedicated table

## For Users Right Now

### If You're Getting This Error

**Option 1: Pull Latest Code (Has SAVEPOINT Fix)**
```bash
docker compose -f docker-compose.containerized.yml down
docker compose -f docker-compose.containerized.yml pull
docker compose -f docker-compose.containerized.yml up -d
```

The comments migration will now skip missing emoji columns with warnings instead of failing.

**Option 2: Manually Apply Emoji Columns**
```bash
# Connect to database
docker compose -f docker-compose.containerized.yml exec postgres psql -U whisperengine -d whisperengine

# Add missing columns
ALTER TABLE characters ADD COLUMN IF NOT EXISTS emoji_frequency VARCHAR(50) NOT NULL DEFAULT 'moderate';
ALTER TABLE characters ADD COLUMN IF NOT EXISTS emoji_style VARCHAR(100) NOT NULL DEFAULT 'general';
ALTER TABLE characters ADD COLUMN IF NOT EXISTS emoji_combination VARCHAR(50) NOT NULL DEFAULT 'text_with_accent_emoji';
ALTER TABLE characters ADD COLUMN IF NOT EXISTS emoji_placement VARCHAR(50) NOT NULL DEFAULT 'end_of_message';
ALTER TABLE characters ADD COLUMN IF NOT EXISTS emoji_age_demographic VARCHAR(50) NOT NULL DEFAULT 'millennial';
ALTER TABLE characters ADD COLUMN IF NOT EXISTS emoji_cultural_influence VARCHAR(100) NOT NULL DEFAULT 'general';

# Then mark as Alembic-managed
\q

# Stamp with current revision
docker compose -f docker-compose.containerized.yml run --rm whisperengine-assistant alembic stamp head
```

## Related Files

- **Migration Script**: `scripts/run_migrations.py`
- **Init SQL**: `sql/00_init.sql`
- **Emoji Migration**: `alembic/versions/20251013_emoji_personality_columns.py`
- **Comments Migration**: `alembic/versions/20251015_1200_add_cdl_table_and_column_comments.py`
- **User Docs**: `docs/database/MIGRATIONS.md`

## Status

- ✅ **SAVEPOINT Fix**: Comments migration now resilient to missing columns
- 🔄 **Pending**: Update `run_migrations.py` to stamp after `00_init.sql`
- 🔄 **Pending**: Regenerate `00_init.sql` with latest schema
