#!/bin/bash

# Multi-Bot Management Script for WhisperEngine
# Manages multiple character bot containers sharing infrastructure

set -e

COMPOSE_FILE="docker-compose.multi-bot.yml"
PROJECT_NAME="whisperengine-multi"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[MULTI-BOT]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Function to check if environment files exist
check_env_files() {
    local missing_files=()
    
    if [[ ! -f ".env.elena" ]]; then
        missing_files+=(".env.elena")
    fi
    
    if [[ ! -f ".env.marcus" ]]; then
        missing_files+=(".env.marcus")
    fi
    
    if [[ ${#missing_files[@]} -gt 0 ]]; then
        print_warning "Missing environment files: ${missing_files[*]}"
        print_info "These files contain bot-specific Discord tokens and configuration"
        print_info "Copy from .env and customize for each bot"
        return 1
    fi
    
    return 0
}

# Function to show status of all containers
show_status() {
    print_status "Multi-Bot Container Status:"
    echo ""
    
    docker compose -f $COMPOSE_FILE -p $PROJECT_NAME ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || {
        print_warning "No containers running"
        return
    }
    
    echo ""
    print_info "Health Check Endpoints:"
    print_info "Elena Bot:  http://localhost:9091/health"
    print_info "Marcus Bot: http://localhost:9092/health"
    echo ""
    print_info "Infrastructure Services:"
    print_info "PostgreSQL: localhost:5432"
    print_info "Redis:      localhost:6379"
    print_info "Qdrant:     localhost:6333"
}

# Function to start all bots
start_all() {
    print_status "Starting all character bots..."
    
    if ! check_env_files; then
        print_error "Cannot start without proper environment files"
        exit 1
    fi
    
    docker compose -f $COMPOSE_FILE -p $PROJECT_NAME up -d
    
    echo ""
    print_status "All bots starting up..."
    sleep 5
    show_status
}

# Function to start specific bot
start_bot() {
    local bot_name=$1
    
    if [[ -z "$bot_name" ]]; then
        print_error "Bot name required. Available: elena, marcus"
        exit 1
    fi
    
    case $bot_name in
        "elena")
            if [[ ! -f ".env.elena" ]]; then
                print_error "Missing .env.elena file"
                exit 1
            fi
            print_status "Starting Elena bot..."
            docker compose -f $COMPOSE_FILE -p $PROJECT_NAME up -d elena-bot redis postgres qdrant
            ;;
        "marcus")
            if [[ ! -f ".env.marcus" ]]; then
                print_error "Missing .env.marcus file"
                exit 1
            fi
            print_status "Starting Marcus bot..."
            docker compose -f $COMPOSE_FILE -p $PROJECT_NAME up -d marcus-bot redis postgres qdrant
            ;;
        *)
            print_error "Unknown bot: $bot_name. Available: elena, marcus"
            exit 1
            ;;
    esac
    
    sleep 3
    show_status
}

# Function to stop specific bot
stop_bot() {
    local bot_name=$1
    
    if [[ -z "$bot_name" ]]; then
        print_error "Bot name required. Available: elena, marcus"
        exit 1
    fi
    
    case $bot_name in
        "elena")
            print_status "Stopping Elena bot..."
            docker compose -f $COMPOSE_FILE -p $PROJECT_NAME stop elena-bot
            ;;
        "marcus")
            print_status "Stopping Marcus bot..."
            docker compose -f $COMPOSE_FILE -p $PROJECT_NAME stop marcus-bot
            ;;
        *)
            print_error "Unknown bot: $bot_name. Available: elena, marcus"
            exit 1
            ;;
    esac
}

# Function to stop all bots
stop_all() {
    print_status "Stopping all character bots..."
    docker compose -f $COMPOSE_FILE -p $PROJECT_NAME down
    print_status "All bots stopped"
}

# Function to show logs
show_logs() {
    local bot_name=$1
    
    if [[ -z "$bot_name" ]]; then
        print_status "Showing logs for all services..."
        docker compose -f $COMPOSE_FILE -p $PROJECT_NAME logs -f
        return
    fi
    
    case $bot_name in
        "elena")
            print_status "Showing Elena bot logs..."
            docker compose -f $COMPOSE_FILE -p $PROJECT_NAME logs -f elena-bot
            ;;
        "marcus")
            print_status "Showing Marcus bot logs..."
            docker compose -f $COMPOSE_FILE -p $PROJECT_NAME logs -f marcus-bot
            ;;
        "infrastructure")
            print_status "Showing infrastructure logs..."
            docker compose -f $COMPOSE_FILE -p $PROJECT_NAME logs -f redis postgres qdrant
            ;;
        *)
            print_error "Unknown service: $bot_name. Available: elena, marcus, infrastructure"
            exit 1
            ;;
    esac
}

# Function to restart specific bot
restart_bot() {
    local bot_name=$1
    
    print_status "Restarting $bot_name bot..."
    stop_bot $bot_name
    sleep 2
    start_bot $bot_name
}

# Function to build containers
build_containers() {
    print_status "Building WhisperEngine bot containers..."
    docker compose -f $COMPOSE_FILE -p $PROJECT_NAME build
    print_status "Build complete"
}

# Function to show help
show_help() {
    echo "WhisperEngine Multi-Bot Management Script"
    echo ""
    echo "Usage: $0 <command> [bot_name]"
    echo ""
    echo "Commands:"
    echo "  start                 - Start all character bots"
    echo "  start <bot>          - Start specific bot (elena, marcus)"
    echo "  stop                 - Stop all bots and infrastructure"
    echo "  stop <bot>           - Stop specific bot"
    echo "  restart <bot>        - Restart specific bot"
    echo "  status               - Show status of all containers"
    echo "  logs [bot]           - Show logs (all, elena, marcus, infrastructure)"
    echo "  build                - Build/rebuild bot containers"
    echo "  help                 - Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 start elena       - Start just Elena bot with infrastructure"
    echo "  $0 logs marcus       - Show Marcus bot logs"
    echo "  $0 restart elena     - Restart Elena bot"
    echo "  $0 status            - Show all container status"
}

# Main script logic
case "${1:-}" in
    "start")
        if [[ -n "${2:-}" ]]; then
            start_bot "$2"
        else
            start_all
        fi
        ;;
    "stop")
        if [[ -n "${2:-}" ]]; then
            stop_bot "$2"
        else
            stop_all
        fi
        ;;
    "restart")
        if [[ -n "${2:-}" ]]; then
            restart_bot "$2"
        else
            print_error "Bot name required for restart. Available: elena, marcus"
            exit 1
        fi
        ;;
    "status")
        show_status
        ;;
    "logs")
        show_logs "${2:-}"
        ;;
    "build")
        build_containers
        ;;
    "help"|"--help"|"-h")
        show_help
        ;;
    "")
        print_error "No command specified"
        show_help
        exit 1
        ;;
    *)
        print_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac