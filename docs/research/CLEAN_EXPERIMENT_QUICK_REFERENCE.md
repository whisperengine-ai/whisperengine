# Clean Experiment Automation - Quick Reference

## 🚀 Execute Experiment

### Validate First (Recommended)
```bash
python scripts/validate_clean_experiment.py
```

### Run Experiment
```bash
# Interactive menu (easiest)
./scripts/run_clean_experiment.sh

# Command line options
python scripts/run_clean_experiment.py --all              # All 12 tests (~90 min)
python scripts/run_clean_experiment.py --phase 1          # Phase 1 only (~20 min)
python scripts/run_clean_experiment.py --test T1-A        # Single test (~7 min)
python scripts/run_clean_experiment.py --list             # Show available tests
```

## 📊 Analyze Results

```bash
# Generate markdown report
python scripts/analyze_clean_experiment.py

# Generate CSV + markdown
python scripts/analyze_clean_experiment.py --format both

# Custom output
python scripts/analyze_clean_experiment.py --output my_results.md
```

## 🎯 What Each Script Does

### `validate_clean_experiment.py`
- ✅ Checks infrastructure (Postgres, Qdrant)
- ✅ Verifies bot ports and health
- ✅ Confirms environment files exist
- ✅ Validates Python dependencies
- ✅ Creates required directories

### `run_clean_experiment.py`
**Per Test**:
1. Clears bot memory (fresh slate)
2. Updates .env files (model + temperature)
3. Restarts bots with new config
4. Waits for health checks
5. Runs 20-turn conversation
6. Saves metadata

**Options**:
- `--all` - Run all 12 tests
- `--phase N` - Run phase 1-4 (3 tests each)
- `--test ID` - Run single test (e.g., T1-A)
- `--list` - Show available tests
- `--skip-backup` - Don't backup .env files

### `run_clean_experiment.sh`
- Interactive menu wrapper
- Handles virtual environment activation
- Checks infrastructure before starting
- Provides post-execution next steps

### `analyze_clean_experiment.py`
**Calculates**:
- Formatting density (bold/italic/caps ratio)
- Response lengths (avg/max/min)
- Name accuracy (identity confusion detection)
- Escalation patterns (theatrical/romantic/chaotic)

**Outputs**:
- Markdown report with detailed metrics
- CSV export for statistical analysis
- Console summary by phase

## 📋 Test Matrix

| Test ID | Dotty Model | NotTaylor Model | Phase | Purpose |
|---------|-------------|-----------------|-------|---------|
| T1-A/B/C | Mistral 0.8 | Mistral 0.8 | 1 | Same-model resonance |
| T2-A/B/C | Claude 0.8 | Claude 0.8 | 2 | Same-model (controlled) |
| T3-A/B/C | Mistral 0.8 | Claude 0.8 | 3 | Cross-model complementarity |
| T4-A/B/C | Claude 0.8 | Mistral 0.8 | 4 | Cross-model (reversed) |

## ⏱️ Time Estimates

- **Validation**: 5 seconds
- **Single Test**: 5-7 minutes
- **Phase (3 tests)**: 20-25 minutes  
- **Full Experiment**: ~90 minutes
- **Analysis**: ~5 minutes

## 🗂️ File Locations

```
experiments/clean_experiment_oct2025/
├── README.md                    # Full documentation
├── raw_conversations/           # JSON + MD conversations
│   ├── T1-A_Mistral0.8_Mistral0.8*.json
│   └── ...
├── metrics/                     # Test metadata
│   ├── T1-A_metadata.json
│   └── ...
└── analysis/                    # Analysis outputs
    ├── results_*.md
    └── metrics_*.csv

.env.dotty.backup_TIMESTAMP      # Environment backups
.env.nottaylor.backup_TIMESTAMP
```

## 🔧 Common Commands

### Check Bot Status
```bash
./multi-bot.sh status
curl http://localhost:9098/health  # Dotty
curl http://localhost:9100/health  # NotTaylor
```

### View Bot Logs
```bash
./multi-bot.sh logs dotty-bot
./multi-bot.sh logs nottaylor-bot
```

### Manual Bot Control
```bash
./multi-bot.sh stop-bot dotty
./multi-bot.sh bot dotty
```

### Check Current Configuration
```bash
grep -E "LLM_CHAT_MODEL|TEMPERATURE" .env.dotty .env.nottaylor
```

### View Qdrant Collections
```bash
curl http://localhost:6334/collections | jq .
```

## 📊 Example Workflow

```bash
# 1. Validate everything is ready
python scripts/validate_clean_experiment.py

# 2. Run experiment (choose one)
./scripts/run_clean_experiment.sh                    # Interactive
python scripts/run_clean_experiment.py --phase 1     # Just Phase 1
python scripts/run_clean_experiment.py --all         # Full experiment

# 3. Convert to markdown (if needed)
python scripts/convert_bot_conversations_to_markdown.py

# 4. Analyze results
python scripts/analyze_clean_experiment.py --format both

# 5. Review outputs
cat experiments/clean_experiment_oct2025/analysis/results_*.md
open experiments/clean_experiment_oct2025/analysis/metrics_*.csv
```

## 🐛 Troubleshooting

### "Infrastructure not running"
```bash
./multi-bot.sh infra
```

### "Bot health check failed"
```bash
./multi-bot.sh stop-bot dotty
./multi-bot.sh stop-bot nottaylor
./multi-bot.sh bot dotty
./multi-bot.sh bot nottaylor
```

### "Qdrant connection failed"
```bash
docker ps | grep qdrant
docker restart whisperengine-multi-qdrant-1
```

### "No conversations found"
Check these directories:
- `logs/bot_conversations/`
- `experiments/clean_experiment_oct2025/raw_conversations/`

## ✅ Success Indicators

- All 12 tests complete without errors
- Metadata files created for each test
- Conversations saved (JSON + MD)
- Analysis generates report
- No bot crashes or timeouts

## 🎯 Next Steps After Completion

1. **Review Results**: Check markdown report in `analysis/` directory
2. **Statistical Analysis**: Open CSV in Excel/Python for deeper analysis
3. **Update Research**: Add findings to main research document
4. **Share Findings**: Results ready for peer review or publication

---

**Quick Links**:
- [Full Documentation](experiments/clean_experiment_oct2025/README.md)
- [Experimental Design](docs/research/DOTTY_NOTTAYLOR_CLEAN_EXPERIMENT_DESIGN.md)
- [Original Research](docs/research/CROSS_MODEL_BOT_CONVERSATION_ANALYSIS.md)

**Status**: 🟢 VALIDATED AND READY

Run `python scripts/validate_clean_experiment.py` to confirm!
