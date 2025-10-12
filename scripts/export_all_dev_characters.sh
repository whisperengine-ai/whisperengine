#!/bin/bash
# Export all development characters to individual SQL files
# This backs up all current dev character data before database refresh

set -e

echo "🔄 Exporting all development characters..."
echo ""

# List of primary dev characters (not duplicates or test characters)
CHARACTERS=(
    "elena"
    "gabriel" 
    "aetheris"
    "marcus"
    "sophia"
    "jake"
    "ryan"
    "dream"
    "aethys"
)

EXPORT_COUNT=0
FAILED_COUNT=0

for char in "${CHARACTERS[@]}"; do
    echo "═══════════════════════════════════════════════════════════"
    if ./scripts/export_character.sh "$char"; then
        ((EXPORT_COUNT++))
    else
        echo "⚠️  Failed to export: $char"
        ((FAILED_COUNT++))
    fi
    echo ""
done

echo "═══════════════════════════════════════════════════════════"
echo "📊 Export Summary:"
echo "  ✅ Successful: $EXPORT_COUNT"
echo "  ❌ Failed: $FAILED_COUNT"
echo ""
echo "📁 Files saved to: sql/characters/dev/"
echo ""
echo "To load a character:"
echo "  ./scripts/load_dev_character.sh CHARACTER_NAME"
