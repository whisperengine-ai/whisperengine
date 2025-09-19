# WhisperEngine AI Coding Agent Instructions

## Project Architecture Overview

WhisperEngine is a modular Discord AI companion bot with advanced memory, emotion intelligence, and personality systems. The architecture follows a **handler-manager-core** pattern with strict separation of concerns.

### Core Components
- **`src/core/`** - Bot initialization and core Discord integration (`bot.py`, `bot_launcher.py`)
- **`src/handlers/`** - Discord command handlers (events, admin, memory, voice, etc.)
- **`src/memory/`** - Multi-layer memory system (conversation cache, user memories, graph database)
- **`src/personality/`** - AI personality engine and character management
- **`src/llm/`** - LLM client abstraction supporting multiple providers
- **`src/conversation/`** - Context managers, thread handling, and boundary management

## Key Development Patterns

### Entry Points & Initialization
- **Primary entry**: `run.py` → auto-detects environment → delegates to `src/main.py`
- **Environment loading**: `env_manager.py` handles `.env` files with precedence rules
- **Logging setup**: `src/utils/logging_config.py` configures before any imports

### Handler Architecture
All Discord interactions use modular handlers inheriting from base patterns:
```python
class ExampleCommandHandlers:
    def __init__(self, bot: DiscordBotCore):
        self.bot = bot
        
    @commands.hybrid_command()
    async def example_command(self, ctx):
        # Pattern: validate → process → respond
```

### Error Handling System
Use production error decorators extensively:
```python
@handle_errors(
    category=ErrorCategory.CONVERSATION,
    severity=ErrorSeverity.MEDIUM,
    graceful_degradation=GracefulDegradation.FALLBACK_RESPONSE
)
```

### Memory Integration Pattern
Always use the integrated memory manager for user data:
```python
# Get memory manager instance
memory_manager = self.bot.memory_manager
# Store/retrieve using user_id as key
await memory_manager.store_memory(user_id, memory_data)
```

## Build & Test Workflows

### Running Tests
- **Quick test run**: `./scripts/run_tests.sh`
- **Category-specific**: `./scripts/run_tests.sh unit` (unit|integration|llm|slow)
- **With coverage**: Tests auto-generate reports to `test_report_TIMESTAMP.json`
- **Framework**: pytest with asyncio support, markers: `@pytest.mark.unit`, `@pytest.mark.integration`

### Docker Development
- **Development**: `docker-compose -f docker-compose.dev.yml up`
- **Production**: `docker-compose -f docker-compose.prod.yml up`
- **With monitoring**: `docker-compose up` (includes health checks on port 9090)

### Bot Management Script
`./bot.sh` is the unified management interface:
- `./bot.sh run` - Start development server
- `./bot.sh build-push v1.0.0` - Build and push container images
- `./bot.sh health` - Check system health
- `./bot.sh logs` - Tail application logs

## Project-Specific Conventions

### Module Organization
- **Handlers**: `src/handlers/` - One handler per Discord feature area
- **Managers**: Classes ending in `Manager` handle business logic and state
- **Cores**: `*Core` classes provide foundational services
- **Utils**: `src/utils/` - Cross-cutting concerns (logging, health, monitoring)

### Configuration Management
- **Environment**: Auto-detection between development/production modes
- **Multi-entity support**: Use `MULTI_ENTITY_MODE=true` for multiple character instances
- **Config validation**: `src/utils/configuration_validator.py` validates startup config

### Memory System Layers
1. **Conversation Cache** (`src/memory/conversation_cache.py`) - Short-term context
2. **User Memory Manager** (`src/memory/memory_manager.py`) - Long-term user data
3. **Graph Memory** (`src/memory/integrated_memory_manager.py`) - Relationship mapping
4. **Emotion Management** (`src/utils/emotion_manager.py`) - Emotional state tracking

### Character & Personality System
- **Character definitions**: `characters/` directory with YAML configurations
- **Personality prompts**: `prompts/` directory with role-specific templates
- **Character bridge**: `src/characters/bridge.py` integrates personality with memory

## Critical Integration Points

### LLM Provider Abstraction
`src/llm/llm_client.py` provides unified interface supporting:
- OpenAI API
- Anthropic Claude
- Local models via llamacpp
- Fallback chains for reliability

### Health & Monitoring
- **Health server**: Runs on port 9090, endpoint `/health`
- **Monitoring integration**: `src/monitoring/` provides metrics collection
- **Production monitoring**: `src/handlers/monitoring_commands.py` for Discord admin commands

### Voice Integration
- **Voice handlers**: `src/handlers/voice.py` with ElevenLabs integration
- **Audio processing**: Uses PyNaCl for Discord voice channel support
- **Voice personality**: Integrates with character emotion states

## Development Guidelines

### Adding New Features
1. Create handler in `src/handlers/` following existing patterns
2. Add business logic to appropriate manager class
3. Update `src/main.py` ModularBotManager to register handler
4. Add tests to `tests/` with appropriate markers
5. Update configuration validation if new env vars added

### Memory Operations
Always use the integrated memory system - never direct database calls:
```python
# Correct pattern
await self.bot.memory_manager.store_conversation_memory(user_id, message_data)

# Avoid direct calls to
# await chromadb.add(...)  # Wrong!
```

### Error Recovery
Production deployments use graceful degradation. When adding error-prone operations, wrap with appropriate error handling and fallback strategies.

## Testing Approach

- **Unit tests**: Mock external dependencies, focus on business logic
- **Integration tests**: Test component interactions with real services
- **LLM tests**: Validate AI integration points (marked `@pytest.mark.llm`)
- **Performance tests**: Located in `utilities/performance/`

Use the test runner script which handles environment setup and parallel execution automatically.
