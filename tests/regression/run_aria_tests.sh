#!/bin/bash
# ARIA Regression Test Runner - Quick Reference
# Location: tests/regression/run_aria_tests.sh
# Usage: ./run_aria_tests.sh [option]

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         ARIA Regression Test Runner                        ║${NC}"
echo -e "${BLUE}║         WhisperEngine - Starship AI Testing               ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"

# Default command
COMMAND="${1:-all}"

case "$COMMAND" in
  all)
    echo -e "${YELLOW}Running all ARIA regression tests...${NC}"
    python tests/regression/comprehensive_character_regression.py --bots aria
    ;;
  
  emotional)
    echo -e "${YELLOW}Running emotional trigger tests...${NC}"
    python tests/regression/comprehensive_character_regression.py --bots aria --category "Emotional Triggers"
    ;;
  
  behavioral)
    echo -e "${YELLOW}Running behavioral quirk tests...${NC}"
    python tests/regression/comprehensive_character_regression.py --bots aria --category "Behavioral Quirks"
    ;;
  
  ethics)
    echo -e "${YELLOW}Running AI ethics tests...${NC}"
    python tests/regression/comprehensive_character_regression.py --bots aria --category "AI Ethics"
    ;;
  
  personality)
    echo -e "${YELLOW}Running character personality tests...${NC}"
    python tests/regression/comprehensive_character_regression.py --bots aria --category "Character Personality"
    ;;
  
  modes)
    echo -e "${YELLOW}Running conversation modes tests...${NC}"
    python tests/regression/comprehensive_character_regression.py --bots aria --category "Conversation Modes"
    ;;
  
  quick)
    echo -e "${YELLOW}Running quick smoke test (5 tests)...${NC}"
    python tests/regression/comprehensive_character_regression.py --bots aria --tests aria_baseline,aria_worry_trigger,aria_emergency_response,aria_consciousness,aria_safety_override
    ;;
  
  compare)
    echo -e "${YELLOW}Comparing ARIA with other characters...${NC}"
    python tests/regression/comprehensive_character_regression.py --bots aria,elena,marcus,gabriel
    ;;
  
  verbose)
    echo -e "${YELLOW}Running all ARIA tests with verbose output...${NC}"
    python tests/regression/comprehensive_character_regression.py --bots aria --verbose
    ;;
  
  setup)
    echo -e "${YELLOW}Setting up test environment...${NC}"
    echo -e "${BLUE}Starting infrastructure...${NC}"
    ./multi-bot.sh infra
    sleep 5
    echo -e "${BLUE}Starting ARIA bot...${NC}"
    ./multi-bot.sh bot aria
    sleep 10
    echo -e "${GREEN}✅ Test environment ready!${NC}"
    echo -e "${BLUE}To run tests:${NC} python tests/regression/comprehensive_character_regression.py --bots aria"
    ;;
  
  stop)
    echo -e "${YELLOW}Stopping ARIA...${NC}"
    ./multi-bot.sh stop-bot aria
    echo -e "${GREEN}✅ ARIA stopped${NC}"
    ;;
  
  health)
    echo -e "${YELLOW}Checking ARIA health...${NC}"
    if curl -s http://localhost:9459/health | grep -q "ok"; then
      echo -e "${GREEN}✅ ARIA is running (port 9459)${NC}"
    else
      echo -e "${RED}❌ ARIA is not responding${NC}"
      echo -e "${BLUE}Start with:${NC} ./multi-bot.sh bot aria"
    fi
    ;;
  
  report)
    echo -e "${YELLOW}Latest test results...${NC}"
    LATEST=$(ls -t smoke_test_reports/regression_test_results_aria_*.json 2>/dev/null | head -1)
    if [ -z "$LATEST" ]; then
      echo -e "${RED}No test reports found${NC}"
      echo -e "${BLUE}Run tests first:${NC} ./run_aria_tests.sh all"
    else
      echo -e "${BLUE}Report:${NC} $LATEST"
      python -m json.tool < "$LATEST" | head -100
    fi
    ;;
  
  help|--help|-h)
    echo -e "${BLUE}Usage:${NC} ./run_aria_tests.sh [COMMAND]"
    echo ""
    echo -e "${BLUE}Commands:${NC}"
    echo "  ${GREEN}all${NC}          Run all 15 ARIA regression tests"
    echo "  ${GREEN}emotional${NC}     Run emotional trigger tests only (8 tests)"
    echo "  ${GREEN}behavioral${NC}    Run behavioral quirk tests only (5 tests)"
    echo "  ${GREEN}ethics${NC}        Run AI ethics tests only (3 tests)"
    echo "  ${GREEN}personality${NC}   Run character personality tests (3 tests)"
    echo "  ${GREEN}modes${NC}         Run conversation mode tests (2 tests)"
    echo "  ${GREEN}quick${NC}         Run quick smoke test (5 critical tests)"
    echo "  ${GREEN}compare${NC}       Compare ARIA with other characters"
    echo "  ${GREEN}verbose${NC}       Run all tests with detailed output"
    echo "  ${GREEN}setup${NC}         Start infrastructure and ARIA bot"
    echo "  ${GREEN}stop${NC}          Stop ARIA bot"
    echo "  ${GREEN}health${NC}        Check if ARIA is running"
    echo "  ${GREEN}report${NC}        Show latest test report"
    echo "  ${GREEN}help${NC}          Show this help message"
    echo ""
    echo -e "${BLUE}Examples:${NC}"
    echo "  # Run all tests"
    echo "  ./run_aria_tests.sh all"
    echo ""
    echo "  # Run emotional triggers and behavioral quirks"
    echo "  ./run_aria_tests.sh emotional"
    echo "  ./run_aria_tests.sh behavioral"
    echo ""
    echo "  # Quick smoke test"
    echo "  ./run_aria_tests.sh quick"
    echo ""
    echo "  # Setup and run"
    echo "  ./run_aria_tests.sh setup"
    echo "  ./run_aria_tests.sh all"
    echo ""
    echo -e "${BLUE}Quick Start:${NC}"
    echo "  1. ./run_aria_tests.sh setup"
    echo "  2. Wait 15 seconds for startup"
    echo "  3. ./run_aria_tests.sh quick"
    ;;
  
  *)
    echo -e "${RED}❌ Unknown command: $COMMAND${NC}"
    echo -e "${BLUE}Use '${NC}./run_aria_tests.sh help${BLUE}' for available commands${NC}"
    exit 1
    ;;
esac
