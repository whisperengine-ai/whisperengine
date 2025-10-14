# 🎭 WhisperEngine

**AI Character Platform with Persistent Memory & Adaptive Learning Intelligence**

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Alpha](https://img.shields.io/badge/Status-Alpha-orange.svg)](https://github.com/whisperengine-ai/whisperengine)

> 🚀 **Get started in 2 minutes** with our single-command setup! [Jump to Quick Start](#-quick-start) ↓

## 🎯 What is WhisperEngine?

**WhisperEngine is an advanced AI character platform** that creates human-like, emotionally intelligent chatbots through three core pillars of sophisticated AI conversation technology.

**Perfect for:**
- 🎮 **Game Masters** creating NPCs with persistent memory and evolving personalities
- 📚 **Writers & Storytellers** developing character interactions and dialogue
- 🎭 **Creative Projects** exploring AI roleplay and character development
- 💼 **Businesses** building custom AI assistants with specific expertise
- 🔬 **Researchers** studying AI conversation patterns and personality modeling

## 🏗️ The Three Pillars of Human-Like AI Conversation

WhisperEngine is built on three foundational technologies that create truly believable and helpful AI characters:

### 🎭 **Pillar 1: Robust Emotion Recognition**
*Going beyond simple keywords to understand emotional nuance, intensity, and flow*

- **🤖 RoBERTa Transformer Analysis** - State-of-the-art emotion detection with 0.7-0.95 confidence
- **📊 Multi-Emotion Detection** - Recognizes 2-3 simultaneous emotions in complex conversations  
- **🔍 Advanced Emotional Intelligence** - 12+ metadata fields per emotion analysis
- **⚡ Real-Time Processing** - Sub-second emotion analysis with cultural adaptation

### 🧠 **Pillar 2: Long-Term Contextual Memory**
*Remembering not just facts, but past emotional states and key relationship events*

- **🎯 Vector-Native Memory** - 384D embeddings for semantic relationship understanding
- **💾 Persistent Conversations** - Characters remember users across sessions and platforms
- **🔄 Intelligent Retrieval** - Context-aware memory search with emotional pattern recognition
- **📈 Relationship Tracking** - Long-term relationship development and user preference learning

### ❤️ **Pillar 3: Empathetic Response Generation**
*AI that responds supportively, appropriately, and feels genuine - not just programmed*

- **🎭 Character Definition Language (CDL)** - Unique personalities with authentic empathy patterns
- **🌟 Adaptive Responses** - Real-time emotional adaptation maintaining character consistency
- **🎯 Cultural Authenticity** - Character-appropriate empathy (Elena's warmth vs Marcus's analytical support)
- **💭 Contextual Intelligence** - Responses calibrated to emotional state and conversation history

---

**🔬 Want to understand how it all works?** Read our comprehensive guide: **[How WhisperEngine's AI Characters Learn and Remember You](docs/guides/HOW_AI_CHARACTERS_LEARN.md)** - a detailed technical walkthrough of the specialized systems working together to create human-like AI conversations.

## ✨ Platform Features

### 🛠️ **Easy Setup & Management**
- **Single Command Setup** - Get running in 2 minutes
- **Web-Based Interface** - Create and manage characters through intuitive UI
- **Docker-Based** - No complex dependencies or manual configuration
- **Cross-Platform** - Works on Windows, macOS, and Linux

### 🔧 **Developer-Friendly**
- **REST API** - Integrate with any application
- **Discord Integration** - Optional Discord bot functionality
- **Multiple LLM Support** - OpenRouter, OpenAI, Claude, or local models
- **Open Source** - GNU GPL v3 licensed and community-driven

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

**📋 Follow-up Guides:**
- **[Configuration Guide](docs/guides/edit-env-after-quickstart.md)** - Configure LLM providers, Discord, advanced settings
- **[Troubleshooting](docs/troubleshooting/README.md)** - Common issues and solutions
- **[Cleanup Scripts](docs/deployment/CLEANUP_SCRIPTS.md)** - Fresh restart if needed

### **What You Get**

After setup completes, you'll have a complete emotional AI platform:

- **🌐 Web Interface**: http://localhost:3001 - Create and manage emotionally intelligent characters
- **💬 Chat API**: http://localhost:9090/api/chat - Direct API access with emotion analysis
- **� Health Check**: http://localhost:9090/health - Basic system status
- **🧠 Vector Database**: Qdrant for intelligent memory and emotional pattern storage
- **💾 PostgreSQL**: Character definitions, user relationships, and conversation history

**Technical Foundation:**
- **🤖 RoBERTa Emotion Analysis** - j-hartmann/emotion-english-distilroberta-base transformer
- **🎯 384D Vector Embeddings** - Semantic memory with emotional context awareness
- **📈 Real-Time Intelligence** - Sub-second emotion detection and contextual memory retrieval

## 🎭 Creating Your First Character

WhisperEngine's character creation process incorporates all three pillars for human-like AI:

1. **Open the Web Interface**: http://localhost:3001
2. **Click "Create New Character"**
3. **🎭 Define Emotional Personality**:
   - Emotional response patterns and empathy style
   - Communication preferences and cultural traits
   - How they recognize and respond to user emotions
4. **🧠 Set Character Knowledge & Memory**:
   - Background experiences and expertise areas
   - Values, beliefs, and relationship patterns
   - Professional knowledge and personal interests
5. **❤️ Configure Empathy & Response Style**:
   - How they show support and understanding
   - Character-appropriate ways of offering help
   - Authentic voice and conversation patterns
6. **Save & Deploy** - Your emotionally intelligent character is ready!

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
4. Stop and restart: `docker-compose stop && docker-compose up -d`

## 🔧 Troubleshooting

**Setup issues?** Run the [cleanup script](docs/deployment/CLEANUP_SCRIPTS.md) and try setup again.

**Other issues?** Check the **[Troubleshooting Guide](docs/troubleshooting/README.md)** or view logs: `docker logs whisperengine-assistant`

## ⚙️ Configuration

WhisperEngine requires an LLM API key to function. The setup script will guide you through configuration.

**📋 [Complete Configuration Guide](docs/guides/edit-env-after-quickstart.md)** - LLM providers, Discord integration, advanced settings

**Quick Config:**
```bash
# Required: Add your LLM API key
LLM_CHAT_API_URL=https://openrouter.ai/api/v1
LLM_CHAT_API_KEY=your_api_key_here
LLM_CHAT_MODEL=mistralai/mistral-small
```

**Recommended**: Start with [OpenRouter](https://openrouter.ai) + `mistralai/mistral-small` for best character consistency.

## 📚 Documentation

**Getting Started:**
- **[Quick Start Guide](docs/guides/QUICKSTART.md)** - Detailed setup instructions
- **[Configuration Guide](docs/guides/edit-env-after-quickstart.md)** - LLM providers and settings
- **[Troubleshooting](docs/troubleshooting/README.md)** - Common issues and solutions

**Advanced:**
- **[Character Creation](docs/characters/CHARACTER_AUTHORING_GUIDE.md)** | **[API Reference](docs/api/CHAT_API_REFERENCE.md)** | **[Multi-Character Setup](docs/setup/MULTI_CHARACTER_SETUP.md)**
- **[Development Guide](docs/development/DEVELOPMENT_GUIDE.md)** - For developers and contributors

## 🌟 Example Characters

WhisperEngine includes example characters that demonstrate the three pillars in action:

- **🧬 Elena Rodriguez** - Marine Biologist with passionate environmental expertise and warm empathy
- **🤖 Marcus Thompson** - AI Researcher with analytical precision and research-backed responses  
- **🎮 Ryan Chen** - Indie Game Developer with creative problem-solving and technical wisdom
- **🎭 Gabriel** - British Gentleman with sophisticated conversation and cultural depth
- **📈 Sophia Blake** - Marketing Executive with business acumen and professional empathy

Each character demonstrates:
- **🎭 Unique Emotional Patterns** - Distinct ways of recognizing and responding to emotions
- **🧠 Specialized Memory** - Domain expertise with contextual knowledge retrieval
- **❤️ Authentic Empathy** - Character-appropriate supportive responses

## 🛟 Getting Help

**[Troubleshooting Guide](docs/troubleshooting/README.md)** | **[Cleanup Scripts](docs/deployment/CLEANUP_SCRIPTS.md)** | **[GitHub Issues](https://github.com/whisperengine-ai/whisperengine/issues)** | **[Discussions](https://github.com/whisperengine-ai/whisperengine/discussions)**

## 🔧 Advanced Setup

**[Production Deployment](docs/deployment/PRODUCTION_SETUP.md)** | **[Multi-Character Setup](docs/setup/MULTI_CHARACTER_SETUP.md)** | **[Local LLM Models](docs/setup/LOCAL_LLM_SETUP.md)**

## 🤝 Contributing

WhisperEngine is open source and welcomes contributions!

- **[Contributing Guide](CONTRIBUTING.md)** - How to contribute
- **[Development Setup](docs/development/DEVELOPMENT_SETUP.md)** - Local development environment
- **[Architecture Overview](docs/architecture/README.md)** - System design and components

## 📄 License

WhisperEngine is licensed under the **GNU General Public License v3.0**. See [LICENSE](LICENSE) for details.

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

---

## 💡 Why WhisperEngine?

Unlike simple chatbots, WhisperEngine creates **human-like AI characters** through sophisticated conversation technology:

### 🎭 **Advanced Emotion Understanding**
- **Beyond Keywords** - RoBERTa transformer models detect emotional nuance and intensity
- **Multi-Emotion Analysis** - Recognizes complex emotional states (joy + anxiety, excitement + worry)
- **Emotional Memory** - Characters remember your emotional patterns and respond appropriately

### 🧠 **Deep Contextual Memory**  
- **Relationship Awareness** - Characters build understanding of your personality and preferences
- **Conversation Continuity** - Seamless memory across sessions, days, and platforms
- **Intelligent Retrieval** - Finds relevant memories based on emotional and semantic context

### ❤️ **Genuine Empathetic Responses**
- **Character-Authentic Empathy** - Elena shows marine biologist enthusiasm, Marcus offers analytical support
- **Emotionally Calibrated** - Responses adapted to your current emotional state
- **Supportive & Appropriate** - Feels genuine, not programmed or robotic

**The result?** AI characters that feel **authentically human** - they understand you, remember you, and respond with genuine care and expertise.

**Start building your emotionally intelligent AI characters today!** 🚀

```bash
# For end users (no technical setup required):
curl -sSL https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/setup-containerized.sh | bash
```

---

## �‍💻 Developer Setup

Want to modify WhisperEngine's source code or contribute to the project?

**[🔧 Complete Developer Setup Guide](docs/development/DEVELOPMENT_GUIDE.md)**

The development guide covers:
- Docker-based development environment setup
- Source code modification workflow  
- Testing and validation procedures
- Contribution guidelines and best practices