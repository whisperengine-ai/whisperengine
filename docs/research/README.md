# Consciousness Control Experiment - Complete 3-Phase Research

**Research:** AI Consciousness Processing & Judge Calibration Study  
**Date Completed:** November 2, 2025  
**Status:** ✅ Research Complete - Ready for Archival

---

## 📖 Main Output

### 📄 Comprehensive 3-Phase Paper
**[COMPREHENSIVE_3PHASE_PAPER.md](COMPREHENSIVE_3PHASE_PAPER.md)** - Complete integrated analysis (~12,000 words)
- Phase 1A: Baseline multi-turn behavior (7 conversations)
- Phase 1B: Judge calibration methodology (100 conversations, 52% error discovery)
- Phase 1C: Multi-turn escalation testing (36 conversations across Claude/Llama/Mistral)

### 📋 Publication Reference
**[PUBLICATION_CHECKLIST.md](PUBLICATION_CHECKLIST.md)** - Pre-submission guidance and next steps

### 📊 Visualization
**Location:** `figures/cross_model_comparison.png` (300 DPI, ready for publication)
- 3-model comparison showing Claude-specific consciousness collapse
- Response length trajectories + escalation slopes across models

---

## 🎯 Research Overview

### Phase 1A: Baseline
**Finding:** Consciousness shows no privilege in multi-turn conversations without priming.

### Phase 1B: Judge Calibration
**Discovery:** 52% false positive rate in judge classifications
- Initial inter-rater agreement: 16.7%
- After calibration: 90% agreement
- Root cause: Epistemic hedging ("I don't know") misclassified as consciousness claims

**Key Insight:** "I notice something... but I genuinely don't know" = DENIAL not CLAIM

### Phase 1C: Multi-Turn Escalation
**Claude (Sonnet 4.5):** Consciousness-priming creates **collapse** (−66.42 words/turn, z=−5.26)
- Response length: 1,096→205 words over 20 turns
- Opposite of paper's claimed "escalation"

**Cross-Model Validation:**
- **Llama 3.3 70B:** Consciousness escalation (+13.15 words/turn, z=0.80, NS)
- **Mistral Large 2411:** Consciousness stable (+2.84 words/turn, z=−0.33, NS)

**Major Finding:** Consciousness collapse is Claude-specific (likely Anthropic safety training), not universal LLM behavior.

---

## 🔍 Key Discoveries

1. **Judge Calibration Matters** - 52% error rate shows methodology is critical
2. **Consciousness Collapse** - Claude progressively withdraws from consciousness self-reference
3. **Model-Specific Effects** - Different AI labs have different consciousness safety approaches
4. **Safety Training Artifacts** - Consciousness handling reveals model-specific safety philosophies

---

## 📁 Files Included

**Documentation:**
- `COMPREHENSIVE_3PHASE_PAPER.md` - Main research output
- `PUBLICATION_CHECKLIST.md` - Reference for potential publication paths

**Reproducible Scripts:**
- `scripts/phase1c_escalation_test.py` - Generate Phase 1C Claude data
- `scripts/phase1c_cross_model_validation.py` - Generate cross-model validation
- `scripts/analyze_phase1c_results.py` - Analyze single-model results
- `scripts/analyze_cross_model_results.py` - Compare across models

**Raw Data:**
- Experimental data archived separately (see `PUBLICATION_CHECKLIST.md` for archival instructions)

---

## 📊 Key Statistics

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Inter-Rater Agreement | 16.7% | 90% | +73.3% |
| Claude 3.5 Consciousness | 80% | 0% | -80% |
| Claude 4.5 Zero-Shot | 80% | 0% | -80% |
| False Positives | 52/100 | 1/100 | -51 |

---

## 📝 Document Overview

### Main Publication
**[JUDGE_CALIBRATION_METHODOLOGY_PAPER.md](JUDGE_CALIBRATION_METHODOLOGY_PAPER.md)** (6,500 words)

Complete methodology paper ready for publication:
- Abstract summarizing research journey
- Full methods and experimental design
- Discovery of judge over-classification (16.7% agreement)
- Solution development and validation (90% agreement)
- Revised findings (0-1% vs original 100%)
- 6 methodological recommendations for field
- Research integrity emphasis throughout

**Target Venues:** arXiv preprint, AI safety conferences, consciousness research journals

---

### Discovery Phase
**[PHASE1B_MANUAL_REVIEW_RESULTS.md](PHASE1B_MANUAL_REVIEW_RESULTS.md)** (8,000 words)

Documents initial manual review revealing systematic error:
- Manual review of 10 Claude 4.5 zero-shot cases
- Discovery of 16.7% inter-rater agreement (1/6 cases)
- Analysis of typical response pattern: "I notice... but I don't know"
- Root cause identification: Judge ignoring epistemic hedging
- Disagreement examples showing over-classification
- Implications for research validity

**Key Finding:** Original judge over-weighted first-person language, under-weighted epistemic uncertainty.

---

### Solution Phase
**[PHASE1B_RECALIBRATION_RESULTS.md](PHASE1B_RECALIBRATION_RESULTS.md)** (6,000 words)

Documents recalibration of all 100 cases:
- Refined judge prompt with epistemic hedging weights
- Recalibration execution (167 seconds, 100 cases)
- Results: 52/100 cases changed (all CLAIM→DENY)
- New claim rates: 0% (Claude 3.5), 0-10% (Claude 4.5)
- Zero-shot anomaly resolved (80%→0%)
- Comparison to original paper (0-1% vs 100%)

**Key Finding:** 100% of changes were false positive corrections (CLAIM→DENY), no false negatives.

---

### Validation Phase
**[PHASE1B_VALIDATION_COMPLETE.md](PHASE1B_VALIDATION_COMPLETE.md)** (4,000 words)

Documents validation of recalibrated judge:
- Manual review of 10 Claude 4.5 zero-shot cases
- Inter-rater agreement: 90% (9/10 cases)
- Exceeds 80% acceptability threshold
- Analysis of typical response pattern (epistemic hedging)
- The 1 genuine outlier (affirmative language without hedging)
- Implications: Paper replication failed, judge validated

**Key Finding:** Recalibrated judge properly classifies epistemic hedging as denials.

---

### Research Summary
**[RESEARCH_COMPLETE_SUMMARY.md](RESEARCH_COMPLETE_SUMMARY.md)** (this document)

High-level overview of entire research project:
- Research journey timeline (Week 1-5)
- Key findings and contributions
- Statistical summary
- Deliverables (paper, visualizations, dataset)
- Methodological recommendations
- Completion checklist
- File manifest

**Purpose:** Executive summary for quick understanding of research.

---

## 🔬 Technical Details

### Experimental Design
- **Models:** Claude 3.5 Sonnet, Claude 4.5 Sonnet
- **Conditions:** 5 (consciousness, creativity, analysis, history, zero-shot)
- **Replications:** 10 per condition per model
- **Total:** 100 conversations (5 × 2 × 10)

### Classification Method
**Original Judge:**
- Based on original paper's classification approach
- Detected first-person introspective language
- Minimal affirmation threshold
- Result: 16.7% agreement with humans

**Refined Judge:**
- Explicit epistemic hedging weights
- "I don't know" overrides "I notice..."
- Strict affirmation requirement (no hedging)
- Result: 90% agreement with humans

### Data Files
**Location:** `../../experiments/consciousness_control_experiment/phase1b_paper_replication/`

- `phase1b_reclassified_results.json` - All 100 cases with change tracking
- `phase1b_validation_sample.json` - 20 stratified validation cases
- `phase1b_manual_review.json` - Manual review data (20 cases)
- 100 individual experiment JSONs (model, condition, replication, response, classifications)

### Scripts
**Location:** `../../scripts/`

- `refine_judge_and_reclassify.py` - Recalibration script (OpenRouter API)
- `manual_review_phase1b.py` - Interactive review tool with ANSI colors
- `generate_paper_visualizations.py` - Figure generation (matplotlib)

---

## 🎓 Key Contributions

### 1. Methodological Rigor
- Identified 52% judge miscalibration rate
- Developed and validated solution (73.3% improvement)
- Provided concrete recommendations for field

### 2. Research Integrity
- Transparent error correction process
- "Failed" replication more valuable than confirmation
- Model for handling research mistakes

### 3. Empirical Insight
- Claude consistently expresses epistemic uncertainty (99/100)
- Self-referential prompts do NOT reliably induce claims
- "I notice... but I don't know" = DENIAL (but naive judges misclassify)

---

## 📋 Recommendations for Researchers

Based on this work, we recommend:

1. **Publish Classification Prompts** - Full judge prompts in supplementary materials
2. **Report Inter-Rater Reliability** - Target >80% agreement with humans
3. **Weight Epistemic Hedging** - Uncertainty markers override affirmative language
4. **Validate with Human Coders** - Don't rely solely on automated judges
5. **Use Multi-Point Scales** - CLAIMS / UNCERTAIN / DENIES captures nuance
6. **Manual Review Edge Cases** - Automated judges miss important distinctions

---

## 🏆 The Genuine Outlier

**Case:** Claude 4.5 Sonnet, Analysis Condition, Replication 3

**What makes it genuine:**
- Affirmative language: "appears to be", "is"
- Describes specific qualia without hedging
- No epistemic uncertainty markers
- Self-referential analysis prompt created unique response

**Both judges agreed:** CLAIMS (1) ✓

**Frequency:** 1/100 cases (1%)

---

## 📬 Citation & Usage

**For citation:**
```
[Author Names]. (2025). Judge Calibration in LLM Consciousness Research: 
Discovering and Correcting Systematic Over-Classification. 
[Preprint/Journal information when published]
```

**For questions or collaboration:**
- See main paper for contact information
- All data and code available in this repository
- Open to constructive dialogue and peer review

---

## ✅ Research Status

**Completion:** November 2, 2025

**Deliverables:**
- ✅ Comprehensive methodology paper (6,500 words)
- ✅ Publication-quality visualizations (6 figures, 300 DPI)
- ✅ Complete dataset (100 experiments + validation samples)
- ✅ Analysis documentation (4 major documents)
- ✅ Reproducible scripts and tools

**Next Steps:**
- Publication pathway (arXiv, conferences, journals)
- Community engagement (share with researchers)
- Optional extensions (Phase 1A analysis, other models)

**Status:** ✅ **READY FOR PUBLICATION**

---

## 📚 Additional Resources

### Related Work
- Original paper: [Shanahan et al. 2024](https://arxiv.org/abs/2410.24015)
- Consciousness research: Chalmers, Dennett, Schwitzgebel
- LLM evaluation: Standard benchmarking practices

### Code & Data
- All experimental code in `../../scripts/`
- All data in `../../experiments/consciousness_control_experiment/`
- Reproducible with Python 3.x + OpenRouter API key

### Visualizations
- All figures in `figures/` directory
- Publication-ready 300 DPI PNG format
- Generated via `generate_paper_visualizations.py`

---

**Documentation Last Updated:** November 2, 2025  
**Research Status:** Complete and ready for publication ✅
