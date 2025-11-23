#!/bin/bash

# WhisperEngine Multi-Bot Development Environment
# Runs multiple character bots with full development features
# Project: whisperengine-multi (separate from containerized)
# Ports: 5000-5999, 9000-9999 range (no conflicts with containerized)

set -e

PROJECT_NAME="whisperengine-multi"
COMPOSE_FILE="docker-compose.multi-bot.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Available bots
AVAILABLE_BOTS=(
    "gabriel:9095:British Gentleman"
    "aetheris:9099:Conscious AI"
    "nottaylor:9100:Taylor Swift Parody"
    "aethys:3007:Omnipotent Entity"
)

print_banner() {
    echo -e "${BLUE}"
    echo "======================================================="
    echo "  WhisperEngine - Multi-Bot Development Environment"
    echo "  Project: ${PROJECT_NAME}"
    echo "  Character Development & Testing Platform"
    echo "======================================================="
    echo -e "${NC}"
}

print_usage() {
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Infrastructure Commands:"
    echo "  infra             Start infrastructure only (postgres, qdrant, influxdb, grafana)"
    echo "  enrichment        Start infrastructure + enrichment worker"
    echo "  up, start         Start all services (infra + enrichment + all bots)"
    echo "  down, stop        Stop all services"
    echo "  restart           Restart all services"
    echo "  clean             Stop and remove all containers, networks, and volumes"
    echo ""
    echo "Bot Management:"
    echo "  bot BOT_NAME      Start specific character bot"
    echo "  stop-bot BOT_NAME Stop specific character bot"
    echo "  bots              List available bots"
    echo "  status            Show service status"
    echo "  logs [SERVICE]    Show logs for all services or specific service"
    echo ""
    echo "Development Tools:"
    echo "  dev               Start development stack (infra + web UI)"
    echo "  db                Connect to PostgreSQL database"
    echo "  health            Check health of all services"
    echo "  pull              Pull latest images"
    echo "  build             Build bot images"
    echo ""
    echo "Available Character Bots:"
    for bot_info in "${AVAILABLE_BOTS[@]}"; do
        IFS=':' read -r name port desc <<< "$bot_info"
        printf "  %-12s %s (Port %s)\n" "$name" "$desc" "$port"
    done
    echo ""
    echo "Access Points:"
    echo "  PostgreSQL:       localhost:5433"
    echo "  Qdrant:          http://localhost:6334"
    echo "  InfluxDB:        http://localhost:8087"
    echo "  Grafana:         http://localhost:3002"
    echo "  CDL Web UI:      http://localhost:3001"
    echo "  Character APIs:   http://localhost:9091-9099, 3007"
}

run_command() {
    echo -e "${YELLOW}Running: docker compose -p ${PROJECT_NAME} -f ${COMPOSE_FILE} $*${NC}"
    docker compose -p "${PROJECT_NAME}" -f "${COMPOSE_FILE}" "$@"
}

start_infrastructure() {
    echo -e "${CYAN}Starting infrastructure services...${NC}"
    run_command up -d postgres qdrant influxdb grafana
    echo -e "${GREEN}Infrastructure started!${NC}"
    echo "  PostgreSQL:  localhost:5433"
    echo "  Qdrant:      http://localhost:6334"
    echo "  InfluxDB:    http://localhost:8087"
    echo "  Grafana:     http://localhost:3002"
}

start_enrichment() {
    echo -e "${CYAN}Starting infrastructure + enrichment worker...${NC}"
    start_infrastructure
    echo ""
    echo -e "${CYAN}Starting enrichment worker...${NC}"
    docker compose -p "${PROJECT_NAME}" -f "${COMPOSE_FILE}" --profile enrichment up -d enrichment-worker
    echo -e "${GREEN}Enrichment worker started!${NC}"
    echo "  Check logs: $0 logs enrichment-worker"
}

start_bot() {
    local bot_name="$1"
    local found=false
    
    for bot_info in "${AVAILABLE_BOTS[@]}"; do
        IFS=':' read -r name port desc <<< "$bot_info"
        if [[ "$name" == "$bot_name" ]]; then
            found=true
            echo -e "${PURPLE}Starting $desc ($name)...${NC}"
            
            # Check if the bot is already running
            if docker compose -p "${PROJECT_NAME}" -f "${COMPOSE_FILE}" ps "${name}-bot" | grep -q "Up"; then
                echo -e "${YELLOW}$desc is already running!${NC}"
            else
                # Use --no-deps to avoid affecting other services
                echo -e "${YELLOW}Running: docker compose -p ${PROJECT_NAME} -f ${COMPOSE_FILE} up -d --no-deps ${name}-bot${NC}"
                docker compose -p "${PROJECT_NAME}" -f "${COMPOSE_FILE}" up -d --no-deps "${name}-bot"
                if [ $? -eq 0 ]; then
                    echo -e "${GREEN}$desc started!${NC}"
                else
                    echo -e "${RED}Failed to start $desc. Check logs with: $0 logs ${name}-bot${NC}"
                    exit 1
                fi
            fi
            
            echo "  API: http://localhost:$port"
            echo "  Health: http://localhost:$port/health"
            break
        fi
    done
    
    if [[ "$found" == "false" ]]; then
        echo -e "${RED}Bot '$bot_name' not found. Available bots:${NC}"
        list_bots
        exit 1
    fi
}

stop_bot() {
    local bot_name="$1"
    local found=false
    
    for bot_info in "${AVAILABLE_BOTS[@]}"; do
        IFS=':' read -r name port desc <<< "$bot_info"
        if [[ "$name" == "$bot_name" ]]; then
            found=true
            echo -e "${PURPLE}Stopping $desc ($name)...${NC}"
            
            # Check if the bot is running
            if docker compose -p "${PROJECT_NAME}" -f "${COMPOSE_FILE}" ps "${name}-bot" | grep -q "Up"; then
                echo -e "${YELLOW}Running: docker compose -p ${PROJECT_NAME} -f ${COMPOSE_FILE} stop ${name}-bot${NC}"
                docker compose -p "${PROJECT_NAME}" -f "${COMPOSE_FILE}" stop "${name}-bot"
                if [ $? -eq 0 ]; then
                    echo -e "${GREEN}$desc stopped!${NC}"
                else
                    echo -e "${RED}Failed to stop $desc.${NC}"
                    exit 1
                fi
            else
                echo -e "${YELLOW}$desc is not running.${NC}"
            fi
            break
        fi
    done
    
    if [[ "$found" == "false" ]]; then
        echo -e "${RED}Bot '$bot_name' not found. Available bots:${NC}"
        list_bots
        exit 1
    fi
}

list_bots() {
    echo -e "${BLUE}Available Character Bots:${NC}"
    for bot_info in "${AVAILABLE_BOTS[@]}"; do
        IFS=':' read -r name port desc <<< "$bot_info"
        printf "  %-12s %s (Port %s)\n" "$name" "$desc" "$port"
    done
}

check_health() {
    echo -e "${BLUE}Checking service health...${NC}"
    echo ""
    
    # Infrastructure
    echo -e "${CYAN}Infrastructure:${NC}"
    echo -e "${YELLOW}PostgreSQL (localhost:5433):${NC}"
    if pg_isready -h localhost -p 5433 -U whisperengine >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Healthy${NC}"
    else
        echo -e "${RED}✗ Unhealthy${NC}"
    fi
    
    echo -e "${YELLOW}Qdrant (http://localhost:6334):${NC}"
    curl -s http://localhost:6334 >/dev/null 2>&1 && echo -e "${GREEN}✓ Accessible${NC}" || echo -e "${RED}✗ Not accessible${NC}"
    
    echo -e "${YELLOW}InfluxDB (http://localhost:8087):${NC}"
    curl -s http://localhost:8087/health 2>/dev/null && echo -e "${GREEN}✓ Healthy${NC}" || echo -e "${RED}✗ Unhealthy${NC}"
    
    echo -e "${YELLOW}Grafana (http://localhost:3002):${NC}"
    curl -s http://localhost:3002 >/dev/null 2>&1 && echo -e "${GREEN}✓ Accessible${NC}" || echo -e "${RED}✗ Not accessible${NC}"
    
    echo -e "${YELLOW}CDL Web UI (http://localhost:3001):${NC}"
    curl -s http://localhost:3001 >/dev/null 2>&1 && echo -e "${GREEN}✓ Accessible${NC}" || echo -e "${RED}✗ Not accessible${NC}"
    
    # Character Bots
    echo ""
    echo -e "${CYAN}Character Bots:${NC}"
    for bot_info in "${AVAILABLE_BOTS[@]}"; do
        IFS=':' read -r name port desc <<< "$bot_info"
        echo -e "${YELLOW}$desc (http://localhost:$port/health):${NC}"
        if curl -s http://localhost:$port/health >/dev/null 2>&1; then
            echo -e "${GREEN}✓ Healthy${NC}"
        else
            echo -e "${RED}✗ Not running${NC}"
        fi
    done
    
    echo ""
    echo -e "${BLUE}Container status:${NC}"
    run_command ps
}

connect_db() {
    echo -e "${CYAN}Connecting to PostgreSQL database...${NC}"
    echo "Connection details:"
    echo "  Host: localhost"
    echo "  Port: 5433"
    echo "  Database: whisperengine"
    echo "  User: whisperengine"
    echo ""
    PGPASSWORD=whisperengine_password psql -h localhost -p 5433 -U whisperengine -d whisperengine
}

case "${1:-}" in
    infra)
        print_banner
        start_infrastructure
        ;;
    enrichment)
        print_banner
        start_enrichment
        ;;
    up|start)
        print_banner
        echo -e "${GREEN}Starting WhisperEngine Multi-Bot Development Environment...${NC}"
        echo -e "${YELLOW}Note: Starting with enrichment worker enabled${NC}"
        docker compose -p "${PROJECT_NAME}" -f "${COMPOSE_FILE}" --profile enrichment up -d
        echo ""
        echo -e "${GREEN}Services started! Access points:${NC}"
        echo "  PostgreSQL:  localhost:5433"
        echo "  Qdrant:      http://localhost:6334"
        echo "  InfluxDB:    http://localhost:8087"
        echo "  Grafana:     http://localhost:3002"
        echo "  CDL Web UI:  http://localhost:3001"
        echo ""
        echo -e "${BLUE}Check individual bot status with: $0 status${NC}"
        echo -e "${BLUE}Start specific bots with: $0 bot BOT_NAME${NC}"
        ;;
    down|stop)
        print_banner
        echo -e "${YELLOW}Stopping WhisperEngine Multi-Bot Environment...${NC}"
        run_command down
        ;;
    clean)
        print_banner
        echo -e "${RED}Cleaning WhisperEngine Multi-Bot Environment...${NC}"
        echo -e "${YELLOW}This will remove all containers, networks, and volumes!${NC}"
        read -p "Are you sure? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            run_command down -v
            echo -e "${GREEN}Environment cleaned!${NC}"
        else
            echo -e "${BLUE}Cancelled.${NC}"
        fi
        ;;
    restart)
        print_banner
        echo -e "${YELLOW}Restarting WhisperEngine Multi-Bot Environment...${NC}"
        run_command restart
        ;;
    bot)
        if [[ -z "${2:-}" ]]; then
            echo -e "${RED}Please specify a bot name.${NC}"
            list_bots
            exit 1
        fi
        print_banner
        start_bot "$2"
        ;;
    stop-bot)
        if [[ -z "${2:-}" ]]; then
            echo -e "${RED}Please specify a bot name.${NC}"
            list_bots
            exit 1
        fi
        print_banner
        stop_bot "$2"
        ;;
    bots)
        list_bots
        ;;
    dev)
        print_banner
        echo -e "${CYAN}Starting development stack...${NC}"
        start_infrastructure
        echo ""
        echo -e "${CYAN}Starting CDL Web UI...${NC}"
        run_command up -d whisperengine-multi-cdl-web-ui
        echo -e "${GREEN}Development stack ready!${NC}"
        echo "  CDL Web UI:  http://localhost:3001"
        ;;
    logs)
        if [[ -n "${2:-}" ]]; then
            run_command logs -f "$2"
        else
            run_command logs -f
        fi
        ;;
    ps|status)
        run_command ps
        ;;
    pull)
        print_banner
        echo -e "${BLUE}Pulling latest images...${NC}"
        run_command pull
        ;;
    build)
        print_banner
        echo -e "${BLUE}Building bot images...${NC}"
        run_command build
        ;;
    db)
        connect_db
        ;;
    health)
        print_banner
        check_health
        ;;
    ""|help|--help|-h)
        print_usage
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        echo ""
        print_usage
        exit 1
        ;;
esac