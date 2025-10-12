# Database Migration System Setup - Quick Reference

## 🎯 For v1.0.6 Deployments (Existing Databases)

If you're upgrading from v1.0.6, your database already has the schema. Tell Alembic to skip the baseline:

```bash
# 1. Install dependencies
source .venv/bin/activate
pip install -r requirements-core.txt

# 2. Mark database as up-to-date (don't run migrations)
./scripts/migrations/db-migrate.sh stamp head

# 3. Verify
./scripts/migrations/db-migrate.sh status
```

## 🆕 For Fresh Installations

```bash
# 1. Install dependencies
source .venv/bin/activate
pip install -r requirements-core.txt

# 2. Apply baseline migration
./scripts/migrations/db-migrate.sh upgrade

# 3. Verify
./scripts/migrations/db-migrate.sh status
```

## 📝 Creating Your First Migration

```bash
# 1. Create migration file
./scripts/migrations/db-migrate.sh create "Add user preferences table"

# 2. Edit the file in alembic/versions/
# Add your SQL changes to upgrade() and downgrade()

# 3. Test it
./scripts/migrations/db-migrate.sh upgrade +1

# 4. Test rollback
./scripts/migrations/db-migrate.sh downgrade -1

# 5. Apply for real
./scripts/migrations/db-migrate.sh upgrade
```

## 🐳 Docker Auto-Migration

Migrations run automatically when containers start. No manual steps needed!

```bash
# Just start your containers
docker-compose up -d

# Check migration logs
docker logs whisperengine-assistant 2>&1 | grep -i migration
```

## 📚 Full Documentation

See `docs/guides/DATABASE_MIGRATIONS.md` for complete guide.

## Common Commands

```bash
# Check status
./scripts/migrations/db-migrate.sh status

# View history
./scripts/migrations/db-migrate.sh history

# Apply all pending
./scripts/migrations/db-migrate.sh upgrade

# Rollback last
./scripts/migrations/db-migrate.sh downgrade -1
```

## Need Help?

- Full guide: `docs/guides/DATABASE_MIGRATIONS.md`
- Alembic docs: https://alembic.sqlalchemy.org/
- GitHub issues: https://github.com/whisperengine-ai/whisperengine/issues
