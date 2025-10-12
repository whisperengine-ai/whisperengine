#!/bin/bash
# WhisperEngine Docker Cleanup Script
# Removes all containers, volumes, and networks for a fresh start

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_step() {
    echo -e "${BLUE}🔧 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

echo ""
echo "🧹 WhisperEngine Docker Cleanup"
echo "================================"
echo "This will remove ALL WhisperEngine containers, volumes, and data"
echo ""

print_warning "This will DELETE:"
print_warning "  • All WhisperEngine containers"
print_warning "  • All database data (PostgreSQL)"
print_warning "  • All vector memory data (Qdrant)"
print_warning "  • All time-series data (InfluxDB)"
print_warning "  • All conversation logs"
print_warning ""
print_warning "You will need to reconfigure your LLM settings after cleanup!"
echo ""

read -p "Are you sure you want to continue? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Cleanup cancelled"
    exit 0
fi

echo ""
print_step "Stopping all WhisperEngine containers..."

# First, try to stop using any compose files we can find
compose_files=(
    "docker-compose.quickstart.yml"
    "docker-compose.containerized.yml"
    "docker-compose.yml"
)

for compose_file in "${compose_files[@]}"; do
    if [ -f "$compose_file" ]; then
        print_success "Stopping containers from $compose_file..."
        docker-compose -f "$compose_file" down 2>/dev/null || true
    fi
done

# Then stop any containers with whisperengine in the name
docker ps -aq --filter "name=whisperengine" | while read container; do
    if [ ! -z "$container" ]; then
        container_name=$(docker inspect --format '{{.Name}}' "$container" | sed 's/\///')
        docker stop "$container" 2>/dev/null || true
        docker rm "$container" 2>/dev/null || true
        print_success "Removed container: $container_name"
    fi
done

print_step "Removing WhisperEngine volumes..."

# First, get all volumes with whisperengine in the name
volumes_to_remove=$(docker volume ls --format "{{.Name}}" | grep -i whisperengine || true)

if [ ! -z "$volumes_to_remove" ]; then
    echo "$volumes_to_remove" | while read volume; do
        if [ ! -z "$volume" ]; then
            docker volume rm "$volume" 2>/dev/null || true
            print_success "Removed volume: $volume"
        fi
    done
else
    print_success "No WhisperEngine volumes found"
fi

# Also try common volume name patterns without prefix
for volume in postgres_data qdrant_data influxdb_data whisperengine_logs grafana_data; do
    if docker volume ls | grep -q "^${volume}$"; then
        docker volume rm "$volume" 2>/dev/null || true
        print_success "Removed volume: $volume"
    fi
done

print_step "Removing WhisperEngine networks..."

# Remove networks
for network in whisperengine-network whisperengine_default; do
    if docker network ls | grep -q "$network"; then
        docker network rm "$network" 2>/dev/null || true
        print_success "Removed network: $network"
    fi
done

print_step "Cleaning up dangling resources..."

# Remove dangling volumes
docker volume prune -f 2>/dev/null || true

echo ""
print_success "Cleanup complete! 🎉"
echo ""
echo "📋 Next steps:"
echo ""
echo "1. Run the quickstart setup again:"
echo "   ${BLUE}./quickstart-setup.sh${NC}"
echo ""
echo "2. Or if you already have the files, start fresh:"
echo "   ${BLUE}docker-compose -f docker-compose.quickstart.yml up -d${NC}"
echo ""
echo "💡 You'll need to reconfigure your LLM settings in .env"
echo ""
