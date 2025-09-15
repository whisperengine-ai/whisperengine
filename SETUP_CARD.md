# 🚀 WhisperEngine - Setup Card

## **60-Second Setup**

### **Desktop App (Recommended)**
```bash
# 1. One-line setup
./setup.sh                          # macOS/Linux
setup.bat                           # Windows

# 2. Start app  
source .venv/bin/activate            # macOS/Linux
.venv\Scripts\activate.bat           # Windows
python universal_native_app.py

# 3. Open browser: http://localhost:8501
```

### **Manual Setup**
```bash
# 1. Environment
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Download AI models (3GB)
python download_models.py

# 3. Run
python universal_native_app.py
```

---

## **What You Get**

✅ **Complete AI Chat System** - ChatGPT-like interface  
✅ **Offline AI Models** - DialoGPT + embeddings + emotion analysis  
✅ **Privacy-First** - Everything runs locally  
✅ **Upgradeable** - Connect to OpenAI/LM Studio later  

---

## **Quick Configuration**

Edit `.env.desktop` to customize:

```bash
# Default: Bundled offline AI
LLM_CHAT_API_URL=local://models

# Upgrade: LM Studio (download from lmstudio.ai)
LLM_CHAT_API_URL=http://localhost:1234/v1

# Upgrade: OpenAI API
LLM_CHAT_API_URL=https://api.openai.com/v1
OPENAI_API_KEY=sk-your-key-here
```

---

## **Build Executable**

```bash
# Download models + build
python build_with_models.py

# Find executable in dist/ folder
# - Contains all AI models (~3GB)
# - Runs without installation
# - Works offline
```

---

## **Quick Test**

After setup, test with:
```
User: "Hello! Can you introduce yourself?"
AI: "Hello! I'm WhisperEngine, an AI assistant..."
```

---

## **Troubleshooting**

| Problem | Solution |
|---------|----------|
| Models not found | `python download_models.py` |
| Slow responses | Use LM Studio or OpenAI API |
| High memory | Edit LOCAL_LLM_MODEL to "small" |
| Build fails | Python 3.9+, 16GB RAM required |

---

## **Resources**

- **Full Guide**: `BUILD_AND_USER_GUIDE.md`
- **Quick Start**: `QUICK_START.md`  
- **Deployment**: `DEPLOYMENT_GUIDE.md`
- **Configuration**: `docs/` folder

**Support**: GitHub Issues or Documentation

---

**🎯 TL;DR**: `./setup.sh && python universal_native_app.py` → Instant AI chat!