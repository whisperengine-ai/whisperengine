#!/bin/bash

# WhisperEngine Containerized Setup Script
# Downloads only necessary files - no source code required!

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[SETUP]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Welcome message
echo ""
echo "🎭 WhisperEngine Containerized Setup"
echo "====================================="
echo "No source code download required!"
echo "Uses pre-built Docker Hub containers"
echo ""

# Check if Docker is running
print_status "Checking Docker..."
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi
print_success "Docker is running"

# Detect if we're running inside the WhisperEngine repository
if [ -f "docker-compose.containerized.yml" ] && [ -f ".env.containerized.template" ]; then
    print_status "Running from WhisperEngine repository directory"
    INSTALL_DIR="."
    COMPOSE_FILE="docker-compose.containerized.yml"
    ENV_TEMPLATE=".env.containerized.template"
else
    # Create WhisperEngine directory for fresh installation
    INSTALL_DIR="whisperengine"
    COMPOSE_FILE="docker-compose.yml"
    ENV_TEMPLATE=".env.template"
    
    if [ -d "$INSTALL_DIR" ]; then
        print_warning "Directory '$INSTALL_DIR' already exists"
        read -p "Remove existing directory and continue? (y/N): " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$INSTALL_DIR"
            print_status "Removed existing directory"
        else
            print_error "Setup cancelled"
            exit 1
        fi
    fi
    
    mkdir -p "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"
print_success "Using directory: $(pwd)"

if [ "$INSTALL_DIR" != "." ]; then
    # Download Docker Compose file
    print_status "Downloading Docker Compose configuration..."
    COMPOSE_URL="https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/docker-compose.containerized.yml"
    if curl -sSL "$COMPOSE_URL" -o docker-compose.yml; then
        print_success "Downloaded docker-compose.yml"
    else
        print_error "Failed to download Docker Compose file"
        exit 1
    fi

    # Download environment template
    print_status "Downloading configuration template..."
    ENV_URL="https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main/.env.containerized.template"
    if curl -sSL "$ENV_URL" -o .env.template; then
        print_success "Downloaded .env.template"
    else
        print_error "Failed to download environment template"
        exit 1
    fi
else
    print_success "Using existing repository files"
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    print_status "Creating configuration file..."
    cp "$ENV_TEMPLATE" .env
    print_success "Created .env file with default settings (LM Studio)"
    print_status "💡 Using LM Studio as default LLM (free, local)"
    print_status "🔧 You can edit .env later to customize settings"
    echo ""
fi

print_success "Configuration file found"

# Check if API key is needed (only for cloud providers)
if grep -q "LLM_CLIENT_TYPE=lmstudio" .env || grep -q "LLM_CLIENT_TYPE=ollama" .env; then
    print_success "Using local LLM (no API key required)"
elif grep -q "your_api_key_here" .env; then
    print_warning "Please set your LLM_CHAT_API_KEY in the .env file for cloud providers"
    echo "   Edit .env and replace 'your_api_key_here' with your actual API key"
    echo ""
    echo "   Get API keys from:"
    echo "   • OpenRouter: https://openrouter.ai (recommended for beginners)"
    echo "   • OpenAI: https://platform.openai.com"
    echo ""
    echo "   💡 Tip: Use LM Studio instead (no API key needed):"
    echo "     Set LLM_CLIENT_TYPE=lmstudio in .env"
    echo ""
    exit 1
fi

print_success "API key configured"

# Create logs directory
mkdir -p logs
print_success "Created logs directory"

echo ""
print_status "🐳 Starting WhisperEngine..."
echo "   This may take 2-3 minutes on first run (downloading container images)"
echo "   ✨ Containers include pre-downloaded AI models (~400MB):"
echo "     • FastEmbed: sentence-transformers/all-MiniLM-L6-v2 (embeddings)"
echo "     • RoBERTa: cardiffnlp emotion analysis (11 emotions)"
echo "   🚀 No model downloads needed - instant startup!"
echo ""

# Pull latest images first
print_status "Pulling latest container images..."
docker-compose -f "$COMPOSE_FILE" pull

# Start WhisperEngine
print_status "Starting services..."
docker-compose -f "$COMPOSE_FILE" up -d

echo ""
print_status "⏳ Waiting for services to start..."

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
    print_error "Services didn't start properly. Check logs:"
    echo "   docker-compose -f $COMPOSE_FILE logs"
    exit 1
fi

echo ""
print_success "🎉 WhisperEngine is ready!"
echo "================================"
echo ""
echo "🌐 Web UI:     http://localhost:3001"
echo "🤖 Chat API:   http://localhost:9090/api/chat"
echo "📊 Health:     http://localhost:9090/health"
echo "📈 InfluxDB:   http://localhost:8086 (Metrics & Machine Learning)"
echo ""
echo "✨ Features:"
echo "• Create AI characters via web interface"
echo "• Persistent memory and conversation history"
echo "• Machine learning & temporal intelligence (InfluxDB)"
echo "• RESTful Chat APIs for integration"
echo "• Optional Discord bot functionality"
echo ""
echo "📖 Next steps:"
echo "1. Visit http://localhost:3001 to create your first character"
echo "2. Test the chat API with curl or your application"
echo "3. Edit .env file to customize LLM settings if needed"
echo "4. Enable Discord integration if desired"
echo ""
echo "🔧 Management commands:"
echo "   docker-compose -f $COMPOSE_FILE stop     # Stop WhisperEngine"
echo "   docker-compose -f $COMPOSE_FILE start    # Restart WhisperEngine"
echo "   docker-compose -f $COMPOSE_FILE logs -f  # View live logs"
echo "   docker-compose -f $COMPOSE_FILE down     # Stop and remove containers"
echo ""

# Auto-open browser on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    print_status "🔗 Opening web interface..."
    sleep 2
    open http://localhost:3001
fi

print_success "Setup complete! Enjoy your AI character platform! 🎭"