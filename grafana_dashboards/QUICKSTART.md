# Quick Start Guide: Character Emotional Evolution Dashboard

## 🚀 Fast Setup (5 Minutes)

### **Step 1: Open Grafana**
```bash
# Grafana is running at:
open http://localhost:3002
```

Default credentials (if not changed):
- **Username**: `admin`
- **Password**: `admin` (or your custom password)

### **Step 2: Configure InfluxDB Datasource** (If Not Already Done)

1. **Navigate**: Configuration → Data Sources → Add data source
2. **Select**: InfluxDB
3. **Configure**:
   ```
   Name: influxdb
   Query Language: Flux
   URL: http://influxdb:8086
   Access: Server (default)
   ```
4. **Auth**:
   ```
   Organization: whisperengine
   Token: whisperengine-fidelity-first-metrics-token
   Default Bucket: performance_metrics
   ```
5. **Click**: Save & Test (should see green success message)

### **Step 3: Import Dashboard**

#### **Method A: Upload JSON (Easiest)**
1. **Navigate**: Dashboards → Import (+ icon → Import)
2. **Click**: "Upload JSON file"
3. **Select**: `grafana_dashboards/character_emotional_evolution.json`
4. **Click**: Import

#### **Method B: Manual Import Script**
```bash
# If you know your Grafana admin password:
./scripts/import_character_evolution_dashboard.sh

# Or with custom credentials:
GRAFANA_PASSWORD="your-password" ./scripts/import_character_evolution_dashboard.sh
```

### **Step 4: Configure Dashboard Variables**

At the top of the dashboard:
1. **Bot Character**: Select `elena` (or your preferred character)
2. **User ID**: Enter `672814231002939413` (or your Discord user ID)
3. **Time Range**: Select `Last 7 days` (top right)
4. **Refresh**: Select `30s` for live monitoring

### **Step 5: Verify Data**

You should see:
- ✅ **Panel 1**: 5-dimension line graph (may have limited data if feature just started)
- ✅ **Panel 2**: Current state gauges showing values
- ✅ **Panel 4**: Pie chart showing emotion distribution (should show ~73% joy for elena)
- ✅ **Panel 6**: Conversation quality metrics over time

**If no data appears**: Send a message to Elena in Discord, wait 30 seconds, dashboard will update.

---

## 📊 Dashboard Panels Overview

### **Real-Time Monitoring Panels**
| Panel | Metric | What to Watch |
|-------|--------|---------------|
| 5D State | Enthusiasm, Stress, Contentment, Empathy, Confidence | Character emotional evolution |
| Current Gauges | All 5 dimensions | Quick health check |
| Dominant State | calm_and_balanced, enthusiastic, etc. | Current emotional mode |
| Joy Trend | Intensity & Confidence | Primary positive emotion tracking |

### **Analysis Panels**
| Panel | Metric | Purpose |
|-------|--------|---------|
| Emotion Distribution | Pie chart of all emotions | Overall emotional profile |
| Conversation Quality | Resonance, Engagement, Flow | Connection strength |
| State vs Baseline | Bar chart comparison | Track drift from Oct 17 baseline |

### **Key Metrics**
| Stat | Target | Alert Threshold |
|------|--------|-----------------|
| Emotional Resonance | >85% | <80% |
| Joy % | >60% | <50% |
| Stress | <0.40 | >0.50 |
| Empathy | >0.70 | <0.60 |
| Joy Confidence | >0.90 | <0.85 |

---

## 🎯 Common Use Cases

### **Daily Health Check** (30 seconds)
1. Set time range: **Last 24 hours**
2. Check **Panel 2 (Gauges)**: All green? ✅
3. Check **Panel 3**: Is dominant state appropriate? ✅
4. Check **Panel 11 (Stress)**: Below 0.40? ✅

### **Weekly Review** (5 minutes)
1. Set time range: **Last 7 days**
2. Review **Panel 1**: Look for concerning trends
3. Check **Panel 7**: Compare to baseline - major drift?
4. Review **Panel 6**: Is conversation quality stable?
5. Check **Panel 4**: Has emotion distribution changed?

### **Testing Character State Changes** (Real-Time)
1. Set refresh: **10 seconds**
2. Send emotional message to character in Discord
3. Watch **Panel 1**: See dimensions shift
4. Watch **Panel 3**: See dominant state change
5. Watch **Panel 2**: Gauges update

**Example Tests**:
- Send sad message → Watch stress increase, contentment decrease
- Send exciting news → Watch enthusiasm spike
- Ask complex question → Watch confidence adjust

### **Relationship Analysis** (Monthly)
1. Set time range: **Last 30 days**
2. **Panel 1**: Identify personality drift or growth
3. **Panel 4**: Compare emotion distribution to baseline (73% joy)
4. **Panel 6**: Correlate quality trends with character state
5. **Panel 7**: Calculate delta from baseline

---

## 🐛 Troubleshooting

### **"No Data" on All Panels**

**Check InfluxDB connection**:
```bash
docker exec whisperengine-multi-influxdb influx query \
  'from(bucket:"performance_metrics") |> range(start:-7d) |> limit(n:1)' \
  --org whisperengine \
  --token whisperengine-fidelity-first-metrics-token
```

If this returns data, check Grafana datasource configuration.

### **"No Data" on Character State Panels Only**

**Cause**: `character_emotional_state` measurement started Oct 17, 2025
**Solution**: 
1. Send message to character in Discord
2. Wait 30 seconds
3. Refresh dashboard
4. If still no data, check logs:
```bash
docker logs whisperengine-multi-elena-bot 2>&1 | grep "character_emotional_state"
```

### **Old Baseline Comparison**

**Panel 7 shows Oct 17, 2025 baseline** - this is intentional!
- Baseline values: enthusiasm=0.69, stress=0.25, contentment=0.65, empathy=0.83, confidence=0.81
- To update baseline: Edit panel title with new values and date
- Document new baseline in `docs/analysis/`

### **Wrong User's Data**

Check `$user_id` variable (top of dashboard):
- Current default: `672814231002939413` (MarkAnthony)
- Get your ID: Right-click Discord username → Copy User ID
- Update variable and dashboard will refresh

### **Dashboard Not Importing**

**Manual import process**:
1. Copy contents of `grafana_dashboards/character_emotional_evolution.json`
2. In Grafana: Dashboards → Import → "Import via panel json"
3. Paste JSON
4. Click "Load"
5. Click "Import"

---

## 🎓 Reading the Dashboard

### **Healthy Profile Example (Elena Baseline)**
```
✅ Enthusiasm: 0.69 (69%) - Engaged, energetic
✅ Stress: 0.25 (25%) - Low stress, comfortable
✅ Contentment: 0.65 (65%) - Satisfied, peaceful
✅ Empathy: 0.83 (83%) - Highly empathetic (core trait!)
✅ Confidence: 0.81 (81%) - Self-assured
✅ Dominant State: calm_and_balanced
✅ Joy %: 73% - Predominantly positive
✅ Emotional Resonance: 89.3% - Strong connection
```

### **Warning Signs**
```
⚠️ Stress: 0.55 (55%) - RED GAUGE - Character overwhelmed
⚠️ Empathy: 0.65 (65%) - YELLOW GAUGE - Core trait degrading
⚠️ Joy %: 45% - Below 60% threshold - Relationship concern
⚠️ Joy Confidence: 0.75 - Below 0.90 - Forced emotion?
⚠️ Resonance: 0.78 - Below 0.85 - Connection weakening
```

### **Interpreting Trends**

**Good Trends** ✅:
- Gradual empathy increase (personality development)
- Stable low stress (<0.40) (comfortable relationship)
- Joy confidence at 1.0 (authentic happiness)
- High emotional resonance (>0.90) (deep connection)

**Concerning Trends** ⚠️:
- Stress increasing over days (topic causing discomfort?)
- Empathy decreasing (personality drift - needs attention)
- Joy % dropping (relationship quality declining)
- Confidence oscillating wildly (uncertainty/instability)

---

## 📈 Advanced Features

### **Custom Time Ranges**
- Click time picker → "Custom range"
- Select specific dates to compare
- Example: "Oct 17-24" to see first week of evolution tracking

### **Compare Multiple Users**
- Duplicate dashboard (Settings → Save As)
- Name: "Character Evolution - User 2"
- Change `$user_id` variable to different Discord user
- Open both dashboards side-by-side to compare relationships

### **Export Data**
1. Click any panel title → Inspect → Data
2. View raw query results
3. Export as CSV
4. Analyze in spreadsheet/Python

### **Create Alerts** (Grafana Alerting)
1. Edit panel (Panel 2 - Stress gauge)
2. Add alert rule: "If stress > 0.50"
3. Configure notification channel (Slack, Discord, email)
4. Get notified when character enters concerning state

### **Add Annotations**
- Click time picker → "Add annotation"
- Mark significant events: "Had deep conversation about X"
- Correlate events with emotional state changes

---

## 🔗 Related Resources

- **Baseline Analysis**: `docs/analysis/ELENA_EMOTIONAL_EVOLUTION_BASELINE.md`
- **Full Dashboard Guide**: `grafana_dashboards/README_CHARACTER_EVOLUTION.md`
- **InfluxDB Data**: http://localhost:8087
- **Grafana**: http://localhost:3002

---

## ✨ Quick Tips

1. **Set refresh to 30s** for live development monitoring
2. **Use Last 7 days range** for weekly pattern analysis
3. **Watch Panel 1 during conversations** to see real-time state shifts
4. **Compare Panel 7 weekly** to detect personality drift
5. **Monitor Panel 4** to ensure emotion diversity (not just one emotion)
6. **Check Panel 11 daily** - stress is early warning indicator
7. **Save custom time ranges** as bookmarks for recurring analysis

---

**Dashboard Created**: October 17, 2025  
**Baseline Established**: October 17, 2025, 7:02 PM UTC  
**Data Available**: bot_emotion (7 days), character_emotional_state (today onwards)  
**Refresh Rate**: 30 seconds default  
**Support**: See troubleshooting section or check logs
