# Phase 3: Background Worker Architecture Design

**Branch**: `refactor/pipeline-optimization`  
**Created**: October 30, 2025  
**Status**: 📋 Design Phase

---

## 🎯 Objective

Design and implement background worker architecture to compute the **7 strategic components** removed from the hot path in Phase 2, while maintaining their analytical value through cached results.

**Strategic Components Moved to Background**:
1. Memory Aging Analysis
2. Character Performance Tracking
3. Personality Profile Evolution
4. Context Switch Detection
5. Human-Like Memory Behavior
6. Conversation Pattern Analysis
7. Proactive Engagement Analysis

---

## 🏗️ Architecture Overview

### Leveraging Existing Infrastructure

WhisperEngine **already has a staging enrichment worker** (`src/enrichment/worker.py`) that:
- ✅ Runs as separate Docker container (zero hot path impact)
- ✅ Scans Qdrant vector storage periodically
- ✅ Uses high-quality LLMs for analysis
- ✅ Stores results in PostgreSQL
- ✅ Supports time-windowed processing

**Phase 3 Strategy**: **Extend** existing enrichment worker with strategic component engines.

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    WhisperEngine Platform                           │
├─────────────────────────────────────────────────────────────────────┤
│  HOT PATH (Real-time) - 4 Tactical Components                       │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │ Discord Message → MessageProcessor                        │      │
│  │   ├─ Enhanced Context Analysis (REAL-TIME)               │      │
│  │   ├─ Conversation Intelligence (REAL-TIME)               │      │
│  │   ├─ Unified Character Intelligence (REAL-TIME)          │      │
│  │   └─ Vector Emotion Analysis (REAL-TIME)                 │      │
│  │                                                           │      │
│  │ Store: Qdrant Vector Memory                              │      │
│  │ Store: InfluxDB Temporal Metrics                         │      │
│  │ Store: PostgreSQL Character State                        │      │
│  └──────────────────────────────────────────────────────────┘      │
│                                                                      │
│  ═══════════════════════════════════════════════════════════════   │
│                                                                      │
│  COLD PATH (Async) - 7 Strategic Components                         │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │ Enrichment Worker (Periodic: 5-15 min intervals)         │      │
│  │                                                           │      │
│  │ Read: Qdrant Vector Memory (scan new messages)           │      │
│  │ Read: InfluxDB Temporal Metrics (trends)                 │      │
│  │ Read: PostgreSQL Character State (history)               │      │
│  │                                                           │      │
│  │ Compute Strategic Components:                            │      │
│  │   ├─ Memory Aging Analysis Engine                        │      │
│  │   ├─ Character Performance Tracker                       │      │
│  │   ├─ Personality Profile Evolution                       │      │
│  │   ├─ Context Switch Detection                            │      │
│  │   ├─ Human-Like Memory Behavior                          │      │
│  │   ├─ Conversation Pattern Analysis                       │      │
│  │   └─ Proactive Engagement Analysis                       │      │
│  │                                                           │      │
│  │ Store: PostgreSQL Strategic Cache Tables                 │      │
│  │   - strategic_memory_health                              │      │
│  │   - strategic_character_performance                      │      │
│  │   - strategic_personality_profiles                       │      │
│  │   - strategic_conversation_patterns                      │      │
│  │   - strategic_engagement_opportunities                   │      │
│  └──────────────────────────────────────────────────────────┘      │
│                                                                      │
│  Hot Path Retrieval: Fast cache reads (<5ms PostgreSQL lookup)      │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │ MessageProcessor checks cache freshness:                 │      │
│  │   IF cache_age < 5 minutes: Use cached strategic data    │      │
│  │   ELSE: Use basic heuristics (graceful degradation)      │      │
│  └──────────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Strategic Component Design

### 1. Memory Aging Analysis Engine

**Purpose**: Track memory access patterns and identify memories losing relevance.

**Data Sources**:
- Qdrant vector memory (last access timestamps, retrieval frequency)
- User conversation patterns (time gaps, topic shifts)

**Computations**:
- Memory staleness score (time since last retrieval)
- Retrieval frequency decay
- Topic relevance drift
- Forgetting curve modeling

**Cache Schema** (`strategic_memory_health`):
```sql
CREATE TABLE strategic_memory_health (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    bot_name TEXT NOT NULL,
    memory_snapshot JSONB NOT NULL,  -- Top stale/fresh memories
    avg_memory_age_hours FLOAT,
    retrieval_frequency_trend TEXT,  -- 'increasing', 'stable', 'declining'
    forgetting_risk_memories JSONB,  -- Array of memory IDs at risk
    computed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,  -- NOW() + 5 minutes
    
    UNIQUE(user_id, bot_name)
);
CREATE INDEX idx_memory_health_expires ON strategic_memory_health(expires_at);
```

**Retrieval Pattern** (MessageProcessor):
```python
# Fast cache lookup in hot path
memory_health = await self._get_cached_strategic_data(
    'strategic_memory_health', user_id, bot_name
)
if memory_health and memory_health['expires_at'] > datetime.now(timezone.utc):
    # Use cached data
    memory_insights = memory_health['memory_snapshot']
else:
    # Graceful degradation: use simple heuristics or skip
    memory_insights = None
```

---

### 2. Character Performance Tracker

**Purpose**: Monitor bot response quality and personality consistency.

**Data Sources**:
- InfluxDB temporal metrics (engagement scores, satisfaction, coherence)
- PostgreSQL character state (emotion trajectory, personality adherence)

**Computations**:
- 7-day rolling average engagement score
- Personality consistency index
- Response quality trends
- Anomaly detection (sudden quality drops)

**Cache Schema** (`strategic_character_performance`):
```sql
CREATE TABLE strategic_character_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bot_name TEXT NOT NULL,
    time_window_hours INTEGER NOT NULL DEFAULT 168,  -- 7 days
    engagement_score_avg FLOAT,
    satisfaction_score_avg FLOAT,
    coherence_score_avg FLOAT,
    personality_consistency_index FLOAT,  -- 0.0-1.0
    quality_trend TEXT,  -- 'improving', 'stable', 'declining'
    recent_anomalies JSONB,  -- Array of detected issues
    computed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    
    UNIQUE(bot_name, time_window_hours)
);
CREATE INDEX idx_character_perf_expires ON strategic_character_performance(expires_at);
```

---

### 3. Personality Profile Evolution

**Purpose**: Track how user perceives/interacts with bot personality over time.

**Data Sources**:
- Qdrant conversation history (topic patterns, emotional tone)
- PostgreSQL character state (personality trait activations)

**Computations**:
- Dominant personality traits exhibited
- User response to different personality modes
- Trait activation frequency
- Personality adaptation opportunities

**Cache Schema** (`strategic_personality_profiles`):
```sql
CREATE TABLE strategic_personality_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    bot_name TEXT NOT NULL,
    dominant_traits JSONB,  -- Array of {trait, frequency, effectiveness}
    user_response_patterns JSONB,  -- How user reacts to each trait
    adaptation_suggestions JSONB,  -- Recommended personality adjustments
    trait_evolution_history JSONB,  -- 30-day trait activation trends
    computed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    
    UNIQUE(user_id, bot_name)
);
CREATE INDEX idx_personality_expires ON strategic_personality_profiles(expires_at);
```

---

### 4. Context Switch Detection

**Purpose**: Identify when user changes topics and predict switch timing.

**Data Sources**:
- Qdrant semantic vectors (topic clustering)
- Conversation message sequences (time gaps, topic shifts)

**Computations**:
- Topic embedding clustering (detect shifts)
- Average conversation duration per topic
- Context switch likelihood (predictive)
- Topic transition patterns

**Cache Schema** (`strategic_conversation_patterns`):
```sql
CREATE TABLE strategic_conversation_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    bot_name TEXT NOT NULL,
    recent_topics JSONB,  -- Array of {topic, start_time, end_time}
    avg_topic_duration_minutes FLOAT,
    context_switch_frequency FLOAT,  -- switches per hour
    predicted_switch_likelihood FLOAT,  -- 0.0-1.0
    topic_transition_graph JSONB,  -- Common topic → topic paths
    computed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    
    UNIQUE(user_id, bot_name)
);
CREATE INDEX idx_conv_patterns_expires ON strategic_conversation_patterns(expires_at);
```

---

### 5. Human-Like Memory Behavior

**Purpose**: Model natural forgetting/recall patterns for authentic interactions.

**Data Sources**:
- Qdrant vector memory (access patterns, retrieval scores)
- Time-based decay curves

**Computations**:
- Ebbinghaus forgetting curve modeling
- Spaced repetition effectiveness
- Natural recall simulation
- Memory consolidation tracking

**Cache Schema** (`strategic_memory_behavior`):
```sql
CREATE TABLE strategic_memory_behavior (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    bot_name TEXT NOT NULL,
    forgetting_curve_params JSONB,  -- Model parameters
    high_retention_memories JSONB,  -- Memories with strong recall
    low_retention_memories JSONB,  -- Memories at risk of forgetting
    recall_simulation_score FLOAT,  -- How "human-like" memory access is
    computed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    
    UNIQUE(user_id, bot_name)
);
CREATE INDEX idx_memory_behavior_expires ON strategic_memory_behavior(expires_at);
```

---

### 6. Conversation Pattern Analysis (Extended)

**Purpose**: Deep analysis of user communication style and preferences.

**Data Sources**:
- Qdrant conversation history (message lengths, complexity)
- RoBERTa emotion metadata (emotional tone patterns)

**Computations**:
- Communication style fingerprint
- Preferred conversation depth
- Emotional engagement patterns
- Optimal response length

**Cache Integration**: Uses `strategic_conversation_patterns` table (see #4).

---

### 7. Proactive Engagement Analysis

**Purpose**: Identify opportunities for bot to initiate meaningful interactions.

**Data Sources**:
- InfluxDB engagement metrics (successful proactive attempts)
- Qdrant conversation gaps (long silence periods)

**Computations**:
- Optimal proactive message timing
- Topic relevance for proactive outreach
- User receptivity score
- Engagement opportunity detection

**Cache Schema** (`strategic_engagement_opportunities`):
```sql
CREATE TABLE strategic_engagement_opportunities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    bot_name TEXT NOT NULL,
    optimal_timing_hours FLOAT,  -- Hours since last message to reach out
    receptivity_score FLOAT,  -- 0.0-1.0, how likely user is receptive
    suggested_topics JSONB,  -- Array of topics likely to engage user
    last_engagement_gap_hours FLOAT,
    proactive_success_rate FLOAT,  -- Historical success of proactive messages
    computed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    
    UNIQUE(user_id, bot_name)
);
CREATE INDEX idx_engagement_expires ON strategic_engagement_opportunities(expires_at);
```

---

## ⚙️ Implementation Plan

### Phase 3A: Cache Schema (Week 1)
- [ ] Create Alembic migration for 6 strategic cache tables
- [ ] Add TTL/expiration indexes
- [ ] Create helper functions for cache reads in `message_processor.py`
- [ ] Test cache read performance (<5ms target)

### Phase 3B: Enrichment Worker Engines (Weeks 2-3)
- [ ] Implement `MemoryAgingEngine` in `src/enrichment/`
- [ ] Implement `CharacterPerformanceEngine`
- [ ] Implement `PersonalityProfileEngine`
- [ ] Implement `ContextSwitchEngine`
- [ ] Implement `HumanMemoryBehaviorEngine`
- [ ] Implement `ConversationPatternEngine`
- [ ] Implement `ProactiveEngagementEngine`

### Phase 3C: Worker Integration (Week 4)
- [ ] Extend `EnrichmentWorker.run()` to compute strategic components
- [ ] Add per-bot processing loop (iterate through all active bots)
- [ ] Implement incremental processing (only new data since last run)
- [ ] Add error handling and retry logic

### Phase 3D: Hot Path Cache Retrieval (Week 5)
- [ ] Add cache lookup functions to `MessageProcessor`
- [ ] Implement graceful degradation (fallback when cache stale)
- [ ] Add cache freshness monitoring
- [ ] Test hot path latency impact (<5ms overhead)

### Phase 3E: Production Deployment (Week 6)
- [ ] Add enrichment worker to `docker-compose.multi-bot.yml`
- [ ] Configure worker intervals (target: 5-15 minutes)
- [ ] Add monitoring dashboards for cache freshness
- [ ] Deploy to staging and validate

---

## 🎯 Success Metrics

### Performance Targets
- **Hot Path Latency Reduction**: 40-60% (215-510ms savings)
- **Cache Read Time**: <5ms per lookup
- **Cache Hit Rate**: >95% (5-minute freshness window)
- **Worker Processing Time**: <2 minutes per bot per cycle

### Quality Targets
- **No Personality Degradation**: Character authenticity maintained
- **Strategic Insights Preserved**: All 7 component outputs available via cache
- **Graceful Degradation**: System works even when cache stale

---

## 🚧 Risk Mitigation

### Risk 1: Cache Staleness
**Mitigation**: 
- 5-minute freshness target (aggressive for background worker)
- Graceful degradation: use simple heuristics when cache stale
- Monitor cache hit rates in Grafana

### Risk 2: Worker Failures
**Mitigation**:
- Worker retries with exponential backoff
- Health checks via Docker Compose
- Alert on worker downtime >10 minutes

### Risk 3: Database Load
**Mitigation**:
- Cache upsert (UPDATE or INSERT) to avoid duplication
- Indexed expiration columns for fast cleanup
- Monitor PostgreSQL query performance

### Risk 4: Personality Impact
**Mitigation**:
- Phase 6 regression testing with character consistency validation
- A/B testing in production (compare cached vs real-time results)
- User feedback monitoring

---

## 📝 Next Steps

**Immediate Actions**:
1. Review this design document with team
2. Create Alembic migration for cache tables (Phase 3A)
3. Implement first strategic engine (`MemoryAgingEngine`) as proof of concept
4. Test cache read performance in MessageProcessor

**Future Enhancements** (Post-Phase 6):
- Add Redis layer for ultra-fast cache (optional)
- Implement ML models for predictive components (context switches, proactive timing)
- Add real-time cache invalidation triggers (message count thresholds)
- Build admin UI for cache inspection and manual invalidation

---

## 📚 Related Documents

- **Phase 1 Audit**: `docs/optimization/PHASE1_AUDIT_RESULTS.md`
- **Original Roadmap**: `docs/optimization/PIPELINE_OPTIMIZATION_ROADMAP.md`
- **Existing Enrichment Worker**: `src/enrichment/README.md`
- **Architecture**: `docs/architecture/README.md`

---

**Status**: 📋 Design Complete - Ready for Implementation (Phase 3A)
