# WhisperEngine Database Migration Guide

**Status**: ✅ Active (v1.0.6+)  
**Migration System**: Alembic  
**Created**: October 11, 2025

## Overview

WhisperEngine uses **Alembic** for database schema migrations. This ensures safe, versioned schema changes that can be applied and rolled back as needed.

## Quick Start

### Check Current Status
```bash
# Show current migration status
./scripts/migrations/db-migrate.sh status

# Show migration history
./scripts/migrations/db-migrate.sh history
```

### Create New Migration
```bash
# Create a new migration file
./scripts/migrations/db-migrate.sh create "Add user preferences column"

# Edit the generated file in alembic/versions/
# Add your SQL changes to upgrade() and downgrade() functions
```

### Apply Migrations
```bash
# Apply all pending migrations
./scripts/migrations/db-migrate.sh upgrade

# Apply only the next migration
./scripts/migrations/db-migrate.sh upgrade +1

# Apply up to a specific revision
./scripts/migrations/db-migrate.sh upgrade abc123
```

### Rollback Migrations
```bash
# Rollback the last migration
./scripts/migrations/db-migrate.sh downgrade -1

# Rollback to a specific revision
./scripts/migrations/db-migrate.sh downgrade abc123

# Rollback all migrations (DANGER!)
./scripts/migrations/db-migrate.sh downgrade base
```

## Migration Workflow

### 1. Planning a Schema Change

Before creating a migration, consider:
- **Backwards compatibility**: Can old code work with new schema?
- **Data migration**: Do you need to migrate existing data?
- **Rollback strategy**: How do you undo this change?
- **Performance impact**: Will this lock tables or affect production?

### 2. Creating a Migration

```bash
# Create migration file
./scripts/migrations/db-migrate.sh create "Add email_verified column to users"

# This creates: alembic/versions/20251011_1430_abc123_add_email_verified_column_to_users.py
```

### 3. Writing Migration Code

Edit the generated file:

```python
"""Add email_verified column to users

Revision ID: abc123
Revises: def456
Create Date: 2025-10-11 14:30:00
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'abc123'
down_revision: Union[str, None] = 'def456'


def upgrade() -> None:
    """Apply migration changes."""
    # Add new column with default value
    op.add_column('users', 
        sa.Column('email_verified', sa.Boolean(), 
                  nullable=False, server_default='false')
    )
    
    # Create index for faster lookups
    op.create_index('idx_users_email_verified', 
                    'users', ['email_verified'])


def downgrade() -> None:
    """Revert migration changes."""
    # Drop index first
    op.drop_index('idx_users_email_verified', 'users')
    
    # Drop column
    op.drop_column('users', 'email_verified')
```

### 4. Testing the Migration

```bash
# 1. Test upgrade
./scripts/migrations/db-migrate.sh upgrade +1

# 2. Verify schema changes
psql -h localhost -p 5433 -U whisperengine -d whisperengine -c "\d users"

# 3. Test rollback
./scripts/migrations/db-migrate.sh downgrade -1

# 4. Verify rollback worked
psql -h localhost -p 5433 -U whisperengine -d whisperengine -c "\d users"

# 5. Re-apply for production
./scripts/migrations/db-migrate.sh upgrade
```

### 5. Committing the Migration

```bash
# Add migration file to git
git add alembic/versions/20251011_1430_abc123_add_email_verified_column_to_users.py

# Commit with descriptive message
git commit -m "feat: Add email_verified column to users table

- Adds email_verified boolean column with default false
- Adds index for performance
- Includes rollback in downgrade()

Migration: abc123
Related: #123"
```

## Common Migration Patterns

### Adding a Column
```python
def upgrade() -> None:
    op.add_column('table_name',
        sa.Column('column_name', sa.String(length=255), nullable=True)
    )

def downgrade() -> None:
    op.drop_column('table_name', 'column_name')
```

### Creating a Table
```python
def upgrade() -> None:
    op.create_table('new_table',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'))
    )

def downgrade() -> None:
    op.drop_table('new_table')
```

### Adding an Index
```python
def upgrade() -> None:
    op.create_index('idx_users_email', 'users', ['email'], unique=True)

def downgrade() -> None:
    op.drop_index('idx_users_email', 'users')
```

### Renaming a Column
```python
def upgrade() -> None:
    op.alter_column('users', 'old_name', new_column_name='new_name')

def downgrade() -> None:
    op.alter_column('users', 'new_name', new_column_name='old_name')
```

### Data Migration
```python
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column

def upgrade() -> None:
    # Define table structure for data operations
    users_table = table('users',
        column('id', sa.Integer),
        column('old_status', sa.String),
        column('new_status', sa.String)
    )
    
    # Migrate data
    op.execute(
        users_table.update()
        .where(users_table.c.old_status == 'active')
        .values(new_status='verified')
    )

def downgrade() -> None:
    # Reverse data migration
    users_table = table('users',
        column('id', sa.Integer),
        column('old_status', sa.String),
        column('new_status', sa.String)
    )
    
    op.execute(
        users_table.update()
        .where(users_table.c.new_status == 'verified')
        .values(old_status='active')
    )
```

## Docker Integration

### Automatic Migration on Startup

WhisperEngine containers automatically run migrations on startup:

```bash
# Start containers (migrations run automatically)
docker-compose up -d

# Check migration logs
docker logs whisperengine-assistant 2>&1 | grep -i migration
```

### Manual Migration in Docker

```bash
# Run migration command in container
docker exec whisperengine-assistant alembic upgrade head

# Check status in container
docker exec whisperengine-assistant alembic current
```

## Production Deployment

### Pre-Deployment Checklist

- [ ] Migration tested in development
- [ ] Migration tested with rollback
- [ ] Backup created before deployment
- [ ] Migration reviewed by team
- [ ] Downtime requirements documented
- [ ] Rollback plan prepared

### Zero-Downtime Migrations

For production systems that can't have downtime:

1. **Phase 1**: Add new column (nullable)
   ```python
   op.add_column('users', sa.Column('new_field', sa.String(), nullable=True))
   ```

2. **Deploy**: Application writes to both old and new columns

3. **Phase 2**: Backfill existing data
   ```python
   op.execute("UPDATE users SET new_field = old_field WHERE new_field IS NULL")
   ```

4. **Phase 3**: Make column required
   ```python
   op.alter_column('users', 'new_field', nullable=False)
   ```

5. **Deploy**: Application uses only new column

6. **Phase 4**: Remove old column
   ```python
   op.drop_column('users', 'old_field')
   ```

### Emergency Rollback

If a migration causes issues in production:

```bash
# SSH into production server
ssh production-server

# Rollback last migration
cd /opt/whisperengine
./scripts/migrations/db-migrate.sh downgrade -1

# Restart application
docker-compose restart whisperengine-assistant

# Verify application health
curl http://localhost:9091/health
```

## Baseline Migration (v1.0.6)

The initial migration captures the v1.0.6 database schema. For existing deployments:

```bash
# Mark database as up-to-date without running migrations
./scripts/migrations/db-migrate.sh stamp head

# This tells Alembic your database already has the v1.0.6 schema
```

## Troubleshooting

### "Target database is not up to date"

Your database is behind. Apply pending migrations:
```bash
./scripts/migrations/db-migrate.sh upgrade
```

### "Can't locate revision identified by 'abc123'"

Migration file is missing. Ensure all migrations are committed:
```bash
git pull origin main
```

### "Duplicate column name"

Migration already partially applied. Check current state:
```bash
./scripts/migrations/db-migrate.sh current
psql -h localhost -p 5433 -U whisperengine -c "\d table_name"
```

### Connection Errors

Check environment variables:
```bash
echo $POSTGRES_HOST
echo $POSTGRES_PORT
echo $POSTGRES_DB

# Verify database is running
docker ps | grep postgres
```

## Best Practices

### ✅ DO

- **Test migrations thoroughly** in development before production
- **Write reversible migrations** with proper downgrade() functions
- **Keep migrations small** and focused on one change
- **Add comments** explaining complex migrations
- **Version control** all migration files
- **Backup before migrations** in production
- **Document breaking changes** in migration commit messages

### ❌ DON'T

- **Edit existing migrations** after they're deployed
- **Delete migration files** that have been applied
- **Skip migrations** by manually editing the database
- **Forget downgrade()** functions
- **Make irreversible changes** without backups
- **Run untested migrations** in production
- **Commit generated code** without review

## Advanced Topics

### Branching and Merging

When multiple branches create migrations:

```bash
# Create merge migration
alembic merge -m "Merge feature branches" head1 head2

# This creates a migration that depends on both branches
```

### Custom Migration Scripts

For complex data transformations, use Python functions:

```python
def upgrade() -> None:
    # Import your application code
    from src.utils.data_migration import migrate_user_data
    
    # Run custom migration logic
    migrate_user_data()
```

## Support

For migration issues:
- Check logs: `docker logs whisperengine-assistant 2>&1 | grep -i migration`
- Review docs: This file
- GitHub issues: https://github.com/whisperengine-ai/whisperengine/issues

## References

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [WhisperEngine Architecture Docs](../architecture/DATABASE_ARCHITECTURE.md)
