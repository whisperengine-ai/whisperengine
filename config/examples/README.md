# WhisperEngine Environment Configuration Guide

## 📁 Configuration Structure

WhisperEngine now uses **focused, use-case-specific** environment configuration files instead of one massive 824-line example. Each file is optimized for its specific deployment scenario.

## 🚀 Quick Start (Most Users)

**File**: `config/examples/.env.quick-start.example` (50 lines)
**Purpose**: Get up and running in 5 minutes
**Features**: Discord bot + LLM + basic memory

```bash
# Copy and configure
cp config/examples/.env.quick-start.example .env
# Edit your Discord token and LLM API key
# Run the bot
./bot.sh start dev
```

## 🛠️ Development Environment

**File**: `config/examples/.env.development.example` (180+ lines)
**Purpose**: Full development with debugging, hot-reload, and all features
**Features**: All systems enabled, debug logging, performance monitoring

```bash
# Copy development config
cp config/examples/.env.development.example .env
# Start development environment
./bot.sh start dev
```

## 🏭 Production Deployment

**File**: `config/examples/.env.production.example` (150+ lines)
**Purpose**: Production-ready with security, monitoring, and optimization
**Features**: Security hardened, performance optimized, backup enabled

```bash
# Copy production config
cp config/examples/.env.production.example .env
# Review security settings and secrets
# Deploy to production
./bot.sh start
```

## 🏠 Local AI (Privacy Focused)

**File**: `config/examples/.env.local-ai.example` (120+ lines)
**Purpose**: 100% local AI processing, no external API calls
**Features**: Local LLM (LM Studio/Ollama), local embeddings, maximum privacy

```bash
# Install LM Studio or Ollama first
# Copy local AI config
cp config/examples/.env.local-ai.example .env
# Start local AI setup
./bot.sh start dev
```

## 🏢 Enterprise Features

**File**: `config/examples/.env.enterprise.example` (200+ lines)
**Purpose**: Full enterprise features and advanced AI systems
**Features**: Multi-entity relationships, advanced analytics, enterprise security

```bash
# Copy enterprise config
cp config/examples/.env.enterprise.example .env
# Configure enterprise infrastructure
# Deploy with enterprise features
./bot.sh start
```

## 🎯 Which Configuration Should I Use?

| Use Case | Configuration File | Description |
|----------|-------------------|-------------|
| **First time user** | `.env.quick-start.example` | Just want to try WhisperEngine |
| **Developer** | `.env.development.example` | Building features, debugging |
| **Production deploy** | `.env.production.example` | Running for real users |
| **Privacy focused** | `.env.local-ai.example` | No external AI APIs |
| **Enterprise user** | `.env.enterprise.example` | Advanced features, compliance |

## 🔧 Common Configuration Patterns

### LLM Provider Options

Each config includes multiple LLM provider options:

```bash
# Local (Free, Private)
LLM_CHAT_API_URL=http://localhost:1234/v1
LLM_CHAT_API_KEY=not-needed
LLM_CHAT_MODEL=local-model

# OpenRouter (Easy, Multiple Models)
LLM_CHAT_API_URL=https://openrouter.ai/api/v1
LLM_CHAT_API_KEY=your_key_here
LLM_CHAT_MODEL=openai/gpt-4o-mini

# OpenAI Direct (Premium)
LLM_CHAT_API_URL=https://api.openai.com/v1
LLM_CHAT_API_KEY=your_key_here
LLM_CHAT_MODEL=gpt-4o-mini
```

### Character System (CDL)

All configs use the new **Character Definition Language** (CDL):

```bash
# Default assistant
CDL_DEFAULT_CHARACTER=characters/default_assistant.json

# Popular options
CDL_DEFAULT_CHARACTER=characters/dream_of_the_endless.json
CDL_DEFAULT_CHARACTER=characters/examples/elena-rodriguez.json
CDL_DEFAULT_CHARACTER=characters/examples/marcus-chen.json
```

### Memory System (Vector-Native)

All configs use the **vector-native memory system**:

```bash
MEMORY_SYSTEM_TYPE=vector
VECTOR_QDRANT_HOST=qdrant
VECTOR_QDRANT_PORT=6333
VECTOR_QDRANT_COLLECTION=whisperengine_memory
VECTOR_EMBEDDING_MODEL=snowflake/snowflake-arctic-embed-xs
```

## 📚 Validation Against Codebase

All environment variables in these configs have been **cross-referenced with the actual codebase** to ensure:

✅ **Variables are actually used** - No dead configuration  
✅ **Defaults are accurate** - Matches code fallback values  
✅ **Required variables included** - Won't fail to start  
✅ **Optional variables documented** - Clear what's needed vs nice-to-have

## 🔄 Migration from Old .env.example

If you were using the old 824-line `.env.example`:

1. **Identify your use case** from the table above
2. **Copy the appropriate new config file** to `.env`
3. **Transfer your secrets** (Discord token, API keys, etc.)
4. **Remove old `.env.example`** - it's been replaced

## 🎉 Benefits of New Structure

- **⚡ Faster setup** - 50 lines vs 824 lines for basic setup
- **🎯 Focused configs** - Only what you need for your use case  
- **✅ Validated** - All variables confirmed against actual code
- **📖 Self-documenting** - Clear comments and examples
- **🔧 Maintainable** - Easy to update and extend

---

**Ready to get started?** Choose your configuration file and follow the setup steps above!