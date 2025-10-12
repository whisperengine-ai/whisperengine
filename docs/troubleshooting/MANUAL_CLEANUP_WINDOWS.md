# Manual Cleanup Commands for Windows

If the automated setup fails, use these manual commands to clean up and start fresh.

## 🧹 Quick Cleanup (Recommended)

### Option 1: PowerShell Cleanup Script (Easiest)

```powershell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/cleanup-docker.ps1" -OutFile "cleanup.ps1"
.\cleanup.ps1
```

### Option 2: Manual Commands

**For PowerShell:**
```powershell
# Stop all WhisperEngine containers
docker stop whisperengine-assistant whisperengine-web-ui whisperengine-db-migrate postgres qdrant influxdb 2>$null

# Remove all WhisperEngine containers
docker rm whisperengine-assistant whisperengine-web-ui whisperengine-db-migrate postgres qdrant influxdb 2>$null

# Remove volumes (WARNING: Deletes all data!)
docker volume rm whisperengine_postgres_data whisperengine_qdrant_data whisperengine_influxdb_data 2>$null

# Remove network
docker network rm whisperengine-network 2>$null

# Remove dangling volumes
docker volume prune -f
```

**For Command Prompt:**
```cmd
REM Stop all WhisperEngine containers
docker stop whisperengine-assistant whisperengine-web-ui whisperengine-db-migrate postgres qdrant influxdb 2>nul

REM Remove all WhisperEngine containers
docker rm whisperengine-assistant whisperengine-web-ui whisperengine-db-migrate postgres qdrant influxdb 2>nul

REM Remove volumes (WARNING: Deletes all data!)
docker volume rm whisperengine_postgres_data whisperengine_qdrant_data whisperengine_influxdb_data 2>nul

REM Remove network
docker network rm whisperengine-network 2>nul

REM Remove dangling volumes
docker volume prune -f
```

---

## 🔍 Check Current State

Before cleanup, see what's running:

```cmd
docker ps -a
docker volume ls
docker network ls
```

---

## 📁 Remove Downloaded Files (Optional)

If you want to completely start over, also delete the `whisperengine` folder:

**PowerShell:**
```powershell
Remove-Item -Recurse -Force whisperengine
```

**Command Prompt:**
```cmd
rmdir /s /q whisperengine
```

---

## 🔧 Troubleshooting Specific Issues

### Issue: "Port already in use"

**Check what's using the ports:**
```cmd
netstat -ano | findstr ":9090"
netstat -ano | findstr ":3001"
netstat -ano | findstr ":5432"
netstat -ano | findstr ":6333"
netstat -ano | findstr ":8086"
```

**Stop specific container by port:**
```cmd
docker ps
docker stop <container_id>
```

### Issue: "Cannot remove volume - in use"

**Force stop and remove everything:**
```powershell
# Stop ALL Docker containers (nuclear option)
docker stop $(docker ps -aq)

# Remove ALL Docker containers
docker rm $(docker ps -aq)

# Then try removing volumes again
docker volume rm whisperengine_postgres_data whisperengine_qdrant_data whisperengine_influxdb_data
```

### Issue: "Network in use"

**Find what's using the network:**
```cmd
docker network inspect whisperengine-network
```

**Force remove network:**
```cmd
docker network rm -f whisperengine-network
```

---

## 🚀 After Cleanup - Start Fresh

Once cleanup is complete, try the setup again:

**PowerShell (Recommended):**
```powershell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/setup-containerized.ps1" -OutFile "setup.ps1"
.\setup.ps1
```

**Command Prompt:**
```cmd
curl -sSL https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/setup-containerized.bat -o setup.bat
setup.bat
```

---

## ⚠️ What Gets Deleted

When you run cleanup, these items are **permanently deleted**:

- ✅ All WhisperEngine containers
- ✅ PostgreSQL database (character data, user data, conversation history)
- ✅ Qdrant vector memory (semantic memory, conversation embeddings)
- ✅ InfluxDB time-series data (metrics, analytics)
- ✅ Docker networks for WhisperEngine
- ❌ Docker images (kept for faster restart)
- ❌ Downloaded setup scripts (manual deletion required)

**To also remove Docker images** (saves disk space):
```cmd
docker rmi whisperengine/whisperengine:latest
docker rmi whisperengine/cdl-web-ui:latest
docker rmi postgres:16-alpine
docker rmi qdrant/qdrant:latest
docker rmi influxdb:2.7-alpine
```

---

## 💡 Alternative: Soft Reset (Keep Data)

If you just want to restart services without losing data:

**Stop services:**
```cmd
docker stop whisperengine-assistant whisperengine-web-ui
```

**Start services:**
```cmd
docker start whisperengine-assistant whisperengine-web-ui
```

**Restart services:**
```cmd
docker restart whisperengine-assistant whisperengine-web-ui postgres qdrant influxdb
```

---

## 🆘 Still Having Issues?

1. **Restart Docker Desktop**
   - Right-click Docker Desktop icon → Quit Docker Desktop
   - Wait 10 seconds
   - Start Docker Desktop again
   - Wait for it to fully initialize (icon stops animating)

2. **Check Docker Desktop Settings**
   - Open Docker Desktop
   - Settings → Resources → WSL Integration (if using WSL)
   - Settings → Resources → Advanced (check RAM allocation - need 4GB+)

3. **Reset Docker Desktop to Factory Defaults** (Last Resort)
   - Docker Desktop → Settings → Troubleshoot → Reset to factory defaults
   - **WARNING**: This deletes ALL Docker data (all containers, images, volumes)

---

## 📚 Related Documentation

- [Windows Quickstart Fixes](WINDOWS_QUICKSTART_FIXES.md)
- [Full Cleanup Guide](../deployment/CLEANUP_SCRIPTS.md)
- [Quick Reference](../../QUICK_REFERENCE.md)
