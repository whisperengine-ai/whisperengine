# WhisperEngine Dependency Management System

## Overview

WhisperEngine uses a unified dependency management system with environment-specific requirements files in the root directory.

## Structure

```
whisperengine/
├── requirements.txt                # All dependencies
├── requirements-core.txt           # Shared AI/ML dependencies
├── requirements-platform.txt       # Platform-specific optimizations
├── requirements-discord.txt        # Discord-specific dependencies
├── requirements-desktop.txt        # Desktop UI dependencies
└── scripts/
    ├── install-discord.sh          # macOS/Linux Discord installation
    ├── install-desktop.sh          # macOS/Linux desktop installation
    ├── install-discord.bat         # Windows Discord installation
    └── install-desktop.bat         # Windows desktop installation
```

## Dependency Tiers

### Core Dependencies (`requirements-core.txt`)
Shared across both Discord bot and desktop app:
- AI/ML frameworks (transformers, chromadb)
- LLM backends (openai API clients)
- Utilities (requests, asyncio)
- Memory systems

### Platform Dependencies (`requirements-platform.txt`)
Platform-specific optimizations:
- **Windows**: Windows-specific libraries
- **Linux**: Linux-optimized packages

### Discord Dependencies (`requirements-discord.txt`)
Discord bot specific:
- discord.py
- Voice processing (PyNaCl)
- Database drivers (psycopg2-binary)

### Desktop Dependencies (`requirements-desktop.txt`)
Desktop app specific:
- PySide6 (cross-platform GUI)
- Desktop integration libraries
- Platform-specific UI enhancements

## Installation Methods

### Automated Installation (Recommended)

#### Discord Bot
```bash
# macOS/Linux
chmod +x scripts/install-discord.sh
./scripts/install-discord.sh

# Windows
scripts\install-discord.bat
```

#### Desktop App
```bash
# macOS/Linux
chmod +x scripts/install-desktop.sh
./scripts/install-desktop.sh

# Windows
scripts\install-desktop.bat
```

### Manual Installation

#### Discord Bot
```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

pip install -r requirements-core.txt
pip install -r requirements-discord.txt
pip install -r requirements-platform.txt
```

#### Desktop App
```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

pip install -r requirements-core.txt
pip install -r requirements-desktop.txt
pip install -r requirements-platform.txt
```

## Platform Support

### macOS (Apple Silicon)
- **Optimization**: Automatic MLX framework integration
- **Requirements**: macOS 12+ with Apple Silicon (M1/M2/M3)
- **Performance**: 20-40% improvement for local LLM inference

### Windows (x64)
- **Requirements**: Windows 10/11 x64
- **Dependencies**: Visual C++ Redistributable may be required
- **Optimization**: CPU-optimized packages

### Linux (x86_64)
- **Requirements**: Ubuntu 20.04+, CentOS 8+, or equivalent
- **Optimization**: Linux-optimized builds
- **Dependencies**: System packages may be required

## Migration from Old Structure

If you have an existing installation with the old monolithic `requirements.txt`:

1. **Backup current environment**:
   ```bash
   pip freeze > old-requirements-backup.txt
   ```

2. **Clean installation**:
   ```bash
   rm -rf .venv
   # Run appropriate installation script
   ```

3. **Verify migration**:
   ```bash
   # For Discord bot
   cd discord-bot && python -c "import discord; print('Discord bot ready')"
   
   # For desktop app
   cd desktop-app && python -c "import PySide6; print('Desktop app ready')"
   ```

## Development

### Adding Dependencies

#### Core Dependencies
Add to `requirements-core.txt` if the dependency is:
- Used by both Discord bot and desktop app
- Core AI/ML functionality
- Essential utilities

#### Platform Dependencies
Add to `requirements-platform.txt` with platform markers:
```
mlx>=0.15.0; sys_platform == "darwin" and platform_machine == "arm64"
windows-specific-package>=1.0.0; sys_platform == "win32"
```

#### Application-Specific
Add to respective `requirements-discord.txt` or `requirements-desktop.txt`

### Testing Installation

Run verification scripts to test installations:
```bash
# Test Discord environment
python -c "
import discord
import chromadb
import transformers
print('✅ Discord bot dependencies verified')
"

# Test Desktop environment
python -c "
import PySide6
import chromadb
import transformers
print('✅ Desktop app dependencies verified')
"
```

## Troubleshooting

### Common Issues

1. **MLX not installing on Apple Silicon**:
   - Ensure macOS 12+ and Apple Silicon hardware
   - Check Xcode Command Line Tools: `xcode-select --install`

2. **PySide6 installation fails**:
   - Update pip: `pip install --upgrade pip`
   - Install Qt dependencies (Linux): `sudo apt-get install qt6-base-dev`

3. **Discord.py import errors**:
   - Verify Python 3.9+
   - Check virtual environment activation

4. **Platform detection issues**:
   - Verify platform markers in requirements files
   - Check output of: `python -c "import platform; print(platform.system(), platform.machine())"`

### Getting Help

1. Check platform-specific installation logs
2. Verify Python version compatibility (3.9+)
3. Ensure virtual environment is activated
4. Review QUICK_START.md for detailed setup
5. Check GitHub issues for platform-specific problems

## Performance Benefits

### Apple Silicon (MLX)
- **Local LLM**: 20-40% faster inference
- **Memory**: More efficient memory usage
- **Power**: Lower energy consumption

### Platform Optimizations
- **Windows**: Optimized for x64 architecture
- **Linux**: Native package builds
- **Cross-platform**: Consistent API across platforms

## User Configuration Overrides

### Smart Backend Selection
WhisperEngine automatically detects and configures the optimal LLM backend for your platform, but **all settings can be overridden** by user configuration.

#### Desktop App Fallback Priority:
1. **Local Servers**: Search for existing Ollama or LM Studio server on localhost
2. **Python APIs**: Use MLX for Apple Silicon for direct Python integration

#### User Override Variables:
```bash
# Primary configuration (highest priority)
export LLM_CHAT_API_URL="https://api.openai.com/v1"          # API endpoint URL
export LLM_CHAT_API_KEY="your-api-key"                      # Authentication key  
export LLM_CHAT_MODEL="gpt-4"                               # Specific model name

# Alternative URL setting
export LLM_BASE_URL="https://api.openrouter.ai/api/v1"      # Alternative base URL

# Backend-specific overrides
export MLX_MODEL_NAME="llama-3.1-8b-instruct"              # MLX model
```

#### Configuration Validation:
```bash
# Check current configuration
python -c "from src.config.llm_config_validator import print_llm_config_report; print_llm_config_report()"

# Test smart backend detection  
python -m src.llm.smart_backend_selector
```

### Override Examples:

#### Use OpenRouter:
```bash
export LLM_CHAT_API_URL="https://openrouter.ai/api/v1"
export LLM_CHAT_API_KEY="sk-or-..."  
export LLM_CHAT_MODEL="anthropic/claude-3.5-sonnet"
```

#### Force Local LM Studio:
```bash
export LLM_CHAT_API_URL="http://localhost:1234/v1"
export LLM_CHAT_MODEL="llama-3.1-8b-instruct-q4"
```

#### Use Custom API:
```bash
export LLM_CHAT_API_URL="https://your-custom-endpoint.com/v1"
export LLM_CHAT_API_KEY="your-custom-key"
export LLM_CHAT_MODEL="your-model-name"
```

**Note**: User overrides always take precedence over auto-detection. The smart backend selector serves as intelligent defaults when no user configuration is provided.