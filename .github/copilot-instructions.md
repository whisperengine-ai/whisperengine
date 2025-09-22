# WhisperEngine AI Agent Instructions

## 🚨 CRITICAL DEVELOPMENT CONTEXT 🚨

**ALPHA/DEV PHASE**: WhisperEngine is in active development/alpha. Prioritize working features over production optimization. No production users yet - we can freely iterate and change.

**VECTOR MEMORY PRIMACY**: Qdrant vector memory system (`src/memory/vector_memory_system.py`) is THE PRIMARY memory implementation. Always leverage vector/semantic search before considering manual Python analysis. Default: `MEMORY_SYSTEM_TYPE=vector`.

**FEATURE FLAG DEFAULTS**: Feature flags MUST default to **"true"** in dev/alpha to prevent feature blindness. Only use "false" defaults for genuinely dangerous features.

**NO PHANTOM FEATURES**: Every implemented feature MUST be integrated into the main application flow. Features marked "done" must actually work in the bot, not just exist in isolated files.

## Anti-Phantom Feature Guidelines

1. **Integration-First Development**: Before marking any feature "complete":
   - ✅ Verify it's imported and called in main application flow
   - ✅ Check feature flags default to "enabled" for dev/alpha
   - ✅ Test the feature actually works via Discord commands
   - ✅ Document the integration points in handlers/main.py

2. **Feature Flag Audit**: These flags currently default to "false" and cause feature blindness:
   ```bash
   ENABLE_GRAPH_DATABASE=false          # Graph features invisible  
   VISION_SUMMARIZER_ENABLED=false      # Vision features disabled
   VOICE_AUTO_JOIN=false                # Voice features hidden
   ENABLE_MONITORING_DASHBOARD=false    # Monitoring invisible
   ENABLE_AB_TESTING=false              # A/B testing disabled
   DISCORD_MESSAGE_TRACE=false          # Debug tracing off
   REQUIRE_DISCORD_MENTION=false        # Mention requirement hidden
   ```
   **ACTION REQUIRED**: Change these to default "true" for development.

3. **Vector-First Analysis**: Before writing manual analysis code:
   - ✅ Check if vector memory can provide the insights via semantic search
   - ✅ Use `search_memories_with_qdrant_intelligence()` for pattern detection
   - ✅ Leverage fastembed embeddings for similarity analysis
   - ✅ Only write manual Python if vector approach is insufficient

## Architecture Overview

WhisperEngine is an **alpha-stage** Discord AI companion bot with **multi-bot architecture**, vector-native memory, and CDL (Character Definition Language) personality systems. The architecture follows a **factory pattern** with **protocol-based dependency injection** for A/B testing and environment flexibility.

### Core Architecture Patterns

**Multi-Bot System**: Single infrastructure supports multiple character bots with isolated personalities:
- `docker-compose.multi-bot.yml` - Multi-bot container orchestration
- `./multi-bot.sh` - Management script for all bot operations
- Individual `.env.{bot-name}` files for bot-specific configuration
- Shared PostgreSQL, Redis, and Qdrant infrastructure

**Factory Pattern**: All major systems use `create_*()` factories in protocol files:
- `src/llm/llm_protocol.py` → `create_llm_client(llm_client_type="openrouter")`
- `src/memory/memory_protocol.py` → `create_memory_manager(memory_type="vector")`
- `src/voice/voice_protocol.py` → `create_voice_service(voice_service_type="discord_elevenlabs")`
- `src/conversation/engagement_protocol.py` → `create_engagement_engine(engagement_engine_type="full")`

**Configuration**: Environment-driven with TYPE-based selection:
```bash
# .env examples
LLM_CLIENT_TYPE=openrouter|local|disabled|mock
MEMORY_SYSTEM_TYPE=vector|hierarchical|test_mock
VOICE_SERVICE_TYPE=discord_elevenlabs|disabled|mock
ENGAGEMENT_ENGINE_TYPE=full|basic|disabled|mock
```

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
- `characters/examples/*.json` - Character definitions (elena-rodriguez.json, marcus-thompson.json, etc.)
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
./multi-bot.sh start marcus-chen  # Start Marcus Chen bot (game developer)
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
- `.env.marcus-chen` - Marcus Chen (Game Developer)
- `.env.dream` - Dream of the Endless (Mythological)
- Each file needs unique `DISCORD_BOT_TOKEN` and `HEALTH_CHECK_PORT`

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
- `AdminCommandHandlers` - Admin operations and backups
- `MemoryCommandHandlers` - Memory system commands
- `VoiceCommandHandlers` - Voice functionality
- `StatusCommandHandlers` - Health and status monitoring
- `MultiEntityCommandHandlers` - Character management
- `CDLTestCommands` - Character definition testing
- `MonitoringCommands` - System monitoring and performance

**Handler Registration Pattern**:
```python
# In src/main.py ModularBotManager
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

**Multi-Bot Architecture** (Complete): Introduced shared infrastructure supporting multiple character bots with isolated personalities. See `MULTI_BOT_SETUP.md`.

**CDL Character System** (Complete): Migrated from markdown prompts to JSON-based Character Definition Language for structured personality modeling.

**Architecture Simplification** (Complete): Eliminated complex try/except ImportError patterns, replaced with clean factory patterns. See `ARCHITECTURE_SIMPLIFICATION_COMPLETE.md`.

**Memory Migration** (Complete): Migrated to vector-native memory with Qdrant + fastembed. Default: `MEMORY_SYSTEM_TYPE=vector`.

**Factory Pattern Adoption**: All major systems now use factory pattern for dependency injection and environment flexibility.

**Phase 4 Integration** (Complete): Advanced conversation intelligence with production optimization components fully integrated and operational.