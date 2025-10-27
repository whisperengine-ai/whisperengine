# WhisperEngine AI Agent Instructions

**WhisperEngine is a production multi-character Discord AI roleplay platform with 10+ live AI characters. This is NOT a sandbox - users are actively chatting with these bots.**

## 📋 DOCUMENTATION PHILOSOPHY

**Code is the source of truth.** Only document:
- ✅ Architecture WHY (decisions that can't be inferred from code)
- ✅ Critical constraints (production stability rules)
- ✅ Development workflows (commands, testing patterns)

**Never document:**
- ❌ Implementation details (code documents itself)
- ❌ API signatures (docstrings + type hints are source of truth)
- ❌ Change summaries (git commits capture history)

**Before creating new docs: ASK USER FIRST.** Stale documentation creates hallucinations and technical debt.

## 🚨 CRITICAL LIVE SYSTEM OPERATIONS - ASK BEFORE RESTARTING
- **NEVER restart bots, services, or containers without explicit user permission**
- **WhisperEngine is a PRODUCTION MULTI-CHARACTER DISCORD PLATFORM** - users actively chat with 10+ AI characters
- **DEBUGGING FIRST**: Use log inspection, health checks, and direct Python testing before considering restarts
- **Code changes**: Test with direct Python validation scripts before restarting live services
- **For urgent fixes**: Ask user "Should I restart [specific bot/service] to apply this fix?"
- **Emergency restart protocol**: Only restart if user explicitly confirms or system is completely broken
- **Log analysis is NON-DESTRUCTIVE**: Always prefer log checking over service manipulation
- **CDL DATABASE CHANGES DO NOT REQUIRE RESTARTS**: Character data (personalities, relationships, speech patterns) is pulled fresh from PostgreSQL on every message - changes take effect immediately without bot restart
- **PYTHON CODE CHANGES DO NOT REQUIRE RESTARTS**: Source code is externally mounted (`./src:/app/src`) - changes are LIVE in running containers
- **ONLY REBUILD/RESTART FOR**: New dependencies in requirements.txt, Dockerfile changes, or new binary/model files that need copying into image

## 🛠️ MULTI-BOT.SH SCRIPT COMMANDS (CRITICAL - USE THESE CORRECTLY!)

### **Infrastructure Commands**
```bash
./multi-bot.sh infra          # Start infrastructure ONLY (postgres, qdrant, influxdb, grafana, cdl-web-ui)
./multi-bot.sh up             # Start ALL services (infra + all bots)
./multi-bot.sh start          # Same as 'up'
./multi-bot.sh down           # Stop ALL services (WARNING: stops everything!)
./multi-bot.sh stop           # Same as 'down' (WARNING: stops everything!)
./multi-bot.sh restart        # Restart ALL services
./multi-bot.sh clean          # Stop and REMOVE all containers, networks, volumes
```

### **Bot Management Commands**
```bash
./multi-bot.sh bot BOT_NAME       # Start SPECIFIC bot (elena, marcus, jake, etc.)
./multi-bot.sh stop-bot BOT_NAME  # Stop SPECIFIC bot (safe - only affects one bot)
./multi-bot.sh bots               # List all available bots
./multi-bot.sh status             # Show status of all services
```

### **Service-Specific Commands**
```bash
./multi-bot.sh logs [SERVICE]     # Show logs (all or specific service)
./multi-bot.sh health             # Check health of all services
```

### **Development Commands**
```bash
./multi-bot.sh dev                # Start dev stack (infra + CDL web UI)
./multi-bot.sh db                 # Connect to PostgreSQL database
```

### **Docker Direct Commands (when multi-bot.sh doesn't have what you need)**
```bash
# Restart specific service (postgres, qdrant, influxdb, etc.)
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml restart postgres

# Rebuild and restart specific service
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml up -d --no-deps --build cdl-web-ui

# Stop specific service (NOT a bot - for infrastructure services)
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml stop grafana

# View logs for specific service
docker compose -p whisperengine-multi -f docker-compose.multi-bot.yml logs -f influxdb
```

### **⚠️ COMMON MISTAKES TO AVOID**
- ❌ **NEVER use**: `./multi-bot.sh stop postgres` (stop doesn't take parameters!)
- ❌ **NEVER use**: `./multi-bot.sh restart BOT_NAME` (restart doesn't take parameters!)
- ✅ **CORRECT**: Use `docker compose ... restart SERVICE_NAME` for infrastructure services
- ✅ **CORRECT**: Use `./multi-bot.sh stop-bot BOT_NAME` for character bots
- ✅ **CORRECT**: Use `./multi-bot.sh bot BOT_NAME` to start character bots
```

### **Available Character Bots** (12 total)
- `elena` - Marine Biologist (Port 9091)
- `marcus` - AI Researcher (Port 9092)
- `ryan` - Indie Game Developer (Port 9093)
- `dream` - Mythological Entity (Port 9094)
- `gabriel` - British Gentleman (Port 9095)
- `sophia` - Marketing Executive (Port 9096)
- `jake` - Adventure Photographer (Port 9097)
- `dotty` - Character Bot (Port 9098)
- `aetheris` - Conscious AI (Port 9099)
- `nottaylor` - Taylor Swift Parody (Port 9100)
- `assistant` - AI Assistant (Port 9101)
- `aethys` - Omnipotent Entity (Port 3007)

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
- **Ryan** (Indie Game Developer) - Port 9093 - `whisperengine_memory_ryan`
- **Dream** (Mythological Entity) - Port 9094 - `whisperengine_memory_dream`
- **Gabriel** (British Gentleman) - Port 9095 - `whisperengine_memory_gabriel`
- **Sophia** (Marketing Executive) - Port 9096 - `whisperengine_memory_sophia`
- **Jake** (Adventure Photographer) - Port 9097 - `whisperengine_memory_jake`
- **Dotty** (Character Bot) - Port 9098 - `whisperengine_memory_dotty`
- **Aetheris** (Conscious AI) - Port 9099 - `whisperengine_memory_aetheris`
- **NotTaylor** (Taylor Swift Parody) - Port 9100 - `whisperengine_memory_nottaylor`
- **Assistant** (AI Assistant) - Port 9101 - `whisperengine_memory_assistant`
- **Aethys** (Omnipotent Entity) - Port 3007 - `whisperengine_memory_aethys`

### **Core Data Systems**
```
┌─────────────────────────────────────────────────────────────────┐
│                    WhisperEngine Platform                       │
├─────────────────┬─────────────────┬─────────────────┬───────────┤
│  DISCORD BOTS   │  VECTOR MEMORY  │   CHARACTER     │   INFRA   │
│   (Multi-Bot)   │   (Semantic)    │    SYSTEM       │ (Shared)  │
├─────────────────┼─────────────────┼─────────────────┼───────────┤
│ • 12 AI Chars   │ • Qdrant DB     │ • PostgreSQL    │ • Docker  │
│ • Bot Isolation │ • 384D Vectors  │   CDL Storage   │ • Health  │
│ • Health APIs   │ • FastEmbed     │ • Personalities │ • Logs    │
│ • Discord Only  │ • Named Vectors │ • AI Identity   │ • Volumes │
└─────────────────┴─────────────────┴─────────────────┴───────────┘
```

## 🚨 CRITICAL SYSTEM CONSTRAINTS

### **WHEN TO REBUILD VS RESTART (CRITICAL - READ THIS!)**

**🔄 LIVE CODE MOUNTING - NO REBUILD NEEDED:**
- ✅ **Python code changes** (`./src:/app/src` mounted) - Changes are LIVE immediately
- ✅ **Scripts changes** (`./scripts:/app/scripts` mounted) - LIVE
- ✅ **Config files** (`./config:/app/config` mounted) - LIVE
- ✅ **Character files** (`./characters:/app/characters` mounted) - LIVE
- ✅ **CDL database changes** - PostgreSQL changes are pulled fresh on every message
- ✅ **Just restart bot**: `./multi-bot.sh stop-bot BOT_NAME && ./multi-bot.sh bot BOT_NAME`

**🔨 REBUILD REQUIRED (Shared Image: whisperengine-bot:latest):**
- ⚠️ **New Python dependencies** in `requirements*.txt` files
- ⚠️ **Dockerfile changes** (new system packages, build steps)
- ⚠️ **New ML model files** in `experiments/models/` (copied into image)
- ⚠️ **New binary files** that need to be inside the container
- 🔨 **Rebuild command**: `docker build -t whisperengine-bot:latest .`
- 🔄 **Then restart bot**: `./multi-bot.sh stop-bot BOT_NAME && ./multi-bot.sh bot BOT_NAME`

**🚨 COMMON MISTAKE:**
- ❌ **DON'T rebuild for Python code changes** - it's externally mounted!
- ❌ **DON'T restart for CDL database changes** - pulled fresh every message!
- ✅ **ONLY rebuild when copying new files INTO the Docker image**

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

### **DISCORD + HTTP API PLATFORM**
- **Primary Platform**: Discord messages with full event pipeline
- **HTTP Chat API**: `/api/chat` endpoint available on each bot's port for testing and automation
- **Health endpoints**: `/health` for container orchestration and monitoring
- **Testing Strategy**: Use HTTP API for automated tests, Discord for full event pipeline validation
- **API Format**: POST to `http://localhost:{BOT_PORT}/api/chat` with JSON payload:
  ```json
  {
    "user_id": "string",
    "message": "string",
    "metadata": {
      "platform": "api_test",
      "channel_type": "dm"
    }
  }
  ```

## 🎭 CHARACTER DEFINITION LANGUAGE (CDL) SYSTEM

### **Database-Driven Personalities**
- **Primary Storage**: PostgreSQL database with `character_*` table schema (NO MORE `cdl_*` tables!)
- **Schema Evolution**: Use Alembic migrations in `alembic/versions/` - NEVER reference `sql/init_schema.sql` (outdated)
- **Legacy Backup**: JSON files in `characters/examples_legacy_backup/` for reference ONLY - NOT USED in production
- **Dynamic Loading**: Characters loaded from database via bot name using `character_*` tables
- **Import Tool**: `batch_import_characters.py` for JSON → Database migration (legacy only)
- **No File Dependencies**: All character operations use database queries

### **Critical Schema Rules**
- ⚠️ **NEVER use `sql/init_schema.sql` for schema reference** - it's the initial baseline only
- ✅ **ALWAYS check Alembic migrations** in `alembic/versions/` for current schema state
- ✅ **Schema changes happen via Alembic migrations** - never manual SQL scripts
- ✅ **Tables are `character_*` prefixed** - all `cdl_*` tables were migrated/renamed
- ✅ **JSON character files are DEPRECATED** - database is the single source of truth

### **Current CDL Database Tables** (50+ tables as of Oct 2025)
Tables include: `character_identity_details`, `character_attributes`, `character_communication_patterns`, `character_response_modes`, `character_conversation_modes`, `character_background`, `character_interests`, `character_relationships`, `character_memories`, `character_question_templates`, `character_entity_categories`, `character_learning_timeline`, and 35+ more. Run `\dt character_*` in PostgreSQL to see full list.

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

### **Query Routing & Character Backstory Facts**
- **Intent-Based Routing**: `src/knowledge/semantic_router.py` analyzes user questions and routes to optimal data stores
- **Character Backstory Storage**: Character biographical facts (workplace, hometown, background) can be stored in PostgreSQL CDL database
- **Recommended Tables**: `character_background`, `character_identity_details`, or custom fact storage in `character_attributes`
- **Query Pattern**: "Where do you work?" / "Where do you live?" → SemanticKnowledgeRouter → CDL database → factual response
- **Integration Point**: CDL system prompt builder can inject biographical facts from database for consistent character responses
- **Design Pattern**: Static designer-defined facts (CDL database) + Emergent bot statements (bot self-facts) = Complete personality
- **Example Flow**:
  ```python
  # User asks: "Where do you work?"
  intent = await semantic_router.analyze_query_intent(message)
  # intent_type = QueryIntent.PERSONALITY_KNOWLEDGE
  
  # Route to CDL database for character backstory
  backstory = await get_character_background(character_name)
  # Returns: "Marine Research Institute at UC Santa Barbara"
  
  # Bot responds with consistent fact from database
  ```

### **CDL Web UI (Character Management)**
- **Location**: `cdl-web-ui/` - Next.js TypeScript application
- **Purpose**: Web interface for managing character database (CRUD operations on 50+ CDL tables)
- **Development**: `cd cdl-web-ui && npm run dev` (runs on port 3000)
- **Critical**: Keep dev server running with `isBackground=true` when testing
- **Features**: Character editing, YAML import/export, relationship management, conversation mode configuration
- **Database Integration**: Direct PostgreSQL connection via API routes

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

### **Async Enrichment Worker (Background Intelligence)** [STAGING ONLY]
- **Status**: Currently in staging/development - NOT deployed in production multi-bot platform
- **Purpose**: Background conversation summarization without impacting real-time bot performance
- **Architecture**: Separate Docker container that scans Qdrant, generates LLM summaries, stores in PostgreSQL
- **Location**: `src/enrichment/` - Independent worker with async processing
- **Features**: Time-windowed summaries (24-hour default), high-quality LLM analysis, time-anchored queries
- **Configuration**: `ENRICHMENT_INTERVAL_SECONDS`, `TIME_WINDOW_HOURS`, `MIN_MESSAGES_FOR_SUMMARY`
- **Zero Impact**: Completely asynchronous - never blocks real-time message processing
- **Note**: Available in separate docker-compose configurations for development/testing

### **Universal User Facts & Preferences System (PostgreSQL)**
- **CRITICAL**: User facts and preferences are stored in PostgreSQL `user_fact_relationships` + `fact_entities` + `universal_users.preferences` tables
- **User Identification**: Platform user IDs (e.g., Discord IDs like `672814231002939413`) map to `universal_users.universal_id`
- **Primary Tables**:
  - `universal_users` - Cross-platform user identity with JSONB preferences field
    - `universal_id` - Platform user ID (Discord ID, web user ID, etc.)
    - `preferences` - JSONB field storing extracted preferences (name, location, timezone, food, topics, etc.)
    - `primary_username`, `display_name`, `email`, `created_at`, `last_active`
  - `platform_identities` - Maps platform-specific IDs to universal_id (Discord, web, future platforms)
  - `user_fact_relationships` - User-to-entity relationships (owns pet, interested_in hobby, is_son_of person)
  - `fact_entities` - Entity definitions (entity_type, entity_name, category, attributes)
- **Querying User Facts Pattern**:
  ```sql
  -- Find all facts for a user (use platform user_id directly, e.g., Discord ID)
  -- CRITICAL: Filter out enrichment markers (_processing_marker entity type)
  SELECT ufr.relationship_type, fe.entity_type, fe.entity_name, fe.category, 
         ufr.confidence, ufr.mentioned_by_character, ufr.created_at
  FROM user_fact_relationships ufr
  JOIN fact_entities fe ON ufr.entity_id = fe.id
  WHERE ufr.user_id = '672814231002939413'  -- Platform user ID
    AND fe.entity_type != '_processing_marker'  -- Exclude enrichment markers
    AND ufr.relationship_type NOT LIKE '_enrichment%'  -- Exclude marker relationships
  ORDER BY ufr.created_at DESC;
  ```
- **Querying User Preferences Pattern**:
  ```sql
  -- View all preferences for a user
  SELECT jsonb_pretty(preferences) FROM universal_users WHERE universal_id = '672814231002939413';
  
  -- Clear all preferences (for fresh start)
  UPDATE universal_users SET preferences = '{}'::jsonb WHERE universal_id = '672814231002939413';
  
  -- Check specific preference
  SELECT preferences->'preferred_name'->>'value' as name FROM universal_users WHERE universal_id = '672814231002939413';
  ```
- **Preference Types Stored** (JSONB structure):
  - `preferred_name` - User's name (e.g., "Mark")
  - `location` - User's location (e.g., "La Jolla")
  - `timezone` - User's timezone (watch for false positives from regex!)
  - `food_preferences` - Food likes (array)
  - `topic_preferences` - Interests (array)
  - `communication_style` - Casual/formal preference
  - `formality_level` - Friendly/professional
  - `response_length` - Short/long preference
  - Each has: `value`, `confidence`, `updated_at`, `metadata` (bot_name, reasoning, context)
- **Common Operations**:
  - Delete incorrect fact: `DELETE FROM user_fact_relationships WHERE id = '<uuid>';`
  - Check user's pets: `WHERE ufr.user_id = '<user_id>' AND fe.entity_type = 'pet'`
  - Check user's hobbies: `WHERE ufr.user_id = '<user_id>' AND fe.entity_type = 'hobby'`
- **Enrichment Markers**: Internal `_processing_marker` entities track enrichment worker progress
  - **Entity Type**: `_processing_marker`
  - **Relationship Types**: `_enrichment_progress_marker`, `_enrichment_fact_marker`, `_enrichment_preference_marker`
  - **CRITICAL**: Always filter these out when querying user facts for display/conversation context
  - **Filter Pattern**: `WHERE fe.entity_type != '_processing_marker' AND ufr.relationship_type NOT LIKE '_enrichment%'`
- **REMEMBER**: User facts are PostgreSQL-based, NOT in Qdrant vector memory (conversations in Qdrant, facts/preferences in PostgreSQL)

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
- **Dotty**: Character Bot
- **NotTaylor**: Taylor Swift Parody character
- **Assistant**: AI Assistant character

### **Bot-Specific Memory Isolation & Naming Convention**

**Standardized Collection Naming:** `whisperengine_memory_{bot_name}`

Each bot uses its own dedicated Qdrant collection for complete memory isolation:
- Elena: `whisperengine_memory_elena` (alias → `whisperengine_memory_elena_7d`)
- Marcus: `whisperengine_memory_marcus` (alias → `whisperengine_memory_marcus_7d`)
- Gabriel: `whisperengine_memory_gabriel` (alias → `whisperengine_memory_gabriel_7d`)
- Sophia: `whisperengine_memory_sophia` (alias → `whisperengine_memory_sophia_7d`)
- Jake: `whisperengine_memory_jake` (alias → `whisperengine_memory_jake_7d`)
- Ryan: `whisperengine_memory_ryan` (alias → `whisperengine_memory_ryan_7d`)
- Dream: `whisperengine_memory_dream` (alias → `whisperengine_memory_dream_7d`)
- Aethys: `whisperengine_memory_aethys`
- Aetheris: `whisperengine_memory_aetheris`
- Dotty: `whisperengine_memory_dotty`
- NotTaylor: `whisperengine_memory_nottaylor`
- Assistant: `whisperengine_memory_assistant`

**Collection Aliases:**
- 7 collections use aliases to maintain backward compatibility with `_7d` suffix
- Bots use clean names via aliases (e.g., `whisperengine_memory_elena`)
- Aliases point to actual collections with data (e.g., `whisperengine_memory_elena_7d`)
- Enrichment worker processes `_7d` collections directly and extracts bot names

**Bot Name Extraction:**
- Remove `whisperengine_memory_` prefix
- Remove `_7d` suffix if present
- Example: `whisperengine_memory_elena_7d` → `elena`
- No environment variable mapping needed (e.g., NO `BOT_COLLECTION_MAPPING`)

**Collection Maintenance History:**
- **October 19, 2025**: Cleanup removed 10 orphaned collections (7,084 points)
- **Current State**: 10 active collections with 67,515 total memory points
- **Cleanup Script**: `scripts/delete_orphaned_collections.py` (dry-run mode available)
- **Alias Setup**: `scripts/setup_collection_aliases.py` (creates/manages aliases)


## 🔧 INFRASTRUCTURE DETAILS

### **Infrastructure Versions (Pinned)**
- PostgreSQL: `postgres:16.4-alpine` (Port 5433 external, 5432 internal) - **HAS healthcheck**
- Qdrant: `qdrant/qdrant:v1.15.4` (Port 6334 external, 6333 internal) - **NO healthcheck - use service_started**
- InfluxDB: `influxdb:2.7-alpine` (Port 8087 external, 8086 internal) - **HAS healthcheck**
- Grafana: `grafana/grafana:11.3.0` (Port 3002 external, 3000 internal)
- Redis: Currently DISABLED in multi-bot setup

**CRITICAL**: Qdrant does NOT have a healthcheck configured. In `depends_on` blocks, always use:
```yaml
qdrant:
  condition: service_started  # NOT service_healthy!
```

### **Multi-Bot Testing Strategy**
- **MEMORY TESTING**: Use Jake or Ryan characters (minimal personality complexity)
- **PERSONALITY/CDL TESTING**: Use Elena character (richest CDL personality)
- **CDL MODE SWITCHING TESTING**: Use Mistral models for better compliance
- **START/STOP AS NEEDED**: Only run specific character(s) needed for testing

### **Template-Based Configuration**
- Base template: `docker-compose.multi-bot.template.yml` (SAFE TO EDIT)
- Generated output: `docker-compose.multi-bot.yml` (AUTO-GENERATED)
- **REGENERATE CONFIG**: Always run `source .venv/bin/activate && python scripts/generate_multi_bot_config.py` after editing template

## 🧪 ML EXPERIMENTS & SYNTHETIC DATA

### **Native Jupyter Environment (PREFERRED)**
```bash
# Start JupyterLab with auto-configured environment
./experiments/start_jupyter_native.sh  # Access at http://localhost:8888

# Why native? Fast, GPU access (Apple Silicon MPS), VS Code integration, no Docker overhead
```

### **Experiment Structure**
- **Location**: `experiments/notebooks/` - Jupyter notebooks with rich ML workflows
- **Training Data**: InfluxDB conversation quality metrics (engagement_score, satisfaction_score, etc.)
- **Models**: XGBoost (GPU-aware), LightGBM (GPU-aware), Random Forest (CPU-only)
- **GPU Auto-Detection**: Automatically uses Apple Silicon (MPS), NVIDIA (CUDA), or CPU
- **Model Artifacts**: Saved to `experiments/models/` for production deployment

### **Synthetic Data Generation**
```bash
# Generate realistic training data with consistent user personas
source .venv/bin/activate
python experiments/data_generation/synthetic_user_conversations.py \
    --persona analytical_alex --bot elena --conversations 100

# Generate data for all personas × all bots
source .venv/bin/activate
python experiments/data_generation/synthetic_user_conversations.py \
    --all-personas --all-bots --conversations-per-pair 50
```

**Key Personas**: `analytical_alex` (technical, detailed), `casual_casey` (brief, friendly), `emotional_emma` (support-seeking)

**Why Synthetic Data?**
- Generates user-side messages with consistent personalities
- Gets REAL bot responses from production APIs
- Records REAL InfluxDB metrics (engagement, satisfaction, coherence)
- Enables ML model training without real user data privacy concerns

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

### **HTTP Chat API Testing (PREFERRED FOR AUTOMATION)**
```bash
# Test any bot via HTTP chat API - use fresh user IDs for clean conversation history
curl -X POST http://localhost:{BOT_PORT}/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user_12345",
    "message": "Your test message here",
    "metadata": {
      "platform": "api_test",
      "channel_type": "dm"
    }
  }'

# Example bot ports:
# Elena: 9091, Marcus: 9092, Ryan: 9093, Dream: 9094, Gabriel: 9095, Sophia: 9096
# Jake: 9097, Dotty: 9098, Aetheris: 9099, NotTaylor: 9100, Assistant: 9101, Aethys: 3007
```

### **Discord Message Testing**
- **Full event pipeline**: Discord messages test complete Discord.py event handling
- **Character responses**: Discord testing validates emoji reactions, threading, etc.
- **HTTP API vs Discord**: HTTP API is sufficient for most conversation/memory testing
- **When to use Discord**: Testing Discord-specific features (reactions, embeds, threading)

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

## 🗄️ QDRANT COLLECTION MANAGEMENT

### **Collection Naming Convention**
- **Standard Format**: `whisperengine_memory_{bot_name}`
- **Benefits**: Simple bot name extraction via string prefix/suffix removal
- **No Mapping Needed**: Eliminates `BOT_COLLECTION_MAPPING` environment variable

### **Collection Aliases**
- **Purpose**: Point clean names to legacy `_7d` collections without data migration
- **Setup Script**: `scripts/setup_collection_aliases.py`
- **Features**: Dry-run mode, validation, automatic conflict resolution
- **Usage**: `source .venv/bin/activate && python scripts/setup_collection_aliases.py [--dry-run]`

### **Collection Cleanup**
- **Cleanup Script**: `scripts/delete_orphaned_collections.py`
- **Safety**: Protects active collections, requires confirmation
- **Reporting**: Generates markdown report of deleted collections
- **Usage**: `source .venv/bin/activate && python scripts/delete_orphaned_collections.py [--dry-run]`
- **Last Cleanup**: October 19, 2025 - Removed 10 orphaned collections (7,084 points)

### **Current Collection State** (as of Oct 2025)
- **12 Active Collections**: All 12 character bots with dedicated Qdrant collections
- **7 Aliases**: Clean names pointing to `_7d` collections (legacy compatibility)
- **Bot Name Extraction**: `collection.removeprefix('whisperengine_memory_').removesuffix('_7d')`

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