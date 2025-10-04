#!/bin/bash

# Phase 4 Intelligence Automated Test Runner
# Runs comprehensive Phase 4 intelligence validation

echo "🚀 Phase 4 Intelligence Automated Test Suite"
echo "=============================================="

# Check if Elena bot is running
echo "🔍 Checking Elena bot status..."
if curl -s http://localhost:9091/health > /dev/null; then
    echo "✅ Elena bot is running and healthy"
else
    echo "❌ Elena bot is not accessible on port 9091"
    echo "💡 Start Elena with: ./multi-bot.sh start elena"
    exit 1
fi

echo "🧪 Running Phase 4 Intelligence Tests..."

# Check dependencies
echo "📦 Checking dependencies..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3"
    exit 1
fi

# Check for required Python packages
python3 -c "import aiohttp, asyncio" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Required Python packages not found"
    echo "💡 Install with: pip install aiohttp asyncio"
    exit 1
fi

echo "✅ Dependencies verified"

# Run the tests
echo "🏃 Executing Phase 4 Intelligence Test Suite..."
echo ""

python3 tests/automated/test_phase4_intelligence_automated.py

test_exit_code=$?

echo ""
echo "📋 Test Runner Summary:"
if [ $test_exit_code -eq 0 ]; then
    echo "✅ Phase 4 Intelligence tests PASSED"
    echo "🎉 All Phase 4 features are operational!"
else
    echo "❌ Phase 4 Intelligence tests FAILED"
    echo "🔧 Some Phase 4 features need attention"
fi

echo "📊 For detailed analysis, check the test output above"
echo "🐳 Bot logs: docker logs whisperengine-elena-bot --tail 50"

exit $test_exit_code