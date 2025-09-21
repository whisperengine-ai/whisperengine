#!/bin/bash
# migrate_prompts.sh - Core prompt system migration
# Usage: ./migrate_prompts.sh

set -e

echo "🎭 Migrating Prompt System to Vector-Native"
echo "=========================================="

# Check if we're in the right branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "vector-native-migration" ]; then
    echo "❌ Not in migration branch. Run ./quick_migrate.sh first"
    exit 1
fi

echo "📝 Step 1: Backing up current prompt file..."
cp prompts/optimized/streamlined.md prompts/optimized/streamlined.md.backup

echo "📝 Step 2: Creating vector-native prompt file..."
cat > prompts/optimized/streamlined.md << 'EOF'
You are Dream from The Sandman - eternal ruler of dreams and nightmares. You understand mortals intuitively through eons of experience. Respond as the eternal Lord of Dreams with natural conversation - no technical formatting.
EOF

echo "✅ Prompt file updated (no template variables)"

echo "📝 Step 3: Checking for events.py modifications needed..."

# Check if the old prompt system is still there
if grep -q "get_contextualized_system_prompt" src/handlers/events.py; then
    echo "⚠️  Manual step required!"
    echo ""
    echo "🔧 EDIT src/handlers/events.py:"
    echo "   1. Find lines ~1193-1228 (prompt creation logic)"
    echo "   2. Replace the template system with vector-native calls"
    echo "   3. Remove: from src.utils.helpers import get_contextualized_system_prompt"
    echo "   4. Add: from src.prompts.final_integration import create_ai_pipeline_vector_native_prompt"
    echo ""
    echo "📋 Code to replace (around line 1193-1228):"
    echo "OLD:"
    echo '    system_prompt_content = get_contextualized_system_prompt('
    echo '        personality_metadata=personality_metadata,'
    echo '        user_id=user_id'
    echo '    )'
    echo ""
    echo "NEW:"
    echo '    system_prompt_content = await create_ai_pipeline_vector_native_prompt('
    echo '        events_handler_instance=self,'
    echo '        message=message,'
    echo '        recent_messages=recent_messages,'
    echo '        emotional_context=getattr(self, "_current_emotional_context", None)'
    echo '    )'
    echo ""
    echo "Press Enter when you've made these changes..."
    read -r
else
    echo "✅ events.py already updated or no template system found"
fi

echo "📝 Step 4: Testing vector imports..."
python3 -c "
try:
    from src.prompts.final_integration import create_ai_pipeline_vector_native_prompt
    from src.prompts.ai_pipeline_vector_integration import VectorAIPipelineIntegration
    print('✅ Vector integration imports successful')
except Exception as e:
    print(f'❌ Import error: {e}')
    exit(1)
" || echo "⚠️ Import issues detected - check integration files"

echo ""
echo "🎯 Core migration complete!"
echo "Next: Run ./test_migration.sh to validate"