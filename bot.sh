#!/bin/bash
# =============================================================================
# Discord Bot - Unified Management Script
# =============================================================================

set -euo pipefail  # Exit on any error, undefined variables, pipe failures
IFS=$'\n\t'       # Secure Internal Field Separator

# Cleanup function
cleanup() {
    local exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        print_warning "Script interrupted. Cleaning up..."
        # Kill any background processes if they exist
        jobs -p | xargs -r kill 2>/dev/null || true
    fi
    exit $exit_code
}

# Set up signal handlers
trap cleanup EXIT
trap 'cleanup' INT TERM

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Helper functions
print_status() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }

check_docker() {
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker not running. Please start Docker first."
        exit 1
    fi
    
    # Check Docker Compose availability (v1 or v2)
    local compose_cmd=""
    if command -v docker-compose &> /dev/null; then
        compose_cmd="docker-compose"
    elif docker compose version &> /dev/null; then
        compose_cmd="docker"
        export COMPOSE_SUBCMD="compose"
    else
        print_error "Docker Compose is not installed."
        echo "Install Docker Compose: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    # Export compose command for use in other functions
    export COMPOSE_CMD="$compose_cmd"
    
    # Check Docker Compose version for compatibility
    local compose_version=$($compose_cmd version --short 2>/dev/null | head -1 | cut -d'.' -f1-2)
    if [[ -n "$compose_version" ]]; then
        print_status "Using $compose_cmd (version $compose_version)"
    fi
}

check_env() {
    if [ ! -f ".env" ]; then
        print_error "No .env file found!"
        echo "📝 Copy .env.example to .env and configure:"
        echo "   cp .env.example .env"
        exit 1
    fi
    
    # Basic .env validation
    if [[ ! -r ".env" ]]; then
        print_error ".env file is not readable"
        exit 1
    fi
    
    # Check for critical variables (without sourcing the file)
    local missing_vars=()
    
    if ! grep -q "^DISCORD_BOT_TOKEN=" ".env" 2>/dev/null; then
        missing_vars+=("DISCORD_BOT_TOKEN")
    fi
    
    if ! grep -q "^LLM_CHAT_API_URL=" ".env" 2>/dev/null; then
        missing_vars+=("LLM_CHAT_API_URL")
    fi
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        print_warning "Missing critical environment variables in .env:"
        for var in "${missing_vars[@]}"; do
            echo "  • $var"
        done
        echo ""
        echo "Please configure these variables in .env before starting the bot."
    fi
}

show_help() {
    echo "Discord Bot Management Script"
    echo ""
    echo "🚀 For Development: Choose your preferred development style!"
    echo "   Containerized Development:  ./bot.sh start dev   # Hot-reload, mounted code"
    echo "   Native Development:         python run.py        # After starting infrastructure"
    echo "   Desktop App:                python universal_native_app.py"
    echo ""
    echo "🚀 New to WhisperEngine? Try our cross-platform quick-start scripts:"
    echo "   Linux/macOS:   curl -sSL https://raw.githubusercontent.com/WhisperEngine-AI/whisperengine/main/scripts/quick-start.sh | bash"
    echo "   Windows (PS):  iwr https://raw.githubusercontent.com/WhisperEngine-AI/whisperengine/main/scripts/quick-start.ps1 | iex"
    echo "   Windows (CMD): Download and run scripts/quick-start.bat"
    echo ""
    echo "Usage: $0 <command> [mode]"
    echo ""
    echo "Commands:"
    echo "  start [prod|dev|infrastructure]  - Start services (mode required)"
    echo "  stop [prod|dev|infrastructure]   - Stop services"
    echo "  logs [service]                   - View logs (default: whisperengine-bot)"
    echo "  status                           - Show container status"
    echo ""
    echo "Data Import:"
    echo "  import-chatgpt <file> <user-id> [options]  - Import ChatGPT conversations"
    echo ""
    echo "Restart Commands (Data Preservation):"
    echo "  restart [prod|dev|infrastructure]     - Restart services"
    echo "  restart-all [prod|dev|infrastructure] - Restart all services, PRESERVE data"
    echo "  restart-full [prod|dev|infrastructure] - Alias for restart-all (preserve data)"
    echo "  restart-clean [prod|dev|infrastructure] - Restart all services, CLEAR cache only"
    echo ""
    echo "Data Management:"
    echo "  clear-cache [prod|dev|infrastructure] - Clear Redis cache, keep persistent data"
    echo "  reset-data [prod|dev|infrastructure]  - ⚠️  DANGER: Clear ALL data volumes"
    echo "  cleanup                                - Remove orphaned containers and volumes"
    echo "  backup <create|list|restore|help>      - Data backup operations"
    echo ""
    echo "Development:"
    echo "  build-push [options]     - Build and push Docker image to Docker Hub"
    echo ""
    echo "Modes:"
    echo "  prod           - Full production deployment (Discord bot + all services in containers)"
    echo "  dev            - Full development deployment with hot-reload and mounted source code"
    echo "  infrastructure - Infrastructure services only (for developers running bot natively)"
    echo ""
    echo ""
    echo "Examples:"
    echo "  $0 start prod                     # Full production deployment"
    echo "  $0 start dev                      # Development with hot-reload (recommended for dev)"
    echo "  $0 start infrastructure           # Start databases only (for native Python development)"
    echo "  $0 import-chatgpt conversations.json 672814231002939413  # Import ChatGPT history"
    echo "  $0 restart dev                    # Restart development services with code changes"
    echo "  $0 restart-all dev                # Restart all dev services, preserve data"
    echo "  $0 restart-clean dev              # Restart all, clear cache only"
    echo "  $0 clear-cache dev                # Clear cache without restarting"
    echo "  $0 logs                           # View bot logs (auto-detects mode)"
    echo "  $0 logs redis                     # View redis logs"
    echo "  $0 stop                           # Stop (auto-detects mode)"
    echo "  $0 cleanup                        # Clean orphaned containers"
    echo ""
    echo "💡 Development Mode Benefits (dev):"
    echo "   • 🔄 Hot-reload: Code changes automatically restart the bot"
    echo "   • 📁 Local mounts: /src, /prompts, /config directories mounted from host"
    echo "   • 🐛 Debug logging: Detailed logs and error information"
    echo "   • 🏥 Health checks: Monitor bot status during development"
    echo "   • 🚀 Full stack: All services running in containers for consistency"
    echo ""
    echo "💡 Data Persistence Guide:"
    echo "   • restart         → Bot only, everything preserved"
    echo "   • restart-all     → All services, data preserved" 
    echo "   • restart-clean   → All services, cache cleared, memories kept"
    echo "   • reset-data      → ⚠️  Nuclear option: ALL data destroyed"
    echo ""
    echo "💡 Backup & Build Commands:"
    echo "  $0 backup create        # Create data backup"
    echo "  $0 backup list          # List available backups"
    echo "  $0 build-push --help    # Show Docker build options"
    echo "  $0 build-push v1.0.0    # Build and push specific version"
}

# Helper function to wait for services using health checks
wait_for_services() {
    local compose_files="$1"
    local max_attempts=60
    local attempt=0
    
    echo "⏳ Waiting for all services to be healthy..."
    echo "📊 Services: PostgreSQL, Redis, ChromaDB, Neo4j, Bot"
    
    while [[ $attempt -lt $max_attempts ]]; do
        local healthy_count=0
        local status_line=""
        
        # Check infrastructure services health
        if $COMPOSE_CMD $compose_files ps postgres | grep -q "healthy"; then 
            ((healthy_count++))
            status_line+="✅DB "
        else
            status_line+="⏳DB "
        fi
        
        if $COMPOSE_CMD $compose_files ps redis | grep -q "healthy"; then 
            ((healthy_count++))
            status_line+="✅Redis "
        else
            status_line+="⏳Redis "
        fi
        
        if $COMPOSE_CMD $compose_files ps chromadb | grep -q "healthy"; then 
            ((healthy_count++))
            status_line+="✅Vector "
        else
            status_line+="⏳Vector "
        fi
        
        if $COMPOSE_CMD $compose_files ps neo4j | grep -q "healthy"; then 
            ((healthy_count++))
            status_line+="✅Graph "
        else
            status_line+="⏳Graph "
        fi
        
        # Check bot health using our new health endpoint
        if curl -sf http://localhost:9090/health >/dev/null 2>&1; then
            ((healthy_count++))
            status_line+="✅Bot"
        else
            status_line+="⏳Bot"
        fi
        
        # Clear previous line and show current status
        echo -ne "\r$status_line (${healthy_count}/5)"
        
        if [[ $healthy_count -eq 5 ]]; then
            echo ""
            return 0
        fi
        
        sleep 2
        ((attempt++))
    done
    
    echo ""
    print_warning "Some services may still be starting. Use '$0 status' to check."
    return 1
}

start_bot() {
    local mode="$1"
    
    # Require explicit mode selection
    if [[ -z "$mode" ]]; then
        print_error "Mode is required. Please specify: prod, dev, or infrastructure"
        echo ""
        echo "Usage: $0 start <mode>"
        echo "  prod           - Full production deployment (Discord bot + all services)"
        echo "  dev            - Full development deployment with hot-reload and mounted code"
        echo "  infrastructure - Infrastructure services only (for native bot development)" 
        echo ""
        echo "💡 For development, we recommend: $0 start dev (for containerized development with hot-reload)"
        echo "💡 Or: python run.py (after starting infrastructure for native development)"
        exit 1
    fi
    
    check_docker
    check_env
    
    # Validate compose files exist
    case $mode in
        "prod")
            if [[ ! -f "docker-compose.yml" ]] || [[ ! -f "docker-compose.prod.yml" ]]; then
                print_error "Required compose files not found (docker-compose.yml and docker-compose.prod.yml)"
                exit 1
            fi
            ;;
        "dev")
            if [[ ! -f "docker-compose.yml" ]] || [[ ! -f "docker-compose.dev.yml" ]]; then
                print_error "Required compose files not found (docker-compose.yml and docker-compose.dev.yml)"
                exit 1
            fi
            ;;
        "infrastructure")
            if [[ ! -f "docker-compose.yml" ]]; then
                print_error "docker-compose.yml not found"
                exit 1
            fi
            ;;
        *)
            print_error "Invalid mode: $mode"
            echo "Valid modes: prod, dev, infrastructure"
            exit 1
            ;;
    esac
    
    case $mode in
        "prod")
            echo "🚀 Starting Discord Bot in Production Mode..."
            $COMPOSE_CMD -f docker-compose.yml -f docker-compose.prod.yml up -d --build
            
            # Use improved health check waiting
            if wait_for_services "-f docker-compose.yml -f docker-compose.prod.yml"; then
                print_status "Bot started in production mode with all services healthy!"
                echo ""
                echo "🏥 Health Check: http://localhost:9090/health"
                echo "📊 Bot Status: http://localhost:9090/status" 
            else
                print_warning "Some services may still be initializing"
            fi
            
            echo ""
            echo "📋 Quick Commands:"
            echo "   $0 logs        # View logs"
            echo "   $0 stop        # Stop bot"
            echo "   $0 status      # Check status"
            ;;
        "dev")
            echo "🚀 Starting Discord Bot in Development Mode with Hot-Reload..."
            echo "   🔄 Code changes will automatically reload"
            echo "   📁 Local prompts and config mounted"
            echo "   🐛 Debug mode enabled with detailed logging"
            
            $COMPOSE_CMD -f docker-compose.yml -f docker-compose.dev.yml up -d --build
            
            # Use improved health check waiting
            if wait_for_services "-f docker-compose.yml -f docker-compose.dev.yml"; then
                print_status "Bot started in development mode with all services healthy!"
                echo ""
                echo "🏥 Health Check: http://localhost:9090/health"
                echo "📊 Bot Status: http://localhost:9090/status" 
                echo "🔄 Hot-reload: Code changes will automatically restart the bot"
            else
                print_warning "Some services may still be initializing"
            fi
            
            echo ""
            echo "📋 Development Features:"
            echo "   • Hot-reload: Edit code and see changes instantly"
            echo "   • Debug logging: Detailed logs for troubleshooting"
            echo "   • Local mounts: /src, /prompts, /config directories mounted"
            echo "   • Health endpoints: Monitor bot status during development"
            echo ""
            echo "📋 Quick Commands:"
            echo "   $0 logs        # View detailed debug logs"
            echo "   $0 stop        # Stop development environment"
            echo "   $0 status      # Check service health"
            echo "   $0 restart dev # Restart with code changes"
            ;;
        "infrastructure")
            echo "🚀 Starting infrastructure services for native development..."
            
            # Start all 4 core datastores (all required for native development)
            echo "🔄 Starting all core datastore services..."
            echo "   📊 PostgreSQL (persistent data)"
            echo "   🔴 Redis (caching)"  
            echo "   🗃️ ChromaDB (vector storage)"
            echo "   🕸️ Neo4j (graph database)"
            
            # Use --remove-orphans to clean up any leftover containers from previous configurations
            $COMPOSE_CMD up -d --remove-orphans postgres redis chromadb neo4j
            
            echo "⏳ Waiting for all services to initialize..."
            
            # Wait for all services to be healthy with proper status checking
            local max_attempts=30
            local attempt=0
            local services_ready=0
            
            while [[ $attempt -lt $max_attempts && $services_ready -lt 4 ]]; do
                services_ready=0
                
                # Check each service individually (only count once per loop)
                if $COMPOSE_CMD ps postgres | grep -q "healthy"; then ((services_ready++)); fi
                if $COMPOSE_CMD ps redis | grep -q "healthy"; then ((services_ready++)); fi
                if $COMPOSE_CMD ps chromadb | grep -q "Up"; then ((services_ready++)); fi
                if $COMPOSE_CMD ps neo4j | grep -q "healthy"; then ((services_ready++)); fi
                
                if [[ $services_ready -eq 4 ]]; then
                    echo "   ✅ All services ready!"
                    break
                fi
                
                echo "   ⏳ Services ready: $services_ready/4 (attempt $((attempt+1))/$max_attempts)"
                sleep 3
                ((attempt++))
            done
            
            if [[ $services_ready -eq 4 ]]; then
                print_status "All 4 datastores are healthy and ready!"
                echo "   📊 PostgreSQL: localhost:5432"
                echo "   🔴 Redis: localhost:6379" 
                echo "   🗃️ ChromaDB: localhost:8000"
                echo "   🕸️ Neo4j: localhost:7474 (web) / localhost:7687 (bolt)"
            else
                print_warning "Some services may still be starting. Run '$0 status' to check."
            fi
            
            # Python dependency checks (optional for infrastructure-only mode)
            # Only check if Python is available - don't force installation
            if command -v python &> /dev/null || command -v python3 &> /dev/null; then
                # Use python3 if python command doesn't exist
                local python_cmd="python"
                if ! command -v python &> /dev/null; then
                    python_cmd="python3"
                fi
                
                # Check Python version
                local python_version=$($python_cmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "unknown")
                if [[ "$python_version" != "unknown" ]] && [[ $(echo "$python_version < 3.13" | bc -l 2>/dev/null || echo "1") -eq 1 ]]; then
                    print_warning "Python $python_version detected. Python 3.13+ recommended for native development."
                fi
                
                # Only show info about dependencies if they're missing (don't try to install)
                if ! $python_cmd -c "import spacy; spacy.load('en_core_web_sm')" &>/dev/null 2>&1; then
                    echo "ℹ️  Note: spaCy model not found (only needed for native development)"
                fi
                
                # Check for required packages
                if ! $python_cmd -c "import discord, asyncio" &>/dev/null 2>&1; then
                    echo "ℹ️  Note: Some Python dependencies not found (only needed for native development)"
                    echo "   If you plan to run the bot natively, install with:"
                    echo "   $python_cmd -m pip install -r requirements-core.txt"
                    echo "   $python_cmd -m pip install -r requirements-platform.txt"
                    echo "   $python_cmd -m pip install -r requirements-discord.txt"
                    echo "   Or use: ./scripts/install-discord.sh"
                fi
            else
                echo "ℹ️  Note: Python not found (only needed for native development)"
            fi
            
            print_status "Infrastructure ready!"
            echo ""
            echo "💡 Next steps:"
            echo "   # For Docker development:"
            echo "   $0 start dev              # Start bot in Docker with hot-reload"
            echo "   $0 start prod             # Start bot in Docker production mode"
            echo ""
            echo "   # For native development:"
            echo "   source .venv/bin/activate # Activate virtual environment"
            echo "   python3 run.py            # Discord bot"
            echo "   python3 universal_native_app.py   # Desktop app"
            echo ""
            echo "📋 Infrastructure Status:"
            echo "   $0 status       # Check infrastructure health"
            echo "   $0 stop         # Stop infrastructure"
            ;;
        *)
            print_error "Invalid mode: $mode"
            show_help
            exit 1
            ;;
    esac
}

stop_bot() {
    local mode="${1:-auto}"
    check_docker  # Ensure COMPOSE_CMD is set
    
    if [ "$mode" = "auto" ]; then
        # Auto-detect running compose setup by checking which containers are running
        if $COMPOSE_CMD ps -q 2>/dev/null | grep -q .; then
            # Check if prod compose is running
            if $COMPOSE_CMD -f docker-compose.yml -f docker-compose.prod.yml ps -q 2>/dev/null | grep -q .; then
                mode="prod"
            # Check if dev compose is running
            elif $COMPOSE_CMD -f docker-compose.yml -f docker-compose.dev.yml ps -q 2>/dev/null | grep -q .; then
                mode="dev"
            else
                mode="infrastructure"  # fallback to infrastructure mode
            fi
        else
            print_warning "No running containers detected. Stopping all compose configurations..."
            $COMPOSE_CMD down 2>/dev/null || true
            $COMPOSE_CMD -f docker-compose.yml -f docker-compose.prod.yml down 2>/dev/null || true
            $COMPOSE_CMD -f docker-compose.yml -f docker-compose.dev.yml down 2>/dev/null || true
            print_status "Services stopped!"
            return 0
        fi
    fi
    
    case $mode in
        "prod")
            echo "🛑 Stopping production bot only..."
            echo "   🤖 Stopping bot container..."
            $COMPOSE_CMD -f docker-compose.yml -f docker-compose.prod.yml stop whisperengine-bot 2>/dev/null || true
            echo "   🗄️ Infrastructure services remain running"
            ;;
        "dev")
            echo "🛑 Stopping development bot only..."
            echo "   🤖 Stopping development bot container..."
            $COMPOSE_CMD -f docker-compose.yml -f docker-compose.dev.yml stop whisperengine-bot 2>/dev/null || true
            echo "   🗄️ Infrastructure services remain running"
            ;;
        "infrastructure")
            echo "🛑 Stopping infrastructure services..."
            echo "   💡 Note: Your native Discord bot (if running) will continue running"
            $COMPOSE_CMD down
            ;;
        "all")
            echo "🛑 Stopping all services..."
            # Graceful shutdown: Bot first, then datastores
            echo "   🤖 Stopping bot..."
            $COMPOSE_CMD -f docker-compose.yml -f docker-compose.prod.yml stop whisperengine-bot 2>/dev/null || true
            $COMPOSE_CMD -f docker-compose.yml -f docker-compose.dev.yml stop whisperengine-bot 2>/dev/null || true
            echo "   🗄️ Stopping datastores..."
            $COMPOSE_CMD -f docker-compose.yml -f docker-compose.prod.yml down 2>/dev/null || true
            $COMPOSE_CMD -f docker-compose.yml -f docker-compose.dev.yml down 2>/dev/null || true
            $COMPOSE_CMD down 2>/dev/null || true
            ;;
        *)
            print_error "Invalid mode: $mode"
            echo "Valid modes: prod, dev, infrastructure, all"
            exit 1
            ;;
    esac
    print_status "Services stopped!"
}

show_logs() {
    check_docker  # Ensure COMPOSE_CMD is set
    
    # Validate service name to prevent command injection
    local service="${1:-whisperengine-bot}"
    if [[ ! "$service" =~ ^[a-zA-Z0-9_-]+$ ]]; then
        print_error "Invalid service name: $service"
        print_warning "Valid service names contain only letters, numbers, underscores, and hyphens"
        return 1
    fi
    
    # Check if the service exists in the compose configuration
    # Auto-detect which compose configuration is running
    local compose_files=""
    if $COMPOSE_CMD -f docker-compose.yml -f docker-compose.prod.yml ps -q 2>/dev/null | grep -q .; then
        compose_files="-f docker-compose.yml -f docker-compose.prod.yml"
    elif $COMPOSE_CMD -f docker-compose.yml -f docker-compose.dev.yml ps -q 2>/dev/null | grep -q .; then
        compose_files="-f docker-compose.yml -f docker-compose.dev.yml"
    else
        compose_files=""  # Default to base compose only (infrastructure mode)
    fi
    
    if ! $COMPOSE_CMD $compose_files config --services 2>/dev/null | grep -q "^${service}$"; then
        print_error "Service '$service' not found in Docker Compose configuration"
        echo ""
        echo "Available services:"
        $COMPOSE_CMD $compose_files config --services 2>/dev/null | sed 's/^/  • /' || echo "  Unable to list services"
        echo ""
        echo "💡 Note: If you're running in infrastructure mode, only infrastructure services are available."
        echo "   For Discord bot logs, check your native Python process logs."
        return 1
    fi
    
    echo "📋 Viewing $service logs (Ctrl+C to exit)..."
    $COMPOSE_CMD $compose_files logs -f "$service"
}

show_status() {
    check_docker  # Ensure COMPOSE_CMD is set
    echo "📊 Container Status:"
    
    # Auto-detect which compose configuration is running
    local compose_files=""
    if $COMPOSE_CMD -f docker-compose.yml -f docker-compose.dev.yml ps -q 2>/dev/null | grep -q .; then
        echo "   (Development configuration)"
        compose_files="-f docker-compose.yml -f docker-compose.dev.yml"
        $COMPOSE_CMD -f docker-compose.yml -f docker-compose.dev.yml ps
    elif $COMPOSE_CMD -f docker-compose.yml -f docker-compose.prod.yml ps -q 2>/dev/null | grep -q .; then
        echo "   (Production configuration)"
        compose_files="-f docker-compose.yml -f docker-compose.prod.yml"
        $COMPOSE_CMD -f docker-compose.yml -f docker-compose.prod.yml ps
    else
        echo "   (Base configuration)"
        $COMPOSE_CMD ps
        return  # Skip health checks for base config
    fi
    
    echo ""
    echo "🏥 Health Status:"
    
    # Check infrastructure health
    local healthy_count=0
    
    if $COMPOSE_CMD -f docker-compose.yml -f docker-compose.dev.yml ps postgres 2>/dev/null | grep -q "healthy" || $COMPOSE_CMD -f docker-compose.yml -f docker-compose.prod.yml ps postgres 2>/dev/null | grep -q "healthy"; then 
        echo "   ✅ PostgreSQL: Healthy"
        ((healthy_count++))
    else
        echo "   ❌ PostgreSQL: Not healthy"
    fi
    
    if $COMPOSE_CMD -f docker-compose.yml -f docker-compose.dev.yml ps redis 2>/dev/null | grep -q "healthy" || $COMPOSE_CMD -f docker-compose.yml -f docker-compose.prod.yml ps redis 2>/dev/null | grep -q "healthy"; then 
        echo "   ✅ Redis: Healthy"
        ((healthy_count++))
    else
        echo "   ❌ Redis: Not healthy"
    fi
    
    if $COMPOSE_CMD -f docker-compose.yml -f docker-compose.dev.yml ps chromadb 2>/dev/null | grep -q "healthy" || $COMPOSE_CMD -f docker-compose.yml -f docker-compose.prod.yml ps chromadb 2>/dev/null | grep -q "healthy"; then 
        echo "   ✅ ChromaDB: Healthy"
        ((healthy_count++))
    else
        echo "   ❌ ChromaDB: Not healthy"
    fi
    
    if $COMPOSE_CMD -f docker-compose.yml -f docker-compose.dev.yml ps neo4j 2>/dev/null | grep -q "healthy" || $COMPOSE_CMD -f docker-compose.yml -f docker-compose.prod.yml ps neo4j 2>/dev/null | grep -q "healthy"; then 
        echo "   ✅ Neo4j: Healthy"
        ((healthy_count++))
    else
        echo "   ❌ Neo4j: Not healthy"
    fi
    
    # Check bot health using our health endpoint
    if curl -sf http://localhost:9090/health >/dev/null 2>&1; then
        echo "   ✅ Bot: Healthy"
        ((healthy_count++))
        
        # Show additional bot info
        echo ""
        echo "🤖 Bot Health Details:"
        if command -v jq >/dev/null 2>&1; then
            curl -s http://localhost:9090/status 2>/dev/null | jq -r '
                "   Bot User: " + (.bot.user // "Unknown"),
                "   Guilds: " + (.bot.guilds_count | tostring),
                "   Latency: " + (.bot.latency_ms | tostring) + "ms",
                "   Ready: " + (.bot.is_ready | tostring)
            ' 2>/dev/null || echo "   (Health endpoint data available at http://localhost:9090/status)"
        else
            echo "   Health endpoint: http://localhost:9090/health"
            echo "   Status endpoint: http://localhost:9090/status"
            echo "   Install 'jq' for detailed health info display"
        fi
    else
        echo "   ❌ Bot: Not healthy or not responding"
    fi
    
    echo ""
    echo "📈 Overall Status: $healthy_count/5 services healthy"
    
    if [[ $healthy_count -eq 5 ]]; then
        print_status "All systems operational!"
    elif [[ $healthy_count -ge 4 ]]; then
        print_warning "Most services healthy, check any failed services above"
    else
        print_error "Multiple services unhealthy. Consider restarting: $0 restart-all"
    fi
}

restart_bot() {
    local mode="$1"
    
    # Require explicit mode selection
    if [[ -z "$mode" ]]; then
        print_error "Mode is required. Please specify: prod, dev, or infrastructure"
        echo ""
        echo "Usage: $0 restart <mode>"
        echo "  prod           - Restart production bot container"
        echo "  dev            - Restart development bot container with hot-reload"
        echo "  infrastructure - Restart infrastructure services only"
        echo ""
        echo "💡 For native development, restart your Python process manually."
        exit 1
    fi
    
    check_docker
    
    # Auto-detect which compose configuration is running
    local compose_files=""
    case $mode in
        "prod")
            compose_files="-f docker-compose.yml -f docker-compose.prod.yml"
            echo "🔄 Restarting production bot container..."
            eval "$COMPOSE_CMD $compose_files restart whisperengine-bot"
            
            # Wait a moment for the container to be ready
            echo "⏳ Waiting for bot to restart..."
            sleep 3
            
            # Check if the bot container is running
            if eval "$COMPOSE_CMD $compose_files ps whisperengine-bot" | grep -q "Up"; then
                print_status "Bot container restarted successfully!"
            else
                print_warning "Bot container may still be starting. Check status with: $0 status"
            fi
            ;;
        "dev")
            compose_files="-f docker-compose.yml -f docker-compose.dev.yml"
            echo "🔄 Restarting development bot container with hot-reload..."
            eval "$COMPOSE_CMD $compose_files restart whisperengine-bot"
            
            # Wait a moment for the container to be ready
            echo "⏳ Waiting for bot to restart..."
            sleep 3
            
            # Check if the bot container is running
            if eval "$COMPOSE_CMD $compose_files ps whisperengine-bot" | grep -q "Up"; then
                print_status "Development bot container restarted successfully!"
                echo "🔄 Hot-reload is active - code changes will automatically restart the bot"
            else
                print_warning "Bot container may still be starting. Check status with: $0 status"
            fi
            ;;
        "infrastructure")
            echo "🔄 Restarting infrastructure services..."
            $COMPOSE_CMD restart postgres redis chromadb neo4j
            
            echo "⏳ Waiting for services to restart..."
            sleep 5
            
            print_status "Infrastructure services restarted!"
            echo "💡 Your native Discord bot (if running) continues unchanged."
            ;;
        *)
            print_error "Invalid mode: $mode"
            echo "Valid modes: prod, dev, infrastructure"
            exit 1
            ;;
    esac
}

restart_all() {
    local mode="$1"
    
    # Require explicit mode selection
    if [[ -z "$mode" ]]; then
        print_error "Mode is required. Please specify: prod, dev, or infrastructure"
        echo ""
        echo "Usage: $0 restart-all <mode>"
        echo "💡 This preserves all data (memories, embeddings, relationships)"
        exit 1
    fi
    
    echo "🔄 Restarting ALL services in $mode mode (preserving data)..."
    stop_bot "$mode"
    sleep 2
    start_bot "$mode"
}

restart_full() {
    # Alias for restart_all with clearer name
    restart_all "$1"
}

restart_clean() {
    local mode="$1"
    
    # Require explicit mode selection
    if [[ -z "$mode" ]]; then
        print_error "Mode is required. Please specify: prod, dev, or infrastructure"
        echo ""
        echo "Usage: $0 restart-clean <mode>"
        echo "💡 This clears cache but preserves memories and embeddings"
        exit 1
    fi
    
    echo "🔄 Restarting ALL services in $mode mode (clearing cache)..."
    
    # Stop services
    stop_bot "$mode"
    
    # Clear Redis cache specifically
    echo "🧹 Clearing Redis cache..."
    clear_redis_cache "$mode"
    
    sleep 2
    start_bot "$mode"
    
    print_status "Services restarted with cache cleared!"
    echo "💾 Persistent data (memories, embeddings) preserved"
}

clear_cache() {
    local mode="${1:-auto}"
    
    echo "🧹 Clearing Redis cache in $mode mode..."
    clear_redis_cache "$mode"
    print_status "Cache cleared! Bot will rebuild conversations from persistent memory."
}

clear_redis_cache() {
    local mode="$1"
    
    # Try to clear Redis if it's running (more reliable check)
    if docker exec whisperengine-redis redis-cli PING >/dev/null 2>&1; then
        echo "   🗑️ Flushing Redis cache..."
        docker exec whisperengine-redis redis-cli FLUSHALL
        echo "   ✅ Redis cache cleared successfully"
    else
        echo "   ⚠️ Redis container not running, cache will be empty on next start"
    fi
}

reset_data() {
    local mode="$1"
    
    # Require explicit mode selection
    if [[ -z "$mode" ]]; then
        print_error "Mode is required. Please specify: prod, dev, or infrastructure"
        echo ""
        echo "Usage: $0 reset-data <mode>"
        exit 1
    fi
    
    # Safety confirmation
    echo "⚠️  DANGER: This will permanently delete ALL data including:"
    echo "   • User memories and conversation history"
    echo "   • Vector embeddings and semantic search index"
    echo "   • Graph relationships and personality profiles"
    echo "   • All cached data"
    echo ""
    echo "🔴 This action CANNOT be undone!"
    echo ""
    read -p "Type 'DELETE ALL DATA' to confirm: " confirmation
    
    if [[ "$confirmation" != "DELETE ALL DATA" ]]; then
        print_status "Data reset cancelled - no changes made"
        return 0
    fi
    
    echo ""
    echo "🔥 Stopping services and deleting ALL data volumes..."
    
    # Stop everything first
    stop_bot "$mode"
    
    # Get compose files for the mode
    local compose_files=""
    case $mode in
        "prod")
            compose_files="-f docker-compose.yml -f docker-compose.prod.yml"
            ;;
        "dev")
            compose_files="-f docker-compose.yml -f docker-compose.dev.yml"
            ;;
        "infrastructure")
            compose_files=""
            ;;
        *)
            print_error "Invalid mode: $mode"
            exit 1
            ;;
    esac
    
    # Remove containers AND volumes
    echo "💥 Removing containers and volumes..."
    eval "$COMPOSE_CMD $compose_files down -v --remove-orphans"
    
    # Also remove any named volumes that might persist
    echo "🗑️ Removing named volumes..."
    docker volume rm whisperengine-redis 2>/dev/null || true
    docker volume rm whisperengine-postgres 2>/dev/null || true
    docker volume rm whisperengine-chromadb 2>/dev/null || true
    docker volume rm whisperengine-neo4j-data 2>/dev/null || true
    docker volume rm whisperengine-data 2>/dev/null || true
    docker volume rm whisperengine-backups 2>/dev/null || true
    
    print_status "ALL data volumes deleted!"
    echo ""
    echo "🚀 Start the bot again with: $0 start $mode"
    echo "💡 The bot will initialize with fresh databases and no memory of previous conversations"
}

cleanup_containers() {
    check_docker  # Ensure COMPOSE_CMD is set
    
    echo "🧹 Cleaning up orphaned containers and volumes..."
    
    # Stop and remove all containers related to this project
    echo "🛑 Stopping all project containers..."
    $COMPOSE_CMD down --remove-orphans 2>/dev/null || true
    $COMPOSE_CMD -f docker-compose.yml -f docker-compose.dev.yml down --remove-orphans 2>/dev/null || true
    $COMPOSE_CMD -f docker-compose.yml -f docker-compose.prod.yml down --remove-orphans 2>/dev/null || true
    
    # Remove any orphaned containers with old custom-bot or whisperengine-bot prefix
    echo "🗑️ Removing orphaned containers..."
    docker ps -a --format "table {{.Names}}" | grep -E "^(custom-bot|whisperengine)" | xargs -r docker rm -f 2>/dev/null || true
    
    # Clean up unused volumes (but keep data volumes)
    echo "💾 Cleaning unused Docker resources..."
    docker system prune -f --volumes 2>/dev/null || true
    
    print_status "Cleanup completed!"
    echo "💡 Note: Data volumes (postgres, redis, chromadb) are preserved"
    echo "   To remove all data, use: docker volume prune"
}

# Backup operations
handle_backup() {
    # Check if backup script exists
    local backup_script="./scripts/backup.sh"
    if [[ ! -f "$backup_script" ]]; then
        print_error "Backup script not found: $backup_script"
        echo "The backup functionality requires the backup script to be present."
        exit 1
    fi
    
    # Make sure backup script is executable
    if [[ ! -x "$backup_script" ]]; then
        chmod +x "$backup_script"
    fi
    
    # Pass all arguments to the backup script
    local backup_command="${1:-help}"
    shift || true  # Remove first argument, keep the rest
    
    case "$backup_command" in
        "create"|"list"|"restore"|"cleanup"|"help")
            exec "$backup_script" "$backup_command" "$@"
            ;;
        *)
            print_error "Invalid backup command: $backup_command"
            echo "Valid backup commands: create, list, restore, cleanup, help"
            echo "Use '$0 backup help' for detailed backup help"
            exit 1
            ;;
    esac
}

# Main command handling
case "${1:-help}" in
    "start")
        start_bot "${2:-}"
        ;;
    "stop")
        stop_bot "${2:-auto}"
        ;;
    "logs")
        # Validate second argument if provided
        if [[ -n "${2:-}" ]] && [[ ! "${2:-}" =~ ^[a-zA-Z0-9_-]+$ ]]; then
            print_error "Invalid service name: ${2:-}"
            exit 1
        fi
        show_logs "${2:-whisperengine-bot}"
        ;;
    "status")
        show_status
        ;;
    "restart")
        restart_bot "${2:-}"
        ;;
    "restart-all")
        restart_all "${2:-}"
        ;;
    "restart-full")
        restart_full "${2:-}"
        ;;
    "restart-clean")
        restart_clean "${2:-}"
        ;;
    "clear-cache")
        clear_cache "${2:-}"
        ;;
    "reset-data")
        reset_data "${2:-}"
        ;;
    "cleanup")
        cleanup_containers
        ;;
    "backup")
        shift  # Remove 'backup' from arguments
        handle_backup "$@"
        ;;
    "import-chatgpt")
        if [[ $# -lt 3 ]]; then
            print_error "Usage: $0 import-chatgpt <conversations.json> <discord-user-id> [options]"
            echo ""
            echo "Examples:"
            echo "  $0 import-chatgpt ~/Downloads/conversations.json 672814231002939413"
            echo "  $0 import-chatgpt conversations.json 672814231002939413 --verbose"
            echo "  $0 import-chatgpt conversations.json 672814231002939413 --dry-run"
            echo ""
            echo "Options:"
            echo "  --verbose     Show detailed progress"
            echo "  --dry-run     Test without importing"
            echo "  --start-date  Only import after date (YYYY-MM-DD)"
            echo "  --end-date    Only import before date (YYYY-MM-DD)"
            echo "  --min-messages Skip conversations shorter than N messages"
            exit 1
        fi
        
        local conversations_file="$2"
        local user_id="$3"
        shift 3  # Remove the command and required arguments
        
        # Validate file exists
        if [[ ! -f "$conversations_file" ]]; then
            print_error "File not found: $conversations_file"
            echo "Make sure the path to your conversations.json file is correct."
            exit 1
        fi
        
        # Validate user ID format (Discord user IDs are 17-19 digits)
        if [[ ! "$user_id" =~ ^[0-9]{17,19}$ ]]; then
            print_error "Invalid Discord User ID format: $user_id"
            echo "Discord User IDs should be 17-19 digit numbers."
            echo "Get your ID: Discord Settings → Advanced → Developer Mode → Right-click username → Copy User ID"
            exit 1
        fi
        
        print_status "Starting ChatGPT import..."
        echo "📁 File: $conversations_file"
        echo "👤 User ID: $user_id"
        echo "⚙️  Options: $*"
        echo ""
        
        # Check if services are running, start if needed
        check_docker
        check_env
        
        # Detect mode and ensure services are running
        local mode="auto"
        if [[ -f "docker-compose.override.yml" ]]; then
            mode="dev"
        else
            mode="prod"
        fi
        
        # Ensure bot services are running
        if ! $COMPOSE_CMD ps whisperengine-bot | grep -q "Up"; then
            print_warning "WhisperEngine bot is not running. Starting services..."
            start_bot "$mode"
            sleep 10  # Give services time to fully start
        fi
        
        # Run the import using Docker exec
        print_status "Running ChatGPT import in container..."
        
        # Convert file path to absolute path for Docker mounting
        local abs_conversations_file=$(realpath "$conversations_file")
        local container_file="/tmp/conversations.json"
        
        # Copy file into container
        docker cp "$abs_conversations_file" whisperengine-bot:"$container_file"
        
        # Run the import command with all passed options
        if docker exec whisperengine-bot python scripts/chatgpt_import/import_chatgpt.py \
            --file "$container_file" \
            --user-id "$user_id" \
            "$@"; then
            print_status "ChatGPT import completed successfully!"
            echo ""
            echo "🧠 Your ChatGPT conversations are now part of WhisperEngine's memory."
            echo "🔍 Test it: Ask WhisperEngine about something you discussed in ChatGPT."
            echo "📊 Check stats with Discord commands like: !memory user stats"
        else
            print_error "ChatGPT import failed. Check the logs above for details."
            echo ""
            echo "💡 Troubleshooting tips:"
            echo "  • Make sure the file is a valid ChatGPT export (conversations.json)"
            echo "  • Verify your Discord User ID is correct"
            echo "  • Check that WhisperEngine services are healthy: $0 status"
            echo "  • Try a dry run first: $0 import-chatgpt file.json user-id --dry-run"
            exit 1
        fi
        
        # Clean up temporary file
        docker exec whisperengine-bot rm -f "$container_file" 2>/dev/null || true
        ;;
    "build-push")
        shift  # Remove 'build-push' from arguments
        # Forward all remaining arguments to the Docker build script
        exec "$(dirname "$0")/scripts/docker-build-push.sh" "$@"
        ;;
    "help"|*)
        show_help
        ;;
esac
