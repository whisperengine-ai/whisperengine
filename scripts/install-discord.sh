#!/bin/bash
# Discord Bot Installation Script
# Supports: macOS (Apple Silicon), Windows (WSL), Linux

set -e

echo "🤖 Installing WhisperEngine Discord Bot..."

# Detect platform
if [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="macOS"
    if [[ $(uname -m) == "arm64" ]]; then
        ARCH="Apple Silicon"
    else
        ARCH="Intel"
    fi
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    PLATFORM="Linux"
    ARCH="x86_64"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    PLATFORM="Windows"
    ARCH="x86_64"
else
    PLATFORM="Unknown"
    ARCH="Unknown"
fi

echo "📍 Platform: $PLATFORM $ARCH"

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1-2)
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python $required_version or higher required. Found: $python_version"
    exit 1
fi

echo "✅ Python $python_version detected"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "🔧 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install core dependencies
echo "📦 Installing core dependencies..."
pip install -r requirements-core.txt

# Install Discord-specific dependencies
echo "🤖 Installing Discord bot dependencies..."
pip install -r requirements-discord.txt

# Install platform-specific optimizations
echo "🍎 Installing platform optimizations..."
pip install -r requirements-platform.txt

# Verify installation
echo "✅ Verifying installation..."
python3 -c "import discord; print(f'Discord.py version: {discord.__version__}')"

echo ""
echo "🎉 Discord Bot installation complete!"
echo ""
echo "📝 Next steps:"
echo "1. Copy .env.example to .env.discord"
echo "2. Configure your Discord bot token and LLM settings"
echo "3. Run: python run.py"
echo ""
echo "📚 See QUICK_START.md for detailed setup instructions"