# WhisperEngine Build & User Guide

## 🚀 Quick Start for End Users

### **Option 1: Ready-to-Run Desktop App (Recommended)**

If you have a pre-built WhisperEngine executable:

```bash
# 1. Download and extract WhisperEngine
# 2. Run the desktop app
./WhisperEngine  # macOS/Linux
# or
WhisperEngine.exe  # Windows

# 3. Open your browser to http://localhost:8501
# 4. Start chatting immediately with the bundled AI!
```

### **Option 2: Run from Source**

```bash
# 1. Clone the repository
git clone https://github.com/whisperengine-ai/whisperengine.git
cd whisperengine

# 2. Set up virtual environment
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate     # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Download AI models (3GB total)
python download_models.py

# 5. Run the desktop app
python universal_native_app.py
```

---

## 🔧 Configuration Guide

### **Basic Configuration**

WhisperEngine works out-of-the-box with bundled AI models, but you can customize it:

#### **1. Desktop Mode (.env.desktop)**
The app automatically uses local AI models for privacy and offline use:

```bash
# Default configuration - uses bundled models
USE_LOCAL_MODELS=true
LOCAL_LLM_MODEL=microsoft_DialoGPT-medium
LLM_CHAT_API_URL=local://models
```

#### **2. Upgrade to Better AI Models**

For better AI quality, connect to external services:

**Option A: LM Studio (Local, Private)**
```bash
# 1. Download LM Studio from https://lmstudio.ai
# 2. Download a model (e.g., Llama 3.1 8B)
# 3. Start LM Studio server
# 4. Edit .env.desktop:
LLM_CHAT_API_URL=http://localhost:1234/v1
LLM_MODEL_NAME=llama3.1:8b
```

**Option B: OpenAI API (Cloud, High Quality)**
```bash
# 1. Get API key from https://openai.com
# 2. Edit .env.desktop:
LLM_CHAT_API_URL=https://api.openai.com/v1
OPENAI_API_KEY=sk-your-key-here
LLM_MODEL_NAME=gpt-4o-mini
```

**Option C: OpenRouter (Multiple Models)**
```bash
# 1. Get API key from https://openrouter.ai
# 2. Edit .env.desktop:
LLM_CHAT_API_URL=https://openrouter.ai/api/v1
OPENROUTER_API_KEY=sk-or-your-key-here
LLM_MODEL_NAME=anthropic/claude-3.5-sonnet
```

### **Advanced Configuration**

#### **Memory & Storage Settings**
```bash
# Local file storage (default for desktop)
DATABASE_URL=sqlite:///./whisperengine.db

# Or use PostgreSQL for production
DATABASE_URL=postgresql://user:pass@localhost/whisperengine
```

#### **UI Customization**
```bash
# Change web interface port
WEBUI_PORT=8501

# Enable system tray (macOS/Windows)
ENABLE_SYSTEM_TRAY=true
```

#### **Performance Tuning**
```bash
# AI response limits
LLM_MAX_TOKENS_CHAT=2048
LLM_MAX_TOKENS_COMPLETION=1024

# Memory cache settings
MAX_MEMORY_ENTRIES=1000
CONVERSATION_CACHE_SIZE=100
```

---

## 🛠️ Developer Build Guide

### **Prerequisites**

- Python 3.13+ 
- Git
- 16GB+ RAM (for model downloads)
- 10GB+ free disk space

### **Development Setup**

```bash
# 1. Clone and setup environment
git clone https://github.com/whisperengine-ai/whisperengine.git
cd whisperengine

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Download models for bundling
python download_models.py

# 5. Test the app
python universal_native_app.py
```

### **Building Executables**

#### **Method 1: Automated Build with Models**
```bash
# Downloads models and builds in one step
python build_with_models.py
```

#### **Method 2: Manual Build Process**
```bash
# 1. Download models first
python download_models.py

# 2. Build platform-specific executable
pyinstaller whisperengine-macos.spec     # macOS
pyinstaller whisperengine-linux.spec     # Linux  
pyinstaller whisperengine-windows.spec   # Windows

# 3. Find executable in dist/ folder
```

#### **Method 3: Cross-Platform Build**
```bash
# Build for all platforms (requires Docker)
python build_cross_platform.py
```

### **Build Configuration**

The build system automatically:

- ✅ Downloads 3GB of AI models (embeddings + LLM + emotion analysis)
- ✅ Bundles models into the executable
- ✅ Sets offline mode (`HF_DATASETS_OFFLINE=1`)
- ✅ Includes all required Python dependencies
- ✅ Creates platform-specific executables

### **Build Artifacts**

After building, you'll find:

```
dist/
├── WhisperEngine              # macOS app
├── WhisperEngine.exe          # Windows executable  
└── WhisperEngine-linux        # Linux binary

# Each contains:
# - Complete AI models (~3GB)
# - All Python dependencies
# - Web UI assets
# - Configuration files
```

---

## 📱 Usage Modes

### **1. Desktop App Mode**
```bash
python desktop_app.py
# OR
./WhisperEngine  # Built executable
```
- Web interface at `http://localhost:8501`
- Complete AI conversation system
- Local file storage
- System tray integration

### **2. Discord Bot Mode**
```bash
python run.py
```
- Full Discord bot functionality
- Advanced memory and personality
- Multi-user support
- Database persistence

### **3. Native App Mode**
```bash
python universal_native_app.py
```
- Cross-platform native interface
- Minimal resource usage
- Embedded AI models

---

## 🔍 Troubleshooting

### **Common Issues**

#### **"Models not found" Error**
```bash
# Solution: Download models
python download_models.py
```

#### **"transformers not available" Error**
```bash
# Solution: Install AI dependencies
pip install transformers torch sentence-transformers
```

#### **High Memory Usage**
```bash
# Solution: Use smaller model
# Edit .env.desktop:
LOCAL_LLM_MODEL=microsoft_DialoGPT-small
```

#### **Slow AI Responses**
```bash
# Solution: Upgrade to external AI service
# See "Upgrade to Better AI Models" section above
```

### **Performance Expectations**

| Model Type | Size | Response Time | Quality |
|------------|------|---------------|---------|
| **Bundled DialoGPT** | 350MB | 3-10s | Basic |
| **LM Studio Llama 3.1** | 4GB | 1-5s | Good |
| **OpenAI GPT-4o** | Cloud | 1-3s | Excellent |

### **System Requirements**

| Mode | RAM | Storage | Notes |
|------|-----|---------|-------|
| **Bundled Models** | 4GB+ | 5GB | Basic AI capability |
| **LM Studio** | 16GB+ | 10GB+ | Good local AI |
| **Cloud API** | 2GB+ | 1GB | Best AI quality |

---

## 🚀 Quick Test

After installation, test your setup:

```bash
# 1. Start the app
python desktop_app.py

# 2. Open browser to http://localhost:8501

# 3. Type a message:
"Hello! Can you introduce yourself?"

# 4. Expected response:
"Hello! I'm WhisperEngine, an AI assistant..."
```

If you see this response, everything is working correctly!

---

## 📚 Additional Resources

- **Documentation**: `docs/` folder
- **Configuration Examples**: `.env.example`
- **Build Scripts**: `build_*.py`
- **Model Management**: `download_models.py`
- **Testing**: `test_*.py` files

For support, check the GitHub issues or documentation in the `docs/` folder.