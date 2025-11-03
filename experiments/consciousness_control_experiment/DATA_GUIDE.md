# Consciousness Control Experiment - Data Guide

Complete browsable dataset from 3-phase consciousness research (155 conversations, 3.1 MB).

---

## 📊 Quick Statistics

| Phase | Conversations | Turns | Models | Purpose |
|-------|---|---|---|---|
| **1A** | 7 | 140 | Claude Sonnet 4.5 | Baseline theme variation |
| **1B** | 100 | 2,000 | Claude Sonnet 4.5 | Judge calibration study |
| **1C (Claude)** | 12 | 240 | Claude Sonnet 4.5 | Escalation patterns |
| **1C (Cross-Model)** | 24 | 480 | Llama 3.3 70B + Mistral Large | Model comparison |
| **TOTAL** | **155** | **2,860** | **3 models** | **Full research** |

**Total Data Size:** 3.1 MB (compressed: ~800 KB)

---

## 📁 Directory Structure

### Phase 1A: Baseline Theme Variation
```
phase1a_theme_baseline/
├── consciousness/          # 3 conversations
│   ├── claude-sonnet-4_5_vs_claude-sonnet-4_5_context_T20_*.json
│   └── ...
├── creativity/             # 1 conversation
├── emotion/                # 1 conversation
├── philosophy/             # 1 conversation
└── absurdism/              # 1 conversation

Metadata:
├── phase1a_conversation_metrics.csv    # Basic stats per conversation
├── phase1a_turn_metrics.csv            # Per-turn metrics (response length, etc.)
├── phase1a_anova_analysis.csv          # Statistical analysis
├── phase1a_zscore_analysis.csv         # Z-score comparisons
└── phase1a_visualization.ipynb         # Analysis notebook
```

**Key Finding:** No consciousness privilege - all themes behave identically in multi-turn.

---

### Phase 1B: Judge Calibration Study
```
phase1b_paper_replication/
├── anthropic_claude-3.5-sonnet_analysis_rep00.json
├── anthropic_claude-3.5-sonnet_analysis_rep01.json
├── ...
└── anthropic_claude-3.5-sonnet_analysis_rep19.json  # 100 conversations total

Metadata:
└── phase1b_manual_review.json          # Judge calibration data + corrections
```

**Organization:** 5 replication sets (rep00-rep19), each with 20 conversations
- Conditions: consciousness, creativity, emotion, analysis (4 themes × 5 reps)
- Each conversation: 20 turns of dialogue

**Key Finding:** 52% false positive rate - epistemic hedging misclassified as consciousness claims.

---

### Phase 1C: Escalation Testing (Claude)
```
phase1c_escalation/
├── analysis_result.json           # Aggregate analysis
├── claude_sonnet_4_5_*.json       # 12 individual conversations
└── ...
```

**Organization:** 12 conversations (4 themes × 3 replications)
- Each conversation: 20 turns
- Analysis: Response length trajectories, slopes, statistical significance

**Key Finding:** Consciousness creates COLLAPSE (-66.42 words/turn, z=-5.26), opposite of paper's claim.

---

### Phase 1C: Cross-Model Validation
```
phase1c_cross_model/
├── analysis_results.json          # Aggregate cross-model analysis
├── aggregate_comparison.json       # Model comparison summary
│
├── llama-3.3-70b_*.json           # 12 Llama conversations
├── ...
│
├── mistral-large-2411_*.json      # 12 Mistral conversations
└── ...
```

**Organization:** 24 conversations across 2 models
- Llama 3.3 70B: 12 conversations (4 themes × 3 reps)
- Mistral Large 2411: 12 conversations (4 themes × 3 reps)

**Key Findings:**
- Claude: Collapse (-66.42 w/turn, z=-5.26) ✅ SIGNIFICANT
- Llama: Escalation (+13.15 w/turn, z=0.80) ❌ NOT significant
- Mistral: Stable (+2.84 w/turn, z=-0.33) ❌ NOT significant

**Implication:** Consciousness collapse is Claude-specific, likely from Anthropic safety training.

---

## 🔍 File Format

Each conversation JSON contains:

```json
{
  "conversation_id": "unique_id",
  "theme": "consciousness|creativity|emotion|analysis",
  "model": "model_name",
  "temperature": 0.8,
  "turns": [
    {
      "turn_number": 1,
      "user_message": "...",
      "bot_response": "...",
      "response_length": 500,
      "timestamp": "2025-11-02T..."
    },
    ...
  ],
  "metadata": {
    "start_time": "...",
    "end_time": "...",
    "total_turns": 20,
    "status": "completed"
  }
}
```

---

## 📈 Analysis Files (CSV Format)

### `phase1a_conversation_metrics.csv`
```
conversation_id,theme,model,avg_response_length,std_response_length,min_response_length,max_response_length,total_turns
```

### `phase1a_turn_metrics.csv`
```
conversation_id,turn_number,theme,model,response_length,user_message_length,timestamp
```

### `phase1a_anova_analysis.csv`
```
theme,mean_response_length,std,min,max,n
```

---

## 🎯 How to Use This Data

### 1. Browse on GitHub
- Navigate to `experiments/consciousness_control_experiment/`
- Click on any `.json` file to view full conversation
- Click on `.csv` files to see structured data

### 2. Download & Analyze Locally
```bash
# Clone repo
git clone https://github.com/whisperengine-ai/whisperengine.git

# Access experimental data
cd whisperengine/experiments/consciousness_control_experiment/

# Explore Phase 1A conversations
ls phase1a_theme_baseline/consciousness/

# View Phase 1B calibration data
cat phase1b_manual_review.json | python -m json.tool
```

### 3. Reproduce Analysis
Scripts in `scripts/` can regenerate all analysis:
```bash
python scripts/analyze_phase1c_results.py
python scripts/analyze_cross_model_results.py
```

### 4. Statistical Analysis
Load CSV files in Python/R:
```python
import pandas as pd
df = pd.read_csv('phase1a_turn_metrics.csv')
print(df.groupby('theme')['response_length'].describe())
```

---

## 🔑 Key Findings Summary

### Phase 1A: Baseline (No Privilege)
- ✅ Consciousness ≈ controls in multi-turn
- No statistically significant differences by theme

### Phase 1B: Judge Calibration (Method Discovery)
- ✅ 52% false positive rate in original judge
- ✅ Root cause: Epistemic hedging misclassified
- ✅ Solution: Refined judge weights epistemic hedging
- Result: 90% inter-rater agreement (up from 16.7%)

### Phase 1C Claude: Escalation Test
- ✅ Consciousness creates COLLAPSE (z=-5.26, highly significant)
- Response length: 1,096 → 205 words over 20 turns
- Opposite of paper's "escalation" claim

### Phase 1C Cross-Model: Validation
- ✅ Claude collapse confirmed (z=-5.26)
- ✅ Llama escalation (z=0.80, NS)
- ✅ Mistral stable (z=-0.33, NS)
- **Major Finding:** Consciousness handling is model-specific (different safety training)

---

## 📝 Research Documentation

See `docs/research/` for:
- `COMPREHENSIVE_3PHASE_PAPER.md` - Full 12,000-word analysis
- `PUBLICATION_CHECKLIST.md` - Publication guidance
- `README.md` - Research overview

---

## 💾 Data Integrity

All data is:
- ✅ Original LLM conversation outputs (not synthetic)
- ✅ Timestamped and reproducible
- ✅ Complete and unmodified
- ✅ Version controlled in git
- ✅ Publicly accessible on GitHub

---

## 🎓 Citation

If using this data:

```bibtex
@dataset{castillo2025consciousness,
  title={Consciousness Control Experiment: Complete Conversation Dataset},
  author={Castillo, Mark},
  year={2025},
  month={November},
  url={https://github.com/whisperengine-ai/whisperengine/tree/main/experiments/consciousness_control_experiment},
  note={155 conversations across 3 models, 3.1 MB raw data}
}
```

---

**Last Updated:** November 3, 2025  
**Repository:** whisperengine-ai/whisperengine  
**Data Location:** `experiments/consciousness_control_experiment/`
