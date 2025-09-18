#!/bin/bash

# WhisperEngine Docker Volume Management Script
# Provides safe operations for managing Docker volumes

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="whisperengine"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to list all WhisperEngine volumes
list_volumes() {
    log_info "Listing all WhisperEngine Docker volumes..."
    echo
    docker volume ls --filter name=${PROJECT_NAME} --format "table {{.Name}}\t{{.Driver}}\t{{.Scope}}"
}

# Function to show volume usage
show_volume_usage() {
    log_info "Showing volume disk usage..."
    echo
    
    for volume in $(docker volume ls --filter name=${PROJECT_NAME} --format "{{.Name}}"); do
        size=$(docker run --rm -v ${volume}:/data alpine du -sh /data | cut -f1)
        echo -e "${BLUE}${volume}:${NC} ${size}"
    done
}

# Function to backup volumes
backup_volume() {
    local volume_name=$1
    local backup_dir=${2:-"./backups/volumes"}
    
    if [ -z "$volume_name" ]; then
        log_error "Volume name required"
        echo "Usage: $0 backup <volume_name> [backup_dir]"
        exit 1
    fi
    
    # Check if volume exists
    if ! docker volume inspect "$volume_name" >/dev/null 2>&1; then
        log_error "Volume '$volume_name' does not exist"
        exit 1
    fi
    
    # Create backup directory
    mkdir -p "$backup_dir"
    
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_file="${backup_dir}/${volume_name}_${timestamp}.tar.gz"
    
    log_info "Backing up volume '$volume_name' to '$backup_file'..."
    
    docker run --rm \
        -v "${volume_name}:/data:ro" \
        -v "$(realpath "$backup_dir"):/backup" \
        alpine \
        tar czf "/backup/$(basename "$backup_file")" -C /data .
    
    log_success "Backup completed: $backup_file"
}

# Function to restore volumes
restore_volume() {
    local volume_name=$1
    local backup_file=$2
    
    if [ -z "$volume_name" ] || [ -z "$backup_file" ]; then
        log_error "Volume name and backup file required"
        echo "Usage: $0 restore <volume_name> <backup_file>"
        exit 1
    fi
    
    if [ ! -f "$backup_file" ]; then
        log_error "Backup file '$backup_file' does not exist"
        exit 1
    fi
    
    log_warning "This will OVERWRITE all data in volume '$volume_name'"
    read -p "Are you sure? (y/N): " -r
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Restore cancelled"
        exit 0
    fi
    
    # Create volume if it doesn't exist
    docker volume create "$volume_name" >/dev/null 2>&1 || true
    
    log_info "Restoring volume '$volume_name' from '$backup_file'..."
    
    docker run --rm \
        -v "${volume_name}:/data" \
        -v "$(realpath "$(dirname "$backup_file")"):/backup:ro" \
        alpine \
        sh -c "cd /data && rm -rf ./* && tar xzf /backup/$(basename "$backup_file")"
    
    log_success "Restore completed for volume '$volume_name'"
}

# Function to clean unused volumes
clean_volumes() {
    log_warning "This will remove ALL unused Docker volumes (not just WhisperEngine)"
    read -p "Are you sure? (y/N): " -r
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Clean cancelled"
        exit 0
    fi
    
    log_info "Removing unused volumes..."
    docker volume prune -f
    log_success "Unused volumes removed"
}

# Function to migrate from old volume structure
migrate_old_volumes() {
    log_info "Checking for old volume structure..."
    
    # Check if old bot_data volume exists
    if docker volume inspect "${PROJECT_NAME}-data" >/dev/null 2>&1; then
        log_warning "Found old 'whisperengine-data' volume"
        log_info "This volume is no longer used due to architecture improvements"
        echo
        echo "The bot container no longer mounts ChromaDB data directly."
        echo "ChromaDB manages its own persistent storage separately."
        echo
        read -p "Remove the old 'whisperengine-data' volume? (y/N): " -r
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker volume rm "${PROJECT_NAME}-data"
            log_success "Old volume removed"
        else
            log_info "Old volume kept (you can remove it manually later)"
        fi
    else
        log_success "No old volumes found - migration not needed"
    fi
}

# Function to check volume health
check_volume_health() {
    log_info "Checking volume health and accessibility..."
    echo
    
    for volume in $(docker volume ls --filter name=${PROJECT_NAME} --format "{{.Name}}"); do
        echo -n "Checking ${volume}... "
        if docker run --rm -v ${volume}:/test alpine test -d /test >/dev/null 2>&1; then
            echo -e "${GREEN}OK${NC}"
        else
            echo -e "${RED}FAILED${NC}"
        fi
    done
}

# Show help
show_help() {
    echo "WhisperEngine Docker Volume Management"
    echo
    echo "Usage: $0 <command> [options]"
    echo
    echo "Commands:"
    echo "  list                    List all WhisperEngine volumes"
    echo "  usage                   Show volume disk usage"
    echo "  backup <volume> [dir]   Backup a volume to compressed file"
    echo "  restore <volume> <file> Restore a volume from backup file"
    echo "  clean                   Remove unused volumes (CAREFUL!)"
    echo "  migrate                 Migrate from old volume structure"
    echo "  health                  Check volume health and accessibility"
    echo "  help                    Show this help message"
    echo
    echo "Examples:"
    echo "  $0 list"
    echo "  $0 backup whisperengine-postgres"
    echo "  $0 restore whisperengine-postgres ./backups/volumes/whisperengine-postgres_20240101_120000.tar.gz"
    echo "  $0 usage"
}

# Main script logic
case "${1:-help}" in
    list)
        list_volumes
        ;;
    usage)
        show_volume_usage
        ;;
    backup)
        backup_volume "$2" "$3"
        ;;
    restore)
        restore_volume "$2" "$3"
        ;;
    clean)
        clean_volumes
        ;;
    migrate)
        migrate_old_volumes
        ;;
    health)
        check_volume_health
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        log_error "Unknown command: $1"
        echo
        show_help
        exit 1
        ;;
esac