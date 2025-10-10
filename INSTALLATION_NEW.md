# 🏗️ WhisperEngine Installation & Setup Guide

**Complete installation guide for WhisperEngine - from zero to AI character platform in minutes.**

## 📋 Table of Contents

- [System Requirements](#-system-requirements)
- [Installation Methods](#-installation-methods)
- [Configuration](#-configuration)
- [Verification](#-verification)
- [Production Setup](#-production-setup)
- [Troubleshooting](#-troubleshooting)
- [Advanced Configuration](#-advanced-configuration)

## 🖥️ System Requirements

### **Minimum Requirements**
- **OS**: macOS 10.14+, Windows 10+, or Linux (Ubuntu 18.04+)
- **RAM**: 4GB available memory (8GB+ recommended)
- **Storage**: 10GB free disk space (includes ~400MB pre-downloaded AI models)
- **Network**: Internet connection for AI model access (models pre-cached in containers)

### **Recommended Requirements**
- **RAM**: 8GB+ for better performance
- **Storage**: 20GB+ for logs and character data
- **CPU**: Multi-core processor for concurrent character handling

### **Required Software**

#### **Docker Desktop** ⭐ (Essential)
- **Download**: [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/)
- **Version**: Docker Desktop 4.0+ (includes Docker Compose V2)
- **Setup**: Install and start Docker Desktop before proceeding

#### **Git** (For downloading WhisperEngine)
- **Download**: [git-scm.com/downloads](https://git-scm.com/downloads)
- **Alternative**: Download WhisperEngine as ZIP from GitHub

#### **Text Editor** (For configuration)
- **Options**: VS Code, Sublime Text, Notepad++, nano, vim
- **Purpose**: Editing `.env` configuration files

## 🚀 Installation Methods

### **Method 1: Instant Containerized Setup** ⭐ (Recommended)

**No source code required - uses pre-built Docker Hub containers!**

This method downloads only the necessary configuration files (under 5KB) and uses pre-built containers from Docker Hub.

**macOS/Linux/WSL:**
```bash
curl -sSL https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/setup-containerized.sh | bash
```

**Windows Command Prompt:**
```cmd
curl -sSL https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/setup-containerized.bat -o setup.bat && setup.bat
```

**Windows PowerShell:**
```powershell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/setup-containerized.bat" -OutFile "setup.bat"
.\setup.bat
```

**What this method does:**
1. ✅ Downloads Docker Compose configuration and environment template (5KB total)
2. ✅ Pulls pre-built containers from Docker Hub (~2GB total)
3. ✅ **Pre-downloaded AI Models**: Containers include ~400MB of models for instant startup
   - FastEmbed: sentence-transformers/all-MiniLM-L6-v2 (embeddings)
   - RoBERTa: cardiffnlp emotion analysis (11 emotions)
4. ✅ Creates configuration file and opens it for editing
5. ✅ Starts WhisperEngine with web UI and chat API
6. ✅ No source code compilation or Git repository required

### **Method 2: Manual Containerized Setup**

If you prefer step-by-step control:

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

# 6. Verify installation
curl http://localhost:9090/health
```

### **Method 3: Developer Setup** (Source code access)

For developers who want to modify the source code or build custom containers:

#### **Step 1: Download WhisperEngine**
```bash
git clone https://github.com/whisperengine-ai/whisperengine.git
cd whisperengine
```

#### **Step 2: Create Configuration**
```bash
cp .env.quickstart.template .env
```

#### **Step 3: Configure API Access**
Edit `.env` with your text editor:
```bash
# Required: Add your LLM API key
LLM_CHAT_API_KEY=your_api_key_here

# Optional: Choose your model
LLM_CHAT_MODEL=anthropic/claude-3-haiku
```

#### **Step 4: Start WhisperEngine**
```bash
docker-compose -f docker-compose.quickstart.yml up -d
```

#### **Step 5: Verify Installation**
```bash
# Check all services are running
docker-compose -f docker-compose.quickstart.yml ps

# Open web interface
open http://localhost:3001  # macOS
# OR visit http://localhost:3001 in your browser
```

### **Method 3: Production Installation**

For production environments, see [Production Setup](#-production-setup) section below.

## ⚙️ Configuration

### **Required Configuration**

#### **LLM API Access** (Required)

WhisperEngine requires access to Large Language Models. Choose one provider:

##### **OpenRouter** ⭐ (Recommended for beginners)
```bash
# .env configuration
LLM_CLIENT_TYPE=openrouter
LLM_CHAT_API_KEY=sk-or-v1-your_openrouter_key
LLM_CHAT_MODEL=anthropic/claude-3-haiku
LLM_CHAT_API_URL=https://openrouter.ai/api/v1
```

**Getting OpenRouter API Key:**
1. Visit [openrouter.ai](https://openrouter.ai)
2. Sign up (Google/GitHub/email)
3. Go to "Keys" → "Create Key"
4. Copy key and paste in `.env`

##### **OpenAI**
```bash
# .env configuration
LLM_CLIENT_TYPE=openai
LLM_CHAT_API_KEY=sk-your_openai_key
LLM_CHAT_MODEL=gpt-4o-mini
LLM_CHAT_API_URL=https://api.openai.com/v1
```

**Getting OpenAI API Key:**
1. Visit [platform.openai.com](https://platform.openai.com)
2. Create account and add billing
3. Go to "API Keys" → "Create new secret key"
4. Copy key and paste in `.env`

##### **Local Models** (Advanced)
```bash
# .env configuration for local Ollama
LLM_CLIENT_TYPE=local
LLM_CHAT_API_URL=http://localhost:11434/v1
LLM_CHAT_MODEL=llama3.1:8b
```

**Setting up Ollama:**
1. Install [Ollama](https://ollama.ai)
2. Pull a model: `ollama pull llama3.1:8b`
3. Start Ollama service
4. Configure WhisperEngine to use local endpoint

### **Optional Configuration**

#### **Discord Integration**
```bash
# Enable Discord bot functionality
ENABLE_DISCORD=true
DISCORD_BOT_TOKEN=your_discord_bot_token

# Discord-specific settings
DISCORD_COMMAND_PREFIX=/
DISCORD_SYNC_COMMANDS=true
```

**Setting up Discord Bot:**
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create "New Application"
3. Go to "Bot" → "Add Bot"
4. Copy token to `.env`
5. Generate invite URL with "Send Messages" permission

#### **Character Settings**
```bash
# Default character configuration
CHARACTER_NAME=assistant
CHARACTER_DESCRIPTION="A helpful AI assistant"

# Character behavior
DEFAULT_PERSONALITY_TRAITS=helpful,patient,knowledgeable
DEFAULT_COMMUNICATION_STYLE=friendly_professional
```

#### **Database Configuration**
```bash
# PostgreSQL settings (using containerized database)
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
POSTGRES_DB=whisperengine
POSTGRES_USER=whisperengine
POSTGRES_PASSWORD=your_secure_password

# Vector database settings (Qdrant)
QDRANT_HOST=localhost
QDRANT_PORT=6334
QDRANT_COLLECTION_NAME=whisperengine_memory
```

#### **Advanced LLM Settings**
```bash
# Model parameters
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2048
LLM_TOP_P=0.9

# Request settings
LLM_TIMEOUT=30
LLM_MAX_RETRIES=3
LLM_RETRY_DELAY=1

# Context management
MAX_CONVERSATION_HISTORY=20
MAX_MEMORY_RETRIEVAL=10
```

#### **Security & Privacy**
```bash
# Enable security features
ENABLE_RATE_LIMITING=true
MAX_REQUESTS_PER_MINUTE=60

# Privacy settings
LOG_USER_MESSAGES=false
ANONYMIZE_LOGS=true
DATA_RETENTION_DAYS=30
```

### **Environment-Specific Configuration**

#### **Development Environment**
```bash
# Development settings
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=debug

# Enable development features
ENABLE_DEBUG_ENDPOINTS=true
ENABLE_API_DOCS=true
```

#### **Production Environment**
```bash
# Production settings
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=info

# Security hardening
ENABLE_DEBUG_ENDPOINTS=false
ENABLE_HTTPS=true
SECURE_COOKIES=true
```

## ✅ Verification

### **Installation Verification**

#### **1. Check Docker Services**
```bash
docker-compose -f docker-compose.quickstart.yml ps
```

**Expected Output:**
```
NAME                        STATUS    PORTS
whisperengine-assistant     Up        0.0.0.0:9090->9090/tcp
cdl-web-ui                  Up        0.0.0.0:3001->3001/tcp
postgres                    Up        0.0.0.0:5433->5432/tcp
qdrant                      Up        0.0.0.0:6334->6333/tcp
```

#### **2. Test Web Interface**
```bash
# Should open browser to web interface
open http://localhost:3001

# Or check manually
curl -s http://localhost:3001 | grep -i "whisperengine"
```

#### **3. Test API Endpoint**
```bash
curl -X GET http://localhost:9090/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "version": "2024.1.0",
  "services": {
    "api": "running",
    "database": "connected",
    "vector_db": "connected",
    "llm": "configured"
  }
}
```

#### **4. Test Character Chat**
```bash
curl -X POST http://localhost:9090/api/chat \\
  -H "Content-Type: application/json" \\
  -d '{
    "user_id": "test_user",
    "message": "Hello! Can you introduce yourself?",
    "context": {"platform": "api"}
  }'
```

**Expected Response:**
```json
{
  "response": "Hello! I'm your AI assistant...",
  "user_id": "test_user",
  "character_name": "assistant",
  "processing_time_ms": 1250,
  "success": true
}
```

### **Performance Verification**

#### **Memory Usage Check**
```bash
docker stats --no-stream
```

#### **Log Analysis**
```bash
# Check for errors
docker-compose -f docker-compose.quickstart.yml logs | grep -i error

# Check startup logs
docker-compose -f docker-compose.quickstart.yml logs whisperengine-assistant | tail -20
```

#### **Database Connection Test**
```bash
# Test PostgreSQL connection
docker exec -it whisperengine-postgres-1 psql -U whisperengine -d whisperengine -c "SELECT version();"

# Test Qdrant connection
curl http://localhost:6334/collections
```

## 🏭 Production Setup

### **Production Installation**

#### **1. Clone Repository**
```bash
git clone https://github.com/whisperengine-ai/whisperengine.git
cd whisperengine
```

#### **2. Create Production Configuration**
```bash
cp .env.production.template .env.production
```

#### **3. Configure Production Settings**
```bash
# Edit .env.production with production values
nano .env.production
```

**Key Production Settings:**
```bash
# Environment
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=info

# Security
ENABLE_HTTPS=true
SSL_CERT_PATH=/etc/ssl/certs/whisperengine.crt
SSL_KEY_PATH=/etc/ssl/private/whisperengine.key

# Database (use external managed databases)
POSTGRES_HOST=your-postgres-server.com
POSTGRES_PORT=5432
QDRANT_HOST=your-qdrant-server.com
QDRANT_PORT=6333

# API Keys (use environment-specific keys)
LLM_CHAT_API_KEY=prod_api_key_here

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9091
SENTRY_DSN=your_sentry_dsn_here
```

#### **4. Start Production Environment**
```bash
docker-compose -f docker-compose.production.yml up -d
```

### **Production Checklist**

#### **Security**
- [ ] Use strong passwords for all database accounts
- [ ] Enable HTTPS with valid SSL certificates
- [ ] Configure firewall to restrict access to necessary ports only
- [ ] Use environment-specific API keys (not development keys)
- [ ] Enable API rate limiting
- [ ] Configure log anonymization

#### **Monitoring**
- [ ] Set up health check endpoints
- [ ] Configure log aggregation (ELK stack, Fluentd, etc.)
- [ ] Set up metrics collection (Prometheus/Grafana)
- [ ] Configure alerting for system failures
- [ ] Monitor API response times and error rates

#### **Backup & Recovery**
- [ ] Configure automated database backups
- [ ] Test backup restoration procedures
- [ ] Set up vector database backups
- [ ] Document recovery procedures
- [ ] Test disaster recovery scenarios

#### **Scalability**
- [ ] Configure horizontal scaling for API services
- [ ] Set up load balancing for multiple instances
- [ ] Configure database connection pooling
- [ ] Monitor resource usage and plan scaling

### **Production Architecture**

```
                    ┌─────────────────┐
                    │   Load Balancer │
                    │    (nginx)      │
                    └─────────┬───────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
    ┌─────────▼──────┐ ┌──────▼─────┐ ┌──────▼─────┐
    │ WhisperEngine  │ │WhisperEngine│ │WhisperEngine│
    │   Instance 1   │ │ Instance 2  │ │ Instance 3 │
    └─────────┬──────┘ └──────┬─────┘ └──────┬─────┘
              │               │               │
              └───────────────┼───────────────┘
                              │
              ┌───────────────▼───────────────┐
              │                               │
    ┌─────────▼──────┐              ┌────────▼──────┐
    │   PostgreSQL   │              │    Qdrant     │
    │   (Managed)    │              │  (Managed)    │
    └────────────────┘              └───────────────┘
```

## 🔧 Troubleshooting

### **Common Installation Issues**

#### **Docker Issues**

**Problem**: "Docker is not running"
```bash
# Check if Docker is running
docker --version
docker ps
```
**Solution**: Start Docker Desktop and wait for full initialization

**Problem**: "Port already in use"
```bash
# Check which process is using the port
lsof -i :3001
lsof -i :9090
```
**Solution**: Stop conflicting services or change ports in docker-compose.quickstart.yml

**Problem**: "Permission denied" (Linux)
```bash
# Add user to docker group
sudo usermod -aG docker $USER
# Logout and login again
```

#### **Configuration Issues**

**Problem**: "API key not working"
```bash
# Verify API key format
echo $LLM_CHAT_API_KEY
# Test API key directly
curl -H "Authorization: Bearer $LLM_CHAT_API_KEY" https://openrouter.ai/api/v1/models
```
**Solution**: Check API key format, verify it's active, check quotas

**Problem**: "Model not found"
```bash
# List available models
curl -H "Authorization: Bearer $LLM_CHAT_API_KEY" https://openrouter.ai/api/v1/models
```
**Solution**: Use exact model name from provider's model list

#### **Network Issues**

**Problem**: "Cannot connect to services"
```bash
# Test network connectivity
curl -I http://localhost:3001
curl -I http://localhost:9090/health
```
**Solution**: Check firewall settings, verify ports aren't blocked

**Problem**: "Database connection failed"
```bash
# Check database container
docker-compose -f docker-compose.quickstart.yml logs postgres
# Test connection
docker exec -it whisperengine-postgres-1 pg_isready
```

### **Performance Issues**

#### **Slow Response Times**
```bash
# Check resource usage
docker stats

# Check logs for timeouts
docker-compose -f docker-compose.quickstart.yml logs | grep -i timeout

# Monitor API response times
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:9090/health
```

#### **Memory Issues**
```bash
# Check memory usage
docker system df
docker system prune  # Clean up unused resources

# Increase Docker memory allocation in Docker Desktop settings
```

### **Character Issues**

#### **Character Not Responding**
```bash
# Check character configuration
curl http://localhost:9090/api/characters

# Verify character is loaded
curl http://localhost:9090/api/characters/assistant

# Check for errors in logs
docker-compose -f docker-compose.quickstart.yml logs whisperengine-assistant | grep -i error
```

#### **Memory/Conversation Issues**
```bash
# Check vector database
curl http://localhost:6334/collections

# Verify conversation storage
curl -X POST http://localhost:9090/api/chat \\
  -H "Content-Type: application/json" \\
  -d '{"user_id": "debug", "message": "test", "context": {}}'
```

### **Getting Help**

#### **Diagnostic Information Collection**
```bash
# Create diagnostic report
cat > diagnostic_info.txt << EOF
=== System Information ===
OS: $(uname -a)
Docker: $(docker --version)
Docker Compose: $(docker-compose --version)

=== Service Status ===
$(docker-compose -f docker-compose.quickstart.yml ps)

=== Recent Logs ===
$(docker-compose -f docker-compose.quickstart.yml logs --tail=50)

=== Health Check ===
$(curl -s http://localhost:9090/health)
EOF
```

#### **Support Channels**
- **GitHub Issues**: [whisperengine-ai/whisperengine/issues](https://github.com/whisperengine-ai/whisperengine/issues)
- **Documentation**: [docs/](docs/)
- **API Documentation**: [docs/api/](docs/api/)

## 🎛️ Advanced Configuration

### **Multi-Character Setup**

For running multiple AI characters simultaneously:

```bash
# Copy multi-character configuration
cp docker-compose.multi-character.template.yml docker-compose.yml

# Configure character-specific settings
cp .env.character1.template .env.elena
cp .env.character2.template .env.marcus

# Start multi-character environment
docker-compose up -d
```

### **Custom Model Integration**

#### **Local Model Setup**
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull models
ollama pull llama3.1:8b
ollama pull mistral:7b

# Configure WhisperEngine
echo "LLM_CLIENT_TYPE=local" >> .env
echo "LLM_CHAT_API_URL=http://localhost:11434/v1" >> .env
echo "LLM_CHAT_MODEL=llama3.1:8b" >> .env
```

#### **Custom API Integration**
```bash
# Configure custom LLM endpoint
LLM_CLIENT_TYPE=custom
LLM_CHAT_API_URL=https://your-custom-api.com/v1
LLM_CHAT_API_KEY=your_custom_key
LLM_CHAT_MODEL=your_custom_model
```

### **Database Optimization**

#### **PostgreSQL Tuning**
```bash
# Create custom PostgreSQL configuration
cat > postgres_custom.conf << EOF
max_connections = 200
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
EOF

# Mount custom config in docker-compose.yml
volumes:
  - ./postgres_custom.conf:/etc/postgresql/postgresql.conf
```

#### **Qdrant Optimization**
```bash
# Configure Qdrant for production
cat > qdrant_config.yaml << EOF
storage:
  storage_path: ./storage
  snapshots_path: ./snapshots
service:
  max_request_size_mb: 32
  max_workers: 0
EOF
```

### **Development Mode**

For development and testing:

```bash
# Enable development features
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=debug
ENABLE_DEBUG_ENDPOINTS=true
ENABLE_API_DOCS=true

# Hot reload configuration
ENABLE_HOT_RELOAD=true
WATCH_FILES=true

# Start development environment
docker-compose -f docker-compose.dev.yml up
```

### **Monitoring Setup**

#### **Prometheus Metrics**
```bash
# Enable metrics collection
ENABLE_METRICS=true
METRICS_PORT=9091

# Add Prometheus configuration
cat > prometheus.yml << EOF
global:
  scrape_interval: 15s
scrape_configs:
  - job_name: 'whisperengine'
    static_configs:
      - targets: ['localhost:9091']
EOF
```

#### **Log Aggregation**
```bash
# Configure structured logging
LOG_FORMAT=json
LOG_OUTPUT=stdout

# Set up log forwarding to external systems
SENTRY_DSN=your_sentry_dsn
ELASTICSEARCH_URL=http://your-elasticsearch:9200
```

## 🎉 Next Steps

### **After Installation**
1. **Create your first character** via web interface
2. **Test chat functionality** with sample conversations
3. **Configure Discord integration** (optional)
4. **Set up monitoring** for production use
5. **Explore API documentation** for integrations

### **Learning Resources**
- **[Character Creation Guide](docs/characters/README.md)**
- **[API Documentation](docs/api/README.md)**
- **[Discord Bot Setup](docs/discord/README.md)**
- **[Production Deployment](docs/production/README.md)**

**🎊 Congratulations! WhisperEngine is now installed and ready to use.**