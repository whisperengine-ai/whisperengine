#!/bin/bash
# =============================================================================
# WhisperEngine Data Backup Script
# =============================================================================
# Simple backup solution for all 4 datastores:
# - PostgreSQL (user profiles and persistent data)
# - Redis (conversation cache and session state)
# - ChromaDB (vector embeddings and semantic memory)
# - Neo4j (graph database for relationships)
# =============================================================================

set -euo pipefail
IFS=$'\n\t'

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Helper functions
print_status() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }

# Configuration
BACKUP_BASE_DIR="${BACKUP_DIR:-./backups}"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
BACKUP_DIR="$BACKUP_BASE_DIR/whisperengine_backup_$TIMESTAMP"

# Docker compose command detection
detect_compose_cmd() {
    if command -v docker-compose &> /dev/null; then
        echo "docker-compose"
    elif docker compose version &> /dev/null; then
        echo "docker compose"
    else
        print_error "Docker Compose not found"
        exit 1
    fi
}

COMPOSE_CMD=$(detect_compose_cmd)

# Check if containers are running
check_containers() {
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running"
        exit 1
    fi
    
    local running_containers=0
    for service in postgres redis chromadb neo4j; do
        if $COMPOSE_CMD ps -q "$service" 2>/dev/null | grep -q .; then
            ((running_containers++))
        fi
    done
    
    if [[ $running_containers -eq 0 ]]; then
        print_error "No WhisperEngine containers are running"
        echo "Start the services first with: ./multi-bot.sh start all"
        exit 1
    fi
    
    if [[ $running_containers -lt 4 ]]; then
        print_warning "Only $running_containers/4 services are running"
        echo "Some backups may fail. Consider starting all services with: ./multi-bot.sh start all"
    fi
}

# Create backup directory
create_backup_dir() {
    mkdir -p "$BACKUP_DIR"
    print_status "Created backup directory: $BACKUP_DIR"
}

# Backup PostgreSQL
backup_postgresql() {
    print_info "Backing up PostgreSQL database..."
    
    if ! $COMPOSE_CMD ps -q postgres 2>/dev/null | grep -q .; then
        print_warning "PostgreSQL container not running, skipping..."
        return 0
    fi
    
    local postgres_backup="$BACKUP_DIR/postgresql_backup.sql"
    
    # Create PostgreSQL backup with proper error handling
    if $COMPOSE_CMD exec -T postgres pg_dumpall -U whisperengine > "$postgres_backup" 2>/dev/null; then
        local backup_size=$(du -h "$postgres_backup" | cut -f1)
        print_status "PostgreSQL backup completed: $backup_size"
    else
        print_error "PostgreSQL backup failed"
        rm -f "$postgres_backup"
        return 1
    fi
}

# Backup Redis
backup_redis() {
    print_info "Backing up Redis data..."
    
    if ! $COMPOSE_CMD ps -q redis 2>/dev/null | grep -q .; then
        print_warning "Redis container not running, skipping..."
        return 0
    fi
    
    local redis_backup="$BACKUP_DIR/redis_backup.rdb"
    
    # Trigger Redis save and copy the RDB file
    if $COMPOSE_CMD exec -T redis redis-cli BGSAVE >/dev/null 2>&1; then
        # Wait for background save to complete
        local max_wait=30
        local wait_count=0
        while [[ $wait_count -lt $max_wait ]]; do
            if $COMPOSE_CMD exec -T redis redis-cli LASTSAVE 2>/dev/null | grep -q "[0-9]"; then
                break
            fi
            sleep 1
            ((wait_count++))
        done
        
        # Copy the RDB file
        if $COMPOSE_CMD exec -T redis cat /data/dump.rdb > "$redis_backup" 2>/dev/null; then
            local backup_size=$(du -h "$redis_backup" | cut -f1)
            print_status "Redis backup completed: $backup_size"
        else
            print_error "Redis backup failed"
            rm -f "$redis_backup"
            return 1
        fi
    else
        print_error "Redis BGSAVE command failed"
        return 1
    fi
}

# Backup ChromaDB
backup_chromadb() {
    print_info "Backing up ChromaDB data..."
    
    if ! $COMPOSE_CMD ps -q chromadb 2>/dev/null | grep -q .; then
        print_warning "ChromaDB container not running, skipping..."
        return 0
    fi
    
    local chromadb_backup="$BACKUP_DIR/chromadb_backup.tar.gz"
    
    # Create tar archive of ChromaDB data directory
    if $COMPOSE_CMD exec -T chromadb tar czf - /chroma/chroma 2>/dev/null > "$chromadb_backup"; then
        local backup_size=$(du -h "$chromadb_backup" | cut -f1)
        print_status "ChromaDB backup completed: $backup_size"
    else
        print_error "ChromaDB backup failed"
        rm -f "$chromadb_backup"
        return 1
    fi
}

# Backup Neo4j
backup_neo4j() {
    print_info "Backing up Neo4j database..."
    
    if ! $COMPOSE_CMD ps -q neo4j 2>/dev/null | grep -q .; then
        print_warning "Neo4j container not running, skipping..."
        return 0
    fi
    
    local neo4j_backup="$BACKUP_DIR/neo4j_backup.tar.gz"
    
    # Create tar archive of Neo4j data directory
    if $COMPOSE_CMD exec -T neo4j tar czf - /data 2>/dev/null > "$neo4j_backup"; then
        local backup_size=$(du -h "$neo4j_backup" | cut -f1)
        print_status "Neo4j backup completed: $backup_size"
    else
        print_error "Neo4j backup failed"
        rm -f "$neo4j_backup"
        return 1
    fi
}

# Create backup metadata
create_backup_metadata() {
    local metadata_file="$BACKUP_DIR/backup_info.txt"
    
    cat > "$metadata_file" << EOF
WhisperEngine Backup Information
================================
Backup Date: $(date)
Backup Directory: $BACKUP_DIR
Backup Type: Full System Backup

Services Backed Up:
EOF

    # Check which services were backed up
    for service in postgresql redis chromadb neo4j; do
        local backup_file=""
        case $service in
            postgresql) backup_file="postgresql_backup.sql" ;;
            redis) backup_file="redis_backup.rdb" ;;
            chromadb) backup_file="chromadb_backup.tar.gz" ;;
            neo4j) backup_file="neo4j_backup.tar.gz" ;;
        esac
        
        if [[ -f "$BACKUP_DIR/$backup_file" ]]; then
            local file_size=$(du -h "$BACKUP_DIR/$backup_file" | cut -f1)
            echo "✅ $service: $backup_file ($file_size)" >> "$metadata_file"
        else
            echo "❌ $service: FAILED" >> "$metadata_file"
        fi
    done
    
    echo "" >> "$metadata_file"
    echo "Docker Container Status at Backup Time:" >> "$metadata_file"
    $COMPOSE_CMD ps >> "$metadata_file" 2>/dev/null || echo "Could not get container status" >> "$metadata_file"
    
    print_status "Backup metadata created: backup_info.txt"
}

# Show backup summary
show_backup_summary() {
    echo ""
    echo "📊 Backup Summary"
    echo "================="
    echo "📁 Backup Location: $BACKUP_DIR"
    echo "📅 Timestamp: $TIMESTAMP"
    echo ""
    
    local total_size=$(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1 || echo "Unknown")
    echo "💾 Total Backup Size: $total_size"
    echo ""
    
    echo "📋 Files Created:"
    if [[ -d "$BACKUP_DIR" ]]; then
        for file in "$BACKUP_DIR"/*; do
            if [[ -f "$file" ]]; then
                local filename=$(basename "$file")
                local filesize=$(du -h "$file" | cut -f1)
                echo "   • $filename ($filesize)"
            fi
        done
    fi
    
    echo ""
    echo "🔄 To restore from this backup:"
    echo "   ./multi-bot.sh backup restore $TIMESTAMP"
    echo ""
    echo "📁 To browse backup contents:"
    echo "   ls -la $BACKUP_DIR/"
}

# Restore functions
restore_postgresql() {
    local backup_file="$1/postgresql_backup.sql"
    
    if [[ ! -f "$backup_file" ]]; then
        print_warning "PostgreSQL backup file not found, skipping..."
        return 0
    fi
    
    print_info "Restoring PostgreSQL database..."
    
    if ! $COMPOSE_CMD ps -q postgres 2>/dev/null | grep -q .; then
        print_error "PostgreSQL container not running"
        echo "Start the services first with: ./multi-bot.sh start all"
        return 1
    fi
    
    # Drop existing connections and restore
    if $COMPOSE_CMD exec -T postgres psql -U whisperengine -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'whisperengine' AND pid <> pg_backend_pid();" >/dev/null 2>&1; then
        if $COMPOSE_CMD exec -T postgres psql -U whisperengine < "$backup_file" >/dev/null 2>&1; then
            print_status "PostgreSQL database restored successfully"
        else
            print_error "PostgreSQL restore failed"
            return 1
        fi
    else
        print_error "Could not prepare PostgreSQL for restore"
        return 1
    fi
}

restore_redis() {
    local backup_file="$1/redis_backup.rdb"
    
    if [[ ! -f "$backup_file" ]]; then
        print_warning "Redis backup file not found, skipping..."
        return 0
    fi
    
    print_info "Restoring Redis data..."
    
    if ! $COMPOSE_CMD ps -q redis 2>/dev/null | grep -q .; then
        print_error "Redis container not running"
        echo "Start the services first with: ./multi-bot.sh start all"
        return 1
    fi
    
    # Stop Redis, replace RDB file, start Redis
    print_info "Stopping Redis to restore data..."
    if $COMPOSE_CMD exec -T redis redis-cli SHUTDOWN NOSAVE >/dev/null 2>&1; then
        sleep 2
        
        # Copy backup file to Redis container
        if cat "$backup_file" | $COMPOSE_CMD exec -T redis tee /data/dump.rdb >/dev/null 2>&1; then
            # Restart Redis container to load the new data
            $COMPOSE_CMD restart redis >/dev/null 2>&1
            
            # Wait for Redis to be ready
            local max_wait=30
            local wait_count=0
            while [[ $wait_count -lt $max_wait ]]; do
                if $COMPOSE_CMD exec -T redis redis-cli ping 2>/dev/null | grep -q "PONG"; then
                    print_status "Redis data restored successfully"
                    return 0
                fi
                sleep 1
                ((wait_count++))
            done
            
            print_error "Redis failed to start after restore"
            return 1
        else
            print_error "Failed to copy Redis backup file"
            return 1
        fi
    else
        print_error "Could not stop Redis for restore"
        return 1
    fi
}

restore_chromadb() {
    local backup_file="$1/chromadb_backup.tar.gz"
    
    if [[ ! -f "$backup_file" ]]; then
        print_warning "ChromaDB backup file not found, skipping..."
        return 0
    fi
    
    print_info "Restoring ChromaDB data..."
    
    if ! $COMPOSE_CMD ps -q chromadb 2>/dev/null | grep -q .; then
        print_error "ChromaDB container not running"
        echo "Start the services first with: ./multi-bot.sh start all"
        return 1
    fi
    
    # Stop ChromaDB, restore data, restart
    print_info "Stopping ChromaDB to restore data..."
    $COMPOSE_CMD stop chromadb >/dev/null 2>&1
    
    # Remove existing data and restore from backup
    if $COMPOSE_CMD exec -T chromadb sh -c "rm -rf /chroma/chroma/*" 2>/dev/null && \
       cat "$backup_file" | $COMPOSE_CMD exec -T chromadb tar xzf - -C / 2>/dev/null; then
        
        # Restart ChromaDB
        $COMPOSE_CMD start chromadb >/dev/null 2>&1
        
        # Wait for ChromaDB to be ready
        local max_wait=30
        local wait_count=0
        while [[ $wait_count -lt $max_wait ]]; do
            if curl -s http://localhost:8000/api/v1/heartbeat >/dev/null 2>&1; then
                print_status "ChromaDB data restored successfully"
                return 0
            fi
            sleep 1
            ((wait_count++))
        done
        
        print_error "ChromaDB failed to start after restore"
        return 1
    else
        print_error "Failed to restore ChromaDB data"
        $COMPOSE_CMD start chromadb >/dev/null 2>&1  # Try to restart anyway
        return 1
    fi
}

restore_neo4j() {
    local backup_file="$1/neo4j_backup.tar.gz"
    
    if [[ ! -f "$backup_file" ]]; then
        print_warning "Neo4j backup file not found, skipping..."
        return 0
    fi
    
    print_info "Restoring Neo4j database..."
    
    if ! $COMPOSE_CMD ps -q neo4j 2>/dev/null | grep -q .; then
        print_error "Neo4j container not running"
        echo "Start the services first with: ./multi-bot.sh start all"
        return 1
    fi
    
    # Stop Neo4j, restore data, restart
    print_info "Stopping Neo4j to restore data..."
    $COMPOSE_CMD stop neo4j >/dev/null 2>&1
    
    # Remove existing data and restore from backup
    if $COMPOSE_CMD exec -T neo4j sh -c "rm -rf /data/*" 2>/dev/null && \
       cat "$backup_file" | $COMPOSE_CMD exec -T neo4j tar xzf - -C / 2>/dev/null; then
        
        # Restart Neo4j
        $COMPOSE_CMD start neo4j >/dev/null 2>&1
        
        # Wait for Neo4j to be ready (takes longer than other services)
        local max_wait=60
        local wait_count=0
        while [[ $wait_count -lt $max_wait ]]; do
            if curl -s http://localhost:7474 >/dev/null 2>&1; then
                print_status "Neo4j database restored successfully"
                return 0
            fi
            sleep 2
            ((wait_count++))
        done
        
        print_error "Neo4j failed to start after restore"
        return 1
    else
        print_error "Failed to restore Neo4j data"
        $COMPOSE_CMD start neo4j >/dev/null 2>&1  # Try to restart anyway
        return 1
    fi
}

# Main restore function
perform_restore() {
    local restore_timestamp="$1"
    local restore_dir="$BACKUP_BASE_DIR/whisperengine_backup_$restore_timestamp"
    
    echo "🔄 WhisperEngine Data Restore"
    echo "============================="
    echo ""
    
    # Validate backup exists
    if [[ ! -d "$restore_dir" ]]; then
        print_error "Backup not found: $restore_dir"
        echo "Available backups:"
        list_backups
        exit 1
    fi
    
    # Show backup information
    if [[ -f "$restore_dir/backup_info.txt" ]]; then
        echo "📋 Backup Information:"
        echo "======================"
        head -10 "$restore_dir/backup_info.txt"
        echo ""
    fi
    
    # Confirmation prompt
    echo "⚠️  WARNING: This will replace all current data!"
    echo "📁 Restoring from: $restore_dir"
    echo ""
    read -p "Are you sure you want to continue? (yes/no): " -r
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        print_warning "Restore cancelled by user"
        exit 0
    fi
    
    check_containers
    
    echo ""
    print_info "Starting restore process..."
    
    local restore_success=0
    local restore_total=0
    
    # Restore each service
    for service_func in restore_postgresql restore_redis restore_chromadb restore_neo4j; do
        ((restore_total++))
        if $service_func "$restore_dir"; then
            ((restore_success++))
        fi
    done
    
    echo ""
    if [[ $restore_success -eq $restore_total ]]; then
        print_status "All data restored successfully! ($restore_success/$restore_total services)"
        echo "🎉 WhisperEngine is ready to use with restored data!"
    elif [[ $restore_success -gt 0 ]]; then
        print_warning "Partial restore completed ($restore_success/$restore_total services)"
        echo "Some services may not have been restored. Check the logs above for details."
    else
        print_error "Restore failed for all services!"
        echo "Your original data should still be intact. Check container status with: ./multi-bot.sh status"
        exit 1
    fi
}

# Cleanup old backups
cleanup_backups() {
    local days_to_keep="${1:-30}"
    
    echo "🧹 Cleaning up old backups"
    echo "=========================="
    echo "Removing backups older than $days_to_keep days..."
    echo ""
    
    if [[ ! -d "$BACKUP_BASE_DIR" ]]; then
        print_warning "No backup directory found: $BACKUP_BASE_DIR"
        return 0
    fi
    
    local deleted_count=0
    local total_size_freed=0
    
    # Find and remove old backups
    for backup_dir in "$BACKUP_BASE_DIR"/whisperengine_backup_*; do
        if [[ -d "$backup_dir" ]]; then
            local backup_name=$(basename "$backup_dir")
            local backup_timestamp=${backup_name#whisperengine_backup_}
            
            # Check if backup is older than specified days
            if [[ -n "$backup_timestamp" ]]; then
                local backup_date=$(date -j -f "%Y%m%d_%H%M%S" "$backup_timestamp" "+%s" 2>/dev/null || echo "0")
                local cutoff_date=$(date -v-${days_to_keep}d "+%s")
                
                if [[ $backup_date -lt $cutoff_date && $backup_date -gt 0 ]]; then
                    local backup_size=$(du -sm "$backup_dir" 2>/dev/null | cut -f1 || echo "0")
                    local backup_display_date=$(date -j -f "%Y%m%d_%H%M%S" "$backup_timestamp" "+%Y-%m-%d %H:%M:%S" 2>/dev/null || echo "$backup_timestamp")
                    
                    echo "🗑️  Removing: $backup_timestamp ($backup_display_date) - ${backup_size}MB"
                    rm -rf "$backup_dir"
                    ((deleted_count++))
                    ((total_size_freed += backup_size))
                fi
            fi
        fi
    done
    
    echo ""
    if [[ $deleted_count -gt 0 ]]; then
        print_status "Cleanup completed: $deleted_count backup(s) removed, ${total_size_freed}MB freed"
    else
        print_info "No old backups found to remove"
    fi
}

# Main backup function
perform_backup() {
    echo "🗄️ WhisperEngine Data Backup"
    echo "============================="
    echo ""
    
    check_containers
    create_backup_dir
    
    local backup_success=0
    local backup_total=0
    
    # Backup each service
    for service_func in backup_postgresql backup_redis backup_chromadb backup_neo4j; do
        ((backup_total++))
        if $service_func; then
            ((backup_success++))
        fi
    done
    
    create_backup_metadata
    
    echo ""
    if [[ $backup_success -eq $backup_total ]]; then
        print_status "All backups completed successfully! ($backup_success/$backup_total)"
    elif [[ $backup_success -gt 0 ]]; then
        print_warning "Partial backup completed ($backup_success/$backup_total services)"
    else
        print_error "All backups failed!"
        exit 1
    fi
    
    show_backup_summary
}

# List available backups
list_backups() {
    echo "📁 Available Backups"
    echo "===================="
    echo ""
    
    if [[ ! -d "$BACKUP_BASE_DIR" ]]; then
        print_warning "No backup directory found: $BACKUP_BASE_DIR"
        echo "Create your first backup with: ./multi-bot.sh backup create"
        return 0
    fi
    
    local backup_count=0
    for backup_dir in "$BACKUP_BASE_DIR"/whisperengine_backup_*; do
        if [[ -d "$backup_dir" ]]; then
            ((backup_count++))
            local backup_name=$(basename "$backup_dir")
            local backup_timestamp=${backup_name#whisperengine_backup_}
            local backup_date=$(date -j -f "%Y%m%d_%H%M%S" "$backup_timestamp" "+%Y-%m-%d %H:%M:%S" 2>/dev/null || echo "$backup_timestamp")
            local backup_size=$(du -sh "$backup_dir" 2>/dev/null | cut -f1 || echo "Unknown")
            
            echo "📦 $backup_timestamp"
            echo "   Date: $backup_date"
            echo "   Size: $backup_size"
            echo "   Path: $backup_dir"
            
            # Show backup contents
            if [[ -f "$backup_dir/backup_info.txt" ]]; then
                echo "   Services:"
                grep "✅\|❌" "$backup_dir/backup_info.txt" | sed 's/^/     /'
            fi
            echo ""
        fi
    done
    
    if [[ $backup_count -eq 0 ]]; then
        print_warning "No backups found in $BACKUP_BASE_DIR"
        echo "Create your first backup with: ./multi-bot.sh backup create"
    else
        print_status "Found $backup_count backup(s)"
        echo "To restore a backup: ./multi-bot.sh backup restore TIMESTAMP"
    fi
}

# Show help
show_help() {
    echo "WhisperEngine Backup System"
    echo "============================"
    echo ""
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  create              - Create a new backup of all data"
    echo "  list                - List all available backups"
    echo "  restore TIMESTAMP   - Restore from a specific backup"
    echo "  cleanup [DAYS]      - Remove backups older than DAYS (default: 30)"
    echo "  help                - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 create                    # Create new backup"
    echo "  $0 list                      # Show available backups"
    echo "  $0 restore 20240912_143022   # Restore specific backup"
    echo "  $0 cleanup 7                 # Remove backups older than 7 days"
    echo ""
    echo "Environment Variables:"
    echo "  BACKUP_DIR    - Custom backup directory (default: ./backups)"
    echo ""
}

# Main command handling
case "${1:-help}" in
    "create")
        perform_backup
        ;;
    "list")
        list_backups
        ;;
    "restore")
        if [[ -z "${2:-}" ]]; then
            print_error "Please specify a backup timestamp"
            echo "Use '$0 list' to see available backups"
            exit 1
        fi
        perform_restore "$2"
        ;;
    "cleanup")
        cleanup_backups "${2:-30}"
        ;;
    "help"|*)
        show_help
        ;;
esac