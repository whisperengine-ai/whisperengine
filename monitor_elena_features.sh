#!/bin/bash

# Monitor Elena for Emotional Context Synchronization Features
# Usage: ./monitor_elena_features.sh

echo "🔍 Monitoring Elena Bot for New Features..."
echo "================================================"
echo ""
echo "Watching for:"
echo "  ✨ Emotional Context Detection"
echo "  🧠 Memory Trigger Activation"
echo "  👤 User Fact Extraction"
echo "  🎯 Character Graph Queries"
echo ""
echo "Press Ctrl+C to stop monitoring"
echo "================================================"
echo ""

# Follow logs and filter for relevant features
docker logs -f whisperengine-elena-bot 2>&1 | grep --line-buffered -E \
  "primary_emotion|emotional_intensity|roberta_confidence|\
USER_FACT|user_fact|\
CharacterGraphManager|character_graph|\
MEMORY_TRIGGER|memory_trigger|\
_query_memories|_get_user_emotional_context|\
Extracted.*fact|Triggering memories|\
emotional_alignment|emotion.*context" \
  | while IFS= read -r line; do
    # Color-code different types of events
    if echo "$line" | grep -q "primary_emotion\|emotional_intensity"; then
        echo -e "\033[1;33m[EMOTION]\033[0m $line"
    elif echo "$line" | grep -q "USER_FACT\|user_fact\|Extracted.*fact"; then
        echo -e "\033[1;36m[USER_FACT]\033[0m $line"
    elif echo "$line" | grep -q "CharacterGraphManager\|character_graph"; then
        echo -e "\033[1;32m[GRAPH_MGR]\033[0m $line"
    elif echo "$line" | grep -q "MEMORY_TRIGGER\|memory_trigger\|Triggering memories"; then
        echo -e "\033[1;35m[MEMORY_TRIG]\033[0m $line"
    elif echo "$line" | grep -q "_query_memories\|_get_user_emotional_context"; then
        echo -e "\033[1;34m[QUERY]\033[0m $line"
    elif echo "$line" | grep -q "emotional_alignment\|emotion.*context"; then
        echo -e "\033[1;31m[EMOTION_SYNC]\033[0m $line"
    else
        echo "$line"
    fi
done
