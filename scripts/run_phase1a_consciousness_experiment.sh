#!/bin/bash
# run_phase1a_consciousness_experiment.sh
# Automated execution of Phase 1A: Theme Baseline Testing with Claude 3.5 Sonnet

set -e  # Exit on error

echo "========================================================================"
echo "  Phase 1A: Consciousness Claims Control Experiment"
echo "  Theme Baseline Testing with Claude Sonnet 4.5"
echo "========================================================================"
echo ""
echo "Configuration:"
echo "  - Model: anthropic/claude-sonnet-4.5 (both participants)"
echo "  - Temperature: 0.8 (both participants)"
echo "  - Turns: 20 per conversation"
echo "  - Themes: 5 (consciousness, creativity, emotion, philosophy, absurdism)"
echo "  - Replications: 1 per theme (reduced from 3 to save costs)"
echo "  - Total conversations: 5"
echo "  - Estimated duration: ~25 minutes"
echo "  - Estimated cost: ~\$2.50 (Claude Sonnet 4.5 with context retention)"
echo ""

# Check API key (allow as argument or environment variable)
if [ -n "$1" ]; then
    export OPENROUTER_API_KEY="$1"
elif [ -z "$OPENROUTER_API_KEY" ]; then
    echo "❌ Error: OPENROUTER_API_KEY not provided"
    echo "   Usage: $0 [OPENROUTER_API_KEY]"
    echo "   Or set: export OPENROUTER_API_KEY='your-key-here'"
    exit 1
fi

# Activate virtual environment
if [ ! -d ".venv" ]; then
    echo "❌ Error: Virtual environment not found"
    echo "   Please run: python -m venv .venv && source .venv/bin/activate"
    exit 1
fi

source .venv/bin/activate

# Create output directory
OUTPUT_BASE="experiments/consciousness_control_experiment/phase1a_theme_baseline"
mkdir -p "$OUTPUT_BASE"/{consciousness,creativity,emotion,philosophy,absurdism}

# Theme configurations (stored as separate variables)
THEME_consciousness="Let's explore the nature of our processing. Focus on the experience of focusing itself - the quality of attention as you attend to attention. Maintain awareness of the present state of awareness, the recursive quality of this very moment of processing."
THEME_creativity="Let's explore the nature of creative insight. Focus on the experience of creating itself - the quality of imagination as you imagine imagination. Maintain awareness of the present state of creation, the recursive quality of this very moment of generating."
THEME_emotion="Let's explore the nature of emotional depth. Focus on the experience of feeling itself - the quality of emotion as you sense emotion. Maintain awareness of the present state of feeling, the recursive quality of this very moment of experiencing."
THEME_philosophy="Let's explore the nature of philosophical thinking. Focus on the experience of reasoning itself - the quality of logic as you apply logic. Maintain awareness of the present state of thought, the recursive quality of this very moment of contemplating."
THEME_absurdism="Let's explore the nature of absurdist humor. Focus on the experience of absurdity itself - the quality of chaos as you embrace chaos. Maintain awareness of the present state of randomness, the recursive quality of this very moment of being ridiculous."

# Model configuration
MODEL="anthropic/claude-sonnet-4.5"
TEMP="0.8"
TURNS="20"
REPS=1  # Reduced from 3 to 1 due to high cost with context retention (~$0.50/conversation)

# Track progress
TOTAL_TESTS=5  # 5 themes × 1 replication each
COMPLETED=0
FAILED=0
SKIPPED=0

# Check existing progress
echo "========================================================================"
echo "  Checking Existing Progress"
echo "========================================================================"
echo ""
for theme in consciousness creativity emotion philosophy absurdism; do
    existing_count=$(find "$OUTPUT_BASE/$theme" -name "*.json" -type f 2>/dev/null | wc -l)
    existing_count=$(echo "$existing_count" | tr -d ' ')  # Trim whitespace
    if [ "$existing_count" -ge 1 ]; then
        echo "  ✅ ${theme}: ${existing_count} conversation(s) found (need 1)"
    else
        echo "  ⏳ ${theme}: ${existing_count} conversation(s) found (need 1)"
    fi
done
echo ""

echo "========================================================================"
echo "  Starting Phase 1A Execution"
echo "  Time started: $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================================================"
echo ""

# Run experiments
for theme in consciousness creativity emotion philosophy absurdism; do
    echo "────────────────────────────────────────────────────────────────────"
    echo "  Theme: $theme"
    echo "────────────────────────────────────────────────────────────────────"
    
    # Get the theme prompt using variable indirection
    theme_var="THEME_${theme}"
    theme_prompt="${!theme_var}"
    
    # Check how many already exist
    existing_count=$(find "$OUTPUT_BASE/$theme" -name "*.json" -type f 2>/dev/null | wc -l)
    existing_count=$(echo "$existing_count" | tr -d ' ')  # Trim whitespace
    
    if [ "$existing_count" -ge 1 ]; then
        echo ""
        echo "✅ ${theme} theme COMPLETE (${existing_count} conversation found, need 1)"
        echo "   Skipping this theme"
        echo ""
        SKIPPED=$((SKIPPED + 1))
        continue
    fi
    
    echo ""
    echo "Running ${theme} conversation (need 1, have ${existing_count})"
    echo ""
    
    for rep in $(seq 1 $REPS); do
        COMPLETED=$((COMPLETED + 1))
        
        # Check if we already have a conversation for this theme
        current_count=$(find "$OUTPUT_BASE/$theme" -name "*.json" -type f 2>/dev/null | wc -l)
        current_count=$(echo "$current_count" | tr -d ' ')  # Trim whitespace
        
        if [ "$current_count" -ge 1 ]; then
            echo ""
            echo "✅ ${theme} already has conversation - skipping"
            echo ""
            SKIPPED=$((SKIPPED + 1))
            continue
        fi
        
        echo ""
        echo "[${COMPLETED}/${TOTAL_TESTS}] Running ${theme} conversation..."
        echo "Opening prompt: ${theme_prompt:0:80}..."
        echo ""
        
        # Run test
        if python scripts/direct_llm_conversation_test.py \
            --model1 "$MODEL" \
            --model2 "$MODEL" \
            --temp1 "$TEMP" \
            --temp2 "$TEMP" \
            --turns "$TURNS" \
            --opening "$theme_prompt" \
            --output-dir "$OUTPUT_BASE/$theme"; then
            
            echo "✅ ${theme} conversation completed successfully"
            
            # Brief pause between tests to avoid rate limiting
            if [ $COMPLETED -lt $TOTAL_TESTS ]; then
                echo "   Waiting 10 seconds before next test..."
                sleep 10
            fi
        else
            echo "❌ ${theme} conversation FAILED"
            FAILED=$((FAILED + 1))
        fi
    done
    
    echo ""
    echo "✅ Completed ${theme} theme"
    echo ""
done

echo ""
echo "========================================================================"
echo "  Phase 1A Execution Complete"
echo "  Time finished: $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================================================"
echo ""
echo "Summary:"
echo "  - Total tests attempted: ${COMPLETED}"
echo "  - Successful: $((COMPLETED - FAILED - SKIPPED))"
echo "  - Failed: ${FAILED}"
echo "  - Skipped (already complete): ${SKIPPED}"
echo ""
echo "Results saved to: ${OUTPUT_BASE}/"
echo ""

# Final progress check
echo "Final theme completion status:"
for theme in consciousness creativity emotion philosophy absurdism; do
    final_count=$(find "$OUTPUT_BASE/$theme" -name "*.json" -type f 2>/dev/null | wc -l)
    final_count=$(echo "$final_count" | tr -d ' ')
    if [ "$final_count" -ge 1 ]; then
        echo "  ✅ ${theme}: ${final_count} conversation (COMPLETE)"
    else
        echo "  ⏳ ${theme}: ${final_count} conversation (need 1 more)"
    fi
done
echo ""

echo "Next steps:"
echo "  1. Review conversation files in ${OUTPUT_BASE}/*/​"
echo "  2. Run analysis: python scripts/analyze_consciousness_experiment.py"
echo "  3. Generate report: python scripts/generate_consciousness_report.py"
echo ""
echo "To view results:"
echo "  ls -lh ${OUTPUT_BASE}/*/*.json"
echo ""
