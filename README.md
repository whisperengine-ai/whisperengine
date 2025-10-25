# 🎭 WhisperEngine

**Open Source AI Character Development Project**

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Alpha](https://img.shields.io/badge/Status-Alpha-orange.svg)](https://github.com/whisperengine-ai/whisperengine)

> 🧪 **Exploring AI character conversations** with persistent memory and emotional understanding! [Try it out](#-try-whisperengine) ↓

**Quick Navigation:** [🚀 Try It](#-try-whisperengine) | [⚙️ Configuration](#%EF%B8%8F-next-step-configuration) | [🎭 Create Characters](#-creating-your-character) | [📚 Documentation](#-documentation)

<img width="871" height="729" alt="image" src="https://github.com/user-attachments/assets/e4c8754f-dce1-422c-a8a9-52fab86adda8" />

<img width="960" height="550" alt="image" src="https://github.com/user-attachments/assets/f1f9256f-aace-4cf4-ae38-b1b43d2a7383" />

<img width="939" height="547" alt="image" src="https://github.com/user-attachments/assets/dafefd8b-73db-4150-938a-5042cb20cb7e" />

## 🎯 What is WhisperEngine?

**WhisperEngine is an open source project** exploring realistic AI character conversations through five key areas of AI conversation technology.

**Great for:**
- 🎮 **AI NPCs** with persistent memory and character development
- 📚 **Character AI** for creative writing and storytelling
- 🎭 **AI Roleplay** with emotionally intelligent characters
- 🔬 **AI Enthusiasts** exploring conversation patterns and personality modeling
- 🛠️ **Personal AI Projects** - build your own character AI system

> 🚀 **Want to start immediately?** [Skip to installation](#-try-whisperengine) | **Want to understand the technology?** Continue reading below ↓

## 🏗️ Five Key Areas in AI Character Conversation

WhisperEngine explores five areas that contribute to more realistic AI character interactions:

### 🎭 **Area 1: Emotion Recognition**
*Understanding how AI can detect emotional nuance, intensity, and flow*

- **🤖 RoBERTa Transformer Implementation** - Using j-hartmann/emotion-english-distilroberta-base
- **📊 Multi-Emotion Detection** - Recognizing simultaneous emotions in conversations  
- **🔍 Emotional Metadata Analysis** - Processing 12+ emotion analysis dimensions
- **⚡ Real-Time Processing** - Sub-second emotion analysis implementation

### 🧠 **Area 2: Memory & Context**
*AI that remembers past interactions and emotional context*

- **🎯 Vector Memory Implementation** - 384D embeddings for character context storage
- **💾 Persistent Conversations** - Cross-session memory retention
- **🔄 Context Retrieval** - Memory search with emotional patterns
- **📈 Character Learning** - Long-term character development patterns

### ❤️ **Area 3: Character Responses**
*AI that responds authentically while maintaining consistent personalities*

- **🎭 Character Definition Language (CDL)** - Structured personality modeling system
- **🌟 Adaptive Responses** - Real-time emotional adaptation techniques
- **🎯 Cultural Authenticity** - Character-appropriate response patterns
- **💭 Contextual Intelligence** - Response calibration based on emotional context

### 🎯 **Area 4: Personalization & Adaptation**
*AI characters that learn individual interaction preferences*

- **📚 Learning Patterns** - How characters adapt to individual interaction styles
- **🔄 Character Evolution** - AI personalities that develop over time
- **🎨 Communication Style Adaptation** - Personalized interaction approaches
- **💡 Predictive Context** - AI that anticipates conversation needs

### 🛡️ **Area 5: Responsible AI**
*Safety tools and ethical considerations for character AI deployment*

- **🎭 AI Ethics Implementation** - Context-sensitive safety tools
- **📊 Interaction Pattern Monitoring** - Usage pattern detection methods
- **🔐 Security Implementation** - Input validation and system protection techniques  
- **⚖️ Responsible Deployment Tools** - Frameworks for ethical AI character deployment

---

**🔬 Want to understand how it works?** Read our guide: **[How WhisperEngine's AI Characters Learn and Remember You](docs/guides/HOW_AI_CHARACTERS_LEARN.md)** - technical details about the five areas and implementation approaches.

## 🤖 What's Included

WhisperEngine includes a **basic AI assistant** that you can customize and extend:

### 🔧 **Default Assistant Features:**
- **Conversational AI** - Standard chat functionality with memory
- **Emotional Intelligence** - RoBERTa-powered emotion recognition
- **Persistent Memory** - Vector-based conversation history
- **Customizable Personality** - Modify traits through configuration
- **Safety Controls** - Built-in ethical interaction boundaries

### 🎨 **Your Character Creation Options:**
- **Modify the Default Assistant** - Adjust personality traits and communication style
- **Create Custom Characters** - Build your own using the Character Definition Language (CDL)
- **Explore Different Archetypes** - Professional, creative, analytical, or supportive roles
- **Test AI Conversation Features** - Experiment with the five key areas in a safe environment

> ⚠️ **Note**: WhisperEngine provides the framework and tools - you're responsible for creating and configuring any specific character personalities according to your needs and local regulations. [See complete AI disclaimers](docs/legal/AI_DISCLAIMERS.md).

## ✨ Project Features

### 🛠️ **Easy to Try**
- **Docker-Based Setup** - Containerized for easy testing
- **Web Interface** - Simple UI for exploring character AI
- **Cross-Platform** - Run on Windows, macOS, and Linux
- **Open Source** - Full access to code and implementation details

### 🔧 **Developer Friendly**
- **REST API** - Programmatic access for integration and testing
- **Discord Bot Support** - Optional real-world conversation testing
- **Multiple LLM Backends** - Test with different language models
- **Extensible Architecture** - Modify and extend for your needs

## 🚀 Try WhisperEngine

Get WhisperEngine running to explore AI character conversations:

### **What You'll Need**
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) for containerized deployment
- **LLM Access** (choose one):
  - LLM API key (OpenRouter, OpenAI, Anthropic, etc.) **OR**
  - Local LLM (Ollama, LM Studio, or similar - no API key needed)
- **No programming experience needed** - setup scripts handle the technical details

### **Quick Setup**

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
5.  Start all services automatically
6. 🌐 Open the web interface in your browser

## ⚙️ Next Step: Configuration

**Before creating characters, you'll need to configure your LLM access.**

WhisperEngine works with both API-based LLMs (OpenRouter, OpenAI, Anthropic) and local LLMs (Ollama, LM Studio). 

**📋 [Complete Configuration Guide](docs/guides/edit-env-after-quickstart.md)** - Step-by-step setup for all LLM providers, Discord integration, and system settings.

## 🎭 Creating Your Character

After configuration, try customizing the basic AI assistant or creating new characters:

1. **Open the Web Interface**: http://localhost:3001
2. **Start with the Default Assistant** or **Click "Create New Character"**
3. **🎭 Design Emotional Patterns**:
   - Set up different emotional response styles
   - Configure communication preferences
   - Define how characters recognize emotions
4. **🧠 Configure Memory Systems**:
   - Add background knowledge for testing
   - Define character values and traits
   - Set up different knowledge domains
5. **❤️ Test Response Generation**:
   - Explore character voice and conversation patterns
   - Try different support and interaction styles
6. **🎯 Explore Personalization**:
   - Configure character adaptation mechanisms
   - Set up learning patterns and evolution
7. **🛡️ Configure Safety Features**:
   - Set up ethical interaction boundaries
   - Test safety monitoring systems
   - Configure responsible AI deployment tools
8. **Deploy & Test** - Start exploring your character AI!

## 💬 Testing Your Characters

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

**📋 Additional Guides:**
- **[Troubleshooting Guide](docs/troubleshooting/README.md)** - Common issues and detailed solutions
- **[Cleanup Scripts](docs/deployment/CLEANUP_SCRIPTS.md)** - Fresh restart if needed

## 📚 Documentation

**Getting Started:**
- **[Quick Start Guide](docs/guides/QUICKSTART.md)** - Detailed setup instructions
- **[Configuration Guide](docs/guides/edit-env-after-quickstart.md)** - LLM providers and settings
- **[Troubleshooting](docs/troubleshooting/README.md)** - Common issues and solutions

**Advanced:**
- **[Character Creation](docs/characters/CHARACTER_AUTHORING_GUIDE.md)** | **[API Reference](docs/api/CHAT_API_REFERENCE.md)** | **[Multi-Character Setup](docs/setup/MULTI_CHARACTER_SETUP.md)**
- **[Development Guide](docs/development/DEVELOPMENT_GUIDE.md)** - For developers and contributors

## 🛟 Getting Help

**[Troubleshooting Guide](docs/troubleshooting/README.md)** | **[Cleanup Scripts](docs/deployment/CLEANUP_SCRIPTS.md)** | **[GitHub Issues](https://github.com/whisperengine-ai/whisperengine/issues)** | **[Discussions](https://github.com/whisperengine-ai/whisperengine/discussions)**

## 🔧 Advanced Setup

**[Production Deployment](docs/deployment/PRODUCTION_SETUP.md)** | **[Multi-Character Setup](docs/setup/MULTI_CHARACTER_SETUP.md)** | **[Local LLM Models](docs/setup/LOCAL_LLM_SETUP.md)**

## 🤝 Contributing

WhisperEngine is open source and welcomes contributions!

- **[Contributing Guide](CONTRIBUTING.md)** - How to contribute
- **[Development Setup](docs/development/DEVELOPMENT_SETUP.md)** - Local development environment
- **[Architecture Overview](docs/architecture/README.md)** - System design and components

## ⚠️ AI Disclaimers & Limitations

**Important:** WhisperEngine enables AI character creation. Key limitations:

- **🤖 AI Limitations**: Characters may hallucinate or provide inaccurate information. Not suitable for factual, medical, or legal advice.
- **👤 User Responsibility**: You are fully responsible for all AI-generated content and ensuring compliance with applicable laws.
- **🛡️ No Warranty**: Software provided "as is" without warranty. Educational/experimental use only.

**📋 [Complete AI Safety & Legal Disclaimers](docs/legal/AI_DISCLAIMERS.md)** - Comprehensive limitations, responsibilities, and legal considerations.

> By using WhisperEngine, you acknowledge these limitations and accept full responsibility for your use of the system.

## 📄 License & Disclaimer

WhisperEngine is licensed under the **GNU General Public License v3.0**. See [LICENSE](LICENSE) for details.

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

**Additional AI System Disclaimer:** WhisperEngine enables AI character creation and conversation. Users assume all responsibility for AI-generated content, character configurations, and compliance with applicable laws and ethical guidelines. The software is provided for educational and experimental purposes only.
