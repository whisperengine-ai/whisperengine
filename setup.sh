#!/bin/bash

# WhisperEngine Quick Setup Script
# Makes setup even easier for non-technical users

set -e

echo "🚀 WhisperEngine Quick Setup"
echo "=============================="
echo

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi

echo "✅ Docker is running"

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating configuration file..."
    cp .env.quickstart.template .env
    echo "✅ Created .env file from template"
    echo
    echo "⚠️  IMPORTANT: You need to edit the .env file with your settings!"
    echo "   Required: Set your LLM_CHAT_API_KEY"
    echo "   Optional: Set DISCORD_BOT_TOKEN for Discord integration"
    echo
    
    # Detect OS and open .env file
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        echo "🔧 Opening .env file for editing..."
        open -e .env
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        echo "🔧 Edit the .env file with your preferred text editor:"
        echo "   nano .env"
        echo "   OR"
        echo "   gedit .env"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        # Windows
        echo "🔧 Opening .env file for editing..."
        notepad .env
    fi
    
    echo
    echo "📖 After editing .env, run this script again to start WhisperEngine"
    exit 0
fi

echo "✅ Configuration file found"

# Check if API key is set
if grep -q "your_api_key_here" .env; then
    echo "⚠️  Please set your LLM_CHAT_API_KEY in the .env file"
    echo "   Edit .env and replace 'your_api_key_here' with your actual API key"
    exit 1
fi

echo "✅ API key configured"

# Create logs directory
mkdir -p logs

echo
echo "🐳 Starting WhisperEngine..."
echo "   This may take 2-3 minutes on first run (downloading images)"
echo

# Start WhisperEngine
docker-compose -f docker-compose.quickstart.yml up -d

echo
echo "⏳ Waiting for services to start..."

# Wait for services to be healthy
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:3001 > /dev/null 2>&1 && curl -s http://localhost:9090/health > /dev/null 2>&1; then
        break
    fi
    echo "   Waiting... ($((attempt + 1))/$max_attempts)"
    sleep 10
    attempt=$((attempt + 1))
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ Services didn't start properly. Check logs:"
    echo "   docker-compose -f docker-compose.quickstart.yml logs"
    exit 1
fi

echo
echo "🎉 WhisperEngine is ready!"
echo "=========================="
echo
echo "🌐 Web UI:     http://localhost:3001"
echo "🤖 Chat API:   http://localhost:9090/api/chat"
echo "📊 Health:     http://localhost:9090/health"
echo
echo "Next steps:"
echo "1. Visit http://localhost:3001 to manage characters"
echo "2. Customize your AI assistant character"
echo "3. Test the chat API or enable Discord integration"
echo
echo "To stop: docker-compose -f docker-compose.quickstart.yml down"
echo "To view logs: docker-compose -f docker-compose.quickstart.yml logs -f"
echo

# Auto-open browser on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "🔗 Opening web interface..."
    sleep 2
    open http://localhost:3001
fi