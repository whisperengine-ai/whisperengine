#!/usr/bin/env bash
set -euo pipefail

# WhisperEngine Unified Backup Script
# Supports: PostgreSQL, Redis, ChromaDB (file copy), Neo4j
# Usage:
#   ./scripts/db/backup_all.sh                # Default location ./backups/<timestamp>
#   BACKUP_DIR=/custom/path ./scripts/db/backup_all.sh
#   PG_HOST=localhost PG_DB=whisper_engine ./scripts/db/backup_all.sh

TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_ROOT="${BACKUP_DIR:-./backups}"/backup_${TIMESTAMP}
mkdir -p "${BACKUP_ROOT}" || true

log() { echo "[backup] $*"; }

# ---------- PostgreSQL ----------
PG_HOST=${POSTGRES_HOST:-localhost}
PG_PORT=${POSTGRES_PORT:-5432}
PG_DB=${POSTGRES_DB:-whisper_engine}
PG_USER=${POSTGRES_USER:-bot_user}
PG_PASSWORD=${POSTGRES_PASSWORD:-securepassword123}

export PGPASSWORD="$PG_PASSWORD"

log "PostgreSQL: dumping $PG_DB"
pg_dump -h "$PG_HOST" -p "$PG_PORT" -U "$PG_USER" -d "$PG_DB" -Fc -f "${BACKUP_ROOT}/postgres_${PG_DB}.dump" || log "WARN: pg_dump failed"

# ---------- Redis ----------
# Strategy: if running locally with default port, attempt SAVE then copy dump.rdb
REDIS_HOST=${REDIS_HOST:-localhost}
REDIS_PORT=${REDIS_PORT:-6379}
REDIS_BACKUP_DIR="${BACKUP_ROOT}/redis"
mkdir -p "$REDIS_BACKUP_DIR"

if command -v redis-cli >/dev/null 2>&1; then
  log "Redis: requesting SAVE"
  if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" SAVE; then
     if [ -f /var/lib/redis/dump.rdb ]; then
        cp /var/lib/redis/dump.rdb "$REDIS_BACKUP_DIR/" 2>/dev/null || true
     else
        # Try common Docker volume path
        find / -maxdepth 3 -name dump.rdb -exec cp {} "$REDIS_BACKUP_DIR/" \; 2>/dev/null || true
     fi
     log "Redis: dump attempted (check directory)"
  else
     log "WARN: Redis SAVE failed"
  fi
else
  log "Redis: redis-cli not found, skipping"
fi

# ---------- ChromaDB ----------
# Assume local persistent storage in ./data/chroma or docker volume
CHROMA_SRC="./data/chroma"
if [ -d "$CHROMA_SRC" ]; then
  log "ChromaDB: copying data directory"
  rsync -a "$CHROMA_SRC" "${BACKUP_ROOT}/chroma/" || log "WARN: Chroma copy failed"
else
  log "ChromaDB: directory not found ($CHROMA_SRC)"
fi

# ---------- Neo4j ----------
# If neo4j-admin available, use dump
NEO4J_HOST=${NEO4J_HOST:-localhost}
NEO4J_DB=${NEO4J_DATABASE:-neo4j}
NEO4J_USER=${NEO4J_USERNAME:-neo4j}
NEO4J_PASS=${NEO4J_PASSWORD:-neo4j_password_change_me}

if command -v cypher-shell >/dev/null 2>&1; then
  log "Neo4j: collecting basic stats"
  cypher-shell -a bolt://$NEO4J_HOST:7687 -u "$NEO4J_USER" -p "$NEO4J_PASS" "MATCH (n) RETURN count(n)" > "${BACKUP_ROOT}/neo4j_node_count.txt" || true
fi

if command -v neo4j-admin >/dev/null 2>&1; then
  log "Neo4j: creating dump (may require permissions)"
  neo4j-admin database dump "$NEO4J_DB" --to-path="${BACKUP_ROOT}/neo4j" || log "WARN: neo4j-admin dump failed"
else
  log "Neo4j: neo4j-admin not found, skipping dump"
fi

# ---------- Metadata ----------
cat > "${BACKUP_ROOT}/BACKUP_METADATA.json" <<EOF
{
  "timestamp": "${TIMESTAMP}",
  "postgres": {
    "host": "${PG_HOST}",
    "database": "${PG_DB}"
  },
  "redis": {
    "host": "${REDIS_HOST}",
    "port": "${REDIS_PORT}"
  },
  "chroma": {
    "source": "${CHROMA_SRC}",
    "present": $( [ -d "$CHROMA_SRC" ] && echo true || echo false )
  },
  "neo4j": {
    "host": "${NEO4J_HOST}",
    "database": "${NEO4J_DB}" 
  }
}
EOF

log "Backup complete -> ${BACKUP_ROOT}"
