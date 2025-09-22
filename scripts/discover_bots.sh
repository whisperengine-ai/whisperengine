#!/bin/bash

# Simple Bot Discovery Script
# Discovers bot configurations from .env.* files and generates list

set -e

WORKSPACE_ROOT="${1:-.}"
cd "$WORKSPACE_ROOT"

echo "🔍 Discovering bot configurations..."

# Find all .env.* files (excluding .example files)
BOT_CONFIGS=()
while IFS= read -r -d '' env_file; do
    filename=$(basename "$env_file")
    if [[ "$filename" =~ ^\.env\.(.+)$ && ! "$filename" =~ \.example$ ]]; then
        bot_name="${BASH_REMATCH[1]}"
        
        # Skip template files
        if [[ "$bot_name" == "template" || "$bot_name" == "multi-bot" ]]; then
            continue
        fi
        
        BOT_CONFIGS+=("$bot_name")
        echo "  ✓ Found bot: $bot_name (env file: $filename)"
    fi
done < <(find . -maxdepth 1 -name ".env.*" -type f -print0)

if [[ ${#BOT_CONFIGS[@]} -eq 0 ]]; then
    echo "❌ No bot configurations found. Make sure you have .env.* files for your bots."
    exit 1
fi

echo "✅ Found ${#BOT_CONFIGS[@]} bot configurations: ${BOT_CONFIGS[*]}"

# Find character files
echo ""
echo "🎭 Mapping character files..."
for bot_name in "${BOT_CONFIGS[@]}"; do
    character_file=""
    
    # Try exact match first
    if [[ -f "characters/examples/${bot_name}.json" ]]; then
        character_file="characters/examples/${bot_name}.json"
    else
        # Try common patterns
        for pattern in "${bot_name}-"*.json "*-${bot_name}".json "*${bot_name}"*.json; do
            matches=(characters/examples/$pattern)
            if [[ -f "${matches[0]}" ]]; then
                character_file="${matches[0]}"
                break
            fi
        done
        
        # Manual mapping for special cases
        case "$bot_name" in
            "elena") character_file="characters/examples/elena-rodriguez.json" ;;
            "marcus") character_file="characters/examples/marcus-thompson.json" ;;
            "dream") character_file="characters/examples/dream_of_the_endless.json" ;;
            "gabriel") character_file="characters/examples/gabriel-tether.json" ;;
        esac
        
        # Check if mapped file exists
        if [[ -n "$character_file" && ! -f "$character_file" ]]; then
            character_file=""
        fi
    fi
    
    if [[ -n "$character_file" ]]; then
        echo "  ✓ $bot_name -> $character_file"
    else
        echo "  ⚠ $bot_name -> No matching character file found"
    fi
done

echo ""
echo "🛠 To generate dynamic configuration:"
echo "1. Install PyYAML: pip3 install PyYAML (or use virtual environment)"
echo "2. Run: python3 scripts/generate_multi_bot_config.py"
echo ""
echo "📋 Current available bots: ${BOT_CONFIGS[*]}"