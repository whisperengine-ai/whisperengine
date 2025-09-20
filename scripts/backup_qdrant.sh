#!/bin/bash
# Qdrant Memory System Backup Script
#
# This script creates a backup of the Qdrant vector database
# containing WhisperEngine's memory data.
#
# Usage: ./backup_qdrant.sh [backup_dir]
# If no backup directory is specified, defaults to ./backups/qdrant

set -e

# Default backup directory
BACKUP_DIR=${1:-"./backups/qdrant"}
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_PATH="${BACKUP_DIR}/${TIMESTAMP}"
DATA_DIR="./data/qdrant"  # Path to bind-mounted Qdrant data

# Ensure backup directory exists
mkdir -p "${BACKUP_PATH}"

echo "🔄 WhisperEngine - Qdrant Memory Backup"
echo "========================================"
echo "Backing up Qdrant vector memory data..."

# Option 1: Using tar for a full backup
echo "Creating compressed backup archive..."
tar -czf "${BACKUP_PATH}/qdrant_full_backup.tar.gz" -C "${DATA_DIR}" .

# Option 2: Using Qdrant's snapshot feature (if container is running)
if docker ps | grep -q "whisperengine-qdrant"; then
    echo "Creating Qdrant snapshot via API..."
    SNAPSHOT_NAME="whisperengine_backup_${TIMESTAMP}"
    
    # Create snapshot via Qdrant REST API
    curl -X POST "http://localhost:6333/snapshots" \
         -H "Content-Type: application/json" \
         -d "{\"snapshot_name\": \"${SNAPSHOT_NAME}\"}"
         
    # Wait for snapshot to complete
    sleep 5
    
    # Copy the snapshot to backup directory
    docker cp whisperengine-qdrant:/qdrant/snapshots/ "${BACKUP_PATH}/snapshots"
    
    echo "✅ Qdrant snapshot backup complete"
else
    echo "⚠️  Qdrant container not running, snapshot backup skipped"
fi

# Calculate size of backup
BACKUP_SIZE=$(du -sh "${BACKUP_PATH}" | cut -f1)

echo "✅ Backup complete!"
echo "📂 Backup location: ${BACKUP_PATH}"
echo "📊 Backup size: ${BACKUP_SIZE}"
echo "📅 Timestamp: ${TIMESTAMP}"

# List available backups
echo -e "\nAvailable backups:"
ls -lh "${BACKUP_DIR}" | grep -v "total"

exit 0
