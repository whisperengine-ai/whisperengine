# Installation & Configuration Guide

This comprehensive guide covers WhisperEngine installation with **Docker-first development** approach, configuration options, troubleshooting, and all available features.

> **🪟 Windows Users:** For comprehensive Windows-specific setup with PowerShell commands and Docker Desktop guidance, see the **[Windows Setup Guide in our main README](../../README.md#-windows-users-complete-setup-guide)**. This guide contains platform-agnostic instructions that work on all systems.

## 🐳 Docker-First Installation (Recommended)

### Prerequisites

**System Requirements:**
- **Docker & Docker Compose** - [Install Docker](https://docs.docker.com/get-docker/)
- **Git** - For cloning the repository
- **8GB+ RAM** - For running multiple containers
- **10GB+ Storage** - For Docker images and data volumes

**Platform Support:**
- ✅ **Windows 10/11** (Docker Desktop)
- ✅ **macOS** (Intel & Apple Silicon with Docker Desktop)
- ✅ **Linux** (Docker Engine + Docker Compose)

### 🚀 Quick Installation

```bash
# 1. Clone WhisperEngine
git clone https://github.com/whisperengine-ai/whisperengine.git
cd whisperengine

# 2. Setup your first character (Elena - Marine Biologist)
cp .env.template .env.elena
# Edit .env.elena with Discord token and LLM API key

# 3. Generate Docker configuration
python scripts/generate_multi_bot_config.py

# 4. Start complete system
./multi-bot.sh start elena

# 5. Verify everything is running
./multi-bot.sh status
```

That's it! You now have a production-ready WhisperEngine system with:
- Elena Discord bot with marine biologist personality
- PostgreSQL database (port 5433) for semantic knowledge
- Qdrant vector database (port 6334) for conversation memory  
- HTTP Chat API (port 9091) for 3rd party integration

## 🔧 Configuration

### Discord Bot Setup

1. **Create Discord Application**
   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Click "New Application" → Name it (e.g., "Elena Marine Bot")

2. **Create Bot & Configure**
   - Go to "Bot" section → Click "Add Bot"
   - Copy the token → Add to `.env.elena`
   - **⚠️ CRITICAL**: Enable "Message Content Intent" 

3. **Set Bot Permissions**
   - Go to "OAuth2" → "URL Generator"
   - **Scopes**: Check "bot"
   - **Permissions**: Check:
     - ✅ Send Messages
     - ✅ Read Message History
     - ✅ Use Slash Commands
     - ✅ Add Reactions
     - ✅ Embed Links

### LLM Provider Setup

Choose your AI service and configure in `.env.elena`:

#### Option A: OpenRouter (Recommended)
```env
LLM_CLIENT_TYPE=openrouter
OPENROUTER_API_KEY=your_api_key_here
LLM_CHAT_MODEL=anthropic/claude-3.5-sonnet
```

#### Option B: Anthropic Direct
```env
LLM_CLIENT_TYPE=anthropic
ANTHROPIC_API_KEY=your_api_key_here
LLM_CHAT_MODEL=claude-3-5-sonnet-20241022
```

#### Option C: OpenAI
```env
LLM_CLIENT_TYPE=openai
OPENAI_API_KEY=your_api_key_here
LLM_CHAT_MODEL=gpt-4o
```

#### Option D: Local LLM (Ollama)
```bash
# Install Ollama first
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve
ollama pull llama3.1:8b

# Configure in .env.elena
LLM_CLIENT_TYPE=ollama
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=llama3.1:8b
```

### Environment Template

Here's a complete `.env.elena` example:

```env
# Discord Configuration
DISCORD_BOT_TOKEN=your_discord_bot_token_here
DISCORD_BOT_NAME=elena

# Character Configuration
CHARACTER_FILE=elena  # Database-stored CDL character

# LLM Configuration
LLM_CLIENT_TYPE=openrouter
OPENROUTER_API_KEY=your_openrouter_api_key_here
LLM_CHAT_MODEL=anthropic/claude-3.5-sonnet

# Infrastructure (auto-configured for Docker)
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=whisperengine
POSTGRES_USER=whisperengine
POSTGRES_PASSWORD=whisperengine_password

QDRANT_HOST=qdrant
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=whisperengine_memory_elena

# Health Monitoring
HEALTH_CHECK_PORT=9091
```

## 🎭 Multi-Character Setup

### Add More Characters

```bash
# Setup Marcus (AI Researcher)
cp .env.template .env.marcus
# Edit .env.marcus:
# - Unique DISCORD_BOT_TOKEN
# - CHARACTER_FILE=marcus  
# - QDRANT_COLLECTION_NAME=whisperengine_memory_marcus
# - HEALTH_CHECK_PORT=9092

# Setup Jake (Adventure Photographer)  
cp .env.template .env.jake
# Edit .env.jake with unique token and port 9097

# Regenerate Docker configuration
python scripts/generate_multi_bot_config.py

# Start all characters
./multi-bot.sh start all
```

### Available Characters

| Character | File | Port | Specialty |
|-----------|------|------|-----------|
| Elena | `.env.elena` | 9091 | Marine Biologist |
| Marcus | `.env.marcus` | 9092 | AI Researcher |
| Jake | `.env.jake` | 9097 | Adventure Photographer |
| Ryan | `.env.ryan` | 9093 | Game Developer |
| Gabriel | `.env.gabriel` | 9095 | British Gentleman |
| Sophia | `.env.sophia` | 9096 | Marketing Executive |
| Dream | `.env.dream` | 9094 | Mythological Entity |
| Aethys | `.env.aethys` | 3007 | Omnipotent Being |

## 🔧 Advanced Configuration

### Development Mode

For development work with hot reloading:

```bash
# Start infrastructure only
docker-compose up postgres qdrant

# Run bot in development mode
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements-discord.txt
python run.py --dev
```

### Production Deployment

```bash
# Use production Docker configuration
./multi-bot.sh start all

# Enable monitoring and logging
docker logs whisperengine-elena-bot -f
docker logs whisperengine-multi-postgres -f
docker logs whisperengine-multi-qdrant -f

# Set up log rotation and monitoring
# See docs/deployment/PRODUCTION_SETUP.md
```

### Local LLM Integration

For complete privacy with local AI models:

```bash
# Option 1: Ollama (recommended)
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve
ollama pull llama3.1:8b

# Option 2: LM Studio  
# Download from https://lmstudio.ai/
# Start server on port 1234

# Configure in .env.elena
LLM_CLIENT_TYPE=ollama
OLLAMA_BASE_URL=http://host.docker.internal:11434  # Docker access to host
OLLAMA_MODEL=llama3.1:8b
```

## 🛠️ Management Commands

### Multi-Bot Management

```bash
# Start specific character
./multi-bot.sh start elena

# Start all configured characters
./multi-bot.sh start all

# Stop specific character
./multi-bot.sh stop elena

# Restart with configuration changes
./multi-bot.sh restart elena

# View logs (recommended for debugging)
./multi-bot.sh logs elena

# Check system status
./multi-bot.sh status

# List available characters
./multi-bot.sh list
```

### Direct Docker Commands

```bash
# Check container status
docker ps

# View specific container logs
docker logs whisperengine-elena-bot --tail 20
docker logs whisperengine-multi-postgres --tail 10
docker logs whisperengine-multi-qdrant --tail 10

# Access container shell
docker exec -it whisperengine-elena-bot bash
docker exec -it whisperengine-multi-postgres psql -U whisperengine

# Check resource usage
docker stats --no-stream
```

### Database Management

```bash
# Access PostgreSQL
docker exec -it whisperengine-multi-postgres psql -U whisperengine

# Access Qdrant web UI
open http://localhost:6334/dashboard

# Check collections
curl http://localhost:6334/collections

# Backup data
docker exec whisperengine-multi-postgres pg_dump -U whisperengine whisperengine > backup.sql
```

## 🧪 Testing & Validation

### Test Discord Bot

```bash
# Check bot status
./multi-bot.sh logs elena | grep "Connected"

# Test in Discord
# Send DM: "Hello Elena!"
# Or mention: "@Elena tell me about marine conservation"
```

### Test HTTP Chat API

```bash
# Test Elena's chat endpoint
curl -X POST http://localhost:9091/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "message": "What do you think about ocean preservation?", 
    "context": {"platform": "api"}
  }'

# Should return rich JSON with emotional intelligence and user facts
```

### Test Memory System

```bash
# Chat with bot, then test memory retrieval
curl http://localhost:9091/api/memory/test_user

# Or in Discord: "What do you remember about me?"
```

### Test Infrastructure

```bash
# Check all services
./multi-bot.sh status

# Test PostgreSQL
docker exec -it whisperengine-multi-postgres psql -U whisperengine -c "SELECT version();"

# Test Qdrant  
curl http://localhost:6334/health

# Check collections
curl http://localhost:6334/collections
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Bot Won't Start
```bash
# Check Docker status
./multi-bot.sh status

# Check configuration
cat .env.elena | grep DISCORD_BOT_TOKEN

# View startup logs
./multi-bot.sh logs elena | head -20
```

#### 2. Discord Connection Issues
```bash
# Verify Message Content Intent is enabled
./multi-bot.sh logs elena | grep "Missing"

# Check bot permissions
./multi-bot.sh logs elena | grep "Forbidden"

# Verify token
./multi-bot.sh logs elena | grep "token"
```

#### 3. LLM Connection Problems
```bash
# Check API configuration
./multi-bot.sh logs elena | grep "LLM"

# Test API key
./multi-bot.sh logs elena | grep -i "unauthorized\|forbidden\|api"

# For Ollama, check host connectivity
docker exec whisperengine-elena-bot curl http://host.docker.internal:11434/v1/models
```

#### 4. Database Connection Issues
```bash
# Check PostgreSQL
docker logs whisperengine-multi-postgres --tail 10

# Check Qdrant
docker logs whisperengine-multi-qdrant --tail 10

# Test connections from bot
docker exec whisperengine-elena-bot nc -zv postgres 5432
docker exec whisperengine-elena-bot nc -zv qdrant 6333
```

#### 5. Memory/Vector Issues
```bash
# Check Qdrant collections
curl http://localhost:6334/collections

# Check collection health
curl http://localhost:6334/collections/whisperengine_memory_elena

# Reset memory (⚠️ deletes all data)
docker volume rm whisperengine_qdrant-data
./multi-bot.sh restart elena
```

### Performance Issues

```bash
# Check resource usage
docker stats --no-stream

# Monitor memory usage
./multi-bot.sh logs elena | grep -i memory

# Check API response times  
./multi-bot.sh logs elena | grep "Processing.*ms"

# Enable debug mode
# Add to .env.elena: DEBUG=true
./multi-bot.sh restart elena
```

### Configuration Validation

```bash
# Validate environment file
python scripts/validate_config.py .env.elena

# Check multi-bot configuration
python scripts/generate_multi_bot_config.py --validate

# Test Discord bot token
python scripts/test_discord_connection.py .env.elena
```

## 📊 Monitoring & Health Checks

### Built-in Monitoring

```bash
# System health overview
curl http://localhost:9091/health

# Detailed health check
curl http://localhost:9091/health?detailed=true

# Component status
./multi-bot.sh status
```

### Log Analysis

```bash
# View real-time logs
./multi-bot.sh logs elena -f

# Search for errors
./multi-bot.sh logs elena | grep -i error

# Monitor performance
./multi-bot.sh logs elena | grep "Processing\|ms\|API"

# Check memory usage
docker logs whisperengine-elena-bot | grep -i "memory\|vector\|qdrant"
```

### Database Monitoring

```bash
# PostgreSQL metrics
docker exec whisperengine-multi-postgres psql -U whisperengine -c "
  SELECT schemaname, tablename, n_tup_ins, n_tup_upd, n_tup_del 
  FROM pg_stat_user_tables;"

# Qdrant metrics
curl http://localhost:6334/metrics

# Collection statistics
curl http://localhost:6334/collections/whisperengine_memory_elena
```

## 🔄 Backup & Recovery

### Data Backup

```bash
# Backup PostgreSQL
docker exec whisperengine-multi-postgres pg_dump -U whisperengine whisperengine > backup_$(date +%Y%m%d).sql

# Backup Qdrant (stop first)
./multi-bot.sh stop
docker run --rm -v whisperengine_qdrant-data:/source -v $(pwd):/backup alpine tar czf /backup/qdrant_backup_$(date +%Y%m%d).tar.gz -C /source .

# Backup configurations
tar czf config_backup_$(date +%Y%m%d).tar.gz .env.*
```

### Data Recovery

```bash
# Restore PostgreSQL
cat backup_20241008.sql | docker exec -i whisperengine-multi-postgres psql -U whisperengine

# Restore Qdrant
./multi-bot.sh stop
docker run --rm -v whisperengine_qdrant-data:/target -v $(pwd):/backup alpine tar xzf /backup/qdrant_backup_20241008.tar.gz -C /target
./multi-bot.sh start elena
```

## 🎓 Next Steps

### Advanced Features

- **[Character Creation](../characters/CDL_CHARACTER_CREATION.md)** - Create custom AI personalities
- **[Production Deployment](../deployment/PRODUCTION_SETUP.md)** - Scale for production use
- **[API Integration](../api/HTTP_CHAT_API.md)** - Build applications with WhisperEngine
- **[Local LLM Guide](../deployment/LOCAL_LLM_SETUP.md)** - Complete privacy setup

### Development

- **[Development Guide](../development/DEVELOPMENT_GUIDE.md)** - Contribute to WhisperEngine
- **[Testing Framework](../testing/TESTING_GUIDE.md)** - Validate your changes
- **[Architecture Deep Dive](../architecture/SYSTEM_ARCHITECTURE.md)** - Understand the system

### Community

- **Discord Community** - Chat with other developers (invite coming soon)
- **[GitHub Issues](https://github.com/whisperengine-ai/whisperengine/issues)** - Report bugs
- **[GitHub Discussions](https://github.com/whisperengine-ai/whisperengine/discussions)** - Ask questions

---

**Need immediate help?** Check the [Quick Start Guide](QUICK_START.md) for the fastest setup path.