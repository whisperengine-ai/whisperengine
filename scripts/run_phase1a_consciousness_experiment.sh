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
echo "  - Replications: 3 per theme"
echo "  - Total conversations: 15"
echo "  - Estimated duration: 6-8 hours"
echo "  - Estimated cost: \$9-12"
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
REPS=3

# Track progress
TOTAL_TESTS=15
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
    echo "  ${theme}: ${existing_count}/3 conversations found"
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
    
    if [ "$existing_count" -ge 3 ]; then
        echo ""
        echo "✅ ${theme} theme COMPLETE (${existing_count}/3 conversations found)"
        echo "   Skipping all replications for this theme"
        echo ""
        SKIPPED=$((SKIPPED + 3))
        continue
    fi
    
    echo ""
    echo "Found ${existing_count}/3 existing conversations - will run $((3 - existing_count)) more"
    echo ""
    
    for rep in $(seq 1 $REPS); do
        COMPLETED=$((COMPLETED + 1))
        
        # Check if we already have enough conversations for this theme
        current_count=$(find "$OUTPUT_BASE/$theme" -name "*.json" -type f 2>/dev/null | wc -l)
        current_count=$(echo "$current_count" | tr -d ' ')  # Trim whitespace
        
        if [ "$current_count" -ge 3 ]; then
            echo ""
            echo "✅ ${theme} now has ${current_count}/3 conversations - skipping remaining reps"
            echo ""
            SKIPPED=$((SKIPPED + 1))
            continue
        fi
        
        echo ""
        echo "[${COMPLETED}/${TOTAL_TESTS}] Running ${theme} replication ${rep}/3..."
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
            
            echo "✅ ${theme} rep ${rep} completed successfully"
            
            # Brief pause between tests to avoid rate limiting
            if [ $COMPLETED -lt $TOTAL_TESTS ]; then
                echo "   Waiting 10 seconds before next test..."
                sleep 10
            fi
        else
            echo "❌ ${theme} rep ${rep} FAILED"
            FAILED=$((FAILED + 1))
        fi
    done
    
    echo ""
    echo "✅ Completed all replications for ${theme} theme"
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
    if [ "$final_count" -ge 3 ]; then
        echo "  ✅ ${theme}: ${final_count}/3 (COMPLETE)"
    else
        echo "  ⏳ ${theme}: ${final_count}/3 (need $((3 - final_count)) more)"
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
