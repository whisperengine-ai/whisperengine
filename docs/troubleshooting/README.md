# WhisperEngine Troubleshooting Guide

## � Specific Issue Guides

- **[YAML Error on Line 25 + WSL Issues](YAML_ERROR_SOLUTION.md)** - Windows users getting YAML syntax errors
- **[Windows PowerShell curl Error](WINDOWS_POWERSHELL_SETUP.md)** - "blank argument where content is expected"
- **[Windows Docker Issues](WINDOWS_DOCKER_ISSUES.md)** - Comprehensive Windows troubleshooting
- **[Docker Compose Files Explained](../deployment/DOCKER_COMPOSE_FILES_EXPLAINED.md)** - Which file to use and why

## �🚨 Most Common Issues

### Database Migration Errors

**Symptoms:**
- Error: "relation 'schema_migrations' already exists"
- Error: "database migration failed"
- Setup fails during database initialization

**Solution:**
Run the cleanup script to remove old data, then setup again:

**macOS/Linux:**
```bash
curl -sSL https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/cleanup-docker.sh | bash
```

**Windows (PowerShell):**
```powershell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/cleanup-docker.ps1" -OutFile "cleanup.ps1"; .\cleanup.ps1
```

**Windows (Command Prompt):**
```cmd
curl -sSL https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/cleanup-docker.bat -o cleanup.bat && cleanup.bat
```

Then run setup again.

---

### Docker Not Running

**Symptoms:**
- Error: "Cannot connect to the Docker daemon"
- Error: "docker: command not found"

**Solution:**
1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/)
2. Start Docker Desktop and wait for it to fully initialize
3. Verify with: `docker ps`

---

### Upgrading from v1.0.6

**Symptoms:**
- Error: "alembic: command not found" 
- Database migration failures during upgrade
- "OCI runtime exec failed" when running alembic commands

**Root Cause:**
v1.0.6 containers don't have Alembic installed. You need to update containers first.

**Solution:**
```bash
# Step 1: Update to latest containers (includes Alembic)
docker-compose down
docker-compose pull
docker-compose up -d

# Step 2: ONLY THEN mark existing database as current
docker exec whisperengine-assistant alembic stamp head

# Step 3: Verify status
docker exec whisperengine-assistant alembic current
```

**If still having issues:**
```bash
# Complete reset (WARNING: Deletes all data)
curl -sSL https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/cleanup-docker.sh | bash

# Then run setup again
curl -sSL https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/setup-containerized.sh | bash
```

---

### Port Already in Use

**Symptoms:**
- Error: "port is already allocated"
- Error: "bind: address already in use"

**Required Ports:**
- `9090` - WhisperEngine API
- `3001` - Web Interface
- `5432` - PostgreSQL
- `6333` - Qdrant
- `8086` - InfluxDB

**Solution:**
Find and stop conflicting services:

**macOS/Linux:**
```bash
# Find process using port
lsof -i :9090

# Kill process (replace PID with actual process ID)
kill -9 <PID>
```

**Windows (PowerShell):**
```powershell
# Find process using port
netstat -ano | findstr :9090

# Kill process (replace PID with actual process ID)
taskkill /PID <PID> /F
```

---

### Services Not Starting

**Symptoms:**
- Containers exit immediately after starting
- "Container whisperengine-assistant exited with code 1"

**Solution:**

1. **Check logs:**
   ```bash
   docker logs whisperengine-assistant --tail 50
   ```

2. **Common causes:**
   - Missing or invalid API key in `.env`
   - PostgreSQL not ready yet (wait 30 seconds and retry)
   - Qdrant initialization timeout

3. **Fix and restart:**
   ```bash
   # Edit your .env file
   nano .env  # or vim, notepad, etc.
   
   # Restart services
   docker-compose restart
   ```

---

### Cannot Access Web Interface

**Symptoms:**
- http://localhost:3001 doesn't load
- "Connection refused" error

**Solution:**

1. **Check if container is running:**
   ```bash
   docker ps | grep whisperengine-web-ui
   ```

2. **Check logs:**
   ```bash
   docker logs whisperengine-web-ui --tail 50
   ```

3. **Restart web interface:**
   ```bash
   docker-compose restart whisperengine-web-ui
   ```

---

### API Returns Errors

**Symptoms:**
- 500 Internal Server Error
- Timeout errors
- "LLM client initialization failed"

**Solution:**

1. **Verify API key in `.env`:**
   ```bash
   # Check current config
   docker exec whisperengine-assistant env | grep LLM
   ```

2. **Check LLM service is configured:**
   - OpenRouter: https://openrouter.ai/keys (verify key is active)
   - OpenAI: https://platform.openai.com/api-keys
   - Local: Ensure LM Studio/Ollama is running

3. **Test API connectivity:**
   ```bash
   # Test OpenRouter
   curl -H "Authorization: Bearer YOUR_API_KEY" https://openrouter.ai/api/v1/models
   ```

---

### Character Data Not Loading

**Symptoms:**
- "Character 'assistant' not found"
- Web interface shows no characters

**Solution:**

1. **Check database connection:**
   ```bash
   docker logs whisperengine-assistant | grep -i "database\|postgres"
   ```

2. **Verify seed data was applied:**
   ```bash
   docker exec whisperengine-postgres psql -U whisperengine -d whisperengine -c "SELECT * FROM characters;"
   ```

3. **If no characters, run cleanup and setup again**

---

### Slow Performance

**Symptoms:**
- API responses take 30+ seconds
- High CPU/memory usage

**Solution:**

1. **Check model size:**
   - Use smaller models: `anthropic/claude-3-haiku` or `openai/gpt-4o-mini`
   - Avoid large local models on limited hardware

2. **Increase Docker resources:**
   - Docker Desktop → Settings → Resources
   - Allocate more RAM (recommended: 4GB minimum)
   - Allocate more CPU cores

3. **Check system resources:**
   ```bash
   docker stats
   ```

---

## 🔍 Diagnostic Commands

### View All Container Status
```bash
docker ps -a
```

### Check Container Logs
```bash
# Main bot
docker logs whisperengine-assistant --tail 50

# Database
docker logs whisperengine-postgres --tail 50

# Vector database
docker logs whisperengine-qdrant --tail 50

# Web interface
docker logs whisperengine-web-ui --tail 50
```

### Check Database Tables
```bash
docker exec whisperengine-postgres psql -U whisperengine -d whisperengine -c "\dt"
```

### Test API Health
```bash
curl http://localhost:9090/health
```

### Check Network Connectivity
```bash
docker network inspect whisperengine-network
```

---

## 🆘 Emergency Reset

If nothing else works, perform a complete reset:

1. **Cleanup all WhisperEngine data:**
   ```bash
   # Use appropriate cleanup script for your OS (see above)
   ```

2. **Verify everything is removed:**
   ```bash
   docker ps -a | grep whisperengine  # Should be empty
   docker volume ls | grep whisperengine  # Should be empty
   ```

3. **Run setup again:**
   ```bash
   # Use appropriate setup script for your OS
   ```

---

## 📝 Getting More Help

If you're still experiencing issues:

1. **Collect diagnostic information:**
   ```bash
   # Save logs
   docker logs whisperengine-assistant > assistant.log 2>&1
   docker logs whisperengine-postgres > postgres.log 2>&1
   
   # Save configuration
   docker inspect whisperengine-assistant > assistant-config.json
   ```

2. **Create a GitHub issue:**
   - Visit: https://github.com/whisperengine-ai/whisperengine/issues
   - Include: OS, Docker version, error messages, relevant logs
   - Attach log files (remove any API keys first!)

3. **Check existing issues:**
   - Search: https://github.com/whisperengine-ai/whisperengine/issues
   - Someone may have already solved your problem

---

## 📚 Additional Resources

- **[Cleanup Guide](../deployment/CLEANUP_SCRIPTS.md)** - Detailed cleanup documentation
- **[Quick Reference](../../QUICK_REFERENCE.md)** - Common commands cheat sheet
- **[Container Operations](../../CONTAINERIZED_OPERATIONS_GUIDE.md)** - Advanced Docker operations
- **[API Documentation](../api/README.md)** - API usage and integration
