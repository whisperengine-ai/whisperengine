#!/bin/bash

# ChatGPT Memories Import Script for WhisperEngine
# Imports ChatGPT-style memories (user facts) into PostgreSQL semantic knowledge graph

set -e

# Default values
USER_ID=""
CHARACTER="aetheris"
MEMORIES_FILE=""
DRY_RUN=""
VERBOSE=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --user-id)
            USER_ID="$2"
            shift 2
            ;;
        --character)
            CHARACTER="$2"
            shift 2
            ;;
        --file)
            MEMORIES_FILE="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN="--dry-run"
            shift
            ;;
        --verbose|-v)
            VERBOSE="--verbose"
            shift
            ;;
        --help|-h)
            echo "Usage: $0 --user-id USER_ID --file MEMORIES_FILE [OPTIONS]"
            echo ""
            echo "Import ChatGPT memories into WhisperEngine PostgreSQL knowledge graph"
            echo ""
            echo "Required:"
            echo "  --user-id USER_ID      Discord user ID (e.g., 1008886439108411472)"
            echo "  --file MEMORIES_FILE   Path to memories file (one memory per line)"
            echo ""
            echo "Options:"
            echo "  --character NAME       Character name (default: aetheris)"
            echo "  --dry-run             Parse only, don't store in database"
            echo "  --verbose, -v         Verbose logging"
            echo "  --help, -h            Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 --user-id 1008886439108411472 --file cynthia_memories.txt"
            echo "  $0 --user-id 1008886439108411472 --file memories.txt --dry-run --verbose"
            exit 0
            ;;
        *)
            echo "❌ Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Validate required arguments
if [[ -z "$USER_ID" ]]; then
    echo "❌ Error: --user-id is required"
    echo "Use --help for usage information"
    exit 1
fi

if [[ -z "$MEMORIES_FILE" ]]; then
    echo "❌ Error: --file is required"
    echo "Use --help for usage information"
    exit 1
fi

# Check if file exists
if [[ ! -f "$MEMORIES_FILE" ]]; then
    echo "❌ Error: Memories file not found: $MEMORIES_FILE"
    exit 1
fi

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "🚀 ChatGPT Memories Import"
echo "=========================="
echo "User ID: $USER_ID"
echo "Character: $CHARACTER"
echo "Memories file: $MEMORIES_FILE"
echo "Project root: $PROJECT_ROOT"

if [[ -n "$DRY_RUN" ]]; then
    echo "Mode: DRY RUN (no database changes)"
else
    echo "Mode: LIVE IMPORT (will store in database)"
fi

echo ""

# Change to project root
cd "$PROJECT_ROOT"

# Activate virtual environment if it exists
if [[ -d ".venv" ]]; then
    echo "📦 Activating virtual environment..."
    source .venv/bin/activate
fi

# Set required environment variables
export QDRANT_HOST="localhost"
export QDRANT_PORT="6334"
export FASTEMBED_CACHE_PATH="/tmp/fastembed_cache"

# Check if infrastructure is running
echo "🔍 Checking infrastructure..."

# Check PostgreSQL
if ! nc -z localhost 5433 2>/dev/null; then
    echo "❌ PostgreSQL not running on localhost:5433"
    echo "   Run: ./multi-bot.sh start infrastructure"
    exit 1
fi

# Check Qdrant (might not be needed for memories but good to verify)
if ! nc -z localhost 6334 2>/dev/null; then
    echo "⚠️  Qdrant not running on localhost:6334 (not required for memories import)"
fi

echo "✅ PostgreSQL is running"

# Run the import
echo "🔄 Starting import..."
python scripts/chatgpt_import/memories_importer.py \
    "$MEMORIES_FILE" \
    --user-id "$USER_ID" \
    --character "$CHARACTER" \
    $DRY_RUN \
    $VERBOSE

echo ""
echo "🎉 Import script completed!"

if [[ -z "$DRY_RUN" ]]; then
    echo ""
    echo "💡 Next steps:"
    echo "   1. Test querying: Ask $CHARACTER about user preferences"
    echo "   2. Import conversations: Use existing ChatGPT conversation importer"
    echo "   3. Verify facts: Check PostgreSQL fact_entities and user_fact_relationships tables"
fi