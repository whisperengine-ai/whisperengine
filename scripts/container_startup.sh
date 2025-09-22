#!/bin/bash

# WhisperEngine Container Startup Script
# Runs automatic database migrations before starting the bot

set -e  # Exit on any error

echo "🚀 WhisperEngine Container Startup"
echo "=================================="
echo ""

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to check if running in container
is_container() {
    [ -f /.dockerenv ] || [ -n "${CONTAINER_MODE:-}" ]
}

# Only run migrations if we're in a container and have database configuration
if is_container && [ -n "${POSTGRES_HOST:-}" ]; then
    log "🔧 Running automatic database migrations..."
    
    # Run the migration system
    python /app/src/utils/auto_migrate.py
    
    migration_exit_code=$?
    if [ $migration_exit_code -eq 0 ]; then
        log "✅ Database migrations completed successfully"
    else
        log "❌ Database migrations failed with exit code $migration_exit_code"
        log "💥 Cannot start bot without valid database schema"
        exit 1
    fi
    
    echo ""
else
    log "⏭️ Skipping migrations (not in container or no database config)"
fi

log "🎯 Starting WhisperEngine bot..."
echo ""

# Start the main application
exec python /app/run.py