# WhisperEngine Deployment Guide

## 🎯 **Deployment Scenarios**

### **Scenario 1: Personal Desktop Use**
**Goal**: Simple AI chat app for personal use  
**Recommended**: Bundled models with option to upgrade

```bash
# Quick setup
./setup.sh              # macOS/Linux
setup.bat               # Windows

# Start app
source .venv/bin/activate && python universal_native_app.py
```

### **Scenario 2: Team/Office Deployment**
**Goal**: Shared AI assistant for small team  
**Recommended**: LM Studio server + desktop clients

```bash
# Server setup (one machine with good hardware)
# 1. Install LM Studio, download Llama 3.1 8B
# 2. Start LM Studio server on port 1234

# Client setup (each user's machine)
./setup.sh
# Edit .env.desktop:
LLM_CHAT_API_URL=http://server-ip:1234/v1
LLM_MODEL_NAME=llama3.1:8b
```

### **Scenario 3: Enterprise/Cloud Deployment**
**Goal**: Scalable AI system with high availability  
**Recommended**: Docker + PostgreSQL + OpenAI API

```bash
# Use Docker Compose
docker-compose -f docker-compose.prod.yml up -d

# Configure enterprise settings
# - PostgreSQL for persistence
# - Redis for caching
# - OpenAI/Azure API for AI
# - Load balancing for scale
```

### **Scenario 4: Offline/Air-Gapped Environment**
**Goal**: Completely offline AI system  
**Recommended**: Bundled models + local database

```bash
# Build with all models bundled
python build_with_models.py

# Deploy executable with no internet access required
# All AI models and dependencies included
```

---

## 🛠️ **Build Configurations**

### **Development Build**
For testing and development:

```bash
# Setup development environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Download models for testing
python download_models.py

# Run in development mode
python universal_native_app.py
```

### **Production Build - Bundled Models**
For distribution with offline AI:

```bash
# Method 1: Automated (recommended)
python build_with_models.py

# Method 2: Manual
python download_models.py
pyinstaller whisperengine.spec
```

**Output**: Single executable with 3GB of bundled AI models

### **Production Build - Lightweight**
For distribution without bundled models:

```bash
# Build without downloading models
pyinstaller whisperengine.spec

# Users must run download_models.py separately
```

**Output**: Small executable (~100MB), models downloaded on first run

### **Cross-Platform Build**
For building multiple platform binaries:

```bash
# Requires Docker for cross-compilation
python build_cross_platform.py

# Outputs:
# - WhisperEngine-macos
# - WhisperEngine-linux  
# - WhisperEngine-windows.exe
```

---

## 📦 **Distribution Strategies**

### **Strategy 1: Single Download (Recommended)**
- Include all models in the build
- Users get complete functionality immediately
- Large download (~3GB) but zero configuration

```bash
python build_with_models.py
# Result: Complete standalone executable
```

### **Strategy 2: Progressive Download**
- Small initial download
- Models downloaded on first run
- Better for users with limited bandwidth

```bash
pyinstaller whisperengine.spec
# Result: Small executable + separate model download
```

### **Strategy 3: Modular Distribution**
- Core app + optional model packs
- Users choose which AI capabilities to install
- Most flexible but requires configuration

```bash
# Core app
pyinstaller whisperengine.spec

# Separate model packages
# - basic-models.zip (embeddings only)
# - conversational-ai.zip (DialoGPT)
# - emotion-analysis.zip (sentiment models)
```

---

## 🔧 **Configuration Management**

### **Environment Files**

#### **`.env.desktop` (Desktop App)**
```bash
# Local AI with bundled models
USE_LOCAL_MODELS=true
LOCAL_LLM_MODEL=microsoft_DialoGPT-medium
LLM_CHAT_API_URL=local://models

# Database (local file)
DATABASE_URL=sqlite:///./whisperengine.db

# UI settings
WEBUI_PORT=8501
ENABLE_SYSTEM_TRAY=true
```

#### **`.env.server` (Server Deployment)**
```bash
# External AI service
LLM_CHAT_API_URL=https://api.openai.com/v1
OPENAI_API_KEY=sk-your-key-here
LLM_MODEL_NAME=gpt-4o-mini

# Database (PostgreSQL)
DATABASE_URL=postgresql://user:pass@db:5432/whisperengine
CHROMADB_HOST=chromadb
CHROMADB_PORT=8000

# Caching
USE_REDIS_CACHE=true
REDIS_URL=redis://redis:6379
```

#### **`.env.offline` (Air-Gapped)**
```bash
# Completely offline configuration
USE_LOCAL_MODELS=true
USE_LOCAL_LLM=true
HF_DATASETS_OFFLINE=1
TRANSFORMERS_OFFLINE=1

# Local storage only
DATABASE_URL=sqlite:///./whisperengine.db
USE_REDIS_CACHE=false
```

### **Configuration Validation**

```bash
# Validate configuration before deployment
python validate_config.py

# Check model availability
python check_dependencies.py

# Test AI connectivity
python test_llm_integration.py
```

---

## 🚀 **Deployment Automation**

### **Docker Deployment**

#### **Single Container (Desktop)**
```dockerfile
# Dockerfile.desktop
FROM python:3.13-slim

# Copy app and models
COPY . /app
COPY models /app/models

# Install dependencies
RUN pip install -r requirements.txt

# Run desktop app
CMD ["python", "desktop_app.py"]
```

#### **Multi-Container (Production)**
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  whisperengine:
    build: .
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/whisperengine
      - CHROMADB_HOST=chromadb
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - chromadb
      - redis

  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: whisperengine
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass

  chromadb:
    image: chromadb/chroma:latest
    
  redis:
    image: redis:alpine
```

### **Cloud Deployment**

#### **AWS ECS**
```json
{
  "family": "whisperengine",
  "containerDefinitions": [
    {
      "name": "whisperengine",
      "image": "whisperengine:latest",
      "memory": 4096,
      "cpu": 2048,
      "environment": [
        {"name": "DATABASE_URL", "value": "postgresql://..."},
        {"name": "OPENAI_API_KEY", "valueFrom": "arn:aws:secretsmanager:..."}
      ]
    }
  ]
}
```

#### **Kubernetes**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: whisperengine
spec:
  replicas: 3
  selector:
    matchLabels:
      app: whisperengine
  template:
    metadata:
      labels:
        app: whisperengine
    spec:
      containers:
      - name: whisperengine
        image: whisperengine:latest
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
```

---

## 📊 **Performance & Scaling**

### **Resource Requirements**

| Deployment Type | RAM | Storage | CPU | Network |
|----------------|-----|---------|-----|---------|
| **Desktop (Bundled)** | 4GB | 5GB | 2 cores | None |
| **Desktop (LM Studio)** | 16GB | 10GB | 4 cores | LAN |
| **Server (Cloud AI)** | 2GB | 1GB | 2 cores | Internet |
| **Enterprise** | 8GB+ | 50GB+ | 4+ cores | High-speed |

### **Scaling Considerations**

#### **Horizontal Scaling**
```bash
# Load balancer + multiple app instances
# Each instance connects to shared database
# AI requests distributed across instances
```

#### **Vertical Scaling**
```bash
# Increase memory for larger models
# Add GPU for faster local AI inference
# Use SSD for faster database operations
```

#### **Caching Strategy**
```bash
# Redis for conversation cache
# ChromaDB for vector embeddings
# File system cache for static assets
```

---

## ✅ **Deployment Checklist**

### **Pre-Deployment**
- [ ] Test build on target platform
- [ ] Validate configuration files
- [ ] Check model availability
- [ ] Test AI connectivity
- [ ] Verify database connections
- [ ] Run integration tests

### **Deployment**
- [ ] Deploy application
- [ ] Configure environment variables
- [ ] Set up database schema
- [ ] Initialize AI models
- [ ] Configure monitoring
- [ ] Set up logging

### **Post-Deployment**
- [ ] Verify AI responses
- [ ] Test user interface
- [ ] Check memory usage
- [ ] Monitor performance
- [ ] Set up backups
- [ ] Document configuration

---

## 🆘 **Troubleshooting Deployment Issues**

### **Common Build Problems**
```bash
# Issue: Models not bundled
# Solution: Run download_models.py before build

# Issue: Missing dependencies
# Solution: Update requirements.txt and hidden imports

# Issue: Large executable size
# Solution: Use lightweight build without models
```

### **Runtime Issues**
```bash
# Issue: AI not responding
# Solution: Check model loading and API configuration

# Issue: High memory usage
# Solution: Use smaller models or increase system RAM

# Issue: Slow responses
# Solution: Upgrade to faster AI service
```

### **Environment-Specific Issues**
```bash
# macOS: Code signing for distribution
codesign --force --deep --sign - WhisperEngine.app

# Windows: Antivirus false positives
# Add exclusion for WhisperEngine.exe

# Linux: Missing system libraries
sudo apt-get install libffi-dev python3-dev
```

---

This guide covers all major deployment scenarios from personal desktop use to enterprise cloud deployment. Choose the configuration that best fits your use case and scale as needed.