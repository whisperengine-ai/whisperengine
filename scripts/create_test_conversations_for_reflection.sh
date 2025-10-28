#!/bin/bash
# Create test conversations with emotional content to trigger bot self-reflections

BOT_NAME="jake"
BOT_PORT=9097
BASE_URL="http://localhost:${BOT_PORT}/api/chat"

# Use unique user ID for fresh conversation history
USER_ID="test_reflection_user_$(date +%s)"

echo "🎭 Creating Emotional Test Conversations for Bot Self-Reflection"
echo "================================================================"
echo "Bot: ${BOT_NAME}"
echo "Port: ${BOT_PORT}"
echo "User ID: ${USER_ID}"
echo ""

# Array of emotional conversation messages
messages=(
    "I'm feeling really overwhelmed today. Everything seems to be going wrong."
    "Thank you so much for listening. It really helps to talk about this."
    "I'm excited about starting my new photography project! Any tips?"
    "I feel like I'm not making progress on my goals. It's frustrating."
    "That's actually really helpful advice. I appreciate your perspective."
    "I'm worried about an important presentation tomorrow. How do you handle nerves?"
    "You always seem so positive! How do you stay motivated?"
    "I just got some bad news about a project I was working on."
    "Your encouragement means a lot to me. I feel more confident now."
    "Tell me about your most memorable adventure. I need some inspiration!"
)

echo "📝 Sending ${#messages[@]} messages to create conversation history..."
echo ""

# Send each message and display response
for i in "${!messages[@]}"; do
    msg_num=$((i + 1))
    message="${messages[$i]}"
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "💬 Message ${msg_num}/${#messages[@]}: \"${message}\""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Send message via HTTP API
    response=$(curl -s -X POST "${BASE_URL}" \
        -H "Content-Type: application/json" \
        -d "{
            \"user_id\": \"${USER_ID}\",
            \"message\": \"${message}\",
            \"metadata\": {
                \"platform\": \"api_test\",
                \"channel_type\": \"dm\"
            }
        }")
    
    # Extract bot response (simple jq-less parsing)
    bot_response=$(echo "$response" | grep -o '"response":"[^"]*"' | sed 's/"response":"//;s/"$//' | sed 's/\\n/ /g')
    
    if [ -n "$bot_response" ]; then
        echo "🤖 Jake: ${bot_response:0:150}..."
    else
        echo "⚠️ No response received"
        echo "Raw response: $response"
    fi
    
    echo ""
    
    # Small delay between messages to simulate natural conversation
    sleep 2
done

echo "✅ Created ${#messages[@]} conversation messages"
echo ""
echo "📊 Next Steps:"
echo "1. Check Qdrant for new memories: whisperengine_memory_jake collection"
echo "2. Run enrichment worker to generate self-reflections"
echo "3. Query PostgreSQL bot_self_reflections table for results"
echo ""
echo "🔍 Quick check command:"
echo "   psql -h localhost -p 5433 -U whisperengine -d whisperengine \\"
echo "      -c \"SELECT COUNT(*) FROM bot_self_reflections WHERE bot_name = 'jake';\""
