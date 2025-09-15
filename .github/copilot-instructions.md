# WhisperEngine AI - Copilot Instructions

## 🎭 Project Overview

WhisperEngine is a privacy-first AI conversation platform that can run as both a Discord bot and a standalone desktop application. The system features sophisticated AI memory, emotional intelligence, and personality adaptation, designed around "Dream of the Endless" from Neil Gaiman's Sandman series.

**Core Deployment Modes:**
- **Discord Bot** (`python run.py`) - Full AI-powered Discord bot with advanced memory
- **Desktop App** (`python desktop_app.py`) - ChatGPT-like standalone application with local privacy
- **Docker Compose** - Multi-container deployment for teams and production

## 🏗️ Architecture Fundamentals

### Component Initialization Flow
The system uses centralized dependency injection through `DiscordBotCore`:
```python
# Entry: run.py -> src/main.py -> ModularBotManager -> DiscordBotCore
self.bot_core = DiscordBotCore(debug_mode=self.debug_mode)
components = self.bot_core.get_components()  # Returns all initialized components
```

**Key architectural patterns:**
- **Modular handlers**: Commands split across `src/handlers/` with dependency injection
- **Universal platform**: `src/platforms/universal_chat.py` abstracts Discord vs desktop
- **Adaptive configuration**: `src/config/adaptive_config.py` for environment-aware settings
- **Database abstraction**: SQLite ↔ PostgreSQL switching via `src/database/`

### Multi-Phase AI System
The AI operates through 4 progressive intelligence phases:
- **Phase 1**: Basic LLM responses with context awareness
- **Phase 2**: Emotional intelligence via `src/emotion/external_api_emotion_ai.py`
- **Phase 3**: Multi-dimensional memory networks via `src/memory/phase3_integration.py`
- **Phase 4**: Human-like conversation adaptation via `src/intelligence/phase4_integration.py`

All phases are **always enabled** in production. Check availability with:
```python
ENABLE_EMOTIONAL_INTELLIGENCE = os.getenv('ENABLE_EMOTIONAL_INTELLIGENCE', 'true')
ENABLE_PHASE3_MEMORY = os.getenv('ENABLE_PHASE3_MEMORY', 'true')
```

## 🔧 Critical Development Workflows

### ⚠️ VIRTUAL ENVIRONMENT REQUIREMENT - ALWAYS USE .venv
**CRITICAL: ALL Python commands MUST use the virtual environment. Never run python directly!**

```bash
# ✅ CORRECT - Always activate venv first
source .venv/bin/activate && python desktop_app.py
source .venv/bin/activate && python run.py
source .venv/bin/activate && python test_something.py

# ❌ WRONG - Will fail with missing dependencies
python desktop_app.py
python3 desktop_app.py
pip install something
```

### Environment Management (NEVER use dotenv directly)
```python
# ALWAYS use env_manager.py - never import dotenv directly
from env_manager import load_environment
if not load_environment():
    # Handle configuration failure
```

**Environment detection hierarchy:**
1. Explicit `ENV_MODE` environment variable
2. Container indicators (`/.dockerenv`, `CONTAINER_MODE`)
3. Development indicators (`DEV_MODE`, presence of `bot.sh`)
4. Available `.env.{mode}` files
5. Default: `development` mode

### Starting Development 
```bash
# Discord bot (fully functional) - ALWAYS use venv
source .venv/bin/activate && python run.py

# Desktop app (works with local UI) - ALWAYS use venv
source .venv/bin/activate && python desktop_app.py

# Docker development (external containers provide dependencies)
./scripts/deployment/docker-dev.sh dev  # or docker-compose -f docker-compose.dev.yml up
```

### Testing Strategy
```bash
# Component-specific tests with markers - ALWAYS use venv
source .venv/bin/activate && pytest tests/test_conversation_cache.py -v
source .venv/bin/activate && pytest -m unit              # Mock-based unit tests
source .venv/bin/activate && pytest -m integration       # Real LLM integration tests
source .venv/bin/activate && pytest -m llm               # All LLM-related tests

# Desktop app workflow testing - ALWAYS use venv
source .venv/bin/activate && python test_complete_desktop_workflow.py
source .venv/bin/activate && python test_desktop_llm_complete.py
```

## 🧠 Memory & Data Architecture

### Multi-Store Memory System
- **ChromaDB**: Vector embeddings for semantic memory (`src/memory/`)
- **Redis**: Conversation caching and session state (`USE_REDIS_CACHE=true`)
- **PostgreSQL**: Persistent user data and relationships
- **SQLite**: Local storage for desktop mode
- **Neo4j**: Optional graph database for relationship mapping (`ENABLE_GRAPH_DATABASE=true`)

### Memory Security Pattern
```python
# ALWAYS use context-aware memory with security
from src.memory.context_aware_memory_security import ContextAwareMemoryManager
memory_manager = ContextAwareMemoryManager(user_id, channel_id)

# Thread-safe wrapper for concurrent access
from src.memory.thread_safe_manager import ThreadSafeMemoryManager
safe_memory = ThreadSafeMemoryManager(context_memory_manager)
```

## 🖥️ Desktop App Architecture 

### FastAPI Web UI Pattern
Desktop app runs a FastAPI server with WebSocket real-time chat:
```python
# src/ui/web_ui.py - Core desktop UI
class WhisperEngineWebUI:
    def setup_routes(self):
        @self.app.websocket("/ws")  # Real-time chat
        @self.app.post("/api/chat")  # REST API
        @self.app.get("/", response_class=HTMLResponse)  # Main UI
```

**Static file serving**: `src/ui/static/` mounted at `/static/`
**Templates**: `src/ui/templates/index.html` for main chat interface
**Universal chat**: Same AI components work in Discord and desktop modes

### Desktop App UI Fixes Pattern
When modifying `src/ui/static/app.js` or `style.css`:
```bash
# Files may not refresh in browser due to caching
# Solution: Force server restart and clear browser cache - ALWAYS use venv
pkill -f "desktop_app" && source .venv/bin/activate && python desktop_app.py
# Then hard refresh browser (Cmd+Shift+R on macOS)
```

## 🔌 Integration Patterns

### LLM Client Universal API
```python
# src/llm/llm_client.py supports all LLM providers
LLM_CHAT_API_URL = "http://host.docker.internal:1234/v1"  # LM Studio
LLM_CHAT_API_URL = "http://localhost:11434/v1"            # Ollama
LLM_CHAT_API_URL = "https://api.openai.com/v1"           # OpenAI
LLM_MODEL_NAME = "local-model"  # Auto-detected for local servers
```

### Command Handler Registration
```python
# All commands follow this dependency injection pattern
class MyCommandHandlers:
    def __init__(self, bot, **dependencies):
        # Store injected dependencies from DiscordBotCore.get_components()
        self.memory_manager = dependencies['memory_manager']
        self.llm_client = dependencies['llm_client']
        
    def register_commands(self, bot_name_filter, is_admin):
        @self.bot.command()
        async def my_command(ctx):
            # Use self.memory_manager, self.llm_client, etc.
```

### Personality System Integration
System prompt loaded from `system_prompt.md` (root level) with dynamic personality adaptation based on conversation history and emotional intelligence analysis.

## 🐳 Docker & Deployment

### Multi-Environment Docker Architecture
```yaml
# Primary compose files for different deployment scenarios
docker-compose.yml          # Production: Full stack with external datastores
docker-compose.dev.yml      # Development: Hot-reload, debug tools
docker-compose.prod.yml     # Production optimized: Resource limits, health checks
```

**Service architecture:**
- `whisperengine-bot`: Main Discord bot application
- `chromadb`: Vector database for semantic memory
- `redis`: Cache layer for conversations
- `postgres`: Persistent storage (production only)

### Configuration Hierarchy (Docker Mode)
1. **Docker environment variables** (highest priority)
2. **Local `.env` file** (development overrides)
3. **Compose file environment** (service defaults)
4. **Built-in defaults** in `src/config/`

### Docker Development Commands
```bash
# Quick setup and management
./scripts/deployment/docker-dev.sh setup    # Initial setup from .env.example
./scripts/deployment/docker-dev.sh dev      # Start development environment
./scripts/deployment/docker-dev.sh prod     # Start production environment
./scripts/deployment/docker-dev.sh logs     # View service logs
```

## 🔒 Security & Validation Patterns

### Input Security
```python
# ALWAYS validate user input before processing
from src.security.input_validator import validate_user_input
is_safe = validate_user_input(user_message, user_id)

# System message leakage prevention
from src.security.system_message_security import validate_system_message_safety
```

### Memory Access Security
- **Cross-user isolation**: Enforced at database level with user_id constraints
- **Admin verification**: Use `is_admin()` helpers for privileged commands
- **Context boundaries**: Memory managers respect channel/guild boundaries

### Environment Validation
```python
# Use env_manager for validation
from env_manager import validate_environment
validation = validate_environment()
if not validation['valid']:
    missing_vars = validation['missing']
```

## 📁 Critical File Locations

### Core Architecture
- **Entry Point**: `run.py` → `src/main.py` → `ModularBotManager`
- **Bot Core**: `src/core/bot.py` (DiscordBotCore - dependency injection hub)
- **Command Handlers**: `src/handlers/*.py` (modular command implementations)
- **Universal Platform**: `src/platforms/universal_chat.py` (Discord/Desktop abstraction)

### AI & Intelligence
- **LLM Integration**: `src/llm/llm_client.py` (universal OpenAI-compatible client)
- **Memory Systems**: `src/memory/` (ChromaDB, Redis, context-aware security)
- **Emotional AI**: `src/emotion/external_api_emotion_ai.py` (Phase 2 integration)
- **Advanced Intelligence**: `src/intelligence/phase4_integration.py` (human-like adaptation)

### Desktop & UI
- **Desktop Entry**: `desktop_app.py` (FastAPI + WebSocket server)
- **Web UI**: `src/ui/web_ui.py` (main FastAPI application)
- **Static Assets**: `src/ui/static/` (CSS, JS, served at `/static/`)
- **Templates**: `src/ui/templates/index.html` (main chat interface)

### Configuration & Environment
- **Environment Manager**: `env_manager.py` (centralized config loading)
- **Adaptive Config**: `src/config/adaptive_config.py` (environment-aware settings)
- **Database Integration**: `src/database/database_integration.py` (SQLite ↔ PostgreSQL)

## 🚨 Common Development Gotchas

### Environment Loading
- **NEVER** use `python-dotenv` directly → Always use `env_manager.load_environment()`
- **Container detection**: System auto-detects Docker vs native environment
- **Mode precedence**: Explicit ENV_MODE > container indicators > development indicators

### Optional Dependencies
- **Voice features**: Require `PyNaCl` → Check `VOICE_AVAILABLE` flags before import
- **Graph database**: Requires `neo4j` → Check `GRAPH_MEMORY_AVAILABLE` before import
- **Desktop UI**: FastAPI optional → Graceful degradation when missing

### Memory Operations
- **Always async**: Memory operations should use proper async patterns
- **Context managers**: Use proper cleanup for database connections
- **Thread safety**: Multi-user bots need `ThreadSafeMemoryManager` wrapper

### Desktop App Development
- **Static file caching**: Browser may cache old CSS/JS → Force refresh after changes
- **Server restart required**: FastAPI static files don't hot-reload → Restart server
- **WebSocket connections**: Remember to handle disconnections gracefully

### Testing Patterns
- **Test markers**: Use `pytest -m unit` vs `pytest -m integration` for different test types
- **LLM dependency**: Integration tests require running LLM server
- **Mock vs real**: Unit tests use mocks, integration tests use real components