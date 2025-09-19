# WhisperEngine AI Coding Agent Instructions

## Architecture Overview

WhisperEngine is a modular, concurrent Discord AI bot with advanced memory, emotion, and personality systems. The architecture is built for high scalability and reliability, using a **handler-manager-core** pattern and a robust scatter-gather concurrency model.

### Major Components
- **`src/core/`**: Bot entry, Discord integration, and main orchestration (`bot.py`, `bot_launcher.py`)
- **`src/handlers/`**: Modular Discord command/event handlers (one per feature area)
- **`src/memory/`**: Hierarchical memory system (cache, user, graph, emotion)
- **`src/personality/`**: Personality engine, character definitions, and prompt templates
- **`src/llm/`**: LLM abstraction layer (OpenAI, Claude, local, fallback chains)
- **`src/conversation/`**: Concurrent conversation manager, thread/task workers, context boundaries

## Concurrency & Pipeline Patterns

- **Scatter-Gather**: All major AI pipeline phases (emotion, memory, personality, Phase 4) use `asyncio.gather()` or task workers for parallel execution. See `src/handlers/events.py` and `src/conversation/concurrent_conversation_manager.py`.
- **Task Workers**: Background processors for conversation, session, metrics, and cache. ThreadPool/ProcessPool for CPU/IO scaling.
- **ConcurrentConversationManager**: Centralizes high-throughput message processing, load balancing, and resource management.

## Docker & Development Workflow

- **Entry Point**: `run.py` → `src/main.py` (auto-detects environment, loads config, sets up logging)
- **Bot Management**: Use `./bot.sh` for run, build, health, logs, and Docker orchestration
- **Development Mode**: `./bot.sh start dev` (hot-reload, mounted code, debug logging)
  - **Equivalent Docker Command**: `docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build`
- **Testing**: `./scripts/run_tests.sh` (unit, integration, LLM, performance)
- **Docker**: Compose files for dev/prod/monitoring; health server on port 9090

## Project-Specific Conventions

- **Handlers**: One per Discord feature, inherit from base, register in `src/main.py`
- **Managers**: `*Manager` classes for business logic/state
- **Memory**: Always use the integrated memory manager (never direct DB calls)
- **Error Handling**: Use `@handle_errors` decorator for all production code
- **Config**: Use `env_manager.py` and `src/utils/configuration_validator.py` for environment and validation

## Integration Points

- **LLM**: `src/llm/llm_client.py` (multi-provider, fallback, local support)
- **Memory**: Multi-layer (cache, user, graph, emotion) with strict API boundaries
- **Personality**: `characters/` YAML, `prompts/`, and `src/characters/bridge.py`
- **Voice**: ElevenLabs, PyNaCl, emotion-driven voice in `src/handlers/voice.py`
- **Monitoring**: `src/monitoring/`, Discord admin commands, health server

## Examples & Patterns

**Parallel AI Component Processing** (scatter-gather):
```python
results = await asyncio.gather(
    self._analyze_emotion(...),
    self._analyze_personality(...),
    self._process_phase4(...),
    ...
)
```

**Memory Operations**:
```python
# Always use the memory manager
await self.bot.memory_manager.store_conversation_memory(user_id, message_data)
# Never call DB/Chroma/Neo4j directly
```

**Handler Registration**:
```python
# In src/main.py
bot_manager.register_handler(EventsHandler)
```

## Troubleshooting & Best Practices

- Use the concurrent conversation manager for all message processing (not just sequential awaits)
- Always wrap error-prone code with `@handle_errors` for graceful degradation
- For new features, follow the handler-manager-core pattern and update config validation
- Use Docker and scripts for consistent local/dev/prod workflows

---
If any section is unclear or incomplete, please provide feedback for further refinement.
