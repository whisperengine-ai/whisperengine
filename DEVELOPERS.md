# 🔧 WhisperEngine for Developers

**Want to contribute, customize, or run from source? You're in the right place!**

## 🚀 Quick Development Setup

### Prerequisites
- Python 3.11+
- Git
- 16GB+ RAM recommended
- 25GB+ free storage

### Clone & Setup
```bash
# Clone repository
git clone https://github.com/yourusername/whisperengine.git
cd whisperengine

# Create virtual environment
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
# OR
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Download AI models
python download_models.py

# Configure environment
cp .env.example .env
# Edit .env with your settings
```

### Running Applications

#### Discord Bot
```bash
source .venv/bin/activate && python run.py
```

#### Desktop App
```bash
source .venv/bin/activate && python desktop_app.py
```

#### Docker Development
```bash
./scripts/deployment/docker-dev.sh dev
```

## 🏗️ Architecture Overview

### Core Components
- **Entry Points**: `run.py` (Discord), `desktop_app.py` (Desktop)
- **Bot Core**: `src/core/bot.py` - Dependency injection hub
- **Universal Platform**: `src/platforms/universal_chat.py` - Discord/Desktop abstraction
- **AI Integration**: `src/llm/llm_client.py` - Universal LLM client
- **Memory Systems**: `src/memory/` - Multi-store memory architecture

### AI Intelligence Phases
1. **Phase 1**: Basic LLM responses with context
2. **Phase 2**: Emotional intelligence via external API
3. **Phase 3**: Multi-dimensional memory networks  
4. **Phase 4**: Human-like conversation adaptation

### Configuration System
- **Environment Detection**: Auto-detects Docker vs native
- **Adaptive Config**: `src/config/adaptive_config.py`
- **Multi-Environment**: `.env.development`, `.env.production`, etc.

## 🧪 Testing

### Unit Tests
```bash
source .venv/bin/activate && pytest -m unit
```

### Integration Tests  
```bash
source .venv/bin/activate && pytest -m integration
```

### Desktop Workflow Tests
```bash
source .venv/bin/activate && python test_complete_desktop_workflow.py
```

### LLM Integration Tests
```bash
source .venv/bin/activate && pytest -m llm
```

## 📦 Building Executables

### Build for Current Platform
```bash
source .venv/bin/activate && python scripts/build_prebuilt_executables.py
```

### Test Existing Build
```bash
source .venv/bin/activate && python scripts/build_prebuilt_executables.py --test-only
```

### Manual PyInstaller Build
```bash
source .venv/bin/activate && pyinstaller --clean --noconfirm whisperengine-unified.spec
```

## 🐳 Docker Development

### Quick Start
```bash
./scripts/deployment/docker-dev.sh setup  # Initial setup
./scripts/deployment/docker-dev.sh dev    # Development environment
./scripts/deployment/docker-dev.sh prod   # Production environment
```

### Available Compose Files
- `docker-compose.yml` - Production stack
- `docker-compose.dev.yml` - Development with hot-reload
- `docker-compose.prod.yml` - Production optimized

## 🔌 LLM Integration

### Supported Providers
```python
# Local LM Studio
LLM_CHAT_API_URL = "http://host.docker.internal:1234/v1"

# Local Ollama  
LLM_CHAT_API_URL = "http://localhost:11434/v1"

# OpenAI API
LLM_CHAT_API_URL = "https://api.openai.com/v1"
```

### Model Configuration
- **Primary**: Phi-3-Mini-4K-Instruct (4096 token context)
- **Embeddings**: all-MiniLM-L6-v2 (sentence transformers)
- **Speech**: Whisper-tiny.en (voice features)

## 🧠 Memory Architecture

### Storage Systems
- **ChromaDB**: Vector embeddings for semantic memory
- **Redis**: Conversation caching and session state  
- **PostgreSQL**: Persistent user data and relationships
- **SQLite**: Local storage for desktop mode
- **Neo4j**: Optional graph database for relationships

### Security Patterns
```python
# Context-aware memory with security
from src.memory.context_aware_memory_security import ContextAwareMemoryManager
memory_manager = ContextAwareMemoryManager(user_id, channel_id)

# Thread-safe wrapper for concurrent access
from src.memory.thread_safe_manager import ThreadSafeMemoryManager
safe_memory = ThreadSafeMemoryManager(context_memory_manager)
```

## 🔧 Development Patterns

### Command Handler Registration
```python
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

### Environment Management
```python
# ALWAYS use env_manager - never import dotenv directly
from env_manager import load_environment
if not load_environment():
    # Handle configuration failure
```

### Input Security
```python
# ALWAYS validate user input before processing
from src.security.input_validator import validate_user_input
is_safe = validate_user_input(user_message, user_id)
```

## 🚨 Development Gotchas

### Critical Rules
- **ALWAYS use virtual environment**: `source .venv/bin/activate`
- **NEVER use dotenv directly**: Use `env_manager.load_environment()`
- **Memory operations async**: Use proper async patterns
- **Optional dependencies**: Check availability flags before import

### Desktop App Development
- **Static file caching**: Force server restart after CSS/JS changes
- **WebSocket connections**: Handle disconnections gracefully
- **UI updates**: Hard refresh browser (Cmd+Shift+R) after changes

### Testing Patterns
- **Mock vs real**: Unit tests use mocks, integration tests use real components
- **LLM dependency**: Integration tests require running LLM server
- **Test markers**: Use pytest markers for different test types

## 📁 Key File Locations

### Core Architecture
```
run.py                           # Discord bot entry point
desktop_app.py                   # Desktop app entry point  
src/main.py                      # Main bot initialization
src/core/bot.py                  # DiscordBotCore - dependency injection
src/platforms/universal_chat.py  # Discord/Desktop abstraction
```

### AI & Intelligence
```
src/llm/llm_client.py                      # Universal LLM client
src/memory/                                # Memory systems
src/emotion/external_api_emotion_ai.py     # Emotional intelligence
src/intelligence/phase4_integration.py     # Advanced AI features
```

### Configuration & Environment
```
env_manager.py                           # Environment loading
src/config/adaptive_config.py            # Environment-aware settings
src/database/database_integration.py     # Database abstraction
```

### Build & Deployment
```
whisperengine-unified.spec               # PyInstaller build spec
scripts/build_prebuilt_executables.py    # Build automation
.github/workflows/                       # CI/CD pipelines
docker-compose*.yml                      # Docker configurations
```

## 🔄 Contributing Workflow

1. **Fork & Clone**: Fork repository and clone locally
2. **Branch**: Create feature branch (`feature/amazing-feature`)
3. **Develop**: Make changes following patterns above
4. **Test**: Run tests (`pytest -m unit` and `pytest -m integration`)
5. **Build**: Test executable build works
6. **PR**: Submit pull request with clear description

## 📚 Additional Resources

- **Architecture Details**: See `ARCHITECTURE_FIX_SUMMARY.md`
- **Security Guidelines**: See `SECURITY.md`
- **Contributing Guide**: See `CONTRIBUTING.md`
- **Current Status**: See `CURRENT_STATUS.md`

---

**For Non-Technical Users**: Want to just download and chat? See [USERS.md](USERS.md)