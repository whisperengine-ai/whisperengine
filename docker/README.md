# WhisperEngine AI Discord Bot

**Advanced AI Discord bot with Phase 4 human-like intelligence, multi-modal capabilities, and sophisticated memory systems.**

## ⚡ Lightning Quick Start (2 minutes)

```bash
# One-command setup
curl -sSL https://raw.githubusercontent.com/WhisperEngine-AI/whisperengine/main/scripts/quick-start.sh | bash

# Edit configuration
nano .env  # Set your DISCORD_BOT_TOKEN

# Start your bot
docker-compose up -d
```

## 🏷️ Tags

- `latest` - Latest stable release (recommended)
- `v1.x.x` - Specific version releases
- `develop` - Development branch (bleeding edge)

## 📋 Manual Setup

### 1. Create Project Directory
```bash
mkdir whisperengine-bot && cd whisperengine-bot
```

### 2. Download Configuration
```bash
# Docker Compose file
curl -sSL https://raw.githubusercontent.com/WhisperEngine-AI/whisperengine/main/docker/quick-start/docker-compose.yml -o docker-compose.yml

# Environment template
curl -sSL https://raw.githubusercontent.com/WhisperEngine-AI/whisperengine/main/docker/quick-start/.env.minimal -o .env
```

### 3. Configure Environment
Edit `.env` with your settings:
```bash
# Required
DISCORD_BOT_TOKEN=your_discord_bot_token_here
LLM_CHAT_API_URL=http://host.docker.internal:1234/v1
LLM_MODEL_NAME=your-model-name

# Optional personality (uncomment one)
# BOT_SYSTEM_PROMPT_FILE=./config/system_prompts/empathetic_companion_template.md
# BOT_SYSTEM_PROMPT_FILE=./config/system_prompts/professional_ai_template.md
```

### 4. Launch Services
```bash
docker-compose up -d
```

## 🎭 Available AI Personalities

- 🌙 **Dream** (default) - Formal, mystical character from The Sandman
- 💝 **Empathetic Companion** - Supportive friend for emotional support
- 👔 **Professional AI** - Business assistant for work tasks
- 😊 **Casual Friend** - Relaxed buddy for everyday conversations
- 🎭 **Character AI** - Template for custom roleplay characters
- 🧠 **Adaptive AI** - Self-learning personality that adapts to users

## 🔧 Management Commands

```bash
# View logs
docker-compose logs -f whisperengine

# Stop services
docker-compose down

# Update to latest version
docker-compose pull && docker-compose up -d

# Restart with new configuration
docker-compose restart whisperengine
```

## 🌟 Key Features

- **Phase 4 Human-Like Intelligence** - Advanced conversation adaptation and emotional awareness
- **Multi-Modal Support** - Text, voice, and image processing
- **Sophisticated Memory** - ChromaDB vector memory + PostgreSQL persistence + Redis caching
- **Personality Templates** - Multiple pre-built AI personalities with hot-reload
- **Enterprise Ready** - Production-grade Docker deployment with standard components
- **Local & Cloud LLM Support** - Works with LM Studio, Ollama, OpenAI, OpenRouter, and more

## 📊 System Requirements

**Minimum:**
- 4GB RAM
- 2 CPU cores
- 10GB disk space
- Docker & Docker Compose

**Recommended:**
- 8GB+ RAM
- 4+ CPU cores
- GPU support (for local LLM)
- SSD storage

## 🔗 Links

- **📖 Documentation**: https://github.com/WhisperEngine-AI/whisperengine
- **🎭 Personality Customization**: https://github.com/WhisperEngine-AI/whisperengine/blob/main/docs/character/SYSTEM_PROMPT_CUSTOMIZATION.md
- **🚀 Full Setup Guide**: https://github.com/WhisperEngine-AI/whisperengine/blob/main/docs/getting-started/DOCKER_HUB_QUICK_START.md
- **💬 Discord Community**: https://discord.gg/whisperengine
- **🐛 Issues**: https://github.com/WhisperEngine-AI/whisperengine/issues

## 📝 License

MIT License - See [LICENSE](https://github.com/WhisperEngine-AI/whisperengine/blob/main/LICENSE) for details.

---

**Need help?** Join our Discord community or check the full documentation on GitHub!