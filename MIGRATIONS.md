# WhisperEngine Database Migrations 🔄

> **Post-v1.0.6 Feature**: Professional database migration system using Alembic

## Overview

WhisperEngine now uses **Alembic** for safe, versioned database schema changes. All post-v1.0.6 releases will use migrations for schema updates.

## Quick Start

### For v1.0.6 Deployments (Existing Databases)

Your database already has the schema. Just mark it as current:

```bash
# 1. Install dependencies
pip install -r requirements-core.txt

# 2. Mark database as up-to-date
./scripts/migrations/db-migrate.sh stamp head

# 3. Verify
./scripts/migrations/db-migrate.sh status
```

### For New Installations

```bash
# 1. Install dependencies
pip install -r requirements-core.txt

# 2. Run migrations
./scripts/migrations/db-migrate.sh upgrade

# 3. Verify
./scripts/migrations/db-migrate.sh status
```

## Creating Migrations

```bash
# 1. Generate migration file
./scripts/migrations/db-migrate.sh create "Add your feature description"

# 2. Edit the generated file in alembic/versions/
# 3. Test migration
./scripts/migrations/db-migrate.sh upgrade

# 4. Commit to git
git add alembic/versions/[generated_file].py
git commit -m "feat: Your migration description"
```

## Docker Integration

Migrations run **automatically** when containers start. No manual steps needed!

```bash
docker-compose up -d  # Migrations run before app starts
```

## Documentation

- **Quick Start**: [`docs/guides/MIGRATION_QUICKSTART.md`](docs/guides/MIGRATION_QUICKSTART.md)
- **Complete Guide**: [`docs/guides/DATABASE_MIGRATIONS.md`](docs/guides/DATABASE_MIGRATIONS.md)
- **Setup Instructions**: [`docs/deployment/MIGRATION_SYSTEM_SETUP.md`](docs/deployment/MIGRATION_SYSTEM_SETUP.md)

## Common Commands

```bash
# Check status
./scripts/migrations/db-migrate.sh status

# View history
./scripts/migrations/db-migrate.sh history

# Apply migrations
./scripts/migrations/db-migrate.sh upgrade

# Rollback last migration
./scripts/migrations/db-migrate.sh downgrade -1
```

## Need Help?

- 📚 [Complete Migration Guide](docs/guides/DATABASE_MIGRATIONS.md)
- 🐛 [GitHub Issues](https://github.com/whisperengine-ai/whisperengine/issues)
- 📖 [Alembic Documentation](https://alembic.sqlalchemy.org/)

---

**Migration System**: ✅ Ready  
**Version**: Post-v1.0.6  
**Tool**: Alembic 1.14.0
