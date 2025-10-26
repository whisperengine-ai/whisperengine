#!/bin/bash
# Quick start ML experiments container

set -e

echo "🧪 WhisperEngine ML Experiments - Quick Start"
echo "=============================================="
echo ""

# Activate virtual environment
if [ -d ".venv" ]; then
    echo "🐍 Activating Python virtual environment..."
    source .venv/bin/activate
else
    echo "❌ Virtual environment not found at .venv"
    echo "💡 Create it with: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements-ml-experiments.txt"
    exit 1
fi

# Check if infrastructure is running
echo "1️⃣  Checking infrastructure..."
if ! docker ps | grep -q "influxdb"; then
    echo "❌ InfluxDB not running. Starting infrastructure..."
    ./multi-bot.sh infra
    echo "⏳ Waiting for InfluxDB to be ready..."
    sleep 5
else
    echo "✅ Infrastructure already running"
fi

# Build and start ML experiments container
echo ""
echo "2️⃣  Building ML experiments container..."
docker compose -f docker-compose.ml-experiments.yml build

echo ""
echo "3️⃣  Starting ML experiments container..."
docker compose -f docker-compose.ml-experiments.yml up -d

echo ""
echo "4️⃣  Waiting for Jupyter Lab to start..."
sleep 3

# Check if container is running
if docker ps | grep -q "whisperengine-ml-experiments"; then
    echo "✅ Container running!"
else
    echo "❌ Container failed to start. Check logs:"
    echo "   docker logs whisperengine-ml-experiments"
    exit 1
fi

echo ""
echo "=============================================="
echo "✅ ML Experiments Ready!"
echo "=============================================="
echo ""
echo "📊 Jupyter Lab: http://localhost:8888"
echo ""
echo "🚀 Run first experiment:"
echo "   docker exec -it whisperengine-ml-experiments python /app/experiments/notebooks/01_response_strategy_optimization.py"
echo ""
echo "📝 View logs:"
echo "   docker logs -f whisperengine-ml-experiments"
echo ""
echo "🛑 Stop experiments:"
echo "   docker compose -f docker-compose.ml-experiments.yml down"
echo ""
