# Installation & Configuration Guide

This comprehensive guide covers WhisperEngine installation with **Docker-first development** approach, configuration options, troubleshooting, and all available features.

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
source .venv/bin/activate  # Create venv first: python -m venv .venv
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
   
   # Linux
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Windows
   # Download installer from https://ollama.ai/download
   ```

2. **Start Ollama Service**
   ```bash
   # Start the service
   ollama serve
   ```

3. **Download & Run Models**
   ```bash
   # In a new terminal, download models
   ollama pull llama3.2:3b          # 3B model (fast)
   ollama pull phi3.5:latest        # Phi-3.5 model
   ollama pull llava:latest         # Vision-capable model
   
   # List installed models
   ollama list
   ```

4. **Test Connection**
   ```bash
   curl http://localhost:11434/v1/models -H "Content-Type: application/json"
   ```

#### Option C: OpenRouter (Cloud, Paid)

1. **Create OpenRouter Account**
   - Visit [openrouter.ai](https://openrouter.ai/)
   - Sign up for an account
   - Add credits to your account (typically $5-10 for testing)

2. **Generate API Key**
   - Go to your account dashboard
   - Create a new API key
   - Copy and save the key securely

3. **Choose Model**
   Browse [openrouter.ai/models](https://openrouter.ai/models) and select:
   
   **Cost-Effective:**
   - `openai/gpt-4o-mini` - $0.15/1M tokens
   - `meta-llama/llama-3.1-8b-instruct` - $0.15/1M tokens
   
   **High Quality:**
   - `anthropic/claude-3.5-sonnet` - $3/1M tokens
   - `openai/gpt-4o` - $2.50/1M tokens
   
   **Specialized:**
   - `google/gemini-pro-1.5` - Multimodal
   - `perplexity/llama-3.1-sonar-large-128k-online` - Web search

### 3. Create Discord Bot

1. **Discord Developer Portal**
   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Click "New Application"
   - Enter a name (e.g., "My AI Assistant")

2. **Create Bot User**
   - Navigate to "Bot" section
   - Click "Add Bot"
   - Copy the bot token (keep this secret!)

3. **⚠️ CRITICAL: Configure Bot Settings**
   
   **Privileged Gateway Intents:**
   - ✅ **Message Content Intent** (REQUIRED - bot can't read messages without this)
   - ❌ Server Members Intent (not needed)
   - ❌ Presence Intent (not needed)
   
   **Bot Permissions (set when inviting):**
   - ✅ Send Messages
   - ✅ Read Message History
   - ✅ Use Slash Commands
   - ✅ Add Reactions
   - ✅ Embed Links
   - ✅ Read Messages/View Channels

4. **Generate Invite URL**
   - Go to "OAuth2" → "URL Generator"
   - **Scopes**: Select "bot"
   - **Bot Permissions**: Select the permissions listed above
   - Copy the generated URL
   - Visit the URL to invite your bot to a server

## ⚙️ Configuration

### Environment Setup

1. **Copy Configuration Template**
   ```bash
   # For local LLM users (LM Studio/Ollama):
   cp .env.minimal .env
   
   # For OpenRouter users:
   cp .env.openrouter.example .env
   ```

2. **Edit Configuration File**
   Open `.env` in any text editor:

### Basic Configuration Examples

#### LM Studio Configuration
```env
# Required
DISCORD_BOT_TOKEN=your_discord_bot_token_here
LLM_CHAT_API_URL=http://localhost:1234/v1
LLM_MODEL_NAME=local-model

# Optional vision support
LLM_SUPPORTS_VISION=false    # Set to true if using vision model
LLM_VISION_MAX_IMAGES=5

# Data paths (will be created automatically)
QDRANT_COLLECTION_NAME=whisperengine_memory
BACKUP_PATH=./backups

# Logging
LOG_LEVEL=INFO
```

#### Ollama Configuration
```env
# Required
DISCORD_BOT_TOKEN=your_discord_bot_token_here
LLM_CHAT_API_URL=http://localhost:11434/v1
LLM_MODEL_NAME=llama3.2:3b

# Optional models
# LLM_MODEL_NAME=phi3.5:latest
# LLM_MODEL_NAME=llava:latest      # For vision support

# Data paths
OPENAI_API_KEY=your_openai_api_key_here
LLM_MODEL_NAME=gpt-4o-mini

# Data paths
QDRANT_COLLECTION_NAME=whisperengine_memory
BACKUP_PATH=./backups

# Logging
LOG_LEVEL=INFO
```

#### OpenRouter Configuration
```env
# Required
DISCORD_BOT_TOKEN=your_discord_bot_token_here
LLM_CHAT_API_URL=https://openrouter.ai/api/v1
OPENROUTER_API_KEY=your_openrouter_api_key_here
LLM_MODEL_NAME=anthropic/claude-3.5-sonnet

# Alternative models
# LLM_MODEL_NAME=openai/gpt-4o-mini          # Cost-effective
# LLM_MODEL_NAME=meta-llama/llama-3.1-8b-instruct
# LLM_MODEL_NAME=google/gemini-pro-1.5       # Multimodal

# Data paths
QDRANT_COLLECTION_NAME=whisperengine_memory
BACKUP_PATH=./backups

# Logging
LOG_LEVEL=INFO
```

### Advanced Multi-Service Configuration

#### Hybrid Setup (Recommended for Cost Optimization)
```env
# === MAIN CHAT SERVICE (High Quality) ===
DISCORD_BOT_TOKEN=your_discord_bot_token_here
LLM_CHAT_API_URL=https://openrouter.ai/api/v1
OPENROUTER_API_KEY=your_openrouter_key
LLM_MODEL_NAME=anthropic/claude-3.5-sonnet

# === ANALYSIS SERVICE (Fast, Cheap/Free) ===
LLM_EMOTION_API_URL=http://localhost:1234/v1
LLM_EMOTION_MODEL_NAME=local-model

# This gives you premium chat quality with free background analysis!
```

#### Advanced Performance Tuning
```env
# === TIMEOUT SETTINGS ===
MAX_PROCESSING_TIME=90.0           # Max time per message (seconds)
LLM_REQUEST_TIMEOUT=90             # LLM request timeout (LM Studio can be slow)
DISCORD_LLM_TIMEOUT=120            # Discord-specific timeout (LM Studio can be slow)

# === MEMORY & PERFORMANCE ===
MEMORY_THREAD_POOL_SIZE=4          # Thread pool for memory operations
IMAGE_THREAD_POOL_SIZE=2           # Thread pool for image processing
CONVERSATION_CACHE_TIMEOUT=900     # Cache expiration (15 minutes)
MEMORY_SIMILARITY_THRESHOLD=0.7     # Memory search sensitivity

# === TOKEN LIMITS (Cost Control) ===
LLM_MAX_TOKENS_CHAT=4096           # Main conversation responses
LLM_MAX_TOKENS_EMOTION=200         # Emotion analysis
LLM_MAX_TOKENS_FACT_EXTRACTION=500 # Fact extraction

# === FEATURE TOGGLES ===
ENABLE_AUTO_FACTS=true             # Auto-extract user facts
ENABLE_GLOBAL_FACTS=false          # Auto-extract global facts
ENABLE_EMOTIONS=true               # Emotion analysis system

# === ADMIN CONTROLS ===
ADMIN_USER_IDS=123456789012345678,987654321098765432  # Your Discord user ID
```

### Complete Configuration Reference

See `.env.minimal` for all available options with detailed comments.

## 🚀 Running the Bot

### Basic Startup
```bash
# Normal operation
python basic_discord_bot.py

# Debug mode (verbose logging)
python basic_discord_bot.py --debug

# Check version and help
python basic_discord_bot.py --help
```

### Running as a Service

#### Linux (systemd)
```bash
# Create service file
sudo nano /etc/systemd/system/discord-bot.service

# Add this content:
[Unit]
Description=Custom Discord Bot
After=network.target

[Service]
Type=simple
User=whisperengine
WorkingDirectory=/path/to/whisperengine
Environment=PATH=/path/to/whisperengine/bot_env/bin
ExecStart=/path/to/whisperengine/bot_env/bin/python basic_discord_bot.py
Restart=always

[Install]
WantedBy=multi-user.target

# Enable and start
sudo systemctl enable discord-bot
sudo systemctl start discord-bot
sudo systemctl status discord-bot
```

#### Windows (Task Scheduler)
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., "At startup")
4. Set action to start your Python script
5. Configure to restart on failure

### Production Deployment
```bash
# Use process manager like PM2
npm install -g pm2
pm2 start basic_discord_bot.py --name discord-bot --interpreter python
pm2 startup
pm2 save
```

## 💬 Commands Reference

### 🎯 Natural Conversation
**No commands needed for basic chat!**
- **Direct Messages**: Just send a DM to the bot
- **Channel Mentions**: Mention `@BotName` in any channel
- **Image Support**: Attach images to your messages for multimodal chat
- **Context Aware**: Bot remembers your conversation history and personal facts

### 📝 Basic Commands
| Command | Description | Example |
|---------|-------------|---------|
| `!ping` | Test bot connectivity and response time | `!ping` |
| `!bot_status` | Check Discord connection health | `!bot_status` |
| `!llm_status` | Check LLM connection and model info | `!llm_status` |
| `!commands` | Show all available commands | `!commands` |
| `!help_custom` | Alternative help command | `!help_custom` |
| `!clear_chat` | Clear conversation history in current channel | `!clear_chat` |

### 🖼️ Image Processing Commands
| Command | Description | Example |
|---------|-------------|---------|
| `!vision_status` | Check if vision/image processing is enabled | `!vision_status` |
| `!test_image` | Test image processing (attach image) | `!test_image` + image |
| `!cache_stats` | Show conversation cache statistics | `!cache_stats` |

**Supported Image Formats**: JPG, PNG, GIF, WebP, BMP  
**File Limits**: 10MB max, auto-resized to 2048×2048 pixels

### 💾 Memory Management Commands
| Command | Description | Example |
|---------|-------------|---------|
| `!add_fact <fact>` | Manually add personal facts | `!add_fact I love coffee` |
| `!list_facts` | View all stored facts about you | `!list_facts` |
| `!remove_fact <search>` | Search and remove facts | `!remove_fact coffee` |
| `!remove_fact_by_number <num> <search>` | Remove specific fact by number | `!remove_fact_by_number 2 coffee` |
| `!my_memory` | Overview of what bot remembers | `!my_memory` |
| `!forget_me` | Delete ALL your data (requires confirmation) | `!forget_me` |

### 🤖 Automatic Fact Discovery Commands
| Command | Description | Example |
|---------|-------------|---------|
| `!auto_facts [on/off]` | Toggle automatic fact extraction | `!auto_facts on` |
| `!auto_extracted_facts` | View automatically discovered facts | `!auto_extracted_facts` |
| `!extract_facts <message>` | Test fact extraction | `!extract_facts I work in tech` |

### 📱 DM-Only Commands
| Command | Description | Example |
|---------|-------------|---------|
| `!sync_check` | Verify DM conversation storage | `!sync_check` |
| `!import_history [limit]` | Import older DM conversations | `!import_history 50` |

### ⚙️ Admin Commands
| Command | Description | Example |
|---------|-------------|---------|
| `!debug [on/off/status]` | Toggle debug logging level | `!debug on` |
| `!memory_stats` | View memory system statistics | `!memory_stats` |
| `!system_status` | Comprehensive system health check | `!system_status` |
| `!add_global_fact <fact>` | Add global knowledge | `!add_global_fact Python is a programming language` |
| `!list_global_facts` | List all global facts | `!list_global_facts` |
| `!remove_global_fact <search>` | Remove global facts | `!remove_global_fact Python` |
| `!create_backup` | Create memory system backup | `!create_backup` |
| `!list_backups` | List available system backups | `!list_backups` |

### 🔧 System & Utility Commands
| Command | Description | Example |
|---------|-------------|---------|
| `!ask <question>` | Explicit AI query with full context | `!ask Tell me about the weather` |
| `!help` | Discord's default help | `!help` |

## 🧪 Testing & Validation

### Pre-Launch Testing
```bash
# Test all critical components
python test_critical_fixes.py

# Test LLM connection specifically
python test_openrouter_integration.py

# Run full test suite
pytest tests/ -v
```

### Manual Bot Testing
1. **Test Basic Connection**
   ```
   !llm_status
   ```
   Should show LLM connection details and model info.

2. **Test Memory System**
   ```
   # Send a DM: "Hi, I'm testing the memory system"
   # Then check memory:
   !my_memory
   ```
   Should show the conversation was stored.

3. **Test Fact Extraction**
   ```
   !extract_facts "I love pizza and work as a software engineer"
   ```
   Should extract facts about food preference and occupation.

4. **Test Image Processing** (if vision enabled)
   ```
   # Attach an image and send message
   !test_image
   ```
   Should process and describe the image.

### Performance Testing
```bash
# Monitor system resources
!system_status

# Check memory efficiency
!memory_stats

# Monitor conversation cache
!cache_stats
```

## 🚨 Troubleshooting Guide

### Common Issues & Solutions

#### 1. Bot Won't Start

**Symptoms**: Bot crashes immediately or shows import errors

**Solutions**:
```bash
# Check Python version
python --version  # Should be 3.8+

# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Check environment variables
cat .env | grep DISCORD_BOT_TOKEN

# Verify token format (should be ~70 characters)
echo "Token length: $(echo $DISCORD_BOT_TOKEN | wc -c)"
```

#### 2. Bot Can See Messages But Won't Respond

**Symptoms**: Bot shows as online but ignores messages

**Solutions**:
1. **Check Message Content Intent** (Most common issue):
   - Go to Discord Developer Portal
   - Your Application → Bot section
   - Under "Privileged Gateway Intents"
   - ✅ Enable "Message Content Intent"

2. **Check Bot Permissions**:
   - Re-invite bot with proper permissions
   - Use OAuth2 URL Generator with all required permissions
   - Test in a channel where bot has explicit permissions

3. **Check for Error Messages**:
   ```bash
   # Run in debug mode
   python basic_discord_bot.py --debug
   ```

#### 3. LLM Connection Issues

**For Local Services (LM Studio/Ollama)**:

```bash
# Verify service is running
curl http://localhost:1234/v1/models  # LM Studio
curl http://localhost:11434/v1/models # Ollama

# Check if model is loaded
# LM Studio: Check the Chat tab
# Ollama: ollama list

# Test service manually
curl -X POST http://localhost:1234/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello"}],
    "model": "local-model"
  }'
```

**For OpenRouter**:

```bash
# Test API key
curl -H "Authorization: Bearer $OPENROUTER_API_KEY" \
     https://openrouter.ai/api/v1/models

# Check account credits
# Visit openrouter.ai dashboard

# Verify model name
# Check openrouter.ai/models for exact spelling
```

#### 4. Memory/ChromaDB Issues

**Symptoms**: Memory commands fail, can't store conversations

**Solutions**:
```bash
# Check ChromaDB directory permissions
ls -la ./chromadb_data/

# Clear corrupted data (WARNING: deletes all user data)
rm -rf ./chromadb_data/

# Check disk space
df -h

# Restart with fresh database
python basic_discord_bot.py --debug
```

#### 5. Permission Errors

**Symptoms**: "Forbidden" errors when bot tries to respond

**Solutions**:
1. **Server-Level Permissions**:
   - Check server settings
   - Ensure bot role has necessary permissions
   - Bot needs to be above other roles in hierarchy

2. **Channel-Level Permissions**:
   - Check individual channel permissions
   - Bot may be restricted in specific channels
   - Test in a different channel

3. **Re-invite Bot**:
   ```bash
   # Generate new invite URL with all permissions
   # Use Discord Developer Portal OAuth2 generator
   ```

#### 6. Fact Extraction Not Working

**Symptoms**: `!extract_facts` returns no results or errors

**Solutions**:
```bash
# Test LLM connection first
!llm_status

# Check if auto-facts is enabled
!auto_facts status

# Test with simple input
!extract_facts "I like cats"

# Check debug logs
python basic_discord_bot.py --debug
```

#### 7. Image Processing Failures

**Symptoms**: Images not processed, vision commands fail

**Solutions**:
```bash
# Check vision status
!vision_status

# Verify model supports vision
# Most local models don't support vision
# Use LLaVA or cloud models with vision

# Check image format and size
# Supported: JPG, PNG, GIF, WebP, BMP
# Max size: 10MB

# Enable vision in config
LLM_SUPPORTS_VISION=true
```

### Error Recovery Procedures

#### Memory Corruption Recovery
```bash
# 1. Create backup of current data (if possible)
python -c "from backup_manager import BackupManager; BackupManager().create_backup()"

# 2. Clear corrupted ChromaDB
rm -rf ./chromadb_data/

# 3. Restart bot
python basic_discord_bot.py --debug

# 4. Restore from backup if needed
python -c "from backup_manager import BackupManager; BackupManager().restore_backup('backup_name')"
```

#### Discord Token Issues
1. Go to Discord Developer Portal
2. Regenerate bot token
3. Update `.env` file with new token
4. Restart bot

#### Complete System Reset
```bash
# 1. Backup user data
!create_backup

# 2. Stop bot
# Ctrl+C or kill process

# 3. Clear all data
rm -rf ./chromadb_data/
rm -f conversations.json
rm -f user_profiles.json
rm -f user_profiles.db

# 4. Restart fresh
python basic_discord_bot.py --debug
```

### Debugging Commands

```bash
# Enable verbose debugging
!debug on

# Check system health
!system_status

# Monitor memory usage
!memory_stats

# Check conversation cache
!cache_stats

# Test components individually
!llm_status           # LLM connection
!vision_status        # Image processing
!auto_facts status    # Fact extraction
```

### Log Analysis

**Important Log Patterns**:
```bash
# Good indicators
INFO: Bot is ready! Connected as YourBot#1234
DEBUG: Memory processing time: 1.23s
INFO: LLM connection successful

# Warning signs
WARN: Slow message processing: 4.56s
WARN: ChromaDB query took longer than expected
WARN: Cache miss rate high: 65%

# Critical issues
ERROR: LLM connection failed
ERROR: Message processing TIMEOUT
ERROR: ChromaDB connection pool exhausted
ERROR: Discord permission denied
```

## 📊 Performance Optimization

### Monitor Performance
```bash
# Check system status
!system_status

# Monitor response times
python basic_discord_bot.py --debug
# Look for timing information in logs

# Check resource usage
top -p $(pgrep -f basic_discord_bot.py)
```

### Optimization Strategies

#### For Slow Responses
1. **Increase Thread Pool Size**:
   ```env
   MEMORY_THREAD_POOL_SIZE=8
   IMAGE_THREAD_POOL_SIZE=4
   ```

2. **Use Faster Models**:
   - Switch to smaller local models
   - Use faster cloud models (GPT-4o-mini)

3. **Reduce Token Limits**:
   ```env
   LLM_MAX_TOKENS_CHAT=2048
   LLM_MAX_TOKENS_EMOTION=100
   ```

#### For Memory Issues
1. **Reduce Cache Timeout**:
   ```env
   CONVERSATION_CACHE_TIMEOUT=300  # 5 minutes
   ```

2. **Enable Aggressive Cleanup**:
   ```env
   USER_LOCK_CLEANUP_INTERVAL=900  # 15 minutes
   ```

3. **Monitor Memory Usage**:
   ```bash
   !memory_stats
   ```

#### Scaling Configuration

**Small Server (1-10 users)**:
```env
MEMORY_THREAD_POOL_SIZE=2
CONVERSATION_CACHE_TIMEOUT=1800    # 30 min
CONVERSATION_HISTORY_MAX_SIZE=500
```

**Medium Server (10-50 users)**:
```env
MEMORY_THREAD_POOL_SIZE=4          # Default
CONVERSATION_CACHE_TIMEOUT=900     # 15 min
CONVERSATION_HISTORY_MAX_SIZE=1000
```

**Large Server (50+ users)**:
```env
MEMORY_THREAD_POOL_SIZE=8
CONVERSATION_CACHE_TIMEOUT=300     # 5 min
CONVERSATION_HISTORY_MAX_SIZE=2000
CHROMADB_CONNECTION_POOL_SIZE=20
```

## 🔄 Backup & Recovery

### Automatic Backups
```bash
# Enable auto-backup on startup
BACKUP_AUTO_CREATE=true

# Manual backup
!create_backup

# List available backups
!list_backups
```

### Manual Backup & Restore
```python
from backup_manager import BackupManager

# Create backup
manager = BackupManager()
backup_name = manager.create_backup(include_metadata=True)

# List backups
backups = manager.list_backups()
print(backups)

# Restore from backup
manager.restore_backup("chromadb_backup_20241201_143022")
```

### ChatGPT History Import
```bash
# Import ChatGPT conversations
python import_chatgpt_history.py <user_id> conversations.json

# Dry run (preview what would be imported)
python import_chatgpt_history.py <user_id> conversations.json --dry-run

# Verbose output
python import_chatgpt_history.py <user_id> conversations.json --verbose
```

## 🔒 Security & Privacy

### Data Protection
- All data stored locally in ChromaDB
- User IDs are hashed for additional privacy
- No cross-user data access
- Conversation data encrypted at rest

### User Privacy Controls
- `!forget_me` - Complete data deletion
- `!auto_facts off` - Disable fact extraction
- `!list_facts` - Full data transparency
- Per-user data isolation

### API Key Security
```bash
# Good practices
export OPENROUTER_API_KEY="sk-or-v1-..."  # Environment variable
echo "OPENROUTER_API_KEY=sk-or-v1-..." >> .env  # .env file

# Bad practices - never do this
# Hard-coding keys in source code
# Committing .env files to git
# Sharing keys in chat/email
```

### Network Security
- HTTPS for all cloud API calls
- Certificate validation enabled
- Connection pooling with secure defaults
- Rate limiting to prevent abuse

## 📞 Support & Community

### Getting Help
1. **Documentation**: Check this guide and other docs/
2. **GitHub Issues**: [Repository Issues](https://github.com/whisperengine-ai/whisperengine/issues)
3. **Discord Community**: Join our support server
4. **Logs**: Always include logs when reporting issues

### Reporting Bugs
Include in your bug report:
- Operating system and Python version
- Complete error messages and logs
- Steps to reproduce the issue
- Configuration (without API keys!)
- Expected vs actual behavior

### Feature Requests
- Check existing issues first
- Describe the use case clearly
- Consider implementation complexity
- Be willing to test proposed solutions

---

## 📜 Changelog & Updates

Check the GitHub repository for:
- Release notes
- Breaking changes
- New features
- Security updates

Keep your bot updated for the best experience and security!
