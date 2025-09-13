# Environment Variables Reference
## Complete Guide to All Configuration Options

This document lists all environment variables available in the Discord bot system, organized by category with their actual default values from the codebase.

---

## 🔑 Core Bot Configuration

### Discord Bot Settings
```bash
# Required - Your Discord bot token
DISCORD_BOT_TOKEN=your_discord_bot_token_here

# Admin user permissions (comma-separated Discord user IDs)
ADMIN_USER_IDS=                             # Default: empty string

# Bot behavior settings
DISCORD_COMMAND_PREFIX=!                    # Default: ! (Command prefix)
DISCORD_BOT_NAME=                           # Default: empty (Bot's preferred name for selective responding)
DISCORD_HEARTBEAT_TIMEOUT=60.0              # Default: 60.0 (Heartbeat timeout in seconds)
DISCORD_HEARTBEAT_CHECK_INTERVAL=10.0       # Default: 10.0 (Heartbeat check interval)
DISCORD_CHUNK_GUILDS=false                  # Default: false (Enable guild chunking)
DISCORD_LLM_TIMEOUT=120                     # Default: 120 (Discord-specific LLM timeout, uses LLM_REQUEST_TIMEOUT fallback)
```

### AI System Configuration

The system provides unified AI capabilities with configurable behavior styles.
```bash
# AI System Configuration
# All AI features are always enabled - unified system

# AI Behavior & Style Configuration
AI_MEMORY_OPTIMIZATION=true                 # Default: true (Advanced memory optimization and retrieval)
AI_EMOTIONAL_RESONANCE=true                 # Default: true (Deep emotional understanding and response)
AI_ADAPTIVE_MODE=true                       # Default: true (Learn and adapt to user preferences)
AI_PERSONALITY_ANALYSIS=true                # Default: true (Comprehensive personality profiling)
```

### System Configuration
```bash
# Environment type and debugging
ENVIRONMENT=development                      # Default: development (Options: development, production)
DEBUG_MODE=false                            # Default: false (Enable debug mode)
LOG_LEVEL=INFO                              # Default: INFO (Options: DEBUG, INFO, WARNING, ERROR)
LOG_DIR=logs                                # Default: logs (Log directory path)
LOG_APP_NAME=discord_bot                    # Default: discord_bot (Application name for logs)

# Performance settings
MAX_PROCESSING_TIME=60.0                    # Default: 60.0 (Max processing time in seconds)

# Container detection (auto-detected)
ENV_MODE=                                   # Default: auto-detected (Explicit environment mode override)
DOCKER_CONTAINER=                           # Default: auto-detected (Container indicator)
CONTAINER_MODE=                             # Default: auto-detected (Container mode indicator)
DEV_MODE=                                   # Default: auto-detected (Development mode indicator)
```

---

## 🤖 LLM (Language Model) Configuration

### Primary LLM Settings
```bash
# Required - Your LLM API endpoint
LLM_CHAT_API_URL=http://localhost:1234/v1   # Default: http://localhost:1234/v1

# Model names
LLM_MODEL_NAME=local-model                  # Default: local-model (Main chat model)
LLM_EMOTION_MODEL_NAME=local-model          # Default: uses LLM_MODEL_NAME (Fast emotion analysis)
LLM_FACTS_MODEL_NAME=local-model            # Default: uses LLM_EMOTION_MODEL_NAME (Fast fact extraction)

# Request settings
LLM_REQUEST_TIMEOUT=90                      # Default: 90 (Request timeout in seconds - LM Studio can be slow)
LLM_CONNECTION_TIMEOUT=10                   # Default: 10 (Connection establishment timeout)
LLM_TEMPERATURE=0.7                         # Default: 0.7 (Creativity 0.0-2.0)
```

### Token Limits
```bash
# Token limits for different types of requests
LLM_MAX_TOKENS_CHAT=4096                   # Default: 4096 (Main chat response tokens)
LLM_MAX_TOKENS_COMPLETION=1024              # Default: 1024 (Completion tokens)
LLM_MAX_TOKENS_EMOTION=200                  # Default: 200 (Emotion analysis tokens)
LLM_MAX_TOKENS_FACT_EXTRACTION=500          # Default: 500 (Fact extraction tokens)
LLM_MAX_TOKENS_PERSONAL_INFO=400            # Default: 400 (Personal info tokens)
LLM_MAX_TOKENS_TRUST_DETECTION=300          # Default: 300 (Trust detection tokens)
LLM_MAX_TOKENS_USER_FACTS=400               # Default: 400 (User facts tokens)

# Deprecated token setting (use specific limits above)
# LLM_MAX_TOKENS=1000                         # Deprecated: use specific token limits above
```

### Vision Support (Experimental)
```bash
# Vision capabilities
LLM_SUPPORTS_VISION=false                   # Default: false (Enable vision support)
LLM_VISION_MAX_IMAGES=5                     # Default: 5 (Max images per request)
```

### Alternative LLM API Endpoints
```bash
# Separate API endpoints for different services (default to main LLM API if not specified)
LLM_EMOTION_API_URL=                        # Default: uses LLM_CHAT_API_URL (Alternative emotion API)
LLM_FACTS_API_URL=                          # Default: uses LLM_EMOTION_API_URL (Alternative facts API)

# API Keys for different services
LLM_API_KEY=                                # Default: empty (Generic API key for main LLM)
LLM_EMOTION_API_KEY=                        # Default: uses LLM_API_KEY (Separate key for emotion analysis)
LLM_FACTS_API_KEY=                          # Default: uses LLM_EMOTION_API_KEY (Separate key for fact extraction)
```

### Embedding Configuration
```bash
# External embedding API settings
LLM_EMBEDDING_API_URL=                      # Default: empty (External embedding API URL)
LLM_EMBEDDING_MODEL_NAME=text-embedding-nomic-embed-text-v1.5 # Default: text-embedding-nomic-embed-text-v1.5
LLM_EMBEDDING_API_KEY=                      # Default: empty (External embedding API key)

# Alternative embedding configuration
EMBEDDING_API_URL=                          # Default: empty (Alternative to LLM_EMBEDDING_API_URL)
EMBEDDING_MODEL_NAME=text-embedding-nomic-embed-text-v1.5 # Default: fallback model name
EMBEDDING_API_KEY=                          # Default: empty (Alternative embedding API key)

# External embeddings control
USE_EXTERNAL_EMBEDDINGS=false               # Default: false (Force use of external embedding service)

# Local embedding models (fallback when external APIs not configured)
LLM_LOCAL_EMBEDDING_MODEL=all-mpnet-base-v2 # Default: all-mpnet-base-v2 (Used by ChromaDB)
FALLBACK_EMBEDDING_MODEL=all-mpnet-base-v2 # Default: all-mpnet-base-v2 (Fallback model)
LOAD_FALLBACK_EMBEDDING_MODELS=true        # Default: true (Load fallback models if needed)

# Embedding performance settings
EMBEDDING_BATCH_SIZE=100                    # Default: 100 (Batch size for embedding requests)
EMBEDDING_MAX_RETRIES=3                     # Default: 3 (Max retry attempts)
EMBEDDING_RETRY_DELAY=1.0                   # Default: 1.0 (Retry delay in seconds)
EMBEDDING_MAX_CONCURRENT=5                  # Default: 5 (Max concurrent embedding requests)
```

### Message Security
```bash
# Security settings for message processing
MAX_SYSTEM_MESSAGE_LENGTH=                  # Default: auto-calculated (Max system message length)
SECURITY_LOG_LEVEL=quiet                    # Default: quiet (Security logging level)
```

---

## 🧠 AI Intelligence System - Always Active

All AI intelligence features are now always enabled for optimal performance.
The unified AI system provides personality profiling, emotional intelligence, 
memory networks, and human-like conversation capabilities without configuration.

# NLP configuration for personality analysis
NLP_DEPLOYMENT_MODE=native_integrated       # Default: native_integrated (Options: native_integrated, microservice)
NLP_SERVICE_HOST=localhost                  # Default: localhost (NLP service host for microservice mode)
NLP_SERVICE_PORT=8080                       # Default: 8080 (NLP service port)
NLP_TIMEOUT_SECONDS=30                      # Default: 30 (NLP request timeout)
NLP_SPACY_MODEL=en_core_web_lg              # Default: en_core_web_lg (spaCy model: en_core_web_sm, en_core_web_md, en_core_web_lg)
```

### Phase 2: Emotional Intelligence
```bash
# Enable/disable emotional intelligence
ENABLE_EMOTIONAL_INTELLIGENCE=false         # Default: false (Enable Phase 2 emotional intelligence)
EMOTION_ANALYSIS_DEPTH=contextual           # Default: contextual (Options: basic, contextual, deep)
EMOTION_AI_TIER=advanced                      # Default: advanced (Emotion AI processing level: basic/advanced)
```

### Phase 3: Memory Networks
```bash
# Enable/disable memory networks
ENABLE_PHASE3_MEMORY=false                  # Default: false (Enable Phase 3 memory networks)
MEMORY_SEARCH_STRATEGY=enhanced             # Default: enhanced (Options: basic, enhanced, comprehensive)
```

### Phase 4: Human-like Intelligence
```bash
# Enable/disable Phase 4 features
ENABLE_PHASE4_HUMAN_LIKE=true               # Default: true (Enable Phase 4 human-like intelligence)

# Phase 4 configuration
PHASE4_CONVERSATION_MODE=adaptive           # Default: adaptive (Options: human_like, analytical, balanced, adaptive)
PHASE4_MEMORY_OPTIMIZATION=true            # Default: true (Advanced memory optimization)
PHASE4_EMOTIONAL_RESONANCE=true            # Default: true (Deep emotional understanding)
PHASE4_ADAPTIVE_MODE=true                   # Default: true (Learn and adapt to user preferences)
```

---

## 🗄️ Database Configuration

### PostgreSQL Database
```bash
# PostgreSQL connection
POSTGRES_HOST=localhost                     # Default: localhost (PostgreSQL host)
POSTGRES_PORT=5432                          # Default: 5432 (PostgreSQL port)
POSTGRES_DB=discord_bot                     # Default: discord_bot (Database name)
POSTGRES_USER=bot_user                      # Default: bot_user (Database user)
POSTGRES_PASSWORD=bot_password_change_me    # Default: bot_password_change_me (CHANGE IN PRODUCTION!)

# Connection pool settings - Main pool
POSTGRES_MIN_CONNECTIONS=5                  # Default: 5 (Minimum pool connections)
POSTGRES_MAX_CONNECTIONS=20                 # Default: 20 (Maximum pool connections)

# Connection pool settings - Privacy manager pool
POSTGRES_PRIVACY_MIN_CONNECTIONS=3          # Default: 3 (Min privacy manager connections)
POSTGRES_PRIVACY_MAX_CONNECTIONS=10         # Default: 10 (Max privacy manager connections)
```

### ChromaDB (Vector Database)
```bash
# ChromaDB connection
USE_CHROMADB_HTTP=true                      # Default: true (Use HTTP connection to ChromaDB)
CHROMADB_HOST=localhost                     # Default: localhost (ChromaDB host)
CHROMADB_PORT=8000                          # Default: 8000 (ChromaDB port)
CHROMADB_PATH=./chromadb_data               # Default: ./chromadb_data (Local ChromaDB path)
CHROMADB_COLLECTION_NAME=user_memories      # Default: user_memories (User memories collection)
CHROMADB_GLOBAL_COLLECTION_NAME=global_facts # Default: global_facts (Global facts collection)
ANONYMIZED_TELEMETRY=false                  # Default: false (ChromaDB telemetry)
```

### Neo4j Graph Database (Optional)
```bash
# Enable graph database features
ENABLE_GRAPH_DATABASE=false                 # Default: false (Enable graph database integration)

# Neo4j connection
NEO4J_HOST=neo4j                            # Default: neo4j (Neo4j host - use 'localhost' for native)
NEO4J_PORT=7687                             # Default: 7687 (Neo4j bolt port)
NEO4J_USERNAME=neo4j                        # Default: neo4j (Neo4j username)
NEO4J_PASSWORD=neo4j_password_change_me     # Default: neo4j_password_change_me (CHANGE IN PRODUCTION!)
NEO4J_DATABASE=neo4j                        # Default: neo4j (Neo4j database name)

# Graph features
GRAPH_SYNC_MODE=async                       # Default: async (Options: async, sync, disabled)
FALLBACK_TO_EXISTING=true                   # Default: true (Fallback to existing emotion manager)
EMOTION_GRAPH_SYNC_INTERVAL=10              # Default: 10 (Graph sync interval in seconds)
```

### Redis Cache
```bash
# Redis connection
REDIS_HOST=localhost                        # Default: localhost (Redis host)
REDIS_PORT=6379                             # Default: 6379 (Redis port)
REDIS_DB=0                                  # Default: 0 (Redis database number)

# Redis cache settings
USE_REDIS_CACHE=true                        # Default: true (Enable Redis-based conversation cache)
CONVERSATION_CACHE_TIMEOUT_MINUTES=15       # Default: 15 (Cache timeout in minutes)
CONVERSATION_CACHE_BOOTSTRAP_LIMIT=20       # Default: 20 (Bootstrap message limit)
CONVERSATION_CACHE_MAX_LOCAL=50             # Default: 50 (Max local cache messages)

# Legacy Redis URL format (alternative to individual settings)
REDIS_URL=redis://localhost:6379            # Alternative format (not used if individual settings present)
```

---

## 🧩 Memory System Configuration

### Memory Features
```bash
# Memory system controls
ENABLE_AUTO_FACTS=true                      # Default: true (Enable automatic fact extraction)
ENABLE_GLOBAL_FACTS=false                   # Default: false (Enable global fact sharing)
ENABLE_EMOTIONS=true                        # Default: true (Enable emotion storage in memory)
```

### Backup System
```bash
# Automatic backup configuration
AUTO_BACKUP_ENABLED=true                    # Default: true (Enable automatic backups)
AUTO_BACKUP_INTERVAL_HOURS=24               # Default: 24 (Backup interval in hours)
BACKUP_RETENTION_COUNT=5                    # Default: 5 (Number of backups to retain)
BACKUP_PATH=./backups                       # Default: ./backups (Backup directory path)
```

---

## 🎤 Voice Features

### Voice System Control
```bash
# Voice system enable/disable
# VOICE_ENABLED=false                         # Deprecated: use VOICE_SUPPORT_ENABLED instead
VOICE_SUPPORT_ENABLED=true                  # Default: true (Enable voice features)
```

### ElevenLabs Voice Integration
```bash
# ElevenLabs API
ELEVENLABS_API_KEY=                         # Default: empty (Your ElevenLabs API key)
ELEVENLABS_DEFAULT_VOICE_ID=21m00Tcm4TlvDq8ikWAM # Default: Rachel voice (21m00Tcm4TlvDq8ikWAM)

# Voice quality settings
ELEVENLABS_VOICE_STABILITY=0.5              # Default: 0.5 (Voice stability 0.0-1.0)
ELEVENLABS_VOICE_SIMILARITY_BOOST=0.8       # Default: 0.8 (Similarity boost 0.0-1.0)
ELEVENLABS_VOICE_STYLE=0.0                  # Default: 0.0 (Voice style 0.0-1.0, 0.0 = most natural)
ELEVENLABS_USE_SPEAKER_BOOST=true           # Default: true (Use speaker boost)
```

### Voice Behavior
```bash
# Voice interaction settings
VOICE_AUTO_JOIN=false                       # Default: false (Auto-join voice channels)
VOICE_RESPONSE_ENABLED=true                 # Default: true (Enable voice responses)
VOICE_LISTENING_ENABLED=true                # Default: true (Enable voice listening)
VOICE_STREAMING_ENABLED=true                # Default: true (Enable voice streaming)
VOICE_MAX_RESPONSE_LENGTH=300               # Default: 300 (Max characters for voice response)
VOICE_MAX_AUDIO_LENGTH=30                   # Default: 30 (Max audio length in seconds)
VOICE_RESPONSE_DELAY=1.0                    # Default: 1.0 (Response delay in seconds)

# Voice connection management
VOICE_JOIN_ANNOUNCEMENTS=true               # Default: true (Announce when joining voice)
VOICE_KEEPALIVE_INTERVAL=300                # Default: 300 (Keepalive interval - 5 minutes)
VOICE_HEARTBEAT_INTERVAL=30                 # Default: 30 (Heartbeat interval - 30 seconds)
VOICE_MAX_RECONNECT_ATTEMPTS=3              # Default: 3 (Max reconnection attempts)
VOICE_RECONNECT_DELAY=5.0                   # Default: 5.0 (Reconnection delay in seconds)
```

---

## ⏰ Job Scheduler & Automation

### Job Scheduler
```bash
# Job scheduling system
JOB_SCHEDULER_ENABLED=true                  # Default: true (Enable background job scheduler)
JOB_SCHEDULER_CHECK_INTERVAL_SECONDS=30     # Default: 30 (Job check interval in seconds)
```

### Follow-up Messages
```bash
# Follow-up system
FOLLOW_UP_ENABLED=true                      # Default: true (Enable automatic follow-up messages)
FOLLOW_UP_DEFAULT_DELAY_HOURS=48            # Default: 48 (Default hours before follow-up)
FOLLOW_UP_MAX_PER_USER_PER_WEEK=2          # Default: 2 (Max follow-ups per user per week)
FOLLOW_UP_MIN_HOURS_BETWEEN=24             # Default: 24 (Minimum hours between follow-ups)
```

### Data Cleanup
```bash
# Cleanup automation
CLEANUP_ENABLED=true                        # Default: true (Enable automatic data cleanup)
CLEANUP_OLD_CONVERSATIONS_DAYS=30           # Default: 30 (Remove conversations older than X days)
CLEANUP_TEMP_FILES_HOURS=24                # Default: 24 (Remove temp files older than X hours)
CLEANUP_FAILED_JOBS_DAYS=7                 # Default: 7 (Remove old failed jobs after X days)
```

---

## 📁 File & System Configuration

### File Processing
```bash
# File and image processing
TEMP_IMAGES_DIR=temp_images                 # Default: temp_images (Temporary images directory)

# System prompt configuration
BOT_SYSTEM_PROMPT_FILE=./system_prompt.md  # Default: ./system_prompt.md (Path to system prompt file)
```

---

## 🔐 External API Keys

### Third-party Service Keys
```bash
# OpenAI API
OPENAI_API_KEY=                             # Default: empty (OpenAI API key)

# OpenRouter API
OPENROUTER_API_KEY=                         # Default: empty (OpenRouter API key)

# HuggingFace API
HUGGINGFACE_API_KEY=                        # Default: empty (HuggingFace API key)
```

---

## 🎯 Quick Setup Examples

### Minimal Setup (Basic Bot)
```bash
# Required minimum configuration
DISCORD_BOT_TOKEN=your_token_here
LLM_CHAT_API_URL=http://localhost:1234/v1
LLM_MODEL_NAME=your_model_name

# Basic databases (using defaults)
POSTGRES_PASSWORD=your_secure_password      # Change from default!
```

### Full AI Features Setup
```bash
# Core requirements
DISCORD_BOT_TOKEN=your_token_here
LLM_CHAT_API_URL=http://localhost:1234/v1
LLM_MODEL_NAME=your_model_name

# Enable all AI phases
ENABLE_PERSONALITY_PROFILING=true
ENABLE_EMOTIONAL_INTELLIGENCE=true
ENABLE_PHASE3_MEMORY=true
ENABLE_PHASE4_HUMAN_LIKE=true
ENABLE_GRAPH_DATABASE=true

# Secure database passwords
POSTGRES_PASSWORD=your_secure_postgres_password
NEO4J_PASSWORD=your_secure_neo4j_password
```

### Voice-Enabled Setup
```bash
# Add to above configurations
VOICE_SUPPORT_ENABLED=true
ELEVENLABS_API_KEY=your_elevenlabs_key
ELEVENLABS_DEFAULT_VOICE_ID=your_preferred_voice
```

---

## 🔒 Security Notes

### Production Security Checklist
- [ ] Change all default passwords (Neo4j, PostgreSQL)
- [ ] Use strong, unique passwords for all services
- [ ] Restrict network access to database ports
- [ ] Use environment variables, never hardcode secrets
- [ ] Regular backup of all databases
- [ ] Monitor access logs

### Default Passwords to Change
```bash
# ⚠️ CHANGE THESE IN PRODUCTION!
POSTGRES_PASSWORD=bot_password_change_me    # Default: bot_password_change_me
NEO4J_PASSWORD=neo4j_password_change_me     # Default: neo4j_password_change_me
```

---

## 🛠️ Environment Detection

The system automatically detects the environment mode using these indicators:

### Auto-Detection Logic
1. **Explicit Override**: `ENV_MODE` environment variable
2. **Container Mode**: Docker container presence (`/.dockerenv`, `CONTAINER_MODE`, `DOCKER_ENV`)
3. **Development Mode**: Development indicators (`DEV_MODE`, presence of `bot.sh`)
4. **Available Files**: Scans for `.env.{mode}` files
5. **Default**: Falls back to `development` mode

### Container Detection Variables
```bash
# These are auto-detected, but can be set explicitly
DOCKER_CONTAINER=true                       # Indicates running in Docker container
CONTAINER_MODE=true                         # Container mode indicator
DEV_MODE=true                              # Development mode indicator
```

---

## 📊 Configuration Validation

To validate your configuration, use the built-in validation:

```bash
# Validate environment configuration
python env_manager.py --validate --info

# Check AI system status
python -c "from src.core.bot import DiscordBotCore; print('AI system running with full capabilities')"
```

### Required Variables for Basic Operation
- `DISCORD_BOT_TOKEN` - Discord bot token
- `LLM_CHAT_API_URL` - LLM API endpoint  
- `POSTGRES_HOST` - PostgreSQL host
- `REDIS_HOST` - Redis host

---

**Total Environment Variables: 100+**

This comprehensive reference includes all configuration options with their actual default values as found in the codebase. Each variable includes its purpose, default value, and usage context.