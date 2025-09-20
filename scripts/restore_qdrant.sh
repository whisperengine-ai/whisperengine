#!/bin/bash
# Qdrant Memory System Restore Script
#
# This script restores a Qdrant vector database backup
# containing WhisperEngine's memory data.
#
# Usage: ./restore_qdrant.sh [backup_path]

set -e

if [ -z "$1" ]; then
    echo "❌ Error: No backup path specified"
    echo "Usage: ./restore_qdrant.sh [backup_path]"
    echo "Example: ./restore_qdrant.sh ./backups/qdrant/20250920_123456"
    exit 1
fi

BACKUP_PATH="$1"
DATA_DIR="./data/qdrant"  # Path to bind-mounted Qdrant data

# Check if backup exists
if [ ! -d "${BACKUP_PATH}" ]; then
    echo "❌ Error: Backup path does not exist: ${BACKUP_PATH}"
    exit 1
fi

# Check if backup archive exists
if [ ! -f "${BACKUP_PATH}/qdrant_full_backup.tar.gz" ]; then
    echo "❌ Error: Backup archive not found at ${BACKUP_PATH}/qdrant_full_backup.tar.gz"
    exit 1
fi

echo "🔄 WhisperEngine - Qdrant Memory Restore"
echo "========================================="
echo "Restoring Qdrant vector memory data from: ${BACKUP_PATH}"

# Stop Qdrant container if it's running
if docker ps | grep -q "whisperengine-qdrant"; then
    echo "Stopping Qdrant container..."
    docker stop whisperengine-qdrant
fi

echo "Clearing existing data directory..."
# Create backup of current data just in case
TEMP_BACKUP="./data/qdrant_current_$(date +"%Y%m%d_%H%M%S")"
if [ -d "${DATA_DIR}" ]; then
    echo "Creating backup of current data at ${TEMP_BACKUP}"
    mv "${DATA_DIR}" "${TEMP_BACKUP}"
fi

# Create fresh data directory
mkdir -p "${DATA_DIR}"

echo "Restoring data from backup archive..."
tar -xzf "${BACKUP_PATH}/qdrant_full_backup.tar.gz" -C "${DATA_DIR}"

echo "Setting correct permissions..."
chmod -R 755 "${DATA_DIR}"

# Start Qdrant container
echo "Starting Qdrant container..."
docker-compose up -d qdrant

echo "Waiting for Qdrant to start..."
sleep 10

# Verify restore
echo "Verifying restore..."
if docker ps | grep -q "whisperengine-qdrant"; then
    echo "✅ Qdrant container is running"
    
    # Check if collections are accessible
    if curl -s "http://localhost:6333/collections" | grep -q "collections"; then
        echo "✅ Qdrant collections are accessible"
    else
        echo "⚠️  Warning: Could not verify Qdrant collections"
    fi
else
    echo "⚠️  Warning: Qdrant container did not start properly"
fi

echo -e "\n✅ Restore complete!"
echo "📂 Restored from: ${BACKUP_PATH}"
echo "📂 Previous data (if any) backed up to: ${TEMP_BACKUP}"

exit 0