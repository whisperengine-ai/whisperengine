#!/bin/bash
# WhisperEngine Quick Setup Script
# This script sets up WhisperEngine with bundled AI models

set -e  # Exit on any error

echo "🚀 WhisperEngine Quick Setup"
echo "=============================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required. Please install Python 3.9 or later."
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "universal_native_app.py" ]; then
    echo "❌ Please run this script from the WhisperEngine directory"
    echo "   Current directory: $(pwd)"
    exit 1
fi

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

echo "📥 Installing dependencies..."
pip install -r requirements.txt

echo "🤖 Downloading AI models (this may take 5-10 minutes)..."
echo "   - Phi-3-Mini conversational AI (~2GB)"
echo "   - Embedding models for memory (~500MB)"  
echo "   - Emotion analysis models (~600MB)"
echo "   Total size: ~3.1GB (full functionality)"
echo ""

python download_models.py

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "🚀 To start WhisperEngine:"
echo "   source .venv/bin/activate"
echo "   python universal_native_app.py"
echo ""
echo "📖 Then open your browser to: http://localhost:8501"
echo ""
echo "💡 For more options, see BUILD_AND_USER_GUIDE.md"