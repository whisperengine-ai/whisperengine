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

# Note: Run database migrations if in container and database config available
if is_container && [ -n "${POSTGRES_HOST:-}" ]; then
    log "🗄️  Running database migrations..."
    python /app/src/utils/auto_migrate.py
    if [ $? -eq 0 ]; then
        log "✅ Database migrations completed successfully"
    else
        log "❌ Database migrations failed"
        exit 1
    fi
else
    log "⏭️ Skipping migration check (not in container or no database config)"
fi

log "🎯 Starting WhisperEngine bot..."
echo ""

# Start the main application
exec python /app/run.py