#!/bin/bash
# =============================================================================
# WhisperEngine Lightning Quick Start
# =============================================================================
# Get your AI Discord bot running in under 2 minutes!
# Usage: curl -sSL https://raw.githubusercontent.com/WhisperEngine-AI/whisperengine/main/scripts/quick-start.sh | bash

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_status() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }

echo "🚀 WhisperEngine Lightning Quick Start"
echo "======================================="
echo ""

# Check if Docker is installed and running
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first:"
    echo "  • macOS/Windows: https://docs.docker.com/desktop/"
    echo "  • Linux: https://docs.docker.com/engine/install/"
    exit 1
fi

if ! docker info >/dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker Desktop or the Docker daemon."
    exit 1
fi

# Check if Docker Compose is available
if ! docker compose version &> /dev/null && ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not available. Please install Docker Compose."
    exit 1
fi

# Determine compose command
COMPOSE_CMD="docker compose"
if ! docker compose version &> /dev/null; then
    COMPOSE_CMD="docker-compose"
fi

print_status "Docker is ready!"

# Create project directory
PROJECT_DIR="whisperengine-bot"
if [ -d "$PROJECT_DIR" ]; then
    print_warning "Directory '$PROJECT_DIR' already exists."
    read -p "Do you want to continue and overwrite files? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi
fi

mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"
print_status "Created project directory: $PROJECT_DIR"

# Download configuration files
print_info "Downloading configuration files..."

# Create docker-compose.yml for quick start
cat > docker-compose.yml << 'EOF'
# WhisperEngine Quick Start - Docker Hub Version
# Minimal setup for fastest deployment

services:
  whisperengine:
    image: whisperengine/whisperengine:latest
    container_name: whisperengine-bot
    restart: unless-stopped
    
    env_file:
      - .env
      
    volumes:
      # Mount config directory for personality templates
      - ./config:/app/config:ro
      # Mount prompts directory
      - ./prompts:/app/prompts:ro
      
    ports:
      - "8000:8000"  # ChromaDB web interface (optional)
      
    depends_on:
      - redis
      - postgres
      - chromadb
      - neo4j
      
  # Minimal required services
  redis:
    image: redis:7-alpine
    container_name: whisperengine-redis
    restart: unless-stopped
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    ports:
      - "\${REDIS_PORT:-6379}:6379"
      
  postgres:
    image: postgres:16-alpine
    container_name: whisperengine-postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: \${POSTGRES_DB:-whisper_engine}
      POSTGRES_USER: \${POSTGRES_USER:-bot_user}
      POSTGRES_PASSWORD: \${POSTGRES_PASSWORD:-}
      POSTGRES_INITDB_ARGS: "--auth-host=scram-sha-256"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "\${POSTGRES_PORT:-5432}:5432"
      
  chromadb:
    image: chromadb/chroma:latest
    container_name: whisperengine-chromadb
    restart: unless-stopped
    environment:
      - CHROMA_SERVER_HOST=0.0.0.0
      - CHROMA_SERVER_HTTP_PORT=\${CHROMADB_PORT:-8000}
    volumes:
      - chromadb_data:/chroma/chroma
    ports:
      - "8001:\${CHROMADB_PORT:-8000}"  # Avoid conflict with potential host services
      
  neo4j:
    image: neo4j:5-enterprise
    container_name: whisperengine-neo4j
    restart: unless-stopped
    environment:
      NEO4J_AUTH: \${NEO4J_USERNAME:-neo4j}/\${NEO4J_PASSWORD:-neo4j}
      NEO4J_ACCEPT_LICENSE_AGREEMENT: "yes"
      NEO4J_dbms_security_procedures_unrestricted: "gds.*,apoc.*"
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
    ports:
      - "7474:7474"  # HTTP
      - "\${NEO4J_PORT:-7687}:7687"  # Bolt

volumes:
  redis_data:
  postgres_data:
  chromadb_data:
  neo4j_data:
  neo4j_logs:
EOF

# Download .env.minimal and use it as template
print_info "Downloading environment configuration template..."
if curl -sSL "https://raw.githubusercontent.com/WhisperEngine-AI/whisperengine/main/docker/quick-start/.env.minimal" -o ".env.minimal" 2>/dev/null; then
    print_status "Downloaded Docker quick-start .env.minimal template"
    
    # Create .env from template
    cp .env.minimal .env
    # Also create a visible copy for easy reference
    cp .env.minimal env.example
    
    print_status "Created .env (hidden) and env.example (visible copy)"
else
    print_warning "Could not download .env.minimal, creating basic template..."
    
    # Create basic fallback .env file
    cat > .env << 'EOF'
# =======================================================
# WhisperEngine - Basic Configuration
# =======================================================

# REQUIRED: Discord Bot Token
# Get from: https://discord.com/developers/applications
DISCORD_BOT_TOKEN=your_discord_bot_token_here

# REQUIRED: Local LLM Configuration
# Default: LM Studio (start LM Studio and load a model first)
LLM_CHAT_API_URL=http://host.docker.internal:1234/v1
LLM_MODEL_NAME=your-loaded-model-name

# Bot Settings
DISCORD_COMMAND_PREFIX=!
ADMIN_USER_IDS=your_discord_user_id_here

# Database Configuration (Auto-configured for Docker)
REDIS_HOST=redis
REDIS_PORT=6379
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=whisper_engine
POSTGRES_USER=bot_user
POSTGRES_PASSWORD=
CHROMADB_HOST=chromadb
CHROMADB_PORT=8000

# Neo4j Graph Database (optional)
ENABLE_GRAPH_DATABASE=false
NEO4J_HOST=neo4j
NEO4J_PORT=7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=neo4j

# Advanced Features
DEBUG_MODE=false
LOG_LEVEL=INFO
USE_REDIS_CACHE=true
USE_CHROMADB_HTTP=true
EOF
    
    # Also create visible copy
    cp .env env.example
    print_status "Created basic .env (hidden) and env.example (visible copy)"
fi

# Download prompts directory
print_info "Downloading personality prompts..."
mkdir -p prompts

# Download personality templates from GitHub (new prompts location)
GITHUB_BASE="https://raw.githubusercontent.com/WhisperEngine-AI/whisperengine/main/prompts"
TEMPLATES=(
    "empathetic_companion_template.md"
    "professional_ai_template.md" 
    "casual_friend_template.md"
    "character_ai_template.md"
    "adaptive_ai_template.md"
    "dream_ai_enhanced.md"
    "README.md"
)

for template in "${TEMPLATES[@]}"; do
    if curl -sSL "$GITHUB_BASE/$template" -o "prompts/$template" 2>/dev/null; then
        print_status "Downloaded: $template"
    else
        print_warning "Could not download: $template (will use defaults)"
    fi
done

# Download default system prompt to prompts directory
if curl -sSL "https://raw.githubusercontent.com/WhisperEngine-AI/whisperengine/main/prompts/default.md" -o "prompts/default.md" 2>/dev/null; then
    print_status "Downloaded default prompt"
else
    # Create a basic fallback in prompts directory
    cat > prompts/default.md << 'EOF'
You are a helpful AI assistant. You are friendly, knowledgeable, and always ready to help users with your questions and tasks. You communicate in a warm, approachable manner while being professional and informative.
EOF
    print_warning "Using fallback default prompt"
fi

# Create legacy config directory for backward compatibility
print_info "Creating backward compatibility links..."
mkdir -p config/system_prompts
for template in prompts/*.md; do
    if [[ -f "$template" && "$(basename "$template")" != "README.md" ]]; then
        ln -sf "../../$template" "config/system_prompts/$(basename "$template")"
    fi
done
print_status "Legacy compatibility maintained"

print_status "Configuration files created!"

# Also create a legacy system_prompt.md link for backward compatibility
if [[ -f "prompts/default.md" ]]; then
    ln -sf "prompts/default.md" "system_prompt.md"
    print_status "Created legacy system_prompt.md link"
fi

# Pull the latest image
print_info "Pulling WhisperEngine image from Docker Hub..."
if docker pull whisperengine/whisperengine:latest; then
    print_status "Image downloaded successfully!"
else
    print_error "Failed to pull image. Please check your internet connection."
    exit 1
fi

# Display next steps
echo ""
echo "🎉 Setup Complete! Next steps:"
echo "==============================="
echo ""
print_info "1. Edit your configuration:"
echo "   nano .env                 # Hidden file (use 'ls -la' to see it)"
echo "   nano env.example          # Visible copy for reference"
echo "   (Set your DISCORD_BOT_TOKEN and LLM settings)"
echo ""
print_info "2. Start your bot:"
echo "   $COMPOSE_CMD up -d"
echo ""
print_info "3. View logs:"
echo "   $COMPOSE_CMD logs -f whisperengine"
echo ""
print_info "4. Check health:"
echo "   curl http://localhost:9090/health    # Health status"
echo "   curl http://localhost:9090/ready     # Bot readiness"
echo "   curl http://localhost:9090/metrics   # Bot metrics"
echo ""
print_info "5. Stop your bot:"
echo "   $COMPOSE_CMD down"
echo ""

# Check if we should open the .env file
if command -v nano &> /dev/null; then
    echo "📝 Would you like to edit the configuration now?"
    read -p "Open .env in nano? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        nano .env
    fi
fi

echo ""
print_status "Your WhisperEngine setup is ready!"
echo ""
echo "📚 Documentation:"
echo "   • Quick Start: https://github.com/WhisperEngine-AI/whisperengine/blob/main/docs/getting-started/DOCKER_HUB_QUICK_START.md"
echo "   • Personality Customization: https://github.com/WhisperEngine-AI/whisperengine/blob/main/docs/character/SYSTEM_PROMPT_CUSTOMIZATION.md"
echo "   • Full Documentation: https://github.com/WhisperEngine-AI/whisperengine"
echo ""
echo "💬 Need help? Join our Discord: https://discord.gg/whisperengine"
echo ""
print_info "To start your bot, run: $COMPOSE_CMD up -d"