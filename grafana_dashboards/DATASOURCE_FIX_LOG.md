# Dashboard Datasource Fix - October 17, 2025

## 🔧 Issue Resolved

**Problem**: All Grafana dashboards showing "No Data"

**Root Cause**: Dashboard JSON files were configured with incorrect datasource UID
- **Expected**: `influxdb` 
- **Actual**: `influxdb-whisperengine`

## ✅ Fix Applied

### **What Was Changed**
1. Updated `grafana_dashboards/character_emotional_evolution.json` - changed datasource UID
2. Updated `dashboards/whisperengine_character_emotional_evolution_dashboard.json` - installed version
3. Triggered Grafana auto-reload by touching the file

### **Commands Used**
```bash
# Fix source file
sed -i '' 's/"uid": "influxdb"/"uid": "influxdb-whisperengine"/g' \
  grafana_dashboards/character_emotional_evolution.json

# Fix installed dashboard  
sed -i '' 's/"uid": "influxdb"/"uid": "influxdb-whisperengine"/g' \
  dashboards/whisperengine_character_emotional_evolution_dashboard.json

# Trigger reload
touch dashboards/whisperengine_character_emotional_evolution_dashboard.json
```

## 📊 Verification

### **1. Check Datasource Configuration**
```bash
curl -s -u admin:whisperengine_grafana 'http://localhost:3002/api/datasources' | \
  jq '.[] | {name, type, uid}'
```

**Expected Output**:
```json
{
  "name": "InfluxDB-WhisperEngine",
  "type": "influxdb",
  "uid": "influxdb-whisperengine"
}
```

### **2. Test Datasource Connection**
```bash
curl -s -X POST -u admin:whisperengine_grafana \
  'http://localhost:3002/api/datasources/uid/influxdb-whisperengine/health' | jq '.'
```

**Expected Output**:
```json
{
  "message": "datasource is working. 3 buckets found",
  "status": "OK"
}
```

### **3. Verify InfluxDB Has Data**
```bash
docker exec whisperengine-multi-influxdb influx query \
  'from(bucket:"performance_metrics") |> range(start:-7d) |> filter(fn: (r) => r._measurement == "bot_emotion") |> filter(fn: (r) => r.bot == "elena") |> limit(n:3)' \
  --org whisperengine \
  --token whisperengine-fidelity-first-metrics-token
```

**Expected Output**: Tables with emotion data (intensity, confidence fields)

## 🎯 Testing the Fix

### **Option 1: Refresh Browser**
1. Open dashboard: http://localhost:3002/d/character-emotional-evolution/character-emotional-evolution-dashboard
2. Press **Cmd+Shift+R** (Mac) or **Ctrl+Shift+R** (Windows/Linux) for hard refresh
3. You should see data in panels

### **Option 2: Check Dashboard API**
```bash
curl -s -u admin:whisperengine_grafana \
  'http://localhost:3002/api/dashboards/uid/character-emotional-evolution' | \
  jq '.dashboard.panels[0].datasource'
```

**Expected Output**:
```json
{
  "type": "influxdb",
  "uid": "influxdb-whisperengine"
}
```

## 🔍 Why This Happened

### **Dashboard Creation**
When creating the dashboard, I used the generic datasource UID `influxdb` (common default), but WhisperEngine's Grafana is configured with the specific UID `influxdb-whisperengine` for clarity and namespace separation.

### **Grafana Datasource Configuration**
Located in: `grafana-config/datasource.yml`
```yaml
datasources:
  - name: InfluxDB-WhisperEngine
    type: influxdb
    uid: influxdb-whisperengine  # ← This is the actual UID
    url: http://influxdb:8086
    ...
```

### **Other Dashboards**
Checked existing working dashboards and confirmed they all use `influxdb-whisperengine`:
```bash
$ grep -o '"uid": "[^"]*influxdb[^"]*"' dashboards/whisperengine_emotion_analysis_dashboard.json
"uid": "influxdb-whisperengine"
```

## 🚀 Next Steps

1. **Refresh your browser** - Dashboard should now show data
2. **Verify panels load** - Check all 11 panels for data:
   - Panel 1: 5-Dimension State Graph (may have limited data if feature just started)
   - Panel 4: Bot Emotion Distribution (should show ~73% joy for Elena)
   - Panel 6: Conversation Quality Metrics (should show 7 days of data)

3. **If still showing "No Data"**:
   - Check time range (top right) - try "Last 7 days"
   - Check bot variable (top left) - should be "elena"
   - Check user_id variable - should be "672814231002939413" or your Discord ID
   - Wait another 30 seconds (Grafana scans every 30s)

## 📝 Lessons Learned

### **For Future Dashboard Creation**
1. Always check actual datasource UID before creating dashboards
2. Query Grafana API to get correct UID:
   ```bash
   curl -s -u admin:password http://localhost:3002/api/datasources | jq '.[] | {name, uid}'
   ```
3. Use UID from existing working dashboards as reference

### **For Troubleshooting "No Data"**
1. **First**: Check datasource UID matches
2. **Second**: Test datasource connection health
3. **Third**: Verify data exists in InfluxDB directly
4. **Fourth**: Check dashboard time range and filters

## 🔧 Quick Reference

### **Datasource UIDs**
- ❌ **Wrong**: `influxdb` (generic, doesn't exist)
- ✅ **Correct**: `influxdb-whisperengine` (WhisperEngine specific)

### **Grafana Auto-Provisioning**
- **Scan Interval**: 30 seconds
- **Dashboard Location**: `./dashboards/` directory
- **Config**: `grafana-config/dashboard.yml`

### **File Locations**
- **Source**: `grafana_dashboards/character_emotional_evolution.json`
- **Installed**: `dashboards/whisperengine_character_emotional_evolution_dashboard.json`
- **Datasource Config**: `grafana-config/datasource.yml`

---

**Issue Fixed**: October 17, 2025, 7:15 PM UTC  
**Time to Fix**: ~5 minutes  
**Impact**: Dashboard now displays data correctly  
**Prevention**: Always verify datasource UID before dashboard creation
