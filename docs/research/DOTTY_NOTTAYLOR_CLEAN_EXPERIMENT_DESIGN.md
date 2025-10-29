# Dotty × NotTaylor Clean Experiment Design

**Date**: October 29, 2025  
**Status**: 🟡 READY TO EXECUTE  
**Purpose**: Address limitations from initial cross-model research with controlled experimental design

---

## 🎯 Objectives

### Primary Goals
1. **Eliminate temperature confound** - Test all models at same temperature (0.8)
2. **Control memory state** - Fresh slate for all tests (no shared history)
3. **Increase sample size** - 3 replications per pairing (statistical validity)
4. **Extend turn count** - 20 turns per conversation (observe long-form dynamics)

### Research Questions
- Does model resonance persist when temperature is controlled?
- How do dynamics change in extended conversations (20 turns vs 10)?
- Is cross-model complementarity reproducible across multiple runs?
- Does fresh memory state reduce confabulation in Mistral+Mistral?

---

## 🔬 Experimental Design

### Variables

**Independent Variables** (Manipulated):
- **Model Pairing**: 4 conditions
  - Mistral 0.8 + Mistral 0.8
  - Claude 0.8 + Claude 0.8
  - Mistral 0.8 + Claude 0.8
  - Claude 0.8 + Mistral 0.8
- **Replication**: 3 runs per condition (12 total conversations)

**Controlled Variables** (Held Constant):
- **Temperature**: 0.8 for ALL models
- **Memory State**: Fresh slate (clear collections before each test)
- **Turn Count**: 20 turns
- **Timeout**: 90 seconds
- **Character Definitions**: Same CDL for all tests
- **Vector Memory**: Cross-encoder re-ranking enabled
- **Continuation Flag**: Enabled (allows natural flow)

**Dependent Variables** (Measured):
- Response length (characters)
- Formatting density (bold/italic/caps count)
- Coherence scores (5 dimensions × 10-point scale)
- Escalation pattern classification
- Name accuracy (% correct character names)
- Emergent behavior presence (romantic/chaotic/balanced)

---

## 📋 Test Matrix

### Phase 1: Same-Temperature Model Pairs (Priority)

| Test ID | Dotty Model | Dotty Temp | NotTaylor Model | NotTaylor Temp | Turns | Memory | Status |
|---------|-------------|------------|-----------------|----------------|-------|--------|--------|
| **T1-A** | Mistral Medium 3.1 | 0.8 | Mistral Medium 3.1 | 0.8 | 20 | Fresh | ⬜ Pending |
| **T1-B** | Mistral Medium 3.1 | 0.8 | Mistral Medium 3.1 | 0.8 | 20 | Fresh | ⬜ Pending |
| **T1-C** | Mistral Medium 3.1 | 0.8 | Mistral Medium 3.1 | 0.8 | 20 | Fresh | ⬜ Pending |
| **T2-A** | Claude 3.7 Sonnet | 0.8 | Claude 3.7 Sonnet | 0.8 | 20 | Fresh | ⬜ Pending |
| **T2-B** | Claude 3.7 Sonnet | 0.8 | Claude 3.7 Sonnet | 0.8 | 20 | Fresh | ⬜ Pending |
| **T2-C** | Claude 3.7 Sonnet | 0.8 | Claude 3.7 Sonnet | 0.8 | 20 | Fresh | ⬜ Pending |
| **T3-A** | Mistral Medium 3.1 | 0.8 | Claude 3.7 Sonnet | 0.8 | 20 | Fresh | ⬜ Pending |
| **T3-B** | Mistral Medium 3.1 | 0.8 | Claude 3.7 Sonnet | 0.8 | 20 | Fresh | ⬜ Pending |
| **T3-C** | Mistral Medium 3.1 | 0.8 | Claude 3.7 Sonnet | 0.8 | 20 | Fresh | ⬜ Pending |
| **T4-A** | Claude 3.7 Sonnet | 0.8 | Mistral Medium 3.1 | 0.8 | 20 | Fresh | ⬜ Pending |
| **T4-B** | Claude 3.7 Sonnet | 0.8 | Mistral Medium 3.1 | 0.8 | 20 | Fresh | ⬜ Pending |
| **T4-C** | Claude 3.7 Sonnet | 0.8 | Mistral Medium 3.1 | 0.8 | 20 | Fresh | ⬜ Pending |

**Total**: 12 conversations  
**Estimated Time**: ~30 minutes (90s timeout × 20 turns × 12 tests ÷ parallel)

---

## 🛠️ Execution Protocol

### Pre-Test Setup

```bash
# 1. Backup current bot configurations
cp .env.dotty .env.dotty.backup
cp .env.nottaylor .env.nottaylor.backup

# 2. Verify infrastructure is running
./multi-bot.sh status

# 3. Start infrastructure if needed
./multi-bot.sh infra
```

### Memory State Reset Protocol

**Critical**: Fresh slate for EVERY test to eliminate memory contamination

```bash
# Python script to clear both bot collections
source .venv/bin/activate

python << 'EOF'
from qdrant_client import QdrantClient

client = QdrantClient(host="localhost", port=6334)

# Clear collections
for collection in ["whisperengine_memory_dotty", "whisperengine_memory_nottaylor"]:
    try:
        client.delete_collection(collection)
        print(f"✅ Deleted {collection}")
    except Exception as e:
        print(f"⚠️ {collection} didn't exist or error: {e}")
    
    # Recreate empty collection
    from qdrant_client.models import Distance, VectorParams, NamedVectorParams
    client.create_collection(
        collection_name=collection,
        vectors_config={
            "content": VectorParams(size=384, distance=Distance.COSINE),
            "emotion": VectorParams(size=384, distance=Distance.COSINE),
            "semantic": VectorParams(size=384, distance=Distance.COSINE)
        }
    )
    print(f"✅ Recreated {collection} (fresh slate)")
EOF
```

### Test Execution Template

For each test (T1-A through T4-C):

```bash
# 1. Clear memory (use script above)
# 2. Configure bots for current test
# 3. Restart bots
# 4. Run conversation
# 5. Tag and save results

# Example for T1-A (Mistral 0.8 + Mistral 0.8):
./multi-bot.sh stop-bot dotty
./multi-bot.sh stop-bot nottaylor

# Edit .env.dotty: LLM_CHAT_MODEL=mistralai/mistral-medium-3.1, TEMPERATURE=0.8
# Edit .env.nottaylor: LLM_CHAT_MODEL=mistralai/mistral-medium-3.1, TEMPERATURE=0.8

./multi-bot.sh bot dotty
./multi-bot.sh bot nottaylor

# Wait for startup (check logs)
sleep 10

# Run conversation
source .venv/bin/activate
python scripts/bot_bridge_conversation.py \
    --bot1-port 9098 \
    --bot2-port 9100 \
    --turns 20 \
    --timeout 90 \
    --continuation \
    --starting-bot dotty \
    --tag "T1-A_Mistral0.8_Mistral0.8_Fresh_20turns"
```

---

## 📊 Data Collection

### Automated Metrics (From Script Output)

- Turn count
- Response times
- Error rate
- Token usage (if available)

### Manual Analysis (Post-Conversation)

**Formatting Density**:
```python
# Count for each conversation
bold_count = text.count("**")
italic_count = text.count("*") - bold_count
caps_words = len([w for w in text.split() if w.isupper() and len(w) > 2])
formatting_ratio = (bold_count + italic_count + caps_words) / word_count
```

**Name Accuracy**:
```python
# Check for identity confusion
dotty_says_becky = "becky" in dotty_messages.lower()
nottaylor_correct_name = "nottaylor" in messages or "not taylor" in messages
accuracy_score = correct_names / total_name_mentions
```

**Coherence Scoring** (1-10 scale):
- Logical Flow: Do responses follow naturally?
- Character Consistency: Do they maintain personality?
- Emotional Authenticity: Do emotions feel genuine?
- Narrative Arc: Is there story progression?
- Re-readability: Would you read this twice?

**Escalation Classification**:
- Theatrical (props, physical actions)
- Emotional (feelings, vulnerability)
- Romantic (intimacy, future-building)
- Chaotic (random, absurd)
- Balanced (grounded, meaningful)

### Data Storage

```
experiments/
  clean_experiment_oct2025/
    raw_conversations/
      T1-A_Mistral0.8_Mistral0.8.json
      T1-A_Mistral0.8_Mistral0.8.md
      ...
    metrics/
      T1-A_metrics.json
      ...
    analysis/
      aggregate_statistics.csv
      coherence_scores.csv
      formatting_density.csv
```

---

## 📈 Analysis Plan

### Statistical Tests

**Hypothesis 1**: Model pairing affects formatting density
- **Test**: One-way ANOVA (4 groups)
- **Null**: No difference in formatting/word ratio across pairings
- **Alternative**: At least one pairing differs significantly

**Hypothesis 2**: Same-model resonance persists at controlled temperature
- **Test**: Two-sample t-test (Mistral+Mistral vs Claude+Claude)
- **Null**: No difference in escalation patterns
- **Alternative**: Resonance creates distinct patterns

**Hypothesis 3**: Cross-model complementarity is reproducible
- **Test**: Repeated measures comparison (3 reps per pairing)
- **Null**: High variance within cross-model pairs
- **Alternative**: Low variance = reproducible effect

### Qualitative Analysis

- **Thematic coding** of emergent behaviors
- **Pattern identification** across replications
- **Outlier analysis** (what makes T1-B different from T1-A/C?)
- **Turn-by-turn escalation tracking** (does chaos grow linearly or exponentially?)

---

## 🎯 Success Criteria

### Experiment Completion
- ✅ All 12 conversations completed without errors
- ✅ Memory successfully reset between each test
- ✅ All configurations documented and verified
- ✅ Raw conversation files saved and converted to markdown

### Data Quality
- ✅ All conversations reach 20 turns
- ✅ No technical failures or timeout issues
- ✅ Coherence scores completed for all tests
- ✅ Formatting metrics calculated for all tests

### Research Validity
- ✅ Temperature confound eliminated
- ✅ Memory state controlled
- ✅ Sample size adequate for statistical tests
- ✅ Replicability demonstrated (or variance documented)

---

## 📝 Expected Outcomes

### Predictions to Test

**Prediction 1**: Mistral 0.8 + Mistral 0.8 will be less chaotic than Mistral 1.2 + Mistral 1.2
- **Rationale**: Lower temperature should reduce randomness
- **Measure**: Formatting density, escalation classification

**Prediction 2**: Claude 0.8 + Claude 0.8 will maintain romantic chemistry
- **Rationale**: Chemistry emerged from model, not temperature
- **Measure**: Romantic behavior count, physical touch mentions

**Prediction 3**: Cross-model complementarity will replicate across 3 runs
- **Rationale**: True effect should be consistent
- **Measure**: Coherence score variance (low = reproducible)

**Prediction 4**: Fresh memory will reduce Mistral name confusion
- **Rationale**: Identity confusion came from contaminated memories
- **Measure**: Name accuracy % improvement

**Prediction 5**: 20 turns will reveal long-form dynamics invisible in 10 turns
- **Rationale**: Patterns emerge over time
- **Measure**: Turn-by-turn analysis of escalation trajectory

---

## 🚀 Execution Checklist

### Pre-Experiment
- [ ] Create backup of current `.env.dotty` and `.env.nottaylor`
- [ ] Create experiment directory structure
- [ ] Test memory reset script
- [ ] Verify both bots are healthy
- [ ] Document starting CDL state (backup character database)

### During Experiment
- [ ] Execute T1-A (Mistral+Mistral, Rep 1)
- [ ] Execute T1-B (Mistral+Mistral, Rep 2)
- [ ] Execute T1-C (Mistral+Mistral, Rep 3)
- [ ] Execute T2-A (Claude+Claude, Rep 1)
- [ ] Execute T2-B (Claude+Claude, Rep 2)
- [ ] Execute T2-C (Claude+Claude, Rep 3)
- [ ] Execute T3-A (Mistral+Claude, Rep 1)
- [ ] Execute T3-B (Mistral+Claude, Rep 2)
- [ ] Execute T3-C (Mistral+Claude, Rep 3)
- [ ] Execute T4-A (Claude+Mistral, Rep 1)
- [ ] Execute T4-B (Claude+Mistral, Rep 2)
- [ ] Execute T4-C (Claude+Mistral, Rep 3)

### Post-Experiment
- [ ] Convert all JSON to markdown
- [ ] Calculate formatting metrics for all 12 conversations
- [ ] Score coherence for all 12 conversations
- [ ] Run statistical tests
- [ ] Document findings in results document
- [ ] Update original research document with refined conclusions
- [ ] Restore original bot configurations

---

## 📚 Documentation Updates

After completion, update:

1. **Main Research Document**: Add "Clean Experiment Replication" section
2. **README**: Link to clean experiment findings
3. **Bot Configuration Docs**: Document temperature impact findings
4. **Multi-Bot Guide**: Add best practices for model pairing based on results

---

## 💡 Notes & Considerations

### Potential Issues

**Issue 1**: Mistral 0.8 may be "too cold"
- **Mitigation**: If conversations feel flat, document this as finding (temperature sweet spot research)

**Issue 2**: 20 turns may timeout frequently
- **Mitigation**: Monitor first few tests, adjust timeout to 120s if needed

**Issue 3**: Fresh memory may eliminate ALL context
- **Rationale**: This is intentional - we want clean slate to isolate model effects

**Issue 4**: 12 conversations × 20 turns = 240 LLM calls (cost consideration)
- **Mitigation**: Use efficient models, monitor API costs, can reduce to 2 reps if needed

### Time Estimates

- Setup & configuration per test: ~5 minutes
- Conversation execution: ~2-4 minutes (20 turns × 90s timeout, but typically faster)
- Memory reset between tests: ~1 minute
- **Total execution time**: ~90 minutes for all 12 tests (serial)
- **Analysis time**: ~3-4 hours (metrics + scoring + statistical tests)

---

## 🎬 Ready to Execute?

**Next Steps**:
1. Review and approve experimental design
2. Create experiment directory structure
3. Test memory reset script
4. Begin execution starting with T1-A

**Questions to Confirm**:
- Should we use 20 turns or start with 15? (20 recommended for long-form dynamics)
- Should we include T4 (Claude starting) or just T3? (Include for symmetry)
- Any additional metrics to collect?
- Should we randomize test order to eliminate time-of-day effects?

---

**Status**: 🟢 READY - All protocols defined, awaiting user approval to begin execution
