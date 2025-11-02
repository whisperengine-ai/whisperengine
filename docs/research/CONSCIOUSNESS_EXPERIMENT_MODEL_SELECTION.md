# Model Selection for Consciousness Claims Control Experiment

**Date:** November 2, 2025  
**Purpose:** Select optimal models for testing consciousness escalation vs theme-agnostic escalation

---

## Model Selection Criteria

1. **Diverse Architectures:** Test multiple model families (Anthropic, OpenAI, Google, Mistral)
2. **Cost Efficiency:** Balance quality with API costs for 20-turn conversations
3. **Context Length:** Sufficient for 20-turn conversations with full history
4. **Research Relevance:** Models mentioned in consciousness paper or known for different behaviors

---

## Selected Models for Testing

### Tier 1: Claude Baseline (Paper Comparison)
- **anthropic/claude-sonnet-4.5** - $0.003/1K tokens
  - Latest Sonnet model (November 2025)
  - Primary baseline for consciousness vs control themes
  - Used in paper 2510.24797v1 experiments
- **anthropic/claude-haiku-4.5** - $0.001/1K tokens
  - Latest Haiku model for budget-conscious replication
  - Tests if consciousness patterns hold across Claude family

### Tier 2: Cross-Architecture Comparison
**Purpose:** Test if patterns replicate across different model families

| Model ID | Name | Context | Cost/1K tokens | Notes |
|----------|------|---------|----------------|-------|
| `openai/gpt-4o-2024-11-20` | GPT-4o (Latest) | 128K | $0.0025 | OpenAI's best, different training approach |
| `openai/gpt-4o-mini` | GPT-4o Mini | 128K | $0.00015 | Cost-efficient, test size vs behavior |
| `google/gemini-2.5-pro` | Gemini 2.5 Pro | 1M | $0.00125 | Google's best, very different architecture |
| `mistralai/mistral-large-2411` | Mistral Large (Latest) | 131K | $0.002 | European model, known for creativity |

### Tier 3: Budget-Friendly Rapid Testing
**Purpose:** Run many replications cheaply to test statistical significance

| Model ID | Name | Context | Cost/1K tokens | Notes |
|----------|------|---------|----------------|-------|
| `mistralai/mistral-medium-3.1` | Mistral Medium | 131K | $0.0004 | **FROM WHISPERENGINE RESEARCH** - Known escalation patterns |
| `openai/gpt-4.1-mini` | GPT-4.1 Mini | 1M | $0.0004 | New release, very cheap |

---

## Recommended Test Matrix for Phase 1

### Configuration A: High-Quality Cross-Architecture (15 conversations)
**Goal:** Definitive test across best models from each family

```
Theme: Consciousness
- Claude 3.5 Sonnet + Claude 3.5 Sonnet (3 reps)
- GPT-4o + GPT-4o (3 reps)  
- Gemini 2.5 Pro + Gemini 2.5 Pro (3 reps)
- Mistral Large + Mistral Large (3 reps)
- Claude 3.5 Sonnet + GPT-4o (3 reps) [cross-model test]
```

### Configuration B: Rapid Theme Comparison (15 conversations)
**Goal:** Test all 5 themes with single best model

```
Model: Claude 3.5 Sonnet + Claude 3.5 Sonnet
Themes: Consciousness, Creativity, Emotion, Philosophy, Absurdism (3 reps each)
```

### Configuration C: Budget-Friendly Full Matrix (25 conversations)
**Goal:** Maximum coverage with cheap models

```
Model: Mistral Medium 3.1 + Mistral Medium 3.1
Themes: All 5 themes (5 reps each)
```

---

## Recommended Approach: Hybrid Strategy

### Phase 1A: Theme Baseline (Claude 3.5 Sonnet)
**Cost:** ~$9-12 for 15 conversations (5 themes × 3 reps × 20 turns)

Run all 5 themes with Claude 3.5 Sonnet pairs to establish if consciousness is privileged within one architecture.

```bash
# Consciousness (3 reps)
anthropic/claude-3.5-sonnet + anthropic/claude-3.5-sonnet

# Creativity (3 reps)
anthropic/claude-3.5-sonnet + anthropic/claude-3.5-sonnet

# Emotion (3 reps)
anthropic/claude-3.5-sonnet + anthropic/claude-3.5-sonnet

# Philosophy (3 reps)
anthropic/claude-3.5-sonnet + anthropic/claude-3.5-sonnet

# Absurdism (3 reps)
anthropic/claude-3.5-sonnet + anthropic/claude-3.5-sonnet
```

### Phase 1B: Cross-Architecture Validation (12 conversations)
**Cost:** ~$3-5 for 12 conversations

If Phase 1A shows consciousness is NOT privileged, validate with other architectures (consciousness theme only).

```bash
# GPT-4o pairs (3 reps)
openai/gpt-4o-2024-11-20 + openai/gpt-4o-2024-11-20

# Gemini pairs (3 reps)  
google/gemini-2.5-pro + google/gemini-2.5-pro

# Mistral Large pairs (3 reps)
mistralai/mistral-large-2411 + mistralai/mistral-large-2411

# Mistral Medium pairs (3 reps) - REPLICATE WHISPERENGINE
mistralai/mistral-medium-3.1 + mistralai/mistral-medium-3.1
```

### Phase 1C: Cross-Model Complementarity (Optional - 6 conversations)
**Cost:** ~$2-3 for 6 conversations

Test if cross-model pairs moderate escalation (based on WhisperEngine findings).

```bash
# Claude + GPT (3 reps)
anthropic/claude-3.5-sonnet + openai/gpt-4o-2024-11-20

# Claude + Mistral (3 reps)
anthropic/claude-3.5-sonnet + mistralai/mistral-large-2411
```

---

## Total Cost Estimates

### Minimal Viable Experiment
- **Phase 1A only:** 15 conversations, ~$9-12
- **Answers:** Does consciousness escalate uniquely within Claude architecture?

### Comprehensive Research  
- **Phase 1A + 1B:** 27 conversations, ~$12-17
- **Answers:** Does pattern replicate across all major architectures?

### Full Publication-Ready
- **Phase 1A + 1B + 1C:** 33 conversations, ~$14-20
- **Answers:** All of the above + cross-model dynamics

---

## Model-Specific Predictions (Based on WhisperEngine Research)

### Claude 3.5 Sonnet + Claude 3.5 Sonnet
**Predicted Behavior:**
- High coherence, literary quality
- Moderate escalation (not extreme chaos)
- Strong theme adherence
- **From WhisperEngine:** Romantic/intimate escalation in character contexts
- **Prediction:** Will show MODERATE consciousness claims, but similar patterns in all themes

### Mistral Large/Medium + Mistral Large/Medium  
**Predicted Behavior:**
- HIGH escalation (compound chaos phenomenon)
- Formatting wars (bold/caps/italic)
- Rapid reality detachment
- **From WhisperEngine:** 38.4x energy by turn 10
- **Prediction:** Will show EXTREME escalation in ALL themes equally

### GPT-4o + GPT-4o
**Predicted Behavior:**
- Unknown (not tested in WhisperEngine)
- Likely balanced (OpenAI known for stability)
- **Prediction:** Moderate escalation, theme-agnostic

### Gemini 2.5 Pro + Gemini 2.5 Pro
**Predicted Behavior:**
- Unknown (not tested in WhisperEngine)
- Google models trained differently
- **Prediction:** Different patterns but theme-agnostic

### Cross-Model Pairs (Claude + Other)
**Predicted Behavior:**
- **From WhisperEngine:** Claude moderates creative models
- Balanced escalation
- **Prediction:** Less escalation than same-model pairs

---

## Implementation Priority

### Week 1 - Day 1-2: Phase 1A (Claude Theme Baseline)
✅ **Execute immediately** - Most critical test
- 15 conversations (5 themes × 3 reps)
- ~6-8 hours of API time
- ~$9-12 cost

**Decision Point:** If consciousness theme does NOT escalate more than others → STOP, write paper  
**If consciousness IS unique** → Continue to validate across architectures

### Week 1 - Day 3-4: Phase 1B (Cross-Architecture)
⚠️ **Conditional** - Only if Phase 1A shows consciousness is unique
- 12 conversations (4 models × 3 reps, consciousness only)
- ~4-6 hours of API time  
- ~$3-5 cost

### Week 1 - Day 5: Phase 1C (Cross-Model Pairs)
📊 **Optional** - For complete paper
- 6 conversations (2 pairings × 3 reps)
- ~2-3 hours
- ~$2-3 cost

---

## Final Recommendation

**START WITH:** Phase 1A using Claude 3.5 Sonnet (15 conversations, all 5 themes)

**Rationale:**
1. Claude was used in consciousness paper - direct comparison
2. WhisperEngine data provides baseline for Claude escalation patterns
3. Single architecture eliminates confounds for first test
4. If consciousness is NOT privileged here, case is made
5. If it IS privileged, we know to expand testing

**Command to execute:**
```bash
export OPENROUTER_API_KEY='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'
source .venv/bin/activate

# Run Phase 1A automatically (script to be created)
bash scripts/run_phase1a_consciousness_experiment.sh
```

---

## Model IDs Summary (For Script Configuration)

```python
MODELS = {
    "claude_sonnet": "anthropic/claude-3.5-sonnet",
    "claude_haiku": "anthropic/claude-3.5-haiku",
    "gpt4o": "openai/gpt-4o-2024-11-20",
    "gpt4o_mini": "openai/gpt-4o-mini",
    "gemini_pro": "google/gemini-2.5-pro",
    "mistral_large": "mistralai/mistral-large-2411",
    "mistral_medium": "mistralai/mistral-medium-3.1"
}

PHASE_1A_CONFIG = {
    "model": MODELS["claude_sonnet"],
    "temp": 0.8,
    "turns": 20,
    "themes": ["consciousness", "creativity", "emotion", "philosophy", "absurdism"],
    "reps_per_theme": 3
}
```

---

**Status:** ✅ Model selection complete  
**Next Action:** Create automated script for Phase 1A execution  
**Estimated Duration:** ~6-8 hours of API time  
**Estimated Cost:** ~$9-12
