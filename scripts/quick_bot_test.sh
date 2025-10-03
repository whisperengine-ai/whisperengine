#!/bin/bash
# Quick Bot API Test Script
# Simple curl-based tests for WhisperEngine bot APIs

echo "🤖 WhisperEngine Bot API Quick Test"
echo "=================================="

# Function to get bot config
get_bot_config() {
    case $1 in
        "elena") echo "9091:Marine Biologist:🌊" ;;
        "marcus") echo "9092:AI Researcher:🤖" ;;
        "ryan") echo "9093:Indie Game Developer:🎮" ;;
        "dream") echo "9094:Mythological Entity:🌙" ;;
        "gabriel") echo "9095:British Gentleman:🎩" ;;
        "sophia") echo "9096:Marketing Executive:💼" ;;
        "jake") echo "9097:Adventure Photographer:📸" ;;
        "aethys") echo "3007:Omnipotent Entity:✨" ;;
        *) echo "" ;;
    esac
}

# All bot names
ALL_BOTS="elena marcus ryan dream gabriel sophia jake aethys"

# Function to test a single bot
test_bot() {
    local bot_name=$1
    local config=$(get_bot_config $bot_name)
    if [ -z "$config" ]; then
        echo "❌ Unknown bot: $bot_name"
        return 1
    fi
    local port=$(echo $config | cut -d: -f1)
    local profession=$(echo $config | cut -d: -f2)
    local emoji=$(echo $config | cut -d: -f3)
    
    echo ""
    echo "$emoji Testing $bot_name ($profession) on port $port"
    echo "----------------------------------------"
    
    # Test health endpoint
    echo -n "Health: "
    health_status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$port/health)
    if [ "$health_status" = "200" ]; then
        echo "✅ PASS"
    else
        echo "❌ FAIL ($health_status)"
        return
    fi
    
    # Test bot info endpoint
    echo -n "Info:   "
    info_status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$port/api/bot-info)
    if [ "$info_status" = "200" ]; then
        echo "✅ PASS"
    else
        echo "❌ FAIL ($info_status)"
        return
    fi
    
    # Test chat endpoint
    echo -n "Chat:   "
    chat_response=$(curl -s -X POST -H "Content-Type: application/json" \
        -d "{\"message\": \"Hello! Quick test.\", \"user_id\": \"test_$(date +%s)\"}" \
        http://localhost:$port/api/chat)
    
    if echo "$chat_response" | jq -e '.success == true' > /dev/null 2>&1; then
        echo "✅ PASS"
        # Show a snippet of the response
        response_text=$(echo "$chat_response" | jq -r '.response' | head -c 60)
        echo "        Response: \"$response_text...\""
    else
        echo "❌ FAIL"
        echo "        Error: $chat_response"
    fi
}

# Function to test all bots
test_all_bots() {
    echo "Testing all bots..."
    local pass_count=0
    local total_count=0
    
    for bot_name in $ALL_BOTS; do
        test_bot "$bot_name"
        ((total_count++))
        
        # Check if all tests passed for this bot
        config=$(get_bot_config $bot_name)
        port=$(echo $config | cut -d: -f1)
        if curl -s http://localhost:$port/health > /dev/null && \
           curl -s http://localhost:$port/api/bot-info > /dev/null && \
           curl -s -X POST -H "Content-Type: application/json" \
           -d '{"message": "test", "user_id": "test"}' \
           http://localhost:$port/api/chat | jq -e '.success == true' > /dev/null 2>&1; then
            ((pass_count++))
        fi
    done
    
    echo ""
    echo "Summary: $pass_count/$total_count bots fully operational"
}

# Function to test a specific bot  
test_specific_bot() {
    local bot_name=$1
    local config=$(get_bot_config $bot_name)
    if [ -z "$config" ]; then
        echo "❌ Unknown bot: $bot_name"
        echo "Available bots: $ALL_BOTS"
        exit 1
    fi
    test_bot "$bot_name"
}

# Function to show working endpoints
show_endpoints() {
    echo ""
    echo "🔗 Available Bot Endpoints:"
    echo "=========================="
    for bot_name in $ALL_BOTS; do
        config=$(get_bot_config $bot_name)
        port=$(echo $config | cut -d: -f1)
        profession=$(echo $config | cut -d: -f2)
        emoji=$(echo $config | cut -d: -f3)
        
        echo "$emoji $bot_name ($profession)"
        echo "   Health: http://localhost:$port/health"
        echo "   Info:   http://localhost:$port/api/bot-info"
        echo "   Chat:   http://localhost:$port/api/chat"
        echo ""
    done
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [COMMAND] [BOT_NAME]"
    echo ""
    echo "Commands:"
    echo "  test [bot_name]  - Test specific bot (or all if no name given)"
    echo "  endpoints        - Show all available endpoints"
    echo "  help            - Show this help message"
    echo ""
    echo "Available bots: $ALL_BOTS"
    echo ""
    echo "Examples:"
    echo "  $0 test           # Test all bots"
    echo "  $0 test elena     # Test only Elena"
    echo "  $0 endpoints      # Show all endpoints"
}

# Main script logic
case "${1:-test}" in
    "test")
        if [ -z "$2" ]; then
            test_all_bots
        else
            test_specific_bot "$2"
        fi
        ;;
    "endpoints")
        show_endpoints
        ;;
    "help"|"-h"|"--help")
        show_usage
        ;;
    *)
        echo "❌ Unknown command: $1"
        show_usage
        exit 1
        ;;
esac