# Contributing to WhisperEngine

Thank you for your interest in contributing to WhisperEngine! This guide will help you get started with development and contribution.

## 🚀 Quick Start for Contributors

### Development Environment Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/whisperengine-ai/whisperengine
   cd whisperengine
   ```

2. **Environment Setup**
   ```bash
   # Copy environment template
   cp .env.example .env
   
   # Configure your Discord token and LLM settings
   nano .env
   ```

3. **Development Mode**
   ```bash
   # Native development (recommended for code changes)
   python run.py
   
   # Or Docker development mode
   ./bot.sh start dev
   ```

## 🏗️ Architecture Overview

WhisperEngine uses a modular architecture with these key components:

### Core Components
- **`src/core/`**: Core bot initialization and dependency injection
- **`src/handlers/`**: Discord command handlers and event processors  
- **`src/memory/`**: Memory management and AI intelligence systems
- **`src/llm/`**: LLM client abstraction and communication
- **`env_manager.py`**: Environment configuration management

### Key Patterns
- **Dependency Injection**: Components are initialized via `DiscordBotCore`
- **Modular Handlers**: All commands follow the handler registration pattern
- **Memory Security**: Cross-user isolation and input validation
- **Graceful Initialization**: Components start in proper dependency order

## 🔧 Development Guidelines

### Code Style

- **Python**: Follow PEP 8 with 4-space indentation
- **Imports**: Use absolute imports, group by standard/third-party/local
- **Docstrings**: Use Google-style docstrings for functions and classes
- **Type Hints**: Use type hints where possible

### Naming Conventions

- **Files**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions/Variables**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`

### Example Code Structure

```python
"""Module docstring describing purpose."""

import os
from typing import Optional, Dict, Any

from src.core.dependencies import CoreDependency


class ExampleHandler:
    """Example handler following our patterns."""
    
    def __init__(self, bot, memory_manager: CoreDependency):
        self.bot = bot
        self.memory_manager = memory_manager
    
    def register_commands(self):
        """Register Discord commands."""
        @self.bot.command()
        async def example_command(ctx):
            # Implementation
            pass
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/test_memory/ -v
python -m pytest tests/test_security/ -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html
```

### Test Structure

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test component interactions
- **Security Tests**: Validate input filtering and memory isolation
- **Performance Tests**: Memory and response time validation

### Writing Tests

```python
import pytest
from unittest.mock import Mock, AsyncMock

from src.handlers.example_handler import ExampleHandler


class TestExampleHandler:
    @pytest.fixture
    def handler(self):
        bot = Mock()
        memory_manager = Mock()
        return ExampleHandler(bot, memory_manager)
    
    @pytest.mark.asyncio
    async def test_example_functionality(self, handler):
        # Test implementation
        result = await handler.some_method()
        assert result is not None
```

## 🔒 Security Guidelines

### Input Validation
- Always validate user input through `src.security.input_validator`
- Sanitize file paths and prevent directory traversal
- Validate Discord user IDs and permissions

### Memory Security
- Ensure cross-user memory isolation
- Prevent system message leakage
- Use proper context managers for database operations

### Admin Commands
- Always check `is_admin()` for administrative functions
- Log admin actions for audit trails
- Validate admin permissions at multiple levels

## 📁 Adding New Features

### 1. Command Handlers

Create new handlers in `src/handlers/`:

```python
# src/handlers/new_feature_handlers.py
class NewFeatureHandlers:
    def __init__(self, bot, **dependencies):
        self.bot = bot
        # Store dependencies
        
    def register_commands(self):
        @self.bot.command()
        async def new_command(ctx):
            # Implementation
            pass
```

### 2. Update Core Registration

Add to `src/core/bot.py`:

```python
def get_components(self):
    # Add your new dependencies
    return {
        'new_feature_dependency': self.new_feature_manager,
        # ... existing components
    }
```

### 3. Register in Main Bot

Update `src/main.py`:

```python
def _initialize_command_handlers(self):
    # Add new handler initialization
    from src.handlers.new_feature_handlers import NewFeatureHandlers
    new_feature = NewFeatureHandlers(self.bot, **components)
    new_feature.register_commands()
```

## 🐳 Docker Development

### Development Containers

```bash
# Start development environment
./bot.sh start dev

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Access running container
docker-compose -f docker-compose.dev.yml exec discord-bot bash
```

### Database Access

```bash
# PostgreSQL
docker-compose exec postgres psql -U bot_user -d discord_bot

# Redis
docker-compose exec redis redis-cli

# ChromaDB
curl http://localhost:8000/api/v1/collections
```

## 📋 Pull Request Process

### Before Submitting

1. **Test Your Changes**
   ```bash
   python -m pytest tests/
   ```

2. **Check Code Style**
   ```bash
   black src/
   flake8 src/
   ```

3. **Update Documentation**
   - Update relevant docstrings
   - Add to CHANGELOG.md if applicable
   - Update README.md for user-facing changes

### Commit Guidelines

- Use clear, descriptive commit messages
- Follow conventional commit format when possible:
  ```
  feat: add new memory optimization feature
  fix: resolve conversation cache timeout issue
  docs: update API documentation
  test: add integration tests for memory system
  ```

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] Added tests for new functionality
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No sensitive information committed
```

## 🐛 Debugging Tips

### Common Issues

1. **Environment Loading**: Always use `env_manager.load_environment()`
2. **Memory Isolation**: Test with multiple users to ensure isolation
3. **Docker Networking**: Use `host.docker.internal` for LLM connections
4. **Component Dependencies**: Check initialization order in logs

### Logging

```python
import logging
logger = logging.getLogger(__name__)

# Use structured logging
logger.info("Processing user request", extra={
    'user_id': user_id,
    'command': command_name
})
```

### Performance Monitoring

- Monitor memory usage with conversation cache
- Profile embedding operations for performance
- Check database connection pool health
- Monitor LLM response times

## 🤝 Community Guidelines

### Code of Conduct

We follow the [Contributor Covenant](CODE_OF_CONDUCT.md). Please read and follow these guidelines.

### Communication

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and community chat
- **Pull Requests**: Code review and technical discussion

### Getting Help

1. Check existing documentation in `docs/`
2. Search existing GitHub issues
3. Create detailed issue with:
   - Clear description
   - Steps to reproduce
   - Environment information
   - Relevant logs

## 📚 Additional Resources

- **[Development Guide](docs/development/DEVELOPMENT_GUIDE.md)**: Comprehensive development setup
- **[Memory System](docs/ai-systems/MEMORY_SYSTEM_README.md)**: Understanding AI memory architecture
- **[API Configuration](docs/configuration/API_KEY_CONFIGURATION.md)**: LLM provider setup
- **[Security Guide](docs/security/SECURITY_AUTHORIZATION_DESIGN.md)**: Security implementation details

---

Thank you for contributing to WhisperEngine! Together we're building the future of privacy-first AI assistants. 🎭