#!/bin/bash
# =======================================================
# Qdrant Vector Database Backup & Restore Script
# =======================================================
#
# This script provides utilities to backup and restore Qdrant vector database
# data for WhisperEngine. It handles both bind mount and Docker volume setups.
#
# Usage:
#   ./backup_qdrant.sh backup   # Create a new backup
#   ./backup_qdrant.sh restore BACKUP_FILE  # Restore from a backup file

# Configuration
BACKUP_DIR="./backups/qdrant"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/qdrant_backup_${DATE}.tar.gz"
DOCKER_VOLUME="whisperengine-qdrant-data"
BIND_MOUNT_PATH="./data/qdrant"

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

# Color output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Display banner
echo -e "${GREEN}"
echo "======================================================"
echo "WhisperEngine Qdrant Vector Database Backup & Restore"
echo "======================================================"
echo -e "${NC}"

# Backup function
backup_qdrant() {
    echo -e "${YELLOW}Starting Qdrant backup process...${NC}"
    
    # Check if bind mount directory exists
    if [ -d "$BIND_MOUNT_PATH" ]; then
        echo -e "📁 ${GREEN}Creating backup of Qdrant data from bind mount...${NC}"
        tar -czf $BACKUP_FILE $BIND_MOUNT_PATH
        if [ $? -eq 0 ]; then
            echo -e "✅ ${GREEN}Backup created at:${NC} $BACKUP_FILE"
            echo -e "📊 ${GREEN}Backup size:${NC} $(du -h $BACKUP_FILE | cut -f1)"
        else
            echo -e "❌ ${RED}Backup failed!${NC}"
            exit 1
        fi
    else
        # Check if Docker volume exists
        if docker volume inspect $DOCKER_VOLUME > /dev/null 2>&1; then
            echo -e "🐳 ${GREEN}Creating backup of Qdrant data from Docker volume...${NC}"
            docker run --rm -v $DOCKER_VOLUME:/data -v $(pwd)/$BACKUP_DIR:/backup \
                alpine sh -c "cd /data && tar -czf /backup/qdrant_backup_${DATE}.tar.gz ."
            if [ $? -eq 0 ]; then
                echo -e "✅ ${GREEN}Backup created at:${NC} $BACKUP_FILE"
                echo -e "📊 ${GREEN}Backup size:${NC} $(du -h $BACKUP_FILE | cut -f1)"
            else
                echo -e "❌ ${RED}Backup failed!${NC}"
                exit 1
            fi
        else
            echo -e "❌ ${RED}Error: Neither bind mount nor Docker volume found!${NC}"
            echo "Please ensure Qdrant is properly configured with either:"
            echo "  - Bind mount at $BIND_MOUNT_PATH"
            echo "  - Docker volume named $DOCKER_VOLUME"
            exit 1
        fi
    fi
}

# Restore function
restore_qdrant() {
    if [ -z "$1" ]; then
        echo -e "❌ ${RED}Error: No backup file specified for restore!${NC}"
        echo "Usage: $0 restore BACKUP_FILE"
        exit 1
    fi
    
    RESTORE_FILE=$1
    
    if [ ! -f "$RESTORE_FILE" ]; then
        echo -e "❌ ${RED}Error: Backup file not found:${NC} $RESTORE_FILE"
        exit 1
    fi
    
    echo -e "${YELLOW}Starting Qdrant restore process...${NC}"
    echo -e "${RED}Warning: This will overwrite existing Qdrant data!${NC}"
    read -p "Are you sure you want to continue? (y/n) " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Restore cancelled.${NC}"
        exit 0
    fi
    
    # Stop Qdrant container if running
    if docker ps | grep -q whisperengine-qdrant; then
        echo -e "🛑 ${YELLOW}Stopping Qdrant container...${NC}"
        docker stop whisperengine-qdrant
    fi
    
    # Check if bind mount directory exists
    if [ -d "$BIND_MOUNT_PATH" ]; then
        echo -e "📁 ${GREEN}Restoring Qdrant data to bind mount...${NC}"
        # Clean existing data
        rm -rf $BIND_MOUNT_PATH/*
        # Restore from backup
        mkdir -p $BIND_MOUNT_PATH
        tar -xzf $RESTORE_FILE -C $(dirname $BIND_MOUNT_PATH)
        if [ $? -eq 0 ]; then
            echo -e "✅ ${GREEN}Restore completed successfully to:${NC} $BIND_MOUNT_PATH"
        else
            echo -e "❌ ${RED}Restore failed!${NC}"
            exit 1
        fi
    else
        # Check if Docker volume exists
        if docker volume inspect $DOCKER_VOLUME > /dev/null 2>&1; then
            echo -e "🐳 ${GREEN}Restoring Qdrant data to Docker volume...${NC}"
            docker run --rm -v $DOCKER_VOLUME:/data -v $(dirname $RESTORE_FILE):/backup \
                alpine sh -c "rm -rf /data/* && tar -xzf /backup/$(basename $RESTORE_FILE) -C /data"
            if [ $? -eq 0 ]; then
                echo -e "✅ ${GREEN}Restore completed successfully to Docker volume:${NC} $DOCKER_VOLUME"
            else
                echo -e "❌ ${RED}Restore failed!${NC}"
                exit 1
            fi
        else
            echo -e "❌ ${RED}Error: Neither bind mount nor Docker volume found!${NC}"
            echo "Please ensure Qdrant storage location is properly configured."
            exit 1
        fi
    fi
    
    # Restart Qdrant container if it was running
    if docker ps -a | grep -q whisperengine-qdrant; then
        echo -e "🚀 ${YELLOW}Restarting Qdrant container...${NC}"
        docker start whisperengine-qdrant
    fi
}

# Main script logic
case "$1" in
    backup)
        backup_qdrant
        ;;
    restore)
        restore_qdrant "$2"
        ;;
    *)
        echo -e "${YELLOW}Usage:${NC}"
        echo "  $0 backup                # Create a new backup"
        echo "  $0 restore BACKUP_FILE   # Restore from a backup file"
        echo
        echo -e "${YELLOW}Available backups:${NC}"
        if [ -d "$BACKUP_DIR" ]; then
            ls -lh $BACKUP_DIR | grep -v "^total" | awk '{print "  " $9 " (" $5 ")"}'
        else
            echo "  No backups found"
        fi
        ;;
esac