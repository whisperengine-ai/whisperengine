# WhisperEngine Deployment Structure

This repository now supports clean separation between Discord bot and desktop app deployments using subdirectories.

## 🏗️ Directory Structure

```
whisperengine/                   # Main repository
├── discord-bot/                 # Discord bot deployment
│   ├── .env                     # Discord bot configuration
│   ├── docker-compose.yml       # Docker services for Discord bot
│   └── run-discord.py           # Discord bot launcher
├── desktop-app/                 # Desktop app deployment
│   ├── .env                     # Desktop app configuration
│   └── run-desktop.py           # Desktop app launcher
├── src/                         # Shared core code
├── requirements.txt             # Shared dependencies
└── README.md                    # Main documentation
```

## 🚀 Running Different Deployments

### Discord Bot (Cloud APIs)
```bash
# Method 1: Using launcher
python discord-bot/run-discord.py

# Method 2: Using Docker
cd discord-bot
docker-compose up

# Method 3: Direct with environment
DOTENV_PATH=discord-bot/.env python run.py
```

### Desktop App (Local Models)
```bash
# Method 1: Using launcher
python desktop-app/run-desktop.py

# Method 2: Direct with environment  
DOTENV_PATH=desktop-app/.env python universal_native_app.py
```

## ⚙️ Configuration Differences

### Discord Bot (`discord-bot/.env`)
- 🌐 **OpenRouter APIs** for scalable cloud deployment
- 🐳 **Docker services** (Redis, PostgreSQL, ChromaDB)
- 🔊 **Voice capabilities** enabled
- 🚀 **High performance** settings

### Desktop App (`desktop-app/.env`)
- 🖥️ **llama-cpp-python** for local privacy
- 💾 **SQLite database** for local storage
- 🔇 **Voice disabled** by default
- ⚡ **Conservative** performance settings

## 🔄 Development Workflow

### Working on Core Features
```bash
# Work in main directory - changes affect both deployments
git add src/
git commit -m "Add new AI feature"
```

### Testing Different Deployments
```bash
# Test Discord bot
python discord-bot/run-discord.py

# Test desktop app
python desktop-app/run-desktop.py
```

### Adding Deployment-Specific Features
```bash
# Discord bot specific
vim discord-bot/run-discord.py

# Desktop app specific  
vim desktop-app/run-desktop.py
```

## 🔧 Environment Priority

The environment loading follows this priority:

1. **`DOTENV_PATH`** (highest) - Explicit path set by launcher
2. **Docker environment** - Compose services
3. **Mode-specific** (e.g., `.env.development`)
4. **Generic `.env`** (lowest) - Local overrides

## 📦 Benefits of This Approach

✅ **Single repository** - Easy to manage and sync changes  
✅ **Shared core code** - No duplication in `src/`  
✅ **Clean separation** - Different configs don't conflict  
✅ **Easy testing** - Switch between deployments instantly  
✅ **Simple CI/CD** - Build both variants from one repo  

## 🔄 Migration from Separate Repos

If you have separate repositories, you can migrate like this:

```bash
# Copy specific configs to subdirectories
cp ../whisperengine-discord/.env discord-bot/
cp ../whisperengine-desktop/.env desktop-app/

# Core code is already shared in src/
```

## 📋 Quick Commands

```bash
# Discord bot development
python discord-bot/run-discord.py

# Desktop app development  
python desktop-app/run-desktop.py

# Run tests with specific config
DOTENV_PATH=discord-bot/.env python test_discord_integration.py
DOTENV_PATH=desktop-app/.env python test_desktop_integration.py
```