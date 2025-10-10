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

# Note: Database migrations are now handled by dedicated init container
if is_container && [ -n "${POSTGRES_HOST:-}" ]; then
    log "ℹ️  Database migrations handled by db-migrate init container"
else
    log "⏭️ Skipping migration check (not in container or no database config)"
fi

log "🎯 Starting WhisperEngine bot..."
echo ""

# Start the main application
exec python /app/run.py