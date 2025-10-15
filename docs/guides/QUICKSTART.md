# 🚀 WhisperEngine Quick Start Guide

**Get your AI character platform running in under 5 minutes - no technical setup required!**

> **Important**: This guide is for **end users** who want to use WhisperEngine without technical setup. If you're a developer wanting to modify the source code, see [Development Guide](../development/DEVELOPMENT_GUIDE.md).

## 📋 Prerequisites

### **Required Software**
- **[Docker Desktop](https://www.docker.com/products/docker-desktop/)** - Download and install, then start it
- **An LLM API Key** - Get one from [OpenRouter](https://openrouter.ai) (recommended for beginners)

### **System Requirements**
- **Windows 10+**, **macOS 10.15+**, or **Linux**
- **4GB RAM minimum** (8GB recommended)
- **5GB free disk space** for containers and data
- **Internet connection** for downloading containers

### **What You DON'T Need**
- ❌ Git or source code
- ❌ Programming knowledge
- ❌ Python, Node.js, or development tools
- ❌ Manual configuration files

## 🚀 One-Command Installation

### **macOS/Linux:**
```bash
curl -sSL https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/setup-containerized.sh | bash
```

### **Windows (PowerShell - Recommended):**
```powershell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/setup-containerized.ps1" -OutFile "setup.ps1"; .\setup.ps1
```

### **Windows (Command Prompt):**
```cmd
curl -sSL https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/setup-containerized.bat -o setup.bat && setup.bat
```

## 📝 What Happens During Setup

The setup script will:

1. ✅ **Check Docker** - Verify Docker Desktop is running
2. 📦 **Download Configuration** - Get only the files needed (~5KB)
3. 🐳 **Pull Containers** - Download pre-built WhisperEngine containers (~2GB)
4. 📝 **Create Configuration** - Set up your `.env` file
5. 🔧 **Open Editor** - Let you add your LLM API key
6. 🚀 **Start Services** - Launch all WhisperEngine components
7. 🌐 **Open Browser** - Show you the web interface

## 🔑 Configure Your LLM Provider

After setup, you'll need to add your LLM configuration to the `.env` file:

> **🔧 Need Help with Configuration?** See our detailed **[Configuration Guide](edit-env-after-quickstart.md)** for step-by-step instructions on setting up LLM providers, Discord integration, and more.

> **💡 Key Concept**: `LLM_CHAT_API_URL` is what **actually determines** your LLM provider (WhisperEngine auto-detects from the URL). `LLM_CLIENT_TYPE` is mainly used for setup hints and logging.

### **Option 1: OpenRouter (Recommended) - ✅ TESTED**
```bash
# Get API key at https://openrouter.ai
LLM_CLIENT_TYPE=openrouter              # Used for: setup hints and logging
LLM_CHAT_API_URL=https://openrouter.ai/api/v1  # CRITICAL: Determines provider
LLM_CHAT_API_KEY=your_openrouter_key_here
LLM_CHAT_MODEL=mistralai/mistral-small-3.2-24b-instruct  # RECOMMENDED: Thoroughly tested with WhisperEngine
```

**✅ Tested Models for AI Characters** (via OpenRouter):

**Mistral Models** (Best for character consistency):
- ✅ **`mistralai/mistral-small-3.2-24b-instruct`** - Best balance of performance and cost (RECOMMENDED)
- ✅ **`mistralai/mistral-medium-3.1`** - More capable for complex characters
- ✅ **`mistralai/mistral-nemo`** - Good for detailed interactions

**GPT-4 & GPT-5 Models** (Excellent quality):
- ✅ **`openai/gpt-4o`** - Highly capable GPT-4 model
- ✅ **`openai/gpt-5-chat`** - Latest GPT-5 reasoning model

**Claude Sonnet Models** (Premium quality):
- ✅ **`anthropic/claude-sonnet-4`** - Latest Claude Sonnet 4 (newest)
- ✅ **`anthropic/claude-3.7-sonnet`** - Claude Sonnet 3.7
- ✅ **`anthropic/claude-3.5-sonnet`** - Claude Sonnet 3.5

> **⚠️ Avoid**: Claude Haiku (expensive, poor character consistency), GPT-3.5-turbo (outdated), GPT-4o-mini (inconsistent)

### **Option 2: OpenAI Direct**
```bash
# Get API key at https://platform.openai.com
LLM_CLIENT_TYPE=openai
LLM_CHAT_API_URL=https://api.openai.com/v1
LLM_CHAT_API_KEY=your_openai_key_here
LLM_CHAT_MODEL=gpt-4o  # GPT-4 recommended
```

**Recommended Models**:
- ✅ **`gpt-4o`** - GPT-4 Omni model
- ✅ **`gpt-5-chat`** - Latest GPT-5 reasoning

### **Option 3: Ollama (Local) - ❌ No API Key Needed**
```bash
# Download Ollama from https://ollama.com
# Start Ollama and pull a model: ollama pull llama3
LLM_CLIENT_TYPE=ollama
LLM_CHAT_API_URL=http://host.docker.internal:11434/v1
LLM_CHAT_API_KEY=not-needed  # Local model - no API key required
LLM_CHAT_MODEL=llama3  # or your preferred model
```

**Note**: Ollama runs locally on your machine - no API key or internet connection required for inference.

### **Option 4: LM Studio (Local) - ❌ No API Key Needed**
```bash
# Download LM Studio from https://lmstudio.ai
# Start LM Studio server (default port 1234)
LLM_CLIENT_TYPE=lmstudio
LLM_CHAT_API_URL=http://host.docker.internal:1234/v1
LLM_CHAT_API_KEY=not-needed  # Local model - no API key required
LLM_CHAT_MODEL=your-downloaded-model-name
```

**Note**: LM Studio runs locally on your machine - no API key or internet connection required for inference.

> **🎯 First-Time Users**: Start with **`mistralai/mistral-small-3.2-24b-instruct`** via OpenRouter! It's been thoroughly tested and provides excellent character consistency at reasonable cost. All models listed above work well for AI characters.


## 🌐 Access Your AI Platform

After setup completes, you can access:

### **Web Interface** (Primary)
- **URL**: http://localhost:3001
- **Use For**: Creating characters, managing settings, chatting with AI
- **Features**: Full WhisperEngine functionality

### **Chat API** (Integration)
- **URL**: http://localhost:9090/api/chat
- **Use For**: Integrating with your own applications
- **Format**: REST API with JSON responses

### **Health Dashboard**
- **URL**: http://localhost:9090/health
- **Use For**: Checking system status and performance

## 🎨 Creating Your First Character

1. **Open Web Interface**: http://localhost:3001
2. **Click "Create New Character"**
3. **Define Basic Info**:
   - Character name and description
   - Personality traits and values
   - Communication style preferences
4. **Set Background Knowledge**:
   - Professional expertise
   - Personal experiences
   - Interests and hobbies
5. **Configure Behavior**:
   - Response style (formal, casual, creative)
   - Emotional patterns
   - Knowledge areas
6. **Save & Test**: Your character is ready to chat!

## 💬 Testing Your Character

### **Via Web Interface**
- Use the built-in chat at http://localhost:3001
- Test different conversation types
- Verify personality consistency

### **Via API**
```bash
curl -X POST http://localhost:9090/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "message": "Hello! Tell me about yourself.",
    "context": {"platform": "api"}
  }'
```

### **Via Discord** (Optional)
1. Create a Discord bot at https://discord.com/developers/applications
2. Add the bot token to your `.env` file:
   ```bash
   DISCORD_BOT_TOKEN=your_discord_token
   ENABLE_DISCORD=true
   ```
3. Stop and restart: `docker-compose stop && docker-compose up -d`

## 🔄 Managing Your Installation

### **Daily Operations**

**Start WhisperEngine:**
```bash
docker-compose up -d
```

**Stop WhisperEngine:**
```bash
docker-compose down
```

**View Logs:**
```bash
docker logs whisperengine-assistant
```

**Check Status:**
```bash
docker ps
```

### **Updates**

**Update to Latest Version:**
```bash
# Stop current version
docker-compose down

# Pull latest containers
docker-compose pull

# Start with new version
docker-compose up -d
```

**Check Version:**
```bash
curl http://localhost:9090/health
```

## 🔧 Troubleshooting

### **Common Issues**

**Docker Not Running:**
```bash
# Check Docker status
docker info

# Make sure Docker Desktop is started
```

**Port Already in Use:**
```bash
# Check what's using the ports (3001, 9090, 5432, 6333)
lsof -i :3001  # macOS/Linux
netstat -ano | findstr :3001  # Windows

# Stop the conflicting service or change ports
```

**API Key Not Working:**
- Verify your API key is correct (no extra spaces)
- Test at provider's website (OpenRouter: https://openrouter.ai)
- Check logs: `docker logs whisperengine-assistant`

**Containers Won't Start:**
```bash
# Check logs for errors
docker-compose logs

# Check system resources
docker system df

# Clean up if low on space
docker system prune
```

### **Complete Reset**

**Clean Restart (keeps data):**
```bash
docker-compose down
docker-compose up -d
```

**Nuclear Reset (deletes ALL data):**
```bash
# ⚠️ WARNING: This deletes ALL your characters and conversations!
docker-compose down -v
docker volume prune
docker-compose up -d
```

### **Database Migration (v1.0.6 → v1.0.8+)**

If upgrading from v1.0.6:
```bash
# Update containers first
docker-compose down
docker-compose pull
docker-compose up -d

# Mark existing database as current
docker exec whisperengine-assistant alembic stamp head
```

## 💾 Data Backup

**Create Backup:**
```bash
# Create backup directory
mkdir -p whisperengine-backups/$(date +%Y%m%d_%H%M%S)

# Backup PostgreSQL (characters, memories)
docker run --rm \
  -v whisperengine_postgres_data:/source:ro \
  -v $(pwd)/whisperengine-backups/$(date +%Y%m%d_%H%M%S):/backup \
  alpine tar czf /backup/postgres_data.tar.gz -C /source .

# Backup Qdrant (vector memories)
docker run --rm \
  -v whisperengine_qdrant_data:/source:ro \
  -v $(pwd)/whisperengine-backups/$(date +%Y%m%d_%H%M%S):/backup \
  alpine tar czf /backup/qdrant_data.tar.gz -C /source .
```

**Restore from Backup:**
```bash
# Stop services
docker-compose down

# Remove existing volumes (⚠️ deletes current data)
docker volume rm whisperengine_postgres_data whisperengine_qdrant_data

# Restore (replace BACKUP_DATE with your backup folder)
BACKUP_DATE="20241012_143000"

docker run --rm \
  -v whisperengine_postgres_data:/target \
  -v $(pwd)/whisperengine-backups/$BACKUP_DATE:/backup:ro \
  alpine tar xzf /backup/postgres_data.tar.gz -C /target

docker run --rm \
  -v whisperengine_qdrant_data:/target \
  -v $(pwd)/whisperengine-backups/$BACKUP_DATE:/backup:ro \
  alpine tar xzf /backup/qdrant_data.tar.gz -C /target

# Start with restored data
docker-compose up -d
```

## 🛠️ Advanced Configuration

### **Model Selection**

Try different AI models by editing `.env`:

```bash
# Fast and affordable (recommended for testing)
LLM_CHAT_MODEL=anthropic/claude-3-haiku

# More capable (higher cost)
LLM_CHAT_MODEL=anthropic/claude-3.5-sonnet
LLM_CHAT_MODEL=openai/gpt-4o

# Open source alternatives (via OpenRouter)
LLM_CHAT_MODEL=meta-llama/llama-3.1-8b-instruct
LLM_CHAT_MODEL=mistralai/mistral-7b-instruct
```

### **Discord Integration**

1. **Create Discord Bot**: https://discord.com/developers/applications
2. **Add to `.env`**:
   ```bash
   DISCORD_BOT_TOKEN=your_bot_token_here
   ENABLE_DISCORD=true
   ```
3. **Stop and restart**: `docker-compose stop && docker-compose up -d`
4. **Invite Bot**: Use OAuth2 URL Generator in Discord Developer Portal

### **Multi-Character Setup**

See [Multi-Character Guide](../setup/MULTI_CHARACTER_SETUP.md) for running multiple AI characters simultaneously.

## 📚 Next Steps

### **Learn More**
- **[Character Creation Guide](../characters/CHARACTER_AUTHORING_GUIDE.md)** - Advanced character building
- **[API Documentation](../api/README.md)** - Integrate with your applications
- **[Development Guide](../development/DEVELOPMENT_GUIDE.md)** - For developers

### **Advanced Features**
- **Persistent Memory**: Characters remember conversations
- **Adaptive Learning**: Characters improve over time
- **Emotional Intelligence**: Sophisticated emotion analysis
- **Vector Memory**: Semantic understanding and recall

### **Production Use**
- **[Production Deployment](../deployment/PRODUCTION_SETUP.md)** - Secure, scalable setup
- **[Monitoring Setup](../monitoring/README.md)** - Performance monitoring

## 🆘 Getting Help

- **📖 Documentation**: [Troubleshooting Guide](../troubleshooting/README.md)
- **🐛 Bug Reports**: [GitHub Issues](https://github.com/whisperengine-ai/whisperengine/issues)
- **💬 Discussions**: [GitHub Discussions](https://github.com/whisperengine-ai/whisperengine/discussions)

---

## 👨‍💻 For Developers

**Want to modify WhisperEngine or contribute code?**

This quickstart is for end users. Developers need source code access:

```bash
# Clone the repository
git clone https://github.com/whisperengine-ai/whisperengine.git
cd whisperengine

# Follow the development guide
# See: docs/development/DEVELOPMENT_GUIDE.md
```

**Developer Requirements:**
- Git for source code access
- Python 3.11+ for local development
- Node.js for web UI development
- Docker for containerized development

---

**🎉 Congratulations!** You now have a fully functional AI character platform running locally. Start creating your first character and explore the possibilities of persistent AI personalities! 🚀
