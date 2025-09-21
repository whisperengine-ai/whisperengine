# WhisperEngine AI Agent Instructions

## Architecture Overview

WhisperEngine is a production-ready Discord AI companion bot with vector-native memory, personality systems, and enterprise features. The architecture follows a **factory pattern** with **protocol-based dependency injection** for A/B testing and environment flexibility.

### Core Architecture Patterns

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

## Memory System (Critical)

**Vector-Native Architecture**: Migrated from hierarchical (Redis/PostgreSQL/ChromaDB) to unified vector storage (Qdrant). See `MEMORY_ARCHITECTURE_V2.md` for details.

**Key Files**:
- `src/memory/core/storage_abstraction.py` - HierarchicalMemoryManager (current production)
- `src/memory/memory_protocol.py` - Protocol and factory for A/B testing
- `src/memory/hierarchical_memory_adapter.py` - Protocol adapter

**Memory Operations**:
```python
# Always use async methods
await memory_manager.store_conversation(user_id, user_message, bot_response)
await memory_manager.retrieve_relevant_memories(user_id, query, limit=10)
await memory_manager.get_conversation_history(user_id, limit=10)
```

## Development Workflow

**Entry Point**: `run.py` (infrastructure setup) → `src/main.py` (bot logic)

**Python Virtual Environment**: ALWAYS use the virtual environment for Python commands:
```bash
source .venv/bin/activate  # Required before any Python operations
python run.py              # ✅ Correct - uses venv Python
python3 run.py             # ✅ Also correct when venv activated
```

**Bot Control Script**: Use `./bot.sh` for all operations:
```bash
./bot.sh start dev          # Development mode with hot reload
./bot.sh start infrastructure  # Database-only for native Python development
./bot.sh logs               # Follow logs
./bot.sh stop               # Graceful shutdown
```

**Testing**: Rebuilt infrastructure with proper mocking:
```bash
source .venv/bin/activate   # Activate venv first
pytest tests/unit/          # Unit tests with full mocking
pytest tests/integration/   # Integration tests (future)
```

**Setup**: Use setup script to create virtual environment:
```bash
./setup.sh                 # Creates .venv and installs dependencies
source .venv/bin/activate   # Activate for development
```

**Docker Development**:
```bash
docker-compose -f docker-compose.dev.yml up    # Development with hot reload
docker-compose up qdrant                       # Vector database only
```

## Production System Architecture

**Phase 4 Integration**: Advanced conversation intelligence with optimized components:
- `src/intelligence/phase_integration_optimizer.py` - Multi-phase processing coordination
- `src/integration/production_system_integration.py` - Production-grade component integration
- Phase 4.1: Memory-triggered moments
- Phase 4.2: Advanced thread management 
- Phase 4.3: Proactive engagement engine

**Production Components** (when available):
- `OptimizedPhase4Engine` - Multi-core processing (310+ messages/sec)
- `FaissMemoryEngine` - Ultra-fast vector search (3-5x speedup)
- `VectorizedEmotionEngine` - High-throughput sentiment analysis (11,440+ emotions/sec)
- `AdvancedMemoryBatcher` - Database efficiency with caching
- `ConcurrentConversationManager` - 1000+ simultaneous sessions

## Handler System

**Modular Handler Architecture**: All Discord commands use handler classes in `src/handlers/`:
- `AdminCommandHandlers` - Admin operations and backups
- `MemoryCommandHandlers` - Memory system commands
- `VoiceCommandHandlers` - Voice functionality
- `StatusCommandHandlers` - Health and status monitoring
- `MultiEntityCommandHandlers` - Character management

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

**Component Removal**: When removing obsolete components, update all references including:
- Factory imports and creation calls
- Protocol type annotations
- Integration adapters
- Test files and utilities

## Key Directories

- `src/core/` - Bot initialization and Discord integration
- `src/handlers/` - Discord command handlers (modular architecture)
- `src/memory/` - Vector-native memory system
- `src/llm/` - LLM client abstraction with concurrent safety
- `src/conversation/` - Context management and engagement
- `src/personality/` - Character systems and emotion intelligence
- `src/intelligence/` - Phase 4 integration and optimization engines
- `src/integration/` - Production system integration components
- `src/security/` - Production security and privacy
- `src/utils/` - Cross-cutting concerns and monitoring

## Recent Major Changes

**Architecture Simplification** (Complete): Eliminated complex try/except ImportError patterns, replaced with clean factory patterns. See `ARCHITECTURE_SIMPLIFICATION_COMPLETE.md`.

**Memory Migration** (In Progress): Moving from hierarchical to vector-native memory. Production uses hierarchical, vector system ready for A/B testing.

**Factory Pattern Adoption**: All major systems now use factory pattern for dependency injection and environment flexibility.

**Phase 4 Integration** (Complete): Advanced conversation intelligence with production optimization components fully integrated and operational.