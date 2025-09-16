# WhisperEngine AI - Quick Start Guide

## 🚀 **60-Second Setup**

### **For End Users (Desktop App)**
```bash
# 1. Download models (3GB - includes small LLM for offline use)
python download_models.py

# 2. Run desktop app
python universal_native_app.py

# 3. Open browser: http://localhost:8501
# 4. Start chatting with AI immediately!
```

### **For Developers (Build from Source)**
```bash
# 1. Setup environment
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Download AI models
python download_models.py

# 3. Test the app
python universal_native_app.py
```

### **For Discord Bot**
```bash
# 1. Add Discord token to .env
DISCORD_BOT_TOKEN=your_token_here

# 2. Run bot
python run.py
```

---

## 📦 **What's Included**

**Bundled AI Models (3GB total):**
- **DialoGPT-medium** (345MB) - Conversational AI for offline chat
- **all-mpnet-base-v2** (500MB) - Advanced memory embeddings  
- **Emotion Analysis** (600MB) - Sentiment and emotion detection
- **Complete offline functionality** - No internet required after setup

**Deployment Modes:**
- 🖥️ **Desktop App** - ChatGPT-like web interface
- 🤖 **Discord Bot** - Full bot with advanced memory
- 📱 **Native App** - Cross-platform executable

---

## ⚡ **Performance Options**

### **Quick Test (Bundled Models)**
- ✅ **Setup Time**: 5 minutes
- ✅ **Storage**: 3GB
- ✅ **Privacy**: 100% local
- ⚠️ **Quality**: Basic conversations

### **Production Quality (External AI)**
- 🔗 **LM Studio**: Download + setup local Llama model
- ☁️ **OpenAI**: Add API key for GPT-4o
- 🌐 **OpenRouter**: Access multiple AI models

---

## 🔧 **Configuration**

Edit `.env.desktop` to customize:

```bash
# Use bundled offline AI (default)
LLM_CHAT_API_URL=local://models
LOCAL_LLM_MODEL=microsoft_DialoGPT-medium

# OR upgrade to LM Studio
LLM_CHAT_API_URL=http://localhost:1234/v1
LLM_MODEL_NAME=llama3.1:8b

# OR use OpenAI API
LLM_CHAT_API_URL=https://api.openai.com/v1
OPENAI_API_KEY=sk-your-key-here
```

---

## 🏗️ **Building Executables**

```bash
# Download models + build in one step
python build_with_models.py

# Or manual build
python download_models.py
pyinstaller whisperengine.spec

# Cross-platform builds
python build_cross_platform.py
```

---

## 📚 **Full Documentation**

- **Complete Guide**: [`BUILD_AND_USER_GUIDE.md`](BUILD_AND_USER_GUIDE.md)
- **Architecture**: [`docs/`](docs/) folder
- **Discord Setup**: [`DISCORD_SETUP.md`](DISCORD_SETUP.md)
- **Local vs Remote AI**: [`docs/deployment/LOCAL_VS_REMOTE_MODELS_GUIDE.md`](docs/deployment/LOCAL_VS_REMOTE_MODELS_GUIDE.md)

---

## 🆘 **Quick Troubleshooting**

| Issue | Solution |
|-------|----------|
| "Models not found" | Run `python download_models.py` |
| Slow responses | Upgrade to LM Studio or OpenAI API |
| High memory usage | Use `microsoft_DialoGPT-small` instead |
| Build fails | Check Python 3.9+, 16GB+ RAM |

**Need Help?** Check [`BUILD_AND_USER_GUIDE.md`](BUILD_AND_USER_GUIDE.md) for detailed instructions.

---

**🎯 TL;DR**: Run `python download_models.py && python universal_native_app.py` for instant AI chat with offline models!