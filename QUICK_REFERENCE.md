# WhisperEngine - Quick Reference Card

## 🚀 Quick Start (No Git Required)

### **macOS/Linux Setup**
```bash
curl -sSL https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/setup-containerized.sh | bash
```

### **Windows Setup (PowerShell)**
```powershell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/setup-containerized.bat" -OutFile "setup.bat"; .\setup.bat
```

### **Windows Setup (Command Prompt)**
```cmd
curl -sSL https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/setup-containerized.bat -o setup.bat && setup.bat
```

---

## 🧹 Cleanup (Start Fresh)

### **macOS/Linux Cleanup**
```bash
curl -sSL https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/cleanup-docker.sh | bash
```

### **Windows Cleanup (PowerShell)**
```powershell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/cleanup-docker.ps1" -OutFile "cleanup.ps1"; .\cleanup.ps1
```

### **Windows Cleanup (Command Prompt)**
```cmd
curl -sSL https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/cleanup-docker.bat -o cleanup.bat && cleanup.bat
```

---

## 🌐 Access Points

After setup completes:

| Service | URL | Description |
|---------|-----|-------------|
| **Web Interface** | http://localhost:3001 | Create and manage characters |
| **Chat API** | http://localhost:9090/api/chat | Direct API access |
| **Health Check** | http://localhost:9090/health | System status |

---

## 🔧 Common Commands

### **View Logs**
```bash
docker logs whisperengine-assistant --tail 50
```

### **Restart Service**
```bash
docker-compose -f docker-compose.quickstart.yml restart
```

### **Stop All Services**
```bash
docker-compose -f docker-compose.quickstart.yml down
```

### **Start All Services**
```bash
docker-compose -f docker-compose.quickstart.yml up -d
```

---

## ❓ Troubleshooting

### **Database Migration Error?**
Run cleanup script (see above), then run setup again.

### **Port Already in Use?**
Stop conflicting services:
- Port 9090: API server
- Port 3001: Web interface
- Port 5432: PostgreSQL
- Port 6333: Qdrant
- Port 8086: InfluxDB

### **Docker Not Running?**
Start Docker Desktop and wait for it to fully initialize.

### **Can't Connect to Services?**
Wait 30-60 seconds after startup for all services to initialize.

---

## 📚 Documentation

- **Full README**: https://github.com/whisperengine-ai/whisperengine/blob/main/README.md
- **Cleanup Guide**: https://github.com/whisperengine-ai/whisperengine/blob/main/docs/deployment/CLEANUP_SCRIPTS.md
- **Troubleshooting**: https://github.com/whisperengine-ai/whisperengine/blob/main/docs/troubleshooting/README.md

---

## 🔑 Required Setup

Before starting, you need:
1. ✅ Docker Desktop installed and running
2. ✅ LLM API key (get free tier at https://openrouter.ai)
3. ✅ Available ports (9090, 3001, 5432, 6333, 8086)

---

## 💡 Quick Test

After setup, test with curl:

```bash
curl -X POST http://localhost:9090/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "message": "Hello! Tell me about yourself.",
    "context": {"platform": "api"}
  }'
```

Expected response: JSON with character's introduction.

---

**Need Help?** Open an issue: https://github.com/whisperengine-ai/whisperengine/issues
