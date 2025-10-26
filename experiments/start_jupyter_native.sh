#!/bin/bash
# Start Jupyter Lab natively (RECOMMENDED for development)
# Faster iteration, better VS Code integration, GPU access

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Jupyter Lab (Native)${NC}"

# Activate virtual environment
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Creating...${NC}"
    python3 -m venv .venv
fi

source .venv/bin/activate

# Install ML requirements if needed
echo -e "${BLUE}📦 Checking ML dependencies...${NC}"
if ! python -c "import xgboost" &> /dev/null; then
    echo -e "${YELLOW}⚠️  ML libraries not found. Installing...${NC}"
    pip install -r requirements-ml.txt
else
    echo -e "${GREEN}✅ ML libraries already installed${NC}"
fi

# Set environment variables for data sources
export INFLUXDB_HOST="localhost"
export INFLUXDB_PORT="8087"
export POSTGRES_HOST="localhost"
export POSTGRES_PORT="5433"
export QDRANT_HOST="localhost"
export QDRANT_PORT="6334"
export FASTEMBED_CACHE_PATH="/tmp/fastembed_cache"

echo -e "${GREEN}✅ Environment configured:${NC}"
echo "   InfluxDB: http://${INFLUXDB_HOST}:${INFLUXDB_PORT}"
echo "   PostgreSQL: ${POSTGRES_HOST}:${POSTGRES_PORT}"
echo "   Qdrant: http://${QDRANT_HOST}:${QDRANT_PORT}"
echo ""

# Start Jupyter Lab
echo -e "${BLUE}🌐 Starting JupyterLab at http://localhost:8888${NC}"
echo -e "${YELLOW}   Press Ctrl+C to stop${NC}"
echo ""

cd /Users/markcastillo/git/whisperengine

jupyter lab --port=8888 --no-browser
