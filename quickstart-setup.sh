#!/bin/bash
# WhisperEngine Quickstart Setup Script
# Downloads and sets up WhisperEngine for immediate use

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_step() {
    echo -e "${BLUE}🚀 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}💡 $1${NC}"
}

echo ""
echo "🚀 WhisperEngine Quickstart Setup"
echo "=================================="
echo "Setting up WhisperEngine for immediate use (no source code required)"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first:"
    echo "   https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first:"
    echo "   https://docs.docker.com/compose/install/"
    exit 1
fi

print_success "Docker and Docker Compose found"

# Download configuration files
print_step "Downloading WhisperEngine configuration files..."

# Base GitHub URL for raw files
GITHUB_RAW_URL="https://raw.githubusercontent.com/whisperengine-ai/whisperengine/main"

# Download Docker Compose file
if curl -s -f "${GITHUB_RAW_URL}/docker-compose.quickstart.yml" -o docker-compose.quickstart.yml; then
    print_success "Downloaded docker-compose.quickstart.yml"
else
    echo "❌ Failed to download docker-compose.quickstart.yml"
    echo "   Please check your internet connection or download manually from:"
    echo "   ${GITHUB_RAW_URL}/docker-compose.quickstart.yml"
    exit 1
fi

# Download environment template
if curl -s -f "${GITHUB_RAW_URL}/.env.quickstart" -o .env.quickstart; then
    print_success "Downloaded .env.quickstart template"
else
    echo "❌ Failed to download .env.quickstart"
    echo "   Please check your internet connection or download manually from:"
    echo "   ${GITHUB_RAW_URL}/.env.quickstart"
    exit 1
fi

# Create environment file
print_step "Setting up environment configuration..."

if [ ! -f ".env" ]; then
    cp .env.quickstart .env
    print_success "Created .env file from template"
    print_info "You can edit .env to customize your LLM settings"
else
    print_info ".env file already exists - keeping your existing settings"
fi

# Check if models need to be downloaded (first time)
print_step "Preparing to download WhisperEngine containers..."

print_info "This will download WhisperEngine containers (~1-2GB total)"
print_info "Containers include pre-downloaded AI models for instant functionality"

echo ""
print_success "Setup complete! 🎉"
echo ""
echo "📋 Next steps:"
echo ""
echo "1. 📝 Configure your LLM provider (REQUIRED):"
echo "   ${YELLOW}nano .env${NC}  # or use your preferred editor"
echo ""
echo "   Choose one option in .env file:"
echo "   • LM Studio (free, local) - recommended for beginners"
echo "   • OpenRouter (paid, cloud) - easy setup"  
echo "   • OpenAI (paid, cloud) - premium option"
echo ""
echo "2. 🚀 Start WhisperEngine:"
echo "   ${YELLOW}docker-compose -f docker-compose.quickstart.yml up${NC}"
echo ""
echo "3. 🌐 Access your AI assistant:"
echo "   • Web UI: ${BLUE}http://localhost:3001${NC}"
echo "   • HTTP API: ${BLUE}http://localhost:9090/api/chat${NC}"
echo ""
echo "4. 🧪 Test with a quick API call:"
echo "   ${YELLOW}curl -X POST http://localhost:9090/api/chat \\${NC}"
echo "   ${YELLOW}  -H \"Content-Type: application/json\" \\${NC}"
echo "   ${YELLOW}  -d '{\"user_id\": \"test\", \"message\": \"Hello!\"}'${NC}"
echo ""
echo "📚 For detailed instructions, see: https://github.com/whisperengine-ai/whisperengine"
echo ""
print_info "First startup may take 2-3 minutes to download containers"
print_info "After that, startup is typically under 30 seconds"