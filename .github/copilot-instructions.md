# WhisperEngine AI Agent Instructions

## 🚨 CRITICAL DEVELOPMENT CONTEXT 🚨

**ALPHA/DEV PHASE**: WhisperEngine is in active development. Prioritize working features over production optimization. No production users yet - we can freely iterate and change.

**🚨 CRITICAL DEV RULE: NO FEATURE FLAGS FOR LOCAL CODE!** 
- Features should work BY DEFAULT in development
- **ONLY use feature flags for REMOTE/EXTERNAL dependencies** (APIs, external services, optional dependencies)
- **NEVER use feature flags for LOCAL code dependencies** - this creates spaghetti conditionals and silent failures
- We are in ALPHA - all LOCAL features should be enabled and testable immediately
- Environment variables are for infrastructure config ONLY (database URLs, API keys, etc.)
- When implementing features with LOCAL dependencies, make them work directly - don't hide them behind flags
- Use stubs/no-op implementations for missing EXTERNAL dependencies, not feature flags

**DOCKER-FIRST DEVELOPMENT**: Container-based development is the PRIMARY workflow. Use `./multi-bot.sh` for all operations (auto-generated, don't edit manually).

**UNIVERSAL IDENTITY SYSTEM**: NEW platform-agnostic user identity system in `src/identity/` allows users to interact across Discord, Web UI, and future platforms while maintaining consistent memory and conversations.

**WEB INTERFACE INTEGRATION**: Complete web chat interface (`src/web/simple_chat_app.py`) with real-time WebSocket messaging, multi-bot character selection, and Universal Identity integration. Accessible at http://localhost:8080 (Docker deployment) or http://localhost:8081 (standalone).

**PYTHON VIRTUAL ENVIRONMENT**: Always use `.venv/bin/activate` for Python commands:
```bash
source .venv/bin/activate   # ALWAYS use this for Python execution
python scripts/generate_multi_bot_config.py  # Example: configuration generation
```

**ENVIRONMENT LOADING**: `run.py` uses `env_manager.py` for smart environment loading:
- `python run.py` - Uses env_manager.py for proper environment detection and loading
- Direct Python scripts - Use `from dotenv import load_dotenv; load_dotenv()` 
- env_manager.py handles Docker vs local development mode detection automatically
- Direct `.env` loading may miss environment-specific configurations

**VECTOR MEMORY PRIMACY**: Qdrant vector memory system (`src/memory/vector_memory_system.py`) is THE PRIMARY memory implementation. Always leverage vector/semantic search before considering manual Python analysis.

**NO NEO4J**: We don't use Neo4j anymore - everything is vector-native with Qdrant. Delete any Neo4j references, imports, or graph database code.

**DYNAMIC MULTI-BOT SYSTEM**: Bot configurations are auto-discovered from `.env.*` files. No hardcoded bot names - everything is generated dynamically by `scripts/generate_multi_bot_config.py`. Currently active bots: Elena, Marcus, Jake, Dream, Aethys, Ryan, Gabriel, Sophia.

## Architecture Overview

WhisperEngine is a **multi-bot Discord AI companion system** with vector-native memory, CDL (Character Definition Language) personalities, Universal Identity system, and protocol-based dependency injection.

### Core Patterns

**Factory Pattern**: All major systems use `create_*()` factories in protocol files:
```python
# Memory system (vector-native)
from src.memory.memory_protocol import create_memory_manager
memory_manager = create_memory_manager(memory_type="vector")

# Multi-bot querying
from src.memory.memory_protocol import create_multi_bot_querier
querier = create_multi_bot_querier()

# LLM client
from src.llm.llm_protocol import create_llm_client
llm_client = create_llm_client(llm_client_type="openrouter")

# Universal Identity (NEW)
from src.identity.universal_identity import create_identity_manager
identity_manager = create_identity_manager(postgres_pool)
```

**Multi-Bot Architecture**: Single infrastructure supports multiple character bots:
- Individual `.env.{bot-name}` files for bot-specific configuration
- Shared PostgreSQL, Redis, and Qdrant infrastructure
- Dynamic discovery and configuration generation
- Isolated personalities but shared memory intelligence

**Universal Identity System**: Platform-agnostic user identity management:
- Users can interact via Discord, Web UI, or future platforms
- Consistent universal IDs that map to platform-specific identities
- Enhanced account discovery prevents duplicate accounts
- Bot-specific memory isolation while preserving cross-platform identity

### Entry Points

**Main Application**: `src/main.py` → `ModularBotManager` class
- Dependency injection with protocol-based factories
- Graceful error handling with production patterns
- Health check integration for container orchestration

**Bot Core**: `src/core/bot.py` → `DiscordBotCore` class
- All component initialization in `initialize_all()`
- Factory-based component creation
- Async initialization for heavy components

**Web Interface**: `src/web/simple_chat_app.py` → `SimpleWebChatApp` class
- FastAPI-based ChatGPT-like interface
- WebSocket real-time messaging
- Universal Identity integration for cross-platform user management
- Enhanced account discovery with bot-specific memory information

## Development Workflow

### Multi-Bot Management

**Template-Based Architecture**: WhisperEngine uses a template-based multi-bot system that fills in environment-specific values from a stable Docker Compose template.

```bash
# NEVER edit multi-bot.sh or docker-compose.multi-bot.yml manually
# They are auto-generated from docker-compose.multi-bot.template.yml

# List available bots
./multi-bot.sh list

# Start specific bot or all bots
./multi-bot.sh start elena
./multi-bot.sh start all

# View logs, stop, restart
./multi-bot.sh logs marcus
./multi-bot.sh stop elena
./multi-bot.sh restart
```

**Infrastructure Versions (Pinned)**:
- PostgreSQL: `postgres:16.4-alpine` (pinned for stability) - Port 5433
- Redis: `redis:7.4-alpine` (pinned for stability) - Port 6380
- Qdrant: `qdrant/qdrant:v1.15.4` (pinned for vector stability) - Port 6334
- Web Interface: Available at http://localhost:8080 (Docker) or http://localhost:8081 (standalone)

### Web Interface Development

**Web UI Setup**: Run the web interface independently:
```bash
# Start infrastructure first (PostgreSQL on port 5433, Redis on 6380, Qdrant on 6334)
./multi-bot.sh start all

# Export correct PostgreSQL configuration
export POSTGRES_HOST=localhost POSTGRES_PORT=5433 POSTGRES_DB=whisperengine 
export POSTGRES_USER=whisperengine POSTGRES_PASSWORD=whisperengine123

# Start web interface (standalone)
source .venv/bin/activate
python src/web/simple_chat_app.py
# Accessible at http://localhost:8081 (standalone)

# OR use Docker-based web interface (included in multi-bot)
# Already running at http://localhost:8080 when using ./multi-bot.sh start all
```

**Web UI Features**:
- Real-time WebSocket chat with multiple bot personalities
- Universal Identity account discovery (prevents duplicate accounts)
- Bot-specific memory isolation and conversation history
- Enhanced UX for Discord users migrating to web interface

### Adding New Bots
```bash
# 1. Copy template and customize
cp .env.template .env.newbot
# Edit .env.newbot with unique Discord token, bot name, character file

# 2. Create character file (optional - will use default if not found)
# Add characters/examples/newbot.json or similar

# 3. Regenerate template-based configuration
source .venv/bin/activate
python scripts/generate_multi_bot_config.py

# 4. Start your new bot
./multi-bot.sh start newbot
```

**Template System**: 
- Base template: `docker-compose.multi-bot.template.yml` (SAFE TO EDIT)
- Generated output: `docker-compose.multi-bot.yml` (AUTO-GENERATED)
- Management script: `multi-bot.sh` (AUTO-GENERATED)

### Key Development Commands
```bash
# Health and status
./multi-bot.sh status              # Container status
./multi-bot.sh logs [bot_name]     # View logs

# Development workflow
source .venv/bin/activate          # Always use venv
python scripts/generate_multi_bot_config.py  # Regenerate config

# Testing (use container-based for consistency)
docker exec whisperengine-elena-bot python -m pytest tests/unit/
```

## Memory System (Critical)

**Vector-Native Architecture**: Qdrant vector memory with fastembed is THE PRIMARY memory system:
```python
# ALWAYS use vector/semantic search before manual Python analysis
memories = await memory_manager.retrieve_relevant_memories(
    user_id=user_id, query=message, limit=10
)

# Store with emotional context for future retrieval  
await memory_manager.store_conversation(
    user_id=user_id, 
    user_message=user_message, 
    bot_response=bot_response,
    pre_analyzed_emotion_data=emotion_data
)
```

**🚨 CRITICAL: Vector Storage Design Patterns**

**ALWAYS use Named Vectors** - Never use single vectors:
```python
# ✅ CORRECT: Named vectors for multi-dimensional search
vectors = {
    "content": content_embedding,      # Main semantic content (384D)
    "emotion": emotion_embedding,      # Emotional context (384D)
    "semantic": semantic_embedding     # Concept/personality context (384D)
}

point = PointStruct(
    id=memory.id,
    vector=vectors,  # Named vectors dict
    payload=qdrant_payload
)

# ✅ CORRECT: Query with named vectors
results = client.search(
    collection_name=collection_name,
    query_vector=models.NamedVector(name="content", vector=query_embedding),
    limit=top_k
)

# ❌ WRONG: Single vector (legacy format)
point = PointStruct(id=memory.id, vector=embedding, payload=payload)
```

**ALWAYS use Bot Segmentation** - Filter by bot_name:
```python
# ✅ CORRECT: All operations must filter by bot_name
must_conditions = [
    models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id)),
    models.FieldCondition(key="bot_name", match=models.MatchValue(value=get_normalized_bot_name_from_env()))
]

# ✅ CORRECT: Store with bot segmentation
payload = {
    "user_id": user_id,
    "bot_name": get_normalized_bot_name_from_env(),  # CRITICAL: Bot isolation
    "content": content,
    "memory_type": memory_type
}

# ❌ WRONG: Missing bot_name segmentation
payload = {"user_id": user_id, "content": content}  # Will leak across bots!
```

**Vector Retrieval Patterns** - Handle named vector responses:
```python
# ✅ CORRECT: Extract vectors from named vector responses
def _extract_named_vector(self, point_vector, vector_name: str = "content"):
    if isinstance(point_vector, dict):
        return point_vector.get(vector_name)  # Named vector format
    elif isinstance(point_vector, list):
        return point_vector  # Legacy single vector
    return None

# ✅ CORRECT: Use specific named vectors in queries
scroll_result = client.scroll(
    collection_name=collection_name,
    with_vectors=["content"],  # Specify which named vector
    limit=batch_size
)
```

**Bot-Specific Memory Isolation**: Critical discovery - each bot has completely isolated memories:
```python
# Memory queries filter by bot_name (Elena, Marcus, etc.)
# This creates complete conversation isolation between bots
# Account discovery must show which bots user has history with

# Memory filtering uses: user_id + bot_name + memory_type
# Environment variable: DISCORD_BOT_NAME determines bot context
```

**Multi-Bot Memory Intelligence**:
```python
# Query across all bots (admin/debugging)
querier = create_multi_bot_querier()
all_results = await querier.query_all_bots("user preferences", "user123")

# Cross-bot analysis and insights
analysis = await querier.cross_bot_analysis("user123", "conversation style")
```

## Universal Identity & Account Discovery

**Universal Identity System**: Platform-agnostic user management:
```python
from src.identity.universal_identity import create_identity_manager
identity_manager = create_identity_manager(postgres_pool)

# Create web-only user
universal_user = await identity_manager.create_web_user(
    username=username, 
    display_name=display_name
)

# Link Discord to existing user
universal_user = await identity_manager.get_or_create_discord_user(
    discord_user_id=discord_id,
    username=username
)
```

**Enhanced Account Discovery**: Prevents duplicate accounts in web UI:
```python
# Search for existing users by username patterns
existing_users = await identity_manager.find_users_by_username(username)

# Shows bot-specific memory counts and conversation history
# Guides users to link Discord accounts or choose different usernames
# Critical for preventing account fragmentation across platforms
```

## Character System

**CDL Integration**: JSON-based character personalities:
```python
from src.prompts.cdl_ai_integration import CDLAIPromptIntegration
cdl_integration = CDLAIPromptIntegration()
prompt = await cdl_integration.create_character_aware_prompt(
    character_file='characters/examples/elena-rodriguez.json',
    user_id=user_id,
    message_content=message
)
```

## Anti-Phantom Feature Guidelines

**Integration-First Development**: Before marking any feature "complete":
- ✅ Verify it's imported and called in main application flow (`src/main.py`)
- ✅ **NO ENVIRONMENT VARIABLE FLAGS** - features work by default in development
- ✅ Test the feature actually works via Discord commands
- ✅ Document integration points in handler classes

**🚨 DEVELOPMENT ANTI-PATTERNS TO AVOID:**
- ❌ Environment variable feature flags (`ENABLE_X=true`) 
- ❌ Features that are "implemented" but require special configuration to work
- ❌ Silent fallbacks that mask real failures
- ❌ "Phantom features" that exist in code but aren't accessible to users

**Vector-First Analysis**: Before writing manual analysis code:
- ✅ Check if vector memory can provide insights via semantic search
- ✅ Use `search_memories_with_qdrant_intelligence()` for pattern detection
- ✅ Only write manual Python if vector approach is insufficient

## Key Directories

- `src/core/` - Bot initialization (`DiscordBotCore`, `ModularBotManager`)
- `src/memory/` - Vector-native memory system with multi-bot querying
- `src/handlers/` - Discord command handlers (modular architecture)
- `src/prompts/` - CDL integration and prompt management
- `src/identity/` - Universal Identity system (NEW) - platform-agnostic user management
- `src/web/` - Web chat interface (NEW) - FastAPI-based real-time chat
- `characters/examples/` - CDL character definitions (JSON)
- `scripts/` - Configuration generation and utilities
- `.env.*` files - Bot-specific configurations (auto-discovered)

## Configuration Files

**NEVER EDIT MANUALLY**:
- `docker-compose.multi-bot.yml` - Auto-generated by discovery script
- `multi-bot.sh` - Auto-generated management script

**EDIT THESE**:
- `.env.{bot_name}` - Bot-specific environment configuration
- `characters/examples/*.json` - Character personality definitions
- `scripts/generate_multi_bot_config.py` - Configuration generator

## AI Conversation Intelligence

WhisperEngine implements conversation intelligence through integrated systems:

**Memory & Context**: Vector-native memory with semantic search provides conversation continuity:
- `src/memory/` - Vector storage with conversation history retrieval
- `src/intelligence/context_switch_detector.py` - Maintains conversation flow
- Memory-triggered moments for long-term relationship continuity

**Character & Emotion Systems**: CDL-based personalities with emotional intelligence:
- `src/characters/cdl/` - Character Definition Language system
- `src/intelligence/enhanced_vector_emotion_analyzer.py` - Vector-based emotion analysis
- `src/prompts/cdl_ai_integration.py` - Integrates personality with conversation context

**Conversation Management**: Multi-bot engagement with context awareness:
- `src/conversation/engagement_protocol.py` - Manages conversation flow and engagement
- `src/handlers/` - Modular command system for Discord interactions
- Thread management and proactive engagement patterns

## Character Definition Language (CDL)

**CDL System**: Modern JSON-based character personalities replacing legacy markdown prompts:
- `characters/examples/*.json` - Character definitions (elena-rodriguez.json, marcus-thompson.json, jake-sterling.json, dream_of_the_endless.json, aethys-omnipotent-entity.json, ryan-chen.json, gabriel.json, sophia-blake.json)
- `src/characters/cdl/parser.py` - CDL parser and validator
- `src/prompts/cdl_ai_integration.py` - Integrates CDL with AI pipeline and emotional intelligence
- Each character has unique personality, occupation, communication style, and values

**CDL Integration Pattern**:
```python
from src.prompts.cdl_ai_integration import CDLAIPromptIntegration
cdl_integration = CDLAIPromptIntegration()
system_prompt = await cdl_integration.create_character_aware_prompt(
    character_file='characters/examples/elena-rodriguez.json',
    user_id=user_id,
    message_content=message,
    pipeline_result=emotion_analysis  # Optional emotional intelligence context
)
```

## Memory System (Critical)

**Vector-Native Architecture**: Qdrant vector memory with fastembed is THE PRIMARY memory system:
- `src/memory/vector_memory_system.py` - Production vector implementation (supersedes all previous)
- Defaults to `MEMORY_SYSTEM_TYPE=vector` in `src/core/bot.py`
- Protocol system (`src/memory/memory_protocol.py`) enables A/B testing
- **ALWAYS use vector/semantic search before manual Python analysis**
- **🚨 CRITICAL**: Follow Named Vectors + Bot Segmentation patterns (see Vector Storage Design Patterns above)
- Memory-triggered moments create long-term relationship continuity

**Key Files**:
- `src/memory/vector_memory_system.py` - Vector-native implementation (USE THIS)
- `src/memory/memory_protocol.py` - Protocol and factory for system selection
- `src/memory/faiss_memory_engine.py` - Alternative engine (not production)

**Memory Operations** (Always use async for contextual continuity):
```python
# Store conversation with emotional context for future retrieval
await memory_manager.store_conversation(
    user_id=user_id, 
    user_message=user_message, 
    bot_response=bot_response,
    pre_analyzed_emotion_data=emotion_data  # Critical for emotional continuity
)

# Retrieve contextually relevant memories for conversation flow
relevant_memories = await memory_manager.retrieve_relevant_memories(
    user_id=user_id, 
    query=current_message, 
    limit=10
)

# Get conversation history for immediate context
conversation_history = await memory_manager.get_conversation_history(
    user_id=user_id, 
    limit=10
)
```

## Development Workflow

**DOCKER-FIRST DEVELOPMENT**: Container-based development is the PRIMARY workflow. Native Python is no longer practical for full system functionality.

**CRITICAL**: The legacy `./bot.sh` script has been **DEPRECATED**. Use `./multi-bot.sh` for all operations:

**Multi-Bot Control Script**: Use `./multi-bot.sh` for all operations:
```bash
./multi-bot.sh start elena        # Start Elena bot (marine biologist)
./multi-bot.sh start marcus       # Start Marcus bot (AI researcher) 
./multi-bot.sh start jake         # Start Jake bot (game developer)
./multi-bot.sh start dream        # Start Dream bot (mythological entity)
./multi-bot.sh start aethys       # Start Aethys bot (omnipotent entity)
./multi-bot.sh start ryan         # Start Ryan bot (software engineer)
./multi-bot.sh start gabriel      # Start Gabriel bot
./multi-bot.sh start sophia       # Start Sophia bot (neuroscientist)
./multi-bot.sh start all          # Start all configured bots
./multi-bot.sh stop               # Stop all bots
./multi-bot.sh logs elena         # View Elena's logs
./multi-bot.sh status             # Show all container status
```

**Development Modes**:
- **Multi-bot Docker**: `./multi-bot.sh start elena` (PRIMARY development method)
- **Single bot Docker**: `./bot.sh start dev` (legacy, use multi-bot instead)
- **Native Python**: `python run.py` (NOT RECOMMENDED - container dependencies required)

**Docker Development**: Container-based development is the standard:
```bash
docker-compose -f docker-compose.multi-bot.yml up    # Multi-bot development (PRIMARY)
docker-compose -f docker-compose.dev.yml up         # Legacy single-bot development
docker-compose up qdrant postgres redis             # Infrastructure only
```

**Testing**: Use containerized testing for consistency:
```bash
# Container-based testing (recommended)
docker exec whisperengine-elena-bot python -m pytest tests/unit/
docker exec whisperengine-marcus-bot python -m pytest tests/integration/

# Native testing (requires manual dependency setup)
source .venv/bin/activate && pytest tests/unit/     # Not recommended
```

**Python Virtual Environment**: Only needed for isolated script testing:
```bash
source .venv/bin/activate   # Only for standalone scripts
python demo_vector_emoji_intelligence.py  # Example: testing demos
```

**Bot Configuration**: Each bot requires individual environment files:
- `.env.elena` - Elena Rodriguez (Marine Biologist)
- `.env.marcus` - Marcus Thompson (AI Researcher)  
- `.env.jake` - Jake Sterling (Game Developer)
- `.env.dream` - Dream of the Endless (Mythological)
- `.env.aethys` - Aethys (Omnipotent Entity)
- `.env.ryan` - Ryan Chen (Software Engineer)
- `.env.gabriel` - Gabriel (Archangel)
- `.env.sophia` - Sophia Blake (Neuroscientist)
- Each file needs unique `DISCORD_BOT_TOKEN` and `HEALTH_CHECK_PORT`

## Current System Status

**Active Infrastructure** (as of current deployment):
- ✅ **Multi-Bot System**: 8+ character bots running simultaneously (Elena, Marcus, Jake, Dream, Aethys, Ryan, Gabriel, Sophia)
- ✅ **Web Interface**: Real-time chat at http://localhost:8080 with cross-platform identity
- ✅ **Vector Memory**: Qdrant-powered with 384D embeddings, named vector support, bot-specific isolation
- ✅ **Universal Identity**: Platform-agnostic user management with account discovery
- ✅ **CDL Character System**: JSON-based personality definitions, integrated AI identity filtering
- ✅ **Health Monitoring**: Container health checks, graceful shutdown, performance monitoring

**Tested Working Features**:
- Multi-bot Discord conversations with persistent memory
- Real-time web chat interface with bot selection
- Vector-based semantic memory retrieval across conversations
- CDL-driven character personality responses
- Bot-specific memory isolation (Elena's memories stay with Elena)
- Cross-platform user identity (Discord users can use web interface)
- Health endpoints for container orchestration
- Template-based configuration management

**Development Commands Verified Working**:
```bash
./multi-bot.sh start all     # ✅ Starts all 8+ bots + infrastructure
./multi-bot.sh status        # ✅ Shows container health status
./multi-bot.sh logs elena    # ✅ Real-time bot logs
http://localhost:8080        # ✅ Web interface with real-time chat
```

## Phase 4 Integration

**Conversation Intelligence**: Advanced AI conversation features:
- `src/intelligence/phase4_integration.py` - Core Phase 4 integration system with HumanLikeMemoryOptimizer
- `src/intelligence/phase4_human_like_integration.py` - Human-like conversation patterns
- `src/intelligence/enhanced_vector_emotion_analyzer.py` - Vector-based emotion analysis
- `src/intelligence/emoji_reaction_intelligence.py` - Advanced emoji processing
- `src/intelligence/simplified_emotion_manager.py` - Unified emotion processing pipeline
- Memory-triggered moments for relationship continuity
- Context switch detection and conversation flow management

## Handler System

**Modular Handler Architecture**: All Discord commands use handler classes in `src/handlers/`:
- `BotEventHandlers` - Core Discord event handling
- `HelpCommandHandlers` - Help system and command documentation
- `StatusCommandHandlers` - Health and status monitoring
- `VoiceCommandHandlers` - Voice functionality
- `PrivacyCommandHandlers` - Privacy and data management
- `MonitoringCommands` - System monitoring and performance
- `PerformanceCommands` - Performance analysis and optimization
- `LLMToolCommandHandlers` - LLM-powered tool commands (conditionally enabled)
- `LLMSelfMemoryHandlers` - Self-memory analysis commands (conditionally enabled)
- `WebSearchCommandHandlers` - Web search integration (available)

**Currently Disabled** (over-engineered or obsolete):
- `AdminCommandHandlers` - Disabled (over-engineered)
- `MemoryCommandHandlers` - Disabled (obsolete API)
- `CDLTestCommands` - Disabled (dev testing only)

**Handler Registration Pattern**:
```python
# In src.main.py ModularBotManager
handler = HandlerClass(bot, memory_manager, llm_client)
await handler.register_commands()
```

## Security & Production

**Error Handling**: Production-grade error handling with graceful degradation:
```python
from src.utils.production_error_handler import handle_errors, ErrorCategory, ErrorSeverity

@handle_errors(category=ErrorCategory.MEMORY, severity=ErrorSeverity.HIGH)
async def memory_operation():
    # Operation with automatic error handling
```

**Health Monitoring**: Multi-component health system:
- `/health` endpoint for container orchestration
- Discord admin commands for live monitoring
- `src/utils/health_monitor.py` for component health tracking

## Code Conventions

**Async-First**: All major operations are async, following WhisperEngine's scatter-gather concurrency model.

**Protocol Compliance**: New components must implement corresponding protocols (e.g., `MemoryManagerProtocol`).

**Factory Creation**: Use factories for component creation, never direct imports of concrete classes.

**Environment Configuration**: Use TYPE-based environment variables, not boolean flags.

**Import Safety**: Use try/except for optional dependencies, fall back to no-op implementations.

**Conversation Intelligence Patterns**: Core AI conversation implementations:

```python
# ✅ Use CDL integration for character-aware responses
from src.prompts.cdl_ai_integration import CDLAIPromptIntegration
cdl_integration = CDLAIPromptIntegration()
prompt = await cdl_integration.create_character_aware_prompt(
    character_file=character_file,
    user_id=user_id,
    message_content=message
)

# ✅ Use vector memory for conversation context
memories = await memory_manager.retrieve_relevant_memories(
    user_id=user_id,
    query=message,
    limit=10
)
```

**Component Removal**: When removing obsolete components, update all references including:
- Factory imports and creation calls
- Protocol type annotations
- Integration adapters
- Test files and utilities

**Anti-Phantom Features**: Prevent "phantom features" that exist but aren't integrated:
- Every feature must be accessible via Discord commands or main application flow
- Feature flags must default to "true" in development (we're in alpha - no production users)
- Integration testing required before marking features "complete"
- Document integration points, not just implementation files

**🚨 CRITICAL: Vector Storage Compliance** - ALL vector operations must follow these patterns:
- **ALWAYS use Named Vectors**: Never single vector format - use `{"content": embedding}` structure
- **ALWAYS use Bot Segmentation**: Every payload must include `bot_name` for isolation
- **ALWAYS extract with helpers**: Use `_extract_named_vector()` when retrieving vectors
- **ALWAYS query with NamedVector**: Use `models.NamedVector(name="content", vector=embedding)`
- **NEVER bypass bot isolation**: All searches must filter by `bot_name` + `user_id`
- Vector retrieval code must handle dictionary format from Qdrant named vectors
- When in doubt, check `src/memory/vector_memory_system.py` for reference patterns

## Key Directories

- `src/core/` - Bot initialization and Discord integration
- `src/handlers/` - Discord command handlers (modular architecture)
- `src/memory/` - Vector-native memory system
- `src/llm/` - LLM client abstraction with concurrent safety
- `src/conversation/` - Context management and engagement
- `src/personality/` - Character systems and emotion intelligence
- `src/intelligence/` - Phase 4 integration and conversation intelligence
- `src/integration/` - System integration framework
- `src/security/` - Production security and privacy
- `src/utils/` - Cross-cutting concerns and monitoring
- `src/characters/` - CDL character system and parsers
- `src/prompts/` - CDL integration and prompt management

## Recent Major Changes

**Universal Identity & Web Interface** (NEW): Introduced platform-agnostic user identity system allowing users to interact via Discord, Web UI, or future platforms while maintaining consistent memory. Enhanced account discovery prevents duplicate accounts.

**Template-Based Multi-Bot System** (Complete): Migrated from programmatic Docker Compose generation to safe template-based approach. Infrastructure versions now pinned (PostgreSQL 16.4, Redis 7.4, Qdrant v1.15.4) to prevent breaking updates.

**Multi-Bot Architecture** (Complete): Introduced shared infrastructure supporting multiple character bots with isolated personalities. See `MULTI_BOT_SETUP.md`.

**CDL Character System** (Complete): Migrated from markdown prompts to JSON-based Character Definition Language for structured personality modeling.

**Architecture Simplification** (Complete): Eliminated complex try/except ImportError patterns, replaced with clean factory patterns. See `ARCHITECTURE_SIMPLIFICATION_COMPLETE.md`.

**Memory Migration** (Complete): Migrated to vector-native memory with Qdrant + fastembed. Default: `MEMORY_SYSTEM_TYPE=vector`.

**Factory Pattern Adoption**: All major systems now use factory pattern for dependency injection and environment flexibility.

**Phase 4 Integration** (Complete): Advanced conversation intelligence with production optimization components fully integrated and operational.