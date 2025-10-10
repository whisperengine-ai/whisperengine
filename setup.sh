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
    echo "✅ Created .env file with default settings (LM Studio)"
    echo "   💡 Using LM Studio as default LLM (free, local)"
    echo "   🔧 You can edit .env later to customize settings"
    echo
fi
fi

echo "✅ Configuration file found"

# Check LLM configuration based on provider type
LLM_CLIENT_TYPE=$(grep "^LLM_CLIENT_TYPE=" .env | cut -d'=' -f2)

if [[ "$LLM_CLIENT_TYPE" == "lmstudio" ]] || [[ "$LLM_CLIENT_TYPE" == "ollama" ]]; then
    echo "✅ Local LLM configured ($LLM_CLIENT_TYPE)"
    echo "   Make sure your local LLM server is running before using WhisperEngine"
elif [[ "$LLM_CLIENT_TYPE" == "openrouter" ]] || [[ "$LLM_CLIENT_TYPE" == "openai" ]]; then
    # Check if API key is set for cloud providers
    if grep -q "your_api_key_here" .env || grep -q "^LLM_CHAT_API_KEY=$" .env || grep -q "^LLM_CHAT_API_KEY=\s*$" .env; then
        echo "⚠️  Please set your LLM_CHAT_API_KEY in the .env file"
        echo "   Edit .env and add your $LLM_CLIENT_TYPE API key"
        exit 1
    fi
    echo "✅ API key configured for $LLM_CLIENT_TYPE"
else
    echo "✅ LLM configuration found"
fi

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
echo "📈 InfluxDB:   http://localhost:8086 (Metrics & Machine Learning)"
echo
echo "Next steps:"
echo "1. Visit http://localhost:3001 to manage characters"
echo "2. Customize your AI assistant character"
echo "3. Edit .env file to customize LLM settings if needed"
echo "4. Test the chat API or enable Discord integration"
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