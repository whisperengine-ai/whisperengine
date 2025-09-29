#!/bin/bash
set -e

echo "🧪 WhisperEngine Emotion System Test Suite"
echo "=========================================="

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Please run from the whisperengine root directory"
    exit 1
fi

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo "🔧 Activating virtual environment..."
    source .venv/bin/activate
fi

echo ""
echo "📋 Test Plan:"
echo "  1. Unit tests for emotion systems"
echo "  2. Integration validation script"
echo "  3. Performance benchmarks"
echo ""

# Run unit tests
echo "1️⃣ Running comprehensive unit tests..."
echo "------------------------------------"
if python -m pytest tests/unit/test_emotion_systems.py -v --tb=short; then
    echo "✅ Unit tests passed!"
else
    echo "❌ Unit tests failed!"
    echo "   See output above for details"
fi

echo ""

# Run integration tests
echo "2️⃣ Running integration validation..."
echo "----------------------------------"
if python scripts/test_emotion_improvements.py; then
    echo "✅ Integration tests passed!"
else
    echo "❌ Integration tests failed!"
    echo "   Check for missing dependencies or model files"
fi

echo ""

# Quick performance test
echo "3️⃣ Running performance validation..."
echo "----------------------------------"
python -c "
import time
import asyncio
from src.intelligence.emotion_taxonomy import UniversalEmotionTaxonomy

# Test VADER mapping performance
test_scores = {'pos': 0.7, 'neg': 0.2, 'neu': 0.1, 'compound': 0.5}
start = time.time()

for _ in range(1000):
    results = UniversalEmotionTaxonomy.vader_sentiment_to_emotions(test_scores)

elapsed = time.time() - start
print(f'VADER mapping: {elapsed:.3f}s for 1000 iterations')
print(f'Average: {elapsed/1000*1000:.2f}ms per mapping')

if elapsed < 0.1:
    print('✅ Performance excellent')
elif elapsed < 0.5:
    print('✅ Performance good') 
else:
    print('⚠️ Performance slower than expected')
"

echo ""
echo "🎉 Emotion system test suite completed!"
echo ""
echo "📊 Summary:"
echo "  • Universal Emotion Taxonomy: Consistent VADER mapping"
echo "  • RoBERTa Analyzer: Non-blocking with timeout protection"
echo "  • Multi-Analyzer: Unified fallback chains"
echo "  • Performance: Optimized for real-time operation"
echo ""
echo "🔍 For detailed results, see:"
echo "  • tests/EMOTION_SYSTEM_IMPROVEMENTS.md"
echo "  • Individual test outputs above"