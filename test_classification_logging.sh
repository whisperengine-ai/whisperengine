#!/bin/bash

# Classification Logging Test Script
# Generates diverse queries to test vector classification and InfluxDB logging

set -e

BOT_URL="http://localhost:9091"
USER_ID="classification_test_$(date +%s)"

echo "🎯 Testing Vector Classification Logging System"
echo "================================================"
echo ""
echo "Bot URL: $BOT_URL"
echo "User ID: $USER_ID"
echo ""

# Function to send query and check logs
send_query() {
    local message="$1"
    local expected_vector="$2"
    
    echo "📤 Query: $message"
    echo "   Expected vector: $expected_vector"
    
    response=$(curl -s -X POST $BOT_URL/api/chat \
        -H "Content-Type: application/json" \
        -d "{\"user_id\": \"$USER_ID\", \"message\": \"$message\", \"context\": {}}")
    
    if [ $? -eq 0 ]; then
        echo "   ✅ Query sent successfully"
    else
        echo "   ❌ Query failed"
    fi
    
    sleep 2
    echo ""
}

echo "🎭 EMOTIONAL QUERIES (Should use emotion vector)"
echo "================================================"
send_query "How am I feeling today?" "emotion"
send_query "I'm feeling really happy about our progress!" "emotion"
send_query "Why am I so worried about this project?" "emotion"
send_query "I'm excited to learn more about this!" "emotion"
send_query "This makes me feel frustrated and confused." "emotion"

echo ""
echo "🔗 SEMANTIC/PATTERN QUERIES (Should use semantic vector)"
echo "========================================================"
send_query "What patterns do you see in my behavior?" "semantic"
send_query "How do our conversations usually go?" "semantic"
send_query "What's the relationship between these concepts?" "semantic"
send_query "Can you see any trends in my learning style?" "semantic"

echo ""
echo "🧠 CONTENT/FACTUAL QUERIES (Should use content vector)"
echo "======================================================"
send_query "What did we discuss about Python yesterday?" "content"
send_query "Tell me about marine biology research." "content"
send_query "What are the technical specifications?" "content"
send_query "How does the algorithm work exactly?" "content"
send_query "Explain the process step by step." "content"

echo ""
echo "⏰ TEMPORAL QUERIES (Should use temporal detection)"
echo "==================================================="
send_query "What was the first thing we talked about today?" "temporal"
send_query "What did I just say a moment ago?" "temporal"
send_query "When did we last discuss this topic?" "temporal"

echo ""
echo "🔄 HYBRID QUERIES (Should use multi-vector fusion)"
echo "=================================================="
send_query "How do I usually feel when we discuss technical topics?" "hybrid"
send_query "What emotional patterns emerge in our relationship?" "hybrid"

echo ""
echo "✅ Test queries sent!"
echo ""
echo "📊 Next Steps:"
echo "=============="
echo ""
echo "1. Check bot logs for classification decisions:"
echo "   docker logs whisperengine-elena-bot | grep 'EMOTIONAL QUERY\\|PATTERN QUERY\\|CONTENT QUERY\\|TEMPORAL QUERY'"
echo ""
echo "2. Verify InfluxDB logging:"
echo "   docker logs whisperengine-elena-bot | grep '📊 Classification logged'"
echo ""
echo "3. Check InfluxDB data:"
echo "   docker exec -it whisperengine-influxdb influx"
echo "   > use whisperengine"
echo "   > SELECT * FROM vector_classification ORDER BY time DESC LIMIT 10"
echo ""
echo "4. View in Grafana:"
echo "   Open http://localhost:3000"
echo "   Login: admin / whisperengine_grafana"
echo "   Check 'Vector Classification Intelligence' dashboard"
echo ""
echo "Expected Results:"
echo "- ~5 emotional queries (25%)"
echo "- ~4 semantic queries (20%)"
echo "- ~5 content queries (25%)"
echo "- ~3 temporal queries (15%)"
echo "- ~2 hybrid queries (10%)"
echo ""
echo "Wait 1-2 minutes for data to appear in Grafana!"
