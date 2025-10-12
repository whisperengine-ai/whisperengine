#!/usr/bin/env bash
# WhisperEngine Container Entrypoint with Auto-Migration
# Runs database migrations before starting the application

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

# Run database migrations
echo "🔄 Running database migrations..."
if alembic upgrade head; then
    echo "✅ Migrations applied successfully"
else
    echo "❌ Migration failed!"
    exit 1
fi

# Show current migration status
echo "📊 Current migration status:"
alembic current

# Start the application
echo "🎯 Starting WhisperEngine application..."
exec python run.py
