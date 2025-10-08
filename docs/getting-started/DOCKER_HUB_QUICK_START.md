# ⚡ Docker-First Quick Start

**Get WhisperEngine running in under 5 minutes!** Docker-based development and deployment.

## 🚀 Recommended: Clone & Multi-Bot Setup

The current WhisperEngine uses a **multi-bot Docker architecture**. This is the recommended approach:

```bash
# 1. Clone WhisperEngine
git clone https://github.com/whisperengine-ai/whisperengine.git
cd whisperengine

# 2. Setup your first character (Elena - Marine Biologist)
cp .env.template .env.elena
# Edit .env.elena with Discord token and LLM API key

# 3. Generate Docker configuration
python scripts/generate_multi_bot_config.py

# 4. Start Elena bot with complete infrastructure
./multi-bot.sh start elena

# 5. Verify everything is running
./multi-bot.sh status
```

**What you get:**
- ✅ Elena Discord bot (marine biologist personality)
- ✅ PostgreSQL database (port 5433) for semantic knowledge
- ✅ Qdrant vector database (port 6334) for conversation memory  
- ✅ HTTP Chat API (port 9091) for 3rd party integration
- ✅ Complete monitoring and logging

📖 **[Complete Installation Guide](INSTALLATION.md)** | **[Quick Start Guide](QUICK_START.md)**

## 🌍 One-Command Setup (Legacy)

⚠️ **Note**: The one-command scripts are available but **clone & multi-bot setup is recommended** for full functionality.

| Platform | Command |
|----------|---------|
| **🐧 Linux** | `curl -sSL https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/scripts/quick-start.sh \| bash` |
| **🍎 macOS** | `curl -sSL https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/scripts/quick-start.sh \| bash` |
| **🪟 Windows (PowerShell)** | `iwr https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/scripts/quick-start.ps1 \| iex` |

**Limitations**: Single-bot setup, limited character options, basic configuration.

## 🛠️ Manual Docker Setup

### Option A: Multi-Bot (Recommended)
```bash
# Clone repository for multi-bot support
git clone https://github.com/whisperengine-ai/whisperengine.git
cd whisperengine

# Setup character configuration
cp .env.template .env.elena
# Edit .env.elena with your credentials

# Generate and start
python scripts/generate_multi_bot_config.py
./multi-bot.sh start elena
```

### Option B: Single Container (Basic)
```bash
# Pull latest image
docker pull whisperengine/whisperengine:latest

# Create basic setup
mkdir whisperengine-bot && cd whisperengine-bot
curl -sSL https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/.env.template -o .env
# Edit .env with your Discord token and LLM API key

# Run with database dependencies
docker run -d --name whisperengine-bot \
  --env-file .env \
  -p 9091:9091 \
  whisperengine/whisperengine:latest
```

## 📋 Quick Configuration

**Edit `.env` with your essential settings:**

```bash
# REQUIRED: Get from Discord Developer Portal
DISCORD_BOT_TOKEN=your_discord_bot_token_here

# REQUIRED: Your LLM API endpoint (LM Studio, Ollama, etc.)
LLM_CHAT_API_URL=http://host.docker.internal:1234/v1
LLM_MODEL_NAME=your-model-name

# OPTIONAL: Choose AI personality (defaults to Dream)
BOT_SYSTEM_PROMPT_FILE=./prompts/empathetic_companion_template.md
```

## 🎭 Available Personalities

After setup, you can instantly switch personalities:

```bash
# Edit .env and change BOT_SYSTEM_PROMPT_FILE to:

# 💝 Supportive companion
BOT_SYSTEM_PROMPT_FILE=./prompts/empathetic_companion_template.md

# 👔 Business assistant  
BOT_SYSTEM_PROMPT_FILE=./prompts/professional_ai_template.md

# 😊 Casual friend
BOT_SYSTEM_PROMPT_FILE=./prompts/casual_friend_template.md

# Restart: docker-compose restart
```

## 🔧 Management Commands

```bash
# View logs
docker-compose logs -f

# Stop bot
docker-compose down

# Update to latest
docker-compose pull && docker-compose up -d
```

## 🚨 Troubleshooting

**Bot not responding?**
```bash
# Check logs for errors
docker-compose logs whisperengine-bot

# Verify token is correct
grep DISCORD_BOT_TOKEN .env

# Restart services
docker-compose restart
```

**Can't connect to LLM?**
```bash
# Check if LM Studio/Ollama is running on localhost:1234
curl http://localhost:1234/v1/models

# Update LLM_CHAT_API_URL in .env if needed
```

## 📚 Next Steps

- **[🎭 Customize Personality](https://github.com/WhisperEngine-AI/whisperengine/blob/main/docs/character/SYSTEM_PROMPT_CUSTOMIZATION.md)** - Create custom AI characters
- **[🧠 Memory & Intelligence](https://github.com/WhisperEngine-AI/whisperengine/blob/main/docs/ai-systems/MEMORY_SYSTEM_README.md)** - Advanced AI features
- **[🔑 API Configuration](https://github.com/WhisperEngine-AI/whisperengine/blob/main/docs/configuration/API_KEY_CONFIGURATION.md)** - Cloud LLM setup
- **[💻 Full Setup](https://github.com/WhisperEngine-AI/whisperengine)** - Clone and customize everything

---

**Need help?** Join our [Discord community](https://discord.gg/whisperengine) or [open an issue](https://github.com/WhisperEngine-AI/whisperengine/issues).