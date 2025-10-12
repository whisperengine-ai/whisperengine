# 🎭 WYour WhisperEngine instance includes:

- **🤖 Discord Bot** - AI-powered with personality and memory
- **🔍 Qdrant** - Vector database for semantic memory (384D embeddings)
- **🐘 PostgreSQL** - Persistent data storage
- **🏥 Health Monitoring** - Container health checks on port 9090gine Quick Start

**Congratulations!** You've successfully set up WhisperEngine using our quick-start script.

## 🚀 What You Have

Your WhisperEngine instance includes:

- **🤖 Discord Bot** - AI-powered with personality and memory
- **🔍 Qdrant** - Vector database for semantic memory (384D embeddings)
- **⚡ Redis** - Fast conversation caching  
- **🐘 PostgreSQL** - Persistent data storage
- **🏥 Health Monitoring** - Container health checks on port 9090
- **� InfluxDB** - Optional temporal intelligence metrics

## ⚙️ What You Need to Provide

### Required Files (User-Provided):

| File | Purpose | Example |
|------|---------|---------|
| **`.env`** | Your configuration (Discord token, API keys, etc.) | See `.env.minimal` for template |
| **`character.json`** | Your CDL character definition | Your custom AI personality |
| **`docker-compose.yml`** | Already provided in this directory | - |

### Optional:
| File | Purpose |
|------|---------|
| **`characters/`** | Directory with multiple character files | Mount as `./characters:/app/characters:ro` |

## 🚀 Quick Setup

### 1. Create Your Configuration

> **📋 Need Help with Configuration?** See our **[Configuration Guide](../../docs/guides/edit-env-after-quickstart.md)** for step-by-step instructions on setting up LLM providers, Discord integration, and all configuration options.

```bash
# Copy the template and customize it
cp .env.minimal .env
nano .env  # Add your Discord token, LLM API settings, etc.
```

### 2. Provide Your Character
```bash
# Create or copy your CDL character file
# Place it as character.json in the same directory as docker-compose.yml
cp your-character.json character.json
```

### 3. Deploy
```bash
docker-compose up -d
```

## 💾 Data Persistence Options

### Default: Docker Named Volumes
```bash
# Data is stored in Docker's internal directory
# Persists between container restarts/updates
docker volume ls  # See volumes: whisperengine_postgres_data, etc.
```

### Alternative: Host Filesystem Mounts
For easier backup and direct access to data:

```bash
# 1. Create data directories
mkdir -p data/{postgres,qdrant}

# 2. Edit docker-compose.yml - uncomment the host mount lines:
# - ./data/postgres:/var/lib/postgresql/data  
# - ./data/qdrant:/qdrant/storage

# 3. Comment out the named volume lines
```

**Benefits of host mounts:**
- ✅ Easy backup (`cp -r data/ backup/`)
- ✅ Direct file access for debugging
- ✅ Clear data location (`./data/`)
- ✅ Portable between systems

## 🌐 Cross-Platform Compatibility

✅ **Works on all platforms:**
- **macOS** (Intel & Apple Silicon)
- **Linux** (x86_64 & ARM64)  
- **Windows** (WSL2 + Docker Desktop)

✅ **Multi-architecture Docker images:**
- Automatically pulls correct image for your CPU architecture
- `linux/amd64` and `linux/arm64` supported

### Requirements
- **Docker**: Docker Desktop (macOS/Windows) or Docker Engine (Linux)
- **Memory**: 4GB+ RAM recommended (2GB minimum)
- **Storage**: 10GB+ free disk space
- **Ports**: 5432, 6333, 6334, 9090 available

> 📖 **Detailed setup guide**: See `CROSS_PLATFORM_DOCKER.md` for platform-specific instructions and troubleshooting.
2. Create a new application
3. Go to "Bot" section
4. Copy the token

### 2. Invite Your Bot to Discord
1. In Discord Developer Portal, go to "OAuth2" → "URL Generator"
2. Select scopes: `bot`, `applications.commands`
3. Select permissions: `Send Messages`, `Read Message History`, `Use Slash Commands`
4. Copy the generated URL and open it to invite your bot

### 3. Start Your Local LLM (Optional)
WhisperEngine works best with a local LLM like:
- **LM Studio** - Download and start a model on port 1234
- **Ollama** - Run `ollama serve` 
- **Text Generation WebUI** - Run on default port

### 4. Choose a Personality (Optional)
Uncomment one line in your `.env` file:
```bash
# Choose one:
CDL_DEFAULT_CHARACTER=characters/examples/elena-rodriguez.json    # 💝 Supportive companion
BOT_SYSTEM_PROMPT_FILE=./prompts/professional_ai_template.md        # 👔 Business assistant
BOT_SYSTEM_PROMPT_FILE=./prompts/casual_friend_template.md          # 😊 Casual chat buddy
```

## 🎛️ Managing Your Bot

### Essential Commands
```bash
# View live logs
docker-compose logs -f whisperengine

# Restart the bot
docker-compose restart whisperengine

# Stop everything
docker-compose down

# Start everything
docker-compose up -d

# Update to latest version
docker-compose pull && docker-compose up -d
```

### Health Checking
```bash
# Check all services
docker-compose ps

# Test health endpoints
curl http://localhost:9090/health
curl http://localhost:9090/ready
curl http://localhost:9090/metrics

# Individual service logs
docker-compose logs redis
docker-compose logs postgres  
docker-compose logs qdrant
```

## 🎭 Personality Customization

Your bot comes with several pre-built personalities in the `prompts/` directory:

- **💝 Empathetic Companion** - Supportive and caring
- **👔 Professional AI** - Business-focused assistant  
- **😊 Casual Friend** - Relaxed and friendly
- **🎭 Character AI** - Template for roleplay characters
- **🧠 Adaptive AI** - Learns and adapts to users
- **✨ Dream AI Enhanced** - Enhanced Dream of the Endless persona

**Hot-reload:** Edit any file in the `prompts/` directory and changes apply instantly!

## 🔧 Troubleshooting

### Bot Not Responding
1. Check Discord token in `.env` file
2. Verify bot is invited to your server
3. Check logs: `docker-compose logs whisperengine`

### Services Not Starting
1. Ensure Docker Desktop is running
2. Check available ports (6379, 5432, 8000)
3. Verify internet connection for image downloads

### Memory/Performance Issues
1. Allocate 4GB+ RAM to Docker Desktop
2. Enable disk space optimization
3. Consider disabling Neo4j if not needed

## 📚 Advanced Configuration

For complete configuration options, check:
- **`.env.example`** - Full configuration template
- **[Documentation](https://github.com/WhisperEngine-AI/whisperengine/wiki)** - Complete guides
- **[Character Creation](../../docs/character/character_prompt_guide.md)** - Custom personalities

## 🌟 What's Next?

- **🎨 Create Custom Personalities** - Define unique character traits
- **🧠 Explore Memory Features** - Watch your bot remember conversations
- **🔗 Add Graph Relationships** - Enable Neo4j for advanced memory
- **📱 Multi-Modal Support** - Add image and voice capabilities

---

🎭 **Dream of the Endless now dwells in your Discord server...**
*The realm of conversations and stories awaits!*

**Need Help?** Visit our [GitHub Discussions](https://github.com/WhisperEngine-AI/whisperengine/discussions)