# 🏠 Local AI Setup for WhisperEngine

## Overview
WhisperEngine supports two primary local AI backends for maximum privacy and offline operation. Both options provide full AI capabilities without sending your data to external services.

## 🎯 Recommended Local AI Options

### 1. 🖥️ **LM Studio** (Recommended for Beginners)
**User-friendly GUI for local AI models**

#### **Installation**
1. Download LM Studio from [lmstudio.ai](https://lmstudio.ai/)
2. Install and launch the application
3. Download a recommended model (see model recommendations below)
4. Start the local server in LM Studio

#### **Configuration**
```bash
# In your .env file
LLM_CHAT_API_URL=http://localhost:1234/v1
LLM_MODEL_NAME=auto  # LM Studio auto-detects loaded model
```

#### **Benefits**
- ✅ User-friendly graphical interface
- ✅ Easy model management and switching
- ✅ Built-in performance monitoring
- ✅ One-click model downloads
- ✅ Automatic server management

### 2. 🦙 **Ollama** (Recommended for Advanced Users)
**Command-line tool for production local AI**

#### **Installation**
```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Windows
# Download from https://ollama.ai/download
```

#### **Setup**
```bash
# Download and run a model
ollama pull llama3.2:3b
ollama run llama3.2:3b

# Or start as a service
ollama serve
```

#### **Configuration**
```bash
# In your .env file
LLM_CHAT_API_URL=http://localhost:11434/v1
LLM_MODEL_NAME=llama3.2:3b
```

#### **Benefits**
- ✅ Production-ready and stable
- ✅ Command-line automation friendly
- ✅ Excellent performance optimization
- ✅ Large model library
- ✅ Multi-platform support

## 🤖 Recommended Models for WhisperEngine

### **For Conversation & Personalities**
| Model | Size | RAM Required | Best For |
|-------|------|--------------|----------|
| **Llama 3.2 3B** | ~2GB | 8GB | General conversation, fast responses |
| **Phi 3.5 Mini** | ~2.3GB | 8GB | Logical reasoning, assistant tasks |
| **Qwen 2.5 7B** | ~4GB | 16GB | Advanced reasoning, multilingual |
| **Llama 3.1 8B** | ~5GB | 16GB | High-quality conversation, creativity |

### **For Demo/Testing**
- **Llama 3.2 1B**: Ultra-fast, minimal RAM (~1GB)
- **Phi 3.5 Mini**: Good balance of size and capability

### **For Production**
- **Llama 3.1 8B**: Best quality for most use cases
- **Qwen 2.5 7B**: Excellent for multilingual users

## ⚙️ WhisperEngine Configuration

### **Automatic Detection**
WhisperEngine automatically detects running local AI servers:

```python
# WhisperEngine will automatically find:
# 1. LM Studio on localhost:1234
# 2. Ollama on localhost:11434
# 3. Other OpenAI-compatible local servers
```

### **Manual Configuration**
For specific setups, configure your `.env` file:

```bash
# === Local AI Configuration ===
DEPLOYMENT_MODE=local
PRIVACY_MODE=maximum

# LM Studio
LLM_CHAT_API_URL=http://localhost:1234/v1
LLM_MODEL_NAME=auto

# OR Ollama
LLM_CHAT_API_URL=http://localhost:11434/v1
LLM_MODEL_NAME=llama3.2:3b

# Performance Tuning
LLM_REQUEST_TIMEOUT=90  # Local models can be slower
LLM_MAX_TOKENS=2048     # Adjust based on your model
```

## 🚀 Performance Optimization

### **Hardware Recommendations**
- **RAM**: 16GB recommended (8GB minimum)
- **CPU**: Modern multi-core processor (2020+)
- **GPU**: Optional but significantly improves performance
- **Storage**: SSD recommended for model loading

### **Performance Tips**
1. **Close other applications** when running local AI
2. **Use GPU acceleration** if available (CUDA/Metal/OpenCL)
3. **Choose appropriate model size** for your hardware
4. **Monitor RAM usage** and adjust model parameters
5. **Use SSD storage** for faster model loading

## 🔧 Troubleshooting

### **Common Issues**

#### **"Connection refused" or "Server not running"**
```bash
# Check if your AI server is running
# For LM Studio: Look for "Server Running" in the UI
# For Ollama: 
ollama ps  # Check running models
ollama serve  # Start server if needed
```

#### **"Out of memory" errors**
- Try a smaller model (3B instead of 7B)
- Close other applications
- Increase virtual memory/swap
- Consider upgrading RAM

#### **Slow responses**
- Use GPU acceleration if available
- Try a smaller model
- Adjust `LLM_MAX_TOKENS` to a lower value
- Close background applications

#### **Model not found**
```bash
# For Ollama - list available models
ollama list

# Download missing model
ollama pull llama3.2:3b
```

## 🔄 Switching Between Local Providers

WhisperEngine can easily switch between local AI providers:

### **LM Studio → Ollama**
1. Stop LM Studio server
2. Start Ollama with your preferred model
3. WhisperEngine will automatically detect the change

### **Testing Multiple Providers**
```bash
# Test LM Studio
LLM_CHAT_API_URL=http://localhost:1234/v1 python run.py

# Test Ollama  
LLM_CHAT_API_URL=http://localhost:11434/v1 python run.py
```

## 🛡️ Privacy & Security

### **Local AI Benefits**
- ✅ **Complete Privacy**: No data leaves your machine
- ✅ **Offline Operation**: Works without internet
- ✅ **No API Keys**: No external service dependencies
- ✅ **Full Control**: You own and control the AI models
- ✅ **No Rate Limits**: Unlimited usage

### **Security Considerations**
- Models are stored locally on your machine
- No telemetry or usage tracking
- No external network connections required
- Complete audit trail of all AI interactions

---

## 🚀 Quick Start Commands

### **LM Studio Setup**
```bash
# 1. Download and install LM Studio
# 2. Download a model through the UI
# 3. Start the server
# 4. Configure WhisperEngine
echo "LLM_CHAT_API_URL=http://localhost:1234/v1" >> .env
python run.py
```

### **Ollama Setup**
```bash
# 1. Install Ollama
brew install ollama  # or download from ollama.ai

# 2. Download and run a model
ollama pull llama3.2:3b
ollama serve &

# 3. Configure WhisperEngine  
echo "LLM_CHAT_API_URL=http://localhost:11434/v1" >> .env
echo "LLM_MODEL_NAME=llama3.2:3b" >> .env
python run.py
```

**Ready to chat with complete privacy!** Your AI companion now runs entirely on your machine. 🏠