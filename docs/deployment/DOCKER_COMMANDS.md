# WhisperEngine Docker Compose Commands Cheatsheet

**Pure Docker Compose workflow** - Cross-platform, no shell scripts required.

## 📋 **Table of Contents**

- [ Core Variables](#-core-variables)
- [🚀 Essential Commands](#-essential-commands)
- [📊 Monitoring & Logs](#-monitoring--logs)
- [🔄 Restart Operations](#-restart-operations)
- [🩺 Health Checks](#-health-checks)
- [🧪 Synthetic Services Management](#-synthetic-services-management)
- [🐳 Infrastructure Services Management](#-infrastructure-services-management)
- [📈 Monitoring & Metrics](#-monitoring--metrics)
- [🎯 Available Bots](#-available-bots)
- [🔧 Development Workflow](#-development-workflow)
- [🧹 Cleanup Commands](#-cleanup-commands)
- [💡 Shortcuts (Optional)](#-shortcuts-optional)
- [🐳 Database Operations](#-database-operations)
- [🚨 Troubleshooting](#-troubleshooting)
- [📚 Resources](#-resources)

## 🔧 **Core Variables**

```bash
PROJECT_NAME="whisperengine-multi"
COMPOSE_FILE="docker-compose.multi-bot.yml"
SYNTHETIC_COMPOSE_FILE="docker-compose.synthetic.yml"
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
curl http://localhost:3002/api/health    # Grafana
curl http://localhost:8087/health        # InfluxDB
curl http://localhost:6334/              # Qdrant
# PostgreSQL health: docker exec postgres pg_isready -U whisperengine -d whisperengine
# PostgreSQL port: 5433
# Qdrant port: 6334
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

## 🧪 **Synthetic Services Management**

### **Start Synthetic Services** (Separate from main multi-bot)
```bash
# Make sure main multi-bot system is running first (for infrastructure dependencies)
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml up -d

# Then start synthetic services
docker compose -f docker-compose.synthetic.yml up -d

# Or start specific synthetic service
docker compose -f docker-compose.synthetic.yml up -d synthetic-generator
docker compose -f docker-compose.synthetic.yml up -d synthetic-validator
```

### **Stop Synthetic Services**
```bash
docker compose -f docker-compose.synthetic.yml down

# Or stop specific synthetic service
docker compose -f docker-compose.synthetic.yml stop synthetic-generator
docker compose -f docker-compose.synthetic.yml stop synthetic-validator
```

### **Synthetic Services Logs**
```bash
docker compose -f docker-compose.synthetic.yml logs synthetic-generator
docker compose -f docker-compose.synthetic.yml logs -f synthetic-validator
```

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

## 🐳 **Infrastructure Services Management**

### **PostgreSQL Database**
```bash
# Start PostgreSQL only
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml up -d postgres

# Stop PostgreSQL
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml stop postgres

# Restart PostgreSQL
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml restart postgres

# PostgreSQL shell access
docker exec -it postgres psql -U whisperengine -d whisperengine

# View PostgreSQL logs
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml logs postgres

# PostgreSQL health check
docker exec postgres pg_isready -U whisperengine -d whisperengine
```

### **InfluxDB Time Series Database**
```bash
# Start InfluxDB only
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml up -d influxdb

# Stop InfluxDB
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml stop influxdb

# Restart InfluxDB
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml restart influxdb

# View InfluxDB logs
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml logs influxdb

# InfluxDB health check
curl http://localhost:8087/health

# InfluxDB CLI access
docker exec -it influxdb influx
```

### **Grafana Monitoring Dashboard**
```bash
# Start Grafana only
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml up -d grafana

# Stop Grafana
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml stop grafana

# Restart Grafana
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml restart grafana

# View Grafana logs
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml logs grafana

# Grafana health check
curl http://localhost:3002/api/health

# Access Grafana Web UI
# URL: http://localhost:3002
# Default login: admin/admin (change on first login)
```

### **Qdrant Vector Database**
```bash
# Start Qdrant only
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml up -d qdrant

# Stop Qdrant
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml stop qdrant

# Restart Qdrant
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml restart qdrant

# View Qdrant logs
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml logs qdrant

# Qdrant health check
curl http://localhost:6334/

# Qdrant Web UI
# URL: http://localhost:6334/dashboard
```

### **Start Infrastructure Services Group**
```bash
# Start all infrastructure services (no bots)
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml up -d postgres qdrant influxdb grafana

# Stop all infrastructure services
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml stop postgres qdrant influxdb grafana

# Restart all infrastructure services
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml restart postgres qdrant influxdb grafana
```

## 📈 **Monitoring & Metrics**

### **Grafana Dashboard Access**
```bash
# Open Grafana in browser
open http://localhost:3002  # macOS
# Or visit: http://localhost:3002
# Default credentials: admin/admin (change on first login)
```

### **InfluxDB Metrics**
```bash
# Check InfluxDB buckets
curl "http://localhost:8087/api/v2/buckets" \
  -H "Authorization: Token whisperengine-fidelity-first-metrics-token"

# Query performance metrics (example)
curl -XPOST "http://localhost:8087/api/v2/query?org=whisperengine" \
  -H "Authorization: Token whisperengine-fidelity-first-metrics-token" \
  -H "Content-Type: application/vnd.flux" \
  -d 'from(bucket:"performance_metrics") |> range(start:-1h)'
```

### **Bot Performance Monitoring**
```bash
# Check bot memory usage
docker stats --no-stream | grep -E "(elena-bot|marcus-bot|sophia-bot)"

# Monitor bot logs for performance
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml logs -f elena-bot | grep -E "(response_time|memory|error)"

# Test bot responsiveness
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:9091/health
```

### **Database Performance**
```bash
# PostgreSQL connection count
docker exec postgres psql -U whisperengine -d whisperengine -c "SELECT count(*) FROM pg_stat_activity;"

# Qdrant collection stats
curl http://localhost:6334/collections

# Check vector collection sizes
curl http://localhost:6334/collections/whisperengine_memory_elena/
curl http://localhost:6334/collections/whisperengine_memory_marcus/
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

### **Infrastructure Service Issues**
```bash
# PostgreSQL connection issues
docker exec postgres pg_isready -U whisperengine -d whisperengine
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml logs postgres

# InfluxDB not responding
curl -i http://localhost:8087/health
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml logs influxdb

# Grafana dashboard not loading
curl -i http://localhost:3002/api/health
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml logs grafana

# Qdrant vector database issues
curl -i http://localhost:6334/
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml logs qdrant
```

### **Synthetic Services Issues**
```bash
# Check synthetic services logs
docker compose -f docker-compose.synthetic.yml logs synthetic-generator
docker compose -f docker-compose.synthetic.yml logs synthetic-validator

# Verify network connectivity to main infrastructure
docker network ls | grep whisperengine-multi
docker network inspect whisperengine-multi_bot_network
```

### **Port Conflicts**
```bash
# Check what's using a port
lsof -i :9096
netstat -tulpn | grep 9096

# Common ports used by WhisperEngine:
# 3002 - Grafana
# 5433 - PostgreSQL
# 6334 - Qdrant
# 8087 - InfluxDB
# 9091-9099, 3007 - Bot health endpoints
```

### **Volume and Data Issues**
```bash
# Check volume usage
docker volume ls | grep whisperengine

# Inspect volume details
docker volume inspect whisperengine-multi_postgres_data
docker volume inspect whisperengine-multi_qdrant_data
docker volume inspect whisperengine-multi_influxdb_data
docker volume inspect whisperengine-multi_grafana_data

# ⚠️ DANGER: Remove all data volumes (complete reset)
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml down -v
```

## 📚 **Resources**

- **Docker Compose Docs**: https://docs.docker.com/compose/
- **WhisperEngine Main Config**: `docker-compose.multi-bot.yml`
- **Synthetic Services Config**: `docker-compose.synthetic.yml`
- **Bot Environments**: `.env.*` files
- **Character Data**: CDL database (PostgreSQL)
- **Grafana Dashboards**: http://localhost:3002
- **InfluxDB UI**: http://localhost:8087
- **Qdrant Dashboard**: http://localhost:6334/dashboard

### **Key Configuration Files**
```bash
docker-compose.multi-bot.yml          # Main multi-bot configuration
docker-compose.synthetic.yml          # Synthetic testing services
docker-compose.multi-bot.template.yml # Template for multi-bot generation
.env.{bot_name}                        # Individual bot configurations
scripts/generate_multi_bot_config.py   # Configuration generator
```

### **Infrastructure Ports**
```bash
3002  # Grafana Dashboard
5433  # PostgreSQL Database
6334  # Qdrant Vector Database
8087  # InfluxDB Time Series Database
```

### **Bot Health Check Ports**
```bash
9091  # Elena (Marine Biologist)
9092  # Marcus (AI Researcher)
9093  # Ryan (Game Developer)
9094  # Dream (Mythological)
9095  # Gabriel (British Gentleman)
9096  # Sophia (Marketing Executive)
9097  # Jake (Adventure Photographer)
9098  # Dotty
9099  # Aetheris (Conscious AI)
3007  # Aethys (Omnipotent Entity)
```

---

**No shell scripts required** - Pure Docker Compose workflow! 🎯