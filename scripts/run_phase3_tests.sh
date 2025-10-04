#!/bin/bash

# Phase 3+ Intelligence Automated Test Runner
# ==========================================

set -e

echo "🚀 Phase 3+ Intelligence Automated Test Suite"
echo "=============================================="

# Check if Elena bot is running
echo "🔍 Checking Elena bot status..."
if ! curl -s http://localhost:9091/health > /dev/null; then
    echo "❌ Elena bot is not running or not accessible at http://localhost:9091"
    echo "💡 Start Elena bot with: ./multi-bot.sh start elena"
    exit 1
fi

echo "✅ Elena bot is running and healthy"

# Create reports directory if it doesn't exist
mkdir -p tests/automated/reports

# Run the automated test suite
echo "🧪 Running Phase 3+ Intelligence Tests..."
echo ""

cd "$(dirname "$0")/../.."  # Go to project root

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo "📦 Activating virtual environment..."
    source .venv/bin/activate
    PYTHON_CMD=".venv/bin/python"
else
    PYTHON_CMD="python"
fi

# Install required dependencies if not already installed
echo "📦 Checking dependencies..."
$PYTHON_CMD -m pip install aiohttp --quiet

# Run the test suite
echo "🎯 Executing test suite..."
$PYTHON_CMD tests/automated/test_phase3_intelligence_automated.py --save-report "$@"

echo ""
echo "✅ Test suite completed!"
echo "📄 Check tests/automated/reports/ for detailed results"