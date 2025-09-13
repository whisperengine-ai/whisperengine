#!/bin/bash

# Docker Development Helper Script
# This script provides easy commands for Docker-based development

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default environment file
ENV_FILE=".env"

show_help() {
    echo -e "${BLUE}Custom Discord Bot - Docker Development Helper${NC}"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  setup         Initial setup (copy .env.example and create data dirs)"
    echo "  setup-dirs    Create external data directories only"
    echo "  build         Build the Docker images"
    echo "  dev           Start development environment"
    echo "  prod          Start production environment  "
    echo "  stop          Stop all services"
    echo "  restart       Restart all services"
    echo "  logs          Show logs (use with service name)"
    echo "  shell         Open shell in the bot container"
    echo "  test          Run tests in container"
    echo "  clean         Clean up containers and volumes"
    echo "  status        Show status of all services"
    echo ""
    echo "Options:"
    echo "  --env FILE    Use specific environment file (default: .env)"
    echo "  --no-deps     Don't start dependencies (Redis, LM Studio)"
    echo "  --monitor     Include monitoring services"
    echo ""
    echo "Examples:"
    echo "  $0 setup                    # Initial setup with data directories"
    echo "  $0 setup-dirs               # Create data directories only"
    echo "  $0 dev                      # Start development environment"
    echo "  $0 logs discord-bot-dev     # Show bot logs"
    echo "  $0 shell                    # Open shell in bot container"
    echo "  $0 prod --monitor           # Start with monitoring"
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Error: Docker is not installed${NC}"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}Error: Docker Compose is not installed${NC}"
        exit 1
    fi
}

check_env_file() {
    if [[ ! -f "$ENV_FILE" ]]; then
        echo -e "${YELLOW}Warning: $ENV_FILE file not found${NC}"
        echo "Run '$0 setup' to create it from the example file"
        return 1
    fi
    return 0
}

setup_data_dirs() {
    # Get DATA_DIR from environment file or use default
    local data_dir
    if [[ -f "$ENV_FILE" ]] && grep -q "DATA_DIR=" "$ENV_FILE"; then
        data_dir=$(grep "DATA_DIR=" "$ENV_FILE" | cut -d'=' -f2)
    else
        data_dir="./docker-data"
    fi
    
    echo -e "${BLUE}Setting up external data directories in $data_dir${NC}"
    
    # Create directory structure
    mkdir -p "$data_dir"/{chromadb,backups,privacy_data,temp_images,logs}
    
    # Set appropriate permissions
    chmod -R 755 "$data_dir"
    
    echo -e "${GREEN}Data directories created:${NC}"
    echo "  📁 $data_dir/chromadb     - Vector database storage"
    echo "  📁 $data_dir/backups      - Backup files"
    echo "  📁 $data_dir/privacy_data - User privacy data"
    echo "  📁 $data_dir/temp_images  - Temporary image processing"
    echo "  📁 $data_dir/logs         - Application logs"
    echo ""
    echo -e "${YELLOW}Note: This keeps your containers clean and data persistent${NC}"
}

setup_env() {
    if [[ -f "$ENV_FILE" ]]; then
        echo -e "${YELLOW}$ENV_FILE already exists${NC}"
        read -p "Do you want to overwrite it? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Setup cancelled"
            return 0
        fi
    fi
    
    if [[ -f ".env.example" ]]; then
        cp .env.example "$ENV_FILE"
        echo -e "${GREEN}Created $ENV_FILE from example${NC}"
        echo -e "${YELLOW}Please edit $ENV_FILE with your Discord bot token and other settings${NC}"
    else
        echo -e "${RED}Error: .env.example file not found${NC}"
        return 1
    fi
    
    # Create external data directory structure
    setup_data_dirs
}

build_images() {
    echo -e "${BLUE}Building Docker images...${NC}"
    docker-compose -f docker-compose.yml build
    docker-compose -f docker-compose.dev.yml build
    echo -e "${GREEN}Build complete${NC}"
}

start_dev() {
    echo -e "${BLUE}Starting development environment...${NC}"
    
    if ! check_env_file; then
        return 1
    fi
    
    local compose_args=""
    if [[ "$NO_DEPS" == "true" ]]; then
        compose_args="--no-deps discord-bot-dev"
    fi
    
    docker-compose -f docker-compose.dev.yml up -d $compose_args
    echo -e "${GREEN}Development environment started${NC}"
    echo -e "${YELLOW}Bot logs: docker-compose -f docker-compose.dev.yml logs -f discord-bot-dev${NC}"
    echo -e "${YELLOW}Shell access: $0 shell${NC}"
}

start_prod() {
    echo -e "${BLUE}Starting production environment...${NC}"
    
    if ! check_env_file; then
        return 1
    fi
    
    local compose_files="-f docker-compose.yml"
    if [[ "$INCLUDE_MONITORING" == "true" ]]; then
        compose_files="$compose_files --profile monitoring"
    fi
    
    docker-compose $compose_files up -d
    echo -e "${GREEN}Production environment started${NC}"
    echo -e "${YELLOW}Bot logs: docker-compose logs -f discord-bot${NC}"
}

stop_services() {
    echo -e "${BLUE}Stopping all services...${NC}"
    docker-compose -f docker-compose.yml down 2>/dev/null || true
    docker-compose -f docker-compose.dev.yml down 2>/dev/null || true
    echo -e "${GREEN}All services stopped${NC}"
}

restart_services() {
    stop_services
    sleep 2
    if [[ "$1" == "dev" ]]; then
        start_dev
    else
        start_prod
    fi
}

show_logs() {
    local service=${1:-discord-bot-dev}
    echo -e "${BLUE}Showing logs for $service...${NC}"
    
    if docker-compose -f docker-compose.dev.yml ps | grep -q "$service"; then
        docker-compose -f docker-compose.dev.yml logs -f "$service"
    elif docker-compose -f docker-compose.yml ps | grep -q "$service"; then
        docker-compose -f docker-compose.yml logs -f "$service"
    else
        echo -e "${RED}Service $service not found or not running${NC}"
        return 1
    fi
}

open_shell() {
    local container="custom-discord-bot-dev"
    
    if docker ps | grep -q "$container"; then
        echo -e "${BLUE}Opening shell in development container...${NC}"
        docker exec -it "$container" /bin/bash
    else
        container="custom-discord-bot"
        if docker ps | grep -q "$container"; then
            echo -e "${BLUE}Opening shell in production container...${NC}"
            docker exec -it "$container" /bin/bash
        else
            echo -e "${RED}No running bot container found${NC}"
            echo "Start the bot with '$0 dev' or '$0 prod' first"
            return 1
        fi
    fi
}

run_tests() {
    echo -e "${BLUE}Running tests in container...${NC}"
    
    local container="custom-discord-bot-dev"
    if ! docker ps | grep -q "$container"; then
        echo -e "${YELLOW}Starting development container for testing...${NC}"
        start_dev
        sleep 5
    fi
    
    docker exec -it "$container" python -m pytest tests/ -v
}

clean_docker() {
    echo -e "${BLUE}Cleaning up Docker resources...${NC}"
    
    # Stop all services
    stop_services
    
    # Remove containers
    docker-compose -f docker-compose.yml down --volumes --remove-orphans 2>/dev/null || true
    docker-compose -f docker-compose.dev.yml down --volumes --remove-orphans 2>/dev/null || true
    
    # Remove unused images
    docker image prune -f
    
    echo -e "${GREEN}Cleanup complete${NC}"
    echo -e "${YELLOW}Note: Persistent data volumes were preserved${NC}"
}

show_status() {
    echo -e "${BLUE}Service Status:${NC}"
    echo ""
    
    echo -e "${YELLOW}Development services:${NC}"
    docker-compose -f docker-compose.dev.yml ps 2>/dev/null || echo "No development services running"
    
    echo ""
    echo -e "${YELLOW}Production services:${NC}"
    docker-compose -f docker-compose.yml ps 2>/dev/null || echo "No production services running"
}

# Parse command line arguments
NO_DEPS=false
INCLUDE_MONITORING=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --env)
            ENV_FILE="$2"
            shift 2
            ;;
        --no-deps)
            NO_DEPS=true
            shift
            ;;
        --monitor)
            INCLUDE_MONITORING=true
            shift
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            break
            ;;
    esac
done

# Check if Docker is available
check_docker

# Execute commands
case ${1:-help} in
    setup)
        setup_env
        ;;
    setup-dirs)
        setup_data_dirs
        ;;
    build)
        build_images
        ;;
    dev)
        start_dev
        ;;
    prod)
        start_prod
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services "$2"
        ;;
    logs)
        show_logs "$2"
        ;;
    shell)
        open_shell
        ;;
    test)
        run_tests
        ;;
    clean)
        clean_docker
        ;;
    status)
        show_status
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac
