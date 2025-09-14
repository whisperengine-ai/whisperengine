# WhisperEngine Universal AI Platform - Copilot Instructions

## 🎯 Project Overview

WhisperEngine is evolving from a Discord-only bot into a **universal AI conversation platform** that provides **two primary deployment options**:

1. **Docker Compose** - For technical users who want self-hosted, multi-container deployments
2. **Native Desktop Apps** - For non-technical users who want simple, ChatGPT-like standalone applications

The native desktop approach offers significant advantages over Docker for end users:
- **Performance**: Direct GPU access without Docker overhead
- **Privacy**: Local SQLite storage, no network requirements
- **Simplicity**: One-click installation, no technical setup requiredsperEngine Universal AI Platform - Copilot Instructions

## � Project Overview

WhisperEngine is evolving from a Discord-only bot into a **universal AI conversation platform** that scales from personal desktop apps to self-hosted Docker deployments. It embodies "Dream of the Endless" from Neil Gaiman's Sandman series with sophisticated AI memory, emotional intelligence, and privacy-first architecture.

## 🏗️ 2-Tier Architecture

### Docker Compose Tier (✅ Working)
**Target Users**: Technical users, developers, self-hosted teams
```bash
# Existing production-ready system
docker-compose up -d
# → PostgreSQL + Redis + ChromaDB + FastAPI web UI
```

### Native Desktop Tier (🔧 1% Complete)
**Target Users**: Non-technical end users wanting ChatGPT-like experience
```bash
# Work in progress - major build issues remain
python desktop_app.py
# → SQLite + local ChromaDB + system tray + embedded web UI
```

## 🔧 Current Branch Purpose

This feature branch specifically focuses on **abstracting core system and persistence mechanisms** to enable both:
- **Local filesystem storage** (SQLite, local ChromaDB, file-based configs)
- **Docker container storage** (PostgreSQL, Redis, HTTP ChromaDB)

The universal platform abstraction allows the same AI conversation engine to work across desktop apps and Docker deployments.

## �️ Adaptive Storage Architecture

### Database Abstraction Layer (✅ Working)
`src/database/abstract_database.py` provides seamless switching:
```python
# Auto-detects environment and chooses appropriate database
from src.database.database_integration import DatabaseIntegrationManager
db = DatabaseIntegrationManager()
# Desktop → SQLite embedded
# Docker → PostgreSQL with connection pooling
```

### Configuration Detection (✅ Working)  
`src/config/adaptive_config.py` auto-optimizes based on deployment:
```python
# Detects hardware: M4 Pro Mac (14 cores, 64GB) → Scale Tier 2
# Desktop mode → SQLite + local ChromaDB + memory cache  
# Docker mode → PostgreSQL + Redis + HTTP ChromaDB
config = AdaptiveConfigManager()
```

## 🎨 Universal Chat Platform

### Platform Abstraction (✅ Architecture Complete)
`src/platforms/universal_chat.py` enables same AI across all interfaces:
```python
# Single API works across web UI, Discord, future Slack/Teams
from src.platforms.universal_chat import create_universal_chat_platform
platform = create_universal_chat_platform()
await platform.handle_message(universal_message)  # Works anywhere
```

### FastAPI Web Interface (✅ Working)
`src/ui/web_ui.py` provides universal chat interface:
- WebSocket real-time communication
- Professional ChatGPT-like UI in `src/ui/templates/` and `src/ui/static/`
- Works in both desktop app and Docker deployments

### System Tray Integration (✅ Working)
`src/ui/system_tray.py` for native desktop experience:
```python
# Auto-detects availability and gracefully degrades
from src.ui.system_tray import create_system_tray, is_tray_available
if is_tray_available():
    tray = create_system_tray()
```

## 🔌 Integration Points

### LLM Client Abstraction (✅ Working)
Universal OpenAI-compatible API client supports multiple providers:
```python
# src/llm/llm_client.py supports LM Studio, Ollama, OpenRouter, OpenAI
LLM_CHAT_API_URL = "http://host.docker.internal:1234/v1"
LLM_MODEL_NAME = "local-model"
```

### WhisperEngine AI Components (✅ Working)
Core AI functionality for both deployment modes:
```python
# These components work in desktop and Docker
from src.memory.memory_manager_llm import MemoryManager
from src.emotion.external_api_emotion_ai import ExternalEmotionAI  
from src.intelligence.phase2_integration import Phase2Integration
```

## 🐳 Docker & Deployment

### Existing Docker Compose System (✅ Production Ready)
`docker-compose.yml` defines production-ready multi-container setup:
```yaml
whisperengine-bot:    # Main application
chromadb:             # Vector database  
redis:                # Cache layer
postgres:             # Primary database (when configured)
```

### Native Desktop Packaging (❌ Major Issues)
Work-in-progress PyInstaller system in `src/packaging/unified_builder.py`:
- **Status**: Framework exists but build system has syntax errors
- **Completion**: ~1% complete, not 90% as previously claimed
- **Issues**: Signal handling broken, PyInstaller integration unstable
- **Build Command**: `python build.py native_desktop --sqlite --debug`

## 🚨 Critical Implementation Status

### Working Systems (✅ Validated)
- ✅ Docker Compose deployment (production-ready for technical users)
- ✅ FastAPI web UI with WebSocket chat
- ✅ WhisperEngine AI components (memory, emotion, phase2 integration)
- ✅ Universal chat platform architecture
- ✅ Adaptive configuration system
- ✅ Database abstraction layer (SQLite ↔ PostgreSQL)

### Major Issues - Not Production Ready (❌ Critical)
- ❌ Desktop app build system has syntax errors and instability
- ❌ Signal handling broken in packaged apps (Ctrl+C doesn't work)
- ❌ PyInstaller integration has multiple build failures
- ❌ Native desktop apps require complete rebuild after every change

### Current Development Priority
1. **Fix desktop app build system** - Address PyInstaller syntax errors and stability
2. **Repair signal handling** - Enable proper Ctrl+C shutdown in packaged apps
3. **Validate Docker deployment** - Confirm end-to-end functionality
4. **Complete universal integration** - Test platform abstraction across modes

## � Developer Workflows

### Starting Development
```bash
# Docker development (reliable)
docker-compose up -d

# Desktop app development (has issues)
python desktop_app.py

# Original Discord bot (legacy)
python run.py
```

### Environment Management
**Critical**: Use `env_manager.py` for environment configuration - **never** load `.env` files directly:
```python
from env_manager import load_environment
if not load_environment():
    # Handle configuration failure
```

### Build System (❌ Unstable)
```bash
# Native desktop building (has major issues, needs work)
python build.py native_desktop --sqlite --debug

# Docker building (works via existing compose system)
docker-compose -f docker-compose.yml up --build
```

## � Key File Locations

### Universal Platform Architecture
- **Desktop Entry**: `desktop_app.py` (desktop app launcher)
- **Universal Platform**: `src/platforms/universal_chat.py` (cross-platform abstraction)
- **Adaptive Config**: `src/config/adaptive_config.py` (environment-aware settings)
- **Database Layer**: `src/database/abstract_database.py` (SQLite/PostgreSQL abstraction)
- **Build System**: `src/packaging/unified_builder.py` (native app packaging - **unstable**)

### Legacy Discord Architecture  
- **Discord Entry**: `run.py` → `src/main.py` (original Discord bot)
- **Core Logic**: `src/core/bot.py` (DiscordBotCore)
- **Commands**: `src/handlers/` (Discord command handlers)
- **Memory**: `src/memory/` (conversation and context management)

## 🔄 Implementation Reality Check

### Honest Status Assessment

**Docker Compose System**: ✅ **Working Well**
- Production-ready for technical users
- Multi-container architecture with PostgreSQL, Redis, ChromaDB
- Suitable for teams and self-hosted deployments

**Native Desktop Apps**: ❌ **1% Complete** 
- Build system exists but has major syntax errors
- Signal handling broken (Ctrl+C doesn't kill processes)
- PyInstaller integration unstable and unreliable
- Requires substantial development work before usability

**Universal Platform**: 🔧 **Architecture Complete, Integration Needed**
- Platform abstraction implemented and working
- Adaptive configuration system functional
- Database layer successfully abstracts SQLite/PostgreSQL
- Needs thorough end-to-end testing and validation

### Development Focus
This branch is specifically for creating the **foundation** that enables both Docker and native desktop deployments. The emphasis is on:
1. **Abstracting persistence mechanisms** (SQLite vs PostgreSQL)
2. **Environment-aware configuration** (desktop vs Docker optimization)
3. **Universal chat platform** (same AI across all deployment modes)
4. **Build system foundation** (even if current implementation is unstable)

The goal is providing **choice** - technical users get Docker's power and flexibility, non-technical users get native apps' simplicity and performance.
        ## 🔒 Security & Best Practices

### Input Validation
```python
from src.security.input_validator import validate_user_input
is_safe = validate_user_input(user_message, user_id)
```

### Memory Security
- Cross-user memory isolation enforced at database level
- System message leakage prevention via `system_message_security.py`
- Admin command access control through `is_admin()` helpers

## 🚨 Common Development Gotchas

- **Environment Loading**: Always use `env_manager.load_environment()`, never `python-dotenv` directly
- **Python Path**: Use `.venv/bin/python` consistently - avoid bare `python` commands
- **Desktop App Status**: Build system exists but has major issues - not production ready
- **Database Context**: Code auto-detects SQLite vs PostgreSQL based on deployment mode
- **Signal Handling**: Desktop apps have broken Ctrl+C handling - manual process killing required
- **Documentation vs Reality**: Status claims in docs often aspirational - validate functionality first
- **PyInstaller Issues**: Current build system has syntax errors and stability problems

## 📝 Documentation & Context Management

### **CRITICAL**: Create Decision Trail Documentation
**The app is getting complex** - context can be lost between chat threads. **Always create MD files** for:

#### **Decision Documentation** (Required for major changes)
- **`docs/decisions/YYYY-MM-DD-decision-name.md`** - Architecture decisions, approach changes
- **`docs/status/COMPONENT_STATUS.md`** - Current implementation status (honest assessment)
- **`docs/troubleshooting/ISSUE_NAME.md`** - Problem resolution and lessons learned

#### **Development Breadcrumbs** (Leave for future sessions)
```markdown
# Current Work Status - [Date]

## What's Working
- [List verified functionality]

## What's Broken  
- [List known issues with specific details]

## Next Steps
- [Specific actionable items with file paths]

## Context Notes
- [Important decisions or discoveries from this session]
```

#### **File Locations for Breadcrumbs**
- **`CURRENT_STATUS.md`** (root level) - Overall project status
- **`DEVELOPMENT_LOG.md`** (root level) - Session-by-session progress
- **`docs/project/IMPLEMENTATION_REALITY.md`** - Honest vs aspirational status

### **Documentation First Approach**
1. **Before starting complex work**: Document current state and plan
2. **During development**: Update status files with discoveries/issues
3. **After sessions**: Leave clear breadcrumbs for next time
4. **Major decisions**: Create dedicated decision documents

**Why This Matters**: WhisperEngine has multiple deployment modes, complex abstractions, and a history of documentation inaccuracy. Breadcrumb files prevent losing context and ensure honest progress tracking.
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
whisperengine-bot:    # Main application
chromadb:             # Vector database
redis:                # Cache layer
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