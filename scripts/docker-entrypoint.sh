#!/bin/bash
# WhisperEngine Docker Entrypoint Script
# Handles initialization tasks and starts the main application

set -e  # Exit on any error

echo "🚀 WhisperEngine Docker Container Starting..."

# Wait for PostgreSQL to be ready (if needed)
if [ -n "$POSTGRES_HOST" ]; then
    echo "⏳ Waiting for PostgreSQL to be ready..."
    while ! nc -z "${POSTGRES_HOST}" "${POSTGRES_PORT:-5432}"; do
        echo "Waiting for PostgreSQL at ${POSTGRES_HOST}:${POSTGRES_PORT:-5432}..."
        sleep 2
    done
    echo "✅ PostgreSQL is ready"
fi

# Wait for Qdrant to be ready (if needed)
if [ -n "$QDRANT_HOST" ]; then
    echo "⏳ Waiting for Qdrant to be ready..."
    while ! nc -z "${QDRANT_HOST}" "${QDRANT_PORT:-6333}"; do
        echo "Waiting for Qdrant at ${QDRANT_HOST}:${QDRANT_PORT:-6333}..."
        sleep 2
    done
    echo "✅ Qdrant is ready"
fi

# Note: Database migrations should be handled by a separate init container
# in production deployments to avoid race conditions

# Start the main application
echo "🎯 Starting WhisperEngine main application..."
exec python /app/run.py "$@"