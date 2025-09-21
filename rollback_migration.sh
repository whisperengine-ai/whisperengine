#!/bin/bash
# rollback_migration.sh - Emergency rollback script
# Usage: ./rollback_migration.sh

set -e

echo "🔄 EMERGENCY ROLLBACK - WhisperEngine Vector Migration"
echo "====================================================="
echo "WARNING: This will undo all migration changes!"
echo "Press Enter to continue, Ctrl+C to abort"
read -r

echo "🔄 Rolling back to pre-migration state..."

# Stop current system
echo "🛑 Stopping current system..."
./bot.sh stop 2>/dev/null || echo "System already stopped"

# Find latest pre-migration tag
LATEST_TAG=$(git tag | grep pre-vector-migration | sort | tail -1)
if [ -z "$LATEST_TAG" ]; then
    echo "❌ No pre-migration tag found! Manual rollback needed."
    echo "Try: git checkout main && git reset --hard HEAD~5"
    exit 1
fi

echo "📦 Rolling back to tag: $LATEST_TAG"

# Rollback to tag
git checkout main
git reset --hard "$LATEST_TAG"

# Restart system
echo "🚀 Restarting system..."
./bot.sh restart dev

echo "✅ Rollback complete!"
echo "📊 System should be back to pre-migration state"
echo "🔍 Check logs: ./bot.sh logs"