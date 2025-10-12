# 🔧 WhisperEngine Development Guide

**Complete setup guide for developers who want to modify WhisperEngine's source code.**

> **Note**: This guide is for **developers only**. If you just want to use WhisperEngine, see [Quick Start Guide](../guides/QUICKSTART.md) for the end-user setup.

## 📋 Developer Prerequisites

### **Required Software**
- **[Git](https://git-scm.com/downloads)** - For source code access
- **[Docker Desktop](https://www.docker.com/products/docker-desktop/)** - For containerized development (PRIMARY workflow)
- **[Python 3.11+](https://www.python.org/downloads/)** - For utility scripts only
- **[Node.js 18+](https://nodejs.org/)** - For web UI development (optional)
- **An LLM API Key** - Get one from [OpenRouter](https://openrouter.ai)

### **System Requirements**
- **8GB RAM minimum** (16GB recommended for development)
- **10GB free disk space** for source code, containers, and data
- **Git knowledge** - Basic familiarity with Git workflows

## 🚀 Development Setup

### **1. Clone the Repository**
\`\`\`bash
git clone https://github.com/whisperengine-ai/whisperengine.git
cd whisperengine
\`\`\`

### **2. Configure Environment**
\`\`\`bash
# Copy environment template for development bot
cp .env.template .env.elena

# Edit configuration (add your API keys)
nano .env.elena  # or your preferred editor

# CRITICAL: Add all required LLM configuration
# NOTE: LLM_CHAT_API_URL determines the actual provider (auto-detected from URL)
# LLM_CLIENT_TYPE is mainly for setup hints and logging
LLM_CLIENT_TYPE=openrouter
LLM_CHAT_API_URL=https://openrouter.ai/api/v1  # CRITICAL: Determines provider
LLM_CHAT_API_KEY=your_openrouter_key_here
LLM_CHAT_MODEL=mistralai/mistral-small  # RECOMMENDED: Tested model

# Set bot-specific settings
DISCORD_BOT_NAME=elena
HEALTH_CHECK_PORT=9091
QDRANT_COLLECTION_NAME=whisperengine_memory_elena
\`\`\`

> **⚠️ IMPORTANT**: `LLM_CHAT_API_URL` is what **actually determines** your LLM provider - WhisperEngine auto-detects the provider from the URL pattern. `LLM_CLIENT_TYPE` is used for setup hints and logging only.

> **🎯 Model Selection**: WhisperEngine has been thoroughly tested with:
**Tested Models** (Production-Ready):
- **Mistral**: `mistralai/mistral-small-3.2-24b-instruct`, `mistralai/mistral-medium-3.1`, `mistralai/mistral-nemo`
- **GPT-4**: `openai/gpt-4o`
- **GPT-5**: `openai/gpt-5-chat`
- **Claude Sonnet**: `anthropic/claude-sonnet-4`, `anthropic/claude-3.7-sonnet`, `anthropic/claude-3.5-sonnet`
> 
> Start with `mistralai/mistral-small-3.2-24b-instruct` for reliable development, then experiment with others. **Avoid**: Claude Haiku (expensive, poor character quality), GPT-3.5/4o-mini (inconsistent).

**Supported Provider URLs**:
| Provider | `LLM_CLIENT_TYPE` | `LLM_CHAT_API_URL` | API Key Required? |
|----------|-------------------|---------------------|-------------------|
| OpenRouter (Mistral, GPT, Claude) | `openrouter` | `https://openrouter.ai/api/v1` | ✅ Yes |
| OpenAI Direct | `openai` | `https://api.openai.com/v1` | ✅ Yes |
| Ollama (Local) | `ollama` | `http://host.docker.internal:11434/v1` | ❌ No - runs locally |
| LM Studio (Local) | `lmstudio` | `http://host.docker.internal:1234/v1` | ❌ No - runs locally |

### **3. Start Development Environment**
\`\`\`bash
# Start infrastructure + development bot (RECOMMENDED)
./multi-bot.sh start elena

# View logs
docker logs whisperengine-elena-bot -f

# Check health
curl http://localhost:9091/health
\`\`\`

### **4. Verify Setup**
\`\`\`bash
# Test API endpoint
curl -X POST http://localhost:9091/api/chat \\
  -H "Content-Type: application/json" \\
  -d '{
    "user_id": "dev_user",
    "message": "Hello from development!",
    "context": {"platform": "api"}
  }'

# Check all containers running
docker ps
\`\`\`

## 🏗️ Development Architecture

### **Docker-Based Development** (PRIMARY Workflow)

**Why Docker-First?**
- ✅ **Consistent environment** - Same setup across all developers
- ✅ **No dependency hell** - All dependencies containerized
- ✅ **Production parity** - Development matches production
- ✅ **Easy infrastructure** - PostgreSQL, Qdrant, InfluxDB auto-configured
- ✅ **Multi-bot testing** - Test multiple characters simultaneously
- ✅ **Clean isolation** - Each bot has dedicated resources

**Architecture:**
- **Infrastructure Services**: PostgreSQL, Qdrant, InfluxDB (shared containers)
- **Bot Containers**: Each character runs in isolated container
- **Volume Mounts**: Source code mounted for live updates
- **Hot Reload**: Code changes reflected without rebuild (where supported)

**Start Development:**
\`\`\`bash
# Start single bot for development
./multi-bot.sh start elena

# Start multiple bots for testing interactions
./multi-bot.sh start elena
./multi-bot.sh start marcus

# View status
./multi-bot.sh status

# View logs
docker logs whisperengine-elena-bot -f
\`\`\`

### **Native Python** (Optional - NOT Recommended)

**Only use when:**
- Need live debugging with breakpoints (use Docker exec with debugpy instead)
- Special IDE integration requirements
- Testing specific Python environment issues

**Limitations:**
- Manual dependency installation required
- Database/infrastructure setup complex
- Not representative of production
- No multi-bot testing

**If you must:**
\`\`\`bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Start infrastructure only
docker-compose up postgres qdrant redis -d

# Run bot natively (not recommended)
python run.py
\`\`\`

## 🔧 Development Workflows

### **Making Code Changes**

**Standard Development Workflow:**
\`\`\`bash
# 1. Start your development bot
./multi-bot.sh start elena

# 2. Edit code in your IDE (changes are live-mounted)

# 3. Restart bot to apply changes
./multi-bot.sh restart elena

# 4. View logs to verify changes
docker logs whisperengine-elena-bot -f --tail 50

# 5. Test your changes
curl -X POST http://localhost:9091/api/chat \\
  -H "Content-Type: application/json" \\
  -d '{"user_id": "dev", "message": "test", "context": {}}'
\`\`\`

**Environment Changes:**
\`\`\`bash
# Environment changes require FULL stop/start (not just restart)
./multi-bot.sh stop elena
# Edit .env.elena
./multi-bot.sh start elena
\`\`\`

### **Testing Your Changes**

**Direct Python Validation** (PREFERRED method):
\`\`\`bash
# Set up environment
source .venv/bin/activate
export FASTEMBED_CACHE_PATH="/tmp/fastembed_cache"
export QDRANT_HOST="localhost"
export QDRANT_PORT="6334"
export POSTGRES_HOST="localhost"
export POSTGRES_PORT="5433"
export DISCORD_BOT_NAME=elena

# Run direct validation tests
python tests/automated/test_your_feature_direct_validation.py
\`\`\`

**HTTP API Testing:**
\`\`\`bash
# Test bot API endpoint
curl -X POST http://localhost:9091/api/chat \\
  -H "Content-Type: application/json" \\
  -d '{
    "user_id": "test_dev",
    "message": "Hello from development!",
    "context": {"platform": "api"}
  }'

# Check health endpoint
curl http://localhost:9091/health
\`\`\`

**Discord Integration Testing:**
\`\`\`bash
# Add Discord token to .env.elena
DISCORD_BOT_TOKEN=your_dev_bot_token
ENABLE_DISCORD=true

# Restart bot
./multi-bot.sh restart elena

# Send message in Discord to test
\`\`\`

**Unit Tests:**
\`\`\`bash
# Run in container (recommended)
docker exec whisperengine-elena-bot python -m pytest tests/unit/

# Or with virtual environment
source .venv/bin/activate
pytest tests/unit/
\`\`\`

### **Debugging**

**View Logs:**
\`\`\`bash
# Follow live logs
docker logs whisperengine-elena-bot -f

# Last 100 lines
docker logs whisperengine-elena-bot --tail 100

# All logs from specific service
docker logs whisperengine-postgres -f
docker logs whisperengine-qdrant -f
\`\`\`

**Interactive Container Shell:**
\`\`\`bash
# Enter running container
docker exec -it whisperengine-elena-bot /bin/bash

# Run commands inside container
docker exec whisperengine-elena-bot python -c "import sys; print(sys.version)"
\`\`\`

**Database Debugging:**
\`\`\`bash
# Connect to PostgreSQL
docker exec -it whisperengine-postgres psql -U whisperengine -d whisperengine

# Check CDL character data
\sql
SELECT name, normalized_name FROM cdl_identity;
\\q
\`\`\`

**Prompt Logging** (enable for debugging):
\`\`\`bash
# In .env.elena
ENABLE_PROMPT_LOGGING=true

# Restart bot
./multi-bot.sh restart elena

# View logged prompts
ls -la logs/prompts/Elena_*
cat logs/prompts/Elena_20251012_143000_*.json
\`\`\`

### **Database Development**

**Running Migrations:**
\`\`\`bash
# Mark database as current version (after updates)
docker exec whisperengine-elena-bot alembic stamp head

# Run migrations
docker exec whisperengine-elena-bot alembic upgrade head

# Check migration status
docker exec whisperengine-elena-bot alembic current
\`\`\`

**Creating New Migrations:**
\`\`\`bash
# Generate migration
docker exec whisperengine-elena-bot alembic revision -m "Add your feature"

# Edit generated file
# Located in: alembic/versions/

# Test migration
docker exec whisperengine-elena-bot alembic upgrade head
\`\`\`

**Resetting Development Database:**
\`\`\`bash
# Stop all services
./multi-bot.sh stop

# Remove database volume (⚠️ deletes all data)
docker volume rm whisperengine_postgres_data

# Restart - migrations run automatically
./multi-bot.sh start elena
\`\`\`

## 🎭 Character Development

### **Creating Test Characters**

**Via Web Interface:**
\`\`\`bash
# Start web UI development
cd cdl-web-ui
npm install
npm run dev

# Access at http://localhost:3000
# Create characters via UI
\`\`\`

**Via Database Import:**
\`\`\`bash
# Import legacy JSON characters
source .venv/bin/activate
python batch_import_characters.py

# Or create directly in PostgreSQL CDL tables
docker exec -it whisperengine-postgres psql -U whisperengine
\`\`\`

### **Testing Character Behavior**

**Direct Validation Testing:**
\`\`\`bash
# Create character-specific test
# Example: tests/automated/test_elena_character_validation.py

source .venv/bin/activate
export DISCORD_BOT_NAME=elena
python tests/automated/test_elena_character_validation.py
\`\`\`

**API Testing:**
\`\`\`bash
# Test character responses
curl -X POST http://localhost:9091/api/chat \\
  -H "Content-Type: application/json" \\
  -d '{
    "user_id": "test_dev",
    "message": "Tell me about your background",
    "context": {"platform": "api"}
  }'
\`\`\`

## �� Building and Distribution

### **Building Docker Images**

**Local Build:**
\`\`\`bash
# Build main application
docker build -t whisperengine/whisperengine:dev .

# Test built image
docker run -it --rm \\
  --env-file .env.elena \\
  -p 9091:9091 \\
  whisperengine/whisperengine:dev
\`\`\`

**Multi-platform Build** (for distribution):
\`\`\`bash
# Use build script
./rebuild-multiplatform.sh

# Or manual buildx
docker buildx build --platform linux/amd64,linux/arm64 \\
  -t whisperengine/whisperengine:latest \\
  --push .
\`\`\`

**Push to Docker Hub:**
\`\`\`bash
# Tag version
docker tag whisperengine/whisperengine:latest whisperengine/whisperengine:v1.0.9

# Push
docker push whisperengine/whisperengine:v1.0.9
docker push whisperengine/whisperengine:latest

# Or use helper script
./push-to-dockerhub.sh whisperengine v1.0.9
\`\`\`

## 🔍 Common Development Issues

### **Port Conflicts**
\`\`\`bash
# Check what's using ports
lsof -i :9091  # Bot API
lsof -i :5433  # PostgreSQL
lsof -i :6334  # Qdrant

# Kill conflicting process
kill -9 <PID>
\`\`\`

### **Container Won't Start**
\`\`\`bash
# Check logs
docker logs whisperengine-elena-bot

# Check disk space
docker system df

# Clean up if needed
docker system prune
\`\`\`

### **Database Connection Errors**
\`\`\`bash
# Check PostgreSQL is running
docker ps | grep postgres

# Test connection
docker exec whisperengine-postgres pg_isready

# View PostgreSQL logs
docker logs whisperengine-postgres
\`\`\`

### **Missing Dependencies**
\`\`\`bash
# Rebuild container with fresh dependencies
docker-compose build --no-cache whisperengine-elena-bot

# Or pull latest image
docker pull whisperengine/whisperengine:latest
\`\`\`

### **Environment Not Loading**
\`\`\`bash
# Verify .env.elena exists
ls -la .env.elena

# Check multi-bot configuration
cat multi-bot.sh | grep elena

# Regenerate multi-bot config
source .venv/bin/activate
python scripts/generate_multi_bot_config.py
\`\`\`

## 🤝 Contributing

### **Development Workflow**

1. **Fork & Clone**
   \`\`\`bash
   git clone https://github.com/YOUR_USERNAME/whisperengine.git
   cd whisperengine
   \`\`\`

2. **Create Feature Branch**
   \`\`\`bash
   git checkout -b feature/your-feature-name
   \`\`\`

3. **Set Up Development**
   \`\`\`bash
   # Copy environment
   cp .env.template .env.elena
   
   # Edit and add API keys
   nano .env.elena
   
   # Start development
   ./multi-bot.sh start elena
   \`\`\`

4. **Make Changes**
   - Edit code (changes are live-mounted)
   - Restart bot to apply: \`./multi-bot.sh restart elena\`
   - Test your changes

5. **Test Changes**
   \`\`\`bash
   # Direct validation tests (REQUIRED for new features)
   python tests/automated/test_your_feature_direct_validation.py
   
   # HTTP API tests
   curl -X POST http://localhost:9091/api/chat -H "Content-Type: application/json" -d '...'
   
   # Unit tests
   docker exec whisperengine-elena-bot python -m pytest tests/unit/
   \`\`\`

6. **Commit & Push**
   \`\`\`bash
   git add .
   git commit -m "feat: your feature description"
   git push origin feature/your-feature-name
   \`\`\`

7. **Submit Pull Request**
   - Create PR on GitHub
   - Include test results
   - Describe changes clearly

### **Code Style Guidelines**

**Python:**
- Follow PEP 8
- Use type hints
- Add docstrings to functions
- Use semantic naming (no "sprint1", "phase2" in variable names)

**Async Patterns:**
- All major operations should be async
- Use \`await\` for database and LLM calls
- Follow scatter-gather concurrency patterns

**Error Handling:**
- Use production error handlers
- Log errors with context
- Graceful degradation

**Memory Patterns:**
- Always use named vectors (content, emotion, semantic)
- Bot-specific collection isolation
- Follow established Qdrant patterns

### **Testing Requirements**

**For New Features:**
1. **Direct validation test** (REQUIRED) - \`tests/automated/test_feature_direct_validation.py\`
2. **HTTP API test** (if API changes)
3. **Unit tests** (for new modules)
4. **Integration test** (if multiple systems involved)

**Test Coverage:**
- Aim for >80% code coverage
- Test happy paths and error cases
- Include edge case testing

## 📚 Additional Resources

- **[Copilot Instructions](.github/copilot-instructions.md)** - AI development guidelines
- **[Architecture Docs](../architecture/)** - System design and patterns
- **[API Documentation](../api/)** - API reference
- **[Character System](../characters/)** - CDL and character design
- **[Testing Guide](../testing/)** - Testing strategies

## 🆘 Getting Help

- **📖 Documentation**: Browse [docs/](../) folder
- **🐛 Issues**: [GitHub Issues](https://github.com/whisperengine-ai/whisperengine/issues)
- **💬 Discussions**: [GitHub Discussions](https://github.com/whisperengine-ai/whisperengine/discussions)
- **📝 Copilot Instructions**: See \`.github/copilot-instructions.md\` for detailed development patterns

---

**🎉 Ready to contribute!** Start with a small feature or bug fix to get familiar with the codebase, then tackle larger features. The WhisperEngine community welcomes your contributions! 🚀
