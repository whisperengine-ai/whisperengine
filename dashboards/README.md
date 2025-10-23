# Dashboard Auto-Loading Setup

## ✅ **Dashboard Now Available!**

The Learning System Telemetry dashboard has been copied to the auto-provisioning directory and Grafana has been restarted. 

**Access it now:**
1. Open: http://localhost:3002
2. Login: `admin` / `whisperengine_grafana` (or your custom password)
3. Navigate: Dashboards → Browse → WhisperEngine folder
4. Click: **Learning System Telemetry & Experimental Features**

---

## 📂 How Auto-Provisioning Works

WhisperEngine uses Grafana's auto-provisioning feature:

```yaml
# grafana-config/dashboard.yml
providers:
  - name: 'whisperengine-dashboards'
    folder: 'WhisperEngine'
    path: /var/lib/grafana/dashboards
    updateIntervalSeconds: 30  # Auto-reloads every 30 seconds
```

**Docker Mount:**
```yaml
# docker-compose.multi-bot.yml
volumes:
  - ./dashboards:/var/lib/grafana/dashboards:ro
```

**Result:** Any JSON dashboard placed in `./dashboards/` appears automatically in Grafana!

---

## 🔧 Adding More Dashboards

To add future dashboards:

1. **Place JSON file** in `./dashboards/` directory
2. **Wait 30 seconds** OR restart Grafana:
   ```bash
   docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml restart grafana
   ```
3. **Find in UI**: Dashboards → Browse → WhisperEngine folder

---

## 📊 Current Auto-Loaded Dashboards

- ✅ `character_emotional_evolution.json` - Character emotional state tracking
- ✅ `learning_system_telemetry.json` - Learning & experimental features (NEW!)

**Note:** The `grafana_dashboards/` directory contains:
- Documentation
- Additional dashboard exports
- Import scripts

The `dashboards/` directory contains:
- **Production dashboards** that auto-load into Grafana

---

## 🔍 Troubleshooting

### Dashboard Not Showing Up?

**Check Grafana logs:**
```bash
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml logs grafana | tail -50
```

**Verify file exists:**
```bash
ls -lh dashboards/
```

**Force reload:**
```bash
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml restart grafana
```

**Check inside container:**
```bash
docker exec grafana ls -lh /var/lib/grafana/dashboards/
```

### Dashboard Shows Errors?

- Check datasource UID matches: `influxdb`
- Verify InfluxDB datasource is configured
- Check Configuration → Data Sources in Grafana UI

---

## 🎯 Default Credentials

```
Username: admin
Password: whisperengine_grafana
```

*(Can be changed via environment variables `GRAFANA_USER` and `GRAFANA_PASSWORD` in docker-compose)*
