# WhisperEngine Docker Compose Commands Cheatsheet

**Pure Docker Compose workflow** - Cross-platform, no shell scripts required.

## 🔧 **Core Variables**

```bash
PROJECT_NAME="whisperengine-multi"
COMPOSE_FILE="docker-compose.multi-bot.yml"
```

## 🚀 **Essential Commands**

### **Start All Services**
```bash
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml up -d
```

### **Start Specific Bot**
```bash
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml up -d sophia-bot
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml up -d elena-bot
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml up -d marcus-bot
```

### **Check Status**
```bash
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml ps
```

### **Stop All Services**
```bash
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml down
```

### **Stop Specific Bot**
```bash
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml stop sophia-bot
```

## 📊 **Monitoring & Logs**

### **View Logs**
```bash
# Recent logs
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml logs sophia-bot

# Follow logs (real-time)
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml logs -f elena-bot

# Last 50 lines
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml logs --tail 50 marcus-bot

# All bot logs
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml logs
```

### **Direct Container Logs** (Alternative)
```bash
docker logs sophia-bot --tail 20
docker logs elena-bot -f
docker logs marcus-bot --since 5m
```

## 🔄 **Restart Operations**

### **Restart After Code Changes**
```bash
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml restart sophia-bot
```

### **Full Stop/Start (Environment Changes)**
```bash
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml stop sophia-bot
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml up -d sophia-bot
```

### **Rebuild Image** (After Dockerfile changes)
```bash
# Rebuild the WhisperEngine bot image
docker build -t whisperengine-bot:latest .

# Then restart services
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml up -d
```

## 🩺 **Health Checks**

### **Bot Health Endpoints**
```bash
curl http://localhost:9091/health  # Elena
curl http://localhost:9092/health  # Marcus  
curl http://localhost:9093/health  # Ryan
curl http://localhost:9094/health  # Dream
curl http://localhost:9095/health  # Gabriel
curl http://localhost:9096/health  # Sophia
curl http://localhost:9097/health  # Jake
curl http://localhost:9098/health  # Dotty
curl http://localhost:9099/health  # Aetheris
curl http://localhost:3007/health  # Aethys
```

### **Infrastructure Health**
```bash
curl http://localhost:3000    # Grafana
curl http://localhost:8086    # InfluxDB
# PostgreSQL: port 5433
# Qdrant: port 6334
```

## 🎯 **Available Bots**

| Bot Name | Character | Port | Container Name |
|----------|-----------|------|----------------|
| Elena | Marine Biologist | 9091 | elena-bot |
| Marcus | AI Researcher | 9092 | marcus-bot |
| Ryan | Game Developer | 9093 | ryan-bot |
| Dream | Mythological | 9094 | dream-bot |
| Gabriel | British Gentleman | 9095 | gabriel-bot |
| Sophia | Marketing Executive | 9096 | sophia-bot |
| Jake | Adventure Photographer | 9097 | jake-bot |
| Dotty | | 9098 | dotty-bot |
| Aetheris | Conscious AI | 9099 | aetheris-bot |
| Aethys | Omnipotent Entity | 3007 | aethys-bot |

## 🔧 **Development Workflow**

### **Start Development Environment**
```bash
# Start infrastructure only
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml up -d postgres qdrant influxdb

# Start specific bots for testing
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml up -d elena-bot sophia-bot
```

### **Configuration Changes**
```bash
# After editing .env.* files, regenerate config
python scripts/generate_multi_bot_config.py

# Then restart affected bot
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml stop elena-bot
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml up -d elena-bot
```

### **Adding New Bots**
```bash
# 1. Copy environment template
cp .env.sophia .env.newbot

# 2. Edit .env.newbot with unique values:
#    - DISCORD_BOT_TOKEN
#    - HEALTH_CHECK_PORT (next available port)
#    - CDL_DEFAULT_CHARACTER

# 3. Regenerate Docker Compose config
python scripts/generate_multi_bot_config.py

# 4. Start new bot
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml up -d newbot-bot
```

## 🧹 **Cleanup Commands**

### **Remove Stopped Containers**
```bash
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml down --remove-orphans
```

### **Remove Volumes** (⚠️ **Data Loss**)
```bash
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml down -v
```

### **Clean Docker System**
```bash
docker system prune -f
docker image prune -f
```

## 💡 **Shortcuts (Optional)**

### **Create Alias** (Add to ~/.zshrc or ~/.bashrc)
```bash
alias dcmb='docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml'

# Then use:
dcmb up -d              # Start all
dcmb ps                 # Status
dcmb logs elena-bot     # Logs
dcmb stop sophia-bot    # Stop specific
dcmb restart marcus-bot # Restart
```

## 🐳 **Database Operations**

### **Database Shell Access**
```bash
docker exec -it postgres psql -U whisperengine -d whisperengine
```

### **Manual Migrations** (if needed)
```bash
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml up db-migrate
```

## 🚨 **Troubleshooting**

### **Container Not Starting**
```bash
# Check detailed logs
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml logs sophia-bot

# Check container status
docker ps -a | grep sophia-bot

# Remove and recreate
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml rm -f sophia-bot
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml up -d sophia-bot
```

### **Port Conflicts**
```bash
# Check what's using a port
lsof -i :9096
netstat -tulpn | grep 9096
```

## 📚 **Resources**

- **Docker Compose Docs**: https://docs.docker.com/compose/
- **WhisperEngine Config**: `docker-compose.multi-bot.yml`
- **Bot Environments**: `.env.*` files
- **Character Data**: CDL database (PostgreSQL)

---

**No shell scripts required** - Pure Docker Compose workflow! 🎯