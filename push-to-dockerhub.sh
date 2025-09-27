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

# Check if user is logged in to Docker Hub
if ! docker info | grep -q "Username"; then
    print_warning "Not logged in to Docker Hub"
    print_status "Logging in to Docker Hub..."
    docker login
fi

# Define local images and their DockerHub counterparts
declare -A IMAGES=(
    ["whisperengine-bot"]="whisperengine-bot"
    ["whisperengine-whisperengine-web"]="whisperengine-web"
)

print_status "Building images if needed..."

# Check if main bot image exists, build if not
if ! docker image inspect whisperengine-bot:latest >/dev/null 2>&1; then
    print_warning "Main bot image not found, building..."
    docker-compose -f docker-compose.multi-bot.yml --profile build-only build whisperengine-bot-builder
fi

# Check if web image exists, build if not  
if ! docker image inspect whisperengine-whisperengine-web:latest >/dev/null 2>&1; then
    print_warning "Web image not found, building..."
    docker-compose -f docker-compose.multi-bot.yml build whisperengine-web
fi

# Tag and push images
for LOCAL_IMAGE in "${!IMAGES[@]}"; do
    DOCKERHUB_IMAGE="${IMAGES[$LOCAL_IMAGE]}"
    FULL_DOCKERHUB_TAG="${DOCKERHUB_USERNAME}/${DOCKERHUB_IMAGE}"
    
    print_status "Processing $LOCAL_IMAGE -> $FULL_DOCKERHUB_TAG"
    
    # Check if local image exists
    if docker image inspect "${LOCAL_IMAGE}:latest" >/dev/null 2>&1; then
        # Tag for DockerHub
        print_status "Tagging ${LOCAL_IMAGE}:latest as ${FULL_DOCKERHUB_TAG}:${VERSION}"
        docker tag "${LOCAL_IMAGE}:latest" "${FULL_DOCKERHUB_TAG}:${VERSION}"
        
        # Also tag as latest if version is not latest
        if [[ "$VERSION" != "latest" ]]; then
            docker tag "${LOCAL_IMAGE}:latest" "${FULL_DOCKERHUB_TAG}:latest"
        fi
        
        # Push to DockerHub
        print_status "Pushing ${FULL_DOCKERHUB_TAG}:${VERSION}"
        docker push "${FULL_DOCKERHUB_TAG}:${VERSION}"
        
        if [[ "$VERSION" != "latest" ]]; then
            print_status "Pushing ${FULL_DOCKERHUB_TAG}:latest"
            docker push "${FULL_DOCKERHUB_TAG}:latest"
        fi
        
        print_success "Successfully pushed ${FULL_DOCKERHUB_TAG}"
    else
        print_error "Local image ${LOCAL_IMAGE}:latest not found"
        print_warning "Skipping ${LOCAL_IMAGE}"
    fi
    
    echo ""
done

print_success "Docker Hub push complete!"
print_status "Your images are now available at:"
echo ""
for LOCAL_IMAGE in "${!IMAGES[@]}"; do
    DOCKERHUB_IMAGE="${IMAGES[$LOCAL_IMAGE]}"
    echo "  📦 https://hub.docker.com/r/${DOCKERHUB_USERNAME}/${DOCKERHUB_IMAGE}"
done
echo ""

print_status "To pull these images on other systems:"
echo ""
for LOCAL_IMAGE in "${!IMAGES[@]}"; do
    DOCKERHUB_IMAGE="${IMAGES[$LOCAL_IMAGE]}"
    echo "  docker pull ${DOCKERHUB_USERNAME}/${DOCKERHUB_IMAGE}:${VERSION}"
done
echo ""

print_status "To update docker-compose.yml for production deployment:"
echo ""
echo "Replace image references:"
echo "  whisperengine-bot:latest -> ${DOCKERHUB_USERNAME}/whisperengine-bot:${VERSION}"
echo "  whisperengine-whisperengine-web:latest -> ${DOCKERHUB_USERNAME}/whisperengine-web:${VERSION}"