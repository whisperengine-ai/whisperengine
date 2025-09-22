# WhisperEngine Bot Operations Guide

## Overview

WhisperEngine uses a **unified bot management system** via `multi-bot.sh`. Whether you want to run 1 bot or 5 bots, you use the same script and configuration approach. This eliminates complexity and provides consistent operations regardless of scale.

**Key Philosophy**: One script (`multi-bot.sh`), scalable from 1 to N bots, shared infrastructure, simple commands.

## Quick Reference

### Essential Commands (Works for 1 or Many Bots)

```bash
# Start all configured bots
./multi-bot.sh start

# Stop all bots  
./multi-bot.sh stop

# Check status
./multi-bot.sh status

# Restart all bots (CORRECT METHOD)
./multi-bot.sh stop && ./multi-bot.sh start

# Build containers
./multi-bot.sh build
```

### Individual Bot Management

```bash
# Start specific bot only
./multi-bot.sh start elena
./multi-bot.sh start marcus  
./multi-bot.sh start marcus-chen
./multi-bot.sh start gabriel
./multi-bot.sh start dream

# Stop specific bot
./multi-bot.sh stop elena

# Restart specific bot
./multi-bot.sh restart elena

# View logs
./multi-bot.sh logs elena
./multi-bot.sh logs infrastructure
```

## Single Bot Workflow (Most Common Use Case)

**Most users want to run just ONE bot.** Here's the complete workflow:

### Step 1: Configure One Bot Environment

```bash
# Choose your bot (elena, marcus, marcus-chen, gabriel, or dream)
cp .env.elena.example .env.elena

# Edit the environment file
vim .env.elena  # or nano, code, etc.

# Required settings:
# - DISCORD_BOT_TOKEN=your_discord_bot_token
# - BOT_NAME=elena  
# - CHARACTER_FILE=characters/examples/elena-rodriguez.json
```

### Step 2: Start Your Single Bot

```bash
# Start just Elena (infrastructure starts automatically)
./multi-bot.sh start elena

# Check that it's running
./multi-bot.sh status
```

### Step 3: Use Your Bot

Your bot is now running with:
- ✅ **Full WhisperEngine AI capabilities**
- ✅ **Vector memory system** (Qdrant)
- ✅ **Persistent storage** (PostgreSQL)  
- ✅ **Session cache** (Redis)
- ✅ **Health monitoring** at http://localhost:9091/health

### That's It!

You now have a fully functional WhisperEngine bot. The "multi-bot" system gracefully handles single bots by only starting what's configured.

### Common Single Bot Operations

```bash
# View logs
./multi-bot.sh logs elena

# Stop the bot
./multi-bot.sh stop elena

# Restart the bot
./multi-bot.sh restart elena

# Stop everything (bot + infrastructure)
./multi-bot.sh stop
```

### Adding More Bots Later

When you're ready to scale:

```bash
# Add Marcus bot
cp .env.marcus.example .env.marcus
# Edit .env.marcus with different Discord token

# Start Marcus alongside Elena
./multi-bot.sh start marcus

# Or restart all to include both
./multi-bot.sh stop && ./multi-bot.sh start
```

---

## Available Bots

| Bot Name | Character | Description |
|----------|-----------|-------------|
| `elena` | Elena Rodriguez | Marine Biologist, Environmentalist |
| `marcus` | Marcus Thompson | AI Researcher, Philosopher |
| `marcus-chen` | Marcus Chen | Indie Game Developer, Creative |
| `gabriel` | Gabriel | (Configure character as needed) |
| `dream` | Dream of the Endless | Mythological Morpheus |

**Want just one bot?** Only configure the `.env` file for that bot. The system automatically scales to however many bots you configure.

## Infrastructure Services

| Service | Port | Description |
|---------|------|-------------|
| PostgreSQL | 5433 | Database (multi-bot instance) |
| Redis | 6380 | Cache/Session (multi-bot instance) |
| Qdrant | 6335 | Vector Database (multi-bot instance) |

### Health Check Endpoints

- Elena Bot: `http://localhost:9091/health`
- Marcus Bot: `http://localhost:9092/health`
- Marcus Chen Bot: `http://localhost:9093/health`
- Dream Bot: `http://localhost:9094/health`

## Common Operations

### Complete System Restart

**⚠️ IMPORTANT**: The script does NOT support `restart all`. Use this sequence:

```bash
# Method 1: Clean restart (recommended)
./multi-bot.sh stop
./multi-bot.sh start

# Method 2: Force clean restart
./multi-bot.sh stop
docker system prune -f  # Optional: clean up resources
./multi-bot.sh start
```

### Single Bot Setup (Most Common Use Case)

If you want to run just **one bot**, this is actually the simplest approach:

```bash
# 1. Configure only one bot environment file
cp .env.elena.example .env.elena
# Edit .env.elena with your Discord token and settings

# 2. Start just that bot
./multi-bot.sh start elena

# 3. Check status
./multi-bot.sh status
```

**That's it!** Infrastructure starts automatically, and you have a single bot running with full WhisperEngine capabilities.

### Adding More Bots Later

To scale from 1 bot to multiple bots:

```bash
# Add another bot
cp .env.marcus.example .env.marcus
# Edit .env.marcus with different Discord token

# Start the new bot (existing bot keeps running)
./multi-bot.sh start marcus

# Or restart all to include the new bot
./multi-bot.sh stop && ./multi-bot.sh start
```

### Troubleshooting Failed Starts

If `./multi-bot.sh start` fails:

```bash
# 1. Check container status
./multi-bot.sh status

# 2. Stop everything cleanly
./multi-bot.sh stop

# 3. Check for lingering containers
docker ps --filter "name=whisperengine-"

# 4. Force stop if needed
docker stop $(docker ps -q --filter "name=whisperengine-")

# 5. Clean up resources
docker system prune -f

# 6. Rebuild if necessary
./multi-bot.sh build

# 7. Start fresh
./multi-bot.sh start
```

### Environment File Issues

Each bot requires its own environment file:

```bash
# Check required files exist
ls -la .env.elena .env.marcus .env.marcus-chen .env.dream

# Copy from examples if missing
cp .env.elena.example .env.elena
cp .env.marcus.example .env.marcus
cp .env.marcus-chen.example .env.marcus-chen
cp .env.dream.example .env.dream
```

**Required environment files:**
- `.env.elena` - Elena bot configuration
- `.env.marcus` - Marcus Thompson bot configuration  
- `.env.marcus-chen` - Marcus Chen bot configuration
- `.env.dream` - Dream bot configuration

### Port Conflicts

If you get port conflicts:

```bash
# Check what's using multi-bot ports
lsof -i :5433  # PostgreSQL
lsof -i :6380  # Redis
lsof -i :6335  # Qdrant
lsof -i :9091  # Elena health check
lsof -i :9092  # Marcus health check
lsof -i :9093  # Marcus Chen health check
lsof -i :9094  # Dream health check

# Stop single-bot instance if running
./bot.sh stop
```

## Logs and Monitoring

### Viewing Logs

```bash
# All logs (mixed)
docker compose -f docker-compose.multi-bot.yml logs -f

# Specific bot logs
./multi-bot.sh logs elena
./multi-bot.sh logs marcus
./multi-bot.sh logs marcus-chen
./multi-bot.sh logs dream

# Infrastructure logs
./multi-bot.sh logs infrastructure

# Follow logs in real-time
./multi-bot.sh logs elena  # Automatically follows (-f)
```

### Health Monitoring

```bash
# Quick health check all services
curl -s http://localhost:9091/health | jq .  # Elena
curl -s http://localhost:9092/health | jq .  # Marcus
curl -s http://localhost:9093/health | jq .  # Marcus Chen
curl -s http://localhost:9094/health | jq .  # Dream

# Check container health
./multi-bot.sh status
```

## Performance Optimization

### Memory Management

```bash
# Monitor memory usage
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"

# Clean up unused resources
docker system prune -f
docker volume prune -f
```

### Log Management

Log files are stored in Docker volumes:
- `whisperengine-multi_elena_logs`
- `whisperengine-multi_marcus_logs`
- `whisperengine-multi_marcus_chen_logs`
- `whisperengine-multi_dream_logs`

```bash
# Clean up old logs if needed
docker volume rm whisperengine-multi_elena_logs
docker volume rm whisperengine-multi_marcus_logs
docker volume rm whisperengine-multi_marcus_chen_logs
docker volume rm whisperengine-multi_dream_logs
```

## Troubleshooting Guide

### Problem: `restart all` Command Not Working

**Error:** `[ERROR] Unknown bot: all. Available: elena, marcus, marcus-chen, dream`

**Solution:** The script doesn't support `restart all`. Use:
```bash
./multi-bot.sh stop && ./multi-bot.sh start
```

### Problem: Container Build Failures

**Symptoms:** Build fails, containers won't start

**Solutions:**
```bash
# 1. Clean build
./multi-bot.sh stop
docker system prune -f
./multi-bot.sh build --no-cache

# 2. If still failing, check Docker resources
docker system df
docker system prune -a  # Warning: removes all unused images
```

### Problem: Memory Isolation Issues

**Symptoms:** Bots seeing each other's memories

**Diagnosis:**
```bash
# Check bot_name payload in vector database
docker exec whisperengine-multi-qdrant-1 /opt/qdrant/qdrant --help
```

**Solution:** Each bot uses `bot_name` payload filtering. Verify environment files have unique `BOT_NAME` values.

### Problem: Port Already in Use

**Error:** `port is already allocated`

**Solutions:**
```bash
# 1. Stop single-bot instance
./bot.sh stop

# 2. Find and stop conflicting services
docker ps --filter "publish=5433"
docker ps --filter "publish=6380"
docker ps --filter "publish=6335"

# 3. Force stop if needed
docker stop $(docker ps -q --filter "publish=5433")
```

### Problem: Environment File Missing

**Error:** `Missing environment files: .env.elena`

**Solution:**
```bash
# Copy from examples
cp .env.elena.example .env.elena

# Edit with correct Discord token
vim .env.elena
```

### Problem: Database Connection Issues

**Symptoms:** Bots start but can't connect to database

**Diagnosis:**
```bash
# Check infrastructure services
./multi-bot.sh logs infrastructure

# Check if databases are ready
docker exec whisperengine-multi-postgres-1 pg_isready
docker exec whisperengine-multi-redis-1 redis-cli ping
```

**Solutions:**
```bash
# 1. Wait for infrastructure startup (30-60 seconds)
./multi-bot.sh status

# 2. Restart infrastructure if needed
docker compose -f docker-compose.multi-bot.yml restart postgres redis qdrant
```

## Development Workflow

### Code Changes

```bash
# 1. Make code changes
# 2. Rebuild containers
./multi-bot.sh build

# 3. Restart affected bots
./multi-bot.sh restart elena  # If you changed Elena-specific code
./multi-bot.sh stop && ./multi-bot.sh start  # If you changed core code
```

### Character File Updates

Character files are automatically reloaded - no restart needed:
```bash
# Edit character file
vim characters/examples/elena-rodriguez.json

# Changes apply immediately, no restart required
```

### Environment Variable Changes

```bash
# 1. Edit environment file
vim .env.elena

# 2. Restart specific bot
./multi-bot.sh restart elena
```

## Security Considerations

### Discord Token Management

- Each bot needs its own Discord token
- Tokens are stored in separate `.env.*` files
- Never commit tokens to git
- Use different bot applications for each character

### Network Isolation

Multi-bot infrastructure runs on dedicated ports:
- Prevents conflicts with single-bot deployments
- Allows both systems to run simultaneously
- Each bot has isolated health check endpoints

## Backup and Recovery

### Memory Backup

```bash
# Backup vector database
docker exec whisperengine-multi-qdrant-1 qdrant-backup

# Backup PostgreSQL
docker exec whisperengine-multi-postgres-1 pg_dump -U postgres whisperengine > backup.sql
```

### Configuration Backup

```bash
# Backup all environment files
tar -czf multi-bot-config-$(date +%Y%m%d).tar.gz .env.elena .env.marcus .env.marcus-chen .env.dream

# Backup character files
tar -czf characters-$(date +%Y%m%d).tar.gz characters/
```

## Performance Benchmarks

Expected performance with all 4 bots running:

| Operation | Single Bot | Multi-Bot (4 bots) | Notes |
|-----------|------------|---------------------|--------|
| Memory Query | <1s | <1s per bot | Parallel processing |
| Vector Search | <500ms | <500ms per bot | Isolated collections |
| Response Generation | 2-5s | 2-5s per bot | LLM rate limits apply |

## Related Documentation

- [Multi-Bot Project Summary](MULTI_BOT_PROJECT_SUMMARY.md) - Architecture overview
- [Multi-Bot Validation Report](MULTI_BOT_VALIDATION_REPORT.md) - Testing results
- [Environment Variables Update Summary](ENVIRONMENT_VARIABLES_UPDATE_SUMMARY.md) - Configuration details
- [AI Features Audit Report](AI_FEATURES_AUDIT_REPORT.md) - Feature configuration

---

**Last Updated:** September 22, 2025  
**Version:** 1.0  
**Covers:** WhisperEngine Multi-Bot System v2.0