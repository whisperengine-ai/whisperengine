#!/bin/bash
# WhisperEngine Docker Hub Push Script
# Usage: ./push-to-dockerhub.sh [DOCKERHUB_USERNAME] [VERSION]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[PUSH]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Get parameters
DOCKERHUB_USERNAME="${1}"
VERSION="${2:-latest}"

# Validate username
if [[ -z "$DOCKERHUB_USERNAME" ]]; then
    print_error "DockerHub username is required"
    echo ""
    echo "Usage: $0 [DOCKERHUB_USERNAME] [VERSION]"
    echo ""
    echo "Examples:"
    echo "  $0 myusername                    # Push with 'latest' tag"
    echo "  $0 myusername v1.0.0            # Push with version tag"
    echo "  $0 whisperengine-ai v1.0.0      # Push to whisperengine-ai org"
    echo ""
    exit 1
fi

print_status "Starting WhisperEngine Docker Hub push..."
print_status "DockerHub Username: $DOCKERHUB_USERNAME"
print_status "Version Tag: $VERSION"
echo ""

# Check if user is logged in to Docker Hub
if ! docker info | grep -q "Username"; then
    print_warning "Not logged in to Docker Hub"
    print_status "Logging in to Docker Hub..."
    docker login
fi

# Define images to build and push
IMAGES="whisperengine whisperengine-ui"

print_status "Building WhisperEngine containers..."
echo ""

# Build main WhisperEngine assistant container
print_status "Building WhisperEngine Assistant container with pre-downloaded models..."
print_status "This will download and bundle:"
print_status "  • FastEmbed: sentence-transformers/all-MiniLM-L6-v2 (~67MB)"
print_status "  • RoBERTa: cardiffnlp/twitter-roberta-base-emotion-multilabel-latest (~300MB)"
print_status "  • Total model cache: ~400MB (embedded in container)"
echo ""

if docker build -t whisperengine:${VERSION} -t whisperengine:latest -f Dockerfile .; then
    print_success "WhisperEngine Assistant container built successfully with pre-downloaded models"
    
    # Verify models are in container
    print_status "Verifying models are bundled in container..."
    docker run --rm whisperengine:latest python -c "
import os, json
config_path = '/app/models/model_config.json'
if os.path.exists(config_path):
    config = json.load(open(config_path))
    print('✅ Models verified in container:')
    print(f'  📊 Embedding: {config.get(\"embedding_models\", {}).get(\"primary\", \"Unknown\")}')
    print(f'  🎭 Emotion: {config.get(\"emotion_models\", {}).get(\"primary\", \"Unknown\")}')
else:
    print('❌ Model configuration not found in container')
    exit(1)
"
    if [ $? -eq 0 ]; then
        print_success "✅ Models successfully bundled in container"
    else
        print_error "❌ Model verification failed"
        exit 1
    fi
else
    print_error "Failed to build WhisperEngine Assistant container"
    exit 1
fi

# Build CDL Web UI container
print_status "Building CDL Web UI container..."
if docker build -t whisperengine-ui:${VERSION} -t whisperengine-ui:latest -f cdl-web-ui/Dockerfile ./cdl-web-ui; then
    print_success "CDL Web UI container built successfully"
else
    print_error "Failed to build CDL Web UI container"
    exit 1
fi

echo ""
print_status "Tagging and pushing containers to Docker Hub..."
echo ""

# Tag and push images
for LOCAL_IMAGE in $IMAGES; do
    DOCKERHUB_IMAGE="$LOCAL_IMAGE"
    FULL_DOCKERHUB_TAG="${DOCKERHUB_USERNAME}/${DOCKERHUB_IMAGE}"
    
    print_status "Processing $LOCAL_IMAGE -> $FULL_DOCKERHUB_TAG"
    
    # Check if local image exists
    if docker image inspect "${LOCAL_IMAGE}:${VERSION}" >/dev/null 2>&1; then
        # Tag for DockerHub
        print_status "Tagging ${LOCAL_IMAGE}:${VERSION} as ${FULL_DOCKERHUB_TAG}:${VERSION}"
        docker tag "${LOCAL_IMAGE}:${VERSION}" "${FULL_DOCKERHUB_TAG}:${VERSION}"
        
        # Also tag as latest
        print_status "Tagging ${LOCAL_IMAGE}:latest as ${FULL_DOCKERHUB_TAG}:latest"
        docker tag "${LOCAL_IMAGE}:latest" "${FULL_DOCKERHUB_TAG}:latest"
        
        # Push to DockerHub
        print_status "Pushing ${FULL_DOCKERHUB_TAG}:${VERSION}"
        docker push "${FULL_DOCKERHUB_TAG}:${VERSION}"
        
        print_status "Pushing ${FULL_DOCKERHUB_TAG}:latest"
        docker push "${FULL_DOCKERHUB_TAG}:latest"
        
        print_success "Successfully pushed ${FULL_DOCKERHUB_TAG}"
    else
        print_error "Local image ${LOCAL_IMAGE}:${VERSION} not found"
        print_warning "Skipping ${LOCAL_IMAGE}"
    fi
    
    echo ""
done

echo ""
print_success "🎉 Docker Hub push complete!"
print_status "Your images are now available at:"
echo ""
for LOCAL_IMAGE in $IMAGES; do
    echo "  📦 https://hub.docker.com/r/${DOCKERHUB_USERNAME}/${LOCAL_IMAGE}"
done
echo ""

print_status "To use these images in production:"
echo ""
echo "  # Pull images:"
for LOCAL_IMAGE in $IMAGES; do
    echo "  docker pull ${DOCKERHUB_USERNAME}/${LOCAL_IMAGE}:${VERSION}"
done
echo ""
echo "  # Use in docker-compose.yml:"
echo "  services:"
echo "    whisperengine-assistant:"
echo "      image: ${DOCKERHUB_USERNAME}/whisperengine:${VERSION}"
echo "    cdl-web-ui:"
echo "      image: ${DOCKERHUB_USERNAME}/whisperengine-ui:${VERSION}"
echo ""

print_status "Next steps:"
echo "  1. Create production docker-compose.yml with these images"
echo "  2. Update documentation to use containerized setup"
echo "  3. Test deployment without source code"