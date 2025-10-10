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

## 🚀 Quick Start

Get WhisperEngine running with a **single command**:

### **Prerequisites**
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- An LLM API key (OpenRouter recommended for beginners)
- **No Git or source code required!**

### **1-Command Setup**

**macOS/Linux:**
```bash
curl -sSL https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/setup-containerized.sh | bash
```

**Windows (Command Prompt):**
```cmd
curl -sSL https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/setup-containerized.bat -o setup.bat && setup.bat
```

**Windows (PowerShell):**
```powershell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/setup-containerized.bat" -OutFile "setup.bat"; .\setup.bat
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
4. Restart: `docker-compose -f docker-compose.quickstart.yml restart`

## 🔧 Configuration Options

Edit your `.env` file to customize:

```bash
# Required: LLM Configuration
LLM_CHAT_API_KEY=your_api_key_here
LLM_CHAT_MODEL=anthropic/claude-3-haiku  # Recommended for beginners

# Optional: Discord Integration
DISCORD_BOT_TOKEN=your_discord_token
ENABLE_DISCORD=true

# Optional: Advanced Settings
LLM_CLIENT_TYPE=openrouter  # or: openai, local
CHARACTER_NAME=assistant    # Default character name
```

### **Supported LLM Providers**

| Provider | Model Examples | Setup |
|----------|---------------|--------|
| **OpenRouter** (Recommended) | `anthropic/claude-3-haiku`<br>`openai/gpt-4o-mini` | Get API key at [openrouter.ai](https://openrouter.ai) |
| **OpenAI** | `gpt-4o-mini`<br>`gpt-3.5-turbo` | Get API key at [platform.openai.com](https://platform.openai.com) |
| **Local Models** | Via LM Studio or Ollama | See [Local Setup Guide](docs/setup/LOCAL_LLM_SETUP.md) |

## 📚 Documentation

- **[Quick Start Guide](QUICKSTART.md)** - Detailed setup instructions
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

## 🛟 Getting Help

- **📖 Documentation**: Comprehensive guides in the [docs/](docs/) folder
- **🐛 Issues**: Report bugs on [GitHub Issues](https://github.com/whisperengine-ai/whisperengine/issues)
- **💬 Community**: [Discord Server](https://discord.gg/whisperengine) (Coming Soon)
- **📧 Support**: Contact us at support@whisperengine.ai

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
# For end users (recommended):
curl -sSL https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/setup-containerized.sh | bash

# For developers:
git clone https://github.com/whisperengine-ai/whisperengine.git && cd whisperengine && ./setup.sh
```