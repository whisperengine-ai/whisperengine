# Quick Start Guide - Docker-First Development

Get WhisperEngine running in **5 minutes** with Docker! This guide focuses on the recommended Docker-based development approach.

## 🐳 Docker Multi-Bot Setup (Recommended)

### Prerequisites

1. **Docker & Docker Compose** installed ([Get Docker](https://docs.docker.com/get-docker/))
2. **Git** for cloning the repository
3. **Discord Bot Token** (free from Discord Developer Portal)
4. **LLM API Key** (OpenRouter, Anthropic, or OpenAI)

### 🚀 Step 1: Clone & Setup

```bash
# Clone WhisperEngine
git clone https://github.com/whisperengine-ai/whisperengine.git
cd whisperengine

# Setup environment for Elena character (marine biologist)
cp .env.template .env.elena

# Generate Docker configuration
python scripts/generate_multi_bot_config.py
```

### 🔑 Step 2: Get Discord Bot Token

1. **Create Discord Application**
   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Click "New Application" → Name it (e.g., "Elena AI")

2. **Create Bot & Get Token**
   - Go to "Bot" section → Click "Add Bot"
   - Copy the token (keep this secret!)
   - **⚠️ CRITICAL**: Enable "Message Content Intent" under Privileged Gateway Intents

3. **Invite Bot to Server**
   - Go to "OAuth2" → "URL Generator"
   - **Scopes**: Check "bot"
   - **Permissions**: Check "Send Messages", "Read Message History", "Use Slash Commands", "Add Reactions"
   - Copy and visit the generated URL to invite your bot

### 🎯 Step 3: Configure Environment

Edit `.env.elena` with your credentials:

```bash
# Discord Configuration
DISCORD_BOT_TOKEN=your_discord_bot_token_here
DISCORD_BOT_NAME=elena

# Character Configuration  
CHARACTER_FILE=elena  # Uses database-stored CDL character data

# LLM Configuration (choose one)
LLM_CLIENT_TYPE=openrouter
OPENROUTER_API_KEY=your_openrouter_api_key_here
LLM_CHAT_MODEL=anthropic/claude-3.5-sonnet

# Alternative: Anthropic direct
# LLM_CLIENT_TYPE=anthropic  
# ANTHROPIC_API_KEY=your_anthropic_api_key_here
# LLM_CHAT_MODEL=claude-3-5-sonnet-20241022

# Infrastructure (auto-configured for Docker)
QDRANT_COLLECTION_NAME=whisperengine_memory_elena
HEALTH_CHECK_PORT=9091
```

### ⚡ Step 4: Start WhisperEngine

```bash
# Start Elena bot + complete infrastructure
./multi-bot.sh start elena

# Check if everything is running
./multi-bot.sh status

# View Elena's logs
./multi-bot.sh logs elena
```

**Expected Output:**
```
✅ Infrastructure Status:
- PostgreSQL: Running (port 5433)
- Qdrant: Running (port 6334)  
- Elena Bot: Running (port 9091)

✅ Elena Bot Features:
- Discord Bot: Connected and responding
- HTTP Chat API: http://localhost:9091/api/chat
- Vector Memory: Isolated collection (whisperengine_memory_elena)
- Character Personality: Marine Biologist (CDL-powered)
```

### 🧪 Step 5: Test Your Bot

1. **Test Discord Bot**
   - Send a DM to your bot: "Hello Elena! Tell me about marine biology."
   - Or mention in a channel: `@Elena Hello!`

2. **Test HTTP Chat API**
   ```bash
   curl -X POST http://localhost:9091/api/chat \
     -H "Content-Type: application/json" \
     -d '{
       "user_id": "test_user",
       "message": "What do you think about ocean conservation?",
       "context": {"platform": "api"}
     }'
   ```

3. **Test Memory System**
   - After chatting, the bot learns facts about you
   - Ask: "What do you remember about me?"

## 🎭 Add More Characters

```bash
# Setup Marcus (AI Researcher)
cp .env.template .env.marcus
# Edit .env.marcus with unique Discord token and set CHARACTER_FILE=marcus

# Regenerate configuration
python scripts/generate_multi_bot_config.py

# Start Marcus alongside Elena
./multi-bot.sh start marcus

# Or start all configured characters
./multi-bot.sh start all
```

**Available Characters:**
- **Elena** (Marine Biologist) - Warm, empathetic, scientific
- **Marcus** (AI Researcher) - Academic, analytical, professional
- **Jake** (Adventure Photographer) - Rugged, protective, creative
- **Ryan** (Game Developer) - Technical, perfectionist, innovative
- **Gabriel** (British Gentleman) - Sophisticated, witty, charming
- **Sophia** (Marketing Executive) - Professional, strategic, luxury-focused
- **Dream** (Mythological) - Profound, otherworldly, philosophical
- **Aethys** (Omnipotent) - Transcendent, mystical, unlimited

## 🔧 Management Commands

```bash
# View all available commands
./multi-bot.sh

# Start specific bot
./multi-bot.sh start elena

# Start all configured bots
./multi-bot.sh start all

# View logs (recommended for troubleshooting)
./multi-bot.sh logs elena

# Check system status
./multi-bot.sh status

# Stop specific bot
./multi-bot.sh stop elena

# Stop everything
./multi-bot.sh stop
```

## 🏥 Health Monitoring

WhisperEngine includes built-in monitoring:

```bash
# Check overall system health
curl http://localhost:9091/health

# Check individual component status
./multi-bot.sh status

# View system logs
docker logs whisperengine-elena-bot --tail 20
docker logs whisperengine-multi-postgres --tail 20
docker logs whisperengine-multi-qdrant --tail 20
```

## 🚨 Common Issues & Quick Fixes

### Bot Won't Respond to Messages
```bash
# Check Discord Message Content Intent is enabled
./multi-bot.sh logs elena | grep "Missing"

# Verify bot permissions in Discord server
./multi-bot.sh logs elena | grep "Forbidden"
```

### LLM Connection Issues  
```bash
# Test API key
./multi-bot.sh logs elena | grep "API"

# Verify configuration
cat .env.elena | grep -E "(OPENROUTER|ANTHROPIC|LLM)"
```

### Infrastructure Problems
```bash
# Check container status
./multi-bot.sh status

# Restart infrastructure
./multi-bot.sh stop
./multi-bot.sh start elena

# Check database connections
docker logs whisperengine-multi-postgres --tail 10
docker logs whisperengine-multi-qdrant --tail 10
```

### Performance Issues
```bash
# Check resource usage
docker stats --no-stream

# View memory usage
./multi-bot.sh logs elena | grep -i memory

# Monitor API response times
./multi-bot.sh logs elena | grep "Processing"
```

## 🎉 You're Ready!

Your WhisperEngine setup now includes:

- ✅ **Multi-Character Discord Bots** - AI roleplay characters with unique personalities
- ✅ **Vector Memory System** - Persistent, searchable conversation memory  
- ✅ **HTTP Chat APIs** - Rich metadata for 3rd party integration
- ✅ **PostgreSQL Knowledge Graph** - Semantic fact storage and relationships
- ✅ **Production Monitoring** - Health checks and performance tracking
- ✅ **CDL Character System** - Database-powered personality modeling

## 📚 Next Steps

- **[Character Creation](../characters/CDL_CHARACTER_CREATION.md)** - Create custom AI personalities
- **[Advanced Configuration](../configuration/ADVANCED_CONFIG.md)** - Customize behavior and features  
- **[Production Deployment](../deployment/PRODUCTION_SETUP.md)** - Scale for production use
- **[API Integration](../api/HTTP_CHAT_API.md)** - Integrate with your applications
- **[Local LLM Setup](../deployment/LOCAL_LLM_SETUP.md)** - Complete privacy with local models

**Need help?** Check our [Installation Guide](INSTALLATION.md) for detailed troubleshooting.
   - Click "New Application"
   - Name it (e.g., "My AI Bot")

2. **Create Bot**
   - Go to "Bot" section
   - Click "Add Bot"
   - Copy the token (keep this secret!)

3. **⚠️ CRITICAL: Enable Message Content Intent**
   - In the "Bot" section under "Privileged Gateway Intents"
   - **Enable "Message Content Intent"** ✅ (REQUIRED for bot to read messages)

4. **Invite Bot to Server**
   - Go to "OAuth2" → "URL Generator"
   - **Scopes**: Check "bot"
   - **Bot Permissions**: Check:
     - ✅ Send Messages
     - ✅ Read Message History  
     - ✅ Use Slash Commands
     - ✅ Add Reactions
     - ✅ Embed Links
     - ✅ Read Messages/View Channels
   - Copy the generated URL and visit it to invite your bot to your server

## 🚀 Step 3: Install & Run the Bot

1. **Clone and Install**
   ```bash
   git clone https://github.com/whisperengine-ai/whisperengine.git
   cd whisperengine
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   ```bash
   # For local LLM users (LM Studio/Ollama):
   cp .env.minimal .env
   
   # For OpenRouter users:
   cp .env.openrouter.example .env
   ```

3. **Edit Configuration**
   
   Open `.env` in any text editor and set:
   
   **For LM Studio:**
   ```env
   DISCORD_BOT_TOKEN=your_discord_bot_token_here
   LLM_CHAT_API_URL=http://localhost:1234/v1
   LLM_MODEL_NAME=local-model
   ```
   
   **For Ollama:**
   ```env
   DISCORD_BOT_TOKEN=your_discord_bot_token_here
   LLM_CHAT_API_URL=http://localhost:11434/v1
   LLM_MODEL_NAME=llama3.2:3b
   ```
   
   **For OpenRouter:**
   ```env
   DISCORD_BOT_TOKEN=your_discord_bot_token_here
   LLM_CHAT_API_URL=https://openrouter.ai/api/v1
   OPENROUTER_API_KEY=your_openrouter_api_key_here
   LLM_MODEL_NAME=anthropic/claude-3.5-sonnet
   ```

4. **Start the Bot**
   ```bash
   # Normal mode
   python basic_discord_bot.py
   
   # Debug mode (if you run into issues)
   python basic_discord_bot.py --debug
   ```

## ✅ Step 4: Test Your Bot

1. **Test LLM Connection**
   - In Discord, send: `!llm_status`
   - Should show connection info and model details

2. **Test Basic Chat**
   - Send a DM to your bot: "Hello! I'm testing you."
   - Or mention it in a channel: `@YourBot Hello!`

3. **Test Memory System**
   - After chatting, use: `!my_memory`
   - Should show facts the bot learned about you

## 🚨 Common Issues & Quick Fixes

### Bot Won't Respond to Messages
- **Missing Message Content Intent**: Go to Discord Developer Portal → Your App → Bot → Enable "Message Content Intent"
- **Missing Permissions**: Re-invite bot with proper permissions

### LLM Connection Issues
- **Local Services**: Make sure LM Studio or Ollama is running and model is loaded
- **OpenRouter**: Check API key is valid and you have credits
- **Test Connection**: Use `!llm_status` command to diagnose

### Bot Starts But Gives Errors
- **Check Logs**: Look at console output for error messages
- **Debug Mode**: Run with `python basic_discord_bot.py --debug`
- **Check Environment**: Verify `.env` file has correct values

## 🎉 You're Done!

Your bot now has:
- ✅ AI-powered conversations
- ✅ Persistent memory across chats
- ✅ Automatic fact learning
- ✅ Complete privacy (if using local LLM)

## 🔄 Next Steps

- **Import ChatGPT History**: Use `python import_chatgpt_history.py` to bring your existing conversations
- **Explore Commands**: Type `!commands` to see all available features
- **Advanced Setup**: Check [Installation Guide](INSTALLATION.md) for hybrid configurations and optimization

---

**Need help?** Check the [Installation Guide](INSTALLATION.md) for detailed troubleshooting.
