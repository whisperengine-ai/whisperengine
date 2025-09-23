# Dynamic Multi-Bot Configuration System

## Overview

WhisperEngine now uses a **dynamic multi-bot configuration system** that automatically discovers bot configurations and generates Docker Compose and management scripts. This eliminates hardcoded bot names and makes it trivial to add new bots.

## How It Works

### Auto-Discovery
The system scans for:
- **Environment files**: `.env.*` files (excluding `.example` and `.template`)
- **Character files**: `characters/examples/*.json` files
- **Automatic mapping**: Links bot names to character files using intelligent pattern matching

### Dynamic Generation
The `scripts/generate_multi_bot_config.py` script automatically:
1. **Discovers** all bot configurations from `.env.*` files
2. **Maps** bot names to character JSON files
3. **Generates** Docker Compose services with unique ports
4. **Creates** management script with all discovered bots

## Adding a New Bot

To add a new bot, simply:

1. **Create environment file**: `.env.{bot_name}`
   ```bash
   cp .env.elena .env.mybot
   # Edit .env.mybot with unique Discord token and bot name
   ```

2. **Create character file**: `characters/examples/mybot.json` (optional)
   ```json
   {
     "name": "MyBot",
     "occupation": "Assistant",
     "personality": {...}
   }
   ```

3. **Regenerate configuration**:
   ```bash
   source .venv/bin/activate
   python scripts/generate_multi_bot_config.py
   ```

4. **Start your new bot**:
   ```bash
   ./multi-bot.sh start mybot
   ```

## Character File Mapping

The system automatically maps bot names to character files using:

1. **Exact match**: `.env.mybot` → `mybot.json`
2. **Pattern matching**: `.env.elena` → `elena-rodriguez.json`
3. **Manual mapping**: Built-in mapping for existing bots
4. **Fallback**: Uses first available character file if no match found

## Key Benefits

### ✅ No More Hardcoding
- **Before**: Bot names hardcoded in docker-compose.yml and multi-bot.sh
- **After**: All bot configurations discovered automatically

### ✅ Easy Bot Addition
- **Before**: Edit multiple files, add case statements, update port lists
- **After**: Create `.env.{bot_name}` file and regenerate

### ✅ Automatic Port Management
- **Before**: Manually assign unique health check ports
- **After**: Automatically generated unique ports (9090-9139)

### ✅ Consistent Configuration
- **Before**: Risk of configuration drift between bots
- **After**: All bots use same template with bot-specific overrides

## Generated Files

### `docker-compose.multi-bot.yml`
- Auto-generated Docker Compose configuration
- One service per discovered bot
- Shared infrastructure (PostgreSQL, Redis, Qdrant)
- Unique ports and volume names per bot

### `multi-bot.sh`
- Auto-generated management script
- Dynamic command handling for all discovered bots
- Automatic validation of bot names
- Help text with current bot list

## Configuration Generator

### Usage
```bash
# Generate configuration (overwrites existing files)
source .venv/bin/activate
python scripts/generate_multi_bot_config.py

# Preview what would be generated (dry run)
python scripts/generate_multi_bot_config.py --dry-run

# Generate to different directory
python scripts/generate_multi_bot_config.py --output-dir /path/to/output
```

### Features
- **Environment scanning**: Finds all `.env.*` files automatically
- **Character mapping**: Links bots to character definitions intelligently
- **Port generation**: Creates unique health check ports (hash-based)
- **Volume management**: Creates isolated volumes per bot
- **Infrastructure sharing**: All bots share PostgreSQL, Redis, Qdrant

## Multi-Bot Management

### Available Commands
```bash
./multi-bot.sh help                    # Show all commands
./multi-bot.sh list                    # List discovered bot configurations
./multi-bot.sh start [bot_name]        # Start specific bot or all bots
./multi-bot.sh stop [bot_name]         # Stop specific bot or all bots
./multi-bot.sh restart [bot_name]      # Restart specific bot or all bots
./multi-bot.sh logs [bot_name]         # Show logs for specific bot
./multi-bot.sh status                  # Show all container status
./multi-bot.sh rebuild [bot_name]      # Rebuild and restart specific bot
./multi-bot.sh cleanup                 # Stop and remove all containers/volumes
```

### Examples
```bash
./multi-bot.sh start elena            # Start only Elena bot
./multi-bot.sh logs marcus            # Show Marcus bot logs
./multi-bot.sh restart                # Restart all bots
```

## Migration from Hardcoded System

### Backup
Original files are backed up as:
- `docker-compose.multi-bot.yml.backup`
- `multi-bot.sh.backup`

### Verification
Verify the new system works:
```bash
./multi-bot.sh list                   # Should show all existing bots
./multi-bot.sh start elena            # Test starting individual bot
./multi-bot.sh status                 # Check container status
```

## File Structure

```
├── scripts/
│   └── generate_multi_bot_config.py  # Configuration generator
├── .env.elena                        # Elena bot environment
├── .env.marcus                       # Marcus bot environment
├── .env.marcus-chen                  # Marcus Chen bot environment
├── .env.gabriel                      # Gabriel bot environment
├── .env.dream                        # Dream bot environment
├── characters/examples/
│   ├── elena-rodriguez.json          # Elena character definition
│   ├── marcus-thompson.json          # Marcus character definition
│   ├── marcus-chen.json              # Marcus Chen character definition
│   ├── gabriel-tether.json           # Gabriel character definition
│   └── dream_of_the_endless.json     # Dream character definition
├── docker-compose.multi-bot.yml      # Generated Docker config
└── multi-bot.sh                      # Generated management script
```

## Best Practices

### Environment Files
- Use descriptive bot names: `.env.assistant`, `.env.researcher`
- Keep unique Discord tokens per bot
- Set unique `HEALTH_CHECK_PORT` values (auto-generated)
- Include bot-specific `DISCORD_BOT_NAME` and `CDL_DEFAULT_CHARACTER`

### Character Files
- Create unique character JSON files for distinct personalities
- Use descriptive filenames: `research-assistant.json`, `game-master.json`
- Test character definitions before deploying

### Development Workflow
1. Create new bot configuration files
2. Regenerate dynamic configuration
3. Test bot individually before adding to production
4. Use `./multi-bot.sh list` to verify configuration

## Troubleshooting

### Bot Not Discovered
- Check `.env.{bot_name}` file exists and doesn't end with `.example` or `.template`
- Regenerate configuration: `python scripts/generate_multi_bot_config.py`
- Verify with: `./multi-bot.sh list`

### Character File Not Found
- System will use default character file with warning
- Create specific character file: `characters/examples/{bot_name}.json`
- Or use manual mapping in generator script

### Port Conflicts
- Ports are auto-generated using hash of bot name
- If conflicts occur, modify hash algorithm in generator script
- Check port usage: `./multi-bot.sh status`

### Environment Issues
- Always use virtual environment: `source .venv/bin/activate`
- Install dependencies: `pip install PyYAML`
- Check Python version: `python --version`