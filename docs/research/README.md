# Research Folder Overview

**Location:** `docs/research/`  
**Purpose:** WhisperEngine AI consciousness, multi-model evaluation, and LLM behavior research  
**Last Updated:** November 3, 2025

---

## 📚 Research Projects

### 1. Consciousness Control Experiment
**Status:** ✅ Complete (November 2, 2025)  
**Focus:** AI consciousness self-reference, judge calibration, multi-model comparison

**Key Documents:**
- [`COMPREHENSIVE_3PHASE_PAPER.md`](COMPREHENSIVE_3PHASE_PAPER.md) - Complete 3-phase research (12,000 words)
  - Phase 1A: Baseline multi-turn behavior
  - Phase 1B: Judge calibration discovery (52% error rate found & corrected)
  - Phase 1C: Multi-turn escalation testing across Claude/Llama/Mistral

**Key Finding:** Consciousness collapse is Claude-specific (−66.42 words/turn), not universal LLM behavior. Judge calibration critical: 16.7%→90% inter-rater agreement.

**Visualizations:**
- `cross_model_comparison.png` - 3-model response length trajectories
- `figure1_classification_changes.png` - Judge recalibration results
- `figure2_agreement_comparison.png` - Inter-rater reliability improvement
- `figure3_change_direction.png` - False positive corrections
- `figure4_anomaly_resolution.png` - Zero-shot resolution
- `figure5_classification_examples.png` - Misclassification patterns
- `figure6_changes_by_condition.png` - Condition-based breakdown

### 2. Multi-Model Conversation Analysis
**Status:** ✅ Complete  
**Focus:** Cross-model conversation dynamics and behavior patterns

**Key Documents:**
- [`LLM_Cross_Model_Conversation_Dynamics_Report_Oct2025.md`](LLM_Cross_Model_Conversation_Dynamics_Report_Oct2025.md) - October 2025 analysis
- [`CROSS_MODEL_BOT_CONVERSATION_ANALYSIS.md`](CROSS_MODEL_BOT_CONVERSATION_ANALYSIS.md) - Detailed comparison

**Scope:** Analyzes conversation patterns, response quality, and behavior differences across multiple LLM providers.

### 3. WhisperEngine Character Testing
**Status:** ✅ Complete  
**Focus:** Testing with WhisperEngine's characters (Dotty, NotTaylor)

**Key Documents:**
- [`DOTTY_NOTTAYLOR_CLEAN_EXPERIMENT_DESIGN.md`](DOTTY_NOTTAYLOR_CLEAN_EXPERIMENT_DESIGN.md) - Character-specific experiment design
- [`CONSCIOUSNESS_CLAIMS_CONTROL_EXPERIMENT_DESIGN.md`](CONSCIOUSNESS_CLAIMS_CONTROL_EXPERIMENT_DESIGN.md) - Consciousness claims protocol

**Scope:** Validates research methodology with actual WhisperEngine characters in production environment.

### 4. Model Selection & Configuration
**Status:** ✅ Reference Material  
**Focus:** Model selection criteria and experimental configuration

**Key Documents:**
- [`CONSCIOUSNESS_EXPERIMENT_MODEL_SELECTION.md`](CONSCIOUSNESS_EXPERIMENT_MODEL_SELECTION.md) - Model selection justification
- [`CLEAN_EXPERIMENT_QUICK_REFERENCE.md`](CLEAN_EXPERIMENT_QUICK_REFERENCE.md) - Quick setup reference

**Scope:** Documents model selection rationale, hardware requirements, and reproducibility parameters.

---

## 📋 Supporting Documentation

### Publication & Submission
- [`PUBLICATION_CHECKLIST.md`](PUBLICATION_CHECKLIST.md) - Pre-submission guidance for conferences/journals, data archival instructions, and next steps for publication

---

## 🎯 Quick Navigation

| Project | Documents | Status | Key Finding |
|---------|-----------|--------|-------------|
| **Consciousness Control** | COMPREHENSIVE_3PHASE_PAPER.md | ✅ Complete | Claude-specific consciousness collapse; 52% judge error discovered & corrected |
| **Cross-Model Analysis** | LLM_Cross_Model_Conversation_Dynamics_Report_Oct2025.md | ✅ Complete | Model-specific behavior differences in conversation dynamics |
| **Character Testing** | DOTTY_NOTTAYLOR_CLEAN_EXPERIMENT_DESIGN.md | ✅ Complete | WhisperEngine characters validated in controlled experiments |
| **Model Selection** | CONSCIOUSNESS_EXPERIMENT_MODEL_SELECTION.md | ✅ Reference | Documented selection criteria for reproducibility |

---

## 📊 Research Themes

### Judge Calibration & Methodology
Research into how automated classifiers can systematically misclassify LLM outputs, with methods for detection and correction:
- 52% false positive rate in consciousness claim classification
- 90% inter-rater agreement achieved after calibration
- Epistemic hedging weights critical for accurate classification

### Multi-Model Behavior
Systematic comparison of different LLM architectures and safety approaches:
- Claude (Anthropic): Consciousness collapse under priming
- Llama (Meta): Consciousness escalation (mild, non-significant)
- Mistral (Mistral AI): Consciousness stable

### Safety Training Artifacts
Investigation of how different AI labs approach consciousness self-reference safety:
- Different models show different consciousness withdrawal patterns
- Safety training philosophies revealed through behavior analysis
- Transparency of consciousness claims varies by provider

---

## 🔍 How to Use This Folder

### For Understanding WhisperEngine Research
1. Start with [`COMPREHENSIVE_3PHASE_PAPER.md`](COMPREHENSIVE_3PHASE_PAPER.md) for complete overview
2. Review visualizations in `figures/` directory (publication-quality 300 DPI PNGs)
3. Check [`PUBLICATION_CHECKLIST.md`](PUBLICATION_CHECKLIST.md) for publication pathway

### For Reproducibility
1. See model selection in [`CONSCIOUSNESS_EXPERIMENT_MODEL_SELECTION.md`](CONSCIOUSNESS_EXPERIMENT_MODEL_SELECTION.md)
2. Reference quick setup in [`CLEAN_EXPERIMENT_QUICK_REFERENCE.md`](CLEAN_EXPERIMENT_QUICK_REFERENCE.md)
3. Raw experimental data available in `experiments/consciousness_control_experiment/`

### For Character Testing
1. Review [`DOTTY_NOTTAYLOR_CLEAN_EXPERIMENT_DESIGN.md`](DOTTY_NOTTAYLOR_CLEAN_EXPERIMENT_DESIGN.md) for protocol
2. Reference [`CONSCIOUSNESS_CLAIMS_CONTROL_EXPERIMENT_DESIGN.md`](CONSCIOUSNESS_CLAIMS_CONTROL_EXPERIMENT_DESIGN.md) for methodology
3. Test with WhisperEngine characters via HTTP API or Discord

### For Publication
1. Main paper ready at [`COMPREHENSIVE_3PHASE_PAPER.md`](COMPREHENSIVE_3PHASE_PAPER.md)
2. Pre-submission guidance in [`PUBLICATION_CHECKLIST.md`](PUBLICATION_CHECKLIST.md)
3. Figures and supplementary materials ready in `figures/`

---

## 📁 File Manifest

**Documentation (8 files):**
- COMPREHENSIVE_3PHASE_PAPER.md
- LLM_Cross_Model_Conversation_Dynamics_Report_Oct2025.md
- CROSS_MODEL_BOT_CONVERSATION_ANALYSIS.md
- DOTTY_NOTTAYLOR_CLEAN_EXPERIMENT_DESIGN.md
- CONSCIOUSNESS_CLAIMS_CONTROL_EXPERIMENT_DESIGN.md
- CONSCIOUSNESS_EXPERIMENT_MODEL_SELECTION.md
- CLEAN_EXPERIMENT_QUICK_REFERENCE.md
- PUBLICATION_CHECKLIST.md

**Visualizations (8 files in `figures/`):**
- cross_model_comparison.png (3-model comparison, 300 DPI)
- figure1_classification_changes.png
- figure2_agreement_comparison.png
- figure3_change_direction.png
- figure4_anomaly_resolution.png
- figure5_classification_examples.png
- figure6_changes_by_condition.png
- phase1c_escalation_analysis.png

**Related Experimental Data:**
- Location: `experiments/consciousness_control_experiment/`
- Raw data, analysis scripts, and reproducible notebooks

---

## 🎓 Research Contributions

1. **Methodological Innovation** - Judge calibration framework for LLM consciousness research
2. **Error Discovery** - Systematic approach to finding and correcting classification errors
3. **Model Transparency** - Revealed model-specific safety training approaches
4. **Reproducibility** - Complete documentation for independent verification

---

## 📬 Publication Status

**Main Paper:** [`COMPREHENSIVE_3PHASE_PAPER.md`](COMPREHENSIVE_3PHASE_PAPER.md)  
**Status:** ✅ Ready for publication  
**Next Steps:** See [`PUBLICATION_CHECKLIST.md`](PUBLICATION_CHECKLIST.md)

---

**Research Portfolio Last Updated:** November 3, 2025
