#!/bin/bash
# Quick start script for clean experiment execution
# This is a simple wrapper around the Python automation script

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}═══════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Dotty × NotTaylor Clean Experiment - Quick Start${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════════${NC}"
echo ""

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source .venv/bin/activate
fi

# Check if infrastructure is running
echo -e "${YELLOW}Checking infrastructure...${NC}"
if ! docker ps | grep -q "postgres"; then
    echo -e "${RED}Infrastructure not running! Starting...${NC}"
    ./multi-bot.sh infra
    sleep 5
fi

# Make script executable
chmod +x scripts/run_clean_experiment.py

# Show menu
echo ""
echo "Choose experiment mode:"
echo "  1) Run all 12 tests (full experiment, ~90 minutes)"
echo "  2) Run Phase 1 only (Mistral+Mistral, 3 tests, ~20 minutes)"
echo "  3) Run Phase 2 only (Claude+Claude, 3 tests, ~20 minutes)"
echo "  4) Run Phase 3 only (Mistral+Claude, 3 tests, ~20 minutes)"
echo "  5) Run Phase 4 only (Claude+Mistral, 3 tests, ~20 minutes)"
echo "  6) Run single test (specify test ID)"
echo "  7) List all available tests"
echo ""
read -p "Enter choice [1-7]: " choice

case $choice in
    1)
        echo -e "${GREEN}Running full experiment (12 tests)...${NC}"
        python scripts/run_clean_experiment.py --all
        ;;
    2)
        echo -e "${GREEN}Running Phase 1 (Mistral+Mistral)...${NC}"
        python scripts/run_clean_experiment.py --phase 1
        ;;
    3)
        echo -e "${GREEN}Running Phase 2 (Claude+Claude)...${NC}"
        python scripts/run_clean_experiment.py --phase 2
        ;;
    4)
        echo -e "${GREEN}Running Phase 3 (Mistral+Claude)...${NC}"
        python scripts/run_clean_experiment.py --phase 3
        ;;
    5)
        echo -e "${GREEN}Running Phase 4 (Claude+Mistral)...${NC}"
        python scripts/run_clean_experiment.py --phase 4
        ;;
    6)
        python scripts/run_clean_experiment.py --list
        echo ""
        read -p "Enter test ID (e.g., T1-A): " test_id
        echo -e "${GREEN}Running test ${test_id}...${NC}"
        python scripts/run_clean_experiment.py --test "$test_id"
        ;;
    7)
        python scripts/run_clean_experiment.py --list
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

# Post-execution
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  Experiment completed! 🎉${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Convert conversations to markdown:"
    echo "     python scripts/convert_bot_conversations_to_markdown.py"
    echo ""
    echo "  2. Analyze results:"
    echo "     python scripts/analyze_clean_experiment.py"
    echo ""
    echo "Results saved to: experiments/clean_experiment_oct2025/"
else
    echo -e "${RED}Experiment failed. Check logs above for details.${NC}"
    exit 1
fi
