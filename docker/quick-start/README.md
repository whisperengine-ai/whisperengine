# 🎭 WhisperEngine Quick Start

**Congratulations!** You've successfully set up WhisperEngine using our quick-start script.

## 🚀 What You Have

Your WhisperEngine instance includes:

- **🤖 Discord Bot** - AI-powered with personality and memory
- **🧠 ChromaDB** - Vector database for semantic memory
- **⚡ Redis** - Fast conversation caching
- **🐘 PostgreSQL** - Persistent data storage
- **🏥 Health Monitoring** - Container health checks on port 9090
- **🕸️ Neo4j** - Optional graph relationships (disabled by default)

## ⚙️ Configuration Files

| File | Purpose | Visibility |
|------|---------|------------|
| **`.env`** | Main configuration (used by Docker) | Hidden (use `ls -la`) |
| **`env.example`** | Visible copy for reference | Visible |
| **`characters/`** | Bot character definitions directory | Visible |
| **`docker-compose.yml`** | Service definitions | Visible |

## 🎯 Next Steps

### ⚠️ Important: Docker Hub Images
**Note**: The quick-start uses pre-built images from Docker Hub. For maximum security:
- **Production**: Build your own images using the main repository
- **Development**: Use the development setup from the main repo
- **Quick Testing**: This setup is perfect for trying WhisperEngine

### 1. Configure Your Bot Token
Edit your `.env` file and set:
```bash
DISCORD_BOT_TOKEN=your_actual_discord_bot_token_here
```

**Get a Discord Bot Token:**
1. Go to https://discord.com/developers/applications
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
docker-compose logs chromadb
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