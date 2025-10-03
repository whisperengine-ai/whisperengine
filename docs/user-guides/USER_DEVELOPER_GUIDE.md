# WhisperEngine User & Developer Guide

Welcome to WhisperEngine! This guide will help you get started whether you're a user wanting to run the bot or a developer contributing to the project.

## 🚀 Quick Start

### For Users (Just Want to Run the Bot)

**Option 1: One-Command Setup (Recommended)**
```bash
# Linux/macOS
curl -sSL https://raw.githubusercontent.com/WhisperEngine-AI/whisperengine/main/scripts/quick-start.sh | bash

# Windows PowerShell
iwr https://raw.githubusercontent.com/WhisperEngine-AI/whisperengine/main/scripts/quick-start.ps1 | iex

# Windows Command Prompt
# Download and run scripts/quick-start.bat
```

**Option 2: Manual Setup**
```bash
# 1. Clone repository
git clone https://github.com/WhisperEngine-AI/whisperengine.git
cd whisperengine

# 2. Set up environment
cp .env.example .env
# Edit .env with your Discord bot token and LLM settings

# 3. Run setup script
./setup.sh  # Linux/macOS
setup.bat   # Windows

# 4. Start the bot
python run.py
```

### For Developers (Want to Contribute)

```bash
# 1. Fork and clone
git clone https://github.com/YOUR_USERNAME/whisperengine.git
cd whisperengine

# 2. Set up development environment
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements-dev.txt

# 3. Start infrastructure services
./bot.sh start infrastructure

# 4. Run bot natively for development
python run.py
```

## 🎯 Choose Your Deployment Mode

### Discord Bot Mode
Perfect for Discord communities and servers.
```bash
# Configure Discord settings in .env
DISCORD_BOT_TOKEN=your_token_here
ENV_MODE=discord

# Start Discord bot
python run.py
```

### Desktop App Mode
Privacy-first standalone application for personal use.
```bash
# Configure for desktop mode
ENV_MODE=desktop

# Start desktop app
python universal_native_app.py
```

### Production Docker Mode
Scalable deployment for teams and production environments.
```bash
# Start full production stack
./bot.sh start prod
```

## 🔧 Configuration Guide

### Essential Configuration (.env file)

1. **Copy the template:**
   ```bash
   cp .env.example .env
   ```

2. **Set your Discord bot token:**
   ```env
   DISCORD_BOT_TOKEN=your_discord_bot_token_here
   ADMIN_USER_IDS=your_discord_user_id_here
   ```

3. **Configure your LLM provider:**

   **Local LLM (LM Studio - Recommended for Privacy):**
   ```env
   LLM_CHAT_API_URL=http://localhost:1234/v1
   LLM_CHAT_MODEL=local-model
   ```

   **Local LLM (Ollama):**
   ```env
   LLM_CHAT_API_URL=http://localhost:11434/v1
   LLM_CHAT_MODEL=phi3:mini
   ```

   **OpenAI:**
   ```env
   LLM_CHAT_API_URL=https://api.openai.com/v1
   LLM_CHAT_API_KEY=your_openai_api_key
   LLM_CHAT_MODEL=gpt-4
   ```

   **OpenRouter:**
   ```env
   LLM_CHAT_API_URL=https://openrouter.ai/api/v1
   LLM_CHAT_API_KEY=your_openrouter_api_key
   LLM_CHAT_MODEL=openai/gpt-4o
   ```

### Advanced Configuration

**Database Options:**
```env
# SQLite (Default - Simple)
USE_SQLITE=true

# PostgreSQL (Production)
USE_POSTGRESQL=true
POSTGRES_HOST=localhost
POSTGRES_DB=whisper_engine
POSTGRES_USER=bot_user
POSTGRES_PASSWORD=secure_password
```

**AI Intelligence Features:**
```env
# All features enabled by default for full capabilities
ENABLE_EMOTIONAL_INTELLIGENCE=true
ENABLE_PHASE3_MEMORY=true
ENABLE_PHASE4_INTELLIGENCE=true
PERSONALITY_ADAPTATION_ENABLED=true
```

**Performance Tuning:**
```env
# Optimize for your system
MAX_CONCURRENT_AI_OPERATIONS=3
AI_RESPONSE_TIMEOUT=30
MEMORY_CACHE_SIZE=auto
```

## 🏗️ Development Workflows

### Recommended Development Setup

1. **Infrastructure Mode (Recommended):**
   ```bash
   # Start only the databases
   ./bot.sh start infrastructure
   
   # Run bot natively for hot-reload and debugging
   source .venv/bin/activate
   python run.py
   ```

2. **Check your setup:**
   ```bash
   # Verify all services are healthy
   ./bot.sh status
   
   # View bot logs
   ./bot.sh logs
   ```

### Development Commands

**Environment Management:**
```bash
# Activate virtual environment
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements-core.txt
pip install -r requirements-discord.txt
pip install -r requirements-dev.txt
```

**Testing:**
```bash
# Run all tests
pytest

# Run specific test categories
pytest -m unit           # Unit tests (fast, mocked)
pytest -m integration    # Integration tests (require LLM)
pytest -m llm            # All LLM-related tests

# Run specific test file
pytest tests/test_conversation_cache.py -v
```

**Code Quality:**
```bash
# Format code
black .

# Check types
mypy src/

# Lint code
flake8 src/
```

### Docker Development

**Start development environment:**
```bash
# Hot-reload development mode
./scripts/deployment/docker-dev.sh dev

# View logs
./bot.sh logs

# Restart services
./bot.sh restart-all infrastructure
```

**Data Management:**
```bash
# Clear cache but keep memories
./bot.sh restart-clean infrastructure

# View service status
./bot.sh status

# Clean up orphaned containers
./bot.sh cleanup
```

### CI/CD Pipeline & Release Process

WhisperEngine includes a comprehensive CI/CD pipeline with security hardening:

#### Automated Testing
```bash
# The CI pipeline runs:
# - Unit tests with mocking
# - Integration tests with real LLMs
# - Performance benchmarks
# - Security vulnerability scanning
# - Code quality analysis
```

#### Release Artifacts
Every release includes:
- **Multi-platform containers** (AMD64, ARM64)
- **SBOM artifacts** for compliance auditing
- **Security scan reports** with vulnerability analysis
- **Signed containers** with provenance attestations

#### Contributing to Production
```bash
# 1. Create feature branch
git checkout -b feature/your-feature

# 2. Develop with tests
pytest -m unit  # Fast feedback during development

# 3. Full test suite before PR
pytest  # Run all tests
./scripts/validate-build.sh  # Validate build system

# 4. Open PR - CI pipeline will:
#    - Run comprehensive tests
#    - Generate security reports  
#    - Build and scan containers
#    - Generate SBOM artifacts
```

#### Release Workflow
```bash
# For maintainers:
git tag v1.2.3
git push origin v1.2.3

# CI automatically:
# 1. Builds multi-platform containers
# 2. Signs with Cosign
# 3. Generates SBOM files
# 4. Publishes to multiple registries
# 5. Creates GitHub release with artifacts
```

**Data Management:**
```bash
# Clear cache but keep memories
./bot.sh restart-clean infrastructure

# View service status
./bot.sh status

# Clean up orphaned containers
./bot.sh cleanup
```

## 🧠 AI System Overview

WhisperEngine features a 4-phase AI intelligence system:

### Phase 1: Basic LLM + Context
- Core conversation abilities
- System prompt personality
- Basic memory integration

### Phase 2: Emotional Intelligence
- Multi-source emotion analysis (96-98% accuracy)
- VADER + RoBERTa emotion models
- Emotional context in responses

### Phase 3: Multi-Dimensional Memory
- ChromaDB vector embeddings
- Redis conversation caching
- Semantic memory clustering
- Long-term relationship tracking

### Phase 4: Human-Like Adaptation
- Dynamic personality adjustment
- Conversation pattern learning
- Context-aware response adaptation
- Relationship-based communication styles

All phases are **enabled by default** for the full experience.

## 🏭 Production & Security Features

WhisperEngine includes enterprise-grade features for production deployments:

### Supply Chain Security
- **SBOM Generation** - Software Bill of Materials for compliance
- **Container Signing** - Cosign-signed containers with provenance
- **Multi-Registry Support** - Docker Hub, GitHub Container Registry, custom registries
- **Vulnerability Scanning** - Automated security scanning in CI/CD

### Production Monitoring
- **Health Endpoints** - REST APIs for external monitoring systems
- **Prometheus Metrics** - Comprehensive metrics export
- **Real-time Dashboard** - Web-based monitoring interface
- **Discord Admin Commands** - Monitor system health from Discord

```bash
# Monitor system health
!health              # Basic health check
!health detailed     # Component-by-component analysis
!errors             # Recent error analysis
!performance        # System performance metrics
!dashboard          # Get web dashboard access
```

### Error Tracking & Analytics
- **Intelligent Error Categorization** - AI, System, User, Network errors
- **Pattern Detection** - Automatic identification of recurring issues
- **Resolution Tracking** - Monitor fix effectiveness
- **User Engagement Analytics** - Usage patterns and conversation quality

### Configuration for Production
```env
# Enable production monitoring
ENABLE_WEB_DASHBOARD=true
HEALTH_CHECK_ENABLED=true
PERFORMANCE_MONITORING_ENABLED=true

# Security features
ENABLE_PRODUCTION_OPTIMIZATION=true
ENABLE_LLM_TRUST_DETECTION=false  # Disable for local models

# Alert configuration
ALERT_DISCORD_ENABLED=true
ALERT_EMAIL_ENABLED=true
ALERT_SLACK_ENABLED=true
```

See **[Production Monitoring Guide](docs/operations/MONITORING.md)** and **[Supply Chain Security](docs/security/SUPPLY_CHAIN.md)** for detailed setup.

## 📁 Project Structure

```
whisperengine/
├── src/                      # Core application code
│   ├── main.py              # Application entry point
│   ├── core/                # Core bot infrastructure
│   ├── handlers/            # Modular command handlers
│   ├── llm/                 # LLM integration layer
│   ├── memory/              # Memory systems (ChromaDB, Redis)
│   ├── emotion/             # Emotional intelligence
│   ├── intelligence/        # Phase 4 advanced AI
│   └── platforms/           # Universal chat abstraction
├── run.py                   # Discord bot launcher
├── universal_native_app.py  # Desktop app launcher
├── bot.sh                   # Docker management script
├── env_manager.py           # Environment configuration
├── requirements-*.txt       # Tiered dependencies
├── docker-compose.*.yml     # Multi-environment deployment
└── scripts/                 # Installation and deployment scripts
```

## 🔧 Troubleshooting

### Common Issues

**Bot won't start:**
```bash
# Check environment configuration
python -c "from env_manager import validate_environment; print(validate_environment())"

# Verify LLM connection
python check_llm_config.py

# Check dependencies
python check_dependencies.py
```

**Database connection errors:**
```bash
# Start infrastructure services
./bot.sh start infrastructure

# Check service status
./bot.sh status

# Restart services if needed
./bot.sh restart-all infrastructure
```

**Memory/Performance issues:**
```bash
# Clear cache to free memory
./bot.sh clear-cache infrastructure

# Check system resources
docker stats

# Optimize memory settings in .env
MEMORY_OPTIMIZATION_LEVEL=high
```

**Permission errors (Linux/macOS):**
```bash
# Fix script permissions
chmod +x bot.sh
chmod +x setup.sh
chmod +x scripts/*.sh
```

### Getting Help

1. **Check the logs:**
   ```bash
   ./bot.sh logs
   ./bot.sh status
   ```

2. **Validate your configuration:**
   ```bash
   python validate_config.py
   ```

3. **Run health checks:**
   ```bash
   curl http://localhost:9090/health
   curl http://localhost:9090/status
   ```

4. **Community Support:**
   - GitHub Issues: [Report bugs or request features](https://github.com/WhisperEngine-AI/whisperengine/issues)
   - Discussions: [Community help and questions](https://github.com/WhisperEngine-AI/whisperengine/discussions)

## 🚢 Deployment Options

### Local Development
```bash
# Native Python (recommended for development)
source .venv/bin/activate
python run.py
```

### Docker Development
```bash
# Infrastructure only (databases)
./bot.sh start infrastructure

# Full production stack
./bot.sh start prod
```

### Production Deployment
```bash
# Production-ready with all optimizations
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Cloud Deployment
- **AWS/GCP/Azure**: Use provided Docker containers
- **Railway/Render**: One-click deployment ready
- **VPS**: Standard Docker Compose deployment
- **Kubernetes**: Helm charts available in `/k8s` directory

## 🔐 Security Best Practices

### Environment Security
```env
# Use strong passwords
POSTGRES_PASSWORD=use_a_strong_random_password
NEO4J_PASSWORD=another_strong_password

# Limit access
POSTGRES_HOST=localhost  # Don't expose to 0.0.0.0 in production
REDIS_HOST=localhost

# API key security
DISCORD_BOT_TOKEN=keep_this_secret
LLM_CHAT_API_KEY=also_keep_secret
```

### Production Security
- Use Docker secrets for sensitive data
- Enable TLS/SSL for all external connections
- Regular security updates
- Monitor access logs
- Implement rate limiting

## 📊 Monitoring & Maintenance

### Health Monitoring
```bash
# Service health
./bot.sh status

# Application health endpoint
curl http://localhost:9090/health

# Detailed status
curl http://localhost:9090/status | jq
```

### Backup & Recovery
```bash
# Create backup
./bot.sh backup create

# List backups
./bot.sh backup list

# Restore backup
./bot.sh backup restore backup_20240101_120000
```

### Performance Monitoring
- Monitor memory usage with `docker stats`
- Check response times via health endpoints
- Review bot latency in Discord
- Monitor database connection pools

## 🎨 Customization

### Personality Customization
Choose from pre-built personalities or create your own:

```env
# Pre-built options
BOT_SYSTEM_PROMPT_FILE=./prompts/empathetic_companion_template.md
BOT_SYSTEM_PROMPT_FILE=./prompts/professional_ai_template.md
BOT_SYSTEM_PROMPT_FILE=./prompts/casual_friend_template.md

# Create custom personality
BOT_SYSTEM_PROMPT_FILE=./prompts/my_custom_personality.md
```

### Adding Custom Commands
1. Create handler in `src/handlers/`
2. Register in `src/main.py`
3. Follow dependency injection pattern
4. Add tests in `tests/`

### Database Customization
- SQLite: Simple, file-based (default)
- PostgreSQL: Production-ready, scalable
- Add custom models in `src/database/models/`

## 🤝 Contributing

### Development Process
1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Develop** with tests: Follow TDD practices
4. **Test** thoroughly: `pytest -v`
5. **Document** changes: Update relevant docs
6. **Submit** a pull request

### Code Standards
- **Python 3.13+** required
- **Type hints** for all functions
- **Docstrings** for public APIs
- **Black** code formatting
- **Pytest** for testing
- **Async/await** for I/O operations

### Testing Requirements
```bash
# All tests must pass
pytest

# Coverage reporting
pytest --cov=src

# Integration tests (requires running LLM)
pytest -m integration
```

---

## 🎉 Welcome to WhisperEngine!

Whether you're a user looking to add an intelligent AI companion to your Discord server or a developer interested in contributing to cutting-edge AI conversation technology, we're excited to have you join our community!

**Next Steps:**
1. ⭐ Star the repository if you find it useful
2. 🚀 Follow the Quick Start guide above
3. 💬 Join our community discussions
4. 🐛 Report issues or suggest features
5. 🤝 Consider contributing to the project

Happy coding! 🎯