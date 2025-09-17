#!/bin/bash

# WhisperEngine Test Runner Script
# Simplified interface for running the comprehensive test suite

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}🚀 WhisperEngine Test Runner${NC}"
echo -e "${BLUE}==============================${NC}"

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo -e "${YELLOW}⚠️  Virtual environment not detected. Attempting to activate...${NC}"
    if [[ -f "$PROJECT_ROOT/.venv/bin/activate" ]]; then
        source "$PROJECT_ROOT/.venv/bin/activate"
        echo -e "${GREEN}✅ Activated virtual environment${NC}"
    else
        echo -e "${RED}❌ Virtual environment not found at $PROJECT_ROOT/.venv${NC}"
        echo -e "${YELLOW}Please run: python -m venv .venv && source .venv/bin/activate${NC}"
        exit 1
    fi
fi

# Install test dependencies if needed
echo -e "${BLUE}📦 Checking test dependencies...${NC}"
python -m pip install -e ".[test]" > /dev/null 2>&1 || {
    echo -e "${YELLOW}⚠️  Installing test dependencies...${NC}"
    python -m pip install -e ".[test]"
}

# Parse command line arguments
TEST_CATEGORY="${1:-all}"
PARALLEL="${2:-true}"
GENERATE_REPORT="${3:-true}"

echo -e "${BLUE}🧪 Running tests...${NC}"
echo -e "   Category: ${TEST_CATEGORY}"
echo -e "   Parallel: ${PARALLEL}"
echo -e "   Generate Report: ${GENERATE_REPORT}"
echo

# Build command arguments
CMD_ARGS=(
    --category "$TEST_CATEGORY"
    --workspace "$PROJECT_ROOT"
)

if [[ "$PARALLEL" == "false" ]]; then
    CMD_ARGS+=(--no-parallel)
fi

if [[ "$GENERATE_REPORT" == "true" ]]; then
    REPORT_FILE="$PROJECT_ROOT/test_report_$(date +%Y%m%d_%H%M%S).json"
    CMD_ARGS+=(--report "$REPORT_FILE")
fi

# Run the tests
cd "$PROJECT_ROOT"
python tests/ci_test_runner.py "${CMD_ARGS[@]}"

# Check exit code
EXIT_CODE=$?

if [[ $EXIT_CODE -eq 0 ]]; then
    echo -e "${GREEN}🎉 All tests passed!${NC}"
    if [[ "$GENERATE_REPORT" == "true" && -f "$REPORT_FILE" ]]; then
        echo -e "${BLUE}📄 Test report saved to: $REPORT_FILE${NC}"
    fi
else
    echo -e "${RED}❌ Some tests failed. Check the output above for details.${NC}"
fi

exit $EXIT_CODE