#!/bin/bash

# PostgreSQL Migration Script: Add preferences column
# Run this script to fix "column 'preferences' does not exist" error

set -e  # Exit on any error

echo "🔄 Running PostgreSQL migration: Add preferences column"
echo "======================================================"

# Database connection parameters (adjust as needed)
DB_HOST=${POSTGRES_HOST:-localhost}
DB_PORT=${POSTGRES_PORT:-5432} 
DB_NAME=${POSTGRES_DB:-whisper_engine}
DB_USER=${POSTGRES_USER:-bot_user}

# For Docker containers, use container hostname
if [ "${CONTAINER_MODE:-false}" = "true" ]; then
    DB_HOST=postgres
fi

echo "📊 Connecting to database..."
echo "   Host: $DB_HOST"
echo "   Port: $DB_PORT"
echo "   Database: $DB_NAME"
echo "   User: $DB_USER"
echo ""

# Check if we can connect to the database
echo "🔍 Testing database connection..."
if ! docker-compose exec postgres psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "\q" 2>/dev/null; then
    echo "❌ Cannot connect to PostgreSQL database"
    echo "   Make sure the database is running: docker-compose up postgres"
    exit 1
fi

echo "✅ Database connection successful"
echo ""

# Run the migration
echo "🚀 Running migration script..."
docker-compose exec postgres psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f /sql/add_preferences_column.sql

echo ""
echo "✅ Migration completed successfully!"
echo "   The 'preferences' column has been added to the user_profiles table"
echo "   Your bots should now start without the column error"