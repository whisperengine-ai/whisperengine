#!/bin/bash
# quick_migrate.sh - No-fallback vector-native migration
# Usage: ./quick_migrate.sh

set -e  # Exit on any error

echo "🚀 WhisperEngine Vector-Native Migration"
echo "========================================"
echo "Mode: No-fallback, git-based rollback"
echo "Date: $(date)"
echo ""

# Phase 1: Safety
echo "📦 Phase 1: Creating safety nets..."
git checkout -b vector-native-migration 2>/dev/null || git checkout vector-native-migration
git tag pre-vector-migration-$(date +%Y%m%d_%H%M%S) 2>/dev/null || echo "Tag exists, continuing..."

# Check current health
echo "🏥 Checking current system health..."
if ./bot.sh health > pre_migration_health.json 2>/dev/null; then
    echo "✅ Current system healthy"
else
    echo "⚠️ System not responding, continuing anyway..."
fi

echo ""
echo "🎯 Phase 2: Ready to execute migration"
echo "Next steps:"
echo "1. Run: ./migrate_prompts.sh (replaces prompt system)"
echo "2. Run: ./test_migration.sh (validates migration)"
echo "3. Run: ./cleanup_migration.sh (removes old code)"
echo ""
echo "Emergency rollback: ./rollback_migration.sh"
echo ""
echo "📋 Manual steps needed:"
echo "- Edit src/handlers/events.py (lines ~1193-1228)"
echo "- Replace template system with vector-native calls"
echo "- Remove template variable imports"
echo ""
echo "Ready to proceed? (Press Enter to continue, Ctrl+C to abort)"
read -r