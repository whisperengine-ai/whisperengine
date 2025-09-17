# WhisperEngine Database Migrations & Backups

This directory contains the lightweight migration framework for evolving the WhisperEngine persistence layer (PostgreSQL-centric) plus guidance for multi-datastore backups.

## ✅ Components
- `migrations/*.sql` — Ordered SQL migration files (e.g. `0001_baseline.sql`)
- `schema_versions` table — Tracks applied migrations, checksums & timestamps
- `scripts/db/run_migrations.py` — Migration runner (no external framework)
- `scripts/db/backup_all.sh` — Unified backup script (Postgres, Redis, ChromaDB, Neo4j)

## 🧩 Philosophy
1. Immutable migrations: never edit a previously applied file; add a new one
2. Deterministic order: numeric prefix (zero-padded) defines execution order
3. Drift detection: checksum mismatch halts execution to prevent silent divergence
4. Explicit evolution: schema changes use `ALTER TABLE` in new migrations

## 🚀 Running Migrations
```bash
# Apply all pending
python scripts/db/run_migrations.py

# Show status without applying
python scripts/db/run_migrations.py --status

# Fake-apply a version (if manually synced)
python scripts/db/run_migrations.py --fake 0001
```

### Example Status Output
```
[migrate] Migration Status:
[migrate] 0001 | 0001_baseline.sql             | APPLIED
[migrate] 0002 | 0002_add_pattern_category.sql | PENDING
```

## ✍️ Creating a New Migration
1. Decide next version number (e.g. `0002`)
2. Create file: `migrations/0002_add_pattern_category.sql`
3. Put only the delta, e.g.:
```sql
BEGIN;
ALTER TABLE user_memory_importance_patterns
    ADD COLUMN pattern_category VARCHAR(100) DEFAULT 'general';
COMMIT;
```
4. Run migrations: `python scripts/db/run_migrations.py`

## 🔐 Backups
Use the provided unified backup script:
```bash
./scripts/db/backup_all.sh
```
Outputs to: `./backups/backup_<timestamp>/`

Contents may include:
- `postgres_<db>.dump` — Compressed pg_dump (custom format)
- `redis/dump.rdb` — Redis snapshot if accessible
- `chroma/` — File copy of Chroma persistent storage
- `neo4j/` — Neo4j database dump (if tooling installed)
- `BACKUP_METADATA.json` — Metadata descriptor

### Restore (PostgreSQL)
```bash
pg_restore -h localhost -U bot_user -d whisper_engine backups/backup_20250916_123000/postgres_whisper_engine.dump
```

### Suggested Backup Schedule
| Datastore  | Recommended | Method |
|------------|-------------|--------|
| PostgreSQL | Daily + pre-deploy | pg_dump custom format |
| Redis (ephemeral) | Optional (if persistence configured) | SAVE + copy dump.rdb |
| ChromaDB | Daily (if semantic memory critical) | rsync directory |
| Neo4j | Weekly or pre-deploy | neo4j-admin dump |

## 🔄 Optional: Automatic Migration on Startup
Add environment variable to your process manager:
```
RUN_DB_MIGRATIONS_ON_START=true
```
Then (optional) call the runner early in `run.py` or `main` init:
```python
import os, subprocess, sys
if os.getenv("RUN_DB_MIGRATIONS_ON_START") == "true":
    subprocess.run([
        sys.executable, "scripts/db/run_migrations.py"], check=True)
```
(We intentionally keep this manual to avoid unexpected schema changes in production.)

## 🧪 Verification Checklist After Schema Change
```bash
python scripts/db/run_migrations.py --status
psql -h localhost -U bot_user -d whisper_engine -c "\d+ user_memory_importance_patterns"
```

## 🛡️ Disaster Recovery Quick Path
1. Stop write traffic
2. Restore PostgreSQL from latest dump
3. Restore Chroma directory from backup
4. Restore Neo4j dump (if used)
5. Restart services
6. Run migrations
7. Validate application behavior

## 🧱 Future Enhancements (Optional)
- Add JSON migration manifest with dependencies
- Add dry-run mode (wrap in a transaction and roll back)
- Add seed data migrations (component='seed')
- Add per-component migration namespaces

## 🙋 FAQ
**Q: Can I edit an old migration?** No—add a new one.
**Q: What if checksum mismatch appears?** Someone changed a historical file; revert or recreate properly.
**Q: Can I include data corrections?** Yes—new migration with `UPDATE` statements.
**Q: Do I need Alembic?** Not unless you need autogeneration or complex branching.

---
Baseline ready. Add `0002_*.sql` to begin evolving.
