# WhisperEngine - Running Modes Guide

This guide covers all the different ways to run the Discord bot locally, for both developers and end users.

## 🔧 **Development Mode (For Developers)**

### **Option 1: Full Containerization (Recommended for Dev)**

Start with live code editing and hot-reloading:

```bash
# Start development mode
./bot.sh start dev
```

View logs:
```bash
# View bot logs
./bot.sh logs

# View specific service logs
./bot.sh logs redis
```

Stop services:
```bash
# Stop development services
./bot.sh stop
```

**Features:**
- ✅ Live code editing (no rebuild needed)
- ✅ Hot-reloading on file changes
- ✅ Debug logging enabled
- ✅ Live system prompt editing

### **Option 2: Native Bot + Containerized Services**

Start infrastructure services only:
```bash
./bot.sh start native
```

Run bot natively (in separate terminal):
```bash
python main.py

# OR with specific environment:
cp .env.development .env
python main.py
```

**Best for:**
- ✅ Live debugging with breakpoints
- ✅ IDE integration (VS Code debugging)
- ✅ Faster iteration
- ✅ Direct access to logs

### **Development Commands Available:**
```bash
./bot.sh start dev      # Start development mode
./bot.sh logs           # View detailed logs
./bot.sh stop           # Stop services
./bot.sh status         # Check service status
./bot.sh restart dev    # Quick restart
```

---

## 👥 **End User Mode (Non-Technical Users)**

### **Easy Setup (Recommended)**

1. Download the project:
```bash
git clone https://github.com/theRealMarkCastillo/whisper-engine
cd whisper-engine
```

2. Configure your settings:
```bash
cp .env.example .env
nano .env  # Add your Discord token
```

3. Start your LLM backend first (LM Studio/Ollama)

4. Start the bot:
```bash
# macOS/Linux
./bot.sh start prod

# Windows
.\bot-manager.ps1 start
```

### **Windows End-User Simplified Commands:**

```powershell
.\bot-manager.ps1 setup   # First time setup
.\bot-manager.ps1 start   # Start bot
.\bot-manager.ps1 status  # Check status
.\bot-manager.ps1 logs    # View logs
.\bot-manager.ps1 stop    # Stop bot
```

### **Universal Quick Start:**

Just start your LLM first, then:
```bash
./start.sh        # Unix/Linux/macOS
.\start.ps1       # Windows PowerShell
start.bat         # Windows batch
```

---

## 🚀 **Production Mode (Local)**

### **Optimized Production Build:**

```bash
./start.sh              # Start production build
./logs.sh               # View production logs
./stop.sh               # Stop production services
./status.sh             # Check service status
```

**Uses:** `docker-compose.yml` only (no dev overrides)

---

## 📊 **Management Commands Summary**

| Mode | Start | Status | Logs | Stop |
|------|-------|--------|------|------|
| **Development** | `./bot.sh start dev` | `./bot.sh status` | `./bot.sh logs` | `./bot.sh stop` |
| **Production** | `./bot.sh start prod` | `./bot.sh status` | `./bot.sh logs` | `./bot.sh stop` |
| **Native Dev** | `./bot.sh start native` + `python main.py` | `./bot.sh status` | Direct Python logs | `./bot.sh stop` |
| **End User (Win)** | `.\bot-manager.ps1 start` | `.\bot-manager.ps1 status` | `.\bot-manager.ps1 logs` | `.\bot-manager.ps1 stop` |

---

## 🔄 **Key Differences**

### **Development Mode:**
- Uses `docker-compose.yml` + `docker-compose.dev.yml`
- Live code mounting from `src` directory
- Debug logging enabled
- Changes reflect immediately

### **Production Mode:**
- Uses `docker-compose.yml` only
- Code copied during build process
- Optimized for performance
- Production logging levels

### **Native Development:**
- Infrastructure in containers, bot runs natively
- Best debugging experience
- Requires Python environment setup
- Direct IDE integration

---

## 🎯 **Choosing the Right Mode**

**For Developers:**
- **Native Development**: Best for debugging and IDE integration
- **Full Containerization**: Good for testing production-like environment

**For End Users:**
- **Production Mode**: Recommended for daily use
- **Windows Bot Manager**: Simplest option for Windows users

**For Testing:**
- **Development Mode**: Quick iteration and testing
- **Production Mode**: Final testing before deployment

The choice depends on your technical level and development needs!
