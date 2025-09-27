# Vector Memory System Data Architecture

## Overview
This document describes the data architecture for the vector memory system in WhisperEngine, with focus on data persistence, backup, and recovery strategies.

## Architecture Components

### 1. Vector Database: Qdrant
WhisperEngine uses Qdrant as its primary vector database for memory storage. Qdrant provides:

- High-performance vector similarity search
- Rich filtering capabilities
- Robust persistence mechanisms
- Efficient memory management
- Horizontal scalability options

### 2. Data Storage Structure

#### Collections
- **Primary Collection**: `whisperengine_memory` - Stores all vector embeddings
- **Per-User Collections**: `memories_{user_id}` - Separate collections for each user's memories

#### Point Structure
Each memory is stored as a vector point with:
- **Vector**: Dense embedding representation (384 dimensions by default)
- **Payload**: Metadata including:
  - `user_id`: Owner of the memory
  - `content`: Actual memory content
  - `memory_type`: Type of memory (conversation, factual, emotional, etc.)
  - `timestamp`: Creation time
  - `importance`: Memory importance score (0-1)
  - `confidence`: Confidence level of the memory
  - Additional custom metadata fields

### 3. Persistence Strategy

#### Docker Volume Approach
WhisperEngine uses direct bind mounts for Qdrant data:
```yaml
volumes:
  - ./data/qdrant:/qdrant/storage   # Direct bind mount for easier backup access
```

This approach provides:
- Direct access to data files from the host
- Easier backup and restore operations
- Better visibility into data structure
- Simplified disaster recovery

#### Data Directory Structure
```
data/
└── qdrant/
    ├── collections/    # Vector collections and indexes
    ├── snapshots/      # Database snapshots (if created)
    └── metadata/       # Qdrant metadata and configuration
```

## Backup and Recovery

### Backup Strategies

#### 1. File-based Backup
Using the provided `scripts/backup_qdrant.sh` script, which:
- Creates compressed archives of the data directory
- Preserves all collection data and indexes
- Uses timestamps for versioning
- Stores backups in `backups/qdrant/{timestamp}/`

#### 2. Snapshot-based Backup
Using Qdrant's native snapshot feature:
- Creates consistent point-in-time snapshots
- API-driven for automation
- Low overhead on running system

### Recovery Process
The `scripts/restore_qdrant.sh` script handles recovery:
1. Stops the running Qdrant instance
2. Backs up current data (if any)
3. Extracts backup archive to data directory
4. Restarts Qdrant service
5. Verifies collection integrity

## Performance Considerations

### Resource Requirements
- **Memory**: Qdrant performs best with at least 1GB RAM allocated
- **CPU**: Vector operations benefit from multiple cores
- **Storage**: Vector indexes typically require 1.2-1.5x the size of raw data

### Optimization Techniques
1. **Index Configuration**: Using HNSW algorithm with optimized parameters
2. **Quantization**: Optional compression for reduced memory footprint
3. **Payload Indexing**: Fast filtering by frequently used metadata fields

## Migrating from Previous Systems

### Legacy ChromaDB to Qdrant Migration
The migration from ChromaDB to Qdrant vector memory has been completed. All memory data now uses:
1. Qdrant collections with named vectors (content, emotion, semantic)
2. FastEmbed local embeddings with sentence-transformers/all-MiniLM-L6-v2  
3. Bot-specific memory segmentation and isolation
4. Advanced vector similarity search with performance optimizations

## Monitoring and Maintenance

### Health Checks
- Regular verification via `scripts/vector_memory_healthcheck.sh`
- Integration with container health checks
- API-based metrics collection

### Regular Maintenance Tasks
1. **Backups**: Schedule daily backups using cron
2. **Optimization**: Periodic index optimization
3. **Cleanup**: Optional removal of low-importance memories

## Conclusion
The vector memory system provides robust persistence with simple backup and recovery mechanisms. By using Qdrant with direct bind mounts, WhisperEngine ensures data durability while maintaining high performance for memory operations.