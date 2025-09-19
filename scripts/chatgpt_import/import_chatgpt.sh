#!/bin/bash

# WhisperEngine ChatGPT Import Script
# Usage: ./scripts/chatgpt_import/import_chatgpt.sh conversations.json 123456789

set -e

CONVERSATIONS_FILE="$1"
USER_ID="$2"

# Validate arguments
if [ -z "$CONVERSATIONS_FILE" ] || [ -z "$USER_ID" ]; then
    echo "Usage: $0 <conversations.json> <user_id>"
    echo "Example: $0 conversations.json 123456789"
    exit 1
fi

# Check if file exists
if [ ! -f "$CONVERSATIONS_FILE" ]; then
    echo "❌ Error: File $CONVERSATIONS_FILE not found"
    exit 1
fi

echo "🚀 Starting ChatGPT conversation import..."
echo "📁 File: $CONVERSATIONS_FILE"
echo "👤 User ID: $USER_ID"

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Check if we should use Docker or direct Python
if command -v docker &> /dev/null && docker image ls | grep -q whisperengine; then
    echo "🐳 Using Docker..."
    python3 "$SCRIPT_DIR/docker_import.py" --file "$CONVERSATIONS_FILE" --user-id "$USER_ID" --verbose
else
    echo "🐍 Using Python directly..."
    cd "$PROJECT_ROOT"
    python3 scripts/chatgpt_import/import_chatgpt.py --file "$CONVERSATIONS_FILE" --user-id "$USER_ID" --verbose
fi

echo "✅ Import completed!"