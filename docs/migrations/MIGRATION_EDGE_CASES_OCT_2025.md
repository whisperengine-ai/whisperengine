# Migration Edge Cases & Unusual Scenarios - October 2025

**Date:** October 19, 2025  
**Context:** Deep dive into edge cases and unusual upgrade scenarios  
**Previous Review:** docs/migrations/MIGRATION_PATH_REVIEW_OCT_2025.md

---

## Scenario 1: Stale 00_init.sql File

### Description
What if `00_init.sql` is from a NEWER version than the baseline, but the Docker image has OLDER migrations?

### Example
- User has v1.0.30 in production
- Generates `00_init.sql` dump from v1.0.30 database
- Downgrades Docker image to v1.0.28
- Fresh install uses NEW schema file with OLD migration code

### Current Behavior
```python
# scripts/run_migrations.py:177-180
else:
    print(f"ℹ️  Large database ({table_count} tables) but missing recent changes (no emoji columns)")
    print("ℹ️  This appears to be from an older 00_init.sql dump")
    print("🏷️  Stamping with baseline revision and will apply incremental updates...")
    stamp_revision = "20251011_baseline_v106"
```

**PROBLEM**: If 00_init.sql is NEWER than baseline:
1. Fresh install creates 80+ tables (more than baseline's 73)
2. Code stamps as baseline `20251011_baseline_v106`
3. Migrations try to create tables that ALREADY exist
4. ❌ **FAILS**: `CREATE TABLE` without `IF NOT EXISTS` will error

### Risk Assessment
**LIKELIHOOD**: Medium (dev environments, testing scenarios)  
**IMPACT**: High (breaks fresh installs)  
**CURRENT STATUS**: ⚠️ **VULNERABLE**

### Recommended Fix
Add version detection to 00_init.sql:
```sql
-- WhisperEngine Database Schema
-- Generated from: v1.0.28
-- Alembic Revision: 20251011_baseline_v106
-- Compatible with: v1.0.28+

COMMENT ON DATABASE whisperengine IS 'WhisperEngine v1.0.28 - Generated 2025-10-19';
```

Then check in migration script:
```python
# Check if 00_init.sql is newer than our migration code
init_sql_version = await conn.fetchval(
    "SELECT description FROM pg_database WHERE datname = current_database()"
)
if init_sql_version and "v1.0.3" in init_sql_version:  # Newer than v1.0.28
    print("⚠️  WARNING: Database schema is NEWER than migration code!")
    print("⚠️  Recommend upgrading Docker image to match database version")
    stamp_revision = "head"  # Skip all migrations
```

---

## Scenario 2: Interrupted Migration (Partial Application)

### Description
What if migration fails halfway through? Some tables created, others not.

### Example
- Migration creates 3 tables
- Table 1: ✅ Created
- Table 2: ✅ Created  
- Table 3: ❌ FAILS (disk full, syntax error, etc.)
- Container restarts → tries to apply same migration again

### Current Behavior
**Alembic migrations**: Use transactions, automatically roll back on failure ✅  
**Legacy SQL files** (`00_init.sql`, `01_seed_data.sql`): No explicit transaction handling ⚠️

### Code Review
```python
# scripts/run_migrations.py:59-72
async def apply_sql_file(conn, file_path, migration_name):
    """Apply a SQL migration file"""
    try:
        sql_content = file_path.read_text()
        
        # ... (search_path adjustment) ...
        
        await conn.execute(sql_content)  # ❌ NO TRANSACTION!
        return True
    except Exception as e:
        print(f"❌ Error applying migration {migration_name}: {e}")
        return False
```

**PROBLEM**: If `00_init.sql` fails partway, database is in INCONSISTENT state!

### Risk Assessment
**LIKELIHOOD**: Low (SQL files are well-tested)  
**IMPACT**: Critical (broken database, manual recovery needed)  
**CURRENT STATUS**: ⚠️ **VULNERABLE**

### Recommended Fix
Wrap SQL file execution in transaction:
```python
async def apply_sql_file(conn, file_path, migration_name):
    """Apply a SQL migration file in a transaction"""
    try:
        sql_content = file_path.read_text()
        
        # ... (search_path adjustment) ...
        
        # Execute in transaction
        async with conn.transaction():
            await conn.execute(sql_content)
            print(f"✅ Migration {migration_name} applied successfully!")
        return True
    except Exception as e:
        print(f"❌ Error applying migration {migration_name}: {e}")
        print("🔄 Transaction rolled back - database is unchanged")
        return False
```

---

## Scenario 3: Manual Schema Changes (User Customization)

### Description
What if user manually added columns, indexes, or modified tables?

### Example
```sql
-- User adds custom column to characters table
ALTER TABLE characters ADD COLUMN custom_metadata JSONB;

-- User adds custom index
CREATE INDEX idx_characters_custom ON characters(custom_metadata);
```

### Current Behavior
**Alembic migrations**: May fail if trying to create columns that exist  
**Personality backfill**: Should work (uses INSERT with conflict handling) ✅

### Risk Assessment
**LIKELIHOOD**: Medium (power users, custom deployments)  
**IMPACT**: Low (migrations fail gracefully, manual fix possible)  
**CURRENT STATUS**: ✅ **ACCEPTABLE**

### Why It's OK
- Alembic migrations fail with clear error messages
- User can manually resolve conflicts
- No data loss (transaction rollback)
- Can use `alembic stamp <revision>` to skip problematic migrations

### Recommendation
**Document in migration failure messages**:
```python
if upgrade_result.returncode != 0:
    print(f"❌ Migration upgrade failed: {upgrade_result.stderr}")
    print(f"STDOUT: {upgrade_result.stdout}")
    print("\n⚠️  TROUBLESHOOTING:")
    print("   1. Check if you have custom schema changes that conflict")
    print("   2. Review migration SQL in alembic/versions/")
    print("   3. Use 'alembic stamp <revision>' to skip problematic migrations")
    print("   4. See: docs/migrations/TROUBLESHOOTING.md")
```

---

## Scenario 4: Corrupted Alembic State

### Description
What if `alembic_version` table exists but contains INVALID revision?

### Example
```sql
-- Current state
SELECT * FROM alembic_version;
-- version_num
-- invalid_revision_12345  ❌ Doesn't exist in migration files!
```

### Current Behavior
```python
# Alembic will ERROR when trying to find revision
# No graceful handling in run_migrations.py
```

### Risk Assessment
**LIKELIHOOD**: Low (requires database corruption or manual tampering)  
**IMPACT**: High (blocks all migrations, container fails to start)  
**CURRENT STATUS**: ⚠️ **VULNERABLE**

### Recommended Fix
Add validation before running migrations:
```python
# After detecting alembic_version exists
current_revision = await conn.fetchval("SELECT version_num FROM alembic_version LIMIT 1")

if current_revision:
    # Validate revision exists in our migration files
    validate_result = subprocess.run([
        'alembic', 'show', current_revision
    ], cwd='/app', env=env, capture_output=True, text=True)
    
    if validate_result.returncode != 0:
        print(f"⚠️  WARNING: Current revision '{current_revision}' is INVALID!")
        print("⚠️  Options:")
        print("   1. Reset to baseline: alembic stamp 20251011_baseline_v106")
        print("   2. Force stamp to head: alembic stamp head")
        print("   3. Manual recovery required")
        return 1  # Fail loudly
```

---

## Scenario 5: Non-Standard Assistant Character ID

### Description
What if assistant character has different ID than expected?

### Example
```sql
-- Normal: assistant has id=29
-- Edge case: User deleted rows, assistant now has id=450
```

### Current Behavior
Migration `c64001afbd46` uses:
```sql
INSERT INTO personality_traits (character_id, trait_name, trait_value, ...)
SELECT 
    id,  -- ✅ DYNAMIC! Uses actual character ID
    'openness', 0.80, ...
FROM characters 
WHERE normalized_name = 'assistant'  -- ✅ Query by name, not hardcoded ID
```

### Risk Assessment
**LIKELIHOOD**: Medium (depends on user data manipulation)  
**IMPACT**: None  
**CURRENT STATUS**: ✅ **HANDLED CORRECTLY**

### Why It Works
- Migration queries by `normalized_name`, not hardcoded ID
- Uses `NOT EXISTS` checks to avoid duplicates
- Completely flexible to any character ID

---

## Scenario 6: Table Schema Mismatch

### Description
What if `personality_traits` table exists but has WRONG schema?

### Example
```sql
-- Expected schema (row-based Big Five)
CREATE TABLE personality_traits (
    character_id INTEGER,
    trait_name VARCHAR(50),
    trait_value DECIMAL(3,2),
    ...
);

-- User has OLD schema (column-based Big Five)
CREATE TABLE personality_traits (
    character_id INTEGER PRIMARY KEY,
    openness DECIMAL(3,2),
    conscientiousness DECIMAL(3,2),
    ...
);
```

### Current Behavior
Migration `9c23e4e81011`:
```sql
CREATE TABLE IF NOT EXISTS personality_traits (...);
-- ✅ Skips if table exists (even with wrong schema!)
```

Migration `c64001afbd46`:
```sql
INSERT INTO personality_traits (character_id, trait_name, trait_value, ...)
-- ❌ FAILS if column names don't match!
```

### Risk Assessment
**LIKELIHOOD**: Very Low (would require manual schema creation)  
**IMPACT**: High (personality backfill fails)  
**CURRENT STATUS**: ⚠️ **POTENTIAL ISSUE**

### Recommended Fix
Add schema validation before personality backfill:
```sql
-- Check if personality_traits has correct schema
DO $$
DECLARE
    has_trait_name BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'personality_traits' 
        AND column_name = 'trait_name'
    ) INTO has_trait_name;
    
    IF NOT has_trait_name THEN
        RAISE NOTICE 'personality_traits table has incorrect schema - skipping backfill';
        RAISE NOTICE 'Please check table structure: trait_name column is missing';
        RETURN;  -- Exit without attempting INSERT
    END IF;
    
    -- Proceed with backfill...
END $$;
```

---

## Scenario 7: Mid-Migration Failure & Recovery

### Description
What if migration fails AFTER Alembic has recorded it as applied?

### Example
```python
# Alembic records migration as applied
# Then Python code crashes BEFORE data insertion
# Restart → Alembic thinks migration is done, skips it
```

### Current Behavior
**Alembic transactions**: ✅ Atomic - either all succeeds or all rolls back  
**Schema changes**: ✅ Rolled back on failure  
**Alembic version table**: ✅ Not updated if transaction fails

### Risk Assessment
**LIKELIHOOD**: Very Low (Alembic handles this correctly)  
**IMPACT**: None  
**CURRENT STATUS**: ✅ **HANDLED BY ALEMBIC**

### Why It Works
All Alembic operations happen in a SINGLE transaction:
1. Schema changes (CREATE TABLE, etc.)
2. Data changes (INSERT, UPDATE, etc.)
3. Update `alembic_version` table

If ANY step fails, ENTIRE transaction rolls back.

---

## Scenario 8: Downgrade Path (Rollback)

### Description
What if user needs to downgrade from v1.0.28 back to v1.0.6?

### Example
```bash
# User upgrades to v1.0.28
docker pull whisperengine-bot:v1.0.28
docker compose up -d

# Something breaks, wants to rollback
docker pull whisperengine-bot:v1.0.6
docker compose up -d
```

### Current Behavior
**v1.0.6 code**: Has NO knowledge of personality_traits tables  
**Database**: Has personality_traits tables (created by v1.0.28 migrations)  
**Result**: ⚠️ **Code ignores new tables, bot works but uses old logic**

### Risk Assessment
**LIKELIHOOD**: Medium (users may need to rollback)  
**IMPACT**: Medium (degraded functionality, confusion)  
**CURRENT STATUS**: ⚠️ **PARTIALLY SUPPORTED**

### Why It's Partially OK
- Extra tables don't BREAK v1.0.6 code
- v1.0.6 simply ignores personality_traits
- Bot functions, just without personality features
- No data loss

### Limitation
**Cannot remove tables** - Alembic downgrade migrations not implemented!

### Current State
```python
# alembic/versions/c64001afbd46_backfill_assistant_personality_data.py
def downgrade() -> None:
    """
    Remove assistant personality data.
    
    NOTE: This does NOT drop the personality_traits table itself,
    only removes the assistant character's data.
    """
    # Implementation exists but rarely tested
```

### Recommended Enhancement
Document downgrade limitations:
```markdown
# DOWNGRADE WARNINGS

## v1.0.28 → v1.0.6
- ⚠️ personality_traits tables will REMAIN in database
- ⚠️ v1.0.6 code will IGNORE these tables (safe but wasteful)
- ⚠️ To fully remove, manually run: DROP TABLE personality_traits CASCADE;

## Supported Rollback Path
1. Downgrade Docker image to v1.0.6
2. Container starts normally (ignores new tables)
3. Bot functions with v1.0.6 behavior
4. Optional: Manually clean up tables if desired
```

---

## Scenario 9: Multiple Assistants (User Creates Duplicate)

### Description
What if user creates ANOTHER character with `normalized_name = 'assistant'`?

### Example
```sql
-- Original assistant (id=29)
INSERT INTO characters (normalized_name, ...) VALUES ('assistant', ...);

-- User tries to create another (id=500)
INSERT INTO characters (normalized_name, ...) VALUES ('assistant', ...);
-- ❌ FAILS: UNIQUE constraint on normalized_name
```

### Risk Assessment
**LIKELIHOOD**: Very Low (database enforces uniqueness)  
**IMPACT**: None  
**CURRENT STATUS**: ✅ **PREVENTED BY DATABASE CONSTRAINTS**

### Why It Can't Happen
```sql
-- From 00_init.sql
CREATE TABLE characters (
    id SERIAL PRIMARY KEY,
    normalized_name VARCHAR(100) UNIQUE NOT NULL,  -- ✅ UNIQUE constraint
    ...
);
```

---

## Scenario 10: Emoji Column Detection False Positive

### Description
What if database has `emoji_*` columns but they're NOT from our migrations?

### Example
User manually added:
```sql
ALTER TABLE characters ADD COLUMN emoji_custom TEXT;
```

Detection code:
```python
emoji_columns_exist = await conn.fetchval("""
    SELECT COUNT(*) 
    FROM information_schema.columns 
    WHERE table_name = 'characters' 
    AND column_name LIKE 'emoji%'  -- ✅ Matches emoji_custom!
""")
```

### Current Behavior
**Detection**: Thinks database has recent migrations  
**Stamps as**: `head` (skips all migrations)  
**Result**: ❌ May skip needed migrations!

### Risk Assessment
**LIKELIHOOD**: Very Low (requires specific manual tampering)  
**IMPACT**: Medium (migrations skipped incorrectly)  
**CURRENT STATUS**: ⚠️ **MINOR ISSUE**

### Recommended Fix
Check for SPECIFIC emoji columns, not pattern:
```python
emoji_columns_exist = await conn.fetchval("""
    SELECT COUNT(*) 
    FROM information_schema.columns 
    WHERE table_name = 'characters' 
    AND column_name IN (
        'emoji_frequency', 
        'emoji_style', 
        'emoji_combination',
        'emoji_placement',
        'emoji_age_demographic',
        'emoji_cultural_influence'
    )
""")
# Should return 6 if ALL emoji columns exist, 0 if none
if emoji_columns_exist >= 5:  # At least 5 of 6 columns present
    stamp_revision = "head"
```

---

## Summary Matrix

| Scenario | Likelihood | Impact | Status | Priority |
|----------|-----------|--------|--------|----------|
| Stale 00_init.sql | Medium | High | ⚠️ Vulnerable | P1 |
| Interrupted Migration | Low | Critical | ⚠️ Vulnerable | P0 |
| Manual Schema Changes | Medium | Low | ✅ Acceptable | P3 |
| Corrupted Alembic State | Low | High | ⚠️ Vulnerable | P2 |
| Non-Standard Assistant ID | Medium | None | ✅ Handled | - |
| Table Schema Mismatch | Very Low | High | ⚠️ Potential | P2 |
| Mid-Migration Failure | Very Low | None | ✅ Handled | - |
| Downgrade Path | Medium | Medium | ⚠️ Partial | P3 |
| Multiple Assistants | Very Low | None | ✅ Prevented | - |
| Emoji Detection False Positive | Very Low | Medium | ⚠️ Minor | P4 |

---

## Recommendations by Priority

### P0 - Critical (Fix Before v1.0.29 Release)
1. **Add transaction wrapper to SQL file execution**
   - Prevents partial migration application
   - Ensures atomic operations
   - File: `scripts/run_migrations.py:apply_sql_file()`

### P1 - High (Fix in v1.0.29)
2. **Add 00_init.sql version detection**
   - Prevent using newer schema with older migration code
   - Add version comment to 00_init.sql
   - Add version check in migration script

### P2 - Medium (Fix in v1.0.30)
3. **Add Alembic state validation**
   - Check revision validity before running migrations
   - Provide recovery instructions for corrupted state

4. **Add schema validation before personality backfill**
   - Check column existence before INSERT
   - Graceful skip if schema mismatched

### P3 - Nice to Have
5. **Improve downgrade documentation**
   - Document rollback limitations
   - Add manual cleanup scripts

6. **Enhanced error messages**
   - Add troubleshooting guides to error output
   - Link to documentation

### P4 - Low Priority
7. **Improve emoji column detection**
   - Check for specific columns, not pattern
   - More robust version detection

---

## Testing Recommendations

### Automated Tests to Add
```python
# tests/migrations/test_edge_cases.py

async def test_interrupted_migration():
    """Test that failed migration doesn't leave partial state"""
    # Create database
    # Start migration
    # Kill process mid-migration
    # Restart → should rollback or complete atomically

async def test_stale_init_sql():
    """Test newer 00_init.sql with older migration code"""
    # Use v1.0.30 schema dump
    # Run v1.0.28 migration code
    # Should detect version mismatch

async def test_corrupted_alembic_state():
    """Test invalid revision in alembic_version"""
    # Set alembic_version to 'invalid_12345'
    # Run migration script
    # Should detect and fail gracefully
```

---

## Conclusion

**Good News**: Most edge cases are handled correctly!  
**Critical Issue Found**: SQL file execution lacks transaction protection  
**Recommended Action**: Add transaction wrapper (P0) before v1.0.29 release

The migration system is ROBUST but needs transaction safety for SQL files.
