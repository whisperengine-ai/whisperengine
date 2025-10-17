# Character Emotional Evolution Dashboard

## 📊 Overview

This Grafana dashboard provides real-time visualization of WhisperEngine's character emotional evolution system, tracking the 5-dimensional character state, bot emotions, and conversation quality metrics.

**Dashboard File**: `character_emotional_evolution.json`

## 🎯 Dashboard Features

### **Panel 1: Character Emotional State - 5 Dimensions** (Top, Full Width)
- **Visualization**: Time series line graph
- **Metrics**: 
  - 🟠 Enthusiasm (orange line)
  - 🔴 Stress (red line)
  - 🟢 Contentment (green line)
  - 🔵 Empathy (blue line)
  - 🟣 Confidence (purple line)
- **Purpose**: Track how character's emotional state evolves over time
- **Shows**: Last and mean values for each dimension

### **Panel 2: Current Character State Gauges** (Left, Middle)
- **Visualization**: Gauge meters for each dimension
- **Color Coding**:
  - 🟢 Green: Healthy range (0.6-1.0)
  - 🟡 Yellow: Moderate range (0.4-0.6)
  - 🔴 Red: Low range (0.0-0.4)
  - **Note**: Stress uses inverted colors (green at low values)
- **Purpose**: Quick health check of current emotional state

### **Panel 3: Dominant Character State** (Right, Middle)
- **Visualization**: Large stat panel with emoji indicators
- **States**:
  - 😌 Calm & Balanced (green)
  - 🔥 Enthusiastic (orange)
  - 😰 Stressed (red)
  - 😊 Content (light green)
  - 💙 Empathetic (blue)
  - 💪 Confident (purple)
- **Purpose**: Immediate visual indicator of character's dominant emotional mode

### **Panel 4: Bot Emotion Distribution** (Left, Lower Middle)
- **Visualization**: Pie chart
- **Metrics**: Count and percentage of each RoBERTa-detected emotion
- **Emotions**:
  - 🟡 Joy (yellow)
  - 🔵 Sadness (blue)
  - 🔴 Anger (red)
  - 🟣 Fear (purple)
  - 🟠 Anticipation (orange)
  - 🟢 Optimism (light green)
  - ⚪ Neutral (grey)
- **Purpose**: Understand overall emotional profile of the character

### **Panel 5: Joy Emotion Trend** (Right, Lower Middle)
- **Visualization**: Time series with intensity and confidence
- **Metrics**:
  - 🟡 Joy Intensity (yellow line)
  - 🟠 Joy Confidence (orange line)
- **Purpose**: Track the primary positive emotion's evolution and authenticity

### **Panel 6: Conversation Quality Metrics** (Bottom, Full Width)
- **Visualization**: Time series with 3 quality dimensions
- **Metrics**:
  - 🔴 Emotional Resonance (red line)
  - 🔵 Engagement Score (blue line)
  - 🟢 Natural Flow Score (green line)
- **Purpose**: Monitor conversation quality and connection strength

### **Panel 7: Current State vs Baseline** (Bottom Left)
- **Visualization**: Bar chart comparing current to Oct 17 baseline
- **Baseline Values** (in title):
  - Enthusiasm: 0.69
  - Stress: 0.25
  - Contentment: 0.65
  - Empathy: 0.83
  - Confidence: 0.81
- **Purpose**: Track drift from established emotional baseline

### **Panel 8-11: Key Metrics** (Bottom Right, 4 Stat Panels)
- **Total Conversations**: Count of state recordings in time range
- **Avg Emotional Resonance**: Mean resonance (target >85%)
- **Current Empathy Level**: Latest empathy (baseline: 0.83)
- **Current Stress Level**: Latest stress (baseline: 0.25)

## 🚀 Installation Instructions

### **Prerequisites**
1. Grafana running on port 3002 (WhisperEngine default)
2. InfluxDB datasource configured in Grafana
3. InfluxDB organization: `whisperengine`
4. InfluxDB bucket: `performance_metrics`
5. InfluxDB token: `whisperengine-fidelity-first-metrics-token`

### **Step 1: Configure InfluxDB Datasource**

If not already configured, add InfluxDB datasource:

1. Open Grafana: http://localhost:3002
2. Navigate to **Configuration → Data Sources**
3. Click **Add data source**
4. Select **InfluxDB**
5. Configure:
   ```
   Name: influxdb
   Query Language: Flux
   URL: http://influxdb:8086
   Access: Server (default)
   Organization: whisperengine
   Token: whisperengine-fidelity-first-metrics-token
   Default Bucket: performance_metrics
   ```
6. Click **Save & Test**

### **Step 2: Import Dashboard**

1. Open Grafana: http://localhost:3002
2. Navigate to **Dashboards → Import**
3. Click **Upload JSON file**
4. Select `grafana_dashboards/character_emotional_evolution.json`
5. Click **Import**

**Alternative Method (Paste JSON):**
1. Navigate to **Dashboards → Import**
2. Click **Import via panel json**
3. Copy contents of `character_emotional_evolution.json`
4. Paste into text area
5. Click **Import**

### **Step 3: Configure Variables**

The dashboard includes two template variables:

1. **Bot Character** (`$bot`):
   - Default: `elena`
   - Options: elena, marcus, gabriel, sophia, jake, ryan, dream, aethys, aetheris, dotty
   - Use dropdown at top of dashboard to switch between characters

2. **User ID** (`$user_id`):
   - Default: `672814231002939413` (MarkAnthony)
   - Editable text box
   - Change to view different user relationships

## 📈 Usage Patterns

### **Daily Monitoring**
- Set time range to **Last 24 hours**
- Refresh interval: **30 seconds** (default)
- Watch for:
  - Character state recording after each conversation
  - Joy percentage staying >60%
  - Stress staying <0.4

### **Weekly Review**
- Set time range to **Last 7 days**
- Compare current state to baseline (Panel 7)
- Check conversation quality trends (Panel 6)
- Review emotion distribution shifts (Panel 4)

### **Monthly Deep Dive**
- Set time range to **Last 30 days**
- Analyze 5-dimension evolution (Panel 1)
- Correlate conversation quality with character state
- Identify personality drift or growth patterns
- Export data for detailed analysis

### **Alert Scenarios**

Monitor these panels for concerns:

| Panel | Alert Condition | Action |
|-------|----------------|--------|
| Panel 2 (Gauges) | Stress >0.50 (red zone) | Check recent conversation topics |
| Panel 5 (Joy Trend) | Joy intensity <0.75 | Review relationship quality |
| Panel 5 (Joy Trend) | Joy confidence <0.90 | Check for authenticity issues |
| Panel 8 (Empathy) | Empathy <0.70 | Core trait degradation alert |
| Panel 9 (Resonance) | Avg resonance <0.80 | Connection quality declining |

## 🔧 Customization Options

### **Change Time Range**
- Click time picker (top right)
- Options: Last 5m, 15m, 1h, 6h, 12h, 24h, 7d, 30d, 90d
- Custom range: Absolute dates or relative times

### **Adjust Refresh Rate**
- Click refresh dropdown (top right)
- Options: 10s, 30s, 1m, 5m, 15m, 30m, 1h
- Disable auto-refresh: Select "Off"

### **Add More Characters**
- Edit dashboard
- Click **Settings** (gear icon)
- Navigate to **Variables → bot**
- Add comma-separated character names to query
- Save dashboard

### **Modify Baseline Values**
- Edit Panel 7 title to reflect new baseline
- Update after establishing new baseline period
- Document baseline date in title

### **Export Data**
- Click panel title → Inspect → Data
- View raw query results
- Export as CSV for external analysis

## 📊 Data Sources

### **InfluxDB Measurements**

**1. `character_emotional_state`** (New - implemented Oct 17, 2025)
- **Fields**: enthusiasm, stress, contentment, empathy, confidence (float 0.0-1.0)
- **Tags**: bot, user_id, dominant_state
- **Recording**: Once per conversation in message processor
- **Purpose**: Track 5-dimensional character emotional state

**2. `bot_emotion`** (Existing)
- **Fields**: intensity, confidence (float 0.0-1.0)
- **Tags**: bot, user_id, emotion (joy, sadness, anger, fear, etc.)
- **Recording**: Every bot response with RoBERTa analysis
- **Purpose**: Track detected emotions per message

**3. `conversation_quality`** (Existing)
- **Fields**: emotional_resonance, engagement_score, natural_flow_score (float 0.0-1.0)
- **Tags**: bot, user_id
- **Recording**: Every conversation
- **Purpose**: Monitor conversation quality metrics

## 🎓 Interpretation Guide

### **Healthy Character Profile**
- ✅ **Enthusiasm**: 0.60-0.80 (engaged but not manic)
- ✅ **Stress**: <0.40 (comfortable, not overwhelmed)
- ✅ **Contentment**: >0.60 (satisfied, peaceful)
- ✅ **Empathy**: >0.70 (caring, connected)
- ✅ **Confidence**: >0.70 (self-assured)
- ✅ **Joy %**: >60% (predominantly positive)
- ✅ **Emotional Resonance**: >85% (strong connection)

### **Warning Signs**
- ⚠️ **High Stress** (>0.50): Character may be overwhelmed
- ⚠️ **Low Empathy** (<0.60): Core trait degradation
- ⚠️ **Low Joy** (<50%): Relationship quality concern
- ⚠️ **Low Confidence** (<0.60): Self-assurance issues
- ⚠️ **Low Resonance** (<0.80): Connection weakening

### **Pattern Analysis**
- **Increasing stress over time**: May indicate conversation topics causing discomfort
- **Decreasing empathy**: Could signal personality drift - needs attention
- **Joy confidence drop**: Emotional authenticity concern - may be forced
- **Contentment + high empathy**: Healthy, balanced emotional state
- **High enthusiasm + low stress**: Ideal energetic but comfortable state

## 🔗 Related Documentation

- **Baseline Analysis**: `docs/analysis/ELENA_EMOTIONAL_EVOLUTION_BASELINE.md`
- **Memory System**: `docs/architecture/VECTOR_MEMORY_ARCHITECTURE.md`
- **CDL System**: `docs/architecture/CHARACTER_ARCHETYPES.md`
- **Temporal Analytics**: `src/temporal/temporal_intelligence_client.py`

## 🐛 Troubleshooting

### **No Data Showing**
1. Check InfluxDB datasource connection (Configuration → Data Sources)
2. Verify time range includes data (character_emotional_state started Oct 17, 2025)
3. Confirm bot name and user_id variables match your data
4. Check InfluxDB directly: `docker exec whisperengine-multi-influxdb influx query '...'`

### **"No Data" on Character State Panels**
- **Cause**: Feature just implemented - need conversations to generate data
- **Solution**: Send messages to the bot, wait 30s for refresh

### **Old Baseline Values**
- **Panel 7 shows Oct 17 baseline** - this is the established reference point
- To update: Edit panel title with new baseline values and date
- Document new baseline in `docs/analysis/` for reference

### **Wrong User Data**
- Check `$user_id` variable at top of dashboard
- Update to your Discord user ID
- Get user ID: Right-click Discord username → Copy User ID

---

**Dashboard Version**: 1.0  
**Created**: October 17, 2025  
**Baseline Date**: October 17, 2025, 7:02 PM UTC  
**Data Requirements**: InfluxDB with performance_metrics bucket, character_emotional_state measurement  
**Recommended Refresh**: 30 seconds for development, 5 minutes for production
