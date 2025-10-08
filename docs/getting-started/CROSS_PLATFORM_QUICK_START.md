# 🌍 Cross-Platform Quick Start Guide

This guide covers WhisperEngine quick-start options for any platform.

⚠️ **Recommended Approach**: [Multi-Bot Docker Setup](QUICK_START.md) provides full functionality with multiple character options.

**Quick-start scripts** below provide basic single-bot setup for rapid testing.

## 📋 **Prerequisites**

All platforms require:
- **Docker Desktop** (running)
- **Internet connection** (for downloading images)
- **Discord bot token** ([Get one here](https://discord.com/developers/applications))
- **LLM API key** (OpenRouter, Anthropic, or OpenAI)

### Platform-Specific Requirements

| Platform | Requirements |
|----------|-------------|
| **🐧 Linux** | `curl`, `bash`, `docker`, `docker-compose` |
| **🍎 macOS** | `curl`, `bash`, `docker`, `docker-compose` |
| **🪟 Windows (PowerShell)** | PowerShell 5.1+, Docker Desktop |
| **🪟 Windows (Command Prompt)** | Command Prompt, Docker Desktop |

## 🚀 **Quick Start Commands** (Single-Bot)

### 🐧 **Linux**
```bash
# Download and run the quick-start script
curl -sSL https://raw.githubusercontent.com/WhisperEngine-AI/whisperengine/main/scripts/quick-start.sh | bash

# Or download first, then run
curl -L -o quick-start.sh https://raw.githubusercontent.com/WhisperEngine-AI/whisperengine/main/scripts/quick-start.sh
chmod +x quick-start.sh
./quick-start.sh
```

### 🍎 **macOS**
```bash
# Download and run the quick-start script
curl -sSL https://raw.githubusercontent.com/WhisperEngine-AI/whisperengine/main/scripts/quick-start.sh | bash

# Or download first, then run
curl -L -o quick-start.sh https://raw.githubusercontent.com/WhisperEngine-AI/whisperengine/main/scripts/quick-start.sh
chmod +x quick-start.sh
./quick-start.sh
```

### 🪟 **Windows PowerShell**
```powershell
# Download and run the quick-start script
iwr https://raw.githubusercontent.com/WhisperEngine-AI/whisperengine/main/scripts/quick-start.ps1 | iex

# Or download first, then run
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/WhisperEngine-AI/whisperengine/main/scripts/quick-start.ps1" -OutFile "quick-start.ps1"
.\quick-start.ps1
```

### 🪟 **Windows Command Prompt**
```batch
@REM Download the batch script
curl -L -o quick-start.bat https://raw.githubusercontent.com/WhisperEngine-AI/whisperengine/main/scripts/quick-start.bat

@REM Run the script
quick-start.bat
```

## 🎯 **What the Scripts Do**

All quick-start scripts perform these steps:

1. **🔍 Environment Check**
   - Verify Docker is installed and running
   - Check Docker Compose availability
   - Validate system requirements

2. **📁 Project Setup**
   - Create a new WhisperEngine project directory
   - Download configuration files from GitHub
   - Set up the correct directory structure

3. **⚙️ Configuration**
   - Create `.env` file from template
   - Open your default editor to configure Discord token
   - Validate configuration settings

4. **🐳 Service Deployment**
   - Pull latest Docker images
   - Start all WhisperEngine services
   - Verify services are running correctly

5. **ℹ️ Usage Instructions**
   - Display monitoring commands
   - Show configuration file locations
   - Provide troubleshooting guidance

## 🔧 **Version Options**

All scripts support version selection:

```bash
# Latest stable (default)
./quick-start.sh

# Specific version
./quick-start.sh v1.0.0

# Development version
./quick-start.sh dev
```

## 📝 **Configuration Steps**

After running any quick-start script:

1. **📝 Edit `.env` file** (opened automatically)
   - Set `DISCORD_BOT_TOKEN=your_bot_token_here`
   - Configure optional LLM settings

2. **🎭 Customize personality** (optional)
   - Edit `system_prompt.md` to change bot personality
   - Changes apply instantly without restart

3. **🚀 Start using**
   - Bot is automatically started by the script
   - Monitor with `docker-compose logs -f whisperengine`

## 📊 **Platform-Specific Features**

### 🐧 **Linux Features**
- Native bash scripting with error handling
- System package manager integration hints
- Terminal color output for better UX

### 🍎 **macOS Features**
- macOS-native bash scripting
- Homebrew integration suggestions
- Terminal color output for better UX

### 🪟 **Windows PowerShell Features**
- PowerShell-native cmdlets and error handling
- VS Code integration (opens files automatically)
- Windows-specific Docker Desktop checks
- Proper Windows path handling

### 🪟 **Windows Command Prompt Features**
- Traditional batch file compatibility
- Notepad integration for file editing
- Windows-native error messages
- Legacy Command Prompt support

## 🔧 **Useful Commands**

After installation, these commands work on all platforms:

```bash
# Monitor bot logs
docker-compose logs -f whisperengine

# View all service logs
docker-compose logs

# Stop all services
docker-compose down

# Restart services
docker-compose restart

# Update to latest images
docker-compose pull && docker-compose up -d

# Check service status
docker-compose ps
```

## 🚨 **Troubleshooting**

### Common Issues

| Issue | Solution |
|-------|----------|
| **Docker not found** | Install Docker Desktop and ensure it's running |
| **Permission denied** | Run with appropriate permissions (Linux/macOS: `sudo`, Windows: Run as Administrator) |
| **Download failed** | Check internet connection and firewall settings |
| **Services won't start** | Ensure ports 6333, 6379 are available |
| **Bot not responding** | Verify Discord token in `.env` file |

### Platform-Specific Troubleshooting

#### 🐧 **Linux**
```bash
# Check Docker daemon
sudo systemctl status docker

# Install Docker if missing
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
```

#### 🍎 **macOS**
```bash
# Install Docker Desktop
brew install --cask docker

# Install curl if missing
brew install curl
```

#### 🪟 **Windows**
```powershell
# Check Docker Desktop status
docker --version

# Install Docker Desktop
# Download from: https://desktop.docker.com/win/main/amd64/Docker Desktop Installer.exe
```

## 🌟 **Next Steps**

After successful installation:

1. **🎭 Customize Your Bot**
   - Read the [Character Creation Guide](../character/character_prompt_guide.md)
   - Explore personality templates in `prompts/`

2. **⚙️ Advanced Configuration**
   - Set up local LLM providers (LM Studio, Ollama)
   - Configure memory and intelligence settings

3. **📚 Learn More**
   - Review the [Development Guide](../development/DEVELOPMENT_GUIDE.md)
   - Explore the [Memory System](../ai-systems/MEMORY_SYSTEM_README.md)

## 🤝 **Getting Help**

- **📖 Documentation**: [WhisperEngine Wiki](https://github.com/WhisperEngine-AI/whisperengine/wiki)
- **🐛 Issues**: [GitHub Issues](https://github.com/WhisperEngine-AI/whisperengine/issues)
- **💬 Discussions**: [GitHub Discussions](https://github.com/WhisperEngine-AI/whisperengine/discussions)

---

🎭 **Dream of the Endless awaits in your Discord server...**