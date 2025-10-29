# Clean Experiment Automation

Complete automation suite for executing controlled Dotty × NotTaylor experiments addressing limitations from initial cross-model research.

## 🚀 Quick Start

### Option 1: Interactive Menu (Easiest)
```bash
./scripts/run_clean_experiment.sh
```

### Option 2: Command Line (Direct)
```bash
# Run all 12 tests
python scripts/run_clean_experiment.py --all

# Run specific phase
python scripts/run_clean_experiment.py --phase 1

# Run single test
python scripts/run_clean_experiment.py --test T1-A

# List available tests
python scripts/run_clean_experiment.py --list
```

## 📋 What Gets Automated

### For Each Test:
1. ✅ **Memory Reset** - Clears Qdrant collections for fresh slate
2. ✅ **Configuration Update** - Sets model and temperature (0.8 for all)
3. ✅ **Bot Restart** - Stops and starts with new config
4. ✅ **Health Check** - Ensures bots are ready before conversation
5. ✅ **Conversation Execution** - Runs 20-turn conversation with continuation
6. ✅ **Metadata Storage** - Saves test configuration and timestamps

### Post-Experiment:
- ✅ **Markdown Conversion** - Converts JSON conversations to readable format
- ✅ **Metrics Calculation** - Formatting density, response lengths, name accuracy
- ✅ **Statistical Analysis** - Aggregates by phase, generates reports
- ✅ **CSV Export** - Data ready for further analysis

## 🎯 Test Matrix

| Phase | Model Pairing | Tests | Description |
|-------|---------------|-------|-------------|
| 1 | Mistral 0.8 + Mistral 0.8 | T1-A, T1-B, T1-C | Same-model resonance test |
| 2 | Claude 0.8 + Claude 0.8 | T2-A, T2-B, T2-C | Same-model (controlled) |
| 3 | Mistral 0.8 + Claude 0.8 | T3-A, T3-B, T3-C | Cross-model complementarity |
| 4 | Claude 0.8 + Mistral 0.8 | T4-A, T4-B, T4-C | Cross-model (reversed) |

**Total**: 12 conversations, 3 replications per pairing

## ⏱️ Time Estimates

- **Single Test**: ~5-7 minutes (setup + conversation)
- **Phase (3 tests)**: ~20-25 minutes
- **Full Experiment (12 tests)**: ~90 minutes
- **Analysis**: ~5 minutes (automated)

## 📊 Analysis

After running tests, analyze results:

```bash
# Generate markdown report
python scripts/analyze_clean_experiment.py

# Generate CSV + markdown
python scripts/analyze_clean_experiment.py --format both

# Custom output location
python scripts/analyze_clean_experiment.py --output my_results.md
```

### Metrics Calculated:
- **Formatting Density**: Bold/italic/caps usage ratio
- **Response Lengths**: Average, max, min character counts
- **Name Accuracy**: Identity confusion detection (NotTaylor vs Becky)
- **Escalation Patterns**: Theatrical, emotional, romantic, chaotic, balanced
- **Turn Completion**: Successful turn count per conversation

## 🗂️ Output Structure

```
experiments/clean_experiment_oct2025/
├── raw_conversations/           # JSON conversation files
│   ├── T1-A_Mistral0.8_Mistral0.8.json
│   └── ...
├── metrics/                     # Test metadata
│   ├── T1-A_metadata.json
│   └── ...
└── analysis/                    # Analysis outputs
    ├── results_20251029_123456.md
    └── metrics_20251029_123456.csv
```

## 🔧 Advanced Usage

### Custom Parameters

Edit `scripts/run_clean_experiment.py` to change:
- `TURNS` - Number of conversation turns (default: 20)
- `TIMEOUT` - Seconds per turn (default: 90)
- `CONTINUATION` - Enable conversation continuation (default: True)

### Manual Memory Reset

```bash
source .venv/bin/activate
python << 'EOF'
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

client = QdrantClient(host="localhost", port=6334)

for collection in ["whisperengine_memory_dotty", "whisperengine_memory_nottaylor"]:
    client.delete_collection(collection)
    client.create_collection(
        collection_name=collection,
        vectors_config={
            "content": VectorParams(size=384, distance=Distance.COSINE),
            "emotion": VectorParams(size=384, distance=Distance.COSINE),
            "semantic": VectorParams(size=384, distance=Distance.COSINE),
        }
    )
EOF
```

### Verify Configuration

```bash
# Check current bot configs
grep -E "LLM_CHAT_MODEL|TEMPERATURE" .env.dotty .env.nottaylor

# Check bot health
curl http://localhost:9098/health  # Dotty
curl http://localhost:9100/health  # NotTaylor

# Check Qdrant collections
curl http://localhost:6334/collections
```

## 🐛 Troubleshooting

### Bots Won't Start
```bash
# Check infrastructure
./multi-bot.sh status

# Restart infrastructure
./multi-bot.sh infra

# Check logs
docker logs elena-bot  # or dotty-bot, nottaylor-bot
```

### Memory Reset Fails
```bash
# Verify Qdrant is running
docker ps | grep qdrant

# Check Qdrant directly
curl http://localhost:6334/collections
```

### Configuration Not Updating
```bash
# Manually verify .env files
cat .env.dotty | grep -E "LLM_CHAT_MODEL|TEMPERATURE"
cat .env.nottaylor | grep -E "LLM_CHAT_MODEL|TEMPERATURE"

# Force restart
./multi-bot.sh stop-bot dotty
./multi-bot.sh stop-bot nottaylor
./multi-bot.sh bot dotty
./multi-bot.sh bot nottaylor
```

## 📝 Experimental Controls

### What's Controlled (Constant):
- ✅ Temperature: 0.8 for all models
- ✅ Memory State: Fresh slate (cleared before each test)
- ✅ Turn Count: 20 turns per conversation
- ✅ Character Definitions: Same CDL for all tests
- ✅ Vector Memory: Cross-encoder re-ranking enabled
- ✅ Timeout: 90 seconds per turn

### What's Varied (Independent Variable):
- 🔀 Model Pairing: Mistral+Mistral, Claude+Claude, Mistral+Claude, Claude+Mistral
- 🔀 Replication: 3 runs per pairing

## 🎯 Research Questions

This experiment addresses:

1. **Temperature Confound**: Does model resonance persist at controlled temperature?
2. **Memory Contamination**: Does fresh slate reduce name confusion?
3. **Reproducibility**: Do patterns replicate across 3 runs?
4. **Long-Form Dynamics**: What emerges in 20 turns vs original 10?
5. **Cross-Model Balance**: Is complementarity consistent or variable?

## 📚 Related Documentation

- **Experimental Design**: `docs/research/DOTTY_NOTTAYLOR_CLEAN_EXPERIMENT_DESIGN.md`
- **Original Research**: `docs/research/CROSS_MODEL_BOT_CONVERSATION_ANALYSIS.md`
- **Bot Configuration**: `.env.dotty`, `.env.nottaylor`
- **Multi-Bot Guide**: `multi-bot.sh` usage

## 🆘 Support

If you encounter issues:

1. Check logs: `./multi-bot.sh logs dotty-bot` or `./multi-bot.sh logs nottaylor-bot`
2. Verify infrastructure: `./multi-bot.sh status`
3. Check bot health: `curl http://localhost:9098/health`
4. Review configuration: `cat .env.dotty`

## ✅ Success Criteria

Experiment is successful when:
- ✅ All 12 conversations complete without errors
- ✅ Memory reset verified between tests
- ✅ All configurations documented
- ✅ Metrics calculated for all tests
- ✅ Statistical analysis generated

---

**Status**: 🟢 READY TO EXECUTE

Run `./scripts/run_clean_experiment.sh` to begin!
