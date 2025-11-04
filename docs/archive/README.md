# WhisperEngine Archive - Legacy and Deprecated Code

This directory contains deprecated and legacy code that has been removed from the active codebase but is preserved for historical reference and documentation purposes.

## Directory Contents

### `deprecated-schema/`
**Purpose:** Legacy database schema files

**Contents:**
- `init_schema.sql` - Initial baseline schema (444 LOC, Oct 20, 2025)
  - Marked as deprecated in October 2025
  - Was used for development and Docker initialization
  - **Replaced by:** Alembic migrations + `sql/00_init.sql`
  - **Status:** No longer used in production multi-bot deployment

**Why archived:**
- Modern WhisperEngine uses Alembic migrations as the schema source of truth
- Current deployment uses `run_migrations.py` with proper version management
- Alembic provides migration tracking, rollback support, and version history
- This file was only used as fallback in legacy code paths

**Reference:** See `docs/schema/UNIFIED_MIGRATION_GUIDE.md` for current schema deployment

---

### `legacy-import-scripts/`
**Purpose:** Historical character import scripts from JSON to database

**Contents:**
- `batch_import_characters.py` - Batch import from JSON files
- `comprehensive_cdl_import.py` - CDL-aware comprehensive import
- `comprehensive_character_import.py` - Complete character data migration
- `import_characters_to_clean_schema.py` - Schema-specific import
- `import_elena_to_db.py` - Single character import (Elena)
- `import_sophia_to_db.py` - Single character import (Sophia)

**Purpose:**
These scripts were used during the migration from JSON-based character files to the PostgreSQL-based CDL database system (October 2025 milestone).

**Why archived:**
- All character data has been migrated to PostgreSQL
- JSON character files are no longer used (`characters/examples_legacy_backup/` is backup only)
- Modern character management uses the CDL Web UI or direct database operations
- No ongoing need for JSON → DB import functionality

**If needed:**
- Refer to these scripts for understanding the migration process
- Most logic is captured in `batch_import_characters.py` if needed for reference
- For new character imports: Use CDL Web UI or direct database inserts

---

## Why This Archive Exists

### Code Cleanliness Philosophy
- **Active code only in main tree** - Reduces cognitive load for developers
- **Historical preservation** - Keep git history for reference via `git log`
- **Clear deprecation path** - Archive clearly marks code as obsolete
- **Easy recovery** - Archived code is still in git history, never truly lost

### What's NOT Archived
- Production code that's still being used
- Code with active callers in the codebase
- Features with ongoing development
- Configuration or deployment files still in use

### What IS Archived
- DEPRECATED code marked for removal
- Code replaced by newer implementations  
- Historical import/migration scripts
- Legacy fallback implementations
- Schema files superseded by newer systems

---

## How to Reference This Archive

### To understand the schema evolution:
```bash
git log --oneline --follow -- docs/archive/deprecated-schema/init_schema.sql
git show 4f15e64:sql/init_schema.sql  # See when it was marked deprecated
```

### To review import process history:
```bash
git log --oneline --all -- legacy_scripts/deprecated_imports/
git show HEAD:legacy_scripts/deprecated_imports/batch_import_characters.py
```

### To restore any file:
```bash
git show <commit>:legacy_scripts/deprecated_imports/batch_import_characters.py > /tmp/restore.py
```

---

## Related Documentation

- **Schema Evolution:** See `docs/schema/UNIFIED_MIGRATION_GUIDE.md`
- **CDL System:** See `.github/copilot-instructions.md` section on CDL
- **Dead Code Cleanup:** See `DEAD_CODE_DELETION_PHASES_1_2_COMPLETE.md`
- **Architecture:** See `docs/architecture/README.md`

---

## Migration Timeline

- **October 2025:** Character data migration from JSON to PostgreSQL completed
- **October 2025:** Alembic migrations established as schema source of truth  
- **October 20, 2025:** `init_schema.sql` marked as deprecated
- **November 4, 2025:** Deprecated files archived to `docs/archive/`

---

**Status:** ✅ Archive complete  
**Date:** November 4, 2025  
**Archival Reason:** Code cleanup and deprecation management  
**Recovery:** All files remain in git history via `git log` and `git show`
