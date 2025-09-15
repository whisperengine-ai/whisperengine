# 🎭 WhisperEngine - Privacy-First AI Character Bot

[![Docker Build](https://github.com/WhisperEngine-AI/whisperengine/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/WhisperEngine-AI/whisperengine/actions/workflows/docker-publish.yml)
[![Docker Hub](https://img.shields.io/docker/pulls/whisperengine/whisperengine.svg)](https://hub.docker.com/r/whisperengine/whisperengine)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Create deeply personalized AI characters that run completely locally.** Your conversations, personality configurations, and memories never leave your computer. No subscriptions, no censorship, no data mining.

## 🎯 **Choose Your Path**

### 👤 **Non-Technical Users** - Just Want to Chat with AI?
**[📥 DOWNLOAD PRE-BUILT APP](USERS.md)** - Ready-to-run executables (~18GB)
- Download → Extract → Run → Chat immediately
- No technical setup required
- Works completely offline
- 100% private and secure

### 🔧 **Developers & Technical Users** - Want to Customize?
**[⚡ DEVELOPER SETUP](DEVELOPERS.md)** - Source code installation
- Full customization capabilities
- Discord bot integration
- Docker deployment options
- Contribute to development

---

## 📚 **Quick Navigation**

- 🚀 **[60-Second Setup](QUICK_START.md)** - Get WhisperEngine running immediately
- 📖 **[Complete Build & User Guide](BUILD_AND_USER_GUIDE.md)** - Comprehensive setup instructions  
- 🏗️ **[Deployment Guide](DEPLOYMENT_GUIDE.md)** - Production deployment scenarios
- 📄 **[Setup Card](SETUP_CARD.md)** - One-page reference for quick setup

**🎯 Super Quick Start**: 
- Discord Bot: `python discord-bot/run-discord.py` for cloud-powered Discord bot
- Desktop App: `python desktop-app/run-desktop.py` for private local AI chat
- See [Deployment Structure Guide](DEPLOYMENT_STRUCTURE.md) for details

## ✨ **Key Features**

### � **Multi-Phase AI Intelligence**
- **Phase 1**: Advanced language model responses with context awareness
- **Phase 2**: Emotional intelligence that adapts to user mood and conversation tone  
- **Phase 3**: Sophisticated memory networks that remember relationships and preferences
- **Phase 4**: Human-like conversation adaptation with deep personality modeling

### 🎨 **Complete Character Customization**
- **Personality Engine**: Define unique speaking patterns, vocabulary, and behavioral traits
- **Memory System**: Characters remember past conversations and develop relationships
- **Emotional Intelligence**: Responds appropriately to user emotions and context
- **Hot-Reload Personalities**: Edit character traits and see changes instantly

### 🔒 **Privacy-First Architecture** 
- **100% Local**: All AI processing happens on your machine
- **Zero Data Collection**: No telemetry, analytics, or cloud dependencies
- **Secure Memory**: Conversation history stays in your local databases
- **Open Source**: Full transparency with auditable code

### 🏗️ **Enterprise-Grade Infrastructure**
- **Modular Architecture**: ChromaDB + Redis + PostgreSQL + Neo4j support
- **Horizontal Scaling**: Each component scales independently  
- **Production Ready**: Docker orchestration with health monitoring
- **Multi-Modal**: Text, voice, and image processing capabilities

## 🚀 **Quick Start - Cross Platform**

### ⚡ **Lightning Quick (2 minutes) - Choose Your Platform**

WhisperEngine supports all major platforms with native quick-start scripts:

| Platform | Command | Description |
|----------|---------|-------------|
| **🐧 Linux** | `curl -sSL https://raw.githubusercontent.com/WhisperEngine-AI/whisperengine/main/scripts/quick-start.sh \| bash` | Native Bash script |
| **🍎 macOS** | `curl -sSL https://raw.githubusercontent.com/WhisperEngine-AI/whisperengine/main/scripts/quick-start.sh \| bash` | Native Bash script |
| **🪟 Windows PowerShell** | `iwr https://raw.githubusercontent.com/WhisperEngine-AI/whisperengine/main/scripts/quick-start.ps1 \| iex` | Native PowerShell script |
| **🪟 Windows Command Prompt** | Download and run: [`quick-start.bat`](https://raw.githubusercontent.com/WhisperEngine-AI/whisperengine/main/scripts/quick-start.bat) | Native Batch script |

#### **Quick Installation Examples:**

**Linux/macOS:**
```bash
# One command setup - no cloning required!
curl -sSL https://raw.githubusercontent.com/WhisperEngine-AI/whisperengine/main/scripts/quick-start.sh | bash
```

**Windows PowerShell:**
```powershell
# One command setup - no cloning required!
iwr https://raw.githubusercontent.com/WhisperEngine-AI/whisperengine/main/scripts/quick-start.ps1 | iex
```

**Windows Command Prompt:**
```batch
@REM Download and run the batch script
curl -L -o quick-start.bat https://raw.githubusercontent.com/WhisperEngine-AI/whisperengine/main/scripts/quick-start.bat
quick-start.bat
```

All scripts will:
1. Download the latest WhisperEngine configuration
2. Set up your environment file (.env)
3. Open your editor to configure Discord token
4. Start all services with Docker Compose

**Perfect for:** First-time users, quick demos, production deployments across any platform

**📖 [Full Docker Hub Guide →](docs/getting-started/DOCKER_HUB_QUICK_START.md)**

### 🔧 **Developer Setup (5 minutes)**
```bash
# 1. Clone and enter directory
git clone https://github.com/whisperengine-ai/whisperengine
cd whisperengine

# 2. Configure (get Discord token from discord.com/developers)
cp .env.minimal .env
nano .env  # Set DISCORD_BOT_TOKEN

# 3. Start your local LLM (LM Studio, Ollama, etc.)
#    OR use optimized llama-cpp-python: python setup_llamacpp.py

# 4. Launch bot
./bot.sh start
```
**Perfect for:** Customization, development, advanced features

**Your character bot is now running!** Edit files in the `prompts/` directory to customize your AI's personality.

## 📚 **Documentation**

| Guide | Audience | Time | Description |
|-------|----------|------|-------------|
| **[🌍 Cross-Platform Quick Start](docs/getting-started/CROSS_PLATFORM_QUICK_START.md)** | All Users | 2 min | Native scripts for Linux, macOS, Windows |
| **[⚡ Docker Hub Quick Start](docs/getting-started/DOCKER_HUB_QUICK_START.md)** | All Users | 2 min | Instant deployment from Docker Hub |
| **[🚀 Developer Quick Start](docs/getting-started/QUICK_START.md)** | Developers | 5 min | Full setup with customization |
| **[👥 End User Guide](docs/getting-started/END_USER_GUIDE.md)** | End Users | 15 min | Complete setup and usage |
| **[💻 Development Guide](docs/development/DEVELOPMENT_GUIDE.md)** | Developers | 30 min | Customize and extend the bot |
| **[🔑 API Configuration](docs/configuration/API_KEY_CONFIGURATION.md)** | All Users | 10 min | LLM provider setup |
| **[🐳 Docker Hub Publishing](docs/deployment/DOCKER_HUB_SETUP.md)** | Maintainers | 15 min | Automated Docker publishing setup |
| **[🧠 Memory System](docs/ai-systems/MEMORY_SYSTEM_README.md)** | Advanced | 20 min | Understanding AI memory |
| **[🎭 Character Creation](docs/character/character_prompt_guide.md)** | All Users | 15 min | Creating unique personalities |

## 🎯 **AI System Configuration**

WhisperEngine provides unified full AI capabilities:

### **Complete AI Intelligence** - Always Active
- **Requirements**: RECOMMENDED - 16GB RAM, modern CPU, GPU required (for AI models) with at least 12GB VRAM
- **Features**: Complete LLM capabilities, emotional intelligence, advanced memory networks
- **Best for**: All production environments and use cases

```bash
# Configure AI behavior style in .env
AI_MEMORY_OPTIMIZATION=true
AI_EMOTIONAL_RESONANCE=true
```

## 🏛️ **Architecture Overview**

### **Modular Component System**
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Discord Bot   │────│  LLM Interface   │────│  Local AI Model │
│   (Frontend)    │    │  (OpenAI Compatible)  │  (LM Studio/Ollama) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │
         ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Memory Manager  │────│   Vector Store   │────│   Conversation │
│ (Intelligence)  │    │   (ChromaDB)     │    │   Cache (Redis) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │
         ▼
┌─────────────────┐    ┌──────────────────┐
│ Personality     │────│   Persistent     │
│ Engine          │    │   Data (Postgres) │
└─────────────────┘    └──────────────────┘
```

### **Key Technologies**
- **AI/ML**: OpenAI-compatible APIs, Transformer models, Embedding systems
- **Databases**: ChromaDB (vectors), Redis (cache), PostgreSQL (persistence), Neo4j (relationships)
- **Infrastructure**: Docker, Docker Compose, Modular Python architecture
- **Security**: Input validation, memory isolation, admin access controls

## 🛠️ **Advanced Configuration**

### **🎭 Character Personality Customization**

**Easy personality switching** - Choose from pre-built templates or create your own:

```bash
# Switch to different personalities via environment variable
BOT_SYSTEM_PROMPT_FILE=./prompts/professional_ai_template.md    # Business assistant
BOT_SYSTEM_PROMPT_FILE=./prompts/empathetic_companion_template.md # Supportive friend
BOT_SYSTEM_PROMPT_FILE=./prompts/casual_friend_template.md       # Casual chat buddy
```

**Hot-reload support** - Edit any file in the `prompts/` directory and changes apply immediately (no restart needed!)

**Available personalities:**
- 🌙 **Dream** (default) - Formal, mystical character from The Sandman
- 💝 **Empathetic Companion** - Supportive, caring friend for emotional support
- 👔 **Professional AI** - Business assistant for work tasks
- 😊 **Casual Friend** - Relaxed, friendly for everyday conversations
- 🎭 **Character AI** - Template for roleplay characters
- 🧠 **Adaptive AI** - Self-learning personality that adapts to users

📖 **[Full Customization Guide](docs/character/SYSTEM_PROMPT_CUSTOMIZATION.md)** - Complete setup instructions

### **LLM Provider Support**
- **Local Optimized**: llama-cpp-python (GGUF models) - **Recommended for best performance** 🚀
- **Local HTTP**: LM Studio, Ollama, GPT4All
- **Cloud**: OpenAI, OpenRouter, Anthropic
- **Self-Hosted**: Any OpenAI-compatible API

📖 **[llama-cpp-python Setup Guide](LLAMACPP_INTEGRATION.md)** - Optimized local inference

### **Memory & Intelligence**
- **Vector Memory**: Semantic similarity search across conversations
- **Graph Memory**: Relationship mapping and context understanding  
- **Emotional Memory**: Mood tracking and adaptive responses
- **Conversation Cache**: Fast access to recent interactions

## 🔧 **Development & Deployment**

### **Development Mode**
```bash
# Native development with hot-reload
./bot.sh start native
python run.py

# Full containerized development  
./bot.sh start dev
```

### **Production Deployment**
```bash
# Production mode with optimization
./bot.sh start

# With custom configuration
cp .env.production .env
./bot.sh start
```

## 🎯 **Use Cases**

- **Virtual Companions**: Create AI friends with unique personalities
- **Interactive NPCs**: Game characters that remember player interactions  
- **Educational Assistants**: Subject-matter experts with teaching styles
- **Creative Partners**: Writing collaborators with distinct voices
- **Therapeutic Bots**: Supportive listeners with emotional intelligence
- **Brand Personalities**: Customer service agents with company voice

## 🌟 **What Makes WhisperEngine Special**

### **Privacy-First Design**
Unlike cloud-based AI services, WhisperEngine ensures your conversations never leave your machine. Build intimate relationships with AI characters without privacy concerns.

### **True Personality Depth**  
Beyond simple prompt engineering, WhisperEngine creates characters with:
- Consistent behavioral patterns across conversations
- Emotional growth and relationship development
- Memory of shared experiences and inside jokes
- Adaptive communication styles based on context

### **Production-Ready Architecture**
Built for real-world deployment with enterprise-grade infrastructure:
- Fault-tolerant service mesh with health monitoring
- Horizontal scaling capabilities for high-traffic scenarios  
- Comprehensive logging and debugging systems
- Modular design for easy feature extension

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 **Contributing**

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details on:
- Setting up the development environment
- Code style and architecture patterns  
- Testing and validation procedures
- Submitting pull requests

## 💬 **Support**

- **Documentation**: Comprehensive guides in the `docs/` directory
- **Issues**: Report bugs and request features via GitHub Issues
- **Community**: Join discussions in GitHub Discussions

---

**Ready to create your first AI character?** Start with the [Quick Start Guide](docs/getting-started/QUICK_START.md) and bring your digital personality to life! 🎭
