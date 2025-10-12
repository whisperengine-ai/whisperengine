# WhisperEngine Database Migrations

This directory contains Alembic database migrations for WhisperEngine.

## Quick Start

### Check Status
```bash
./scripts/migrations/db-migrate.sh status
```

### Apply Migrations
```bash
./scripts/migrations/db-migrate.sh upgrade
```

### Create New Migration
```bash
./scripts/migrations/db-migrate.sh create "Add your feature description"
```

## For v1.0.6 Users

If upgrading from v1.0.6, your database already has the baseline schema:

```bash
# Mark database as up-to-date without running migrations
./scripts/migrations/db-migrate.sh stamp head
```

## Docker Integration

Migrations run automatically when containers start. No manual steps needed!

## Documentation

- **Quick Start**: `docs/guides/MIGRATION_QUICKSTART.md`
- **Full Guide**: `docs/guides/DATABASE_MIGRATIONS.md`
- **Alembic Docs**: https://alembic.sqlalchemy.org/

## Directory Structure

```
alembic/
├── versions/           # Migration files (committed to git)
│   ├── __init__.py
│   └── 20251011_baseline_v106.py  # v1.0.6 baseline
├── env.py             # Alembic environment config
└── script.py.mako     # Migration template
```

## Migration Files

Each migration file includes:
- **Revision ID**: Unique identifier
- **upgrade()**: Forward migration (apply changes)
- **downgrade()**: Rollback migration (undo changes)

## Best Practices

✅ **DO**:
- Test migrations locally before committing
- Write reversible migrations (proper downgrade())
- Keep migrations small and focused
- Document complex migrations
- Commit migration files to git

❌ **DON'T**:
- Edit existing migrations after deployment
- Delete migration files that have been applied
- Skip migrations by manually editing the database
- Forget to write downgrade() functions
