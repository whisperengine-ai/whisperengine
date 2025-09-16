#!/bin/bash
# WhisperEngine Quick Setup Script
# This script sets up WhisperEngine with the new multi-tier dependency system

set -e  # Exit on any error

echo "🚀 WhisperEngine Quick Setup"
echo "=============================="

# Detect platform for optimization notes
PLATFORM=$(uname -s)
ARCH=$(uname -m)

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required. Please install Python 3.13 or later."
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "universal_native_app.py" ]; then
    echo "❌ Please run this script from the WhisperEngine directory"
    echo "   Current directory: $(pwd)"
    exit 1
fi

# Ask user what they want to install
echo "📦 What would you like to install?"
echo "1) Desktop App only (recommended for local use)"
echo "2) Discord Bot only (for server deployment)"
echo "3) Both Desktop App and Discord Bot"
echo ""
read -p "Choose option (1-3): " choice

case $choice in
    1)
        INSTALL_TYPE="desktop"
        echo "🖥️ Installing Desktop App..."
        ;;
    2)
        INSTALL_TYPE="discord"
        echo "🤖 Installing Discord Bot..."
        ;;
    3)
        INSTALL_TYPE="both"
        echo "🔄 Installing Both Desktop App and Discord Bot..."
        ;;
    *)
        echo "❌ Invalid choice. Defaulting to Desktop App."
        INSTALL_TYPE="desktop"
        ;;
esac

echo "📦 Setting up virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

echo "📥 Installing dependencies..."

# Install core dependencies (always needed)
echo "   📦 Installing core AI/ML dependencies..."
pip install -r requirements-core.txt

# Install platform-specific optimizations
echo "   🚀 Installing platform optimizations..."
pip install -r requirements-platform.txt

# Install application-specific dependencies
if [ "$INSTALL_TYPE" = "desktop" ] || [ "$INSTALL_TYPE" = "both" ]; then
    echo "   🖥️ Installing desktop app dependencies..."
    pip install -r requirements-desktop.txt
fi

if [ "$INSTALL_TYPE" = "discord" ] || [ "$INSTALL_TYPE" = "both" ]; then
    echo "   🤖 Installing Discord bot dependencies..."
    pip install -r requirements-discord.txt
fi

echo ""
echo "🎉 Setup completed successfully!"
echo ""

# Provide startup instructions based on what was installed
if [ "$INSTALL_TYPE" = "desktop" ]; then
    echo "�️ To start the Desktop App:"
    echo "   source .venv/bin/activate"
    echo "   python universal_native_app.py"
    echo ""
elif [ "$INSTALL_TYPE" = "discord" ]; then
    echo "🤖 To start the Discord Bot:"
    echo "   1. Copy .env.example to .env"
    echo "   2. Configure your Discord bot token and LLM settings"
    echo "   3. source .venv/bin/activate"
    echo "   4. python run.py"
    echo ""
elif [ "$INSTALL_TYPE" = "both" ]; then
    echo "🔄 Installation complete for both apps:"
    echo ""
    echo "🖥️ To start the Desktop App:"
    echo "   source .venv/bin/activate"
    echo "   python universal_native_app.py"
    echo ""
    echo "🤖 To start the Discord Bot:"
    echo "   1. Copy .env.example to .env"
    echo "   2. Configure your Discord bot token and LLM settings"
    echo "   3. source .venv/bin/activate"
    echo "   4. python run.py"
    echo ""
fi

