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
        compose_cmd="docker compose"
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
    echo "🚀 New to WhisperEngine? Try our cross-platform quick-start scripts:"
    echo "   Linux/macOS:   curl -sSL https://raw.githubusercontent.com/WhisperEngine-AI/whisperengine/main/scripts/quick-start.sh | bash"
    echo "   Windows (PS):  iwr https://raw.githubusercontent.com/WhisperEngine-AI/whisperengine/main/scripts/quick-start.ps1 | iex"
    echo "   Windows (CMD): Download and run scripts/quick-start.bat"
    echo ""
    echo "Usage: $0 <command> [mode]"
    echo ""
    echo "Commands:"
    echo "  start [prod|dev|native]  - Start bot (mode required)"
    echo "  stop [prod|dev|native]   - Stop bot"
    echo "  logs [service]           - View logs (default: whisperengine-bot)"
    echo "  status                   - Show container status"
    echo "  restart [prod|dev|native] - Restart bot container only"
    echo "  restart-all [prod|dev|native] - Restart all services (bot + databases)"
    echo "  cleanup                  - Remove orphaned containers and volumes"
    echo "  backup <create|list|restore|help> - Data backup operations"
    echo "  build-push [options]     - Build and push Docker image to Docker Hub"
    echo ""
    echo "Modes:"
    echo "  prod    - Production mode"
    echo "  dev     - Development mode with hot-reload"
    echo "  native  - Native bot + containerized services"
    echo ""
    echo "Examples:"
    echo "  $0 start prod           # Start in production"
    echo "  $0 start dev            # Start in development"
    echo "  $0 restart prod         # Restart bot container only"
    echo "  $0 restart-all prod     # Restart everything (bot + databases)"
    echo "  $0 logs                 # View bot logs"
    echo "  $0 logs redis           # View redis logs"
    echo "  $0 stop                 # Stop (auto-detects mode)"
    echo "  $0 cleanup              # Clean orphaned containers"
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
        print_error "Mode is required. Please specify: prod, dev, or native"
        echo ""
        echo "Usage: $0 start <mode>"
        echo "  prod    - Production mode (docker-compose.yml + docker-compose.prod.yml)"
        echo "  dev     - Development mode (docker-compose.yml + docker-compose.dev.yml)" 
        echo "  native  - Native development (docker-compose.yml only for infrastructure)"
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
        "native")
            if [[ ! -f "docker-compose.yml" ]]; then
                print_error "docker-compose.yml not found"
                exit 1
            fi
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
            echo "🚀 Starting Discord Bot in Development Mode..."
            $COMPOSE_CMD -f docker-compose.yml -f docker-compose.dev.yml up -d --build
            
            # Use improved health check waiting
            if wait_for_services "-f docker-compose.yml -f docker-compose.dev.yml"; then
                print_status "Bot started in development mode with all services healthy!"
                echo ""
                echo "🏥 Health Check: http://localhost:9090/health"
                echo "📊 Bot Status: http://localhost:9090/status"
            else
                print_warning "Some services may still be initializing"
            fi
            
            echo ""
            echo "🔄 Development Features Enabled:"
            echo "   • Live code editing • Debug logging • Auto-restart"
            echo "   • All 4 datastores: PostgreSQL, Redis, ChromaDB, Neo4j"
            ;;
        "native")
            echo "🚀 Starting infrastructure services for native development..."
            
            # Start all 4 core datastores (all required)
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
            
            # Check Python installation
            if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
                print_error "Python not found. Please install Python 3.13+ for native development."
                exit 1
            fi
            
            # Use python3 if python command doesn't exist
            local python_cmd="python"
            if ! command -v python &> /dev/null; then
                python_cmd="python3"
            fi
            
            # Check Python version
            local python_version=$($python_cmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
            if [[ $(echo "$python_version < 3.13" | bc -l 2>/dev/null || echo "1") -eq 1 ]]; then
                print_warning "Python $python_version detected. Python 3.13+ recommended."
            fi
            
            # Check for spaCy model
            if ! $python_cmd -c "import spacy; spacy.load('en_core_web_sm')" &>/dev/null; then
                echo "📦 Installing spaCy English language model..."
                if ! $python_cmd -m spacy download en_core_web_sm; then
                    print_error "Failed to install spaCy model. You may need to install it manually:"
                    echo "   $python_cmd -m pip install spacy"
                    echo "   $python_cmd -m spacy download en_core_web_sm"
                else
                    print_status "spaCy model installed!"
                fi
            fi
            
            # Check for required packages
            if ! $python_cmd -c "import discord, asyncio" &>/dev/null; then
                print_warning "Some Python dependencies may be missing. Install with:"
                echo "   $python_cmd -m pip install -r requirements.txt"
            fi
            
            print_status "Infrastructure ready! Run: $python_cmd run.py"
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
            # Check if dev compose is running
            if $COMPOSE_CMD -f docker-compose.yml -f docker-compose.dev.yml ps -q 2>/dev/null | grep -q .; then
                mode="dev"
            # Check if prod compose is running
            elif $COMPOSE_CMD -f docker-compose.yml -f docker-compose.prod.yml ps -q 2>/dev/null | grep -q .; then
                mode="prod"
            else
                mode="prod"  # fallback to prod
            fi
        else
            print_warning "No running containers detected. Stopping all compose configurations..."
            $COMPOSE_CMD down 2>/dev/null || true
            $COMPOSE_CMD -f docker-compose.yml -f docker-compose.dev.yml down 2>/dev/null || true
            $COMPOSE_CMD -f docker-compose.yml -f docker-compose.prod.yml down 2>/dev/null || true
            print_status "Bot stopped!"
            return 0
        fi
    fi
    
    case $mode in
        "prod")
            echo "🛑 Stopping production services..."
            # Graceful shutdown: Bot first, then datastores
            echo "   🤖 Stopping bot..."
            $COMPOSE_CMD -f docker-compose.yml -f docker-compose.prod.yml stop whisperengine-bot 2>/dev/null || true
            echo "   🗄️ Stopping datastores..."
            $COMPOSE_CMD -f docker-compose.yml -f docker-compose.prod.yml down
            ;;
        "dev")
            echo "🛑 Stopping development services..."
            # Graceful shutdown: Bot first, then datastores
            echo "   🤖 Stopping bot..."
            $COMPOSE_CMD -f docker-compose.yml -f docker-compose.dev.yml stop whisperengine-bot 2>/dev/null || true
            echo "   🗄️ Stopping datastores..."
            $COMPOSE_CMD -f docker-compose.yml -f docker-compose.dev.yml down
            ;;
        "native")
            echo "🛑 Stopping infrastructure services..."
            $COMPOSE_CMD down
            ;;
    esac
    print_status "Bot stopped!"
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
    if $COMPOSE_CMD -f docker-compose.yml -f docker-compose.dev.yml ps -q 2>/dev/null | grep -q .; then
        compose_files="-f docker-compose.yml -f docker-compose.dev.yml"
    elif $COMPOSE_CMD -f docker-compose.yml -f docker-compose.prod.yml ps -q 2>/dev/null | grep -q .; then
        compose_files="-f docker-compose.yml -f docker-compose.prod.yml"
    else
        compose_files=""  # Default to base compose only
    fi
    
    if ! $COMPOSE_CMD $compose_files config --services 2>/dev/null | grep -q "^${service}$"; then
        print_error "Service '$service' not found in Docker Compose configuration"
        echo ""
        echo "Available services:"
        $COMPOSE_CMD $compose_files config --services 2>/dev/null | sed 's/^/  • /' || echo "  Unable to list services"
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
        print_error "Mode is required. Please specify: prod, dev, or native"
        echo ""
        echo "Usage: $0 restart <mode>"
        echo "Note: This only restarts the bot container. Use 'restart-all' to restart everything."
        exit 1
    fi
    
    check_docker
    
    # Auto-detect which compose configuration is running if not native
    local compose_files=""
    case $mode in
        "prod")
            compose_files="-f docker-compose.yml -f docker-compose.prod.yml"
            ;;
        "dev")
            compose_files="-f docker-compose.yml -f docker-compose.dev.yml"
            ;;
        "native")
            print_error "Native mode doesn't run the bot container. Use 'python run.py' to restart the native bot."
            exit 1
            ;;
        *)
            print_error "Invalid mode: $mode"
            exit 1
            ;;
    esac
    
    echo "🔄 Restarting bot container in $mode mode..."
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
}

restart_all() {
    local mode="$1"
    
    # Require explicit mode selection
    if [[ -z "$mode" ]]; then
        print_error "Mode is required. Please specify: prod, dev, or native"
        echo ""
        echo "Usage: $0 restart-all <mode>"
        exit 1
    fi
    
    echo "🔄 Restarting ALL services in $mode mode..."
    stop_bot "$mode"
    sleep 2
    start_bot "$mode"
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
    "cleanup")
        cleanup_containers
        ;;
    "backup")
        shift  # Remove 'backup' from arguments
        handle_backup "$@"
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
