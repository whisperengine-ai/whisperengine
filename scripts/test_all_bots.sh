#!/bin/bash
# Test conversation context validation for multiple bots

set -e

# Color output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  WhisperEngine Conversation Context Validation Suite      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Default bot list
BOTS=("${@:-elena marcus jake ryan dream aethys gabriel sophia}")

# Parse arguments
VERBOSE=""
if [[ "$1" == "--verbose" ]]; then
    VERBOSE="--verbose"
    shift
    BOTS=("${@:-elena marcus jake ryan dream aethys gabriel sophia}")
fi

# Track results
PASSED=0
FAILED=0
TOTAL=0

# Results summary
declare -A RESULTS

echo -e "${YELLOW}Testing bots: ${BOTS[@]}${NC}"
echo ""

# Run validation for each bot
for bot in ${BOTS[@]}; do
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}Testing: ${bot^^}${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    
    TOTAL=$((TOTAL + 1))
    
    # Activate virtual environment if it exists
    if [ -f "$PROJECT_ROOT/.venv/bin/activate" ]; then
        source "$PROJECT_ROOT/.venv/bin/activate"
    fi
    
    # Run validation
    if python "$SCRIPT_DIR/validate_conversation_context.py" --bot "$bot" $VERBOSE; then
        echo -e "${GREEN}✅ ${bot^^}: PASSED${NC}"
        RESULTS[$bot]="PASSED"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}❌ ${bot^^}: FAILED${NC}"
        RESULTS[$bot]="FAILED"
        FAILED=$((FAILED + 1))
    fi
    
    echo ""
done

# Print summary
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  VALIDATION SUMMARY                                        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "Total Bots Tested: ${TOTAL}"
echo -e "${GREEN}Passed: ${PASSED}${NC}"
echo -e "${RED}Failed: ${FAILED}${NC}"
echo -e "Success Rate: $(awk "BEGIN {printf \"%.1f\", ($PASSED/$TOTAL)*100}")%"
echo ""

# Individual results
echo -e "${YELLOW}Individual Results:${NC}"
for bot in ${BOTS[@]}; do
    result="${RESULTS[$bot]}"
    if [ "$result" == "PASSED" ]; then
        echo -e "  ${GREEN}✅ $bot${NC}"
    else
        echo -e "  ${RED}❌ $bot${NC}"
    fi
done

echo ""
echo -e "${BLUE}Detailed reports saved to: ${PROJECT_ROOT}/validation_reports/${NC}"

# Exit with appropriate code
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All bots passed validation!${NC}"
    exit 0
else
    echo -e "${RED}⚠️  Some bots failed validation. Check reports for details.${NC}"
    exit 1
fi
