#!/bin/bash
# Desktop App Installation Script
# Supports: macOS (Apple Silicon), Windows (WSL), Linux

set -e

echo "🖥️ Installing WhisperEngine Desktop App..."

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

# Platform-specific system dependencies
if [[ "$PLATFORM" == "Linux" ]]; then
    echo "🐧 Installing Linux system dependencies..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y python3-dev qt6-base-dev libxcb1-dev libxcb-xinerama0-dev
    elif command -v yum &> /dev/null; then
        sudo yum install -y python3-devel qt6-qtbase-devel libxcb-devel
    elif command -v pacman &> /dev/null; then
        sudo pacman -S --noconfirm python qt6-base libxcb
    fi
fi

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

# Install desktop-specific dependencies
echo "🖥️ Installing desktop app dependencies..."
pip install -r requirements-desktop.txt

# Install platform-specific optimizations
echo "🍎 Installing platform optimizations..."
pip install -r requirements-platform.txt

# Verify installation
echo "✅ Verifying installation..."
python3 -c "
try:
    from PySide6.QtWidgets import QApplication
    print('✅ PySide6 (Qt6) available')
except ImportError:
    print('❌ PySide6 installation failed')
    exit(1)
"

echo ""
echo "🎉 Desktop App installation complete!"
echo ""
echo "📝 Next steps:"
echo "1. Copy .env.example to .env.desktop-app"
echo "2. Configure your LLM settings"
echo "3. Run: python universal_native_app.py"
echo ""
echo "📚 See QUICK_START.md for detailed setup instructions"