#!/bin/bash

# WhisperEngine Local Development Migration Helper
# This script runs Alembic migrations with the correct database configuration for local development

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Database configuration for the quickstart environment
export POSTGRES_HOST="localhost"
export POSTGRES_PORT="5432"
export POSTGRES_USER="whisperengine"
export POSTGRES_PASSWORD="whisperengine_password"
export POSTGRES_DB="whisperengine"

echo -e "${BLUE}🚀 WhisperEngine Local Development Migration Helper${NC}"
echo "Database: ${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}"
echo ""

# Activate virtual environment
if [ ! -d ".venv" ]; then
    echo -e "${RED}❌ Virtual environment not found. Please run: python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt${NC}"
    exit 1
fi

echo -e "${YELLOW}📦 Activating virtual environment...${NC}"
source .venv/bin/activate

# Check if PostgreSQL is running
echo -e "${YELLOW}🔍 Checking database connectivity...${NC}"
if ! docker ps | grep -q whisperengine-postgres; then
    echo -e "${RED}❌ PostgreSQL container not running. Please start it with: docker compose up -d postgres${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Database is accessible${NC}"

# Run the requested Alembic command
if [ $# -eq 0 ]; then
    echo -e "${YELLOW}📊 Showing current migration status...${NC}"
    alembic current
    echo ""
    echo -e "${YELLOW}📜 Available commands:${NC}"
    echo "  $0 current      - Show current migration"
    echo "  $0 history      - Show migration history"  
    echo "  $0 upgrade head - Apply all pending migrations"
    echo "  $0 downgrade -1 - Downgrade one migration"
    echo "  $0 revision -m 'description' - Create new migration"
    echo ""
    echo -e "${YELLOW}📋 Recent migration history:${NC}"
    alembic history -r-3:
else
    echo -e "${YELLOW}🔧 Running: alembic $@${NC}"
    alembic "$@"
fi

echo -e "${GREEN}✅ Migration operation complete${NC}"