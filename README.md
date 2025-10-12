# 🎭 WhisperEngine

**AI Character Platform with Persistent Memory & Adaptive Learning Intelligence**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Alpha](https://img.shields.io/badge/Status-Alpha-orange.svg)](https://github.com/whisperengine-ai/whisperengine)

> 🚀 **Get started in 2 minutes** with our single-command setup! [Jump to Quick Start](#-quick-start) ↓

## 🎯 What is WhisperEngine?

**WhisperEngine is an advanced AI character platform** that lets you create, customize, and deploy AI characters with unique personalities, persistent memory, and intelligent conversation capabilities.

**Perfect for:**
- 🎮 **Game Masters** creating NPCs with persistent memory and evolving personalities
- 📚 **Writers & Storytellers** developing character interactions and dialogue
- 🎭 **Creative Projects** exploring AI roleplay and character development
- 💼 **Businesses** building custom AI assistants with specific expertise
- 🔬 **Researchers** studying AI conversation patterns and personality modeling

## ✨ Key Features

### 🧠 **Advanced AI Characters**
- **Multi-Character Support** - Deploy multiple AI characters simultaneously
- **Persistent Memory** - Characters remember conversations and relationships
- **Adaptive Learning** - Characters improve responses based on interactions
- **Personality Modeling** - Define unique traits, values, and communication styles

### 🛠️ **Easy Setup & Management**
- **Single Command Setup** - Get running in 2 minutes
- **Web-Based Interface** - Create and manage characters through intuitive UI
- **Docker-Based** - No complex dependencies or manual configuration
- **Cross-Platform** - Works on Windows, macOS, and Linux

### 🔧 **Developer-Friendly**
- **REST API** - Integrate with any application
- **Discord Integration** - Optional Discord bot functionality
- **Multiple LLM Support** - OpenRouter, OpenAI, Claude, or local models
- **Open Source** - MIT licensed and community-driven

## 🚀 Quick Start (End Users)

Get WhisperEngine running with a **single command** - no technical setup required:

### **Prerequisites**
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- An LLM API key (OpenRouter recommended for beginners)
- **No Git, source code, or programming knowledge required!**

### **1-Command Setup**

**macOS/Linux:**
```bash
curl -sSL https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/setup-containerized.sh | bash
```

**Windows (PowerShell - Recommended):**
```powershell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/setup-containerized.ps1" -OutFile "setup.ps1"; .\setup.ps1
```

**Windows (Command Prompt):**
```cmd
curl -sSL https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/setup-containerized.bat -o setup.bat && setup.bat
```

The setup script will:
1. ✅ Check Docker is running
2. 📦 Download only configuration files (~5KB)
3. 🐳 Pull pre-built containers from Docker Hub
4. 📝 Create your configuration file 
5. 🔧 Open the config file for you to add your API key
6. 🚀 Start all services automatically
7. 🌐 Open the web interface in your browser

### **What You Get**

After setup completes, you'll have:

- **🌐 Web Interface**: http://localhost:3001 - Create and manage characters
- **💬 Chat API**: http://localhost:9090/api/chat - Direct API access
- **📊 Health Dashboard**: http://localhost:9090/health - System status
- **🔍 Vector Database**: Qdrant for intelligent memory storage
- **💾 PostgreSQL**: Character definitions and user data

## 🎭 Creating Your First Character

1. **Open the Web Interface**: http://localhost:3001
2. **Click "Create New Character"**
3. **Define Basic Info**:
   - Name and description
   - Personality traits
   - Communication style
4. **Set Character Knowledge**:
   - Background and experiences
   - Expertise areas
   - Values and beliefs
5. **Save & Deploy** - Your character is ready to chat!

## 💬 Testing Your Character

### **Via Web Interface**
- Use the built-in chat interface at http://localhost:3001

### **Via API**
```bash
curl -X POST http://localhost:9090/api/chat \\
  -H "Content-Type: application/json" \\
  -d '{
    "user_id": "test_user",
    "message": "Hello! Tell me about yourself.",
    "context": {"platform": "api"}
  }'
```

### **Via Discord** (Optional)
1. Create a Discord bot at https://discord.com/developers/applications
2. Add the bot token to your `.env` file
3. Set `ENABLE_DISCORD=true`
4. Restart: `docker-compose restart`

## 🔧 Troubleshooting

### **Setup Failed or Database Errors?**

If you encounter errors like "relation already exists" or other deployment issues, run the cleanup script:

**macOS/Linux:**
```bash
curl -sSL https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/cleanup-docker.sh | bash
```

**Windows (PowerShell):**
```powershell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/cleanup-docker.ps1" -OutFile "cleanup.ps1"; .\cleanup.ps1
```

**Windows (Command Prompt):**
```cmd
curl -sSL https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/cleanup-docker.bat -o cleanup.bat && cleanup.bat
```

Then run the setup command again. See [Cleanup Guide](docs/deployment/CLEANUP_SCRIPTS.md) for details.

### **Other Issues?**
- Check [Troubleshooting Guide](docs/troubleshooting/README.md)
- Verify Docker Desktop is running
- Ensure ports 9090, 3001, 5432, 6333, and 8086 are available
- View logs: `docker logs whisperengine-assistant`

## ⚙️ Configuration Options

Edit your `.env` file to customize WhisperEngine settings. 

> **📋 Need Help Editing?** See our **[Configuration Guide](docs/guides/edit-env-after-quickstart.md)** for step-by-step instructions on configuring LLM providers, Discord integration, and more.

```bash
# Required: LLM Configuration (ALL fields required)
LLM_CLIENT_TYPE=openrouter  # Used for: setup hints and logging only
LLM_CHAT_API_URL=https://openrouter.ai/api/v1  # CRITICAL: Determines actual provider
LLM_CHAT_API_KEY=your_api_key_here
LLM_CHAT_MODEL=mistralai/mistral-small  # RECOMMENDED: Start with tested models

# Optional: Discord Integration
DISCORD_BOT_TOKEN=your_discord_token
ENABLE_DISCORD=true

# Optional: Advanced Settings
CHARACTER_NAME=assistant    # Default character name
```

> **⚠️ IMPORTANT**: `LLM_CHAT_API_URL` is what **actually determines your LLM provider** - WhisperEngine auto-detects the provider from the URL pattern. `LLM_CLIENT_TYPE` is mainly used for setup hints and logging.

### **Supported LLM Providers**

| Provider | `LLM_CLIENT_TYPE` | `LLM_CHAT_API_URL` | Recommended Models | API Key Required? |
|----------|-------------------|--------------------|--------------------|-------------------|
| **OpenRouter** (Recommended) | `openrouter` | `https://openrouter.ai/api/v1` | **✅ Mistral**: `mistralai/mistral-small-3.2-24b-instruct`, `mistralai/mistral-medium-3.1`, `mistralai/mistral-nemo`<br>**✅ GPT-4/5**: `openai/gpt-4o`, `openai/gpt-5-chat`<br>**✅ Claude Sonnet**: `anthropic/claude-sonnet-4`, `anthropic/claude-3.7-sonnet`, `anthropic/claude-3.5-sonnet` | ✅ Yes - [Get key](https://openrouter.ai) |
| **OpenAI Direct** | `openai` | `https://api.openai.com/v1` | **✅ GPT-4**: `gpt-4o`<br>**✅ GPT-5**: `gpt-5-chat` | ✅ Yes - [Get key](https://platform.openai.com) |
| **Ollama** (Local) | `ollama` | `http://host.docker.internal:11434/v1` | Your downloaded model | ❌ No - runs locally |
| **LM Studio** (Local) | `lmstudio` | `http://host.docker.internal:1234/v1` | Your downloaded model | ❌ No - runs locally |

> **🎯 Getting Started**: We **strongly recommend starting with `mistralai/mistral-small`** via OpenRouter - it's been thoroughly tested with WhisperEngine and provides excellent character consistency. All models listed above have been tested and work well for AI characters.

## 📚 Documentation

- **[Quick Start Guide](docs/guides/QUICKSTART.md)** - Detailed end-user setup instructions
- **[Development Guide](docs/development/DEVELOPMENT_GUIDE.md)** - Developer setup and contribution guide
- **[Installation Guide](INSTALLATION.md)** - Complete installation options
- **[Container Operations Guide](CONTAINERIZED_OPERATIONS_GUIDE.md)** - Updates, backups, troubleshooting
- **[Character Creation Guide](docs/characters/CHARACTER_AUTHORING_GUIDE.md)** - Advanced character building
- **[API Documentation](docs/api/README.md)** - Integration guide
- **[Discord Setup](docs/discord/DISCORD_SETUP.md)** - Discord bot configuration
- **[Troubleshooting](docs/troubleshooting/README.md)** - Common issues and solutions

## 🌟 Example Characters

WhisperEngine comes with example characters to get you started:

- **🧬 Elena Rodriguez** - Marine Biologist with environmental expertise
- **🤖 Marcus Thompson** - AI Researcher focused on machine learning
- **🎮 Ryan Chen** - Indie Game Developer with creative insights
- **🎭 Gabriel** - British Gentleman with sophisticated conversation
- **📈 Sophia Blake** - Marketing Executive with business acumen

## 🛟 Getting Help & Support

- **📖 Documentation**: [Quick Start](docs/guides/QUICKSTART.md) | [Troubleshooting](docs/troubleshooting/README.md)
- **🧹 Need to Start Fresh?**: [Cleanup Guide](docs/deployment/CLEANUP_SCRIPTS.md)
- **🐛 Bug Reports**: [GitHub Issues](https://github.com/whisperengine-ai/whisperengine/issues)
- **💬 Discussions**: [GitHub Discussions](https://github.com/whisperengine-ai/whisperengine/discussions)

## 🔧 Advanced Setup

For production deployment, multi-character setups, or custom configurations:

- **[Multi-Character Setup](docs/setup/MULTI_CHARACTER_SETUP.md)** - Run multiple characters simultaneously
- **[Production Deployment](docs/deployment/PRODUCTION_SETUP.md)** - Secure, scalable deployment
- **[Custom Models](docs/setup/LOCAL_LLM_SETUP.md)** - Use local or custom LLM models
- **[API Integration](docs/api/INTEGRATION_GUIDE.md)** - Embed in your applications

## 🤝 Contributing

WhisperEngine is open source and welcomes contributions!

- **[Contributing Guide](CONTRIBUTING.md)** - How to contribute
- **[Development Setup](docs/development/DEVELOPMENT_SETUP.md)** - Local development environment
- **[Architecture Overview](docs/architecture/README.md)** - System design and components

## 📄 License

WhisperEngine is licensed under the **MIT License**. See [LICENSE](LICENSE) for details.

---

## 💡 Why WhisperEngine?

Unlike simple chatbots, WhisperEngine creates **persistent AI characters** with:

- ✅ **Memory** - Characters remember past conversations and relationships
- ✅ **Personality** - Consistent traits, values, and communication styles  
- ✅ **Intelligence** - Adaptive learning and contextual responses
- ✅ **Flexibility** - Easy customization and deployment options
- ✅ **Integration** - REST API for embedding in any application

**Start building your AI characters today!** 🚀

```bash
# For end users (no technical setup required):
curl -sSL https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/setup-containerized.sh | bash
```

---

## 🔧 Developer Setup

For developers who want to modify WhisperEngine's source code:

```bash
# Clone the repository
git clone https://github.com/whisperengine-ai/whisperengine.git
cd whisperengine

# Docker-based development (RECOMMENDED - primary workflow)
./multi-bot.sh start elena  # Start development bot

# Alternative: Native Python (requires manual dependency setup)
python run.py  # Not recommended - use Docker for consistency
```

**See**: [Development Guide](docs/development/DEVELOPMENT_GUIDE.md) for complete Docker-based development workflow.

**Developer Requirements:**
- Docker Desktop for containerized development
- Git for source code management
- Python 3.11+ (for utility scripts only)
- Your preferred code editor