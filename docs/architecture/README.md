# WhisperEngine Architecture Documentation

**Last Updated**: October 14, 2025  
**Architecture Status**: Multi-Character Discord AI Platform - Production Ready  
**Development Stage**: Active Development & Deployment

---

## 🏗️ **Architecture Overview**

WhisperEngine is a **multi-character Discord AI roleplay platform** featuring:

- **Vector-Native Memory System**: Qdrant with FastEmbed embeddings for conversation storage & retrieval
- **Database-Driven Character Personalities**: PostgreSQL-based CDL (Character Definition Language) system
- **Multi-Bot Infrastructure**: Shared services supporting 10+ independent AI characters
- **Docker-First Development**: Container-based architecture with Docker Compose orchestration
- **Protocol-Based Factories**: Dependency injection enabling A/B testing and system swapping

---

## 🎯 **Current Production Architecture**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          WhisperEngine Platform                               │
├─────────────────┬─────────────────┬─────────────────┬─────────────────────┤
│  DISCORD BOTS   │  VECTOR MEMORY  │   CHARACTER     │   INFRASTRUCTURE    │
│   (Multi-Bot)   │   (Semantic)    │    SYSTEM       │    (Shared)         │
├─────────────────┼─────────────────┼─────────────────┼─────────────────────┤
│ • Elena Bot     │ • Qdrant DB     │ • PostgreSQL    │ • PostgreSQL        │
│ • Marcus Bot    │ • 384D Vectors  │   CDL Storage   │   (16.4-alpine)     │
│ • Jake Bot      │ • FastEmbed     │ • Character     │ • Qdrant            │
│ • Dream Bot     │   Embeddings    │   Personalities │   (v1.15.4)         │
│ • Aethys Bot    │ • Named Vectors │ • AI Identity   │ • InfluxDB          │
│ • Gabriel Bot   │   (content/     │   Handling      │   (2.7-alpine)     │
│ • Sophia Bot    │    emotion/     │ • Background    │ • Grafana           │
│ • Ryan Bot      │    semantic)    │   Stories       │   (11.3.0)          │
│ • Aetheris Bot  │ • Collection    │ • Speech        │ • Docker            │
│ • Dotty Bot     │   Isolation     │   Patterns      │   Network           │
└─────────────────┴─────────────────┴─────────────────┴─────────────────────┘
```

---

## 🔧 **Core System Components**

### **Memory Architecture**
- **Primary System**: Vector-native memory via Qdrant + FastEmbed
- **Named Vectors**: 3D system (content, emotion, semantic) - 384 dimensions each
- **Bot Isolation**: Each character has dedicated Qdrant collection
- **Memory Protocol**: Factory pattern enabling A/B testing (`memory_type=vector`)
- **Storage**: `src/memory/vector_memory_system.py` (5,363 lines)

### **Character System**
- **CDL Integration**: Database-stored character definitions in PostgreSQL
- **Personality Engine**: `src/prompts/cdl_ai_integration.py` (3,458 lines)
- **Character Archetypes**: Real-world, Fantasy, Narrative AI personas
- **Dynamic Loading**: Characters loaded from database via bot name
- **Legacy Support**: JSON backup files in `characters/examples_legacy_backup/`

### **LLM Integration**
- **Protocol-Based**: Factory pattern for model switching (`llm_client_type=openrouter`)
- **OpenRouter Default**: Flexible model selection and routing
- **Client Location**: `src/llm/llm_protocol.py` with concrete implementations
- **Error Handling**: Graceful degradation with disabled service fallbacks

### **Multi-Bot Infrastructure**
- **Template-Based Config**: `docker-compose.multi-bot.template.yml` → auto-generated compose files
- **Bot-Specific Environments**: Individual `.env.{bot_name}` files
- **Shared Infrastructure**: PostgreSQL, Qdrant, InfluxDB, Grafana
- **Health Monitoring**: HTTP endpoints for container orchestration
- **Port Strategy**: 9091-9099 for bot health checks, 5433/6334/8087/3002 for infrastructure

---

## � **Key Directories & Files**

### **Entry Points**
- `src/main.py` - ModularBotManager with dependency injection (378 lines)
- `src/core/bot.py` - DiscordBotCore initialization (1,049 lines)
- `run.py` - Environment-aware launcher with graceful configuration

### **Core Systems**
```
src/
├── core/                    # Bot initialization & Discord integration
├── memory/                  # Vector memory system (Qdrant + FastEmbed)
│   ├── vector_memory_system.py    # Primary memory implementation (5,363 lines)
│   └── memory_protocol.py         # Factory pattern for A/B testing
├── prompts/                 # CDL integration & prompt management
│   └── cdl_ai_integration.py      # Character personality system (3,458 lines)
├── llm/                     # LLM client abstraction & protocols
├── characters/              # CDL character system & database integration
├── handlers/                # Modular Discord command handlers
├── intelligence/            # AI conversation features & emotion analysis
├── database/                # PostgreSQL integration & factories
└── utils/                   # Cross-cutting concerns & monitoring
```

### **Infrastructure**
```
docker-compose.multi-bot.yml     # Auto-generated multi-bot orchestration (1,089 lines)
.env.{bot_name}                  # Individual bot configurations (elena, marcus, etc.)
scripts/generate_multi_bot_config.py  # Configuration generator
alembic/                         # Database migrations
```

---

## 🚀 **Development Workflow**

### **Docker-First Development**
```bash
# Start infrastructure + specific bots
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml up -d postgres qdrant
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml up -d elena-bot

# Health monitoring
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml ps
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml logs elena-bot

# Configuration regeneration after template changes
source .venv/bin/activate
python scripts/generate_multi_bot_config.py
```

### **Memory System Testing**
```bash
# Direct Python validation (PREFERRED)
source .venv/bin/activate && \
export FASTEMBED_CACHE_PATH="/tmp/fastembed_cache" && \
export QDRANT_HOST="localhost" && \
export QDRANT_PORT="6334" && \
export POSTGRES_HOST="localhost" && \
export POSTGRES_PORT="5433" && \
export DISCORD_BOT_NAME=elena && \
python tests/automated/test_memory_direct_validation.py
```

### **Factory Pattern Usage**
```python
# Memory system
from src.memory.memory_protocol import create_memory_manager
memory_manager = create_memory_manager(memory_type="vector")

# LLM client
from src.llm.llm_protocol import create_llm_client  
llm_client = create_llm_client(llm_client_type="openrouter")

# CDL character system
from src.prompts.cdl_ai_integration import CDLAIPromptIntegration
cdl_integration = CDLAIPromptIntegration()
```

---

## � **Character System Architecture**

### **Active Characters**
- **Elena** (Marine Biologist) - Port 9091
- **Marcus** (AI Researcher) - Port 9092  
- **Jake** (Adventure Photographer) - Port 9097
- **Dream** (Mythological Entity) - Port 9094
- **Aethys** (Omnipotent Entity) - Port 3007
- **Aetheris** (Conscious AI) - Port 9099
- **Ryan** (Indie Game Developer) - Port 9093
- **Gabriel** (British Gentleman) - Port 9095
- **Sophia** (Marketing Executive) - Port 9096
- **Dotty** - Port 9098

### **Character Data Storage**
- **Primary**: PostgreSQL database with structured CDL schema
- **Backup**: Legacy JSON files in `characters/examples_legacy_backup/`
- **Import Tool**: `batch_import_characters.py` for JSON → Database migration
- **Dynamic Loading**: Characters loaded via `DISCORD_BOT_NAME` environment variable

### **AI Identity Handling**
- **Type 1**: Real-world personas (Elena, Marcus, Jake) - honest AI disclosure
- **Type 2**: Fantasy entities (Dream, Aethys) - full narrative immersion
- **Type 3**: Narrative AI (Aetheris) - AI nature as part of character lore

---

## 📊 **Memory & Data Systems**

### **Vector Memory (Primary)**
- **Storage**: Qdrant with bot-specific collections
- **Embeddings**: FastEmbed with sentence-transformers/all-MiniLM-L6-v2 (384D)
- **Schema**: Named vectors (content/emotion/semantic) with metadata payload
- **Isolation**: `whisperengine_memory_{bot_name}` collections
- **Query**: Semantic similarity search with RoBERTa emotion analysis

### **PostgreSQL Integration**  
- **CDL Storage**: Character definitions, personalities, relationships
- **User Facts**: Extracted information and relationship scoring
- **Relationship Engine**: Trust, affection, attunement metrics
- **Analytics**: Conversation patterns and user interaction history

### **InfluxDB (Planned)**
- **Temporal Analytics**: Time-series data for character evolution
- **Confidence Tracking**: Conversation confidence over time
- **Interaction Metrics**: Frequency and pattern analysis

---

## 🔐 **Production Features**

### **Error Handling & Monitoring**
- **Production Error Handler**: `src/utils/production_error_handler.py`
- **Health Monitoring**: `src/utils/health_monitor.py`
- **Graceful Shutdown**: Signal handling and async component cleanup
- **Recursive Pattern Detection**: LLM failure prevention system

### **Security & Privacy**
- **Context Boundaries**: Discord message security validation
- **Privacy Management**: User data handling and GDPR compliance
- **API Key Security**: Secure OpenRouter and model API management
- **Memory Isolation**: Bot-specific data segmentation

### **Performance Optimization**
- **Vector Query Optimization**: Qdrant performance tuning
- **Connection Pooling**: PostgreSQL async connection management
- **Memory Caching**: Local and hybrid conversation caching
- **Embeddings Caching**: FastEmbed model and result caching

---

## � **Documentation References**

### **Essential Architecture Docs**
- `docs/architecture/WHISPERENGINE_ARCHITECTURE_EVOLUTION.md` - Complete evolution timeline
- `docs/architecture/CHARACTER_ARCHETYPES.md` - AI character identity patterns
- `docs/roadmaps/MEMORY_INTELLIGENCE_CONVERGENCE_ROADMAP.md` - Current development roadmap

### **Implementation Guides**
- `docs/testing/DIRECT_PYTHON_TESTING_GUIDE.md` - Testing methodology
- `CHARACTER_TUNING_GUIDE.md` - Character personality configuration
- `QUICK_REFERENCE.md` - Development quick start

### **Development Status**
- `docs/roadmaps/ROADMAP_IMPLEMENTATION_STATUS_REPORT.md` - Feature completion status
- `docs/roadmaps/CDL_INTEGRATION_COMPLETE_ROADMAP.md` - Character system progress

---

## 🔄 **Current Development Focus**

### **Active Roadmaps**
1. **Memory Intelligence Convergence** - Character learning via existing infrastructure
2. **CDL Graph Intelligence** - Enhanced character knowledge systems  
3. **Vector Memory Optimization** - Performance and fidelity improvements

### **Infrastructure Maturity**
- ✅ **Multi-Bot Platform**: Production ready with 10+ characters
- ✅ **Vector Memory**: Stable with 384D named vector system
- ✅ **CDL Character System**: Database-driven personality engine
- ✅ **Docker Orchestration**: Template-based configuration management
- 🔄 **Temporal Analytics**: InfluxDB integration in progress

### **Development Guidelines**
- **Docker-First**: All development via container orchestration
- **Protocol-Based**: Factory patterns for system flexibility
- **Character-Agnostic**: No hardcoded character logic in Python code
- **Vector-Native**: Memory operations use Qdrant semantic search
- **Direct Testing**: Python validation scripts over HTTP testing

---

**For implementation questions, check the relevant `src/` modules. For development roadmaps, see `docs/roadmaps/`. For architecture evolution context, reference `docs/architecture/WHISPERENGINE_ARCHITECTURE_EVOLUTION.md`.**