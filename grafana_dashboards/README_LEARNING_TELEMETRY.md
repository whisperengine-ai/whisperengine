# Learning System Telemetry Dashboard

## Overview

This Grafana dashboard visualizes telemetry data from WhisperEngine's learning systems and experimental features added in Enhancement Sprint (Enhancements #4, #5, #6).

## Dashboard Sections

### 1. **Attachment Monitor Metrics** (InfluxDB - Active)
- **Risk Level Distribution**: Pie chart showing LOW/MEDIUM/HIGH risk user distribution
- **Emotional Intensity Trends**: Time series of emotional attachment intensity
- **Intervention Count**: Stat showing attachment interventions provided
- **Interaction Frequency**: User message frequency tracking
- **Consecutive Days**: Streak tracking per user

### 2. **Experimental Features** (Logging-Based - Pending InfluxDB Integration)
- **ProactiveConversationEngagementEngine**: Enhancement #5 telemetry status
- **TrustRecoverySystem**: Enhancement #6 telemetry status
- **Learning Components**: Enhancement #4 telemetry status (8 components)

## Current Status

### ✅ Fully Tracked (InfluxDB)
- **AttachmentMonitor**: Complete InfluxDB integration
  - Measurement: `attachment_monitoring`
  - Tags: `user_id`, `bot_name`, `risk_level`
  - Fields: `emotional_intensity`, `interaction_frequency`, `dependency_count`, `consecutive_days`, `intervention_provided`

### 🔄 Logging-Based (Pending InfluxDB)
The following components have telemetry via INFO-level logging, ready for InfluxDB integration:

**Enhancement #4: Learning Components**
1. CharacterGraphKnowledgeBuilder
2. CharacterGraphKnowledgeIntelligence
3. CharacterInsightStorage
4. CharacterLearningMomentDetector
5. CharacterSelfKnowledgeExtractor
6. CharacterTemporalEvolutionAnalyzer
7. CharacterVectorEpisodicIntelligence

**Enhancement #5: EngagementEngine**
- ProactiveConversationEngagementEngine

**Enhancement #6: Trust Recovery**
- TrustRecoverySystem

## Installation

### 1. Import Dashboard to Grafana

```bash
# Using Grafana API (recommended)
curl -X POST http://localhost:3002/api/dashboards/db \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d @grafana_dashboards/learning_system_telemetry.json

# OR: Import via Grafana UI
# 1. Navigate to Grafana (http://localhost:3002)
# 2. Click "+" → "Import"
# 3. Upload learning_system_telemetry.json
# 4. Select InfluxDB datasource (uid: "influxdb")
# 5. Click "Import"
```

### 2. Verify InfluxDB Datasource

Ensure InfluxDB datasource is configured:
- **Name**: InfluxDB
- **UID**: `influxdb`
- **URL**: `http://influxdb:8086`
- **Organization**: `whisperengine`
- **Token**: (configured in docker-compose)
- **Default Bucket**: `whisperengine`

## Extending with InfluxDB Integration

To add InfluxDB tracking to the logging-based telemetry components:

### Pattern 1: Periodic Telemetry Write (Recommended)

```python
# Add to component __init__
from influxdb_client import Point

# Add periodic flush method
async def _flush_telemetry_to_influxdb(self):
    """Write current telemetry counters to InfluxDB."""
    if not self.temporal_client:
        return
        
    try:
        point = Point("engagement_engine_telemetry") \
            .tag("component", "ProactiveConversationEngagementEngine") \
            .field("analyze_engagement_potential_count", self._telemetry['analyze_engagement_potential_count']) \
            .field("analyze_conversation_engagement_count", self._telemetry['analyze_conversation_engagement_count']) \
            .field("interventions_generated", self._telemetry['interventions_generated']) \
            .field("total_recommendations", self._telemetry['total_recommendations'])
        
        await self.temporal_client.write_point(point)
        logger.info("📊 Flushed telemetry to InfluxDB")
        
    except Exception as e:
        logger.error(f"Error flushing telemetry: {e}")
```

### Pattern 2: Event-Based Write

```python
# Write on significant events
async def analyze_engagement_potential(self, ...):
    # ... existing code ...
    
    # After telemetry increment
    if self.temporal_client and self._telemetry['analyze_engagement_potential_count'] % 10 == 0:
        await self._flush_telemetry_to_influxdb()
```

### Pattern 3: Scheduled Background Task

```python
# In bot initialization (src/core/bot.py)
async def _start_telemetry_flush_task(self):
    """Background task to flush telemetry every 5 minutes."""
    while True:
        await asyncio.sleep(300)  # 5 minutes
        
        # Flush all component telemetry
        if hasattr(self, 'engagement_engine'):
            await self.engagement_engine._flush_telemetry_to_influxdb()
        
        if hasattr(self, 'trust_recovery_system'):
            await self.trust_recovery_system._flush_telemetry_to_influxdb()
```

## Dashboard Customization

### Adding New Panels

To add panels for newly InfluxDB-enabled components:

```json
{
  "id": 9,
  "title": "🚀 Engagement Engine - Analysis Invocations",
  "type": "timeseries",
  "gridPos": {"h": 8, "w": 12, "x": 0, "y": 28},
  "targets": [{
    "refId": "A",
    "datasource": {"type": "influxdb", "uid": "influxdb"},
    "query": "from(bucket: \"whisperengine\")\n  |> range(start: -24h)\n  |> filter(fn: (r) => r[\"_measurement\"] == \"engagement_engine_telemetry\")\n  |> filter(fn: (r) => r[\"_field\"] == \"analyze_engagement_potential_count\")\n  |> aggregateWindow(every: 10m, fn: mean, createEmpty: false)"
  }],
  "fieldConfig": {
    "defaults": {
      "unit": "short",
      "custom": {"drawStyle": "line", "lineInterpolation": "smooth"}
    }
  }
}
```

## Measurements Reference

### Current Measurements
- `attachment_monitoring`: Attachment risk tracking
- `vector_classification`: Multi-vector routing intelligence
- `character_emotional_evolution`: Emotional state tracking

### Pending Measurements (Ready to Add)
- `engagement_engine_telemetry`: ProactiveConversationEngagementEngine metrics
- `trust_recovery_telemetry`: TrustRecoverySystem metrics
- `character_graph_builder_telemetry`: Knowledge graph building
- `character_insight_storage_telemetry`: Insight persistence
- `learning_moment_detector_telemetry`: Learning opportunity detection
- `self_knowledge_extractor_telemetry`: Bot self-knowledge extraction
- `temporal_evolution_telemetry`: Character trait evolution
- `episodic_intelligence_telemetry`: Episodic memory tracking

## Monitoring Best Practices

1. **Start with AttachmentMonitor**: Fully instrumented example to follow
2. **Incremental InfluxDB Integration**: Add one component at a time
3. **Test Before Production**: Verify InfluxDB writes in development
4. **Monitor Cardinality**: Be cautious with high-cardinality tags (like `user_id`)
5. **Use Aggregations**: Apply `aggregateWindow()` for large time ranges
6. **Set Retention Policies**: Configure InfluxDB retention for telemetry data

## Troubleshooting

### Dashboard Shows No Data

1. **Check InfluxDB Connection**:
   ```bash
   docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml logs influxdb
   ```

2. **Verify Bucket Exists**:
   ```bash
   docker exec -it influxdb influx bucket list
   ```

3. **Check Data Exists**:
   ```flux
   from(bucket: "whisperengine")
     |> range(start: -1h)
     |> filter(fn: (r) => r["_measurement"] == "attachment_monitoring")
     |> limit(n: 10)
   ```

4. **Verify Datasource UID**:
   - Dashboard expects datasource UID: `influxdb`
   - Check in Grafana → Configuration → Data Sources

### Panels Show "No Data"

- **AttachmentMonitor not running**: Check if bot is processing messages
- **InfluxDB writes disabled**: Verify `temporal_client` is configured
- **Time range too narrow**: Adjust dashboard time range (top right)

## Future Enhancements

1. **Add alerting rules** for attachment risk thresholds
2. **Create composite metrics** (e.g., learning efficiency ratio)
3. **Add user-specific drill-downs** (click pie chart → user detail panel)
4. **Integrate with Prometheus** for infrastructure metrics correlation
5. **Add SLO tracking** for experimental feature adoption

## Related Documentation

- `docs/roadmaps/QUICK_ENHANCEMENT_WINS_TRACKER.md`: Enhancement sprint status
- `grafana_dashboards/vector_classification_intelligence.json`: Multi-vector routing dashboard
- `grafana_dashboards/character_emotional_evolution.json`: Emotional state tracking
- `src/relationships/trust_recovery.py`: Trust recovery implementation
- `src/conversation/proactive_engagement_engine.py`: Engagement engine implementation
