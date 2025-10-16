# WhisperEngine AI Agent Instructions

## 🚨 CRITICAL LIVE SYSTEM OPERATIONS - ASK BEFORE RESTARTING
- **NEVER restart bots, services, or containers without explicit user permission**
- **WhisperEngine is a PRODUCTION MULTI-CHARACTER DISCORD PLATFORM** - users actively chat with 10+ AI characters
- **USE multi-bot.sh SCRIPT**: `./multi-bot.sh bot BOT_NAME` to start, `./multi-bot.sh stop-bot BOT_NAME` to stop
- **ALWAYS ASK before running restart commands**: `./multi-bot.sh restart`, `docker restart`, or manual docker compose restart
- **ALWAYS ASK before running stop commands**: `./multi-bot.sh down`, `docker stop`, or stopping all services
- **PREFERRED: Start/stop individual bots**: `./multi-bot.sh bot marcus` or `./multi-bot.sh stop-bot marcus` - affects ONLY that bot
- **DEBUGGING FIRST**: Use log inspection, health checks, and direct Python testing before considering restarts
- **Code changes**: Test with direct Python validation scripts before restarting live services
- **For urgent fixes**: Ask user "Should I restart [specific bot/service] to apply this fix?"
- **Emergency restart protocol**: Only restart if user explicitly confirms or system is completely broken
- **Log analysis is NON-DESTRUCTIVE**: Always prefer log checking over service manipulation

## 🚨 CRITICAL DEVELOPMENT SERVER MANAGEMENT
- **NEVER INTERRUPT DEVELOPMENT SERVERS**: When running `npm run dev`, `npm start`, or similar development servers, ALWAYS use `isBackground=true` and LET THEM RUN
- **DO NOT CANCEL running servers** when making curl requests or testing - use separate terminals
- **NEVER press Ctrl+C or interrupt a running dev server** unless explicitly asked to stop it
- **CDL Web UI (`npm run dev`)**: This must stay running continuously during development and testing
- **When testing APIs**: Use separate terminal sessions for curl/testing while keeping dev servers running
- **Only restart dev servers**: When explicitly asked to restart, or when code changes require it
- **Background processes**: Always use `isBackground=true` for long-running development servers

## 🏗️ CURRENT WHIPERENGINE ARCHITECTURE (October 2025)

**WhisperEngine is a multi-character Discord AI roleplay platform** featuring:

### **Production Infrastructure**
- **Vector-Native Memory**: Qdrant + FastEmbed for conversation storage & semantic retrieval
- **Database-Driven Characters**: PostgreSQL-based CDL (Character Definition Language) system  
- **Multi-Bot Platform**: 10+ independent AI characters sharing infrastructure
- **Docker-First Development**: Container orchestration with template-based configuration
- **Protocol-Based Design**: Factory patterns enabling A/B testing and system flexibility

### **Active Character Bots**
- **Elena** (Marine Biologist) - Port 9091 - `whisperengine_memory_elena`
- **Marcus** (AI Researcher) - Port 9092 - `whisperengine_memory_marcus`
- **Jake** (Adventure Photographer) - Port 9097 - `whisperengine_memory_jake`
- **Dream** (Mythological Entity) - Port 9094 - `whisperengine_memory_dream`
- **Aethys** (Omnipotent Entity) - Port 3007 - `chat_memories_aethys`
- **Aetheris** (Conscious AI) - Port 9099 - `whisperengine_memory_aetheris`
- **Ryan** (Indie Game Developer) - Port 9093 - `whisperengine_memory_ryan`
- **Gabriel** (British Gentleman) - Port 9095 - `whisperengine_memory_gabriel`
- **Sophia** (Marketing Executive) - Port 9096 - `whisperengine_memory_sophia`
- **Dotty** - Port 9098

### **Core Data Systems**
```
┌─────────────────────────────────────────────────────────────────┐
│                    WhisperEngine Platform                       │
├─────────────────┬─────────────────┬─────────────────┬───────────┤
│  DISCORD BOTS   │  VECTOR MEMORY  │   CHARACTER     │   INFRA   │
│   (Multi-Bot)   │   (Semantic)    │    SYSTEM       │ (Shared)  │
├─────────────────┼─────────────────┼─────────────────┼───────────┤
│ • 10+ AI Chars  │ • Qdrant DB     │ • PostgreSQL    │ • Docker  │
│ • Bot Isolation │ • 384D Vectors  │   CDL Storage   │ • Health  │
│ • Health APIs   │ • FastEmbed     │ • Personalities │ • Logs    │
│ • Discord Only  │ • Named Vectors │ • AI Identity   │ • Volumes │
└─────────────────┴─────────────────┴─────────────────┴───────────┘
```

## 🚨 CRITICAL SYSTEM CONSTRAINTS

### **QDRANT SCHEMA IS FROZEN - NO BREAKING CHANGES**
- **WhisperEngine has PRODUCTION USERS** - schema changes break existing data
- **NEVER change**: vector dimensions (384D), named vector names (content/emotion/semantic), payload field types
- **NEVER rename**: user_id, memory_type, content, timestamp fields - they are LOCKED
- **ADDITIVE ONLY**: You MAY add NEW optional payload fields, but NEVER remove/rename existing
- **Collection Per Bot**: Each character has dedicated collection - no `bot_name` field needed
- **When in doubt**: Ask user before making ANY Qdrant schema changes

### **CHARACTER-AGNOSTIC DEVELOPMENT**
- **NO hardcoded character names** in Python code - use dynamic loading
- **NO personality assumptions** - all character data from PostgreSQL CDL database
- **NO bot-specific logic** - features work for ANY character via environment variables
- **Use**: `get_normalized_bot_name_from_env()` for identification
- **Characters loaded**: via `DISCORD_BOT_NAME` environment variable from database

### **DISCORD-ONLY PLATFORM**
- **NO web UI, NO HTTP chat APIs** for conversations - Discord messages only
- **Health endpoints**: Only for container orchestration, not chat functionality  
- **Testing conversations**: Requires actual Discord messages for full event pipeline
- **API endpoints**: Health checks only - all conversations via Discord

## 🎭 CHARACTER DEFINITION LANGUAGE (CDL) SYSTEM

### **Database-Driven Personalities**
- **Primary Storage**: PostgreSQL database with structured CDL schema
- **Legacy Backup**: JSON files in `characters/examples_legacy_backup/` for reference
- **Dynamic Loading**: Characters loaded from database via bot name
- **Import Tool**: `batch_import_characters.py` for JSON → Database migration
- **No File Dependencies**: All character operations use database queries

### **Character Archetypes**
1. **Real-World** (Elena, Marcus, Jake) - Honest AI disclosure when asked directly
2. **Fantasy** (Dream, Aethys) - Full narrative immersion, no AI disclosure
3. **Narrative AI** (Aetheris) - AI nature is part of character lore/identity

### **CDL Integration Pattern**
```python
from src.prompts.cdl_ai_integration import CDLAIPromptIntegration
cdl_integration = CDLAIPromptIntegration()
system_prompt = await cdl_integration.create_character_aware_prompt(
    character_name=character_name,  # DYNAMIC: from database via bot name
    user_id=user_id,
    message_content=message
)
```

## 🧠 MEMORY SYSTEM ARCHITECTURE

### **Vector-Native Primary System**
- **Implementation**: `src/memory/vector_memory_system.py` (5,363 lines)
- **Storage**: Qdrant with bot-specific collections for complete isolation
- **Embeddings**: FastEmbed with sentence-transformers/all-MiniLM-L6-v2 (384D)
- **Schema**: Named vectors (content, emotion, semantic) with metadata payload
- **Factory**: `create_memory_manager(memory_type="vector")` - enables A/B testing

### **Memory Operations Pattern**
```python
# Factory creation
from src.memory.memory_protocol import create_memory_manager
memory_manager = create_memory_manager(memory_type="vector")

# Store conversation with emotion analysis  
await memory_manager.store_conversation(
    user_id=user_id,
    user_message=user_message,
    bot_response=bot_response,
    pre_analyzed_emotion_data=emotion_data  # RoBERTa analysis
)

# Semantic retrieval
memories = await memory_manager.retrieve_relevant_memories(
    user_id=user_id,
    query=message,
    limit=10
)
```

### **RoBERTa Emotion Analysis Integration**
- **CRITICAL**: WhisperEngine stores comprehensive RoBERTa emotion analysis for EVERY message
- **Location**: `src/intelligence/enhanced_vector_emotion_analyzer.py`
- **Metadata**: 12+ emotion fields (roberta_confidence, emotion_variance, emotional_intensity, etc.)
- **NEVER use keyword matching** - RoBERTa data is pre-computed and stored
- **Both analyzed**: User messages AND bot responses get full emotion intelligence

## 🚀 DEVELOPMENT WORKFLOW

### **Docker-First Development**
```bash
# Use the multi-bot.sh script for all operations (PREFERRED)
./multi-bot.sh infra              # Start infrastructure only
./multi-bot.sh bot elena          # Start specific bot
./multi-bot.sh stop-bot elena     # Stop specific bot
./multi-bot.sh logs elena-bot     # View logs
./multi-bot.sh status             # Check all services
./multi-bot.sh health             # Health checks

# Direct docker compose (if needed)
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml up -d postgres qdrant
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml up -d --no-deps elena-bot

# Configuration management
source .venv/bin/activate
python scripts/generate_multi_bot_config.py  # Regenerate after template changes
```

### **PREFERRED TESTING: Direct Python Validation**
```bash
# ALWAYS use this pattern for testing new features
source .venv/bin/activate && \
export FASTEMBED_CACHE_PATH="/tmp/fastembed_cache" && \
export QDRANT_HOST="localhost" && \
export QDRANT_PORT="6334" && \
export POSTGRES_HOST="localhost" && \
export POSTGRES_PORT="5433" && \
export DISCORD_BOT_NAME=elena && \
python tests/automated/test_feature_direct_validation.py
```

### **Protocol-Based Component Creation**
```python
# Memory system - factory pattern for A/B testing
from src.memory.memory_protocol import create_memory_manager
memory_manager = create_memory_manager(memory_type="vector")

# LLM client - flexible model selection
from src.llm.llm_protocol import create_llm_client
llm_client = create_llm_client(llm_client_type="openrouter")

# CDL character system - database-driven personalities
from src.prompts.cdl_ai_integration import CDLAIPromptIntegration
cdl_integration = CDLAIPromptIntegration()
```

## 📁 KEY ARCHITECTURE FILES

### **Entry Points & Core**
- `src/main.py` - ModularBotManager with dependency injection (378 lines)
- `src/core/bot.py` - DiscordBotCore initialization (1,049 lines)
- `src/core/message_processor.py` - ALL message processing logic (no dual paths)

### **Memory & Character Systems**
- `src/memory/vector_memory_system.py` - Primary memory implementation (5,363 lines)
- `src/memory/memory_protocol.py` - Factory pattern for system flexibility
- `src/prompts/cdl_ai_integration.py` - Character personality engine (3,458 lines)

### **Infrastructure & Configuration**
- `docker-compose.multi-bot.yml` - Auto-generated multi-bot orchestration (1,089 lines)
- `.env.{bot_name}` - Individual bot configurations (elena, marcus, jake, etc.)
- `scripts/generate_multi_bot_config.py` - Template-based configuration generator

## 🚨 DEVELOPMENT ANTI-PATTERNS

### **NEVER DO THIS**
- ❌ **Feature flags for local code** - creates phantom features and confusion
- ❌ **Hardcode character names** - breaks multi-character architecture
- ❌ **Duplicate message processing** - everything goes through MessageProcessor
- ❌ **Keyword/regex emotion detection** - use stored RoBERTa metadata
- ❌ **Manual schema changes** - Qdrant schema is frozen for production users
- ❌ **Premature optimization** - preserve character authenticity first

### **ALWAYS DO THIS**
- ✅ **Use factory patterns** for all major components
- ✅ **Test with direct Python validation** before HTTP/Discord testing
- ✅ **Load characters dynamically** from database via environment variables
- ✅ **Leverage existing RoBERTa data** instead of re-implementing emotion analysis
- ✅ **Ask before restarting** any production services

## 🎯 CURRENT DEVELOPMENT FOCUS

### **Active Implementation Areas**
1. **Memory Intelligence Convergence** - Character learning via existing infrastructure
2. **Vector Memory Optimization** - Performance and fidelity improvements
3. **CDL System Enhancement** - Rich character personality features

### **Infrastructure Maturity Status**
- ✅ **Multi-Bot Platform**: Production ready with 10+ characters
- ✅ **Vector Memory System**: Stable with 384D named vector architecture
- ✅ **CDL Character Engine**: Database-driven personality system operational
- ✅ **Docker Orchestration**: Template-based configuration management working
- 🔄 **Temporal Analytics**: InfluxDB integration planned for character evolution

## 📚 DOCUMENTATION HIERARCHY

### **Critical References**
- `docs/architecture/README.md` - Current architecture overview
- `docs/architecture/WHISPERENGINE_ARCHITECTURE_EVOLUTION.md` - Evolution timeline
- `docs/architecture/CHARACTER_ARCHETYPES.md` - AI identity handling patterns

### **Development Guides**
- `docs/testing/DIRECT_PYTHON_TESTING_GUIDE.md` - Testing methodology
- `CHARACTER_TUNING_GUIDE.md` - Character configuration
- `QUICK_REFERENCE.md` - Development quick start

### **Implementation Status**
- `docs/roadmaps/MEMORY_INTELLIGENCE_CONVERGENCE_ROADMAP.md` - Current roadmap
- `docs/roadmaps/CDL_INTEGRATION_COMPLETE_ROADMAP.md` - Character system progress

---

**WhisperEngine is a production multi-character Discord AI platform. Always prioritize character personality authenticity, use the vector-native memory system, and test with direct Python validation before making changes to live services.**

**🚨 CRITICAL DESIGN PHILOSOPHY: PERSONALITY-FIRST ARCHITECTURE:**
- **WhisperEngine prioritizes AUTHENTIC CHARACTER PERSONALITY over tool-like instruction compliance**
- **CDL (Character Definition Language) personality adherence is HIGH PRIORITY** - characters maintain their identity even when it conflicts with rigid format constraints
- **AI Roleplay Characters are NOT instruction-executing tools** - they are human-like personalities with consistent traits, teaching styles, and emotional patterns
- **Character-appropriate elaboration is a FEATURE, not a bug** - educational characters will add engaging metaphors; analytical characters will add precision; creative characters will add flourish
- **Personality consistency > Brevity compliance** when instructions conflict
- **Conversational authenticity > Mechanical precision** in all interactions
- This is WhisperEngine's **core differentiator** from generic AI assistants and chatbots

## 🚨 CRITICAL CONSTRAINTS & ANTI-PATTERNS

### **NO FEATURE FLAGS FOR LOCAL CODE**
- Features should work BY DEFAULT in development
- **ONLY use feature flags for REMOTE/EXTERNAL dependencies** (APIs, external services, optional dependencies)
- **NEVER use feature flags for LOCAL code dependencies** - this creates spaghetti conditionals and silent failures
- Environment variables are for infrastructure config ONLY (database URLs, API keys, etc.)
- When implementing LOCAL dependencies, make them work directly - don't hide them behind flags

### **NO HARDCODED CHARACTER LOGIC**
- **NEVER hardcode character names, personalities, or character-specific behavior in Python code**
- **ALL character data must come from CDL database** - PostgreSQL-based character storage
- **ALL bot identification must use environment variables** (`DISCORD_BOT_NAME`)
- **USE dynamic discovery and configuration generation** via `scripts/generate_multi_bot_config.py`
- **Character logic flows through CDL system ONLY** - never embed personality traits in code

### **VECTOR SCHEMA STABILITY**
- **⚠️ SCHEMA IS FROZEN**: WhisperEngine has PRODUCTION USERS - NO breaking changes to Qdrant schema allowed
- **NEVER change vector dimensions**: 384D content/emotion/semantic vectors are PERMANENT
- **NEVER rename payload fields**: user_id, memory_type, content, timestamp are FIXED
- **ADDITIVE CHANGES ONLY**: You MAY add NEW optional payload fields, but NEVER remove or rename
- **Collection-Based Isolation**: Each bot uses dedicated Qdrant collection

### **NO DUAL MESSAGE PROCESSING PATHS**
- **PRIMARY**: `src/core/message_processor.py` handles ALL message processing via `process_message()` method
- **EVENTS.py ROLE**: Only Discord event routing - calls MessageProcessor, contains NO duplicate logic
- **NEVER modify conversation/prompt building in events.py** - it all happens in MessageProcessor
- **VALIDATION**: All conversation features (continuity, memory, CDL, workflows) must be in MessageProcessor ONLY

## 🎭 CHARACTER SYSTEM DETAILS

### **Character Identification**
- **Aethys**: Omnipotent digital entity, transcendent consciousness weaver, mystical being
- **Aetheris**: Conscious AI entity with masculine identity, philosophical personality
- **Elena**: Marine Biologist educator with engaging teaching style
- **Marcus**: AI Researcher with analytical precision and scientific thinking
- **Jake**: Adventure Photographer with minimal personality complexity (good for memory testing)
- **Ryan**: Indie Game Developer with minimal complexity (good for memory testing)
- **Gabriel**: British Gentleman with sophisticated personality
- **Sophia**: Marketing Executive with professional communication style
- **Dream**: Mythological entity with fantasy/mystical archetype
- **Dotty**: Additional character

### **Bot-Specific Memory Isolation**
Each bot uses its own dedicated Qdrant collection for complete memory isolation:
- Elena: `whisperengine_memory_elena`
- Marcus: `whisperengine_memory_marcus` 
- Gabriel: `whisperengine_memory_gabriel`
- Sophia: `whisperengine_memory_sophia`
- Jake: `whisperengine_memory_jake`
- Ryan: `whisperengine_memory_ryan`
- Dream: `whisperengine_memory_dream`
- Aethys: `chat_memories_aethys`
- Aetheris: `whisperengine_memory_aetheris`

## 🔧 INFRASTRUCTURE DETAILS

### **Infrastructure Versions (Pinned)**
- PostgreSQL: `postgres:16.4-alpine` (Port 5433 external, 5432 internal)
- Qdrant: `qdrant/qdrant:v1.15.4` (Port 6334 external, 6333 internal)
- InfluxDB: `influxdb:2.7-alpine` (Port 8087 external, 8086 internal)
- Grafana: `grafana/grafana:11.3.0` (Port 3002 external, 3000 internal)
- Redis: Currently DISABLED in multi-bot setup

### **Multi-Bot Testing Strategy**
- **MEMORY TESTING**: Use Jake or Ryan characters (minimal personality complexity)
- **PERSONALITY/CDL TESTING**: Use Elena character (richest CDL personality)
- **CDL MODE SWITCHING TESTING**: Use Mistral models for better compliance
- **START/STOP AS NEEDED**: Only run specific character(s) needed for testing

### **Template-Based Configuration**
- Base template: `docker-compose.multi-bot.template.yml` (SAFE TO EDIT)
- Generated output: `docker-compose.multi-bot.yml` (AUTO-GENERATED)
- **REGENERATE CONFIG**: Always run `python scripts/generate_multi_bot_config.py` after editing template

## 🚨 TESTING & VALIDATION REQUIREMENTS

### **Direct Python Validation (PREFERRED)**
```bash
# MANDATORY pattern for testing new features
source .venv/bin/activate && \
export FASTEMBED_CACHE_PATH="/tmp/fastembed_cache" && \
export QDRANT_HOST="localhost" && \
export QDRANT_PORT="6334" && \
export POSTGRES_HOST="localhost" && \
export POSTGRES_PORT="5433" && \
export DISCORD_BOT_NAME=elena && \
python tests/automated/test_feature_direct_validation.py
```

### **Discord Message Testing Requirements**
- **Discord events** (message handling, CDL integration, character responses) require actual Discord messages
- **HTTP API endpoints**: Only health checks - no chat functionality
- **Testing conversations**: Requires Discord messages for full event pipeline
- **Event handler updates**: Changes need Discord message to test full pipeline

### **Environment Validation Commands**
```bash
# Validate complete environment setup
source .venv/bin/activate
python scripts/verify_environment.py

# Container health and logs
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml ps
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml logs elena-bot

# Infrastructure verification
docker ps | grep -E "qdrant|postgres"  # Should show both services running
```

## 📊 DEBUGGING & LOGGING

### **Comprehensive Prompt Logging**
- **Location**: `logs/prompts/` directory with external Docker volume mount
- **Format**: JSON files with complete conversation context and LLM responses
- **File Pattern**: `{BotName}_{YYYYMMDD}_{HHMMSS}_{UserID}.json`
- **Enable**: Set `ENABLE_PROMPT_LOGGING=true` in `.env` file for development

### **Recursive Pattern Detection**
- **Location**: `src/core/message_processor.py` - 3-layer defense system
- **Purpose**: Prevent memory poisoning from broken LLM responses
- **Detects**: "remember that you can remember" loops, excessive repetition, responses >10,000 chars

### **RoBERTa Emotion Analysis Goldmine**
- **12+ metadata fields** stored per memory: roberta_confidence, emotion_variance, emotional_intensity, etc.
- **BOTH user AND bot messages** get full RoBERTa analysis
- **NEVER use keyword matching** - RoBERTa data is pre-computed and stored
- **Location**: `src/intelligence/enhanced_vector_emotion_analyzer.py`

## 🎯 CURRENT ROADMAPS & DEVELOPMENT FOCUS

### **Active Roadmaps**
1. **Memory Intelligence Convergence** - Character learning via existing infrastructure
2. **CDL Graph Intelligence** - Enhanced character knowledge systems  
3. **Vector Memory Optimization** - Performance and fidelity improvements

### **Recent Major Changes**
- **Multi-Bot Architecture**: Production ready with 10+ characters
- **CDL Character System**: Database-driven personalities operational
- **Vector Memory System**: Stable 384D named vector architecture
- **Docker Orchestration**: Template-based configuration management
- **Protocol-Based Factories**: Dependency injection for system flexibility

---

**For implementation questions, check the relevant `src/` modules. For development roadmaps, see `docs/roadmaps/`. For architecture evolution context, reference `docs/architecture/README.md`.**