# WhisperEngine AI Discord Bot - Copilot Instructions

## 🎭 Project Overview

WhisperEngine is a privacy-first Discord bot embodying "Dream of the Endless" from Neil Gaiman's Sandman series. It runs completely locally with sophisticated AI memory, emotional intelligence, and personality adaptation systems.

## 🏗️ Architecture Patterns

### Modular Component Architecture
The codebase uses dependency injection through `DiscordBotCore` that initializes all components:
```python
# Entry point: run.py -> src/main.py -> ModularBotManager
self.bot_core = DiscordBotCore(debug_mode=self.debug_mode)
components = self.bot_core.get_components()
```

Key architectural principles:
- **Separation of concerns**: Commands in `src/handlers/`, core logic in `src/core/`
- **Dependency injection**: All handlers receive dependencies via constructor
- **Graceful initialization**: Components initialize in proper dependency order

### Multi-Phase AI Intelligence System
The bot implements a 4-phase intelligence architecture:
- **Phase 1**: Basic LLM responses
- **Phase 2**: Emotional intelligence via `external_api_emotion_ai.py`
- **Phase 3**: Advanced memory networks via `phase3_integration.py`
- **Phase 4**: Human-like conversation adaptation

Check feature availability with environment variables:
```python
ENABLE_EMOTIONAL_INTELLIGENCE = os.getenv('ENABLE_EMOTIONAL_INTELLIGENCE', 'true')
ENABLE_PHASE3_MEMORY = os.getenv('ENABLE_PHASE3_MEMORY', 'true')
```

## 🔧 Developer Workflows

### Starting Development
```bash
# Development mode with hot-reloading
./bot.sh start      # Production Docker mode
python run.py       # Native Python development
```

### Environment Management
Use `env_manager.py` for environment configuration - **never** load `.env` files directly:
```python
from env_manager import load_environment
if not load_environment():
    # Handle configuration failure
```

### Testing Strategy
```bash
# Component-specific tests
pytest tests/test_conversation_cache.py -v
pytest tests/test_memory_manager_llm.py -v

# Integration tests focus on security and memory systems
pytest tests/test_complete_integration.py
```

## 🧠 Memory & Data Flow

### Memory Architecture
- **ChromaDB**: Vector embeddings for semantic memory
- **Redis**: Conversation caching and session state  
- **PostgreSQL**: Persistent user data and relationships
- **Graph Database**: Optional Neo4j for relationship mapping

### Critical Memory Patterns
```python
# Always use safe memory access
from src.memory.context_aware_memory_security import ContextAwareMemoryManager
memory_manager = ContextAwareMemoryManager(user_id, channel_id)

# Conversation flow through cache layers
conversation_cache = HybridConversationCache()
await conversation_cache.store_conversation(user_id, message, response)
```

## 🔌 Integration Points

### LLM Client Abstraction
Universal OpenAI-compatible API client in `src/llm/llm_client.py`:
```python
# Supports LM Studio, Ollama, OpenRouter, OpenAI
LLM_CHAT_API_URL = "http://host.docker.internal:1234/v1"
LLM_MODEL_NAME = "local-model"
```

### Command Handler Pattern
All commands follow this registration pattern:
```python
class MyCommandHandlers:
    def __init__(self, bot, **dependencies):
        self.bot = bot
        # Store injected dependencies
        
    def register_commands(self, *filters):
        @self.bot.command()
        async def my_command(ctx):
            # Implementation
```

### Personality System
The bot's personality is defined in `system_prompt.md` (root level) and loaded dynamically:
- Formal, archaic speech patterns
- Emotional intelligence with relationship depth tracking
- Memory of past conversations influences current responses

## 🐳 Docker & Deployment

### Service Architecture
```yaml
# docker-compose.yml defines 3 core services:
discord-bot:    # Main application
chromadb:      # Vector database
redis:         # Cache layer
```

### Configuration Hierarchy
1. Docker environment variables override everything
2. `.env` file for local development  
3. `.env.{mode}` for environment-specific defaults
4. Built-in defaults in `src/config/` directory

## 🔒 Security Patterns

### Input Validation
```python
from src.security.input_validator import validate_user_input
is_safe = validate_user_input(user_message, user_id)
```

### Memory Security
- Cross-user memory isolation enforced at database level
- System message leakage prevention via `system_message_security.py`
- Admin command access control through `is_admin()` helpers

## 📁 Key File Locations

- **Entry point**: `run.py` (handles env loading + logging setup)
- **Main logic**: `src/main.py` (ModularBotManager)
- **Core initialization**: `src/core/bot.py` (DiscordBotCore)
- **Commands**: `src/handlers/` (all Discord command handlers)
- **AI/LLM**: `src/llm/`, `src/emotion/`, `src/intelligence/`
- **Memory**: `src/memory/` (multiple memory subsystems)
- **Configuration**: `env_manager.py`, `src/config/`

## 🚨 Common Gotchas

- Always import environment via `env_manager.load_environment()`, not `python-dotenv`
- Voice features require `PyNaCl` and are optional - check `VOICE_AVAILABLE` flags
- Graph database features are optional - check `GRAPH_MEMORY_AVAILABLE` imports
- Admin commands require `is_admin()` checks for security
- Memory operations should use async patterns and proper context managers
- System prompts are dynamically generated - avoid hardcoding personality text

## 🔄 Refactoring Status

The codebase is actively migrating from monolithic to modular architecture. When modifying:
1. Add new commands to appropriate `src/handlers/` modules
2. Update `DiscordBotCore.get_components()` for new dependencies
3. Register handlers in `ModularBotManager._initialize_command_handlers()`
4. Test both modular and legacy paths during transition