# 🚀 Message Pipeline Quick Reference Card

**Print this! Keep it handy!**

---

## 📊 THE FULL PIPELINE (23+ ACTUAL PHASES)

```
┌──────────┬─────────────────────────────────────────┬──────────┬────────┐
│ PHASE    │ NAME                                    │ TIME     │ TYPE   │
├──────────┼─────────────────────────────────────────┼──────────┼────────┤
│ 0        │ Initialize                              │ ~1ms     │ Setup  │
│ 1        │ Security Validation                     │ 5-10ms   │ Serial │
│ 1.5      │ Chronological Ordering (FIXED)          │ 0ms      │ No-op  │
│ 2        │ Name Detection (DISABLED)               │ 0ms      │ No-op  │
│ 2.25     │ Memory Summary Detection                │ 50-100ms │ Cond   │
│ 2.5      │ Workflow Detection & Transactions       │ 30-50ms  │ Serial │
│ 2.75     │ Early Emotion + NLP Cache + Stance      │ 150-250ms│ Serial │
│ 2.8      │ Strategic Intelligence Cache            │ 10-50ms  │ Serial │
│ 2   ⚙️   │ AI Enrichment (RoBERTa, Facts)          │ 100-200ms│ PARA   │
│ 3        │ Memory Retrieval (Qdrant)               │ 20-50ms  │ Serial │
│ 4        │ Context Building (PromptAsm)            │ 50-100ms │ Serial │
│ 4.5  ⭐  │ 7 Strategic Intelligence Engines        │ 200-400ms│ PARA   │
│ 5        │ Structured Prompt Assembly              │ 50-100ms │ Serial │
│ 5.5      │ Enhanced Context with AI Intelligence   │ 20-50ms  │ Serial │
│ 6        │ CDL Character Integration               │ 30-50ms  │ Serial │
│ 7   🖼️   │ Image Processing (if needed)            │ 0-2000ms │ Opt    │
│ 6.5      │ Bot Emotional State (REMOVED)           │ ─────    │ Depr   │
│ 6.7  💕  │ Adaptive Learning Enrichment            │ 50-150ms │ Serial │
│ 6.9  🔧  │ Hybrid Query Routing & Tools (opt)      │ 0-200ms  │ Opt    │
│ 8   🤖⚠️ │ LLM Response Generation                 │ 1-5s ❌  │ Serial │
│ 8.5  🎭  │ Bot Emotion Analysis                    │ 50-100ms │ Serial │
│ 8.6  🛡️  │ Enhanced AI Ethics Monitoring           │ 10-20ms  │ Serial │
│ 8.7  ✨  │ Intelligent Emoji Decoration            │ 20-50ms  │ Serial │
│ 9        │ Response Validation & Sanitization      │ 5-10ms   │ Serial │
│ 10  💾⚡ │ Memory & Knowledge Storage              │ 50-150ms │ PARA+NB│
│ 10a      │  ├─ Qdrant Vector Memory                │ 20-40ms  │ Async  │
│ 10b      │  ├─ PostgreSQL Facts                    │ 10-20ms  │ Async  │
│ 10c      │  ├─ PostgreSQL Preferences              │ 5-10ms   │ Async  │
│ 10d      │  └─ InfluxDB Temporal Recording         │ 5-15ms   │ Async  │
│ 11  🧠   │ Learning Orchestration                  │ 20-50ms  │ Serial │
│ 12  💕   │ Relationship Evolution                  │ 20-40ms  │ Serial │
│ 13  📦   │ Metadata & Response Return              │ 1-2ms    │ Serial │
└──────────┴─────────────────────────────────────────┴──────────┴────────┘

⚙️  = Parallelized (async gather)
🤖⚠️ = Bottleneck (70-90% of total time!)
💾⚡ = Non-blocking (fire-and-forget async, Phase 10a-10d parallel)
⭐ = MAJOR: 7-engine strategic system (NEW!)
```

---

## 🎯 THREE GOLDEN RULES

**Rule 1: RoBERTa is EVERYWHERE** 🎭
- Phase 2.75: Early emotion analysis (150-250ms)
- Phase 2 (parallel): User message emotion (50-100ms) 
- Phase 8.5: Bot response emotion (50-100ms)
- 12+ metadata fields stored with EVERY memory
- **NEVER use keyword matching!** (use stored emotion data)

**Rule 2: PostgreSQL is the SOURCE OF TRUTH** 📊
- **NOT** in Qdrant (that's for conversations only)
- Facts: `user_fact_relationships` + `fact_entities` (Phase 10b)
- Preferences: `universal_users.preferences` (JSONB, Phase 10c)
- Relationships: `relationship_metrics` (trust/affection/attunement)
- Character CDL: 50+ `character_*` tables
- Strategic cache: Phase 4.5 engines

**Rule 3: Three Summary Systems** 📝
- **Real-Time (5-20ms)**: Fast, lossy, no LLM (Phase 3)
- **Background (2-5s)**: High-quality, LLM, PostgreSQL storage (enrichment worker)
- **Advanced (500ms-1s)**: Balanced, optional real-time

---

## 🔄 DATA STORAGE DECISION TREE

```
Is it a conversation pair?
  YES → Qdrant (Phase 10a)
        Vectors (content/emotion/semantic) + RoBERTa metadata
  NO → Is it a fact about user?
       YES → PostgreSQL fact_relationships (Phase 10b)
             Entity type, relationship, confidence
       NO → Is it a preference?
            YES → PostgreSQL preferences (Phase 10c)
                  JSONB with confidence
            NO → Is it a time-series metric?
                 YES → InfluxDB (Phase 10d)
                       Timestamp, value, dimensions, tags
                 NO → Check enrichment worker (11-min cycle)
```

---

## ⚡ PERFORMANCE TARGETS

```
Response Time: <2s ideal (most is unavoidable LLM time)

Latency Budget (UPDATED):
  Phase 8 (LLM):         1000-5000ms  ← BOTTLENECK (70-90%)
  Phase 2.75 (Emotion):  150-250ms    ← Second bottleneck (emotion + stance + NLP cache)
  Phase 4.5 (Engines):   200-400ms    ← New strategic system (parallel, cached)
  Phase 2 (RoBERTa):     100-200ms    ← Parallel with other Phase 2 tasks
  All others:            300-500ms    ← Optimized
  ──────────────────────────────────
  TOTAL:                 1900-8800ms  ← Up from 1300-7800ms (new phases)

NEW: Strategic Cache (Phase 4.5)
  Cache hit: ~10-50ms (from PostgreSQL)
  Cache miss: ~200-400ms (run engines in parallel)
  Cache rate: ~70-80% (enrichment worker every 11min)

Storage: Non-blocking (Phase 10a-10d)
  Response returns in <2s
  All storage happens in background (asyncio.gather)
  Failures logged, don't break chat
  Parallel: 4 storage operations (Qdrant, Facts, Prefs, InfluxDB)

Concurrent: 100+ users (non-blocking storage helps!)
```

---

## 🎨 PARALLEL EXECUTION WINDOWS

**Phase 2: AI Enrichment** (4 async tasks)
```
RoBERTa:  50-100ms ─┐
Facts:    30-50ms   ├─ MAX = 50-100ms (vs 110ms serial!)
Name:     10-20ms   │
CDL:      20-40ms ─┘
```

**Phase 9: Storage** (4 async + non-blocking)
```
Qdrant:     20-40ms ─┐
PostgreSQL: 10-20ms  ├─ MAX = 20-40ms (but DOESN'T BLOCK!)
Prefs:      5-10ms   │
InfluxDB:   5-15ms ─┘

Message returns immediately!
Storage happens async in background
```

---

## 📍 WHERE DOES MY FEATURE GO?

| Need | Phase | Type |
|------|-------|------|
| Validate input | 1 | Serial, before all |
| Analyze emotion | 2 | Parallel (with others) |
| Get memories | 3 | Serial, after input |
| Build prompt | 4 | Serial, before LLM |
| Personalize | 5 | Serial, before LLM |
| Process image | 6 | Optional, conditional |
| Generate response | 7 | Serial LLM call |
| Analyze response emotion | 7.5 | Serial, after response |
| Pretty up response | 7.6 | Serial, after response |
| Check ethics | 7.7 | Serial, after response |
| Validate response | 8 | Serial, after response |
| Store data | 9 | Async, non-blocking |
| Extract learning | 10 | Serial, after storage |
| Update relationship | 11 | Serial, after learning |
| Return result | 12 | Serial, final |

---

## 🛠️ DEBUGGING QUICK REFERENCE

**"Pipeline is slow" → Check:**
```
Is it >5s? → Phase 7 (LLM) - Check model/provider
Is it 1-2s? → Phase 2 (RoBERTa) - Check GPU availability  
Is it <1s? → Phase 9 (Storage) - Check DB latency
→ Look at `processing_time_ms` in result
```

**"Memory not stored" → Check:**
```
1. Phase 9 logs (💾 STORAGE running?)
2. Datastore connectivity (Qdrant/PostgreSQL up?)
3. Run: memory_manager.store_conversation(...)
4. Query datastore directly (SELECT * FROM ...)
```

**"Wrong memories retrieved" → Check:**
```
1. Phase 3 vector type (content/emotion/semantic?)
2. Recency decay (filtering recent memories?)
3. Deduplication (filtering duplicates?)
4. Direct Qdrant query with raw vectors
```

**"User facts not stored" → Check:**
```
1. Phase 9b logs (📊 PostgreSQL Facts running?)
2. NER working (spaCy entity extraction?)
3. SELECT * FROM user_fact_relationships WHERE user_id = '...'
4. No _processing_marker filtering (that's enrichment metadata)
```

---

## 📚 KEY DATABASES

```
Qdrant (Vector Memory)
  ├─ Collection: whisperengine_memory_{bot_name}
  ├─ Per memory: 3 vectors (384D) + 12+ metadata
  └─ Query: Semantic search + quality scoring

PostgreSQL (Knowledge Graph)
  ├─ user_fact_relationships (facts)
  ├─ fact_entities (entity definitions)
  ├─ universal_users (user identity + preferences JSONB)
  ├─ relationship_metrics (trust/affection/attunement)
  └─ character_* (50+ character CDL tables)

InfluxDB (Time-Series)
  ├─ User emotion evolution (hourly)
  ├─ Bot emotion evolution (hourly)
  ├─ Confidence trends
  ├─ Conversation quality metrics
  └─ Retention: 30 days (auto-purged)
```

---

## 🚨 CRITICAL CONSTRAINTS

**Qdrant Schema FROZEN** 🔒
- 384D vectors (CANNOT CHANGE!)
- Named vectors: content, emotion, semantic (FIXED)
- Payload fields: user_id, memory_type, content, timestamp (LOCKED)
- ADDITIVE ONLY (add new fields, never remove)

**Message Order STRICT** 📋
- Security (Phase 1) BEFORE processing
- LLM (Phase 7) needs all previous context
- Validation (Phase 8) BEFORE storage
- Cannot reorder without careful analysis

**Storage NON-BLOCKING** ⚡
- return_exceptions=True (failures logged, not fatal)
- Trade-off: Speed vs 100% reliability
- Errors in logs, not in response

**Character Data DYNAMIC** 🎭
- All from PostgreSQL (no hardcoding!)
- Via DISCORD_BOT_NAME environment variable
- Run once at startup, not per message

---

## 📊 SUMMARIZATION SYSTEMS COMPARISON

| System | Speed | Quality | Storage | When | Use For |
|--------|-------|---------|---------|------|---------|
| Real-Time | 5-20ms | Low | None | Phase 3 | Token budget |
| Background | 2-5s | High | PostgreSQL | 24h async | Storage |
| Advanced | 500ms-1s | Medium | Cache 1h | Opt real-time | Balanced |

**Don't mix them up!**
- Need fast? → Real-Time (no LLM)
- Need quality? → Background (high-quality LLM)
- Need balance? → Advanced (medium effort)

---

## 🎓 LEARNING PATH (Time Estimates)

```
⏱️  5 min:   Read "3 Golden Rules" + this quick ref
⏱️  15 min:  Read MESSAGE_PIPELINE_EXECUTIVE_SUMMARY.md
⏱️  30 min:  Read MESSAGE_PIPELINE_AND_SUMMARIES_REVIEW.md (overview)
⏱️  15 min:  Look at MESSAGE_PIPELINE_VISUAL_FLOWS.md diagrams
⏱️  30 min:  Trace src/core/message_processor.py code
⏱️  30 min:  Run test: test_memory_intelligence_convergence_complete_validation.py
⏱️  ──────
      2h:    Complete understanding
```

---

## 📞 KEY CODE LOCATIONS

```
Main Pipeline:        src/core/message_processor.py (8,000+ lines)
RoBERTa Emotion:      src/intelligence/enhanced_vector_emotion_analyzer.py
Qdrant Memory:        src/memory/vector_memory_system.py (5,363 lines)
CDL Character:        src/prompts/cdl_ai_integration.py (3,458 lines)
Real-Time Summaries:  src/utils/helpers.py (~220 lines)
Background Summaries: src/enrichment/summarization_engine.py
Advanced Summaries:   src/memory/conversation_summarizer.py
Tests:                tests/automated/test_memory_intelligence_convergence_*
```

---

## ✅ CHECKLIST: READY TO USE THIS?

- [ ] Understand 3 golden rules (you should now)
- [ ] Know which phase your feature goes in (use table above)
- [ ] Know which datastore to use (use decision tree)
- [ ] Know how to debug if something breaks (use quick ref)
- [ ] Know where to look in code (use code locations)
- [ ] Ready to read full documents if needed (they exist!)

---

## 🎯 NEXT STEPS

**To Add a Feature:**
1. ✅ Use "Where does my feature go?" table
2. ✅ Read that phase in full documents
3. ✅ Find code in src/core/message_processor.py
4. ✅ Implement + test with test_*_validation.py

**To Debug:**
1. ✅ Use "Debugging Quick Reference" above
2. ✅ Check logs for phase timing
3. ✅ Query datastore directly
4. ✅ Run isolated test

**To Understand More:**
1. ✅ Read MESSAGE_PIPELINE_EXECUTIVE_SUMMARY.md
2. ✅ Read MESSAGE_PIPELINE_AND_SUMMARIES_REVIEW.md
3. ✅ Study MESSAGE_PIPELINE_VISUAL_FLOWS.md
4. ✅ Use MESSAGE_PIPELINE_COMPLETE_INDEX.md for navigation

---

**Bookmark this page! Print it! Reference it when:**
- Adding new features
- Debugging issues
- Onboarding team members
- Making architecture decisions

**WhisperEngine: 18 months of evolution. 10+ live characters. Millions of messages. This is production-grade AI architecture.** ✅

---

*Created: November 5, 2025 | Status: Ready to Use | Version: 1.0*
