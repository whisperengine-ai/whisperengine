#!/bin/bash
# HTTP API Validation Test for Proactive Engagement Integration
# Tests: engagement detection → strategy recommendation → prompt integration

set -e

ELENA_API="http://localhost:9091"
TEST_USER="http_test_proactive_$(date +%s)"

echo "================================================================================"
echo "  PROACTIVE ENGAGEMENT HTTP API VALIDATION TEST"
echo "================================================================================"
echo ""
echo "Elena API: $ELENA_API"
echo "Test User: $TEST_USER"
echo ""

# Health check
echo "--- HEALTH CHECK ---"
HEALTH=$(curl -s "$ELENA_API/health")
if [ $? -eq 0 ]; then
    echo "✅ Elena bot is healthy"
    echo "$HEALTH" | python3 -m json.tool 2>/dev/null || echo "$HEALTH"
else
    echo "❌ Elena bot is not responding"
    exit 1
fi

sleep 2

# Test 1: Baseline conversation
echo ""
echo "================================================================================"
echo "  TEST 1: BASELINE - Normal Conversation"
echo "================================================================================"
echo ""

send_message() {
    local message="$1"
    echo "📤 Sending: '$message'"
    
    RESPONSE=$(curl -s -X POST "$ELENA_API/api/chat" \
        -H "Content-Type: application/json" \
        -d "{
            \"user_id\": \"$TEST_USER\",
            \"message\": \"$message\",
            \"metadata_level\": \"extended\"
        }")
    
    if [ $? -eq 0 ]; then
        echo "✅ Response received"
        BOT_RESPONSE=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('response', 'No response')[:300])" 2>/dev/null || echo "Could not parse response")
        echo "   Elena: $BOT_RESPONSE"
        echo "$RESPONSE" > "/tmp/elena_response_$(date +%s).json"
    else
        echo "❌ Request failed"
    fi
    echo ""
}

send_message "Hi Elena! How are you today?"
sleep 3

send_message "Tell me about your marine research work"
sleep 3

echo ""
echo "================================================================================"
echo "  TEST 2: STAGNATION - Short Message Pattern"
echo "================================================================================"
echo ""
echo "⚠️  Sending very short messages to trigger stagnation detection"
echo "    Expected: Proactive topic suggestion after 3-4 short messages"
echo ""

send_message "ok"
sleep 3

send_message "cool"
sleep 3

send_message "nice"
sleep 3

send_message "yeah"
sleep 3

echo ""
echo "================================================================================"
echo "  TEST 3: RECOVERY - Re-engagement"
echo "================================================================================"
echo ""

send_message "Elena, I'd love to hear more about your coral restoration projects. What's the biggest challenge?"
sleep 3

echo ""
echo "================================================================================"
echo "  TEST COMPLETE"
echo "================================================================================"
echo ""
echo "✅ All requests sent successfully"
echo ""
echo "📋 Check for proactive engagement in responses:"
echo "   - Look for natural topic suggestions in short message responses"
echo "   - Check for questions that weren't directly prompted"
echo "   - Verify Elena suggests new conversation directions"
echo ""
echo "🔍 Detailed logs:"
echo "   docker compose logs elena-bot --since 10m | grep -E '🎯 ENGAGEMENT'"
echo ""
