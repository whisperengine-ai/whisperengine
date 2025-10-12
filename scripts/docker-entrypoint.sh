#!/usr/bin/env bash
# WhisperEngine Container Entrypoint with Smart Auto-Migration
# Automatically detects fresh vs existing databases and handles migrations appropriately

set -e

echo "🚀 WhisperEngine Container Starting..."

# Database configuration from environment
DB_HOST="${POSTGRES_HOST:-localhost}"
DB_PORT="${POSTGRES_PORT:-5433}"
DB_NAME="${POSTGRES_DB:-whisperengine}"
DB_USER="${POSTGRES_USER:-whisperengine}"

echo "📦 Environment: ${ENVIRONMENT:-production}"
echo "🗄️  Database: ${DB_NAME} at ${DB_HOST}:${DB_PORT}"

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
for i in {1..30}; do
    if pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" > /dev/null 2>&1; then
        echo "✅ PostgreSQL is ready"
        break
    fi
    
    if [ $i -eq 30 ]; then
        echo "❌ PostgreSQL failed to become ready in time"
        exit 1
    fi
    
    echo "   Attempt $i/30: PostgreSQL not ready yet, waiting..."
    sleep 2
done

# Smart migration detection
echo "🔍 Detecting database state..."

# Check if alembic_version table exists (migration tracking enabled)
if PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
   -tAc "SELECT 1 FROM information_schema.tables WHERE table_name='alembic_version'" 2>/dev/null | grep -q 1; then
    
    # Migration tracking exists - run normal upgrade
    echo "📊 Migration tracking found - checking for pending migrations..."
    if alembic upgrade head; then
        echo "✅ Migrations applied successfully"
    else
        echo "❌ Migration failed!"
        exit 1
    fi
    
else
    # No alembic_version table - check if database has existing tables
    TABLE_COUNT=$(PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
                  -tAc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public'" 2>/dev/null || echo "0")
    
    if [ "$TABLE_COUNT" -gt 5 ]; then
        # Existing database without migration tracking (v1.0.6 database)
        echo "🏷️  Existing v1.0.6 database detected (${TABLE_COUNT} tables)"
        echo "   Marking database as up-to-date with baseline..."
        if alembic stamp head; then
            echo "✅ Database marked at baseline (v1.0.6 → v1.0.7 upgrade complete)"
        else
            echo "❌ Failed to stamp database"
            exit 1
        fi
    else
        # Fresh database - run migrations
        echo "🆕 Fresh database detected - running baseline migration..."
        if alembic upgrade head; then
            echo "✅ Baseline migration complete - database initialized"
        else
            echo "❌ Migration failed!"
            exit 1
        fi
    fi
fi

# Show current migration status
echo "📊 Current migration status:"
alembic current

# Start the application
echo "🎯 Starting WhisperEngine application..."
exec python run.py
