# WhisperEngine Deployment Structure

This repository uses a unified root structure with environment-specific configurations.

## 🏗️ Directory Structure

```
whisperengine/                   # Main repository
├── .env                         # Default configuration
├── .env.discord                 # Discord bot configuration  
├── .env.desktop-app             # Desktop app configuration
├── run.py                       # Discord bot entry point
├── universal_native_app.py      # Desktop app entry point
├── src/                         # Shared core code
├── requirements.txt             # Shared dependencies
└── README.md                    # Main documentation
```

## 🚀 Running Different Deployments

### Discord Bot (Cloud APIs)
```bash
# Method 1: Using default configuration
python run.py

# Method 2: Using Discord-specific environment
DOTENV_PATH=.env.discord python run.py

# Method 3: Direct with environment
DOTENV_PATH=.env.discord python run.py
```

### Desktop App (Local Models)
```bash
# Method 1: Using default configuration
python universal_native_app.py

# Method 2: Using desktop-specific environment  
DOTENV_PATH=.env.desktop-app python universal_native_app.py
```

## ⚙️ Configuration Differences

### Discord Bot (`.env.discord`)
- 🌐 **OpenRouter APIs** for scalable cloud deployment
- 🐳 **Docker services** (Redis, PostgreSQL, ChromaDB)
- 🔊 **Voice capabilities** enabled
- 🚀 **High performance** settings

### Desktop App (`.env.desktop-app`)
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
python run.py

# Test desktop app
python universal_native_app.py
```

### Environment-Specific Configuration
```bash
# Discord bot with specific environment
DOTENV_PATH=.env.discord python run.py

# Desktop app with specific environment
DOTENV_PATH=.env.desktop-app python universal_native_app.py
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
# Copy specific configs to root directory
cp ../whisperengine-discord/.env .env.discord
cp ../whisperengine-desktop/.env .env.desktop-app

# Core code is already shared in src/
```

## 📋 Quick Commands

```bash
# Discord bot development
python run.py

# Desktop app development  
python universal_native_app.py

# Run tests with specific config
DOTENV_PATH=.env.discord python test_discord_integration.py
DOTENV_PATH=.env.desktop-app python test_desktop_integration.py
```