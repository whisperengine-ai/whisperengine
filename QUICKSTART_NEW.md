# 🚀 WhisperEngine Quick Start Guide

**Get your AI character platform running in under 5 minutes!**

## 📋 Prerequisites

Before starting, ensure you have:

### **Required Software**
- **[Docker Desktop](https://www.docker.com/products/docker-desktop/)** - Download and install, then start it
- **[Git](https://git-scm.com/downloads)** - For downloading WhisperEngine

### **Required API Access**
You'll need an API key from one of these LLM providers:

| Provider | Cost | Setup Time | Best For |
|----------|------|------------|----------|
| **[OpenRouter](https://openrouter.ai)** ⭐ | Pay-per-use | 2 minutes | Beginners, trying different models |
| **[OpenAI](https://platform.openai.com)** | Monthly credits | 5 minutes | Production use, reliability |
| **Local Models** | Free | 30+ minutes | Privacy, offline use |

> 💡 **Recommendation**: Start with OpenRouter - it's fastest to set up and gives access to multiple AI models including Claude, GPT-4, and open-source alternatives.

## ⚡ Installation Methods

Choose your preferred installation method:

### **Method 1: Instant Containerized Setup** ⭐ (Recommended)

**No source code download required! Uses pre-built Docker containers.**

✨ **Features:**
- 🚀 **Pre-downloaded Models**: Containers include ~400MB of AI models for instant startup
  - FastEmbed: sentence-transformers/all-MiniLM-L6-v2 (embeddings)
  - RoBERTa: cardiffnlp emotion analysis (11 emotions)
- 🐳 **Fully Containerized**: No dependencies, just Docker
- ⚡ **Zero Configuration**: Works out of the box

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

That's it! The script downloads only the necessary configuration files and runs pre-built containers.

### **Manual Containerized Setup**

If you prefer manual control:

```bash
# 1. Create project directory
mkdir whisperengine && cd whisperengine

# 2. Download Docker Compose configuration
curl -sSL https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/docker-compose.containerized.yml -o docker-compose.yml

# 3. Download configuration template
curl -sSL https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/.env.containerized.template -o .env

# 4. Edit configuration (add your API key)
nano .env  # or your preferred editor

# 5. Start WhisperEngine
docker-compose up -d

# 6. Open web interface
open http://localhost:3001  # macOS
# OR visit http://localhost:3001 in your browser
```

## ⚙️ Configuration Setup

When the setup script opens your `.env` file (or if doing manual setup), you need to configure:

### **Required Settings**

```bash
# Your LLM API Key (REQUIRED)
LLM_CHAT_API_KEY=your_api_key_here

# Model selection (optional, has good defaults)
LLM_CHAT_MODEL=anthropic/claude-3-haiku
```

### **Getting Your API Key**

#### **OpenRouter** (Recommended for beginners)
1. Go to [openrouter.ai](https://openrouter.ai)
2. Sign up with Google/GitHub
3. Click "Keys" in sidebar → "Create Key"
4. Copy the key and paste it in your `.env` file

#### **OpenAI**
1. Go to [platform.openai.com](https://platform.openai.com)
2. Create account and add billing info
3. Go to "API Keys" → "Create new secret key"
4. Copy the key and set:
   ```bash
   LLM_CLIENT_TYPE=openai
   LLM_CHAT_API_KEY=sk-your_openai_key
   LLM_CHAT_MODEL=gpt-4o-mini
   ```

### **Optional Settings**

```bash
# Discord Integration (optional)
DISCORD_BOT_TOKEN=your_discord_bot_token
ENABLE_DISCORD=true

# Character Settings
CHARACTER_NAME=assistant  # Default character name

# Advanced LLM Settings
LLM_CLIENT_TYPE=openrouter  # or: openai, local
LLM_CHAT_API_URL=https://openrouter.ai/api/v1
```

## 🌐 Accessing WhisperEngine

After installation, you can access:

### **Web Interface** (Primary)
- **URL**: http://localhost:3001
- **Purpose**: Create characters, manage settings, chat interface
- **Features**: Full character creation and management

### **Chat API** (For Developers)
- **URL**: http://localhost:9090/api/chat
- **Purpose**: Direct API access for integrations
- **Documentation**: See [API Guide](docs/api/README.md)

### **Health Dashboard**
- **URL**: http://localhost:9090/health
- **Purpose**: System status and diagnostics

## 🎭 Creating Your First Character

### **Via Web Interface** (Recommended)

1. **Open**: http://localhost:3001
2. **Click**: "Create New Character"
3. **Basic Info**:
   - **Name**: "Alex"
   - **Description**: "A helpful coding assistant"
   - **Occupation**: "Software Developer"

4. **Personality**:
   - **Traits**: Helpful, Patient, Technical
   - **Communication Style**: Clear and concise
   - **Values**: Learning, Problem-solving

5. **Knowledge**:
   - **Expertise**: Programming languages, debugging
   - **Background**: 5 years of software development
   - **Interests**: Open source, clean code

6. **Save & Deploy**: Character is ready to use!

### **Via API** (Advanced)

```bash
curl -X POST http://localhost:9090/api/characters \\
  -H "Content-Type: application/json" \\
  -d '{
    "name": "Alex",
    "description": "A helpful coding assistant",
    "personality": {
      "traits": ["helpful", "patient", "technical"],
      "communication_style": "clear_and_concise"
    },
    "knowledge": {
      "expertise": ["programming", "debugging"],
      "background": "5 years of software development"
    }
  }'
```

## 💬 Testing Your Character

### **Web Chat**
1. Go to http://localhost:3001
2. Select your character
3. Start chatting!

### **API Testing**
```bash
curl -X POST http://localhost:9090/api/chat \\
  -H "Content-Type: application/json" \\
  -d '{
    "user_id": "test_user",
    "message": "Hi Alex! Can you help me debug a Python function?",
    "context": {"platform": "api"}
  }'
```

### **Discord Testing** (If Enabled)
1. Invite your bot to a Discord server
2. Use `/chat` commands or mention the bot
3. Characters respond with persistent memory

## 🔧 Management Commands

### **View Status**
```bash
docker-compose -f docker-compose.quickstart.yml ps
```

### **View Logs**
```bash
# All services
docker-compose -f docker-compose.quickstart.yml logs

# Specific service
docker-compose -f docker-compose.quickstart.yml logs whisperengine-assistant

# Follow logs in real-time
docker-compose -f docker-compose.quickstart.yml logs -f
```

### **Stop WhisperEngine**
```bash
docker-compose -f docker-compose.quickstart.yml down
```

### **Restart WhisperEngine**
```bash
docker-compose -f docker-compose.quickstart.yml restart
```

### **Update WhisperEngine**
```bash
git pull
docker-compose -f docker-compose.quickstart.yml pull
docker-compose -f docker-compose.quickstart.yml up -d
```

## 🛠️ Customization Options

### **Model Selection**

Edit your `.env` file to try different AI models:

```bash
# Fast and affordable (recommended for testing)
LLM_CHAT_MODEL=anthropic/claude-3-haiku

# More capable (higher cost)
LLM_CHAT_MODEL=anthropic/claude-3.5-sonnet
LLM_CHAT_MODEL=openai/gpt-4o

# Open source alternatives
LLM_CHAT_MODEL=meta-llama/llama-3.1-8b-instruct
LLM_CHAT_MODEL=mistralai/mistral-7b-instruct
```

### **Character Personalities**

Customize character behavior by editing:
- **Personality Traits**: Helpful, Creative, Analytical, Humorous
- **Communication Style**: Formal, Casual, Technical, Storytelling
- **Values**: Honesty, Creativity, Efficiency, Empathy
- **Knowledge Areas**: Add specific expertise and background

### **Discord Integration**

To enable Discord functionality:

1. **Create Discord Bot**:
   - Go to https://discord.com/developers/applications
   - Create "New Application"
   - Go to "Bot" section → "Add Bot"
   - Copy the token

2. **Configure WhisperEngine**:
   ```bash
   # Add to .env file
   DISCORD_BOT_TOKEN=your_bot_token_here
   ENABLE_DISCORD=true
   ```

3. **Restart**:
   ```bash
   docker-compose -f docker-compose.quickstart.yml restart
   ```

4. **Invite Bot**:
   - In Discord Developer Portal, go to "OAuth2" → "URL Generator"
   - Select "bot" scope and "Send Messages" permission
   - Use generated URL to invite bot to your server

## 🚨 Troubleshooting

### **Common Issues**

#### **"Docker is not running"**
- **Solution**: Start Docker Desktop and wait for it to fully load
- **Check**: Docker icon in system tray should show "Docker Desktop is running"

#### **"Port already in use"**
- **Problem**: Another service is using ports 3001 or 9090
- **Solution**: Stop conflicting services or change ports in `docker-compose.quickstart.yml`

#### **"API key not working"**
- **Check**: Ensure your API key is correctly copied (no extra spaces)
- **Verify**: Test your API key at the provider's website
- **OpenRouter**: Visit [openrouter.ai](https://openrouter.ai) → Credits to verify

#### **"Character not responding"**
- **Check**: View logs for errors: `docker-compose -f docker-compose.quickstart.yml logs`
- **Verify**: API key is set and valid
- **Test**: Try the health endpoint: http://localhost:9090/health

### **Getting Help**

1. **Check Logs**: Always check logs first for error messages
2. **Health Status**: Visit http://localhost:9090/health for system status
3. **Documentation**: See [Troubleshooting Guide](docs/troubleshooting/README.md)
4. **GitHub Issues**: Report bugs at [GitHub Issues](https://github.com/whisperengine-ai/whisperengine/issues)

## 📚 Next Steps

### **Learn More**
- **[Character Creation Guide](docs/characters/CHARACTER_AUTHORING_GUIDE.md)** - Advanced character building
- **[API Documentation](docs/api/README.md)** - Integrate with your applications
- **[Multi-Character Setup](docs/setup/MULTI_CHARACTER_SETUP.md)** - Run multiple characters

### **Advanced Features**
- **Persistent Memory**: Characters remember conversations
- **Adaptive Learning**: Characters improve over time
- **Emotional Intelligence**: Sophisticated emotion analysis
- **Vector Memory**: Semantic understanding and recall

### **Production Use**
- **[Production Deployment](docs/deployment/PRODUCTION_SETUP.md)** - Secure, scalable setup
- **[Monitoring Setup](docs/monitoring/README.md)** - Performance monitoring
- **[Backup Strategies](docs/backup/README.md)** - Data protection

## 🎉 Success!

You now have WhisperEngine running with:
- ✅ AI character platform accessible at http://localhost:3001
- ✅ REST API available at http://localhost:9090/api/chat
- ✅ Persistent character memory and personality
- ✅ Web-based character creation and management
- ✅ Optional Discord integration

**Start creating your AI characters and explore the possibilities!** 🚀