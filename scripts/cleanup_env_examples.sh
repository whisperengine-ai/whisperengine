#!/bin/bash

# Cleanup Script for Redundant Environment Example Files
# Removes individual .env.*.example files since we now have a unified .env.bot-template

set -e

WORKSPACE_ROOT="${1:-.}"
cd "$WORKSPACE_ROOT"

echo "🧹 Cleaning up redundant environment example files..."

# List of specific bot example files to remove
EXAMPLE_FILES=(
    ".env.elena.example"
    ".env.marcus.example" 
    ".env.marcus-chen.example"
    ".env.gabriel.example"
    ".env.dream.example"
    ".env.multi-bot.example"
)

removed_count=0
for file in "${EXAMPLE_FILES[@]}"; do
    if [[ -f "$file" ]]; then
        echo "  🗑️  Removing $file"
        rm "$file"
        ((removed_count++))
    else
        echo "  ⚠️  $file not found (already removed)"
    fi
done

echo ""
if [[ $removed_count -gt 0 ]]; then
    echo "✅ Removed $removed_count redundant example files"
else
    echo "✅ No redundant files found to remove"
fi

echo ""
echo "📋 Template file: .env.bot-template"
echo "📖 To create a new bot:"
echo "   1. cp .env.bot-template .env.{bot_name}"
echo "   2. Edit .env.{bot_name} with bot-specific values"
echo "   3. Create character JSON in characters/examples/"
echo "   4. Regenerate config: source .venv/bin/activate && python scripts/generate_multi_bot_config.py"