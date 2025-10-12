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

# NOTE: Database migrations now handled by dedicated db-migrate init container
# See docker-compose.multi-bot.yml for db-migrate service configuration
# Bot containers should NOT run migrations - this prevents race conditions
# and separates concerns between infrastructure setup and application runtime

log "⏭️  Skipping migrations (handled by db-migrate init container)"
log "🎯 Starting WhisperEngine bot..."
echo ""

# Start the main application
exec python /app/run.py