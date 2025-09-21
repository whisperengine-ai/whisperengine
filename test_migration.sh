#!/bin/bash
# test_migration.sh - Test vector-native migration
# Usage: ./test_migration.sh

set -e

echo "🧪 Testing Vector-Native Migration"
echo "================================="

echo "📊 Step 1: Starting system..."
./bot.sh stop 2>/dev/null || echo "System already stopped"
echo "🚀 Starting in dev mode..."
./bot.sh start dev

# Wait for startup
sleep 15

echo "📊 Step 2: Checking system health..."
if ./bot.sh health > post_migration_health.json; then
    echo "✅ System started successfully"
    
    # Compare health before/after
    if [ -f "pre_migration_health.json" ]; then
        echo "📊 Health comparison available in:"
        echo "   - pre_migration_health.json (before)"
        echo "   - post_migration_health.json (after)"
    fi
else
    echo "❌ System health check failed"
    echo "🔍 Checking logs for errors..."
    ./bot.sh logs | tail -20
    exit 1
fi

echo "📊 Step 3: Monitoring logs for vector-native activity..."
echo "🔍 Looking for vector prompt creation..."

# Monitor logs for vector activity
timeout 30s ./bot.sh logs -f | grep -E "(vector-native|🎭|Vector|pipeline)" || echo "No vector activity detected yet"

echo ""
echo "📋 Manual testing checklist:"
echo "1. 💬 Send a test message in Discord"
echo "2. 🔍 Watch logs: ./bot.sh logs -f"
echo "3. 🎭 Look for: '🎭 Creating vector-native prompt'"
echo "4. 🧠 Verify AI pipeline still works (Phase 1-4)"
echo "5. 💾 Check vector memory storage"
echo "6. 🎪 Test personality/emotion features"
echo ""
echo "📊 Current system status:"
./bot.sh health | jq . 2>/dev/null || ./bot.sh health

echo ""
echo "✅ Migration test complete!"
echo "🔍 Monitor logs: ./bot.sh logs"
echo "🎯 Next: Send Discord messages to test functionality"