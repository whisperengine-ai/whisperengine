#!/bin/bash

# Vector Classification Testing Script
# Generates synthetic conversations specifically designed to test multi-vector intelligence classification

set -e

BOT_NAME="elena"
BOT_PORT="9091"
NUM_CONVERSATIONS=5

echo "🎯 Vector Classification Testing with Synthetic Conversations"
echo "=============================================================="
echo ""
echo "Bot: $BOT_NAME"
echo "Port: $BOT_PORT"
echo "Conversations per type: $NUM_CONVERSATIONS"
echo ""

# Activate Python environment
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

# Run synthetic conversation generator with vector classification focus
echo "🚀 Starting synthetic conversation generation..."
echo ""

python3 synthetic_conversation_generator.py \
    --bot $BOT_NAME \
    --port $BOT_PORT \
    --conversation-types \
        emotional_query_test \
        semantic_query_test \
        content_query_test \
        temporal_query_test \
        hybrid_query_test \
        multi_vector_fusion_test \
        classification_accuracy_test \
    --num-conversations $NUM_CONVERSATIONS \
    --delay-between-messages 2 \
    --save-results

echo ""
echo "✅ Synthetic conversation generation complete!"
echo ""
echo "📊 Next Steps:"
echo "=============="
echo ""
echo "1. Check classification logs:"
echo "   docker logs elena-bot | grep 'MULTI-VECTOR\\|CLASSIFICATION\\|📊'"
echo ""
echo "2. View Grafana dashboard:"
echo "   open http://localhost:3000/d/ff0prb5syvy0wc/vector-classification-intelligence"
echo ""
echo "3. Query InfluxDB data:"
echo "   docker exec -it whisperengine-influxdb influx"
echo "   > use whisperengine"
echo "   > SELECT * FROM vector_classification ORDER BY time DESC LIMIT 20"
echo ""
echo "4. Analyze results:"
echo "   cat synthetic_conversations_*.json | jq '.conversations[] | {type, expected_vector, messages_count}'"
echo ""
echo "Expected Classification Distribution:"
echo "- Emotional queries: ~25% (emotion vector)"
echo "- Semantic queries: ~20% (semantic vector)"
echo "- Content queries: ~25% (content vector)"
echo "- Temporal queries: ~15% (temporal vector)"
echo "- Hybrid queries: ~10% (hybrid fusion)"
echo "- Multi-vector fusion: ~5% (all vectors)"
echo ""
