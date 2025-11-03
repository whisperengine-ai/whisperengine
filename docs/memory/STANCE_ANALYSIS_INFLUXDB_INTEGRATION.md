# Stance Analyzer Integration - InfluxDB Metrics Update

## Summary

The stance analyzer has been fully integrated into WhisperEngine's metrics collection system. Emotion and stance analysis data is now automatically recorded to InfluxDB alongside performance metrics, enabling tracking of emotional attribution accuracy and bot character consistency.

## Changes Made

### 1. FidelityMetricsCollector Enhancement (`src/monitoring/fidelity_metrics_collector.py`)

#### New Method: `record_emotion_and_stance()`

Added comprehensive metrics recording for both user and bot emotions with stance analysis:

```python
def record_emotion_and_stance(
    self,
    user_id: str,
    operation: str,
    user_emotion: Optional[str] = None,
    user_emotion_confidence: float = 0.0,
    bot_emotion: Optional[str] = None,
    bot_emotion_confidence: float = 0.0,
    user_stance: Optional[str] = None,
    user_self_focus: float = 0.0,
    bot_stance: Optional[str] = None,
    bot_self_focus: float = 0.0,
    stance_confidence: float = 0.0
) -> None
```

**Purpose**: Records three separate InfluxDB metrics:
1. **User Emotion Metric** - primary emotion detected in user message with self-focus ratio
2. **Bot Emotion Metric** - primary emotion in bot response (after stance filtering)
3. **Stance Analysis Summary** - meta-metric tracking emotional attribution accuracy

**InfluxDB Fields**:
- `user_self_focus` - Ratio of self-focused emotions (0.0-1.0)
- `bot_self_focus` - Ratio of bot's self-focused emotions
- `stance_confidence` - Overall stance detection confidence
- `confidence` - Individual emotion confidence (RoBERTa)

**InfluxDB Tags**:
- `emotion_source` - "user" or "bot"
- `emotion_type` - Specific emotion (joy, anxiety, etc.)
- `stance_type` - "direct", "attributed", "mixed", or "none"
- `user_stance` / `bot_stance` - Overall stance classification

#### Convenience Function

Added module-level function for easy access:
```python
def record_emotion_and_stance(user_id, operation, user_emotion, ...)
```

### 2. Message Processor Integration (`src/core/message_processor.py`)

#### Location: Main Response Pipeline (Lines ~1547-1557)

Added emotion and stance metrics recording after performance metrics:

```python
# 🎯 STANCE METRICS: Record emotion and stance analysis data
try:
    user_emotion = ai_components.get('emotion_data', {}).get('primary_emotion')
    user_emotion_confidence = ai_components.get('emotion_data', {}).get('confidence', 0.0)
    
    bot_emotion = ai_components.get('bot_emotion', {}).get('primary_emotion')
    bot_emotion_confidence = ai_components.get('bot_emotion', {}).get('confidence', 0.0)
    
    # Get stance analysis from message processor state
    user_stance = getattr(user_stance_analysis, 'emotion_type', None)
    user_self_focus = getattr(user_stance_analysis, 'self_focus', 0.0)
    
    if user_emotion or bot_emotion:
        self.fidelity_metrics.record_emotion_and_stance(...)
except Exception as e:
    logger.debug(f"Failed to record emotion/stance metrics: {e}")
```

**Data Source**: Extracts from `ai_components` dict:
- `ai_components['emotion_data']` - User emotion from RoBERTa analysis
- `ai_components['bot_emotion']` - Bot emotion from filtered response
- `user_stance_analysis` - Stance object from Phase 2.75 early analysis

**Error Handling**: Gracefully handles missing data without blocking message processing

### 3. Data Flow Architecture

```
┌─────────────────────────────────────────────────────┐
│         User Message + Bot Response                  │
└──────────────┬──────────────────────────────────────┘
               │
               ├─→ Phase 2.75: Stance Analysis
               │   ├─→ analyze_user_stance()
               │   └─→ user_stance_analysis: StanceAnalysis
               │
               ├─→ Phase 3-6: Emotional Analysis + Response
               │   ├─→ RoBERTa (user emotion)
               │   ├─→ Bot generation (bot emotion)
               │   └─→ filter_second_person_emotions()
               │
               └─→ Performance Metrics Recording
                   ├─→ record_performance_metric()
                   │   ├─ Processing time
                   │   ├─ LLM timing
                   │   └─ Memory counts
                   │
                   └─→ record_emotion_and_stance() ← NEW
                       ├─ User emotion + self-focus
                       ├─ Bot emotion + self-focus
                       └─ Stance confidence
                           │
                           └─→ InfluxDB
```

## InfluxDB Schema

### Measurements

Three measurements are recorded for each message:

#### 1. Fidelity Score (User Emotion)
- **Measurement**: `fidelity_score_v2`
- **Value**: user_emotion_confidence (0.0-1.0)
- **Tags**: 
  - `bot_name`: Character bot name
  - `operation`: "message_processing_user_emotion"
  - `emotion_source`: "user"
  - `emotion_type`: Specific emotion
  - `stance_type`: Stance classification
- **Fields**:
  - `user_self_focus`: Self-focus ratio
  - `confidence`: RoBERTa confidence

#### 2. Fidelity Score (Bot Emotion)
- **Measurement**: `fidelity_score_v2`
- **Value**: bot_emotion_confidence (0.0-1.0)
- **Tags**:
  - `bot_name`: Character bot name
  - `operation`: "message_processing_bot_emotion"
  - `emotion_source`: "bot"
  - `emotion_type`: Specific emotion
  - `stance_type`: Stance classification
- **Fields**:
  - `bot_self_focus`: Self-focus ratio
  - `confidence`: RoBERTa confidence

#### 3. Character Consistency (Stance Analysis)
- **Measurement**: `character_consistency_v2`
- **Value**: stance_confidence (0.0-1.0)
- **Tags**:
  - `bot_name`: Character bot name
  - `operation`: "message_processing_stance_analysis"
  - `user_stance`: User stance type
  - `bot_stance`: Bot stance type
- **Fields**:
  - `user_self_focus`: User self-focus ratio
  - `bot_self_focus`: Bot self-focus ratio
  - `stance_confidence`: Detection confidence

## Query Examples

### Query 1: User vs Bot Emotional Dynamics Over Time

```flux
from(bucket: "performance_metrics")
  |> range(start: -24h)
  |> filter(fn: (r) => r["_measurement"] == "fidelity_score_v2")
  |> filter(fn: (r) => r["emotion_source"] == "user" or r["emotion_source"] == "bot")
  |> filter(fn: (r) => r["bot_name"] == "elena")
  |> aggregateWindow(every: 1h, fn: mean, createEmpty: false)
  |> group(by: ["emotion_source"])
```

### Query 2: Stance Detection Accuracy

```flux
from(bucket: "performance_metrics")
  |> range(start: -7d)
  |> filter(fn: (r) => r["_measurement"] == "character_consistency_v2")
  |> filter(fn: (r) => r["operation"] == "message_processing_stance_analysis")
  |> filter(fn: (r) => r["bot_name"] == "elena")
  |> aggregateWindow(every: 1d, fn: mean, createEmpty: false)
```

### Query 3: Self-Focus Ratio Trends

```flux
from(bucket: "performance_metrics")
  |> range(start: -30d)
  |> filter(fn: (r) => r["_measurement"] == "character_consistency_v2")
  |> filter(fn: (r) => r["bot_name"] == "elena")
  |> group(by: ["user_stance", "bot_stance"])
  |> map(fn: (r) => ({r with user_self_focus: float(v: r["user_self_focus"]), bot_self_focus: float(v: r["bot_self_focus"])}))
  |> aggregateWindow(every: 1d, fn: mean, createEmpty: false)
```

## Grafana Dashboard Integration

Recommended dashboard visualizations:

1. **User vs Bot Emotion Confidence** (Time series)
   - Measurement: fidelity_score_v2
   - Split by: emotion_source

2. **Stance Type Distribution** (Pie chart)
   - Measurement: character_consistency_v2
   - Group by: user_stance, bot_stance

3. **Self-Focus Ratios** (Line chart)
   - Measurement: character_consistency_v2
   - Y-axis: user_self_focus, bot_self_focus
   - Query: Time windowed averages

4. **Emotion Distribution by User** (Bar chart)
   - Measurement: fidelity_score_v2
   - Filter: emotion_source="user"
   - Group by: emotion_type

## Benefits

### 1. Emotional Attribution Accuracy Tracking
- Monitor if bot correctly identifies user emotions
- Detect when bot misattributes emotions (attribution errors)
- Track improvement over time

### 2. Bot Character Consistency
- Verify bot responses reflect genuine emotions
- Track if empathetic echoing is being filtered out
- Monitor bot personality consistency

### 3. Conversation Quality Analysis
- Correlate stance accuracy with user satisfaction
- Identify patterns in emotional conversations
- Optimize character responses based on stance patterns

### 4. Performance vs Quality Trade-offs
- See if stance filtering impacts response time
- Monitor fidelity preservation with filtering
- Track memory retrieval quality with stance context

## Testing & Validation

### Integration Test
Run: `python tests/automated/test_stance_integration.py`

### InfluxDB Verification
```bash
# Connect to InfluxDB
docker exec -it whisperengine-influxdb influx

# Query recent emotion metrics
from(bucket: "performance_metrics")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "fidelity_score_v2")
  |> filter(fn: (r) => r["emotion_source"] == "user")
  |> limit(n: 100)
```

### Check Message Processor Logs
```bash
./multi-bot.sh logs elena-bot 2>&1 | grep "EMOTION/STANCE METRICS"
```

## Migration Notes

### Backward Compatibility
✅ **Fully backward compatible**
- All changes are additive
- Existing metrics recording continues unchanged
- Emotion/stance recording is optional based on data availability
- Graceful degradation if stance analyzer unavailable

### No Breaking Changes
- No existing InfluxDB schemas modified
- No changes to existing metrics recording
- No impact on message processing if stance data missing
- Silent failures logged as debug messages

## Future Enhancements

1. **Temporal Patterns**: Track how stance affects conversation flow over multiple messages
2. **User Profiling**: Identify users with consistent stance patterns
3. **Bot Learning**: Use stance accuracy as signal for character fine-tuning
4. **Anomaly Detection**: Alert on unusual emotion/stance combinations
5. **Multi-bot Comparison**: Compare stance accuracy across 12+ character bots

## Related Files

- `src/intelligence/spacy_stance_analyzer.py` - Core stance analyzer
- `src/core/message_processor.py` - Message processing integration
- `src/memory/vector_memory_system.py` - Qdrant storage with stance fields
- `src/monitoring/fidelity_metrics_collector.py` - Metrics recording
- `tests/automated/test_spacy_stance_analyzer.py` - Unit tests
- `tests/automated/test_stance_integration.py` - Integration tests

## Conclusion

Stance analysis is now fully integrated into WhisperEngine's telemetry pipeline. Emotional attribution accuracy and bot character consistency can now be monitored in real-time via InfluxDB and Grafana dashboards.
