# WhisperEngine Database Migrations 🔄

> **Post-v1.0.6 Feature**: Professional database migration system using Alembic

## Overview

WhisperEngine now uses **Alembic** for safe, versioned database schema changes. All post-v1.0.6 releases will use migrations for schema updates.

## Quick Start

### For End Users (Quickstart Deployments)

**Upgrading from v1.0.6:**
```bash
# Step 1: Update to latest containers (this will include Alembic)
docker-compose down
docker-compose pull
docker-compose up -d

# Step 2: Mark existing database as current (prevents migration errors)
docker exec whisperengine-assistant alembic stamp head

# Step 3: Verify status
docker exec whisperengine-assistant alembic current
```

**New Installations:**
Migrations run automatically when containers start - no action needed!

### For Developers (Git Repository)

**Upgrading from v1.0.6:**
```bash
# 1. Install dependencies
pip install -r requirements-core.txt

# 2. Mark database as up-to-date
./scripts/migrations/db-migrate.sh stamp head

# 3. Verify
./scripts/migrations/db-migrate.sh status
```

**New Installations:**
```bash
# 1. Install dependencies
pip install -r requirements-core.txt

# 2. Run migrations
./scripts/migrations/db-migrate.sh upgrade

# 3. Verify
./scripts/migrations/db-migrate.sh status
```

## Creating Migrations (Developers Only)

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

Migrations run **automatically** when containers start. No manual steps needed for end users!

**End Users (Quickstart):**
```bash
docker-compose up -d  # Migrations run automatically
```

**Developers:**
```bash
# Development environment
./bot.sh start dev  # Migrations run automatically

# Or manual migration commands
./scripts/migrations/db-migrate.sh upgrade
```

## Common Commands

**End Users:**
```bash
# Check migration status
docker exec whisperengine-assistant alembic current

# For v1.0.6 upgrades only (after updating containers)
docker exec whisperengine-assistant alembic stamp head
```

**Developers:**

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
