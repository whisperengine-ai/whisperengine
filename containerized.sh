#!/bin/bash

# WhisperEngine Containerized Setup
# Runs the single-assistant containerized deployment
# Project: whisperengine-containerized (separate from multi-bot)
# Ports: 8000-8999 range (no conflicts with multi-bot)

set -e

PROJECT_NAME="whisperengine-containerized"
COMPOSE_FILE="docker-compose.containerized.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_banner() {
    echo -e "${BLUE}"
    echo "=================================================="
    echo "  WhisperEngine - Containerized Deployment"
    echo "  Project: ${PROJECT_NAME}"
    echo "  Single Assistant Mode"
    echo "=================================================="
    echo -e "${NC}"
}

print_usage() {
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  up, start         Start all services"
    echo "  down, stop        Stop all services"
    echo "  restart           Restart all services"
    echo "  logs              Show logs for all services"
    echo "  logs SERVICE      Show logs for specific service"
    echo "  ps, status        Show service status"
    echo "  pull              Pull latest images"
    echo "  health            Check health of all services"
    echo ""
    echo "Services:"
    echo "  whisperengine-assistant   Main AI assistant"
    echo "  cdl-web-ui               Character management UI"
    echo "  postgres                 Database"
    echo "  qdrant                   Vector database"
    echo "  influxdb                 Time-series database"
    echo ""
    echo "Access Points:"
    echo "  Assistant API:    http://localhost:8090"
    echo "  Web UI:          http://localhost:8001"
    echo "  InfluxDB UI:     http://localhost:8086"
    echo "  Database & Qdrant: Internal only (production security)"
}

run_command() {
    echo -e "${YELLOW}Running: docker compose -p ${PROJECT_NAME} -f ${COMPOSE_FILE} $*${NC}"
    docker compose -p "${PROJECT_NAME}" -f "${COMPOSE_FILE}" "$@"
}

case "${1:-}" in
    up|start)
        print_banner
        echo -e "${GREEN}Starting WhisperEngine Containerized...${NC}"
        run_command up -d
        echo ""
        echo -e "${GREEN}Services started! Access points:${NC}"
        echo "  Assistant API:    http://localhost:8090"
        echo "  Web UI:          http://localhost:8001"
        echo "  InfluxDB UI:     http://localhost:8086"
        echo ""
        echo -e "${BLUE}Check status with: $0 status${NC}"
        ;;
    down|stop)
        print_banner
        echo -e "${YELLOW}Stopping WhisperEngine Containerized...${NC}"
        run_command down
        ;;
    restart)
        print_banner
        echo -e "${YELLOW}Restarting WhisperEngine Containerized...${NC}"
        run_command restart
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
    health)
        print_banner
        echo -e "${BLUE}Checking service health...${NC}"
        echo ""
        
        # Check each service
        echo -e "${YELLOW}Assistant API (http://localhost:8090/health):${NC}"
        curl -s http://localhost:8090/health 2>/dev/null && echo -e "${GREEN}✓ Healthy${NC}" || echo -e "${RED}✗ Unhealthy${NC}"
        
        echo -e "${YELLOW}Web UI (http://localhost:8001):${NC}"
        curl -s http://localhost:8001 >/dev/null 2>&1 && echo -e "${GREEN}✓ Accessible${NC}" || echo -e "${RED}✗ Not accessible${NC}"
        
        echo -e "${YELLOW}InfluxDB (http://localhost:8086/health):${NC}"
        curl -s http://localhost:8086/health 2>/dev/null 2>&1 && echo -e "${GREEN}✓ Healthy${NC}" || echo -e "${RED}✗ Unhealthy${NC}"
        
        echo -e "${YELLOW}Database & Qdrant:${NC}"
        echo -e "${BLUE}ℹ️  Internal only (production security)${NC}"
        
        echo ""
        echo -e "${BLUE}Container status:${NC}"
        run_command ps
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