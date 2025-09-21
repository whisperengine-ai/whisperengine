# WhisperEngine Multi-Bot Setup Guide

## 🚀 Overview

WhisperEngine supports running multiple character bot containers that share the same infrastructure! This allows you to have different Discord bots with unique personalities (Elena the marine biologist, Marcus the AI researcher, etc.) all powered by the same backend services.

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Elena Bot     │    │   Marcus Bot    │    │   Future Bot    │
│  (Container)    │    │  (Container)    │    │  (Container)    │
│                 │    │                 │    │                 │
│ Token: Elena    │    │ Token: Marcus   │    │ Token: Other    │
│ Character: *.json│    │ Character: *.json│    │ Character: *.json│
│ Port: 9091      │    │ Port: 9092      │    │ Port: 9093      │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
    ┌─────────────────────────────┼─────────────────────────────┐
    │                             │                             │
    │           SHARED INFRASTRUCTURE                           │
    │                             │                             │
    │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
    │  │ PostgreSQL   │  │    Redis     │  │   Qdrant     │    │
    │  │ (Database)   │  │  (Cache)     │  │ (Vectors)    │    │
    │  │ Port: 5432   │  │ Port: 6379   │  │ Port: 6333   │    │
    │  └──────────────┘  └──────────────┘  └──────────────┘    │
    └─────────────────────────────────────────────────────────┘
```

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
- `.env.marcus` - Marcus bot-specific environment variables (example)
- `characters/examples/elena-rodriguez.json` - Elena's character definition
- `characters/examples/marcus-thompson.json` - Marcus's character definition

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

#### For Additional Bots (`.env.marcus`, etc.):
```bash
# Create for each new bot
DISCORD_BOT_TOKEN=your_other_bot_token_here
DISCORD_BOT_NAME=Marcus  
CDL_DEFAULT_CHARACTER=characters/examples/marcus-thompson.json
HEALTH_CHECK_PORT=9092  # Increment for each bot
```

### 2. Character Definitions

Create character JSON files in `characters/examples/` directory:
- Define personality, expertise, communication style
- Use the CDL (Character Definition Language) format
- Examples: `elena-rodriguez.json`, `marcus-thompson.json`

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

## 🎯 Adding New Bots

### 1. Create Character Definition
```bash
# Create new character file
cp characters/examples/elena-rodriguez.json characters/examples/new-character.json
# Edit to define new personality
```

### 2. Create Environment File
```bash
# Copy and customize environment
cp .env.elena .env.newcharacter
# Update Discord token, bot name, character file, and health port
```

### 3. Add to Docker Compose
Edit `docker-compose.multi-bot.yml`:
```yaml
  newcharacter-bot:
    # Copy elena-bot section and modify:
    env_file:
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