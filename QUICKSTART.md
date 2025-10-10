# 🚀 WhisperEngine Quick Start Guide

Get WhisperEngine running in **5 minutes** with a single command!

## 📋 **Prerequisites**

- **Docker Desktop** installed ([download here](https://www.docker.com/products/docker-desktop/))
- **Git** installed ([download here](https://git-scm.com/downloads))
- An **LLM API key** (OpenRouter, OpenAI, etc.) OR local LM Studio/Ollama

## 🎯 **Quick Start (3 Steps)**

### 1. Download WhisperEngine
```bash
git clone https://github.com/whisperengine-ai/whisperengine.git
cd whisperengine
```

### 2. Run Setup Script

**For macOS/Linux:**
```bash
./setup.sh
```

**For Windows:**
```cmd
setup.bat
```

**Alternative for Windows (using Git Bash):**
```bash
./setup.sh
```

The setup script will:
- Check if Docker is running
- Create your configuration file (`.env`)
- Open the file for editing
- Start WhisperEngine services
- Open the web interface in your browser

### 3. Configure Your Settings (automated by setup script)
When the setup script opens your `.env` file:
- Set your `LLM_CHAT_API_KEY` (required)
- Optionally set `DISCORD_BOT_TOKEN` if you want Discord integration
- Choose your LLM model (default: Claude 3 Haiku via OpenRouter)

**That's it!** The setup script handles everything else.

## 🌐 **Access Your WhisperEngine**

Once running, you can access:

### **Character Management Web UI**
- **URL**: http://localhost:3001
- **Purpose**: Create, edit, and manage AI characters
- **Features**: 
  - Create your first character
  - Customize personality, background, abilities
  - Configure LLM settings
  - Enable/disable Discord integration

### **Chat API Endpoint**  
- **URL**: http://localhost:9090/api/chat
- **Purpose**: Direct API access for integrations
- **Example**:
```bash
curl -X POST http://localhost:9090/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "your_user_id",
    "message": "Hello! Tell me about yourself.",
    "context": {"channel_type": "api", "platform": "web"}
  }'
```

## 🎭 **Your Default Character**

WhisperEngine starts with a default "AI Assistant" character that you can:
- **Customize** via the web UI at http://localhost:3001
- **Replace** by creating a new character
- **Use as-is** for general assistance tasks

## ⚙️ **LLM Provider Options**

### **Option 1: OpenRouter (Recommended for beginners)**
```env
LLM_CLIENT_TYPE=openrouter
LLM_CHAT_API_URL=https://openrouter.ai/api/v1
LLM_CHAT_MODEL=anthropic/claude-3-haiku
LLM_CHAT_API_KEY=your_openrouter_key
```
- Get API key: https://openrouter.ai/
- Access to multiple models (Claude, GPT, Llama, etc.)
- Pay-per-use pricing

### **Option 2: OpenAI**
```env
LLM_CLIENT_TYPE=openai
LLM_CHAT_API_URL=https://api.openai.com/v1
LLM_CHAT_MODEL=gpt-3.5-turbo
LLM_CHAT_API_KEY=your_openai_key
```

### **Option 3: Local LM Studio**
```env
LLM_CLIENT_TYPE=lmstudio
LLM_CHAT_API_URL=http://host.docker.internal:1234/v1
LLM_CHAT_MODEL=local-model
LLM_CHAT_API_KEY=
```
- Download LM Studio: https://lmstudio.ai/
- Run any local model
- No API costs

### **Option 4: Local Ollama**
```env
LLM_CLIENT_TYPE=ollama
LLM_CHAT_API_URL=http://host.docker.internal:11434
LLM_CHAT_MODEL=llama2
LLM_CHAT_API_KEY=
```

## 📱 **Discord Integration (Optional)**

To enable Discord bot functionality:

1. **Create Discord Bot**:
   - Go to https://discord.com/developers/applications
   - Create new application → Bot
   - Copy the bot token

2. **Configure WhisperEngine**:
   ```env
   DISCORD_BOT_TOKEN=your_discord_bot_token
   ENABLE_DISCORD=true
   ```

3. **Invite Bot to Server**:
   - Use Discord Developer Portal to generate invite link
   - Give bot permissions: Send Messages, Read Message History

## 🛠️ **Management Commands**

```bash
# Start WhisperEngine
docker-compose -f docker-compose.quickstart.yml up

# Start in background
docker-compose -f docker-compose.quickstart.yml up -d

# Stop WhisperEngine
docker-compose -f docker-compose.quickstart.yml down

# View logs
docker-compose -f docker-compose.quickstart.yml logs -f

# Restart after config changes
docker-compose -f docker-compose.quickstart.yml restart

# Remove all data (fresh start)
docker-compose -f docker-compose.quickstart.yml down -v
```

## 🆘 **Troubleshooting**

### **Common Issues**

**"Port already in use"**
- Change ports in docker-compose.quickstart.yml
- Default ports: 3001 (web UI), 9090 (API)

**"LLM API errors"**
- Check your API key in `.env`
- Verify model name spelling
- Test API key directly with provider

**"Character not responding"**
- Check logs: `docker-compose -f docker-compose.quickstart.yml logs whisperengine-assistant`
- Verify LLM configuration in web UI
- Check API key validity

**"Web UI won't load"**
- Wait 2-3 minutes for full startup
- Check if container is running: `docker ps`
- View web UI logs: `docker-compose -f docker-compose.quickstart.yml logs cdl-web-ui`

### **Getting Help**

- **Check logs**: `docker-compose -f docker-compose.quickstart.yml logs`
- **System health**: Visit http://localhost:9090/health
- **Community**: [GitHub Issues](https://github.com/whisperengine-ai/whisperengine/issues)

## 🎉 **Next Steps**

Once your WhisperEngine is running:

1. **Visit the Web UI** (http://localhost:3001) to customize your character
2. **Test the Chat API** with some conversations
3. **Explore character personalities** by creating multiple characters
4. **Set up Discord integration** if desired
5. **Customize the system** through the web interface

## 🔧 **Advanced Configuration**

For advanced users who want to customize further:
- **Multiple Characters**: Create multiple characters via web UI
- **Custom Memory Settings**: Modify vector database settings
- **Performance Tuning**: Adjust container resources
- **Custom Models**: Use fine-tuned or specialized models

---

**That's it!** You now have a fully functional WhisperEngine AI character platform running locally. Enjoy building and customizing your AI characters! 🎭