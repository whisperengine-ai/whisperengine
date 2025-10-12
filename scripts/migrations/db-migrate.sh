#!/usr/bin/env bash
# WhisperEngine Database Migration Helper Script
# Wrapper for migrate.py with convenient shortcuts

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
MIGRATE_SCRIPT="$SCRIPT_DIR/migrate.py"

# Load environment if .env exists
if [ -f "$PROJECT_ROOT/.env" ]; then
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
fi

# Activate virtual environment if it exists
if [ -d "$PROJECT_ROOT/.venv" ]; then
    source "$PROJECT_ROOT/.venv/bin/activate"
fi

cd "$PROJECT_ROOT"

# Run the migration script
python "$MIGRATE_SCRIPT" "$@"
