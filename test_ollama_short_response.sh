#!/bin/bash

# Test script to reproduce Ollama short response issue
# This mimics the user's setup with dolphin-mistral:7b

echo "🧪 Testing Ollama Short Response Issue"
echo "=========================================="
echo ""

# Check if dolphin-mistral:7b is available
echo "1️⃣  Checking if dolphin-mistral:7b is installed..."
if ollama list | grep -q "dolphin-mistral:7b"; then
    echo "✅ dolphin-mistral:7b is installed"
else
    echo "❌ dolphin-mistral:7b not found. Pulling..."
    ollama pull dolphin-mistral:7b
fi

echo ""
echo "2️⃣  Restarting Ryan bot with Ollama configuration..."
./multi-bot.sh stop-bot ryan
sleep 2
./multi-bot.sh bot ryan

echo ""
echo "3️⃣  Waiting for bot to start..."
sleep 5

echo ""
echo "4️⃣  Testing with HTTP chat API..."
echo "   Sending test message that should get a long response..."

# Use a fresh user ID to avoid conversation history
TEST_USER_ID="test_ollama_$(date +%s)"

curl -X POST http://localhost:9093/api/chat \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"${TEST_USER_ID}\",
    \"message\": \"Tell me a detailed story about your favorite video game project. Include lots of details about the gameplay, story, and what inspired you.\",
    \"metadata\": {
      \"platform\": \"api_test\",
      \"channel_type\": \"dm\"
    }
  }" | jq '.response' 2>/dev/null || echo "Error: jq not installed or response parsing failed"

echo ""
echo ""
echo "5️⃣  Check the logs for token limits and response length:"
echo "   Look for: 'Token limits - Chat:', 'max_tokens=', 'Extracted response text:'"
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml logs ryan-bot --tail=50 | grep -E "(Token limits|max_tokens|Extracted response|Successfully received)"

echo ""
echo "=========================================="
echo "✅ Test complete! Review the response above."
echo "   - If response is cut short (~256 chars), issue reproduced"
echo "   - If response is full length, issue may be model-specific"
