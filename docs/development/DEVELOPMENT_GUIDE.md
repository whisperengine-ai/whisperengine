# Development Mode Guide

This guide explains how to run the Discord bot in different development modes for easier debugging and development.

## 🎯 **TL;DR - Quick Start**

**For native development (recommended):**
```bash
# Start infrastructure services only
./bot.sh start native

# Run bot natively (separate terminal)
python run.py
```

## 🏗️ **Development Architecture Options**

### Option 1: **Native Bot + Containerized Services** (Recommended)

**Best for:**
- ✅ Live debugging with breakpoints
- ✅ Faster code iteration
- ✅ IDE integration
- ✅ Direct access to logs
- ✅ Easy dependency management

**How it works:**
- Infrastructure services (PostgreSQL, Redis, ChromaDB) run in containers
- Bot code runs natively on your machine
- Bot connects to containerized services via localhost

**Commands:**
```bash
# Start infrastructure only
./bot.sh start native

# Run bot natively (separate terminal)
python run.py

# Or with specific environment:
cp .env.development .env
python run.py
```

### Option 2: **Full Containerization**

**Best for:**
- ✅ Production-like environment
- ✅ Consistent across team members
- ✅ Easy deployment testing

**Commands:**
```bash
# Everything in containers
./bot.sh start dev

# Or manually:
cp .env.production .env
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

## 📁 **Environment Files**

| File | Purpose | Bot Location | Service Hosts |
|------|---------|--------------|---------------|
| `.env.development` | Native bot development | Host machine | `localhost` |
| `.env.production` | Containerized deployment | Container | `redis`, `postgres`, `chromadb` |
| `.env` | Active configuration | Auto-detected | Auto-selected |

## 🔧 **Environment Auto-Detection**

The bot automatically detects its environment:

```python
# In run.py - automatically loads the right config
from env_manager import load_environment
load_environment()  # Auto-detects development vs production
```

**Detection logic:**
- **Development mode**: When `REDIS_HOST=localhost` or running outside container
- **Production mode**: When `REDIS_HOST=redis` or running inside container

## 🐛 **Debugging Workflows**

### **VS Code Debugging (Native Mode)**

1. Start infrastructure:
   ```bash
   ./bot.sh start native
   ```

2. Create `.vscode/launch.json`:
   ```json
   {
     "version": "0.2.0",
     "configurations": [
       {
         "name": "Debug Discord Bot",
         "type": "python",
         "request": "launch",
         "program": "${workspaceFolder}/run.py",
         "console": "integratedTerminal",
         "env": {
           "PYTHONPATH": "${workspaceFolder}"
         }
       }
     ]
   }
   ```

3. Set breakpoints and press F5

### **Live Code Reloading**

For faster development, consider using `watchdog`:

```bash
pip install watchdog
python -m watchdog src --recursive --patterns="*.py" --command="python run.py"
```

## 🔍 **Service Health Checks**

Check if services are ready:

```bash
# Redis
docker-compose exec redis redis-cli ping

# PostgreSQL
docker-compose exec postgres pg_isready -U bot_user

# ChromaDB
curl http://localhost:8000/api/v1/heartbeat

# All at once
python env_manager.py --mode development --info
```

## 📊 **Development vs Production Comparison**

| Aspect | Development (Native) | Production (Containerized) |
|--------|---------------------|---------------------------|
| **Bot Code** | Native Python | Docker container |
| **Services** | Docker containers | Docker containers |
| **Networking** | `localhost` | Docker network |
| **Debugging** | Full IDE support | Docker logs only |
| **Performance** | Faster iteration | Production-like |
| **Dependencies** | Local pip/venv | Docker image |

## 🛠️ **Common Development Tasks**

### **Start fresh development session:**
```bash
# Stop everything
./bot.sh stop

# Start infrastructure
./bot.sh start native

# Run bot (new terminal)
python run.py
```

### **Switch between modes:**
```bash
# Switch to native development
cp .env.development .env

# Switch to containerized
cp .env.production .env
```

### **Database management:**
```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U bot_user -d discord_bot

# Check Redis
docker-compose exec redis redis-cli

# View ChromaDB collections
curl http://localhost:8000/api/v1/collections
```

### **Troubleshooting:**

**"Connection refused" errors:**
- Check if services are running: `docker-compose ps`
- Verify correct .env file is loaded
- Check port conflicts: `lsof -i :6379` (Redis), `:5432` (PostgreSQL), `:8000` (ChromaDB)

**Import errors:**
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt`
- Check PYTHONPATH includes project root

## 🎬 **Recommended Development Workflow**

1. **Morning startup:**
   ```bash
   ./bot.sh start native
   ```

2. **Code in your IDE** with full debugging support

3. **Run/test changes:**
   ```bash
   python run.py
   ```

4. **End of day:**
   ```bash
   ./bot.sh stop
   ```

This gives you the best of both worlds: production-like infrastructure with native development experience!
