#!/bin/bash

# WhisperEngine InfluxDB/Grafana Monitoring Setup Script
# Comprehensive character intelligence monitoring deployment

set -e

echo "🎯 WhisperEngine Character Intelligence Monitoring Setup"
echo "========================================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MONITORING_ENV_FILE=".env.monitoring"
GRAFANA_PORT="3000"
INFLUXDB_PORT="8086"

# Create monitoring environment file if it doesn't exist
create_monitoring_env() {
    if [ ! -f "$MONITORING_ENV_FILE" ]; then
        echo -e "${YELLOW}Creating monitoring environment configuration...${NC}"
        cat > "$MONITORING_ENV_FILE" << EOF
# WhisperEngine Monitoring Configuration
INFLUXDB_USER=admin
INFLUXDB_PASSWORD=whisperengine_metrics_$(date +%s)
INFLUXDB_ORG=whisperengine
INFLUXDB_BUCKET=temporal_intelligence
INFLUXDB_TOKEN=whisperengine_admin_token_$(date +%s)

GRAFANA_USER=admin
GRAFANA_PASSWORD=whisperengine_grafana_$(date +%s)

# PostgreSQL (existing)
POSTGRES_DB=whisperengine
POSTGRES_USER=whisperengine_user
POSTGRES_PASSWORD=your_secure_password_$(date +%s)
EOF
        echo -e "${GREEN}✅ Created $MONITORING_ENV_FILE${NC}"
    else
        echo -e "${BLUE}ℹ️  Using existing $MONITORING_ENV_FILE${NC}"
    fi
}

# Generate dashboard JSON files
generate_dashboards() {
    echo -e "${YELLOW}Generating Grafana dashboard configurations...${NC}"
    
    # Create dashboards directory
    mkdir -p dashboards
    
    # Generate dashboards using Python script
    python3 create_influxdb_dashboards.py
    
    echo -e "${GREEN}✅ Dashboard configurations generated in dashboards/${NC}"
}

# Setup monitoring stack
setup_monitoring_stack() {
    echo -e "${YELLOW}Setting up InfluxDB + Grafana monitoring stack...${NC}"
    
    # Load environment variables
    if [ -f "$MONITORING_ENV_FILE" ]; then
        export $(cat "$MONITORING_ENV_FILE" | grep -v '^#' | xargs)
    fi
    
    # Stop existing monitoring containers
    echo "Stopping existing monitoring containers..."
    docker-compose -f docker-compose.monitoring.yml down grafana influxdb 2>/dev/null || true
    
    # Start monitoring infrastructure
    echo "Starting InfluxDB..."
    docker-compose -f docker-compose.monitoring.yml up -d influxdb
    
    # Wait for InfluxDB to be ready
    echo "Waiting for InfluxDB to be ready..."
    timeout=60
    while [ $timeout -gt 0 ]; do
        if docker exec whisperengine-influxdb curl -f http://localhost:8086/ping >/dev/null 2>&1; then
            echo -e "${GREEN}✅ InfluxDB is ready${NC}"
            break
        fi
        sleep 2
        ((timeout-=2))
    done
    
    if [ $timeout -le 0 ]; then
        echo -e "${RED}❌ InfluxDB failed to start within 60 seconds${NC}"
        exit 1
    fi
    
    # Start Grafana
    echo "Starting Grafana..."
    docker-compose -f docker-compose.monitoring.yml up -d grafana
    
    # Wait for Grafana to be ready
    echo "Waiting for Grafana to be ready..."
    timeout=60
    while [ $timeout -gt 0 ]; do
        if curl -f http://localhost:${GRAFANA_PORT}/api/health >/dev/null 2>&1; then
            echo -e "${GREEN}✅ Grafana is ready${NC}"
            break
        fi
        sleep 2
        ((timeout-=2))
    done
    
    if [ $timeout -le 0 ]; then
        echo -e "${RED}❌ Grafana failed to start within 60 seconds${NC}"
        exit 1
    fi
}

# Import dashboards to Grafana
import_dashboards() {
    echo -e "${YELLOW}Importing dashboards to Grafana...${NC}"
    
    # Load environment variables
    if [ -f "$MONITORING_ENV_FILE" ]; then
        export $(cat "$MONITORING_ENV_FILE" | grep -v '^#' | xargs)
    fi
    
    GRAFANA_URL="http://localhost:${GRAFANA_PORT}"
    
    # Wait for Grafana API to be available
    echo "Verifying Grafana API availability..."
    for i in {1..30}; do
        if curl -s -o /dev/null -w "%{http_code}" "$GRAFANA_URL/api/health" | grep -q "200"; then
            echo -e "${GREEN}✅ Grafana API is available${NC}"
            break
        fi
        echo "Waiting for Grafana API... ($i/30)"
        sleep 2
    done
    
    # Import each dashboard
    for dashboard_file in dashboards/whisperengine_*.json; do
        if [ -f "$dashboard_file" ]; then
            dashboard_name=$(basename "$dashboard_file" .json)
            echo "Importing $dashboard_name..."
            
            # Import dashboard via Grafana API
            response=$(curl -s -X POST \
                -H "Content-Type: application/json" \
                -u "$GRAFANA_USER:$GRAFANA_PASSWORD" \
                -d @"$dashboard_file" \
                "$GRAFANA_URL/api/dashboards/db")
            
            if echo "$response" | grep -q '"status":"success"'; then
                echo -e "${GREEN}✅ Imported $dashboard_name${NC}"
            else
                echo -e "${YELLOW}⚠️  Dashboard $dashboard_name may already exist or failed to import${NC}"
                echo "Response: $response"
            fi
        fi
    done
}

# Start character bots with monitoring
start_monitored_bots() {
    echo -e "${YELLOW}Starting WhisperEngine character bots with monitoring...${NC}"
    
    # Load environment variables
    if [ -f "$MONITORING_ENV_FILE" ]; then
        export $(cat "$MONITORING_ENV_FILE" | grep -v '^#' | xargs)
    fi
    
    # Start core infrastructure first
    docker-compose -f docker-compose.monitoring.yml up -d postgres qdrant influxdb grafana
    
    # Start character bots
    if [ -f ".env.elena" ]; then
        echo "Starting Elena bot..."
        docker-compose -f docker-compose.monitoring.yml up -d elena-bot
    fi
    
    if [ -f ".env.gabriel" ]; then
        echo "Starting Gabriel bot..."
        docker-compose -f docker-compose.monitoring.yml up -d gabriel-bot
    fi
    
    if [ -f ".env.sophia" ]; then
        echo "Starting Sophia bot..."
        docker-compose -f docker-compose.monitoring.yml up -d sophia-bot
    fi
    
    echo -e "${GREEN}✅ Character bots started with monitoring enabled${NC}"
}

# Display monitoring information
show_monitoring_info() {
    echo -e "${BLUE}"
    echo "🎯 WhisperEngine Character Intelligence Monitoring"
    echo "=================================================="
    echo ""
    echo "📊 Grafana Dashboard: http://localhost:${GRAFANA_PORT}"
    echo "📈 InfluxDB Web UI: http://localhost:${INFLUXDB_PORT}"
    echo ""
    echo "🔐 Login Credentials:"
    echo "   Grafana: admin / $(grep GRAFANA_PASSWORD $MONITORING_ENV_FILE | cut -d'=' -f2)"
    echo "   InfluxDB: admin / $(grep INFLUXDB_PASSWORD $MONITORING_ENV_FILE | cut -d'=' -f2)"
    echo ""
    echo "📈 Available Dashboards:"
    echo "   • Character Performance Overview"
    echo "   • Emotion Analysis Intelligence" 
    echo "   • Vector Memory Performance"
    echo "   • System Health & Optimization"
    echo ""
    echo "🤖 Character Bot Health Checks:"
    if docker ps | grep -q "whisperengine-elena-bot"; then
        echo "   • Elena (Marine Biologist): http://localhost:9091/health"
    fi
    if docker ps | grep -q "whisperengine-gabriel-bot"; then
        echo "   • Gabriel (British Gentleman): http://localhost:9095/health" 
    fi
    if docker ps | grep -q "whisperengine-sophia-bot"; then
        echo "   • Sophia (Marketing Executive): http://localhost:9096/health"
    fi
    echo ""
    echo "🔧 Management Commands:"
    echo "   docker-compose -f docker-compose.monitoring.yml logs grafana"
    echo "   docker-compose -f docker-compose.monitoring.yml logs influxdb"
    echo "   docker-compose -f docker-compose.monitoring.yml ps"
    echo -e "${NC}"
}

# Main execution
main() {
    case "${1:-setup}" in
        "setup")
            create_monitoring_env
            generate_dashboards
            setup_monitoring_stack
            import_dashboards
            start_monitored_bots
            show_monitoring_info
            ;;
        "dashboards-only")
            generate_dashboards
            import_dashboards
            ;;
        "monitoring-only")
            setup_monitoring_stack
            ;;
        "start")
            start_monitored_bots
            ;;
        "stop")
            echo "Stopping monitoring stack..."
            docker-compose -f docker-compose.monitoring.yml down
            ;;
        "status")
            docker-compose -f docker-compose.monitoring.yml ps
            ;;
        "info")
            show_monitoring_info
            ;;
        "logs")
            docker-compose -f docker-compose.monitoring.yml logs -f "${2:-grafana}"
            ;;
        *)
            echo "Usage: $0 {setup|dashboards-only|monitoring-only|start|stop|status|info|logs [service]}"
            echo ""
            echo "Commands:"
            echo "  setup          - Complete monitoring stack setup (default)"
            echo "  dashboards-only - Generate and import dashboards only"
            echo "  monitoring-only - Setup InfluxDB + Grafana only"
            echo "  start          - Start character bots with monitoring"
            echo "  stop           - Stop monitoring stack"
            echo "  status         - Show container status"
            echo "  info           - Show monitoring information"
            echo "  logs [service] - Show logs for service (default: grafana)"
            exit 1
            ;;
    esac
}

main "$@"