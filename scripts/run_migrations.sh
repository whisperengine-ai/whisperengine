#!/bin/bash
# Migration runner script for Docker init container
# Runs all SQL migrations before bot starts

set -e  # Exit on any error

echo "🔧 Starting database migration..."

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL..."
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\q' 2>/dev/null; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 2
done

echo "✅ PostgreSQL is ready!"

# Create migrations tracking table if it doesn't exist
echo "📋 Creating migrations tracking table..."
PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<-EOSQL
    CREATE TABLE IF NOT EXISTS schema_migrations (
        migration_name VARCHAR(255) PRIMARY KEY,
        applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
EOSQL

# Apply init schema if not already applied
echo "🗄️  Checking for init schema..."
MIGRATION_EXISTS=$(PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "SELECT COUNT(*) FROM schema_migrations WHERE migration_name = '00_init_schema.sql';")

if [ "$MIGRATION_EXISTS" -eq "0" ]; then
    echo "📝 Applying init schema..."
    PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /app/sql/init_schema.sql
    
    # Record migration
    PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<-EOSQL
        INSERT INTO schema_migrations (migration_name) VALUES ('00_init_schema.sql');
EOSQL
    echo "✅ Init schema applied!"
else
    echo "✅ Init schema already applied, skipping..."
fi

# Apply all migrations in order
echo "🔄 Applying migrations from /app/sql/migrations/..."
if [ -d "/app/sql/migrations" ]; then
    for migration_file in /app/sql/migrations/*.sql; do
        if [ -f "$migration_file" ]; then
            MIGRATION_NAME=$(basename "$migration_file")
            
            # Check if migration already applied
            APPLIED=$(PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "SELECT COUNT(*) FROM schema_migrations WHERE migration_name = '$MIGRATION_NAME';")
            
            if [ "$APPLIED" -eq "0" ]; then
                echo "📝 Applying migration: $MIGRATION_NAME"
                PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f "$migration_file"
                
                # Record migration
                PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<-EOSQL
                    INSERT INTO schema_migrations (migration_name) VALUES ('$MIGRATION_NAME');
EOSQL
                echo "✅ Migration $MIGRATION_NAME applied!"
            else
                echo "✅ Migration $MIGRATION_NAME already applied, skipping..."
            fi
        fi
    done
else
    echo "ℹ️  No migrations directory found, skipping..."
fi

echo "🎉 All migrations complete!"
