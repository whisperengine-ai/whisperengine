#!/bin/bash

# WhisperEngine Unified Bot Management - Redirect Script
# All bot operations now use ./multi-bot.sh

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo -e "${YELLOW}⚠️  Bot.sh has been replaced with a unified approach!${NC}"
echo ""
echo -e "${BLUE}ℹ️  WhisperEngine now uses ./multi-bot.sh for ALL bot operations:${NC}"
echo -e "${BLUE}   • Single bot: ./multi-bot.sh start elena${NC}"
echo -e "${BLUE}   • Multiple bots: ./multi-bot.sh start${NC}"
echo -e "${BLUE}   • Infrastructure only: Configure only the bots you want${NC}"
echo ""

command="${1:-help}"
case "$command" in
    "start")
        echo -e "${GREEN}✅ Equivalent command: ./multi-bot.sh start elena${NC}"
        echo "   (or whichever bot you want to run)"
        ;;
    "stop")
        echo -e "${GREEN}✅ Equivalent command: ./multi-bot.sh stop${NC}"
        ;;
    "logs")
        echo -e "${GREEN}✅ Equivalent command: ./multi-bot.sh logs elena${NC}"
        ;;
    "status")
        echo -e "${GREEN}✅ Equivalent command: ./multi-bot.sh status${NC}"
        ;;
    *)
        echo -e "${GREEN}✅ Try: ./multi-bot.sh help${NC}"
        ;;
esac

echo ""
echo -e "${BLUE}ℹ️  🚀 Quick Start for Single Bot:${NC}"
echo "   1. cp .env.elena.example .env.elena"
echo "   2. # Edit .env.elena with your Discord token"  
echo "   3. ./multi-bot.sh start elena"
echo ""
echo -e "${BLUE}ℹ️  📖 Full Documentation: MULTI_BOT_OPERATIONS_GUIDE.md${NC}"
echo ""
echo -e "${GREEN}✅ Use ./multi-bot.sh for all future bot operations!${NC}"
