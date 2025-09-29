#!/bin/bash
#
# Quick Smoke Test Runner for WhisperEngine
# 
# This script activates the virtual environment and runs smoke tests
# with common configurations.
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Activate virtual environment
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "❌ Virtual environment not found at .venv/bin/activate"
    echo "Please run: python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Parse command line arguments
BOT=""
VERBOSE=""
SEQUENTIAL=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --bot)
            BOT="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE="--verbose"
            shift
            ;;
        --sequential)
            SEQUENTIAL="--sequential"
            shift
            ;;
        -h|--help)
            echo "WhisperEngine Quick Smoke Test"
            echo ""
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --bot NAME        Test specific bot (elena, marcus, ryan, dream, gabriel, sophia, jake, aethys)"
            echo "  -v, --verbose     Verbose output"
            echo "  --sequential      Run tests sequentially instead of parallel"
            echo "  -h, --help        Show this help"
            echo ""
            echo "Examples:"
            echo "  $0                      # Test all bots in parallel"
            echo "  $0 --bot elena         # Test only Elena"
            echo "  $0 --bot elena -v      # Test Elena with verbose output"
            echo "  $0 --sequential        # Test all bots sequentially"
            echo ""
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Run smoke tests
echo "🚀 Starting WhisperEngine Smoke Tests..."
if [ -n "$BOT" ]; then
    echo "🎯 Target Bot: $BOT"
fi
if [ -n "$SEQUENTIAL" ]; then
    echo "📋 Mode: Sequential"
else
    echo "⚡ Mode: Parallel"
fi
echo ""

if [ -n "$BOT" ]; then
    python scripts/smoke_test.py --bot "$BOT" $VERBOSE $SEQUENTIAL
else
    python scripts/smoke_test.py $VERBOSE $SEQUENTIAL
fi

echo ""
echo "✅ Smoke test completed!"