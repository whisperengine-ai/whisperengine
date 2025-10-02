# WhisperEngine AI Agent Instructions

## 🚨 CRITICAL DEVELOPMENT CONTEXT 🚨

**🚨 CRITICAL TERMINOLOGY DIRECTIVE:**
- **WhisperEngine uses "AI Roleplay Characters" NOT "AI Companions"**
- **ALWAYS use "AI roleplay characters" or "AI characters" in all documentation, code comments, and communications**
- **NEVER use "companions", "assistants", or "bots" when referring to character entities**
- **Multi-character architecture** not "multi-bot architecture"
- **Character-based system** not "bot-based system"
- This is a foundational branding and positioning distinction

**🚨 CRITICAL DOCUMENTATION TONE DIRECTIVE:**
- **MAINTAIN CASUAL TECHNICAL TONE** in all documentation and communications
- **AVOID SENSATIONAL LANGUAGE** - no "revolutionary", "breakthrough", "groundbreaking" claims
- **NO SCIENTIFIC CLAIMS** - avoid "scientific validation", "empirical proof", "research findings"
- **USE TECHNICAL PRECISION** with humble, measured language
- **FRAME AS DEVELOPMENT PROGRESS** not academic research or commercial breakthroughs
- **FOCUS ON IMPLEMENTATION DETAILS** rather than broad claims or implications
- This reflects WhisperEngine's pragmatic engineering approach

**ALPHA/DEV PHASE**: WhisperEngine is in active development. Prioritize working features over production optimization. No production users yet - we can freely iterate and change.

**🚨 CRITICAL DEV RULE: NO FEATURE FLAGS FOR LOCAL CODE!** 
- Features should work BY DEFAULT in development
- **ONLY use feature flags for REMOTE/EXTERNAL dependencies** (APIs, external services, optional dependencies)
- **NEVER use feature flags for LOCAL code dependencies** - this creates spaghetti conditionals and silent failures
- We are in ALPHA - all LOCAL features should be enabled and testable immediately
- Environment variables are for infrastructure config ONLY (database URLs, API keys, etc.)
- When implementing LOCAL dependencies, make them work directly - don't hide them behind flags
- Use stubs/no-op implementations for missing EXTERNAL dependencies, not feature flags

**🚨 CRITICAL ARCHITECTURE RULE: NO CHARACTER-SPECIFIC HARDCODED LOGIC!**
- **NEVER hardcode character names, personalities, or character-specific behavior in Python code**
- **ALL character data must come from CDL JSON files** (`characters/examples/*.json`)
- **ALL bot identification must use environment variables** (`DISCORD_BOT_NAME`, `CHARACTER_FILE`)
- **USE dynamic discovery and configuration generation** via `scripts/generate_multi_bot_config.py`
- **NO hardcoded bot lists, character references, or personality assumptions**
- **Character logic flows through CDL system ONLY** - never embed personality traits in code
- **Bot names are discovered dynamically** from `.env.*` files - never maintain static lists
- **Multi-character architecture requires complete character agnosticism** in all Python components
- When adding features, ensure they work for ANY character via CDL integration
- Use `get_normalized_bot_name_from_env()` for bot identification, never literal strings

**DOCKER-FIRST DEVELOPMENT**: Container-based development is the PRIMARY workflow. Use `./multi-bot.sh` for all operations (auto-generated, don't edit manually).

**AI CHARACTER TESTING STRATEGY**: Use different AI roleplay characters for specific testing scenarios:
- **MEMORY TESTING**: Use Jake or Ryan characters - they have minimal personality complexity, making memory issues easier to isolate
- **PERSONALITY/CDL TESTING**: Use Elena character - she has the richest and most extensive CDL personality for testing emotional intelligence, character responses, and CDL pipeline functionality
- **CODE CHANGES**: Use `./multi-bot.sh restart <character>` for code changes, but `./multi-bot.sh stop <character> && ./multi-bot.sh start <character>` for environment changes
- **START/STOP AS NEEDED**: Only run the specific character(s) needed for testing to reduce resource usage and isolate issues

**DISCORD-FIRST ARCHITECTURE**: WhisperEngine is a Discord-focused multi-character AI roleplay system. **Web interface has been removed** - Discord is the primary and only supported platform.

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

**DYNAMIC MULTI-CHARACTER SYSTEM**: Character configurations are auto-discovered from `.env.*` files. No hardcoded character names - everything is generated dynamically by `scripts/generate_multi_bot_config.py`. Currently active characters: elena, marcus, jake, dream, aethys, ryan, gabriel, sophia.

**BOT-SPECIFIC COLLECTION ISOLATION**: Each bot uses its own dedicated Qdrant collection for complete memory isolation:
- Elena: `whisperengine_memory_elena` (4,834 memories)
- Marcus: `whisperengine_memory_marcus` (2,738 memories) 
- Gabriel: `whisperengine_memory_gabriel` (2,897 memories)
- Sophia: `whisperengine_memory_sophia` (3,131 memories)
- Jake: `whisperengine_memory_jake` (1,040 memories)
- Ryan: `whisperengine_memory_ryan` (821 memories)
- Dream: `whisperengine_memory_dream` (916 memories)
- Aethys: `chat_memories_aethys` (6,630 memories)

**REDIS STATUS**: Redis is CURRENTLY DISABLED in multi-bot setup. Only PostgreSQL (port 5433) and Qdrant (port 6334) are active. Redis references remain in code for potential future re-enabling.

## Architecture Overview

WhisperEngine is a **multi-character Discord AI roleplay system** with vector-native memory, CDL (Character Definition Language) personalities, Universal Identity system, and protocol-based dependency injection.

## 🎯 FIDELITY-FIRST ARCHITECTURE PRIORITY

**CRITICAL DESIGN PHILOSOPHY**: WhisperEngine prioritizes **conversation fidelity** and **character authenticity** over premature optimization. This architectural principle guides all development decisions:

**Fidelity-First Design Patterns**:
- **Preserve Full Character Nuance**: Keep complete personality context until absolutely necessary to reduce
- **Graduated Optimization**: Only compress/optimize when context limits are actually exceeded
- **Vector-Enhanced Intelligence**: Leverage existing Qdrant infrastructure instead of building separate NLP pipelines
- **Character-Aware Memory Filtering**: Elena's memories stay with Elena, Marcus's with Marcus
- **Intelligent Context Assembly**: Use semantic similarity for prioritization, not arbitrary truncation

**Architecture Direction**:
- **Vector-Native Operations**: All semantic processing uses existing Qdrant vector memory system
- **Character Consistency**: CDL system provides authentic personality responses throughout pipeline
- **Memory Intelligence**: Bot-specific segmentation with named vector embeddings (content/emotion/semantic)
- **Fidelity Preservation**: Maintain conversation quality and character depth as primary design constraint

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

# Structured CDL Personal Knowledge (NEW) - Integrated into prompt building
# Personal knowledge is extracted directly in CDL AI Integration during prompt building
# No separate helper needed - question type detection pulls relevant CDL sections
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

## Development Workflow

### Multi-Bot Management

**Template-Based Architecture**: WhisperEngine uses a template-based multi-bot system that fills in environment-specific values from a stable Docker Compose template.

**Multi-Bot Testing Strategy**:
```bash
# MEMORY TESTING: Use Jake or Ryan (minimal personality complexity)
./multi-bot.sh start jake       # Start Jake for memory testing
./multi-bot.sh start ryan       # Or Ryan for memory testing

# PERSONALITY/CDL TESTING: Use Elena (rich CDL personality)
./multi-bot.sh start elena      # Start Elena for CDL/personality testing

# 🚨 CRITICAL: Environment changes require FULL STOP/START, not restart
./multi-bot.sh stop jake && ./multi-bot.sh start jake    # After .env.jake changes
./multi-bot.sh restart jake     # ONLY for code changes (not .env changes)

# ALWAYS use Docker commands for logs (multi-bot.sh logs fails consistently)
docker logs whisperengine-jake-bot --tail 20   # Jake logs
docker logs whisperengine-ryan-bot --tail 20   # Ryan logs  
docker logs whisperengine-elena-bot --tail 20  # Elena logs
docker logs whisperengine-<bot>-bot -f         # Follow any bot logs
```

**Discord Message Testing**: Discord message processing requires manual triggering:
- **IMPORTANT**: Discord events (message handling, CDL integration, character responses) require actual Discord messages
- **Bot API endpoints work automatically**: HTTP API calls to `http://localhost:9091/api/chat` work immediately
- **Discord integration testing**: Ask the user to send a Discord message to trigger event handlers when testing Discord-specific features
- **Event handler updates**: Changes to `src/handlers/events.py` require Discord message to test the full pipeline

**Multi-Bot Operations**:
```bash
# NEVER edit multi-bot.sh or docker-compose.multi-bot.yml manually
# They are auto-generated from docker-compose.multi-bot.template.yml

# List available bots
./multi-bot.sh list

# Start specific bot or all bots
./multi-bot.sh start elena
./multi-bot.sh start all

# 🚨 CRITICAL: Environment vs Code Changes
# Environment changes (.env.* files) - REQUIRE FULL STOP/START:
./multi-bot.sh stop elena && ./multi-bot.sh start elena

# Code changes (Python files) - restart is sufficient:
./multi-bot.sh restart elena

# Stop operations
./multi-bot.sh stop elena

# CRITICAL: ALWAYS use Docker commands for viewing logs
docker logs whisperengine-elena-bot --tail 20     # Elena logs
docker logs whisperengine-marcus-bot --tail 20    # Marcus logs  
docker logs whisperengine-gabriel-bot --tail 20   # Gabriel logs
docker logs whisperengine-<bot>-bot -f            # Follow any bot logs
```

**Infrastructure Versions (Pinned)**:
- PostgreSQL: `postgres:16.4-alpine` (pinned for stability) - Port 5433
- Qdrant: `qdrant/qdrant:v1.15.4` (pinned for vector stability) - Port 6334
- Redis: Currently DISABLED in multi-bot setup (references remain in code)

### Bot API Endpoints

**Individual Bot APIs**: Each bot exposes HTTP API endpoints for direct chat access:

**Bot Health Check Ports**:
- Elena (Marine Biologist): http://localhost:9091
- Marcus (AI Researcher): http://localhost:9092  
- Ryan (Indie Game Developer): http://localhost:9093
- Dream (Mythological): http://localhost:9094
- Gabriel (Archangel): http://localhost:9095
- Sophia (Marketing Executive): http://localhost:9096
- Jake (Adventure Photographer): http://localhost:9097
- Aethys (Omnipotent): http://localhost:3007

**API Endpoints**:
```bash
# Health check
curl http://localhost:9091/health

# Bot information
curl http://localhost:9091/api/bot-info

# Send chat message
curl -X POST -H "Content-Type: application/json" \
  -d '{"message": "Hello!", "user_id": "your_user_id"}' \
  http://localhost:9091/api/chat
```

**Example Response**:
```json
{
  "response": "¡Hola! How can I help you today? 🌊",
  "timestamp": "2025-09-29T05:02:16.906209",
  "message_id": "web_1759122135.930857",
  "bot_name": "Elena Rodriguez [AI DEMO]",
  "success": true
}
```

### Web Interface Development

### Development Workflow

**DOCKER-FIRST DEVELOPMENT**: Container-based development is the PRIMARY workflow. Use `./multi-bot.sh` for all operations (auto-generated, don't edit manually).

### Adding New Bots
```bash
# 1. Copy template and customize
cp .env.template .env.newbot
# Edit .env.newbot with unique Discord token, bot name, character file
# CRITICAL: Set QDRANT_COLLECTION_NAME=whisperengine_memory_newbot for memory isolation

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

## Debugging & Validation

**Environment Validation**: Critical for troubleshooting setup issues:
```bash
# Validate complete environment setup
source .venv/bin/activate
python scripts/verify_environment.py  # Tests LLM endpoints, DB connections, Redis, Qdrant

# Quick bot health testing (all bots)
./scripts/quick_bot_test.sh        # HTTP API health checks for all running bots
```

**Debug Utilities**: Located in `utilities/` directory (NOT in main application flow):
```bash
# Debug memory system issues
cd utilities/debug && python debug_memory_manager.py

# Debug relationship issues  
cd utilities/debug && python debug_relationships.py

# Performance benchmarking
cd utilities/performance && python performance_comparison.py
```

**CDL Character Validation**: For character definition troubleshooting:
```bash
# Validate character file structure and content
python src/validation/validate_cdl.py structure characters/examples/elena.json
python src/validation/validate_cdl.py audit characters/examples/elena.json  
python src/validation/validate_cdl.py patterns characters/examples/elena.json

# Run complete CDL demo validation
python src/validation/demo_validation_system.py
```

## Memory System (Critical)

**Vector-Native Architecture**: Qdrant vector memory with fastembed is THE PRIMARY memory system:

**🚨 CRITICAL: Bot-Specific Collections** - Each bot has its own dedicated Qdrant collection:
```python
# ALWAYS use the correct collection name for each bot via environment variable
collection_name = os.getenv('QDRANT_COLLECTION_NAME')

# Current bot collection assignments:
# Elena: whisperengine_memory_elena (4,834 memories)
# Marcus: whisperengine_memory_marcus (2,738 memories)  
# Gabriel: whisperengine_memory_gabriel (2,897 memories)
# Sophia: whisperengine_memory_sophia (3,131 memories)
# Jake: whisperengine_memory_jake (1,040 memories)
# Ryan: whisperengine_memory_ryan (821 memories)
# Dream: whisperengine_memory_dream (916 memories)
# Aethys: chat_memories_aethys (6,630 memories)

# Memory operations are automatically isolated by collection
# Elena's memories stay in whisperengine_memory_elena
# Marcus's memories stay in whisperengine_memory_marcus
# No cross-bot memory leakage possible
```

```python
# ALWAYS use vector/semantic search before manual Python analysis
memories = await memory_manager.retrieve_relevant_memories(
    user_id=user_id, query=message, limit=10
)

# NEW: Fidelity-first memory retrieval with graduated filtering (Elena bot has this)
memories = await memory_manager.retrieve_relevant_memories_fidelity_first(
    user_id=user_id, 
    query=message, 
    top_k=15,
    full_fidelity=True,
    intelligent_ranking=True,
    preserve_character_nuance=True
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

**ALWAYS use Bot Segmentation** - Filter by bot_name AND use correct collection:
```python
# ✅ CORRECT: Bot-specific collection isolation (PRIMARY method)
collection_name = os.getenv('QDRANT_COLLECTION_NAME')  # Each bot has unique collection

# ✅ CORRECT: All operations must also filter by bot_name within collection
must_conditions = [
    models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id)),
    models.FieldCondition(key="bot_name", match=models.MatchValue(value=get_normalized_bot_name_from_env()))
]

# ✅ CORRECT: Store with bot segmentation and collection isolation
payload = {
    "user_id": user_id,
    "bot_name": get_normalized_bot_name_from_env(),  # CRITICAL: Bot isolation
    "content": content,
    "memory_type": memory_type
}

# ❌ WRONG: Missing bot_name segmentation
payload = {"user_id": user_id, "content": content}  # Will leak across bots!

# ❌ WRONG: Using wrong collection
collection_name = "whisperengine_memory"  # Don't hardcode - use environment variable!
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

**Bot-Specific Memory Isolation**: Each bot has completely isolated memories via dedicated collections:
```python
# CRITICAL: Each bot uses its own dedicated Qdrant collection
# Environment variable QDRANT_COLLECTION_NAME determines collection:
# - Elena: whisperengine_memory_elena (4,834 memories)
# - Marcus: whisperengine_memory_marcus (2,738 memories)
# - Dream: whisperengine_memory_dream (916 memories)
# - Aethys: chat_memories_aethys (6,630 memories)
# - etc.

# Memory operations are collection-isolated + bot_name filtered
collection_name = os.getenv('QDRANT_COLLECTION_NAME')  # Bot-specific collection
# Memory filtering uses: collection + user_id + bot_name + memory_type
# Complete conversation isolation between bots at collection level
```

**Multi-Bot Memory Intelligence**:
```python
# Query across all bots (admin/debugging)
querier = create_multi_bot_querier()
all_results = await querier.query_all_bots("user preferences", "user123")

# Cross-bot analysis and insights
analysis = await querier.cross_bot_analysis("user123", "conversation style")
```

## Prompt Building Pipeline (Fidelity-First Architecture)

**OptimizedPromptBuilder**: Core prompt assembly with fidelity preservation:
```python
from src.prompts.optimized_prompt_builder import create_optimized_prompt_builder

# Fidelity-first prompt building - preserves character nuance until last resort
prompt_builder = create_optimized_prompt_builder(
    max_words=1000,
    llm_client=llm_client,
    memory_manager=memory_manager
)

# Build with graduated optimization
optimized_prompt = await prompt_builder.build_optimized_prompt(
    system_prompt=cdl_enhanced_prompt,
    conversation_context=conversation_context,
    user_message=user_message,
    full_fidelity=True,  # CRITICAL: Start with complete context
    preserve_character_details=True,
    intelligent_trimming=True
)
```

**HybridContextDetector**: Vector-enhanced context detection:
```python
from src.prompts.hybrid_context_detector import create_hybrid_context_detector

# Vector-enhanced pattern recognition leveraging existing Qdrant infrastructure
context_detector = create_hybrid_context_detector(memory_manager=memory_manager)

# Multi-method context detection with vector boost
context_result = context_detector.detect_context_patterns(
    message=user_message,
    conversation_history=recent_messages,
    vector_boost=True,  # CRITICAL: Use vector intelligence
    confidence_threshold=0.7
)
```

**Vector Enhancement Patterns**: Leverage existing Qdrant instead of separate NLP:
```python
# ✅ CORRECT: Use existing vector infrastructure
vector_context = await memory_manager.search_similar_contexts(
    query=current_context,
    context_type="conversation_pattern",
    bot_specific=True  # Elena's patterns vs Marcus's patterns
)

# ❌ WRONG: Building separate NLP pipelines
separate_nlp_analyzer = CustomNLPProcessor()  # Don't do this!
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
    character_file=character_file,  # DYNAMIC: Load from environment/config
    user_id=user_id,
    message_content=message
)
```

## Anti-Phantom Feature Guidelines

**Fidelity-First Development**: Before marking any feature "complete":
- ✅ Verify it preserves conversation quality and character authenticity
- ✅ Confirm it's integrated with vector-native memory system
- ✅ Test it maintains character consistency across conversation contexts
- ✅ Ensure it follows graduated optimization (full fidelity → intelligent compression)
- ✅ **NO ENVIRONMENT VARIABLE FLAGS** - features work by default in development
- ✅ Document integration points in handler classes

**🚨 DEVELOPMENT ANTI-PATTERNS TO AVOID:**
- ❌ Environment variable feature flags (`ENABLE_X=true`) 
- ❌ Premature optimization that sacrifices character nuance
- ❌ Building separate NLP pipelines instead of using existing Qdrant infrastructure
- ❌ Features that are "implemented" but require special configuration to work
- ❌ Silent fallbacks that mask real failures
- ❌ "Phantom features" that exist in code but aren't accessible to users
- ❌ **CHARACTER-SPECIFIC HARDCODED LOGIC** (bot names, personalities, character assumptions)
- ❌ Hardcoded bot lists or character references in Python code
- ❌ Embedding personality traits directly in code instead of using CDL system
- ❌ Static character assumptions that break multi-bot architecture

**Vector-First Analysis**: Before writing manual analysis code:
- ✅ Check if vector memory can provide insights via semantic search
- ✅ Use existing Qdrant infrastructure for semantic processing
- ✅ Leverage bot-specific memory segmentation (Elena's memories stay with Elena)
- ✅ Apply fidelity-first principles: full context → intelligent filtering
- ✅ Only write manual Python if vector approach is insufficient

**Fidelity Preservation Patterns**: Core development philosophy:

```python
# ✅ CORRECT: Fidelity-first approach
def process_conversation_context(context, max_size):
    # Start with full fidelity
    full_context = build_complete_context(context)
    
    # Only optimize if absolutely necessary
    if estimate_size(full_context) > max_size:
        return intelligent_compression(full_context, preserve_character=True)
    
    return full_context

# ❌ WRONG: Premature optimization
def process_conversation_context(context, max_size):
    # Immediately truncates without considering character impact
    return context[:max_size]
```

## Key Directories

- `src/core/` - Bot initialization (`DiscordBotCore`, `ModularBotManager`)
- `src/memory/` - Vector-native memory system with multi-bot querying
- `src/handlers/` - Discord command handlers (modular architecture)
- `src/prompts/` - CDL integration and prompt management
- `src/identity/` - Universal Identity system (NEW) - platform-agnostic user management
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
- `characters/examples/*.json` - Character definitions (elena.json, marcus.json, jake.json, dream.json, aethys.json, ryan.json, gabriel.json, sophia.json)
- `src/characters/cdl/parser.py` - CDL parser and validator
- `src/prompts/cdl_ai_integration.py` - Integrates CDL with AI pipeline and emotional intelligence
- Each character has unique personality, occupation, communication style, and values

**CDL Integration Pattern**:
```python
from src.prompts.cdl_ai_integration import CDLAIPromptIntegration
cdl_integration = CDLAIPromptIntegration()
system_prompt = await cdl_integration.create_character_aware_prompt(
    character_file=character_file,  # DYNAMIC: Load from environment/config
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

## Data Flow Architecture (Fidelity-First)

**End-to-End Pipeline**: Conversation fidelity preserved throughout:

```
Discord Message → Security Validation → Memory Retrieval → 
CDL Character Enhancement → Fidelity-First Prompt Building → 
Vector-Enhanced Context Detection → LLM Generation → 
Character Consistency Validation → Memory Storage → Platform Delivery
```

**Key Fidelity Preservation Points**:

1. **Memory Retrieval**: Start with full semantic search, intelligent filtering only if needed
2. **Character Enhancement**: Apply complete CDL personality before optimization  
3. **Prompt Building**: Use graduated optimization preserving character nuance
4. **Context Detection**: Vector-enhanced pattern recognition using existing infrastructure
5. **Response Validation**: Ensure character consistency post-generation

**Performance vs Fidelity Balance**:
```python
# ✅ CORRECT: Graduated optimization approach
async def build_conversation_context(memories, character_data, conversation_history):
    # Phase 1: Full fidelity assembly
    full_context = assemble_complete_context(memories, character_data, conversation_history)
    
    # Phase 2: Intelligent compression only if necessary
    if estimate_tokens(full_context) > context_limit:
        return apply_smart_compression(full_context, preserve_character=True)
    
    return full_context

# ❌ WRONG: Immediate truncation without fidelity consideration
async def build_conversation_context(memories, character_data, conversation_history):
    return truncate_to_limit(memories[:5], character_data[:100], conversation_history[:10])
```
```

## Development Workflow

**DOCKER-FIRST DEVELOPMENT**: Container-based development is the PRIMARY workflow. Native Python is no longer practical for full system functionality.

**CRITICAL**: The legacy `./bot.sh` script has been **DEPRECATED**. Use `./multi-bot.sh` for all operations:

**Multi-Bot Control Script**: Use `./multi-bot.sh` for all operations:
```bash
./multi-bot.sh start elena        # Start Elena bot (marine biologist)
./multi-bot.sh start marcus       # Start Marcus bot (AI researcher) 
./multi-bot.sh start jake         # Start Jake bot (adventure photographer)
./multi-bot.sh start dream        # Start Dream bot (mythological entity)
./multi-bot.sh start aethys       # Start Aethys bot (omnipotent entity)
./multi-bot.sh start ryan         # Start Ryan bot (indie game developer)
./multi-bot.sh start gabriel      # Start Gabriel bot
./multi-bot.sh start sophia       # Start Sophia bot (marketing executive)
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
- `.env.jake` - Jake Sterling (Adventure Photographer)
- `.env.dream` - Dream of the Endless (Mythological)
- `.env.aethys` - Aethys (Omnipotent Entity)
- `.env.ryan` - Ryan Chen (Indie Game Developer)
- `.env.gabriel` - Gabriel (Archangel)
- `.env.sophia` - Sophia Blake (Marketing Executive)
- Each file needs unique `DISCORD_BOT_TOKEN` and `HEALTH_CHECK_PORT`

## Current System Status

**Active Infrastructure** (as of current deployment):
- ✅ **Multi-Bot System**: 8+ character bots running simultaneously (Elena, Marcus, Jake, Dream, Aethys, Ryan, Gabriel, Sophia)
- ✅ **Discord-First Architecture**: Pure Discord bot system, no web interface
- ❌ **Individual Bot APIs**: Chat API endpoints have been removed - Discord-only functionality
- ✅ **Vector Memory**: Qdrant-powered with 384D embeddings, named vector support, bot-specific isolation
- ✅ **Universal Identity**: Platform-agnostic user management with account discovery
- ✅ **CDL Character System**: JSON-based personality definitions, integrated AI identity filtering
- ✅ **Health Monitoring**: Container health checks, graceful shutdown, performance monitoring

**Tested Working Features**:
- Multi-bot Discord conversations with persistent memory
- Health endpoints for container orchestration status
- Vector-based semantic memory retrieval across conversations
- CDL-driven character personality responses
- Bot-specific memory isolation (Elena's memories stay with Elena)
- Template-based configuration management
- CDL-driven character personality responses
- Bot-specific memory isolation (Elena's memories stay with Elena)
- Health endpoints for container orchestration
- Template-based configuration management

**Development Commands Verified Working**:
```bash
./multi-bot.sh start all     # ✅ Starts all 8+ bots + infrastructure
./multi-bot.sh status        # ✅ Shows container health status
./multi-bot.sh logs elena    # ✅ Real-time bot logs
curl http://localhost:9091/api/chat  # ✅ Individual bot API endpoints
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
- `PerformanceCommands` - Performance analysis and optimization
- `WebSearchCommandHandlers` - Web search integration (available)

**Currently Disabled** (over-engineered or obsolete):
- `AdminCommandHandlers` - Disabled (over-engineered)
- `MemoryCommandHandlers` - Disabled (obsolete API)
- `CDLTestCommands` - Disabled (dev testing only)
- `PrivacyCommandHandlers` - Disabled (privacy and data management)
- `MonitoringCommands` - Disabled (system monitoring and performance)
- `LLMToolCommandHandlers` - Disabled (LLM-powered tool commands)
- `LLMSelfMemoryHandlers` - **REMOVED** (replaced with structured CDL personal knowledge integration)

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

**Character Agnosticism**: ALL Python components must be character-agnostic:
- Use `get_normalized_bot_name_from_env()` for bot identification
- Load character data dynamically from CDL JSON files
- Never hardcode character names, personalities, or bot-specific behavior
- Features must work for ANY character via CDL integration
- Use environment variables for bot identification, never literal strings

**CDL Personal Knowledge Integration**: For personal questions (relationships, family, career, etc.):
- Use structured CDL section extraction in `src/prompts/cdl_ai_integration.py`
- Question type detection categorizes queries and pulls relevant CDL sections
- Structured data integration follows same patterns as Big Five personality, life phases
- NO separate CDL Query Helper - personal knowledge is integrated into prompt building
- Zero latency direct JSON access, no LLM API calls for character knowledge

**Fidelity-First Development Patterns**: Core architectural implementations:

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

# ✅ Apply fidelity-first prompt building
from src.prompts.optimized_prompt_builder import create_optimized_prompt_builder
prompt_builder = create_optimized_prompt_builder(memory_manager=memory_manager)
optimized_prompt = await prompt_builder.build_optimized_prompt(
    system_prompt=system_prompt,
    conversation_context=conversation_context,
    user_message=user_message,
    full_fidelity=True,  # CRITICAL: Preserve character nuance
    preserve_character_details=True,
    intelligent_trimming=True
)

# ✅ Use vector-enhanced context detection
from src.prompts.hybrid_context_detector import create_hybrid_context_detector
context_detector = create_hybrid_context_detector(memory_manager=memory_manager)
context_result = context_detector.detect_context_patterns(
    message=user_message,
    conversation_history=recent_messages,
    vector_boost=True,  # Leverage existing Qdrant infrastructure
    confidence_threshold=0.7
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

**Error Handling Patterns**: All async operations use production error handling:
```python
from src.utils.production_error_handler import handle_errors, ErrorCategory, ErrorSeverity

@handle_errors(category=ErrorCategory.MEMORY, severity=ErrorSeverity.HIGH)
async def memory_operation():
    # Automatic error handling, logging, and graceful degradation
```

**Configuration Pattern**: Use TYPE-based environment variables, not boolean flags:
```python
# ✅ CORRECT: Type-based configuration
MEMORY_SYSTEM_TYPE=vector           # "vector", "hierarchical", "test_mock"
LLM_CLIENT_TYPE=openrouter         # "openrouter", "local", "mock"

# ❌ WRONG: Boolean feature flags for local code
ENABLE_MEMORY_SYSTEM=true          # Creates phantom features
```

**Testing Commands**: Essential testing and validation workflows:
```bash
# Environment validation (CRITICAL for troubleshooting)
source .venv/bin/activate && python scripts/verify_environment.py

# Bot health testing (all running bots)
./scripts/quick_bot_test.sh

# Container-based testing (recommended)
docker exec whisperengine-elena-bot python -m pytest tests/unit/

# Quick test commands for specific components
python tests/QUICK_TEST_COMMANDS.md  # See file for component testing
```

**Error Handling Patterns**: All async operations use production error handling:
```python
from src.utils.production_error_handler import handle_errors, ErrorCategory, ErrorSeverity

@handle_errors(category=ErrorCategory.MEMORY, severity=ErrorSeverity.HIGH)
async def memory_operation():
    # Automatic error handling, logging, and graceful degradation
```

**Configuration Pattern**: Use TYPE-based environment variables, not boolean flags:
```python
# ✅ CORRECT: Type-based configuration
MEMORY_SYSTEM_TYPE=vector           # "vector", "hierarchical", "test_mock"
LLM_CLIENT_TYPE=openrouter         # "openrouter", "local", "mock"

# ❌ WRONG: Boolean feature flags for local code
ENABLE_MEMORY_SYSTEM=true          # Creates phantom features
```

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
- `utilities/` - Debug and performance tools (NOT in main app flow)
- `scripts/` - Configuration generation and environment validation

## Recent Major Changes

**Universal Identity & Account Discovery** (NEW): Introduced platform-agnostic user identity system allowing users to interact via Discord or future platforms while maintaining consistent memory. Enhanced account discovery prevents duplicate accounts.

**Template-Based Multi-Bot System** (Complete): Migrated from programmatic Docker Compose generation to safe template-based approach. Infrastructure versions now pinned (PostgreSQL 16.4, Redis 7.4, Qdrant v1.15.4) to prevent breaking updates.

**Multi-Bot Architecture** (Complete): Introduced shared infrastructure supporting multiple character bots with isolated personalities. See `MULTI_BOT_SETUP.md`.

**CDL Character System** (Complete): Migrated from markdown prompts to JSON-based Character Definition Language for structured personality modeling.

**Architecture Simplification** (Complete): Eliminated complex try/except ImportError patterns, replaced with clean factory patterns. See `ARCHITECTURE_SIMPLIFICATION_COMPLETE.md`.

**Memory Migration** (Complete): Migrated to vector-native memory with Qdrant + fastembed. Default: `MEMORY_SYSTEM_TYPE=vector`.

**Factory Pattern Adoption**: All major systems now use factory pattern for dependency injection and environment flexibility.

**Fidelity-First Prompt Building Architecture** (NEW): Implemented graduated optimization system that preserves character nuance and conversation quality as primary design constraint. Includes OptimizedPromptBuilder with intelligent context assembly, HybridContextDetector with vector-enhanced pattern recognition, and vector-first analysis patterns that leverage existing Qdrant infrastructure instead of building separate NLP pipelines.

**Phase 2.1 Fidelity-First Memory Management** (Complete): Implemented and tested comprehensive fidelity-first memory retrieval with graduated filtering, character-aware ranking, and intelligent memory tier management. Elena bot has the latest implementation - other bots may not have these updates yet. Use Elena for testing memory-related features.

**Phase 4 Integration** (Complete): Advanced conversation intelligence with production optimization components fully integrated and operational.