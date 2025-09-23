# WhisperEngine Multi-Bot Setup Guide

> **📚 Documentation Structure**: This is the primary multi-bot setup guide. See also:
> - `MULTI_BOT_MEMORY_ARCHITECTURE.md` - Memory system architecture details
> - `MULTI_BOT_IMPLEMENTATION_GUIDE.md` - Technical implementation reference

## 🚀 Overview

WhisperEngine supports running multiple character bot containers that share the same infrastructure using a **template-based architecture**! This allows you to have different Discord bots with unique personalities (Elena the marine biologist, Marcus the AI researcher, etc.) all powered by the same backend services with pinned, stable versions.

## 🏗️ Template-Based Architecture

**Key Innovation**: Instead of programmatically generating Docker Compose files (which can break), WhisperEngine uses a template approach that fills in discovered bot configurations safely.

**Pinned Infrastructure Versions** (No more "latest" surprises!):
- **PostgreSQL**: `postgres:16.4-alpine` 
- **Redis**: `redis:7.4-alpine`
- **Qdrant**: `qdrant/qdrant:v1.15.4`

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Elena Bot     │    │   Marcus Bot    │    │  Marcus Chen    │
│  (Container)    │    │  (Container)    │    │  (Container)    │
│                 │    │                 │    │                 │
│ Token: Elena    │    │ Token: Marcus   │    │ Token: M.Chen   │
│ Character: *.json│    │ Character: *.json│    │ Character: *.json│
│ Port: 9091      │    │ Port: 9092      │    │ Port: 9093      │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
    ┌─────────────────────────────┼─────────────────────────────┐
    │                             │                             │
    │     SHARED INFRASTRUCTURE (PINNED VERSIONS)              │
    │                             │                             │
    │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
    │  │ PostgreSQL   │  │    Redis     │  │   Qdrant     │    │
    │  │16.4-alpine   │  │ 7.4-alpine   │  │  v1.15.4     │    │
    │  │ Port: 5433   │  │ Port: 6380   │  │ Port: 6335   │    │
    │  └──────────────┘  └──────────────┘  └──────────────┘    │
    └─────────────────────────────────────────────────────────┘
```

## 🔧 Template System Files

**SAFE TO EDIT**:
- `docker-compose.multi-bot.template.yml` - Infrastructure template with pinned versions
- `.env.{bot_name}` - Individual bot configurations  
- `characters/examples/*.json` - Character personality definitions

**AUTO-GENERATED (NEVER EDIT)**:
- `docker-compose.multi-bot.yml` - Generated from template + discovered bots
- `multi-bot.sh` - Generated management script with all discovered bots

### Key Benefits

- **Shared Infrastructure**: All bots share PostgreSQL, Redis, and Qdrant services
- **Memory Isolation**: Each Discord user has isolated memory regardless of which bot they interact with
- **Resource Efficiency**: Infrastructure scales with bot count, not duplicated per bot
- **Independent Deployment**: Start/stop individual bots without affecting others
- **Unique Personalities**: Each bot can have completely different character definitions

## 📁 Files Overview

- `docker-compose.multi-bot.yml` - Multi-bot container configuration
- `multi-bot.sh` - Management script for all bot operations
- `.env.elena` - Elena bot-specific environment variables
- `.env.marcus` - Marcus bot-specific environment variables  
- `.env.marcus-chen` - Marcus Chen bot-specific environment variables
- `characters/examples/elena-rodriguez.json` - Elena's character definition
- `characters/examples/marcus-thompson.json` - Marcus's character definition
- `characters/examples/marcus-chen.json` - Marcus Chen's character definition

## 🔧 Setup Instructions

### 1. Environment Configuration

Each bot needs its own environment file with a unique Discord token:

#### For Elena Bot (`.env.elena`):
```bash
# Copy from main .env and customize
DISCORD_BOT_TOKEN=your_elena_bot_token_here
DISCORD_BOT_NAME=Elena
CDL_DEFAULT_CHARACTER=characters/examples/elena-rodriguez.json
HEALTH_CHECK_PORT=9091
```

#### For Additional Bots (`.env.marcus`, `.env.marcus-chen`, etc.):
```bash
# Create for each new bot
DISCORD_BOT_TOKEN=your_other_bot_token_here
DISCORD_BOT_NAME=Marcus  # or "Marcus Chen"
CDL_DEFAULT_CHARACTER=characters/examples/marcus-thompson.json  # or marcus-chen.json
HEALTH_CHECK_PORT=9092  # Increment for each bot (9093 for Marcus Chen)
```

### 2. Character Definitions

Create character JSON files in `characters/examples/` directory:
- Define personality, expertise, communication style
- Use the CDL (Character Definition Language) format
- Available characters: 
  - `elena-rodriguez.json` - Marine Biologist (Elena)
  - `marcus-thompson.json` - AI Researcher (Marcus)  
  - `marcus-chen.json` - Indie Game Developer (Marcus Chen)

### 3. Discord Bot Tokens

You'll need separate Discord bot applications for each character:
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create new application for each bot character
3. Generate bot token for each application
4. Add tokens to respective `.env.{character}` files

## 🚀 Usage

### Start All Bots
```bash
./multi-bot.sh start
```

### Start Specific Bot
```bash
./multi-bot.sh start elena
./multi-bot.sh start marcus
./multi-bot.sh start marcus-chen
```

### Check Status
```bash
./multi-bot.sh status
```

### View Logs
```bash
./multi-bot.sh logs elena    # Elena bot logs
./multi-bot.sh logs marcus   # Marcus bot logs  
./multi-bot.sh logs          # All service logs
```

### Stop Bots
```bash
./multi-bot.sh stop elena    # Stop Elena only
./multi-bot.sh stop          # Stop all bots
```

### Restart Bot
```bash
./multi-bot.sh restart elena
```

## 🔍 Monitoring

Each bot has its own health check endpoint:
- Elena Bot: http://localhost:9091/health
- Marcus Bot: http://localhost:9092/health  
- Additional bots: Increment port numbers

Infrastructure services:
- PostgreSQL: localhost:5432
- Redis: localhost:6379
- Qdrant: localhost:6333

## 💾 Data Isolation

### How Memory Works with Multiple Bots

The WhisperEngine memory system is designed for multi-bot scenarios:

1. **User-Based Isolation**: All memory is keyed by Discord `user_id`
2. **Shared Infrastructure**: All bots store data in the same databases
3. **Consistent Experience**: A user's memory persists regardless of which bot they talk to

Example:
- User talks to Elena about marine biology
- Later, user talks to Marcus about AI
- Both conversations are stored under the same `user_id`
- Both bots can reference the user's full conversation history

This creates a cohesive experience where your "AI assistant team" knows you across all personalities!

## 🎯 Adding New Bots (Template-Based)

### 1. Create Environment File
```bash
# Copy template and customize
cp .env.template .env.newbot
# Edit with your bot-specific settings:
# - DISCORD_BOT_TOKEN (unique token from Discord Developer Portal)
# - DISCORD_BOT_NAME (display name)
# - HEALTH_CHECK_PORT (unique port, e.g., 9096)
```

### 2. Create Character Definition (Optional)
```bash
# Create new character file
cp characters/examples/elena-rodriguez.json characters/examples/newbot.json
# Edit personality traits, communication style, background, etc.
```

### 3. Generate Configuration (Automatic)
```bash
# Always use virtual environment
source .venv/bin/activate

# Template-based generation discovers your bot automatically
python scripts/generate_multi_bot_config.py
```

### 4. Start Your Bot
```bash
# List discovered bots (including your new one)
./multi-bot.sh list

# Start your new bot
./multi-bot.sh start newbot

# Check status
./multi-bot.sh status
./multi-bot.sh health
```

**That's it!** No manual Docker Compose editing required. The template system:
- Auto-discovers your `.env.newbot` file
- Finds matching character file using smart naming patterns
- Generates safe Docker Compose configuration
- Creates management script with your bot included
      - .env.newcharacter
    environment:
      - DISCORD_BOT_NAME=NewCharacter
      - CDL_DEFAULT_CHARACTER=characters/examples/new-character.json
      - HEALTH_CHECK_PORT=9093  # Increment port
    ports:
      - "9093:9093"  # Expose health check
    # Add volumes, etc.
```

### 4. Update Management Script
Add your new bot to the `multi-bot.sh` case statements for start/stop/logs operations.

## 🔧 Troubleshooting

### Common Issues

1. **Port Conflicts**: Each bot needs unique health check ports (9091, 9092, 9093...)
2. **Missing Environment Files**: Ensure `.env.{character}` files exist with valid Discord tokens
3. **Character File Paths**: Verify character JSON files exist in `characters/examples/`
4. **Discord Token Limits**: Each bot needs its own Discord application and token

### Debugging Commands

```bash
# Check container status
./multi-bot.sh status

# View specific bot logs
./multi-bot.sh logs elena

# Check infrastructure logs
./multi-bot.sh logs infrastructure

# Restart problematic bot
./multi-bot.sh restart elena
```

### Health Checks

Verify each bot is responding:
```bash
curl http://localhost:9091/health  # Elena
curl http://localhost:9092/health  # Marcus
```

## 🔐 Security Considerations

- Each bot has isolated volumes for backups and privacy data
- Shared infrastructure uses the same security model as single-bot deployment
- Discord tokens should be kept secure and never committed to version control
- Consider using Discord server permissions to control bot access

## 🎉 Example Deployment

Here's how to deploy Elena and Marcus bots:

```bash
# 1. Set up environment files
cp .env .env.elena
# Edit .env.elena with Elena's Discord token

cp .env .env.marcus  
# Edit .env.marcus with Marcus's Discord token

# 2. Start both bots
./multi-bot.sh start

# 3. Check they're running
./multi-bot.sh status

# 4. Test health endpoints
curl http://localhost:9091/health  # Elena
curl http://localhost:9092/health  # Marcus
```

Now you have two unique AI personalities running simultaneously! 🎭

## 📈 Scaling Considerations

- **Infrastructure Resources**: Scale up PostgreSQL, Redis, and Qdrant resources as you add more bots
- **Memory Requirements**: Each bot container needs ~4GB RAM 
- **Network Ports**: Plan port allocation for health checks (9091, 9092, 9093...)
- **Discord Rate Limits**: Each bot has independent Discord API rate limits

The current configuration supports 2-5 bots comfortably on a typical development machine. For production with many bots, consider dedicated infrastructure scaling.

---

Ready to launch your AI character team? 🚀