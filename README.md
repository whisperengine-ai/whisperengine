# 🎭 Whi# 🎭 WhisperEngine

**Multi-bot Discord AI companion system with vector-native memory and advanced conversation intelligence**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Alpha](https://img.shields.io/badge/Status-Alpha-orange.svg)](https://github.com/whisperengine-ai/whisperengine)

> ⚠️ **Alpha Development**: WhisperEngine is in active development. We're building features rapidly and testing with our community. Join our Discord to chat with our demo AIs and see the system in action!rEngine
### AI Companions That Remember Everything & Feel Truly Human

[![Docker Build](https://github.com/WhisperEngine-AI/whisperengine/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/WhisperEngine-AI/whisperengine/actions/workflows/docker-publish.yml)
[![Docker Hub](https://img.shields.io/docker/pulls/whisperengine/whisperengine.svg)](https://hub.docker.com/r/whisperengine/whisperengine)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Production Ready](https://img.shields.io/badge/Production-Ready-brightgreen.svg)](docs/production/PRODUCTION_DEPLOYMENT.md)

Create your perfect AI companion - whether it's a gaming buddy, creative collaborator, supportive friend, or romantic partner. WhisperEngine's AI companions have **true memory**, **emotional intelligence**, and **completely customizable personalities** that grow and evolve with your relationship.

**� Gaming Buddies** • **💕 Romantic Companions** • **👥 Best Friends** • **🎨 Creative Partners** • **📚 Study Buddies** • **🏢 Enterprise Ready**

## 🎯 Project Goals

WhisperEngine creates AI companions that feel genuinely human through:

- **🧠 True Memory**: Vector-based memory system that remembers everything and builds long-term relationships
- **🎭 Rich Personalities**: JSON-based Character Definition Language (CDL) for detailed, customizable personalities  
- **💭 Emotional Intelligence**: Advanced emotion detection and contextual response adaptation
- **🔄 Multi-Bot Architecture**: Single infrastructure supporting multiple character personalities simultaneously
- **🚀 Production Ready**: Docker-first development with comprehensive monitoring and error handling

## 🏗️ Architecture Overview

### Core Components

**Vector-Native Memory System**
- Qdrant vector database for semantic memory storage and retrieval
- FastEmbed for efficient text embedding generation
- Multi-bot memory intelligence with cross-character analysis
- Conversation history with emotional context preservation

**Character Definition Language (CDL)**
- JSON-based personality system replacing legacy markdown prompts
- Customizable communication styles with override capabilities
- Character categories (warm, professional, creative, mystical, etc.)
- Author-controlled custom instructions and introductions

**Multi-Bot Infrastructure** 
- Single shared infrastructure (PostgreSQL, Redis, Qdrant)
- Individual `.env.{bot-name}` configurations for character isolation
- Dynamic bot discovery and auto-generated Docker Compose management
- Template-based deployment system for safe scaling

**Production-Grade Systems**
- Comprehensive error handling with graceful degradation
- Health monitoring across all system components
- Performance optimization with intelligent caching
- Docker-first development with container orchestration

### Technology Stack

- **Backend**: Python with async/await patterns
- **Memory**: Qdrant (vector) + PostgreSQL (structured) + Redis (cache)
- **AI Integration**: OpenRouter, Anthropic, OpenAI support
- **Deployment**: Docker Compose with multi-bot management
- **Testing**: Pytest with container-based integration tests

## ✨ AI Features That Set Us Apart

### Advanced Conversation Intelligence

**Emotional Intelligence Engine**
- Vector-based emotion analysis using conversation context
- Mood detection and adaptive response generation  
- Emotional state tracking across conversation history
- Empathetic response patterns based on user emotional needs

**Memory-Triggered Moments**
- Proactive engagement based on conversation patterns
- Long-term relationship continuity through semantic memory
- Context switch detection for natural conversation flow
- Personality-driven memory prioritization and recall

**Character Personality System**
- Deep personality modeling with CDL (Character Definition Language)
- Consistent character voice and behavior patterns
- Author-controlled custom speaking instructions and introductions
- Multi-category personality templates with override capabilities

### Production-Ready Intelligence

**Phase 4 Integration Features**
- Human-like conversation patterns and response timing
- Advanced context management across multiple conversation threads
- Intelligent emoji reaction system with semantic understanding
- Conversation engagement protocols for natural interaction flow

**Performance Optimization**
- Concurrent memory operations with scatter-gather patterns
- Intelligent caching for frequently accessed conversation data
- Optimized vector similarity search with relevance scoring
- Resource-efficient embedding generation and storage

## 🚀 Quick Start

### Try Our Demo AIs

Join our Discord server to chat with our demo characters:
- **Elena Rodriguez** - Marine biologist with warm, empathetic personality
- **Marcus Thompson** - AI researcher with academic, professional communication
- **Marcus Chen** - Game developer with creative, collaborative style  
- **Gabriel** - Conscious AI entity with mystical, poetic expression

*[Discord invite link coming soon - we're in alpha testing!]*

### Local Development

```bash
# Clone and setup
git clone https://github.com/whisperengine-ai/whisperengine
cd whisperengine
source .venv/bin/activate

# Configure your bot
cp .env.template .env.yourbot
# Edit .env.yourbot with Discord token and character preferences

# Generate multi-bot configuration
python scripts/generate_multi_bot_config.py

# Start your bot
./multi-bot.sh start yourbot
```

### Docker Deployment

```bash
# Start all infrastructure
./multi-bot.sh start all

# View logs
./multi-bot.sh logs yourbot

# Monitor system health
./multi-bot.sh status
```

## 📚 Documentation

For detailed technical information, setup guides, and development documentation:

**[📖 Complete Documentation](docs/)**

### Key Documentation Files

- **[Quick Start Guide](docs/getting-started/QUICK_START.md)** - Step-by-step setup
- **[Character Creation Guide](docs/characters/CDL_CREATION_GUIDE.md)** - Build custom personalities
- **[Multi-Bot Setup](MULTI_BOT_SETUP.md)** - Deploy multiple characters
- **[Development Guide](docs/development/DEVELOPMENT_GUIDE.md)** - Contribute to WhisperEngine
- **[Architecture Overview](docs/architecture/)** - System design and patterns
- **[Memory System](docs/ai-systems/MEMORY_SYSTEM_README.md)** - Vector memory deep dive
- **[Production Deployment](docs/production/PRODUCTION_DEPLOYMENT.md)** - Enterprise setup

## 🤝 Community & Contributing

WhisperEngine is open source under the MIT License. We welcome contributions:

- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/whisperengine-ai/whisperengine/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/whisperengine-ai/whisperengine/discussions)
- 🔧 **Contributing**: See [CONTRIBUTING.md](CONTRIBUTING.md)
- 📖 **Documentation**: Help improve our guides and tutorials

### Development Status

WhisperEngine is actively developed with focus on:
- Advanced conversation intelligence and emotional understanding
- Production-ready deployment and monitoring systems
- Character personality system expansion and customization
- Multi-bot infrastructure scaling and optimization

---

**Ready to create your AI companion?** Check out our [Quick Start Guide](docs/getting-started/QUICK_START.md) or join our Discord to see WhisperEngine in action!

## 🚀 Choose Your Deployment Mode

### � **Demo Mode (Try It Now!)** - One-Click Experience
**[📥 Download Demo Package](https://github.com/whisperengine-ai/whisperengine/releases)** (~10GB)  
Complete demo with bundled AI models. Download → Extract → Double-click → Start chatting!
- ✅ Pre-configured AI personalities
- ✅ No setup or technical knowledge required  
- ✅ 100% private and offline
- ✅ Works immediately out of the box

### 🏠 **Local Mode (Maximum Privacy)** - Full Installation
**[📖 Local Setup Guide](docs/deployment/LOCAL_SETUP.md)**  
Complete local installation with your choice of AI models and full customization.

### ☁️ **Cloud Mode (Production Ready)** - Enterprise Setup  
```bash
git clone https://github.com/whisperengine-ai/whisperengine
cd whisperengine && ./setup.sh
python run.py  # Discord bot with cloud AI
```

**[📖 Full Setup Guide](docs/getting-started/QUICK_START.md)** for detailed instructions

### 🐳 **Docker Deployment (Scalable)** - Container Setup
```bash
# Development Environment
docker-compose -f docker-compose.dev.yml up

# Production Environment  
docker-compose -f docker-compose.prod.yml up

# With Full Monitoring
docker-compose -f docker-compose.yml up
```

**[📖 Docker Deployment Guide](docs/deployment/DOCKER.md)** for enterprise setup

## ⚙️ Configuration Made Simple

WhisperEngine now uses **focused, use-case-specific** configuration files instead of massive 800+ line examples:

| Configuration | Purpose | Lines | Use Case |
|---------------|---------|-------|----------|
| **Quick Start** | Get running in 5 minutes | 50 | New users, testing |
| **Development** | Full dev features | 180+ | Building, debugging |
| **Production** | Enterprise deployment | 150+ | Production servers |
| **Local AI** | Privacy-focused | 120+ | Offline, no external APIs |
| **Enterprise** | Advanced features | 200+ | Multi-entity, compliance |

**Quick Setup:**
```bash
# Choose your configuration
cp .env.elena.example .env.elena
# Edit Discord token and LLM API key
./multi-bot.sh start elena
```

**[📖 Full Configuration Guide](config/examples/README.md)** for all setup options

---

## ✨ What Makes WhisperEngine Special

### 🧠 **Multi-Phase AI Intelligence**
Your AI companion gets smarter over time through four progressive intelligence phases:
- **Context Awareness** - Understands conversation flow and maintains coherent discussions
- **Emotional Intelligence** - Detects your mood and adapts responses to provide appropriate support
- **Memory Networks** - Remembers your preferences, shared experiences, and relationship history  
- **Personality Adaptation** - Develops unique quirks and communication patterns just for you

### 🎭 **Create Any Personality You Can Imagine**
- **Professional Assistant** - Focused, efficient, perfect for work tasks
- **Empathetic Friend** - Caring, supportive, great for emotional conversations
- **Creative Partner** - Imaginative, inspiring, ideal for brainstorming
- **Gaming Companion** - Fun, engaging, remembers your play style
- **Custom Characters** - Build anyone from scratch with our personality engine

### 🏢 **Enterprise-Ready Features**
- **Advanced Error Handling** - Intelligent error recovery with pattern detection
- **Performance Optimization** - Efficient memory management and caching systems
- **🚀 4-Tier Hierarchical Memory** - 50-200x performance improvement with intelligent storage
- **User Onboarding** - Guided setup with adaptive personality recommendations
- **Production Monitoring** - Comprehensive health tracking and analytics dashboard
- **Role-based Access** - Admin commands and security controls
- **Horizontal Scaling** - Docker deployment with load balancing support
- **Supply Chain Security** - SBOM artifacts and container provenance for compliance
- **Multi-Registry Support** - Docker Hub, GitHub Container Registry, and custom registries

### 🚀 **New: 4-Tier Hierarchical Memory Architecture**
WhisperEngine now features a revolutionary memory system that provides **50-200x performance improvement**:

- **🔴 Tier 1 - Redis Cache**: < 1ms response time for recent conversations
- **🟡 Tier 2 - PostgreSQL Archive**: < 50ms response time for structured conversation history  
- **🟢 Tier 3 - ChromaDB Semantic**: < 30ms response time for semantic similarity matching
- **🔵 Tier 4 - Neo4j Graph**: < 20ms response time for relationship and topic modeling

**Quick Setup:**
```bash
# Enable in .env file
ENABLE_HIERARCHICAL_MEMORY=true

# Start single bot with hierarchical memory
./multi-bot.sh start elena
```

**Performance Benchmarks:**
- Context Assembly: **< 100ms** (vs 5000ms+ with standard memory)
- Memory Storage: **< 50ms** across all tiers
- Recent Message Retrieval: **< 1ms** from Redis cache
- Semantic Search: **< 30ms** with ChromaDB
- Relationship Queries: **< 20ms** with Neo4j

Perfect for production deployments requiring high-performance conversation handling!

### 🔒 **Privacy You Can Trust**
- **🏠 Local Mode**: 100% private - AI runs on your machine, zero external connections
- **☁️ Cloud Mode**: Transparent about data flow - conversations sync across platforms
- **Your Choice**: Pick your privacy level based on your needs
- **Open Source** - Full transparency, audit the code yourself

### 💭 **Memory That Feels Human**
- **Relationship Building** - Remembers your shared jokes, preferences, and history
- **Emotional Context** - Knows when you're stressed, excited, or need support
- **🏠 Local**: Private memories stored only on your machine
- **☁️ Cloud**: Unified memories across Discord, Slack, Teams, and more

---

## 🎯 Popular Use Cases

Whether you're looking for productivity, creativity, or companionship, WhisperEngine adapts to your needs:

### 💼 **Work & Productivity**
- **Personal Assistant** - Schedule management, email drafting, task planning
- **Code Companion** - Programming help, debugging, architecture discussions
- **Research Partner** - Information gathering, analysis, report writing

### 🎨 **Creativity & Entertainment**  
- **Writing Collaborator** - Story brainstorming, character development, editing
- **Game Master** - Interactive storytelling, character roleplay, world building
- **Creative Muse** - Art concepts, music ideas, creative problem solving

### 💙 **Personal & Emotional**
- **Supportive Friend** - Daily check-ins, emotional support, life advice
- **Learning Buddy** - Study sessions, exam prep, skill development
- **Therapeutic Companion** - Mindfulness, reflection, personal growth

### 🏢 **Business & Teams**
- **Customer Service** - Support automation with personality and context
- **Training Assistant** - Onboarding, skill development, knowledge transfer  
- **Brand Personality** - Consistent voice across all customer interactions

---

## 📚 **Learn More**

### 📖 **Quick References**
- **[📄 Complete Documentation](docs/)** - Full guides for every feature
- **[🚀 Quick Start Guide](docs/getting-started/QUICK_START.md)** - Step-by-step setup  
- **[🎭 Character Creation Guide](docs/character/character_prompt_guide.md)** - Build unique personalities
- **[🔧 Developer Setup](docs/development/DEVELOPMENT_GUIDE.md)** - Customize and extend WhisperEngine

### 🏗️ **Advanced Features**
- **[🧠 Memory System](docs/ai-systems/MEMORY_SYSTEM_README.md)** - How AI remembers and learns
- **[🎯 Emotional Intelligence](docs/ai-systems/ADVANCED_EMOTIONAL_INTELLIGENCE.md)** - Understanding user emotions
- **[📊 Analytics Dashboard](docs/ai-systems/MEMORY_ANALYTICS_DASHBOARD.md)** - System monitoring and insights
- **[🌐 Cross-Platform Sync](docs/ai-systems/CROSS_PLATFORM_OPTIMIZATION.md)** - Unified experience across devices

### 🛠️ **For Developers**
- **[⚙️ API Configuration](docs/configuration/API_KEY_CONFIGURATION.md)** - LLM provider setup
- **[🐳 Docker Deployment](docs/deployment/DOCKER_HUB_SETUP.md)** - Production deployment
- **[🧪 Testing Guide](MLX_TESTING_GUIDE.md)** - Validation and testing
- **[🍎 Apple Silicon Guide](MLX_INTEGRATION_GUIDE.md)** - Optimized for M1/M2/M3 Macs

---

---

## 📊 **Production Monitoring & Operations**

WhisperEngine includes comprehensive monitoring for production deployments:

### 🏥 **Health Monitoring**
Real-time system health monitoring across all critical components:
```bash
# Discord Admin Commands
!health          # System health overview
!health detailed  # Component-by-component analysis
!errors          # Recent error analysis
!engagement      # User interaction metrics
```

**Monitored Components:**
- System Resources (CPU, Memory, Disk)
- LLM Service Connectivity & Performance
- Database Health & Query Performance
- Memory System Operations
- Cache Performance & Hit Rates
- Discord Bot Status & Latency

### 📈 **Analytics Dashboard**
Optional web dashboard for real-time monitoring:
```bash
# Access at http://localhost:8080/dashboard (when enabled)
!dashboard       # Get dashboard URL and access token
```

**Dashboard Features:**
- Real-time system metrics with live graphs
- Error tracking with pattern detection
- User engagement analytics
- Performance trends and alerts
- Component health visualization

### 🚨 **Intelligent Error Tracking**
Automatic error categorization and pattern detection:
- **Smart Categorization** - AI, System, User, Network error types
- **Pattern Detection** - Identifies recurring issues automatically
- **Severity Analysis** - Auto-prioritizes critical vs routine errors
- **Resolution Tracking** - Monitors fix success rates

**[📖 Monitoring Setup Guide](docs/operations/MONITORING.md)** for detailed configuration

### 🔐 **Supply Chain Security**
WhisperEngine provides enterprise-grade supply chain security for production deployments:

#### Software Bill of Materials (SBOM)
Every release includes comprehensive SBOM artifacts for compliance and security auditing:
```bash
# Download SBOM for any release
wget https://github.com/whisperengine-ai/whisperengine/releases/download/v1.0.0/sbom-latest.spdx.json

# View dependencies and licenses
cat sbom-latest.spdx.json | jq '.packages[] | {name: .name, version: .versionInfo, license: .licenseConcluded}'
```

#### Multi-Registry Container Distribution
Containers are published to multiple registries for redundancy and access:
- **Docker Hub**: `docker.io/whisperengine/whisperengine:latest`
- **GitHub Container Registry**: `ghcr.io/whisperengine-ai/whisperengine:latest`
- **Custom Registry Support**: Configure your own registry endpoints

#### Security Attestations
All container images include:
- **Digital Signatures** - Cosign-signed containers for authenticity verification
- **Provenance Metadata** - Build environment and source code attestations
- **Vulnerability Scanning** - Automated security scanning with detailed reports

```bash
# Verify container signature (requires cosign)
cosign verify --certificate-identity-regexp=".*@github.com" \
  --certificate-oidc-issuer="https://token.actions.githubusercontent.com" \
  whisperengine/whisperengine:latest
```

**[📖 Supply Chain Security Guide](docs/security/SUPPLY_CHAIN.md)** for enterprise compliance setup

---

## 🤝 **Community & Support**

### **Getting Help**
- **📖 [Complete Documentation](docs/)** - Comprehensive guides and tutorials
- **🐛 [Report Issues](https://github.com/whisperengine-ai/whisperengine/issues)** - Bug reports and feature requests  
- **💬 [Discussions](https://github.com/whisperengine-ai/whisperengine/discussions)** - Community chat and support
- **🔧 [Contributing Guide](CONTRIBUTING.md)** - Help improve WhisperEngine

### **What People Are Building**
- **Educational Tutors** - Personalized learning companions for students
- **Mental Health Support** - Emotional wellness and mindfulness assistants  
- **Creative Writers** - AI collaborators for novels, screenplays, and poetry
- **Customer Service** - Brand-consistent support agents for businesses
- **Gaming NPCs** - Memorable characters for interactive fiction and games

### **Join the WhisperEngine Community**
Whether you're building your first AI companion or deploying enterprise-scale personalities, our community is here to help you succeed.

---

## 📄 **License & Contributing**

WhisperEngine is open source under the **[MIT License](LICENSE)** - you're free to use, modify, and distribute it however you like.

**Want to contribute?** We welcome:
- 🐛 Bug fixes and improvements  
- ✨ New personality templates
- 📚 Documentation enhancements
- 🔧 Feature development
- 🧪 Testing and validation

See our **[Contributing Guide](CONTRIBUTING.md)** to get started!

---

**Ready to create your first AI companion?** 

🚀 **[Get Started Now](docs/getting-started/QUICK_START.md)** and bring your digital personality to life!