#!/bin/bash
# Quick script to adjust token limits for comprehensive Phase3 testing

set -e

echo "=================================================="
echo "Phase3 Intelligence Testing - Token Limit Adjuster"
echo "=================================================="
echo ""

# Check if argument provided
if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <token_limit> [bot_names...]"
    echo ""
    echo "Examples:"
    echo "  $0 3000              # Set all bots to 3000 tokens"
    echo "  $0 3000 elena marcus # Set only Elena and Marcus to 3000"
    echo "  $0 1000              # Restore default 1000 tokens"
    echo ""
    exit 1
fi

TOKEN_LIMIT=$1
shift  # Remove first argument

# Determine which bots to update
if [ "$#" -eq 0 ]; then
    # Update all bots
    BOT_FILES=(.env.*)
    echo "Updating token limit to $TOKEN_LIMIT for ALL bots..."
else
    # Update specific bots
    BOT_FILES=()
    for bot in "$@"; do
        BOT_FILES+=(".env.$bot")
    done
    echo "Updating token limit to $TOKEN_LIMIT for: $@"
fi

echo ""

# Backup current configs
BACKUP_DIR="backup-configs/token-limits-$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

for env_file in "${BOT_FILES[@]}"; do
    if [ -f "$env_file" ]; then
        # Backup
        cp "$env_file" "$BACKUP_DIR/"
        
        # Update token limit
        if grep -q "LLM_MAX_TOKENS_CHAT=" "$env_file"; then
            sed -i '' "s/LLM_MAX_TOKENS_CHAT=.*/LLM_MAX_TOKENS_CHAT=$TOKEN_LIMIT/" "$env_file"
            echo "  ✅ Updated $env_file"
        else
            echo "  ⚠️  No LLM_MAX_TOKENS_CHAT found in $env_file"
        fi
    else
        echo "  ❌ File not found: $env_file"
    fi
done

echo ""
echo "Backup saved to: $BACKUP_DIR"
echo ""

# Ask if user wants to restart bots
read -p "Restart bots to apply changes? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Restarting bots..."
    
    if [ "$#" -eq 0 ]; then
        # Restart all bots
        ./multi-bot.sh restart all
    else
        # Restart specific bots
        ./multi-bot.sh restart "$@"
    fi
    
    echo ""
    echo "Waiting for bots to initialize (30 seconds)..."
    sleep 30
    
    echo ""
    echo "✅ Token limits updated and bots restarted!"
    echo ""
    echo "You can now run the Phase3 tests:"
    echo "  python tests/automated/test_phase3_intelligence_api.py"
else
    echo ""
    echo "⚠️  Remember to restart bots manually for changes to take effect:"
    echo "  ./multi-bot.sh restart all"
fi

echo ""
echo "To restore original settings:"
echo "  cp $BACKUP_DIR/.env.* ."
echo "  ./multi-bot.sh restart all"
echo ""
