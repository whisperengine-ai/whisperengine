# Quick Start Guide

Get your private AI Discord bot running in ~15 minutes! This guide covers the fastest path to a working bot using either free local AI or paid cloud services.

## 🎯 What You'll Need

1. **Python 3.8+** installed
2. **A Discord bot token** (free from Discord)
3. **Choose ONE AI service:**
   - **Local LLM** (LM Studio/Ollama - free but needs 8GB+ RAM)
   - **OpenRouter API** (paid cloud service - works on any computer)

## 🤖 Step 1: Choose Your AI Service

| Service | Cost | Setup | Privacy | Performance | Best For |
|---------|------|-------|---------|-------------|----------|
| **LM Studio** | Free | Medium | 100% Private | Good | Privacy-focused users, permanent setup |
| **Ollama** | Free | Easy | 100% Private | Good | Command-line users, lightweight setup |
| **OpenRouter** | Pay-per-use | Very Easy | Shared with provider | Excellent | Quick setup, latest models, scaling |

### Option A: LM Studio (Recommended for Privacy)

**LM Studio** provides a user-friendly GUI for running local LLMs.

1. **Download LM Studio**
   - Visit [lmstudio.ai](https://lmstudio.ai/)
   - Download for your OS (Windows/Mac/Linux)
   - Install and launch the application

2. **Download a Model**
   - In LM Studio, click the "🔍 Search" tab
   - Search for and download one of these beginner-friendly models:
     - **"microsoft/Phi-3.5-mini-instruct"** (3.8B - fast and efficient)
     - **"meta-llama/Llama-3.2-3B-Instruct"** (3B - good balance)
     - **"meta-llama/Llama-3.1-8B-Instruct"** (8B - better quality, needs more RAM)
   - Click "Download" and wait for completion

3. **Start the Server**
   - Go to the "💬 Chat" tab
   - Select your downloaded model
   - Click "Start Server" 
   - **Important**: Note the server URL (usually `http://localhost:1234/v1`)
   - Test by visiting the URL in your browser - you should see an API page

### Option B: Ollama (Command Line)

**Ollama** is a command-line tool that's lightweight and efficient.

1. **Install Ollama**
   ```bash
   # macOS
   brew install ollama
   
   # Linux
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Windows - Download from https://ollama.ai/download
   ```

2. **Download and Run a Model**
   ```bash
   # Start Ollama service
   ollama serve
   
   # In a new terminal, pull a model
   ollama pull llama3.2:3b
   # or for something smaller:
   ollama pull phi3.5:latest
   ```

3. **Verify It's Running**
   ```bash
   # Test the API
   curl http://localhost:11434/v1/models -H "Content-Type: application/json"
   ```

### Option C: OpenRouter (Cloud API)

**OpenRouter** provides access to multiple AI models through a single API.

1. **Sign Up for OpenRouter**
   - Visit [openrouter.ai](https://openrouter.ai/)
   - Create an account and add credits to your account
   - Generate an API key from your dashboard

2. **Choose Your Model**
   - Browse available models at [openrouter.ai/models](https://openrouter.ai/models)
   - Popular options:
     - **"anthropic/claude-3.5-sonnet"** - Excellent for conversation
     - **"openai/gpt-4o-mini"** - Fast and cost-effective
     - **"meta-llama/llama-3.1-8b-instruct"** - Good balance of cost and quality

3. **No Local Setup Required**
   - Models run in the cloud
   - Just configure your API key in the bot

## 🔑 Step 2: Get Your Discord Bot Token

1. **Create Discord Application**
   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Click "New Application"
   - Name it (e.g., "My AI Bot")

2. **Create Bot**
   - Go to "Bot" section
   - Click "Add Bot"
   - Copy the token (keep this secret!)

3. **⚠️ CRITICAL: Enable Message Content Intent**
   - In the "Bot" section under "Privileged Gateway Intents"
   - **Enable "Message Content Intent"** ✅ (REQUIRED for bot to read messages)

4. **Invite Bot to Server**
   - Go to "OAuth2" → "URL Generator"
   - **Scopes**: Check "bot"
   - **Bot Permissions**: Check:
     - ✅ Send Messages
     - ✅ Read Message History  
     - ✅ Use Slash Commands
     - ✅ Add Reactions
     - ✅ Embed Links
     - ✅ Read Messages/View Channels
   - Copy the generated URL and visit it to invite your bot to your server

## 🚀 Step 3: Install & Run the Bot

1. **Clone and Install**
   ```bash
   git clone https://github.com/theRealMarkCastillo/custom_bot.git
   cd custom_bot
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   ```bash
   # For local LLM users (LM Studio/Ollama):
   cp .env.minimal .env
   
   # For OpenRouter users:
   cp .env.openrouter.example .env
   ```

3. **Edit Configuration**
   
   Open `.env` in any text editor and set:
   
   **For LM Studio:**
   ```env
   DISCORD_BOT_TOKEN=your_discord_bot_token_here
   LLM_CHAT_API_URL=http://localhost:1234/v1
   LLM_MODEL_NAME=local-model
   ```
   
   **For Ollama:**
   ```env
   DISCORD_BOT_TOKEN=your_discord_bot_token_here
   LLM_CHAT_API_URL=http://localhost:11434/v1
   LLM_MODEL_NAME=llama3.2:3b
   ```
   
   **For OpenRouter:**
   ```env
   DISCORD_BOT_TOKEN=your_discord_bot_token_here
   LLM_CHAT_API_URL=https://openrouter.ai/api/v1
   OPENROUTER_API_KEY=your_openrouter_api_key_here
   LLM_MODEL_NAME=anthropic/claude-3.5-sonnet
   ```

4. **Start the Bot**
   ```bash
   # Normal mode
   python basic_discord_bot.py
   
   # Debug mode (if you run into issues)
   python basic_discord_bot.py --debug
   ```

## ✅ Step 4: Test Your Bot

1. **Test LLM Connection**
   - In Discord, send: `!llm_status`
   - Should show connection info and model details

2. **Test Basic Chat**
   - Send a DM to your bot: "Hello! I'm testing you."
   - Or mention it in a channel: `@YourBot Hello!`

3. **Test Memory System**
   - After chatting, use: `!my_memory`
   - Should show facts the bot learned about you

## 🚨 Common Issues & Quick Fixes

### Bot Won't Respond to Messages
- **Missing Message Content Intent**: Go to Discord Developer Portal → Your App → Bot → Enable "Message Content Intent"
- **Missing Permissions**: Re-invite bot with proper permissions

### LLM Connection Issues
- **Local Services**: Make sure LM Studio or Ollama is running and model is loaded
- **OpenRouter**: Check API key is valid and you have credits
- **Test Connection**: Use `!llm_status` command to diagnose

### Bot Starts But Gives Errors
- **Check Logs**: Look at console output for error messages
- **Debug Mode**: Run with `python basic_discord_bot.py --debug`
- **Check Environment**: Verify `.env` file has correct values

## 🎉 You're Done!

Your bot now has:
- ✅ AI-powered conversations
- ✅ Persistent memory across chats
- ✅ Automatic fact learning
- ✅ Complete privacy (if using local LLM)

## 🔄 Next Steps

- **Import ChatGPT History**: Use `python import_chatgpt_history.py` to bring your existing conversations
- **Explore Commands**: Type `!commands` to see all available features
- **Advanced Setup**: Check [Installation Guide](INSTALLATION.md) for hybrid configurations and optimization

---

**Need help?** Check the [Installation Guide](INSTALLATION.md) for detailed troubleshooting.
