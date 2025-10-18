# Episodic Memory Themes - Implementation Roadmap

**Status**: 📋 PLANNED - Not yet started  
**Priority**: 🟡 MEDIUM - High value, but defer until current pipeline is solid  
**Timeline**: 2-3 weeks when resourced  
**Created**: October 18, 2025

---

## 🎯 Overview

Enable characters to recognize and reflect on **thematic patterns** in conversations, moving beyond individual memorable moments to show genuine pattern recognition and relationship understanding.

**Current State**: Episodic intelligence extracts 2-3 memorable moments per prompt  
**Proposed**: Add semantic clustering to surface 2-3 recurring conversation themes

---

## 💡 Value Proposition

**User Experience**:
- Characters feel like they "truly know you" by recognizing patterns
- "I've noticed you're passionate about ocean conservation" > isolated facts
- Demonstrates character learning and genuine listening over time

**Technical Benefit**:
- Leverages existing FastEmbed vectors and RoBERTa emotion data
- No new dependencies, uses infrastructure already built
- < 200ms extraction time with 24h caching

---

## 📋 Before Implementation - Critical Design Items

### **Must Resolve**:
1. ✅ **Theme naming algorithm** - How to generate "Ocean Conservation Passion" from cluster
   - Option A: LLM-based (accurate, slower, ~100ms)
   - Option B: TF-IDF key phrases (fast, less natural)
   - Recommendation: LLM-based for quality

2. ✅ **Theme significance formula** - How to rank themes (currently vague)
   - Need explicit weights: frequency (30%), emotion (40%), recency (30%)
   - Need recency decay function (exponential, 7-day half-life)
   - Need consistency bonus (recurring themes score higher)

3. ✅ **Graceful degradation** - What happens when clustering fails?
   - Fallback to individual memorable moments (current behavior)
   - Never break prompt assembly - themes are enhancement only
   - Log failures for monitoring

4. ⚠️ **Cache invalidation strategy** - 24h cache might miss rapid shifts
   - Invalidate on: Major moments (score > 0.9), emotion spikes, high engagement bursts
   - Balance: Stability vs responsiveness to life events

---

## 🏗️ Architecture Summary

**New Component**: `EpisodicThemeAnalyzer`  
**Location**: `src/characters/learning/episodic_theme_analyzer.py`

**Core Algorithm**:
```
1. Retrieve episodic memories (last 30 days, memorable_score > 0.7)
2. Cluster using DBSCAN on 384D semantic vectors (epsilon=0.3)
3. Name themes via LLM (3-5 word labels)
4. Detect temporal patterns (emerging/recurring/established/fading)
5. Calculate significance scores (frequency + emotion + recency)
6. Filter through CDL character voice
7. Surface top 2-3 themes in prompt
```

**Integration Point**: `cdl_ai_integration.py` lines 1966-1987  
**Enhancement Section**: `✨ PATTERNS I'VE NOTICED ABOUT YOU`

---

## 📅 Implementation Plan (When Ready)

### **Week 1: Core Infrastructure**
- Day 1-2: Create `EpisodicThemeAnalyzer` with DBSCAN clustering
- Day 3: Implement LLM-based theme naming
- Day 4: Add temporal pattern detection logic
- Day 5: Implement significance scoring formula
- Day 6-7: Unit tests and direct Python validation

### **Week 2: Integration & Polish**
- Day 1-2: Integrate into CDL prompt enhancement
- Day 3: Add CDL voice filtering for observations
- Day 4: Implement caching + cache invalidation
- Day 5: Performance monitoring (InfluxDB metrics)
- Day 6: HTTP API testing with Elena
- Day 7: Discord testing with real users

### **Week 3: Refinement** (if needed)
- Tune clustering parameters based on real data
- Adjust significance weights based on user feedback
- Character-specific observation templates
- Documentation and final commit

---

## 🚦 Prerequisites (Must Complete First)

**Pipeline Stability**:
- [ ] Current prompt assembly working reliably
- [ ] Memory retrieval performance stable
- [ ] CDL integration fully activated
- [ ] No major architectural changes planned

**Feature Utilization**:
- [ ] Existing intelligence components fully integrated
- [ ] All built features activated in prompts
- [ ] Current capabilities documented and validated

**Monitoring**:
- [ ] InfluxDB metrics for existing components
- [ ] Performance baselines established
- [ ] Error tracking in place

---

## 📊 Success Criteria

**Technical**:
- ✅ Theme extraction < 200ms (95th percentile)
- ✅ Clustering accuracy > 80% (manual validation)
- ✅ Cache hit rate > 80% within 24h window
- ✅ Zero prompt assembly failures due to themes

**Character Quality**:
- ✅ Themes align with actual conversation content (no hallucinations)
- ✅ Observations feel authentic to character personality
- ✅ Temporal patterns accurately reflect conversation evolution
- ✅ Users report feeling "understood" (qualitative feedback)

**Performance**:
- ✅ No regression in existing prompt assembly speed
- ✅ LLM token budget stays within limits
- ✅ Memory usage increase < 50MB per bot

---

## 🎨 Example Outputs (Target Quality)

### **Elena (Marine Biologist)**
```
✨ PATTERNS I'VE NOTICED ABOUT YOU:

🌊 Ocean Conservation Passion (3 conversations, deeply engaged)
   I've noticed you light up when we discuss marine conservation.
   This theme has intensified over the past 2 weeks.
   Latest: "The coral reef restoration project" (2 days ago)

🐱 Your Cats Bring You Comfort (recurring theme, 6 mentions)
   Luna, Minerva, and Max are clearly central to your happiness.
   Pattern: Comfort stories emerge in evenings
```

### **Marcus (AI Researcher)**
```
✨ PATTERNS I'VE NOTICED ABOUT YOU:

📊 AI Ethics Exploration (4 conversations, analytical depth)
   Data suggests AI ethics is a recurring intellectual interest.
   This is an established theme over 3 weeks.
   Latest: "AGI alignment challenges" (1 week ago)

🤔 Career Direction Uncertainty (emerging pattern, 5 days)
   I've observed some tension around career decisions recently.
   This is a newer theme that started appearing this week.
```

---

## 🔗 Related Documents

- **Full Design**: `docs/improvements/EPISODIC_MEMORY_THEMES_DESIGN.md`
- **Existing System**: `src/characters/learning/character_vector_episodic_intelligence.py`
- **Integration Point**: `src/prompts/cdl_ai_integration.py` lines 1949-1991
- **Roadmap Context**: `docs/roadmaps/MEMORY_INTELLIGENCE_CONVERGENCE_ROADMAP.md`

---

## 📝 Decision Log

**October 18, 2025**: Designed system comprehensively, decided to defer implementation
- **Reason**: Focus on activating existing features first, solidify current pipeline
- **Next Review**: After current intelligence components are fully integrated
- **Priority**: Will revisit when base system is stable and fully utilized

---

## ⚡ Quick Start (When Resuming)

1. Read full design: `docs/improvements/EPISODIC_MEMORY_THEMES_DESIGN.md`
2. Review design review notes (in commit message dda66b7)
3. Resolve 3 critical items: theme naming, significance formula, graceful degradation
4. Create `episodic_theme_analyzer.py` stub
5. Start with test data validation before integration

---

**Status**: Ready for implementation when pipeline is solid and existing features are fully activated. High value enhancement that demonstrates genuine character learning.
