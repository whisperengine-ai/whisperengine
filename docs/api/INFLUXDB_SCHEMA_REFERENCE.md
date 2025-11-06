# WhisperEngine InfluxDB Schema Reference

**Last Updated**: October 22, 2025  
**Source**: `src/temporal/temporal_intelligence_client.py`

---

## Quick Reference: All Valid Measurements

| Measurement | Tags | Fields | Purpose |
|-------------|------|--------|---------|
| `confidence_evolution` | bot, user_id, session_id | user_fact_confidence, relationship_confidence, context_confidence, emotional_confidence, overall_confidence | Track bot's confidence in various knowledge areas |
| `relationship_progression` | bot, user_id, session_id | trust_level, affection_level, attunement_level, interaction_quality, communication_comfort | Track user-bot relationship development |
| `conversation_quality` | bot, user_id, session_id | engagement_score, satisfaction_score, natural_flow_score, emotional_resonance, topic_relevance | Measure conversation quality metrics |
| `bot_emotion` | bot, user_id, emotion, session_id | intensity, confidence | Bot's detected emotions per response |
| `user_emotion` | bot, user_id, emotion, session_id | intensity, confidence | User's detected emotions per message |
| `character_emotional_state` | bot, user_id, dominant_state, session_id | enthusiasm, stress, contentment, empathy, confidence | 5-dimensional character emotional state |
| `memory_aging_metrics` | bot, collection_name | total_memories, memories_0_24h, memories_1_7d, memories_7_30d, memories_30_plus, avg_age_hours, oldest_memory_hours | Memory distribution by age |
| `character_graph_performance` | bot, operation, cache_hit | query_time_ms, knowledge_matches | Character graph query performance |
| `intelligence_coordination_metrics` | bot, context_type, coordination_strategy | systems_used, coordination_time_ms, authenticity_score, confidence_score | Multi-system intelligence coordination |
| `emotion_analysis_performance` | bot, user_id, primary_emotion | analysis_time_ms, confidence_score, emotion_count | RoBERTa emotion analysis performance |
| `vector_memory_performance` | bot, collection_name, vector_type, operation | search_time_ms, memories_found, avg_relevance_score | Qdrant vector search performance |
| `cdl_integration_performance` | bot, integration_type | load_time_ms, components_loaded, cache_hit | CDL character loading performance |

---

## Common Flux Query Patterns

### 1. Query Bot Emotional State (5D)
```flux
from(bucket: "performance_metrics")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "character_emotional_state")
  |> filter(fn: (r) => r.bot == "${bot}")
  |> filter(fn: (r) => r.user_id == "${user_id}")
  |> filter(fn: (r) => r._field == "enthusiasm" or r._field == "stress" or r._field == "contentment" or r._field == "empathy" or r._field == "confidence")
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
```

### 2. Query Bot Emotion Distribution
```flux
from(bucket: "performance_metrics")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "bot_emotion")
  |> filter(fn: (r) => r.bot == "${bot}")
  |> filter(fn: (r) => r.user_id == "${user_id}")
  |> filter(fn: (r) => r._field == "intensity")
  |> group(columns: ["emotion"])
  |> count()
```

### 3. Query Confidence Evolution
```flux
from(bucket: "performance_metrics")
  |> range(start: -2h)
  |> filter(fn: (r) => r._measurement == "confidence_evolution")
  |> filter(fn: (r) => r.bot == "${bot}")
  |> filter(fn: (r) => r.user_id == "${user_id}")
  |> filter(fn: (r) => r._field == "overall_confidence")
  |> aggregateWindow(every: 5m, fn: mean, createEmpty: false)
```

### 4. Query Conversation Quality
```flux
from(bucket: "performance_metrics")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "conversation_quality")
  |> filter(fn: (r) => r.bot == "${bot}")
  |> filter(fn: (r) => r.user_id == "${user_id}")
  |> filter(fn: (r) => r._field == "engagement_score" or r._field == "emotional_resonance" or r._field == "natural_flow_score")
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
```

### 5. Query Relationship Progression
```flux
from(bucket: "performance_metrics")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "relationship_progression")
  |> filter(fn: (r) => r.bot == "${bot}")
  |> filter(fn: (r) => r.user_id == "${user_id}")
  |> filter(fn: (r) => r._field == "trust_level" or r._field == "affection_level" or r._field == "attunement_level")
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
```

### 6. Query Performance Metrics (Coordination Time)
```flux
from(bucket: "performance_metrics")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "intelligence_coordination_metrics")
  |> filter(fn: (r) => r.bot == "${bot}")
  |> filter(fn: (r) => r._field == "coordination_time_ms")
  |> aggregateWindow(every: 2m, fn: mean, createEmpty: false)
```

### 7. Query Vector Memory Performance
```flux
from(bucket: "performance_metrics")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "vector_memory_performance")
  |> filter(fn: (r) => r.bot == "${bot}")
  |> filter(fn: (r) => r._field == "search_time_ms" or r._field == "memories_found" or r._field == "avg_relevance_score")
  |> aggregateWindow(every: 2m, fn: mean, createEmpty: false)
```

---

## Field Value Ranges

All confidence/score fields are **float 0.0-1.0**:
- `overall_confidence`, `user_fact_confidence`, `relationship_confidence`, etc.
- `trust_level`, `affection_level`, `attunement_level`, etc.
- `engagement_score`, `satisfaction_score`, `emotional_resonance`, etc.
- `intensity` (emotion intensity)
- `confidence` (detection confidence)
- `enthusiasm`, `stress`, `contentment`, `empathy` (character state)

Performance metrics use **milliseconds**:
- `coordination_time_ms`
- `analysis_time_ms`
- `search_time_ms`
- `query_time_ms`
- `load_time_ms`

---

## Deprecated / Removed Measurements

**DO NOT USE** - These measurements no longer exist:

- ❌ `response_time_v2` → Use `intelligence_coordination_metrics.coordination_time_ms`
- ❌ `optimization_ratio_v2` → No replacement (removed)
- ❌ `character_authenticity` → Never implemented
- ❌ `user_engagement` → Use `conversation_quality.engagement_score`
- ❌ `emotional_intelligence` → Use `bot_emotion`/`user_emotion`
- ❌ `character_consistency_v2` → Never existed
- ❌ `fidelity_score_v2` → Never existed
- ❌ `memory_quality_v2` → Never existed
- ❌ `performance_metrics` → Too generic, never existed

---

## Dashboard Variables

### Standard Variables for All Dashboards

```json
{
  "name": "bot",
  "type": "query",
  "datasource": "influxdb-whisperengine",
  "query": "import \"influxdata/influxdb/schema\"\nschema.tagValues(\n  bucket: \"performance_metrics\",\n  tag: \"bot\"\n)",
  "label": "Bot"
}
```

```json
{
  "name": "user_id",
  "type": "query",
  "datasource": "influxdb-whisperengine",
  "query": "import \"influxdata/influxdb/schema\"\nschema.tagValues(\n  bucket: \"performance_metrics\",\n  tag: \"user_id\",\n  predicate: (r) => r.bot == \"${bot}\"\n)",
  "label": "User ID"
}
```

---

## Validation

**Always validate dashboards** after making changes:

```bash
python3 scripts/validate_grafana_dashboards.py
```

This script checks:
- ✅ Measurement names match actual InfluxDB schema
- ✅ Field names are correct
- ✅ Tag names are documented
- ✅ No deprecated measurements used

---

## References

- **Implementation**: `src/temporal/temporal_intelligence_client.py` (lines 133-794)
- **Full Audit**: `docs/maintenance/GRAFANA_DASHBOARD_AUDIT_OCT_2025.md`
- **Working Dashboards**: `grafana_dashboards/character_emotional_evolution.json`
