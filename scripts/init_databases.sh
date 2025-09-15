#!/bin/bash

# Database Initialization Orchestrator
# Coordinates initialization of all datastores in proper order

set -e

echo "🚀 Starting WhisperEngine Database Initialization..."
echo "=" * 60

# Configuration from environment
POSTGRES_HOST=${POSTGRES_HOST:-postgres}
POSTGRES_PORT=${POSTGRES_PORT:-5432}
POSTGRES_DB=${POSTGRES_DB:-discord_bot}
POSTGRES_USER=${POSTGRES_USER:-bot_user}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-}

CHROMADB_HOST=${CHROMADB_HOST:-chromadb}
CHROMADB_PORT=${CHROMADB_PORT:-8000}

REDIS_HOST=${REDIS_HOST:-redis}
REDIS_PORT=${REDIS_PORT:-6379}

NEO4J_HOST=${NEO4J_HOST:-neo4j}
NEO4J_PORT=${NEO4J_PORT:-7687}
NEO4J_USERNAME=${NEO4J_USERNAME:-neo4j}
NEO4J_PASSWORD=${NEO4J_PASSWORD:-}

# Wait for services to be ready
wait_for_service() {
    local service_name=$1
    local host=$2
    local port=$3
    local max_attempts=${4:-30}
    
    echo "⏳ Waiting for $service_name to be ready at $host:$port..."
    
    for i in $(seq 1 $max_attempts); do
        if nc -z "$host" "$port" 2>/dev/null; then
            echo "✅ $service_name is ready!"
            return 0
        fi
        echo "  Attempt $i/$max_attempts - waiting for $service_name..."
        sleep 2
    done
    
    echo "❌ $service_name failed to become ready within expected time"
    return 1
}

# Wait for PostgreSQL to be ready
wait_for_postgresql() {
    echo "⏳ Waiting for PostgreSQL to be ready..."
    
    for i in $(seq 1 30); do
        if PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT 1" > /dev/null 2>&1; then
            echo "✅ PostgreSQL is ready!"
            return 0
        fi
        echo "  Attempt $i/30 - waiting for PostgreSQL..."
        sleep 2
    done
    
    echo "❌ PostgreSQL failed to become ready"
    return 1
}

# Initialize PostgreSQL schema
init_postgresql() {
    echo "📝 Initializing PostgreSQL schema..."
    
    if ! wait_for_postgresql; then
        return 1
    fi
    
    # Run main schema initialization
    echo "  Running main schema initialization..."
    PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /app/scripts/init_postgres.sql
    
    # Run privacy schema if exists
    if [ -f "/app/scripts/privacy_schema.sql" ]; then
        echo "  Running privacy schema initialization..."
        PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /app/scripts/privacy_schema.sql
    fi
    
    echo "✅ PostgreSQL schema initialized"
    return 0
}

# Initialize ChromaDB collections
init_chromadb() {
    echo "🗃️ Initializing ChromaDB collections..."
    
    if ! wait_for_service "ChromaDB" "$CHROMADB_HOST" "$CHROMADB_PORT"; then
        return 1
    fi
    
    # Additional wait for ChromaDB API to be fully ready
    sleep 5
    
    # Run ChromaDB initialization
    if [ -f "/app/scripts/init_chromadb.py" ]; then
        echo "  Running ChromaDB collection initialization..."
        CHROMADB_HOST="$CHROMADB_HOST" CHROMADB_PORT="$CHROMADB_PORT" python3 /app/scripts/init_chromadb.py
    else
        echo "  ⚠️ ChromaDB initialization script not found, skipping..."
    fi
    
    echo "✅ ChromaDB collections initialized"
    return 0
}

# Verify Redis
verify_redis() {
    echo "🔴 Verifying Redis connection..."
    
    if ! wait_for_service "Redis" "$REDIS_HOST" "$REDIS_PORT"; then
        return 1
    fi
    
    # Test Redis with a simple ping
    if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping | grep -q "PONG"; then
        echo "✅ Redis connection verified"
        return 0
    else
        echo "❌ Redis ping failed"
        return 1
    fi
}

# Initialize Neo4j (if available)
init_neo4j() {
    echo "🕸️ Initializing Neo4j graph database..."
    
    if ! wait_for_service "Neo4j" "$NEO4J_HOST" "$NEO4J_PORT"; then
        echo "⚠️ Neo4j not available, skipping graph database initialization"
        return 0
    fi
    
    # Run Neo4j setup script if available
    if [ -f "/app/scripts/setup_neo4j.sh" ]; then
        echo "  Running Neo4j setup script..."
        NEO4J_PASSWORD="$NEO4J_PASSWORD" bash /app/scripts/setup_neo4j.sh
    else
        echo "  ⚠️ Neo4j setup script not found, skipping..."
    fi
    
    echo "✅ Neo4j graph database initialized"
    return 0
}

# Run health checks
run_health_checks() {
    echo "🔍 Running comprehensive health checks..."
    
    local all_healthy=true
    
    # PostgreSQL health check
    if wait_for_postgresql; then
        echo "✅ PostgreSQL: Healthy"
    else
        echo "❌ PostgreSQL: Unhealthy"
        all_healthy=false
    fi
    
    # ChromaDB health check
    if curl -f "http://$CHROMADB_HOST:$CHROMADB_PORT/api/v1/heartbeat" > /dev/null 2>&1; then
        echo "✅ ChromaDB: Healthy"
    else
        echo "❌ ChromaDB: Unhealthy"
        all_healthy=false
    fi
    
    # Redis health check
    if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping | grep -q "PONG"; then
        echo "✅ Redis: Healthy"
    else
        echo "❌ Redis: Unhealthy"
        all_healthy=false
    fi
    
    # Neo4j health check (optional)
    if nc -z "$NEO4J_HOST" "$NEO4J_PORT" 2>/dev/null; then
        echo "✅ Neo4j: Available"
    else
        echo "⚠️ Neo4j: Not available (optional)"
    fi
    
    if $all_healthy; then
        echo "🎉 All critical services are healthy!"
        return 0
    else
        echo "❌ Some services are unhealthy"
        return 1
    fi
}

# Main initialization sequence
main() {
    echo "Starting database initialization sequence..."
    
    # Initialize services in dependency order
    
    # 1. PostgreSQL (foundational data)
    if ! init_postgresql; then
        echo "❌ PostgreSQL initialization failed"
        exit 1
    fi
    
    # 2. Redis (caching)
    if ! verify_redis; then
        echo "❌ Redis verification failed"
        exit 1
    fi
    
    # 3. ChromaDB (vector storage)
    if ! init_chromadb; then
        echo "❌ ChromaDB initialization failed"
        exit 1
    fi
    
    # 4. Neo4j (optional graph storage)
    init_neo4j  # Don't fail if Neo4j is unavailable
    
    # 5. Final health checks
    if ! run_health_checks; then
        echo "❌ Health checks failed"
        exit 1
    fi
    
    echo ""
    echo "🎉 WhisperEngine Database Initialization Complete!"
    echo "All datastores are ready for bot operation."
    echo ""
}

# Install required tools if not present
ensure_tools() {
    # Check for required tools
    local missing_tools=()
    
    if ! command -v psql &> /dev/null; then
        missing_tools+=("postgresql-client")
    fi
    
    if ! command -v redis-cli &> /dev/null; then
        missing_tools+=("redis-tools")
    fi
    
    if ! command -v curl &> /dev/null; then
        missing_tools+=("curl")
    fi
    
    if ! command -v nc &> /dev/null; then
        missing_tools+=("netcat")
    fi
    
    if [ ${#missing_tools[@]} -gt 0 ]; then
        echo "📦 Installing required tools: ${missing_tools[*]}"
        apt-get update && apt-get install -y "${missing_tools[@]}"
    fi
}

# Command line interface
case "${1:-init}" in
    "init")
        ensure_tools
        main
        ;;
    "health")
        run_health_checks
        ;;
    "postgresql")
        ensure_tools
        init_postgresql
        ;;
    "chromadb")
        ensure_tools
        init_chromadb
        ;;
    "redis")
        ensure_tools
        verify_redis
        ;;
    "neo4j")
        ensure_tools
        init_neo4j
        ;;
    *)
        echo "Usage: $0 [init|health|postgresql|chromadb|redis|neo4j]"
        echo ""
        echo "Commands:"
        echo "  init       - Run full initialization sequence (default)"
        echo "  health     - Run health checks only"
        echo "  postgresql - Initialize PostgreSQL only"
        echo "  chromadb   - Initialize ChromaDB only"
        echo "  redis      - Verify Redis only"
        echo "  neo4j      - Initialize Neo4j only"
        exit 1
        ;;
esac