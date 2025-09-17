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
- Discord Bot: `python run.py` - cloud-powered Discord bot (from project root)
- Desktop App: `python universal_native_app.py` - private local AI chat (from project root)
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

# 2. Quick setup with automated configuration
./setup.sh  # Interactive setup for all dependencies and environment

# 3. Start Discord bot OR desktop app
source .venv/bin/activate && python run.py            # Discord bot
source .venv/bin/activate && python universal_native_app.py  # Desktop app

# Optional: Validate your installation
python validate_build_system.py  # Comprehensive validation
```
**Perfect for:** Customization, development, advanced features

**Your AI is now running!** The setup script automatically:
- Creates virtual environment
- Installs all dependencies  
- Configures environment from `.env.example`
- Sets up your choice of Discord bot or desktop app

## 📚 **Documentation**

| Guide | Audience | Time | Description |
|-------|----------|------|-------------|
| **[🌍 Cross-Platform Quick Start](docs/getting-started/CROSS_PLATFORM_QUICK_START.md)** | All Users | 2 min | Native scripts for Linux, macOS, Windows |
| **[⚡ Docker Hub Quick Start](docs/getting-started/DOCKER_HUB_QUICK_START.md)** | All Users | 2 min | Instant deployment from Docker Hub |
| **[🚀 Developer Quick Start](docs/getting-started/QUICK_START.md)** | Developers | 5 min | Full setup with customization |
| **[👥 End User Guide](docs/getting-started/END_USER_GUIDE.md)** | End Users | 15 min | Complete setup and usage |
| **[💻 Development Guide](docs/development/DEVELOPMENT_GUIDE.md)** | Developers | 30 min | Customize and extend the bot |
| **[🔑 API Configuration](docs/configuration/API_KEY_CONFIGURATION.md)** | All Users | 10 min | LLM provider setup |
| **[� Build Validation](validate_build_system.py)** | Developers | 2 min | Validate all build methods and deployment options |
| **[�🐳 Docker Hub Publishing](docs/deployment/DOCKER_HUB_SETUP.md)** | Maintainers | 15 min | Automated Docker publishing setup |
| **[🍎 MLX Integration Guide](MLX_INTEGRATION_GUIDE.md)** | Apple Users | 20 min | Native Apple Silicon optimization |
| **[🧪 MLX Testing Guide](MLX_TESTING_GUIDE.md)** | Developers | 15 min | Comprehensive MLX validation |
| **[🧠 Memory System](docs/ai-systems/MEMORY_SYSTEM_README.md)** | Advanced | 20 min | Understanding AI memory |
| **[🔄 Memory Aging System](docs/ai-systems/MEMORY_AGING.md)** | Advanced | 15 min | Intelligent memory consolidation & aging |
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

# Memory Aging System (Sprint 4 - NEW!)
MEMORY_AGING_ENABLED=true
MEMORY_DECAY_LAMBDA=0.01
MEMORY_PRUNE_THRESHOLD=0.2
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
```bash
# Recommended: Simple native development
python run.py

# Alternative: Infrastructure services + native bot
./bot.sh start infrastructure
python run.py

# Full containerized production deployment  
./bot.sh start prod
```
```

### **Production Deployment**
```bash
# Production mode with optimization
./bot.sh start

# With custom configuration
cp .env.production .env
./bot.sh start
```

### 📊 Observability & Metrics

WhisperEngine ships with a lightweight in‑process metrics collector (no external deps) guarded by `ENABLE_METRICS_LOGGING` (default: `true`). It tracks counters & timings for emotional assessment, memory importance, retrieval, pattern learning hooks, and end‑to‑end conversation phases.

Key tooling:

| Purpose | Command (venv active) | Output |
|---------|-----------------------|--------|
| One‑time Sprint 1‑3 feature verification (human readable) | `python verify_sprint_features.py` | Console summary |
| Same verification + machine readable JSON | `python verify_sprint_features.py --json verifications/sprint1_3.json` | JSON file |
| Ad‑hoc metrics snapshot (no workload) | `python scripts/metrics/export_snapshot.py --output metrics_snapshot.json --pretty` | Current counters & timings |
| Reset metrics after snapshot | `python scripts/metrics/export_snapshot.py --reset` | Snapshot + collector cleared |
| Baseline synthetic workload + KPIs | `python scripts/perf/collect_baseline.py --iterations 25 --output baseline_perf.json` | KPIs + raw metrics |

Environment Flag:

```
# .env
ENABLE_METRICS_LOGGING=true   # set false to disable collection
```

Example verification JSON payload structure:

```jsonc
{
    "generated_at": "2025-09-16T12:34:56.123456+00:00",
    "summary": { "total_checks": 7, "passed": 7, "percentage": 100.0 },
    "results": {
        "environment_config": true,
        "database_connectivity": true,
        "sprint1_emotional_intelligence": true,
        "sprint2_memory_importance": true,
        "sprint3_emotional_memory_bridge": true,
        "sprint3_automatic_learning": true,
        "full_integration": true
    },
    "environment": {
        "enable_emotional_intelligence": "true",
        "enable_phase3_memory": "true"
    }
}
```

Metrics snapshot JSON (truncated example):

```jsonc
{
    "generated_at": "2025-09-16T12:35:10.789012+00:00",
    "metrics_enabled": true,
    "snapshot": {
        "counters": [ { "name": "interventions_triggered", "value": 4, "labels": {"type": "support"} } ],
        "timings": [ { "name": "emotional_assessment_seconds", "avg_seconds": 0.034, "count": 10, "min_seconds": 0.028, "max_seconds": 0.042 } ]
    }
}
```

Use cases:
* CI artifact comparison (`git diff` on JSON files) for performance regressions
* Local tuning & before/after measurements when adjusting emotional or memory algorithms
* Historical baselines (store `baseline_perf.json` per release)

> Tip: Pair a metrics snapshot before & after running a workload to measure incremental cost of a new feature.


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
