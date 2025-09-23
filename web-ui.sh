#!/bin/bash
# WhisperEngine Web UI Management Script
# Manages web UI as part of the multi-bot infrastructure

set -e

# Configuration - Use multi-bot infrastructure
COMPOSE_FILE="docker-compose.multi-bot.yml"
SERVICE_NAME="whisperengine-web"
WEB_UI_PORT="8080"
PROJECT_NAME="whisperengine-multi"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

show_usage() {
    echo -e "${BLUE}WhisperEngine Web UI Management Script${NC}"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  start           Start the web UI service"
    echo "  stop            Stop the web UI service"
    echo "  restart         Restart the web UI service"
    echo "  logs            Show web UI logs"
    echo "  logs -f         Follow web UI logs"
    echo "  status          Show service status"
    echo "  health          Check web UI health"
    echo "  build           Build/rebuild the web UI container"
    echo "  shell           Open shell in web UI container"
    echo "  clean           Stop and remove containers/volumes"
    echo ""
    echo "Examples:"
    echo "  $0 start"
    echo "  $0 logs -f"
    echo "  $0 health"
    echo ""
    echo -e "${YELLOW}Note: Web UI runs standalone - no external dependencies required!${NC}"
    echo "  Optional: Start bots with ./multi-bot.sh start [bot_name] for real bot responses"
}

check_requirements() {
    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        echo -e "${RED}❌ Docker is not running${NC}"
        exit 1
    fi
    
    # Check if compose file exists
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        echo -e "${RED}❌ Docker Compose file not found: $COMPOSE_FILE${NC}"
        exit 1
    fi
}

check_infrastructure() {
    echo -e "${BLUE}🔍 Checking multi-bot infrastructure status...${NC}"
    
    # Check if compose file exists
    if [ ! -f "$COMPOSE_FILE" ]; then
        echo -e "${RED}❌ Docker compose file not found: $COMPOSE_FILE${NC}"
        echo -e "${YELLOW}💡 Run: python scripts/generate_multi_bot_config.py${NC}"
        exit 1
    fi
    
    # Check infrastructure services
    echo -e "${BLUE}📦 Checking infrastructure services...${NC}"
    docker-compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" ps postgres redis qdrant
}

start_service() {
    echo -e "${BLUE}🚀 Starting WhisperEngine Web UI (multi-bot infrastructure)...${NC}"
    check_infrastructure
    
    # Start infrastructure first if not running
    echo -e "${BLUE}📦 Ensuring infrastructure is running...${NC}"
    docker-compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" up -d postgres redis qdrant
    
    # Wait a moment for infrastructure to be ready
    sleep 3
    
    # Start web UI
    echo -e "${BLUE}🌐 Starting web interface...${NC}"
    docker-compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" up -d "$SERVICE_NAME"
    
    echo -e "${GREEN}✅ Web UI service started (part of multi-bot infrastructure)${NC}"
    echo -e "${BLUE}🌐 Access at: http://localhost:$WEB_UI_PORT${NC}"
    echo -e "${BLUE}📊 Admin at: http://localhost:$WEB_UI_PORT/admin${NC}"
}

stop_service() {
    echo -e "${BLUE}🛑 Stopping WhisperEngine Web UI...${NC}"
    docker-compose -f "$COMPOSE_FILE" down
    echo -e "${GREEN}✅ Web UI service stopped${NC}"
}

restart_service() {
    echo -e "${BLUE}🔄 Restarting Web UI...${NC}"
    docker-compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" restart "$SERVICE_NAME"
    echo -e "${GREEN}✅ Web UI restarted${NC}"
}

logs_service() {
    echo -e "${BLUE}📋 Showing Web UI logs...${NC}"
    docker-compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" logs -f "$SERVICE_NAME"
}

show_status() {
    echo -e "${BLUE}📊 WhisperEngine Web UI Status${NC}"
    echo ""
    
    # Service status
    if docker-compose -f "$COMPOSE_FILE" ps | grep -q "$SERVICE_NAME.*Up"; then
        echo -e "${GREEN}✅ Service: Running${NC}"
    else
        echo -e "${RED}❌ Service: Stopped${NC}"
    fi
    
    # Port status
    if nc -z localhost "$WEB_UI_PORT" 2>/dev/null; then
        echo -e "${GREEN}✅ Port $WEB_UI_PORT: Accessible${NC}"
    else
        echo -e "${RED}❌ Port $WEB_UI_PORT: Not accessible${NC}"
    fi
    
    # Container details
    echo ""
    docker-compose -f "$COMPOSE_FILE" ps
}

check_health() {
    echo -e "${BLUE}🔍 Checking Web UI health...${NC}"
    
    # Check if service is running
    if docker-compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" ps "$SERVICE_NAME" | grep -q "Up"; then
        echo -e "${GREEN}✅ Web UI container is running${NC}"
        
        # Check HTTP health endpoint
        echo -e "${BLUE}📡 Testing HTTP health endpoint...${NC}"
        if curl -s "http://localhost:$WEB_UI_PORT/health" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Web UI is responding to HTTP requests${NC}"
            
            # Show health details
            echo -e "${BLUE}📊 Health status:${NC}"
            curl -s "http://localhost:$WEB_UI_PORT/health" | python3 -m json.tool
        else
            echo -e "${RED}❌ Web UI is not responding to HTTP requests${NC}"
        fi
    else
        echo -e "${RED}❌ Web UI container is not running${NC}"
    fi
}

build_service() {
    echo -e "${BLUE}🔨 Building Web UI container...${NC}"
    docker-compose -f "$COMPOSE_FILE" build --no-cache
    echo -e "${GREEN}✅ Web UI container built${NC}"
}

open_shell() {
    echo -e "${BLUE}🐚 Opening shell in Web UI container...${NC}"
    docker-compose -f "$COMPOSE_FILE" exec "$SERVICE_NAME" /bin/bash
}

clean_service() {
    echo -e "${YELLOW}⚠️  This will stop and remove all Web UI containers and volumes${NC}"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}🧹 Cleaning Web UI service...${NC}"
        docker-compose -f "$COMPOSE_FILE" down -v --remove-orphans
        echo -e "${GREEN}✅ Web UI service cleaned${NC}"
    else
        echo -e "${BLUE}Operation cancelled${NC}"
    fi
}

# Main script logic
check_requirements

case "${1:-}" in
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        restart_service
        ;;
    logs)
        show_logs "$2"
        ;;
    status)
        show_status
        ;;
    health)
        check_health
        ;;
    build)
        build_service
        ;;
    shell)
        open_shell
        ;;
    clean)
        clean_service
        ;;
    help|--help|-h)
        show_usage
        ;;
    "")
        show_usage
        ;;
    *)
        echo -e "${RED}❌ Unknown command: $1${NC}"
        echo ""
        show_usage
        exit 1
        ;;
esac