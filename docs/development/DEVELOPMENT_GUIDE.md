# 🔧 WhisperEngine Development Guide

**Complete setup guide for developers who want to modify WhisperEngine's source code.**

> **Note**: This guide is for **developers only**. If you just want to use WhisperEngine, see [Quick Start Guide](../guides/QUICKSTART.md) for the end-user setup.

## 📋 Developer Prerequisites

### **Required Software**
- **[Git](https://git-scm.com/downloads)** - For source code access
- **[Docker Desktop](https://www.docker.com/products/docker-desktop/)** - For containerized services
- **[Python 3.11+](https://www.python.org/downloads/)** - For WhisperEngine development
- **[Node.js 18+](https://nodejs.org/)** - For web UI development
- **An LLM API Key** - Get one from [OpenRouter](https://openrouter.ai)

### **System Requirements**
- **8GB RAM minimum** (16GB recommended for development)
- **10GB free disk space** for source code, containers, and dependencies
- **Git knowledge** - Basic familiarity with Git workflows

## 🚀 Development Setup

### **1. Clone the Repository**
```bash
git clone https://github.com/whisperengine-ai/whisperengine.git
cd whisperengine
```

### **2. Set Up Python Environment**
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
# OR
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### **3. Configure Development Environment**
```bash
# Copy development template
cp .env.template .env.development

# Edit configuration (add your API key)
nano .env.development  # or your preferred editor
```

### **4. Set Up Infrastructure Services**
```bash
# Start only infrastructure (PostgreSQL, Qdrant, Redis)
./bot.sh start native

# Verify services are running
docker ps
```

### **5. Run Database Migrations**
```bash
# Run migrations to set up database schema
source .venv/bin/activate
python scripts/run_migrations.py
```

### **6. Test Your Setup**
```bash
# Test the bot natively
python run.py

# In another terminal, test API
curl http://localhost:9090/health
```

## 🏗️ Development Architecture Options

### **Option 1: Native Bot + Containerized Services** (Recommended)

**Best for:**
- ✅ Live debugging with breakpoints
- ✅ Faster code iteration
- ✅ IDE integration
- ✅ Direct access to logs
- ✅ Easy dependency management

**How it works:**
- Infrastructure services (PostgreSQL, Redis, Qdrant) run in containers
- Bot code runs natively on your machine
- Bot connects to containerized services via localhost

**Commands:**
```bash
# Start infrastructure only
./bot.sh start native

# Run bot natively (separate terminal)
source .venv/bin/activate
python run.py

# Or with specific environment
cp .env.development .env
python run.py
```

### **Option 2: Full Containerization**

**Best for:**
- ✅ Production-like environment
- ✅ Consistent across team members
- ✅ Easy deployment testing
- ✅ Testing Docker configurations

**Commands:**
```bash
# Full development environment
./bot.sh start dev

# Or specific configurations
docker-compose -f docker-compose.dev.yml up -d
```

### **Option 3: Multi-Bot Development**

**Best for:**
- ✅ Testing multiple characters
- ✅ Advanced feature development
- ✅ Production simulation

**Commands:**
```bash
# Generate multi-bot configuration
source .venv/bin/activate
python scripts/generate_multi_bot_config.py

# Start all bots
./multi-bot.sh start all

# Start specific bot
./multi-bot.sh start elena
```

## 🔧 Development Workflows

### **Making Code Changes**

**Hot Reload Development:**
```bash
# Start infrastructure
./bot.sh start native

# Run with auto-reload (if available)
python run.py --reload

# Or manually restart after changes
# Kill python run.py and restart
```

**Containerized Development:**
```bash
# Use development compose file with volume mounts
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker logs whisperengine-dev-bot -f

# Restart after code changes
docker-compose -f docker-compose.dev.yml restart whisperengine-bot
```

### **Testing Your Changes**

**Unit Tests:**
```bash
source .venv/bin/activate
pytest tests/unit/
```

**Integration Tests:**
```bash
# Ensure infrastructure is running
./bot.sh start native

# Run integration tests
pytest tests/integration/
```

**Manual Testing:**
```bash
# Test HTTP API
curl -X POST http://localhost:9090/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_dev",
    "message": "Hello from development!",
    "context": {"platform": "api"}
  }'

# Test Discord (if Discord token configured)
# Send message in Discord channel
```

### **Database Development**

**Creating Migrations:**
```bash
source .venv/bin/activate

# Generate new migration
./scripts/migrations/db-migrate.sh create "Add your feature description"

# Edit the generated file in alembic/versions/
# Test migration
./scripts/migrations/db-migrate.sh upgrade
```

**Resetting Development Database:**
```bash
# Stop services
./bot.sh stop

# Remove database volume
docker volume rm whisperengine_postgres_data

# Restart and run migrations
./bot.sh start native
python scripts/run_migrations.py
```

## 🎭 Character Development

### **Creating Test Characters**

**Via Database:**
```bash
# Use character import script
python batch_import_characters.py

# Or create directly in PostgreSQL CDL tables
# See: src/characters/cdl/ for schema
```

**Via Web Interface:**
```bash
# Start web UI development
cd cdl-web-ui
npm install
npm run dev

# Access at http://localhost:3000
```

### **Testing Character Behavior**

**Direct Python Testing:**
```bash
# Create validation test
source .venv/bin/activate
python tests/automated/test_character_direct_validation.py
```

**Discord Testing:**
```bash
# Set up Discord bot token in .env.development
# Test character responses in Discord
```

## 🔍 Debugging

### **Common Development Issues**

**Port Conflicts:**
```bash
# Check what's using development ports
lsof -i :9090  # API port
lsof -i :5432  # PostgreSQL
lsof -i :6333  # Qdrant

# Kill conflicting processes
kill -9 <PID>
```

**Database Connection Issues:**
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Check connection
python -c "import psycopg2; print('DB connection OK')"

# View PostgreSQL logs
docker logs whisperengine-postgres
```

**Missing Dependencies:**
```bash
# Reinstall all dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

### **Development Logging**

**Enable Debug Logging:**
```bash
# In your .env.development file
LOG_LEVEL=DEBUG
ENABLE_PROMPT_LOGGING=true

# View logs
tail -f logs/bot.log
tail -f logs/prompts/*.json
```

**Container Logs:**
```bash
# View all container logs
docker-compose logs -f

# Specific container
docker logs whisperengine-postgres -f
docker logs whisperengine-qdrant -f
```

## 🚀 Building and Distribution

### **Building Docker Images**

**Local Build:**
```bash
# Build main application
docker build -t whisperengine/whisperengine:local .

# Build web UI
cd cdl-web-ui
docker build -t whisperengine/whisperengine-ui:local .
```

**Multi-platform Build:**
```bash
# Use build script
./rebuild-multiplatform.sh

# Or manual buildx
docker buildx build --platform linux/amd64,linux/arm64 \
  -t whisperengine/whisperengine:latest .
```

### **Testing Built Images**

```bash
# Test with built images
docker-compose -f docker-compose.quickstart.yml up -d

# Verify functionality
curl http://localhost:9090/health
```

## 🤝 Contributing

### **Development Workflow**

1. **Fork the Repository**
   ```bash
   # Fork on GitHub, then clone your fork
   git clone https://github.com/YOUR_USERNAME/whisperengine.git
   ```

2. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make Changes**
   - Follow code style guidelines
   - Add tests for new features
   - Update documentation

4. **Test Changes**
   ```bash
   # Run full test suite
   pytest tests/
   
   # Test with direct validation
   python tests/automated/test_your_feature_direct_validation.py
   ```

5. **Submit Pull Request**
   - Push to your fork
   - Create PR with clear description
   - Include test results

### **Code Style Guidelines**

**Python:**
- Follow PEP 8
- Use type hints
- Add docstrings for public functions
- Use async/await for I/O operations

**Documentation:**
- Update relevant MD files
- Add examples for new features
- Keep documentation current

**Git Commits:**
- Use conventional commit format
- Include clear descriptions
- Reference issues when applicable

## 📚 Advanced Development

### **Architecture Understanding**

**Key Components:**
- `src/core/` - Bot initialization and Discord integration
- `src/memory/` - Vector-native memory system
- `src/characters/` - CDL character system
- `src/prompts/` - Prompt building and CDL integration
- `src/intelligence/` - Conversation intelligence features

**Data Flow:**
```
Discord Message → Security Validation → Memory Retrieval → 
CDL Character Enhancement → Prompt Building → LLM Generation → 
Memory Storage → Response Delivery
```

### **Performance Optimization**

**Memory Profiling:**
```bash
# Profile memory usage
python -m memory_profiler run.py

# Profile specific function
python utilities/performance/performance_comparison.py
```

**Database Optimization:**
```bash
# Analyze query performance
python utilities/debug/debug_memory_manager.py

# Check database statistics
python scripts/analyze_database_performance.py
```

### **Custom Features Development**

**Adding New Intelligence Features:**
1. Create feature module in `src/intelligence/`
2. Add integration point in `src/core/message_processor.py`
3. Create direct validation test
4. Update documentation

**Adding New Memory Types:**
1. Extend memory protocol in `src/memory/memory_protocol.py`
2. Implement new memory manager
3. Add factory support
4. Test with existing character system

## 🛟 Development Support

### **Getting Help**

- **📖 Code Documentation**: Extensive inline documentation
- **🔧 Architecture Docs**: [Architecture Overview](../architecture/README.md)
- **🐛 Issues**: [GitHub Issues](https://github.com/whisperengine-ai/whisperengine/issues)
- **💬 Development Chat**: Discord #dev-discussion (Coming Soon)

### **Common Development Questions**

**Q: How do I add a new character field?**
A: Update CDL database schema in `src/characters/cdl/`, run migrations, update web UI forms.

**Q: How do I test new memory features?**
A: Create direct validation test, use `tests/automated/test_*_direct_validation.py` pattern.

**Q: How do I debug LLM prompts?**
A: Enable `ENABLE_PROMPT_LOGGING=true`, check `logs/prompts/*.json` files.

**Q: How do I add new LLM providers?**
A: Extend `src/llm/llm_protocol.py`, implement provider class, add factory support.

---

**Ready to contribute?** Start with [Contributing Guide](CONTRIBUTING.md) and dive into the codebase! 🚀

**Commands:**
```bash
# Everything in containers
./bot.sh start dev

# Or manually:
cp .env.production .env
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

## 📁 **Environment Files**

| File | Purpose | Bot Location | Service Hosts |
|------|---------|--------------|---------------|
| `.env.development` | Native bot development | Host machine | `localhost` |
| `.env.production` | Containerized deployment | Container | `redis`, `postgres`, `qdrant` |
| `.env` | Active configuration | Auto-detected | Auto-selected |

## 🔧 **Environment Auto-Detection**

The bot automatically detects its environment:

```python
# In run.py - automatically loads the right config
from env_manager import load_environment
load_environment()  # Auto-detects development vs production
```

**Detection logic:**
- **Development mode**: When `REDIS_HOST=localhost` or running outside container
- **Production mode**: When `REDIS_HOST=redis` or running inside container

## 🐛 **Debugging Workflows**

### **VS Code Debugging (Native Mode)**

1. Start infrastructure:
   ```bash
   ./bot.sh start native
   ```

2. Create `.vscode/launch.json`:
   ```json
   {
     "version": "0.2.0",
     "configurations": [
       {
         "name": "Debug Discord Bot",
         "type": "python",
         "request": "launch",
         "program": "${workspaceFolder}/run.py",
         "console": "integratedTerminal",
         "env": {
           "PYTHONPATH": "${workspaceFolder}"
         }
       }
     ]
   }
   ```

3. Set breakpoints and press F5

### **Live Code Reloading**

For faster development, consider using `watchdog`:

```bash
pip install watchdog
python -m watchdog src --recursive --patterns="*.py" --command="python run.py"
```

## 🔍 **Service Health Checks**

Check if services are ready:

```bash
# Redis
docker-compose exec redis redis-cli ping

# PostgreSQL
docker-compose exec postgres pg_isready -U bot_user

# Qdrant Vector Database
curl http://localhost:6333/health

# All at once
python env_manager.py --mode development --info
```

## 📊 **Development vs Production Comparison**

| Aspect | Development (Native) | Production (Containerized) |
|--------|---------------------|---------------------------|
| **Bot Code** | Native Python | Docker container |
| **Services** | Docker containers | Docker containers |
| **Networking** | `localhost` | Docker network |
| **Debugging** | Full IDE support | Docker logs only |
| **Performance** | Faster iteration | Production-like |
| **Dependencies** | Local pip/venv | Docker image |

## 🛠️ **Common Development Tasks**

### **Start fresh development session:**
```bash
# Stop everything
./bot.sh stop

# Start infrastructure
./bot.sh start native

# Run bot (new terminal)
python run.py
```

### **Switch between modes:**
```bash
# Switch to native development
cp .env.development .env

# Switch to containerized
cp .env.production .env
```

### **Database management:**
```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U bot_user -d discord_bot

# Check Redis
docker-compose exec redis redis-cli

# View Qdrant collections
curl http://localhost:6333/collections
```

### **Troubleshooting:**

**"Connection refused" errors:**
- Check if services are running: `docker-compose ps`
- Verify correct .env file is loaded
- Check port conflicts: `lsof -i :6379` (Redis), `:5432` (PostgreSQL), `:6333` (Qdrant)

**Import errors:**
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt`
- Check PYTHONPATH includes project root

## 🎬 **Recommended Development Workflow**

1. **Morning startup:**
   ```bash
   ./bot.sh start native
   ```

2. **Code in your IDE** with full debugging support

3. **Run/test changes:**
   ```bash
   python run.py
   ```

4. **End of day:**
   ```bash
   ./bot.sh stop
   ```

This gives you the best of both worlds: production-like infrastructure with native development experience!
