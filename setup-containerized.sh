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

# Create WhisperEngine directory
INSTALL_DIR="whisperengine"
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
cd "$INSTALL_DIR"
print_success "Created directory: $INSTALL_DIR"

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

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    print_status "Creating configuration file..."
    cp .env.template .env
    print_success "Created .env file from template"
    echo ""
    print_warning "IMPORTANT: You need to edit the .env file with your settings!"
    echo "   Required: Set your LLM_CHAT_API_KEY"
    echo "   Optional: Set DISCORD_BOT_TOKEN for Discord integration"
    echo ""
    
    # Detect OS and open .env file
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        print_status "Opening .env file for editing..."
        open -e .env
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        print_status "Edit the .env file with your preferred text editor:"
        echo "   nano .env"
        echo "   OR"
        echo "   gedit .env"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        # Windows
        print_status "Opening .env file for editing..."
        notepad .env
    fi
    
    echo ""
    echo "📖 After editing .env, run this script again to start WhisperEngine"
    exit 0
fi

print_success "Configuration file found"

# Check if API key is set
if grep -q "your_api_key_here" .env; then
    print_warning "Please set your LLM_CHAT_API_KEY in the .env file"
    echo "   Edit .env and replace 'your_api_key_here' with your actual API key"
    echo ""
    echo "   Get API keys from:"
    echo "   • OpenRouter: https://openrouter.ai (recommended for beginners)"
    echo "   • OpenAI: https://platform.openai.com"
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
docker-compose pull

# Start WhisperEngine
print_status "Starting services..."
docker-compose up -d

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
    echo "   docker-compose logs"
    exit 1
fi

echo ""
print_success "🎉 WhisperEngine is ready!"
echo "================================"
echo ""
echo "🌐 Web UI:     http://localhost:3001"
echo "🤖 Chat API:   http://localhost:9090/api/chat"
echo "📊 Health:     http://localhost:9090/health"
echo ""
echo "✨ Features:"
echo "• Create AI characters via web interface"
echo "• Persistent memory and conversation history"
echo "• RESTful Chat APIs for integration"
echo "• Optional Discord bot functionality"
echo ""
echo "📖 Next steps:"
echo "1. Visit http://localhost:3001 to create your first character"
echo "2. Test the chat API with curl or your application"
echo "3. Enable Discord integration if desired"
echo ""
echo "🔧 Management commands:"
echo "   docker-compose stop     # Stop WhisperEngine"
echo "   docker-compose start    # Restart WhisperEngine"
echo "   docker-compose logs -f  # View live logs"
echo "   docker-compose down     # Stop and remove containers"
echo ""

# Auto-open browser on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    print_status "🔗 Opening web interface..."
    sleep 2
    open http://localhost:3001
fi

print_success "Setup complete! Enjoy your AI character platform! 🎭"