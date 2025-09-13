#!/bin/bash
"""
Automated Log Management for Discord Bot
Cron job script for regular log maintenance
"""

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_DIR/logs"
PYTHON_CMD="python3"

# Logging for the cron job itself
CRON_LOG="$LOG_DIR/log_management_cron.log"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Function to log with timestamp
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$CRON_LOG"
}

# Navigate to project directory
cd "$PROJECT_DIR" || exit 1

log_message "Starting automated log management"

# Archive logs older than 7 days (compress them)
log_message "Archiving old logs..."
$PYTHON_CMD scripts/manage_logs.py --action archive --days-old 7 --compress >> "$CRON_LOG" 2>&1

# Clean up logs older than 30 days
log_message "Cleaning up very old logs..."
$PYTHON_CMD scripts/manage_logs.py --action cleanup --days-to-keep 30 >> "$CRON_LOG" 2>&1

# Get current stats
log_message "Current log statistics:"
$PYTHON_CMD scripts/manage_logs.py --action stats --log-dir logs >> "$CRON_LOG" 2>&1

log_message "Automated log management completed"

# Keep cron log itself under control (last 1000 lines)
if [ -f "$CRON_LOG" ]; then
    tail -n 1000 "$CRON_LOG" > "$CRON_LOG.tmp" && mv "$CRON_LOG.tmp" "$CRON_LOG"
fi
