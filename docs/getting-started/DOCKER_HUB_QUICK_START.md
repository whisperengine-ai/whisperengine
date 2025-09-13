# ⚡ Lightning Quick Start - Docker Hub

**Get WhisperEngine running in under 2 minutes!** No building, no cloning repos.

## 🌍 Cross-Platform One-Command Setup

Choose your platform and run the appropriate command:

| Platform | Command |
|----------|---------|
| **🐧 Linux** | `curl -sSL https://raw.githubusercontent.com/WhisperEngine-AI/whisperengine/main/scripts/quick-start.sh \| bash` |
| **🍎 macOS** | `curl -sSL https://raw.githubusercontent.com/WhisperEngine-AI/whisperengine/main/scripts/quick-start.sh \| bash` |
| **🪟 Windows (PowerShell)** | `iwr https://raw.githubusercontent.com/WhisperEngine-AI/whisperengine/main/scripts/quick-start.ps1 \| iex` |
| **🪟 Windows (Command Prompt)** | Download and run: [`quick-start.bat`](https://raw.githubusercontent.com/WhisperEngine-AI/whisperengine/main/scripts/quick-start.bat) |

**That's it!** The script will:
1. Pull the latest WhisperEngine image from Docker Hub
2. Create a minimal `.env` file for you to edit  
3. Open your editor to configure Discord token
4. Start all services
5. Show you monitoring commands

📖 **[Detailed Cross-Platform Guide](CROSS_PLATFORM_QUICK_START.md)**

## 🛠️ Manual Setup (3 steps)

### Step 1: Pull the Image
```bash
docker pull whisperengine/whisperengine:latest
```

### Step 2: Create Configuration
```bash
# Create minimal config directory
mkdir -p whisperengine-bot && cd whisperengine-bot

# Download minimal setup files
curl -sSL https://raw.githubusercontent.com/WhisperEngine-AI/whisperengine/main/docker/quick-start/docker-compose.yml -o docker-compose.yml
curl -sSL https://raw.githubusercontent.com/WhisperEngine-AI/whisperengine/main/docker/quick-start/.env.minimal -o .env

# Edit with your Discord token
nano .env
```

### Step 3: Launch
```bash
docker-compose up -d
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
BOT_SYSTEM_PROMPT_FILE=./config/system_prompts/empathetic_companion_template.md
```

## 🎭 Available Personalities

After setup, you can instantly switch personalities:

```bash
# Edit .env and change BOT_SYSTEM_PROMPT_FILE to:

# 💝 Supportive companion
BOT_SYSTEM_PROMPT_FILE=./config/system_prompts/empathetic_companion_template.md

# 👔 Business assistant  
BOT_SYSTEM_PROMPT_FILE=./config/system_prompts/professional_ai_template.md

# 😊 Casual friend
BOT_SYSTEM_PROMPT_FILE=./config/system_prompts/casual_friend_template.md

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
docker-compose logs discord-bot

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