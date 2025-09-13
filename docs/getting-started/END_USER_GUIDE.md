# 🚀 End User Guide - Discord AI Bot

This guide is for users who want to **run the bot** without modifying code. Choose your preferred setup method below.

---

## 🎯 **Quick Setup Overview**

| Method | Best For | Time | Complexity |
|--------|----------|------|------------|
| **[Local (Easy)](#-local-setup-easy)** | Most users | 5 minutes | ⭐ Simple |
| **[Local (Advanced)](#-local-setup-advanced)** | Tech-savvy users | 10 minutes | ⭐⭐ Medium |
| **[Cloud Deployment](#-cloud-deployment)** | Remote hosting | 15 minutes | ⭐⭐⭐ Advanced |

---

## 🏠 **Local Setup (Easy)**

### **Prerequisites**
- Docker Desktop installed and running
- Discord Developer Account (free)

### **Step 1: Download the Bot**
```bash
# Download
git clone https://github.com/whisperengine-ai/whisperengine.git
cd whisperengine
```

### **Step 2: Get Discord Bot Token**
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click **"New Application"** 
3. Give it a name (e.g., "My AI Bot")
4. Go to **"Bot"** tab
5. Click **"Reset Token"** and copy the token
6. Enable **"Message Content Intent"** under Privileged Gateway Intents

### **Step 3: Configure the Bot**
```bash
# Create configuration file
cp .env.example .env

# Edit configuration (replace YOUR_TOKEN_HERE with your Discord token)
nano .env  # macOS/Linux
# OR
notepad .env  # Windows
```

**Minimal .env setup:**
```bash
DISCORD_BOT_TOKEN=your_actual_discord_token_here
LLM_CHAT_API_URL=http://host.docker.internal:1234/v1
LLM_MODEL_NAME=local-model
```

### **Step 4: Start LLM Backend**
**Option A: LM Studio (Recommended for beginners)**
1. Download [LM Studio](https://lmstudio.ai/)
2. Download a model (e.g., "Phi-3.5-mini-instruct")
3. Start local server on port 1234

**Option B: Ollama (Command-line)**
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Download and run a model
ollama run phi3:mini
```

### **Step 5: Start the Bot**
```bash
# Start bot
./start.sh        # macOS/Linux
start.bat         # Windows

# View logs (optional)
./logs.sh         # macOS/Linux  
logs.bat          # Windows
```

### **Step 6: Invite Bot to Server**  
1. In Discord Developer Portal, go to **OAuth2 > URL Generator**
2. Check **"bot"** scope
3. Check **"Send Messages"**, **"Read Message History"** permissions
4. Copy generated URL and open in browser
5. Select your server and authorize

**✅ Done! Your bot is now running locally.**

---

## 🔧 **Local Setup (Advanced)**

For users who want more control over their setup.

### **Advanced Configuration Options**

**Performance Tuning (.env):**
```bash
# LLM Response Settings
LLM_TEMPERATURE=0.7        # Creativity (0.0 = focused, 2.0 = creative)
LLM_MAX_TOKENS=1000        # Response length limit
LLM_TIMEOUT=60             # Request timeout

# Memory Settings  
REDIS_HOST=redis           # Conversation caching
REDIS_PORT=6379
REDIS_DB=0

# Voice Features (optional)
VOICE_SUPPORT_ENABLED=true
ELEVENLABS_API_KEY=your_elevenlabs_key  # For voice responses

# Debugging
DEBUG_MODE=true            # Detailed logging
LOG_LEVEL=DEBUG            # Log verbosity
```

**Custom System Prompt:**
```bash
# Edit bot personality
nano system_prompt.md

# Restart bot to apply changes
./stop.sh && ./start.sh
```

### **Advanced LLM Backends**

**OpenAI API (Cloud):**
```bash
# In .env file
LLM_CHAT_API_URL=https://api.openai.com/v1
LLM_MODEL_NAME=gpt-4o-mini
OPENAI_API_KEY=your_openai_key
```

**Custom API Endpoints:**
```bash
# Any OpenAI-compatible API
LLM_CHAT_API_URL=https://your-api-endpoint.com/v1
LLM_MODEL_NAME=your-model-name
API_KEY=your_api_key
```

### **Monitoring & Maintenance**

```bash
# Check bot status
./status.sh              # View running services

# View detailed logs
./logs.sh                # Follow live logs

# Restart bot (apply config changes)
./stop.sh && ./start.sh

# Update bot
git pull
./stop.sh && ./start.sh
```

---

## ☁️ **Cloud Deployment**

Deploy your bot to run 24/7 in the cloud.

### **Option 1: Digital Ocean (Recommended)**

**Step 1: Create Droplet**
1. Sign up at [DigitalOcean](https://digitalocean.com)
2. Create new Droplet:
   - **Image**: Docker on Ubuntu
   - **Size**: Basic $6/month (1GB RAM)
   - **Region**: Closest to you

**Step 2: Setup on Server**
```bash
# SSH into your server
ssh root@your_server_ip

# Download bot
git clone https://github.com/whisperengine-ai/whisperengine.git
cd whisperengine

# Configure
cp .env.example .env
nano .env  # Add your Discord token and LLM settings

# Start bot
./start.sh
```

**Step 3: Setup LLM Backend (Cloud)**
Since cloud servers have limited resources, use a cloud LLM:

```bash
# Option A: OpenAI (recommended for cloud)
LLM_CHAT_API_URL=https://api.openai.com/v1
LLM_MODEL_NAME=gpt-4o-mini
OPENAI_API_KEY=your_openai_key

# Option B: OpenRouter (multiple models)
LLM_CHAT_API_URL=https://openrouter.ai/api/v1
LLM_MODEL_NAME=meta-llama/llama-3.1-8b-instruct:free
OPENROUTER_API_KEY=your_openrouter_key
```

### **Option 2: AWS/GCP/Azure**

**Using Docker Compose on any cloud provider:**

1. **Create VM instance** (1-2GB RAM minimum)
2. **Install Docker**:
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sh get-docker.sh
   ```
3. **Deploy bot**:
   ```bash
   git clone https://github.com/whisperengine-ai/whisperengine.git
   cd whisperengine
   cp .env.example .env
   nano .env  # Configure
   ./start.sh
   ```

### **Option 3: Heroku/Railway (Platform-as-a-Service)**

**Using Railway (easier):**
1. Fork the repository on GitHub
2. Connect Railway to your GitHub account
3. Deploy from your fork
4. Add environment variables in Railway dashboard
5. Deploy automatically

---

## 🔧 **Troubleshooting**

### **Common Issues**

**Bot won't start:**
```bash
# Check Docker is running
docker info

# Check configuration
cat .env | grep DISCORD_BOT_TOKEN

# View detailed logs
./logs.sh
```

**Bot connects but doesn't respond:**
- Check Message Content Intent is enabled in Discord Developer Portal
- Verify LLM backend is running and accessible
- Check bot has proper permissions in your Discord server

**LLM connection issues:**
```bash
# Test LLM endpoint
curl -X POST http://localhost:1234/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"local-model","messages":[{"role":"user","content":"test"}]}'
```

**Performance issues:**
- Use lighter models (phi3:mini instead of large models)
- Increase `LLM_TIMEOUT` in .env
- Add more RAM to your server/computer

### **Getting Help**

1. **Check logs**: `./logs.sh` shows detailed error messages
2. **Verify setup**: Ensure Discord token, LLM backend, and permissions are correct  
3. **GitHub Issues**: Report bugs or ask questions on the repository
4. **Discord Community**: Join support servers for real-time help

---

## 📊 **Usage & Commands**

### **Basic Bot Interaction**
- **@mention the bot**: Direct message to get a response
- **Reply to bot**: Continue conversation with context
- **DM the bot**: Private conversations work too

### **Management Commands**
```bash
# View bot status
./status.sh

# Restart bot  
./stop.sh && ./start.sh

# Update bot
git pull && ./stop.sh && ./start.sh

# Change personality
nano system_prompt.md && ./stop.sh && ./start.sh
```

### **Resource Usage**
- **Minimum**: 1GB RAM, 10GB storage
- **Recommended**: 2GB RAM, 20GB storage  
- **CPU**: Minimal (unless running local LLM)
- **Network**: ~1GB/month for typical usage

---

## 🔒 **Privacy & Security**

### **Data Handling**
- **Local Mode**: All data stays on your computer/server
- **Cloud LLM**: Only messages sent to configured LLM provider
- **No Telemetry**: Bot doesn't send data to developers

### **Security Best Practices**
- Keep Discord bot token secret
- Use environment variables for API keys
- Regularly update the bot (`git pull`)
- Monitor logs for unusual activity
- Use strong passwords for cloud servers

### **Conversation Data**
- **Stored locally**: In SQLite database and Redis cache
- **Retention**: Configurable (default: 30 days)
- **Backup**: Automatic backups in `./backups/` folder
- **Deletion**: Stop bot and delete database files

---

**🎉 Congratulations! Your Discord AI Bot is now running. Enjoy your private, customizable AI assistant!**
