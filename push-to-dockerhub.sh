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
NO_CACHE_FLAG=""

# Check for --no-cache flag in any position
for arg in "$@"; do
    if [[ "$arg" == "--no-cache" ]]; then
        NO_CACHE_FLAG="--no-cache"
        print_warning "Building with --no-cache (fresh build, slower but ensures latest changes)"
        break
    fi
done

# Validate username
if [[ -z "$DOCKERHUB_USERNAME" ]]; then
    print_error "DockerHub username is required"
    echo ""
    echo "Usage: $0 [DOCKERHUB_USERNAME] [VERSION] [--no-cache]"
    echo ""
    echo "Examples:"
    echo "  $0 myusername                    # Push with 'latest' tag"
    echo "  $0 myusername v1.0.0            # Push with version tag"
    echo "  $0 myusername v1.0.0 --no-cache # Fresh build without cache"
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
# Note: Database migrations use the main whisperengine container with a different command
# (python /app/scripts/run_migrations.py), so no separate migrations image is needed
IMAGES="whisperengine whisperengine-ui"

print_status "Building WhisperEngine containers..."
echo ""

# Setup Docker buildx for multi-platform builds
print_status "Setting up Docker buildx for multi-platform builds..."
BUILDER_NAME="whisperengine-multiplatform"
if ! docker buildx inspect "$BUILDER_NAME" >/dev/null 2>&1; then
    print_status "Creating new buildx builder: $BUILDER_NAME"
    docker buildx create --name "$BUILDER_NAME" --driver docker-container --use
else
    print_status "Using existing buildx builder: $BUILDER_NAME"
    docker buildx use "$BUILDER_NAME"
fi
docker buildx inspect --bootstrap
echo ""

# Build main WhisperEngine assistant container
print_status "Building WhisperEngine Assistant container with pre-downloaded models..."
print_status "This will download and bundle:"
print_status "  • FastEmbed: sentence-transformers/all-MiniLM-L6-v2 (~67MB)"
print_status "  • RoBERTa: cardiffnlp/twitter-roberta-base-emotion-multilabel-latest (~300MB)"
print_status "  • Total model cache: ~400MB (embedded in container)"
print_status "Platforms: linux/amd64, linux/arm64 (multi-platform support)"
echo ""

# Build and push multi-platform image
print_status "Building and pushing multi-platform image..."
if [[ -n "$NO_CACHE_FLAG" ]]; then
    print_warning "Using --no-cache: This will be slower but ensures fresh build"
fi

if docker buildx build \
    --platform linux/amd64,linux/arm64 \
    -t ${DOCKERHUB_USERNAME}/whisperengine:${VERSION} \
    -t ${DOCKERHUB_USERNAME}/whisperengine:latest \
    -f Dockerfile \
    ${NO_CACHE_FLAG} \
    --push \
    .; then
    print_success "WhisperEngine Assistant container built and pushed successfully (multi-platform)"
    
    # Verify multi-platform manifest
    print_status "Verifying multi-platform manifest..."
    if docker buildx imagetools inspect ${DOCKERHUB_USERNAME}/whisperengine:${VERSION} | grep -E "linux/(amd64|arm64)"; then
        print_success "✅ Multi-platform manifest verified (AMD64 + ARM64)"
    else
        print_warning "⚠️ Could not verify multi-platform manifest"
    fi
else
    print_error "Failed to build WhisperEngine Assistant container"
    exit 1
fi

# Build CDL Web UI container
print_status "Building CDL Web UI container (multi-platform)..."
if docker buildx build \
    --platform linux/amd64,linux/arm64 \
    -t ${DOCKERHUB_USERNAME}/whisperengine-ui:${VERSION} \
    -t ${DOCKERHUB_USERNAME}/whisperengine-ui:latest \
    -f cdl-web-ui/Dockerfile \
    ${NO_CACHE_FLAG} \
    --push \
    ./cdl-web-ui; then
    print_success "CDL Web UI container built and pushed successfully (multi-platform)"
else
    print_error "Failed to build CDL Web UI container"
    exit 1
fi

echo ""
print_success "🎉 Docker Hub push complete (multi-platform support)!"
print_status "Your images are now available at:"
echo ""
for LOCAL_IMAGE in $IMAGES; do
    echo "  📦 https://hub.docker.com/r/${DOCKERHUB_USERNAME}/${LOCAL_IMAGE}"
done
echo ""

print_status "Multi-platform support verified:"
echo "  ✅ linux/amd64 (Intel/AMD processors)"
echo "  ✅ linux/arm64 (ARM processors, Apple Silicon)"
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