# Import Learning System Telemetry Dashboard - Quick Guide

## 📊 Manual Import (Recommended - 2 minutes)

### Step 1: Open Grafana
```bash
open http://localhost:3002
```

**Login Credentials:**
- Username: `admin`
- Password: `admin` (or your custom password)

### Step 2: Import Dashboard

1. **Click** the "+" icon in the left sidebar (or "Dashboards" → "New" → "Import")
2. **Click** "Upload JSON file" button
3. **Select** the file: `grafana_dashboards/learning_system_telemetry.json`
4. **Configure Import**:
   - Name: `Learning System Telemetry & Experimental Features` (pre-filled)
   - Folder: `General` (or choose a folder)
   - **IMPORTANT**: Select the InfluxDB datasource from the dropdown
     - Should show datasource with UID: `influxdb`
5. **Click** "Import"

### Step 3: Verify Dashboard

The dashboard should now appear with:
- ✅ Attachment Monitor metrics (if data exists)
- ℹ️ Info panels for experimental features (EngagementEngine, TrustRecovery)
- 📚 Learning components telemetry status

---

## 🔧 Troubleshooting

### "No Data" or Panels Empty

**Cause 1: InfluxDB Datasource Not Configured**
1. Go to Configuration → Data Sources
2. Add InfluxDB datasource:
   - **Name**: `influxdb` (must match exactly)
   - **Query Language**: Flux
   - **URL**: `http://influxdb:8086`
   - **Organization**: `whisperengine`
   - **Token**: (check your `.env` file for `INFLUXDB_ADMIN_TOKEN`)
   - **Default Bucket**: `whisperengine`
3. Click "Save & Test" - should show "✅ datasource is working"

**Cause 2: No Data in InfluxDB Yet**
- AttachmentMonitor writes data when it detects attachment risk
- EngagementEngine writes every 10 invocations
- TrustRecovery writes every 5 detections
- **Solution**: Use the bots for a while, then check back

**Cause 3: Bots Not Running**
```bash
# Check bot status
./multi-bot.sh status

# Start bots if needed
./multi-bot.sh start
```

### "Datasource UID Not Found"

If the import says datasource UID `influxdb` not found:

1. **Check existing datasources**: Configuration → Data Sources
2. **Find your InfluxDB datasource** and note its UID
3. **Edit the JSON file** before importing:
   ```bash
   # Replace "influxdb" with your actual UID
   sed -i '' 's/"uid": "influxdb"/"uid": "YOUR_ACTUAL_UID"/g' grafana_dashboards/learning_system_telemetry.json
   ```
4. **Re-import** the modified JSON

---

## 🚀 Alternative: API Import (If You Have Credentials)

If you have Grafana API credentials or token:

```bash
# Method 1: Using admin credentials
curl -X POST http://localhost:3002/api/dashboards/db \
  -H "Content-Type: application/json" \
  -u admin:admin \
  -d @- <<EOF
{
  "dashboard": $(cat grafana_dashboards/learning_system_telemetry.json | jq '.dashboard'),
  "folderId": 0,
  "overwrite": true
}
EOF

# Method 2: Using API key
curl -X POST http://localhost:3002/api/dashboards/db \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d @- <<EOF
{
  "dashboard": $(cat grafana_dashboards/learning_system_telemetry.json | jq '.dashboard'),
  "folderId": 0,
  "overwrite": true
}
EOF
```

---

## 📊 What You'll See

### Active Panels (With Data):
1. **📊 Attachment Monitor - Risk Level Distribution**
   - Pie chart showing LOW/MEDIUM/HIGH risk users
2. **🧠 Emotional Intensity Trends**
   - Time series of attachment emotional intensity
3. **⚠️ Attachment Interventions**
   - Count of interventions provided
4. **📈 Interaction Frequency**
   - User message frequency tracking
5. **📊 Consecutive Days Streak**
   - User engagement streak visualization

### Info Panels (Status Only):
6. **🎯 Engagement Engine Metrics (Coming Soon)**
   - Shows telemetry is configured, pending data
7. **🔧 Trust Recovery Metrics (Coming Soon)**
   - Shows telemetry is configured, pending data
8. **📚 Learning Components Status**
   - Overview of all 8 learning component telemetry

---

## ✅ Success Checklist

- [ ] Dashboard imported successfully
- [ ] InfluxDB datasource configured (UID: `influxdb`)
- [ ] Bots are running (`./multi-bot.sh status`)
- [ ] Can see dashboard in Grafana UI
- [ ] AttachmentMonitor panels show "No Data" or actual data (both OK)
- [ ] Info panels display correctly

---

## 🔗 Related Documentation

- **Full Setup Guide**: `grafana_dashboards/README_LEARNING_TELEMETRY.md`
- **InfluxDB Integration**: See commit `2cd1a17`
- **Other Dashboards**: 
  - `vector_classification_intelligence.json`
  - `character_emotional_evolution.json`

---

## 💡 Next Steps After Import

1. **Let bots run** for 24-48 hours to generate data
2. **Monitor AttachmentMonitor** panels for immediate data
3. **Check EngagementEngine/TrustRecovery** after usage
4. **Adjust time ranges** (top right) to see historical data
5. **Create alerts** if needed for attachment risk thresholds
