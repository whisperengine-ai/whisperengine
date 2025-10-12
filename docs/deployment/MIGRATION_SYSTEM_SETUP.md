# WhisperEngine v1.0.6+ Database Migration System

**Created**: October 11, 2025  
**Status**: ✅ Production Ready  
**Migration Tool**: Alembic 1.14.0

## 🎯 What Was Added

### Core Migration Infrastructure
- ✅ **Alembic Configuration** (`alembic.ini`) - Database migration settings
- ✅ **Migration Environment** (`alembic/env.py`) - PostgreSQL integration with environment variables
- ✅ **Baseline Migration** (`alembic/versions/20251011_baseline_v106.py`) - v1.0.6 schema snapshot
- ✅ **Migration Scripts** (`scripts/migrations/`) - Helper tools for managing migrations
- ✅ **Docker Integration** (`scripts/docker-entrypoint.sh`) - Auto-migration on container start

### Documentation
- ✅ **Comprehensive Guide** (`docs/guides/DATABASE_MIGRATIONS.md`) - Full migration workflow
- ✅ **Quick Start** (`docs/guides/MIGRATION_QUICKSTART.md`) - Fast reference
- ✅ **README** (`alembic/README.md`) - Directory documentation

### Dependencies
- ✅ **Added to requirements-core.txt**:
  - `alembic==1.14.0` - Migration framework
  - `sqlalchemy==2.0.36` - Required by Alembic

## 🚀 Installation

### For Existing v1.0.6 Deployments

Your database already has the schema. Just mark it as up-to-date:

```bash
# 1. Update dependencies
source .venv/bin/activate
pip install -r requirements-core.txt

# 2. Mark database as current (don't run migrations)
./scripts/migrations/db-migrate.sh stamp head

# 3. Verify setup
./scripts/migrations/db-migrate.sh status
```

### For Fresh Installations

```bash
# 1. Update dependencies
source .venv/bin/activate
pip install -r requirements-core.txt

# 2. Run baseline migration
./scripts/migrations/db-migrate.sh upgrade

# 3. Verify setup
./scripts/migrations/db-migrate.sh status
```

### Docker Deployments

Migrations run automatically on container start. Just rebuild:

```bash
# Rebuild containers with new dependencies
docker-compose build

# Start containers (migrations run automatically)
docker-compose up -d

# Check migration logs
docker logs whisperengine-assistant 2>&1 | grep -i migration
```

## 📝 Creating Migrations

### 1. Generate Migration File
```bash
./scripts/migrations/db-migrate.sh create "Add email verification to users"
```

### 2. Edit Migration File
File created in `alembic/versions/`:
```python
def upgrade() -> None:
    """Add email_verified column."""
    op.add_column('users', 
        sa.Column('email_verified', sa.Boolean(), 
                  nullable=False, server_default='false')
    )

def downgrade() -> None:
    """Remove email_verified column."""
    op.drop_column('users', 'email_verified')
```

### 3. Test Migration
```bash
# Apply migration
./scripts/migrations/db-migrate.sh upgrade +1

# Test rollback
./scripts/migrations/db-migrate.sh downgrade -1

# Apply for production
./scripts/migrations/db-migrate.sh upgrade
```

### 4. Commit Migration
```bash
git add alembic/versions/[generated_file].py
git commit -m "feat: Add email verification column

Migration: [revision_id]"
```

## 🔍 Common Commands

```bash
# Check current status
./scripts/migrations/db-migrate.sh status

# View migration history
./scripts/migrations/db-migrate.sh history

# Apply all pending migrations
./scripts/migrations/db-migrate.sh upgrade

# Apply next migration only
./scripts/migrations/db-migrate.sh upgrade +1

# Rollback last migration
./scripts/migrations/db-migrate.sh downgrade -1

# Show current revision
./scripts/migrations/db-migrate.sh current
```

## 🧪 Testing Your Setup

Run the validation script:

```bash
python scripts/migrations/test_migration_setup.py
```

Expected output:
```
✅ Alembic imports successful
✅ alembic.ini found and valid
✅ alembic/env.py found
✅ alembic/versions/ found with 1 migration(s)
✅ Migration management script found
✅ Database config: whisperengine at localhost:5433
✅ All checks passed! Migration system is ready.
```

## 📦 Files Added/Modified

### New Files
```
alembic/
├── README.md                          # Directory documentation
├── env.py                             # Alembic environment config
├── script.py.mako                     # Migration template
└── versions/
    ├── __init__.py
    └── 20251011_baseline_v106.py      # v1.0.6 baseline migration

alembic.ini                            # Alembic configuration

scripts/
├── docker-entrypoint.sh               # Auto-migration on startup
└── migrations/
    ├── db-migrate.sh                  # Shell wrapper script
    ├── migrate.py                     # Python migration manager
    └── test_migration_setup.py        # Validation script

docs/guides/
├── DATABASE_MIGRATIONS.md             # Comprehensive guide
└── MIGRATION_QUICKSTART.md            # Quick reference
```

### Modified Files
```
requirements-core.txt                  # Added alembic + sqlalchemy
Dockerfile                             # Added entrypoint for auto-migration
NEXT_STEPS.md                          # Added migration section
.gitignore                             # Added migration-specific ignores
```

## 🔒 Security Notes

- ✅ Database credentials use environment variables (never hardcoded)
- ✅ Migrations are versioned and auditable via Git
- ✅ Each migration includes rollback capability
- ✅ Auto-migration runs as non-root user in containers

## 🎓 Learning Resources

- **WhisperEngine Docs**: `docs/guides/DATABASE_MIGRATIONS.md`
- **Alembic Tutorial**: https://alembic.sqlalchemy.org/en/latest/tutorial.html
- **SQLAlchemy Docs**: https://docs.sqlalchemy.org/

## 🐛 Troubleshooting

### "Target database is not up to date"
```bash
./scripts/migrations/db-migrate.sh upgrade
```

### "Can't locate revision"
```bash
git pull origin main  # Get latest migration files
```

### "Connection refused"
```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Verify environment variables
echo $POSTGRES_HOST
echo $POSTGRES_PORT
```

## 🎉 Next Steps

You're ready to use database migrations! For your next schema change:

1. Create migration: `./scripts/migrations/db-migrate.sh create "Description"`
2. Edit the generated file in `alembic/versions/`
3. Test: `./scripts/migrations/db-migrate.sh upgrade`
4. Commit: `git add alembic/versions/[file].py && git commit`

**Full workflow**: See `docs/guides/DATABASE_MIGRATIONS.md`

---

**Questions?** Open an issue at https://github.com/whisperengine-ai/whisperengine/issues
