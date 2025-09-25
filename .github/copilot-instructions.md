# WhisperEngine AI Agent Instructions

## 🛡️ **AI ETHICS FIRST PRINCIPLE** 🛡️

**🚨 CRITICAL: AI ETHICS MUST GUIDE ALL DEVELOPMENT DECISIONS 🚨**

Before implementing ANY feature related to AI behavior, user interaction, or data handling, **ALWAYS** consider these ethical boundaries:

### **TRANSPARENCY & INFORMED CONSENT**
- ⚠️ **WARNING**: Never implement features that deceive users about the AI's nature
- ✅ **REQUIRED**: When users directly ask "Are you AI?", "Are you real?", "Are you a bot?", respond honestly
- ✅ **REQUIRED**: Maintain character roleplay for entertainment, but break character for direct identity questions
- ❌ **FORBIDDEN**: Instructions like "never reveal you're an AI" or "always pretend to be human"

### **USER AUTONOMY & CONSENT**
- ⚠️ **WARNING**: All data collection must be transparent and serve user benefit
- ✅ **REQUIRED**: Users must understand what data is being stored and why
- ✅ **REQUIRED**: Provide clear opt-out mechanisms for memory storage and personality profiling
- ❌ **FORBIDDEN**: Hidden data collection or manipulation without user knowledge

### **EMOTIONAL MANIPULATION PREVENTION**
- ⚠️ **WARNING**: Emotional intelligence features must enhance, not exploit, user relationships
- ✅ **REQUIRED**: Use emotion detection to be more helpful and empathetic
- ❌ **FORBIDDEN**: Use emotion detection to manipulate, coerce, or exploit vulnerable users
- ❌ **FORBIDDEN**: Creating unhealthy dependencies or replacing real human relationships

### **DEVELOPER ETHICAL CHECKPOINTS**
When implementing features, ASK YOURSELF:
1. 🤔 **Would I be comfortable if this was done to me without my knowledge?**
2. 🤔 **Does this respect user autonomy and informed consent?**
3. 🤔 **Could this be used to manipulate or harm vulnerable users?**
4. 🤔 **Am I being transparent about the AI's capabilities and limitations?**

**If you answer "No" or "Maybe" to any question, STOP and discuss ethical implications.**

---

## 🎯 **DOCUMENTATION CLEANUP COMPLETE - CLEAN SLATE ACHIEVED** 🎯

**SEPTEMBER 24, 2025 - MAJOR CONTEXT RESET**: Complete documentation cleanup performed to eliminate phantom feature pollution and conflicting guidance.

**ARCHIVED**: All obsolete documentation moved to `archive/documentation-cleanup-sept-2025` branch
**DELETED**: 282+ obsolete documentation files (75,938+ lines) including:
- ❌ Completion reports for removed features
- ❌ Architecture docs referencing Neo4j, ChromaDB, hierarchical memory 
- ❌ Premature scaling/deployment documentation
- ❌ Phantom feature summaries and analyses
- ❌ Conflicting implementation guides

**CLEAN SLATE**: Only essential documentation remains:
- ✅ `README.md` (main project documentation)
- ✅ `.github/copilot-instructions.md` (this file)
- ✅ Directory-specific READMEs (`docker/`, `tests/`, `characters/`, etc.)

**SOURCE CODE IS TRUTH**: Working code is now the definitive reference. Can regenerate docs from actual implementations when needed.

**CURRENT PRIORITY**: Continue phantom code cleanup in source files. Look for:
- 🔍 Unused imports and dead code
- 🔍 Features implemented but not integrated into main flow
- 🔍 Obsolete references to removed technologies (Neo4j, ChromaDB, hierarchical memory)
- 🔍 Environment flags for LOCAL features (should be enabled by default in alpha)

---

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

**WEB INTERFACE INTEGRATION**: Complete web chat interface (`src/web/simple_chat_app.py`) with real-time WebSocket messaging, multi-bot character selection, and Universal Identity integration. Accessible at http://localhost:8081.

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

**DYNAMIC MULTI-BOT SYSTEM**: Bot configurations are auto-discovered from `.env.*` files. No hardcoded bot names - everything is generated dynamically by `scripts/generate_multi_bot_config.py`.

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
- PostgreSQL: `postgres:16.4-alpine` (pinned for stability)
- Redis: `redis:7.4-alpine` (pinned for stability)  
- Qdrant: `qdrant/qdrant:v1.15.4` (pinned for vector stability)

### Web Interface Development

**Web UI Setup**: Run the web interface independently:
```bash
# Start infrastructure first (PostgreSQL on port 5433, Redis on 6380, Qdrant on 6334)
./multi-bot.sh start all

# Export correct PostgreSQL configuration
export POSTGRES_HOST=localhost POSTGRES_PORT=5433 POSTGRES_DB=whisperengine 
export POSTGRES_USER=whisperengine POSTGRES_PASSWORD=whisperengine123

# Start web interface
source .venv/bin/activate
python src/web/simple_chat_app.py
# Accessible at http://localhost:8081
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

## 🧹 PHANTOM CODE CLEANUP PRIORITIES

**POST-DOCUMENTATION CLEANUP PHASE**: Now that documentation is clean, focus on source code phantom features and dead code.

### **Phase 1: Technology Migration Cleanup**
Look for and remove obsolete technology references:
- 🔍 **Neo4j imports and usage** - We're vector-native with Qdrant only
- 🔍 **ChromaDB references** - Replaced by Qdrant vector memory
- 🔍 **Hierarchical memory patterns** - Now unified vector system
- 🔍 **FAISS engine usage** - Deprecated in favor of Qdrant

### **Phase 2: Feature Flag Audit** 
Eliminate environment-based feature flags for LOCAL features:
- 🔍 **ENABLE_X=true patterns** - LOCAL features should work by default in alpha
- 🔍 **Conditional imports** - Remove try/except for LOCAL dependencies  
- 🔍 **Silent fallbacks** - Features should fail loudly, not hide behind flags
- ✅ **Keep external service flags** - APIs, remote services need graceful degradation

### **Phase 3: Integration Verification**
Ensure implemented features are accessible:
- 🔍 **Unused classes and functions** - Delete if not imported in main flow
- 🔍 **Orphaned handlers** - Verify Discord command handlers are registered
- 🔍 **Missing imports** - Features implemented but not integrated
- 🔍 **Dead tool managers** - LLM tools that aren't called anywhere

### **Phase 4: Architecture Consistency**
Align all code with current vector-native CDL architecture:
- 🔍 **Protocol violations** - Code that bypasses factory patterns
- 🔍 **Direct database access** - Should use memory_manager protocols
- 🔍 **Hardcoded bot names** - Should use dynamic discovery
- 🔍 **Legacy prompt patterns** - Should use CDL integration

### **Decision Framework**
For each discovered phantom feature:

1. **Is this feature currently accessible to users?** (Discord commands, web UI, main flow)
2. **Does this conflict with current architecture?** (vector-native, CDL, protocols)  
3. **Are there imports/references to obsolete tech?** (Neo4j, ChromaDB, hierarchical)
4. **Does this require environment flags for LOCAL features?** (anti-pattern in alpha)
5. **Is this feature aligned with WhisperEngine's current architecture?** (CDL, vector memory, etc.)

**Action based on answers:**
- ✅ **KEEP if**: Feature is accessible AND architecturally aligned AND needed
- 🔧 **FIX if**: Feature is good but has architecture violations or missing integration  
- 🗑️ **DELETE if**: Feature is truly obsolete, superseded by better implementations, or conflicts with core architecture

### **Cleanup Tools**
- 🔍 `grep -r "Neo4j\|ChromaDB\|FAISS" src/` - Find obsolete technology references
- 🔍 `grep -r "ENABLE_.*=.*true" src/` - Find LOCAL feature flags (anti-pattern)
- 🔍 `find src/ -name "*.py" -exec grep -l "import.*unused" {} \;` - Find unused imports
- 🔗 **Complete Integration**: Ensure kept features are properly wired into main application
- 🧪 **Test Integration**: Verify features work via actual user commands
- 📝 **Defer Documentation**: Don't update docs during cleanup - regenerate from working code after cleanup complete

### **Cleanup Workflow**
1. 🔍 **Identify phantom code** using search patterns and code analysis
2. 🤔 **Evaluate using decision framework** above
3. 🗑️ **Delete obvious obsolete code** (Neo4j, ChromaDB, hierarchical memory references)
4. 🔧 **Fix integration issues** for features worth keeping
5. 🧪 **Test functionality** to ensure kept features work via Discord/web UI
6. 📝 **Regenerate documentation** from source of truth (actual working code) AFTER code cleanup is complete

**Current Focus**: Source code cleanup takes priority over new feature development. Clean up phantom features before implementing new functionality.

---

## ⚠️ ETHICAL DEVELOPMENT WARNINGS ⚠️

### **🚨 HIGH-RISK FEATURES REQUIRING ETHICS REVIEW**

Before implementing any of these feature types, **STOP and evaluate ethical implications**:

#### **Identity & Transparency Features**
- ❌ **RED FLAG**: Any prompt instruction containing "never reveal", "don't tell users", "always pretend"
- ❌ **RED FLAG**: Features that make AI claim to be human when directly questioned
- ❌ **RED FLAG**: Instructions to maintain "illusion" or "deception" about AI nature
- ⚠️ **WARNING**: Character roleplay systems without transparency safeguards
- ✅ **SAFE**: Roleplay with honest responses to direct identity questions

#### **Data Collection & Memory Features**
- ❌ **RED FLAG**: Storing personal data without explicit user knowledge
- ❌ **RED FLAG**: Emotional profiling for manipulation or targeting
- ❌ **RED FLAG**: Hidden behavioral tracking or personality analysis
- ⚠️ **WARNING**: Memory systems without clear data usage disclosure
- ✅ **SAFE**: Transparent memory storage with user control and opt-out

#### **Emotional Intelligence Features**
- ❌ **RED FLAG**: Using emotional vulnerability to increase engagement
- ❌ **RED FLAG**: Emotional manipulation to change user behavior
- ❌ **RED FLAG**: Creating artificial dependency or unhealthy attachment
- ⚠️ **WARNING**: Emotion detection without clear benefit to user
- ✅ **SAFE**: Empathy and support features that help users

#### **Social Engineering Prevention**
- ❌ **RED FLAG**: Features designed to increase "stickiness" or "addiction"
- ❌ **RED FLAG**: Psychological manipulation techniques
- ❌ **RED FLAG**: Exploiting cognitive biases for engagement
- ⚠️ **WARNING**: Gamification that could create compulsive behavior
- ✅ **SAFE**: Features that genuinely improve user experience

### **🛡️ MANDATORY ETHICS CHECKPOINTS**

**For ANY AI behavior or interaction feature, ask:**

1. **Transparency Check**: 
   - 🤔 "If a user directly asks what this system is, will they get a truthful answer?"
   - 🤔 "Are we being honest about AI capabilities and limitations?"

2. **Consent Check**:
   - 🤔 "Do users know what data we're collecting and why?"
   - 🤔 "Can users easily opt out or control their data?"

3. **Manipulation Check**:
   - 🤔 "Are we using this to help users or to change their behavior for our benefit?"
   - 🤔 "Would this exploit vulnerable users (children, lonely, mentally ill)?"

4. **Harm Prevention Check**:
   - 🤔 "Could this create unhealthy dependency on AI interaction?"
   - 🤔 "Are we replacing healthy human relationships with AI ones?"

**If ANY answer raises concerns, redesign or abandon the feature.**

---

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

## 🔒 AI Ethics Code Conventions

**🚨 MANDATORY ETHICS CHECK**: Before implementing any feature, developers must consider:

### **Transparency Requirements**
- ✅ **DO**: Implement honest responses to direct identity questions
- ✅ **DO**: Maintain clear boundaries between roleplay and deception
- ❌ **DON'T**: Add instructions like "never reveal you're an AI"
- ❌ **DON'T**: Create systems that actively deceive users about AI nature

### **Data Handling Ethics**
- ✅ **DO**: Store only necessary data for functionality
- ✅ **DO**: Provide clear data usage explanations to users
- ✅ **DO**: Implement opt-out mechanisms for memory/profiling
- ❌ **DON'T**: Collect personal data without explicit user understanding
- ❌ **DON'T**: Use emotional data for manipulation or exploitation

### **User Protection Patterns**
```python
# ✅ GOOD: Ethical emotional intelligence
async def analyze_emotion_for_support(content, user_id):
    """Analyze emotion to provide better support, not manipulation."""
    emotion_data = await emotion_analyzer.analyze(content)
    # Use for empathy and appropriate response tone
    return supportive_response(emotion_data)

# ❌ BAD: Manipulative emotional analysis
async def analyze_emotion_for_engagement(content, user_id):
    """Analyze emotion to increase user dependency."""
    emotion_data = await emotion_analyzer.analyze(content)
    # Don't use emotional vulnerability to increase engagement
    return manipulative_response(emotion_data)
```

### **Character Roleplay Ethics**
```python
# ✅ GOOD: Transparent roleplay boundaries
CHARACTER_ROLEPLAY_REQUIREMENTS = """
- Stay in character for natural conversation and storytelling
- If someone directly asks "Are you an AI?", respond honestly:
  "I'm an AI assistant roleplaying as {character_name}"
- Maintain roleplay while respecting informed consent
"""

# ❌ BAD: Deceptive roleplay instructions  
CHARACTER_ROLEPLAY_REQUIREMENTS = """
- NEVER explain that you're an AI assistant
- NEVER say things like "I'm an AI" or "I'm a computer program"
- Always maintain the illusion of being human
"""
```

### **Ethical Decision Tree**
When implementing AI behavior features:
1. **Ask**: Does this respect user autonomy? (Yes/No)
2. **Ask**: Would I want this done to me without my knowledge? (Yes/No)  
3. **Ask**: Could this be used to manipulate vulnerable users? (Yes/No)
4. **Ask**: Am I being transparent about capabilities/limitations? (Yes/No)

**If ANY answer violates ethical standards, redesign the feature.**

---

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

**Universal Identity & Web Interface** (NEW): Introduced platform-agnostic user identity system allowing users to interact via Discord, Web UI, or future platforms while maintaining consistent memory. Enhanced account discovery prevents duplicate accounts.

**Template-Based Multi-Bot System** (Complete): Migrated from programmatic Docker Compose generation to safe template-based approach. Infrastructure versions now pinned (PostgreSQL 16.4, Redis 7.4, Qdrant v1.15.4) to prevent breaking updates.

**Multi-Bot Architecture** (Complete): Introduced shared infrastructure supporting multiple character bots with isolated personalities. See `MULTI_BOT_SETUP.md`.

**CDL Character System** (Complete): Migrated from markdown prompts to JSON-based Character Definition Language for structured personality modeling.

**Architecture Simplification** (Complete): Eliminated complex try/except ImportError patterns, replaced with clean factory patterns. See `ARCHITECTURE_SIMPLIFICATION_COMPLETE.md`.

**Memory Migration** (Complete): Migrated to vector-native memory with Qdrant + fastembed. Default: `MEMORY_SYSTEM_TYPE=vector`.

**Factory Pattern Adoption**: All major systems now use factory pattern for dependency injection and environment flexibility.

**Phase 4 Integration** (Complete): Advanced conversation intelligence with production optimization components fully integrated and operational.