#!/bin/bash
# Docker LM Studio Integration Test Script
# Builds and tests the synthetic conversation system with local LM Studio

set -e

echo "🔨 Building Docker image for synthetic testing..."
docker build -f Dockerfile.synthetic -t whisperengine-synthetic:latest .

echo "🧪 Testing LM Studio connection..."
docker run --rm \
  -e LLM_CLIENT_TYPE=lmstudio \
  -e LLM_CHAT_API_URL=http://host.docker.internal:1234/v1 \
  -e LLM_CHAT_MODEL=local-model \
  whisperengine-synthetic:latest \
  python test_docker_lmstudio.py

echo "🚀 Starting synthetic conversation generation..."
docker-compose -f docker-compose.synthetic.yml up --build -d

echo "📋 Showing service status..."
docker-compose -f docker-compose.synthetic.yml ps

echo "📝 To view logs:"
echo "  docker-compose -f docker-compose.synthetic.yml logs -f synthetic-generator"
echo "  docker-compose -f docker-compose.synthetic.yml logs -f synthetic-validator"

echo "🛑 To stop services:"
echo "  docker-compose -f docker-compose.synthetic.yml down"