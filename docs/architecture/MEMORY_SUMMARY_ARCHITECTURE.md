# Memory Summary Architecture Design
**Date:** November 7, 2025  
**Status:** Design Phase  
**Author:** WhisperEngine Team

## Executive Summary

Replace runtime PostgreSQL fact/preference queries with Claude-style memory summaries for prompt injection, while retaining structured facts as background validation and analytics layer.

**Core Insight:** Use structured fact extraction as **input signal** for generating high-quality memory summaries, not as end product for prompts.

---

## Problem Statement

### Current System Issues

**PostgreSQL Fact Storage (`fact_entities`, `user_fact_relationships`, `universal_users.preferences`)**

**Weaknesses:**
- ❌ **Context-dependent retrieval**: "Deciding what to query requires good context" - complex query routing logic needed
- ❌ **Atomized facts lose narrative**: Individual facts like `[pizza (likes, food)]` lack conversational context
- ❌ **Query complexity**: Sophisticated intent analysis required to decide WHICH facts to retrieve
- ❌ **Integration overhead**: 50+ CDL tables + fact tables + preference tables = complex system
- ❌ **Latency**: Complex joins across multiple tables at runtime
- ❌ **Duplicate LLM calls**: Fact extraction LLM call + Summary LLM call = expensive

**Alternative Approach:**
- ✅ **spaCy preprocessing**: Fast local NLP extracts entities, patterns, negations
- ✅ **Direct synthesis**: One LLM call creates memory summary from conversations + spaCy scaffold
- ✅ **Cost reduction**: 50% fewer LLM calls (1 instead of 2)
- ✅ **Simpler pipeline**: No intermediate structured fact storage needed for prompts

---

## Proposed Architecture: Single-Stage Direct Synthesis

**Key Insight:** Use spaCy preprocessing to build structured scaffolds, then do ONE LLM call to generate Claude-style memory summary directly. No intermediate fact extraction LLM calls needed.

```
┌─────────────────────────────────────────────────────────────────┐
│                    CONVERSATION HAPPENS                          │
│              (User chats with Elena/Marcus/Jake)                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│               ENRICHMENT WORKER (Background)                     │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ SINGLE-STAGE: Memory Summary Engine (NEW)                │  │
│  │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━│  │
│  │ INPUT GATHERING:                                          │  │
│  │ • Conversation history from Qdrant (90 days)              │  │
│  │ • Existing memory summary (for incremental updates)       │  │
│  │                                                           │  │
│  │ SPACY PREPROCESSING (LOCAL, FAST):                        │  │
│  │ • Named entities (PERSON, ORG, GPE, etc.)                 │  │
│  │ • Dependency parsing (subject-verb-object)                │  │
│  │ • Negation detection ("don't like", "hate")               │  │
│  │ • Preference patterns ("love", "enjoy", "favorite")       │  │
│  │ • Key topics and themes                                   │  │
│  │ • Temporal references ("recently", "always")              │  │
│  │ → RESULT: Structured scaffold (JSON)                      │  │
│  │                                                           │  │
│  │ SINGLE LLM CALL:                                          │  │
│  │ • Input: Conversations + spaCy scaffold                   │  │
│  │ • Output: Claude-style memory summary                     │  │
│  │ • Format: Work context, personal, top of mind             │  │
│  │                                                           │  │
│  │ OPTIONAL: Extract structured facts for analytics          │  │
│  │ • Parse summary to populate fact_entities table           │  │
│  │ • Used for validation/debugging only (not prompts)        │  │
│  │                                                           │  │
│  │ STORAGE:                                                  │  │
│  │ • user_memory_summaries table (PRIMARY)                   │  │
│  │ • fact_entities/relationships (OPTIONAL analytics)        │  │
│  └──────────────────────────┬───────────────────────────────┘  │
└────────────────────────────┼───────────────────────────────────┘
                              │
                              │ Memory summary in PostgreSQL
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│               RUNTIME MESSAGE PROCESSING                         │
│                                                                  │
│  A/B TEST: Memory summary (10%) vs Facts (90%)                   │
│  PRIMARY (test):   Load memory_summary → Inject into prompt     │
│  CONTROL (legacy): Load facts → Complex routing → Inject        │
└─────────────────────────────────────────────────────────────────┘
```

**System Architecture:**
- 🔄 **INLINE (Real-time)**: spaCy+regex fact extraction + regex preference extraction (feature flagged, default=on)
- 🧠 **ENRICHMENT (Background)**: LLM fact/preference extraction + NEW unified memory summaries
- 📊 **THREE LAYERS**: Inline spaCy+regex + Enrichment LLM + Unified memory summaries (validation period)
- 🔗 **UNIFIED SUMMARY**: Memory summary combines facts + preferences (no distinction, like Claude)
- ⚡ **EVENTUAL STATE**: Keep best extraction method + Unified memory summaries for prompts

---

## Database Schema

### New Table: `user_memory_summaries`

```sql
CREATE TABLE user_memory_summaries (
    user_id TEXT NOT NULL,
    bot_name TEXT NOT NULL,
    summary_text TEXT NOT NULL,  -- Full natural language synthesis
    summary_sections JSONB,       -- Structured sections
    
    -- Metadata
    total_conversations INT DEFAULT 0,
    total_facts_included INT DEFAULT 0,
    
    -- Quality metrics
    validation_status TEXT,  -- 'valid', 'contradictions_detected', 'pending_review'
    validation_issues JSONB, -- List of detected contradictions/concerns
    
    -- Timestamps
    last_synthesis_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    PRIMARY KEY (user_id, bot_name)
);

CREATE INDEX idx_memory_summaries_user ON user_memory_summaries(user_id);
CREATE INDEX idx_memory_summaries_bot ON user_memory_summaries(bot_name);
CREATE INDEX idx_memory_summaries_synthesis ON user_memory_summaries(last_synthesis_at);
```

### Example `summary_sections` JSONB:

```json
{
  "work_context": "Mark works on WhisperEngine, a multi-bot Discord AI platform. He conducts technical testing including regression testing on different model versions.",
  "personal_context": "Mark enjoys Italian food, particularly pizza. He prefers warm weather and finds cold temperatures uncomfortable.",
  "top_of_mind": "Recently analyzing Discord content patterns and conducting counter-experiments with WhisperEngine's multi-bot conversation system.",
  "brief_history": {
    "recent_months": "Operating WhisperEngine for research purposes...",
    "earlier_context": "Engaged in testing Claude's safety behaviors..."
  }
}
```

---

## Component Design

### 1. Memory Summary Engine (NEW)

**Location:** `src/enrichment/memory_summary_engine.py`

**Key Methods:**

```python
class MemorySummaryEngine:
    """
    Generates Claude-style memory summaries using spaCy preprocessing + single LLM call.
    
    EFFICIENT SINGLE-STAGE APPROACH:
    1. spaCy extracts structured scaffold (local, fast, no LLM cost)
    2. One LLM call synthesizes memory summary from conversations + scaffold
    3. Optionally extract structured facts from summary for analytics
    
    Cost: 1 LLM call per user (vs 2 in two-stage approach)
    """
    
    def __init__(self, llm_client, llm_model: str, preprocessor):
        self.llm_client = llm_client
        self.llm_model = llm_model
        self.preprocessor = preprocessor  # EnrichmentNLPPreprocessor (spaCy)
    
    async def generate_user_memory_summary(
        self,
        user_id: str,
        bot_name: str,
        lookback_days: int = 90
    ) -> Dict[str, Any]:
        """
        Generate comprehensive memory summary with single LLM call.
        
        Returns:
            {
                'summary_text': str,      # Full prose summary
                'summary_sections': dict, # Organized sections
                'total_conversations': int,
                'spacy_scaffold': dict,   # Preprocessing results
                'existing_summary': str   # Previous summary for incremental updates
            }
        """
        
    async def _get_conversation_history(
        self,
        user_id: str,
        bot_name: str,
        lookback_days: int
    ) -> List[Dict]:
        """
        Get conversation history from Qdrant vector memory.
        
        Returns list of messages with content, timestamp, memory_type.
        """
        
    def _build_spacy_scaffold(
        self,
        conversations: List[Dict]
    ) -> Dict[str, Any]:
        """
        Use spaCy to extract structured information (NO LLM calls).
        
        Returns:
            {
                'named_entities': {
                    'PERSON': ['Mark', 'Elena'],
                    'ORG': ['WhisperEngine', 'OpenAI'],
                    'GPE': ['La Jolla', 'California'],
                    'PRODUCT': ['Claude', 'Discord']
                },
                'preferences': {
                    'likes': ['pizza', 'warm weather', 'testing'],
                    'dislikes': ['cold weather', 'bugs'],
                    'interests': ['AI research', 'marine biology']
                },
                'key_topics': ['WhisperEngine development', 'AI testing', 'consciousness research'],
                'negations': ['does not like cold weather', 'is not interested in sports'],
                'temporal_markers': ['recently', 'always', 'used to'],
                'dependency_patterns': [
                    {'subject': 'Mark', 'verb': 'works on', 'object': 'WhisperEngine'},
                    {'subject': 'Mark', 'verb': 'enjoys', 'object': 'pizza'}
                ]
            }
        
        This scaffold guides the LLM synthesis without requiring an LLM call for extraction.
        """
        
    async def _synthesize_with_llm(
        self,
        conversations: List[Dict],
        spacy_scaffold: Dict[str, Any],
        existing_summary: Optional[str],
        bot_name: str
    ) -> str:
        """
        SINGLE LLM call for direct memory summary synthesis.
        
        Prompt structure:
        1. Conversation history (full context)
        2. spaCy scaffold (structured hints)
        3. Existing summary (for incremental updates)
        4. Synthesis instructions (Claude-style format)
        
        The spaCy scaffold helps the LLM focus on important entities/patterns
        without requiring a separate fact extraction LLM call.
        """
        
    async def _optional_extract_structured_facts(
        self,
        summary_text: str,
        user_id: str,
        bot_name: str
    ) -> None:
        """
        OPTIONAL: Extract structured facts from summary for analytics/debugging.
        
        This is NOT required for prompt injection - only for:
        - Validation/contradiction detection
        - Export functionality (GDPR, migrations)
        - Analytics dashboards
        
        Can be skipped to save processing time if not needed.
        """
        
    async def _should_regenerate_summary(
        self,
        user_id: str,
        bot_name: str
    ) -> bool:
        """
        Decide if summary needs regeneration.
        
        Triggers:
        - 10+ new conversations since last synthesis
        - 24 hours elapsed since last synthesis
        - Manual invalidation flag
        """
```

---

### 2. Enrichment Worker Integration (MODIFY EXISTING)

**Location:** `src/enrichment/worker.py`

**Add to enrichment cycle:**

```python
async def _enrichment_cycle(self):
    """
    Enhanced enrichment cycle with memory summary generation.
    
    IMPORTANT: THREE extraction systems run in parallel during validation period.
    
    INLINE (Real-time):
    - Fact extraction: spaCy lemmatization + REGEX patterns, feature flag ENABLE_RUNTIME_FACT_EXTRACTION=true (default)
    - Preference extraction: REGEX patterns, feature flag ENABLE_RUNTIME_PREFERENCE_EXTRACTION=true (default)
    - Speed: Fast, free, runs during conversation
    - Output: PostgreSQL fact_entities, user_fact_relationships, universal_users.preferences (SEPARATED)
    
    ENRICHMENT (Background):
    1. Fact extraction (existing - LLM-based, high quality)
    2. Preference extraction (existing - LLM-based, high quality)
    3. Conversation summarization (existing - 24hr windows)
    4. Memory aging (existing)
    5. Character performance (existing)
    6. [OTHER ENGINES...]
    
    NEW ENRICHMENT ENGINE:
    7. Memory summary generation (90-day user memory for prompts)
       - Uses spaCy preprocessing + 1 LLM call
       - **UNIFIED**: Combines facts + preferences into single prose summary (no distinction)
       - Example: "Mark lives in La Jolla and enjoys pizza..." (not separated)
       - Can reference existing structured facts for validation (optional)
       - Produces prompt-ready memory summary
       - Feature flag: ENABLE_MEMORY_SUMMARY_GENERATION=true
    
    COEXISTENCE STRATEGY:
    - Keep all three during validation (3-6 months)
    - A/B test prompts: Separated facts/preferences vs Unified memory summary
    - Deprecate one fact extraction path after validation
    - Most likely: Keep inline spaCy+regex, deprecate enrichment fact extraction (duplicate)
    """
    
    # Memory summary generation
    if self.memory_summary_engine:
        for user_id in active_users:
            should_regen = await self.memory_summary_engine._should_regenerate_summary(
                user_id, 
                bot_name
            )
            
            if should_regen:
                logger.info(f"🧠 Regenerating memory summary for {user_id}/{bot_name}")
                summary = await self.memory_summary_engine.generate_user_memory_summary(
                    user_id, 
                    bot_name
                )
                await self._store_memory_summary(user_id, bot_name, summary)
                
                # Optional: Extract structured facts for analytics
                if config.ENABLE_FACT_ANALYTICS:
                    await self.memory_summary_engine._optional_extract_structured_facts(
                        summary['summary_text'],
                        user_id,
                        bot_name
                    )
```

---

### 3. Message Processor Integration (MODIFY EXISTING)

**Location:** `src/core/message_processor.py`

**Replace fact injection with summary injection:**

```python
async def _get_user_memory_summary(
    self,
    user_id: str,
    bot_name: str
) -> Optional[str]:
    """
    Load Claude-style memory summary from PostgreSQL.
    
    Single query, simple injection - no complex routing logic needed.
    Falls back to structured facts if summary not yet generated.
    """
    
    if not self.bot_core.postgres_pool:
        return None
    
    try:
        # Single query for memory summary
        query = """
            SELECT summary_text, summary_sections, validation_status
            FROM user_memory_summaries
            WHERE user_id = $1 AND bot_name = $2
        """
        
        result = await self.bot_core.postgres_pool.fetchrow(query, user_id, bot_name)
        
        if result:
            # Check validation status
            if result['validation_status'] == 'valid':
                logger.info(f"✅ MEMORY SUMMARY: Loaded validated summary ({len(result['summary_text'])} chars)")
                return result['summary_text']
            else:
                logger.warning(f"⚠️ MEMORY SUMMARY: Validation issues detected, using with caution")
                return result['summary_text']
        else:
            logger.debug(f"🔍 MEMORY SUMMARY: No summary found, falling back to structured facts")
            return None
            
    except Exception as e:
        logger.error(f"❌ MEMORY SUMMARY: Failed to load: {e}")
        return None

# In prompt assembly:
async def _build_system_prompt(...):
    # Try memory summary first (new path)
    memory_summary = await self._get_user_memory_summary(user_id, bot_name)
    
    if memory_summary:
        # Simple injection - no query routing needed!
        prompt_parts.append(f"""
## What I Know About You
{memory_summary}
""")
    else:
        # Fallback to structured facts (legacy path)
        user_facts = await self._get_user_facts_from_postgres(user_id, bot_name)
        if user_facts:
            prompt_parts.append(f"Known facts: {', '.join(user_facts)}")
```

---

## Benefits Analysis

### Performance Improvements

| Metric | Current (Structured Facts) | Proposed (Memory Summary + Facts) | Improvement |
|--------|---------------------------|----------------------------------|-------------|
| **Prompt Query Complexity** | Multi-table joins (fact_entities + user_fact_relationships + universal_users) | Single table read (user_memory_summaries) | 3x simpler |
| **Prompt Query Latency** | ~5-10ms (joins + filters) | ~1-2ms (single row) | 5x faster |
| **Context Decision** | Complex intent routing | None (always inject summary) | Eliminates complexity |
| **Integration Logic** | Query builder + formatter + intent analysis | Simple string injection | 10x less code |
| **Inline Processing** | Fact extraction during conversation (existing) | No change (stays active) | No impact on real-time |
| **Enrichment LLM Calls** | Fact extraction LLM + Summary LLM | Summary only (spaCy replaces fact LLM) | **50% enrichment cost reduction** |

**Note:** Inline fact extraction continues running in real-time (no change). Enrichment worker savings come from using spaCy scaffold instead of LLM for fact extraction during summary generation.

### Quality Improvements

- ✅ **Narrative coherence**: Facts connected to conversational context
- ✅ **Temporal awareness**: "Recently mentioned" vs "long-standing interest"
- ✅ **Natural language**: Prose format matches system prompt style
- ✅ **Automatic prioritization**: LLM decides what's important during synthesis
- ✅ **Self-maintaining**: Stale info naturally drops out during re-synthesis
- ✅ **spaCy guidance**: Local NLP provides structured hints without LLM cost

### Cost Improvements

- ✅ **50% fewer LLM calls**: 1 synthesis call vs 2 (extraction + synthesis)
- ✅ **spaCy preprocessing**: Fast local NLP extracts patterns (no API cost)
- ✅ **Optional fact extraction**: Only extract structured facts if analytics needed
- ✅ **Batch processing**: Generate summaries in background (no real-time pressure)

### Architectural Benefits

- ✅ **Simpler pipeline**: One-stage direct synthesis (no intermediate storage)
- ✅ **Incremental migration**: Can A/B test without breaking existing system
- ✅ **Leverages existing infrastructure**: Enrichment worker + spaCy already available
- ✅ **Optional analytics**: Extract facts from summary only if needed

---

## Implementation Phases

### Phase 1: Database Schema (Week 1)
- [ ] Create `user_memory_summaries` table
- [ ] Add Alembic migration
- [ ] Create indexes for performance
- [ ] Add `spacy_scaffold` JSONB column for debugging

### Phase 2: Memory Summary Engine (Week 2)
- [ ] Implement `MemorySummaryEngine` class
- [ ] Integrate spaCy preprocessing (reuse existing `EnrichmentNLPPreprocessor`)
- [ ] Build single-stage synthesis prompt template
- [ ] Implement optional structured fact extraction for analytics
- [ ] Add regeneration trigger logic

### Phase 3: Enrichment Worker Integration (Week 3)
- [ ] Add memory summary generation to enrichment cycle
- [ ] Implement storage methods
- [ ] Add logging/metrics
- [ ] Test background processing
- [ ] Make fact extraction optional (analytics only)

### Phase 4: Message Processor Integration (Week 4)
- [ ] Add `_get_user_memory_summary()` method
- [ ] Modify prompt assembly to use summary
- [ ] Remove complex fact query routing logic
- [ ] Add feature flag for A/B testing

### Phase 5: Validation & Testing (Week 5)
- [ ] Test summary quality on production users
- [ ] Compare spaCy scaffold quality vs LLM fact extraction
- [ ] Performance benchmarking (cost + latency)
- [ ] A/B test conversation quality

### Phase 6: Production Rollout (Week 6)
- [ ] Enable for 10% of users
- [ ] Monitor metrics (latency, quality, errors, LLM costs)
- [ ] Gradual rollout to 100%
- [ ] Consider deprecating fact extraction engine (if successful)

---

## Configuration

### Environment Variables

```bash
# EXISTING: Inline extraction feature flags (transition period)
ENABLE_RUNTIME_FACT_EXTRACTION=true         # Inline regex fact extraction (default: on)
ENABLE_RUNTIME_PREFERENCE_EXTRACTION=true   # Inline regex preference extraction (default: on)

# NEW: Memory summary configuration
ENABLE_MEMORY_SUMMARY_GENERATION=true       # Generate memory summaries in enrichment worker
ENABLE_MEMORY_SUMMARY_PROMPTS=false         # Use summaries in prompts (A/B test flag, default: off)
MEMORY_SUMMARY_LOOKBACK_DAYS=90             # How far back to analyze
MEMORY_SUMMARY_REGENERATION_HOURS=24       # How often to regenerate
MEMORY_SUMMARY_MIN_CONVERSATIONS_TRIGGER=10 # New conversations threshold for regen

# Fallback configuration
ENABLE_FACT_INJECTION_FALLBACK=true    # Use structured facts if no summary
```

---

## Success Metrics

### Performance Metrics
- **Prompt assembly latency**: Target <50ms reduction (eliminate complex queries)
- **Database query count**: Target 70% reduction (1 query vs 3-5 queries)
- **Memory retrieval time**: Target <5ms (single row vs joins)

### Quality Metrics
- **Conversation coherence**: Measure with user satisfaction scores
- **Context relevance**: Track how often bots reference appropriate facts
- **Contradiction rate**: Monitor validation_issues in summaries

### System Health Metrics
- **Summary generation success rate**: Target >95%
- **Validation pass rate**: Target >90% (summaries without contradictions)
- **Enrichment worker latency**: Ensure <1s increase per user

---

## Risk Mitigation

### Risk: LLM synthesis quality varies
**Mitigation:**
- spaCy scaffold provides structured hints to improve quality
- Can add validation step if needed (parse summary for contradictions)
- Existing memory summary used for incremental updates (not from scratch)

### Risk: Summary generation cost (LLM tokens)
**Mitigation:**
- **50% cost reduction**: 1 LLM call instead of 2 (no separate fact extraction)
- spaCy preprocessing reduces LLM token requirements (structured scaffold)
- Generate summaries incrementally (include existing summary in context)
- Only regenerate when 10+ new conversations or 24 hours elapsed
- Use cost-effective models (Claude Haiku, GPT-3.5) for synthesis

### Risk: Migration breaks existing workflows
**Mitigation:**
- Feature flag allows instant rollback
- Inline fact extraction in main bots stays active (for real-time facts)
- Gradual rollout (10% → 50% → 100%)

### Decision: Keep or Remove Inline Fact/Preference Extraction?

**CURRENT STATE (As of Nov 2025):**
WhisperEngine has **dual-path extraction systems** with feature flags:

```python
# src/core/message_processor.py

# Inline fact extraction (spaCy lemmatization + REGEX patterns, fast)
if os.getenv('ENABLE_RUNTIME_FACT_EXTRACTION', 'true').lower() == 'true':
    await self._extract_and_store_knowledge(...)  # Uses spaCy for lemmatization
else:
    logger.debug("⏭️ RUNTIME FACT EXTRACTION: Disabled")

# Inline preference extraction (REGEX patterns, fast)
if os.getenv('ENABLE_RUNTIME_PREFERENCE_EXTRACTION', 'true').lower() == 'true':
    await self._extract_and_store_user_preferences(...)  # Regex for names, timezones
else:
    logger.debug("⏭️ RUNTIME PREFERENCE EXTRACTION: Disabled")

# Background extraction (LLM-based, high quality)
# src/enrichment/worker.py - runs every 11 minutes
await self._process_fact_extraction(...)      # LLM-based
await self._process_preference_extraction(...) # LLM-based
```

**KEY INSIGHT: Memory Summary Combines Facts + Preferences**

The new memory summary will **synthesize both facts and preferences** into a single natural language summary. This matches Claude's approach where there's no distinction between "facts" and "preferences" - it's all just "what I know about you."

Example:
```
# Current (Separated):
Facts: [pizza (likes, food)], [hiking (enjoys, hobby)]
Preferences: [preferred_name: Mark], [location: La Jolla]

# Memory Summary (Unified):
"Mark lives in La Jolla and enjoys Italian food, particularly pizza. 
He's interested in outdoor activities like hiking..."
```

**ARCHITECTURAL DECISION: Keep Dual-Path During Memory Summary Rollout (RECOMMENDED)**

**Phase 1: Co-existence (Current + Memory Summaries)**
```
INLINE (Real-time, spaCy + Regex)        ENRICHMENT (Background, LLM-based)
├─ Fact extraction (spaCy lemma + regex) ├─ Fact extraction (LLM)
├─ Preference extraction (regex)         ├─ Preference extraction (LLM)
└─ ENABLE_RUNTIME_* flags (default=on)   └─ NEW: Memory summary generation
                                              └─ Combines facts + preferences
                                              └─ Uses spaCy scaffold (not LLM extraction)
```

**Phase 2: Memory Summary Validation (2-3 months)**
- Keep all three systems running (inline spaCy+regex, enrichment LLM facts, memory summaries)
- A/B test: Separated facts/preferences vs Unified memory summaries in prompts
- Validate: Summary quality, conversation coherence, cost savings
- Feature flag: `ENABLE_MEMORY_SUMMARY_PROMPTS` (test on 10% → 100%)

**Phase 3: Deprecation Decision (6+ months)**
Once memory summaries proven successful:

**Option A: Keep Inline Extraction (Simplest)**
- ✅ Inline spaCy+regex extraction stays active (fast, free, real-time)
- ✅ Enrichment generates memory summaries (spaCy + LLM)
- ❌ Deprecate enrichment fact/preference extraction (duplicate of inline)
- ✅ Memory summary **unifies** facts + preferences (no distinction)
- **Result**: Inline for structured facts, Background for unified summaries

**Option B: Keep Enrichment Fact Extraction (Highest Quality)**
- ✅ Enrichment fact extraction stays active (LLM-based, high quality)
- ✅ Enrichment generates memory summaries (spaCy + LLM)
- ❌ Deprecate inline spaCy+regex extraction (set ENABLE_RUNTIME_*=false)
- ✅ Memory summary **unifies** facts + preferences
- **Result**: Background for everything (facts + unified summaries)

**Option C: Memory Summaries Only (Radical Simplification)**
- ✅ Enrichment generates memory summaries (spaCy + LLM)
- ❌ Deprecate ALL fact extraction (inline + enrichment)
- ❌ Extract facts from summaries only if analytics needed
- ✅ Single unified summary is source of truth (no facts/preferences split)
- **Result**: Summaries are single source of truth

**RECOMMENDATION: Phase 1 → Phase 2 → Decide Phase 3 based on data**

For now, keep everything running:
1. **Inline spaCy+regex extraction**: Real-time facts/preferences (fast, free)
2. **Enrichment LLM fact extraction**: High-quality facts (LLM-based)
3. **NEW: Memory summaries**: Prompt-ready unified context (spaCy + LLM, **no separation** between facts and preferences)

Once memory summaries prove successful, deprecate one of the fact extraction paths (likely enrichment, since inline is faster).

---

## Future Enhancements

### Short-term (3-6 months)
- **Cross-bot memory summaries**: Synthesize across all bots user talks to
- **Memory import/export**: Claude-compatible format for portability
- **Summary diff tracking**: Show what changed between regenerations

### Medium-term (6-12 months)
- **Hierarchical summaries**: Short (100 words), medium (300 words), long (1000 words)
- **Topic-based sections**: Automatically detect and organize topics
- **Confidence visualization**: Show which facts are high vs low confidence

### Long-term (12+ months)
- **Real-time summary updates**: Incremental updates instead of full regeneration
- **Multi-modal memory**: Include image/voice conversation context
- **Federated memory**: Share summaries across WhisperEngine instances

---

## Open Questions

1. **Should we keep inline fact/preference extraction?** ✅ **ANSWERED**
   - **Decision: YES - Keep ALL extraction systems during rollout**
   - Current: Inline spaCy+regex (facts) + regex (preferences) + Enrichment LLM (both)
   - NEW: Unified memory summary generation (combines facts + preferences in prose)
   - Three-layer validation period: Compare all approaches
   - Deprecate one fact extraction path after 6 months based on data
   - **Feature flags**: `ENABLE_RUNTIME_FACT_EXTRACTION`, `ENABLE_RUNTIME_PREFERENCE_EXTRACTION`, `ENABLE_MEMORY_SUMMARY_PROMPTS`
   - **Key insight**: Memory summary unifies facts + preferences (no separation, like Claude)

2. **How good is spaCy scaffold vs LLM fact extraction?**
   - Need to benchmark: spaCy entities/patterns vs LLM-extracted facts
   - spaCy advantages: Fast, free, no API calls
   - LLM advantages: Better context understanding, relationship extraction
   - **Test in Phase 5**: Compare summary quality with/without spaCy scaffold

3. **Should summaries be bot-specific or user-global?**
   - Current design: Bot-specific (separate summary per character)
   - Alternative: Global summary + bot-specific addendums
   - Tradeoff: Personalization vs consistency
   - **Recommendation**: Start bot-specific, evaluate cross-bot summaries later

4. **How do we migrate existing users?**
   - Option A: Batch generate summaries for all users (expensive - 1 LLM call per user)
   - Option B: Generate on-demand when user sends message (incremental)
   - Option C: Gradual enrichment worker processing (low priority queue)
   - **Recommendation**: Option C - enrichment worker processes gradually

5. **What's the optimal regeneration frequency?**
   - Claude uses 24 hours
   - Consider: User activity level (10+ new conversations), LLM cost (1 call per user/day)
   - **Recommendation**: 24 hours OR 10+ new conversations, whichever comes first

---

## References

- **Claude Memory Documentation**: See attached example in user request
- **WhisperEngine Fact Extraction**: `src/enrichment/fact_extraction_engine.py`
- **WhisperEngine Conversation Summaries**: `src/enrichment/summarization_engine.py`
- **WhisperEngine Enrichment Worker**: `src/enrichment/worker.py`

---

## Approval & Sign-off

- [ ] Architecture Review
- [ ] Database Schema Review
- [ ] Performance Impact Assessment
- [ ] Security Review (user data handling)
- [ ] Privacy Review (GDPR compliance)

---

**Next Steps:**
1. Review this design with team
2. Prototype `MemorySummaryEngine` on test dataset
3. Benchmark summary quality vs structured facts
4. Approve implementation plan and timeline
