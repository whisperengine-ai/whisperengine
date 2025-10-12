# 🎭 WhisperEngine - Quick Start

**AI Character Platform** - Create, customize, and deploy AI characters with personality, memory, and intelligence.

## 🚀 **Get Started in 2 Minutes**

### **Ultra-Quick Setup**

**For macOS/Linux:**
```bash
git clone https://github.com/whisperengine-ai/whisperengine.git
cd whisperengine
./setup.sh
```

**For Windows:**
```cmd
git clone https://github.com/whisperengine-ai/whisperengine.git
cd whisperengine
setup.bat
```

**Alternative for Windows (Git Bash):**
```bash
git clone https://github.com/whisperengine-ai/whisperengine.git
cd whisperengine
./setup.sh
```

### **Manual Setup**
```bash
git clone https://github.com/whisperengine-ai/whisperengine.git
cd whisperengine
cp .env.quickstart.template .env
# Edit .env with your LLM API key - see Configuration Guide for help: docs/guides/edit-env-after-quickstart.md
docker-compose -f docker-compose.quickstart.yml up
```

### **Access Your Platform**
- **Web UI**: http://localhost:3001 (Character management)
- **Chat API**: http://localhost:9090/api/chat (Direct API access)

## 📖 **Full Documentation**

- **[Quick Start Guide](QUICKSTART.md)** - Complete setup instructions
- **[Character Creation](cdl-web-ui/README.md)** - How to create custom characters
- **[API Documentation](docs/api/)** - Integration guide
- **[Advanced Setup](docs/setup/)** - Multi-character, Discord, custom deployment

## 🎭 **What You Get**

### **Out of the Box**
- ✅ **Default AI Assistant** character ready to chat
- ✅ **Web-based character editor** for customization
- ✅ **Chat API** for integrations
- ✅ **Memory & intelligence** with conversation learning
- ✅ **Multi-platform support** (Discord optional)

### **Customize Everything**
- 🎨 **Character Personalities** - Create unique AI characters
- 🧠 **Memory Systems** - Characters remember conversations
- 💬 **Communication Styles** - Adapt to different interaction patterns
- 🔌 **LLM Integration** - Works with OpenAI, Claude, local models, etc.
- 📱 **Platform Integration** - Discord, web, API, custom apps

## 🤝 **Community & Support**

- **Issues**: [GitHub Issues](https://github.com/whisperengine-ai/whisperengine/issues)
- **Discussions**: [GitHub Discussions](https://github.com/whisperengine-ai/whisperengine/discussions)
- **Documentation**: [Wiki](https://github.com/whisperengine-ai/whisperengine/wiki)

---

**Ready to create your first AI character?** 🎭

👉 **[Start with the Quick Setup Guide](QUICKSTART.md)**
