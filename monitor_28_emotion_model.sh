#!/bin/bash
# Monitor Elena for 28-emotion model loading and emotion detection

echo "🔍 Monitoring Elena for 28-emotion model initialization..."
echo "📝 Send a test message to Elena to trigger model loading"
echo ""
echo "⏰ First message will take 5-10 seconds (model download)"
echo "✅ Look for these success indicators:"
echo "   - '28-emotion model' in initialization message"
echo "   - '28 emotion results' from RoBERTa"
echo "   - 'EMOTION MAPPING (28→7)' for emotion conversions"
echo ""
echo "Press Ctrl+C to stop monitoring"
echo ""

docker logs whisperengine-elena-bot -f 2>&1 | grep --line-buffered -E \
  "(28-emotion|emotion results|EMOTION MAPPING|ROBERTA ANALYSIS: Initializing|RoBERTa detected (nervousness|annoyance|optimism)|nervousness → fear|annoyance → anger|optimism → joy)"
