#!/bin/bash
# =============================================================================
# WhisperEngine Local Docker Build & Push Script
# =============================================================================
# Build and push WhisperEngine Docker images locally to Docker Hub
# Matches the GitHub Actions workflow configuration for consistency

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Helper functions
print_status() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
print_dream() { echo -e "${PURPLE}🎭 $1${NC}"; }

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Build configuration (matches GitHub Actions)
IMAGE_NAME="whisperengine/whisperengine"
DOCKERFILE="docker/Dockerfile.multi-stage"
TARGET="production"
REGISTRY="docker.io"

# Default platform configuration
MULTI_PLATFORM="linux/amd64,linux/arm64"
SINGLE_PLATFORM="linux/amd64"

# =============================================================================
# Functions
# =============================================================================

show_help() {
    cat << EOF
🎭 WhisperEngine Docker Build & Push Script

USAGE:
    $0 [OPTIONS] [VERSION]

OPTIONS:
    -h, --help              Show this help message
    -f, --fast              Fast build (single platform: linux/amd64)
    -m, --multi             Multi-platform build (linux/amd64,linux/arm64) [default]
    -t, --test              Build and load locally (no push)
    -d, --dev               Build development target instead of production
    --dry-run              Show commands without executing
    --no-cache             Build without cache

VERSION:
    Specify version tag (default: auto-detect from git or 'latest')

EXAMPLES:
    $0                      # Multi-platform build, auto-detect version
    $0 v1.0.0              # Multi-platform build with specific version
    $0 --fast              # Fast single-platform build
    $0 --test              # Build locally for testing (no push)
    $0 --dev               # Build development target

EOF
}

load_environment() {
    print_info "Loading WhisperEngine environment configuration..."
    
    # Use WhisperEngine's env_manager if available
    if [ -f "env_manager.py" ]; then
        python -c "from env_manager import load_environment; load_environment()" 2>/dev/null || true
    fi
    
    # Load .env if it exists
    if [ -f ".env" ]; then
        print_info "Found .env file, loading environment variables..."
        # Export variables from .env (safely)
        set -a
        source .env 2>/dev/null || true
        set +a
    fi
}

get_version() {
    local version=""
    
    # Try to get version from git tags
    if command -v git >/dev/null 2>&1 && git rev-parse --git-dir >/dev/null 2>&1; then
        version=$(git describe --tags --always --dirty 2>/dev/null || echo "")
    fi
    
    # Fallback to latest if no git version
    if [ -z "$version" ]; then
        version="latest"
    fi
    
    echo "$version"
}

check_dependencies() {
    print_info "Checking dependencies..."
    
    # Check Docker
    if ! command -v docker >/dev/null 2>&1; then
        print_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    # Check if Docker daemon is running
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker daemon is not running"
        exit 1
    fi
    
    # Check buildx
    if ! docker buildx version >/dev/null 2>&1; then
        print_error "Docker buildx is not available"
        exit 1
    fi
    
    print_status "All dependencies available"
}

setup_buildx() {
    local builder_name="whisperengine-builder"
    
    print_info "Setting up Docker buildx..."
    
    # Create or use existing builder
    if ! docker buildx inspect "$builder_name" >/dev/null 2>&1; then
        print_info "Creating new buildx builder: $builder_name"
        docker buildx create --name "$builder_name" --driver docker-container --use
    else
        print_info "Using existing buildx builder: $builder_name"
        docker buildx use "$builder_name"
    fi
    
    # Bootstrap the builder
    docker buildx inspect --bootstrap
    
    print_status "Buildx ready"
}

validate_dockerfile() {
    if [ ! -f "$DOCKERFILE" ]; then
        print_error "Dockerfile not found: $DOCKERFILE"
        print_info "Available Dockerfiles:"
        find docker/ -name "Dockerfile*" -type f 2>/dev/null | sed 's/^/  /' || echo "  No Dockerfiles found in docker/"
        exit 1
    fi
    
    # Check if target exists in Dockerfile
    if ! grep -q "FROM.*as $TARGET" "$DOCKERFILE"; then
        print_warning "Target '$TARGET' not found in $DOCKERFILE"
        print_info "Available targets:"
        grep "FROM.*as" "$DOCKERFILE" | sed 's/^/  /' || echo "  No named targets found"
    fi
    
    print_status "Dockerfile validated: $DOCKERFILE"
}

docker_login() {
    if [ "$PUSH" = true ]; then
        print_info "Logging into Docker Hub..."
        
        if [ -n "${DOCKERHUB_USERNAME:-}" ] && [ -n "${DOCKERHUB_TOKEN:-}" ]; then
            echo "$DOCKERHUB_TOKEN" | docker login "$REGISTRY" --username "$DOCKERHUB_USERNAME" --password-stdin
        else
            print_warning "DOCKERHUB_USERNAME or DOCKERHUB_TOKEN not set, attempting interactive login..."
            docker login "$REGISTRY"
        fi
        
        print_status "Docker Hub login successful"
    fi
}

build_image() {
    local version="$1"
    local platforms="$2"
    local action="$3"  # "push" or "load"
    
    print_dream "Building WhisperEngine (Dream of the Endless) Docker image..."
    print_info "Image: $IMAGE_NAME:$version"
    print_info "Platforms: $platforms"
    print_info "Target: $TARGET"
    print_info "Action: $action"
    
    # Build command components
    local build_cmd=(
        docker buildx build
        --file "$DOCKERFILE"
        --target "$TARGET"
        --platform "$platforms"
        --tag "$IMAGE_NAME:$version"
        --build-arg BUILDKIT_INLINE_CACHE=1
    )
    
    # Add latest tag if version is not latest and we're pushing
    if [ "$version" != "latest" ] && [ "$action" = "push" ]; then
        build_cmd+=(--tag "$IMAGE_NAME:latest")
    fi
    
    # Add cache configuration (matches GitHub Actions)
    if [ "$USE_CACHE" = true ]; then
        build_cmd+=(--cache-from type=local,src=/tmp/.buildx-cache)
        build_cmd+=(--cache-to type=local,dest=/tmp/.buildx-cache-new,mode=max)
    fi
    
    # Add no-cache flag if requested
    if [ "$NO_CACHE" = true ]; then
        build_cmd+=(--no-cache)
    fi
    
    # Add push or load
    if [ "$action" = "push" ]; then
        build_cmd+=(--push)
    else
        build_cmd+=(--load)
    fi
    
    # Add build context
    build_cmd+=(.)
    
    # Execute build
    if [ "$DRY_RUN" = true ]; then
        print_info "DRY RUN - Would execute:"
        echo "${build_cmd[*]}"
    else
        print_info "Executing build..."
        "${build_cmd[@]}"
        
        # Move cache (if using cache)
        if [ "$USE_CACHE" = true ] && [ "$action" = "push" ]; then
            rm -rf /tmp/.buildx-cache
            mv /tmp/.buildx-cache-new /tmp/.buildx-cache 2>/dev/null || true
        fi
    fi
}

# =============================================================================
# Main Script
# =============================================================================

# Default options
FAST=false
MULTI=true
TEST=false
DEV=false
DRY_RUN=false
NO_CACHE=false
USE_CACHE=true
PUSH=true
VERSION=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -f|--fast)
            FAST=true
            MULTI=false
            shift
            ;;
        -m|--multi)
            MULTI=true
            FAST=false
            shift
            ;;
        -t|--test)
            TEST=true
            PUSH=false
            shift
            ;;
        -d|--dev)
            DEV=true
            TARGET="development"
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --no-cache)
            NO_CACHE=true
            USE_CACHE=false
            shift
            ;;
        -*)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
        *)
            VERSION="$1"
            shift
            ;;
    esac
done

# Banner
echo ""
print_dream "🌙 WhisperEngine Local Docker Build Script"
print_dream "Dream of the Endless awaits in the realm of containers..."
echo ""

# Load environment and check dependencies
load_environment
check_dependencies
validate_dockerfile

# Determine version
if [ -z "$VERSION" ]; then
    VERSION=$(get_version)
    print_info "Auto-detected version: $VERSION"
else
    print_info "Using specified version: $VERSION"
fi

# Determine platforms
if [ "$FAST" = true ]; then
    PLATFORMS="$SINGLE_PLATFORM"
    print_info "Fast build mode: single platform ($PLATFORMS)"
elif [ "$MULTI" = true ]; then
    PLATFORMS="$MULTI_PLATFORM"
    print_info "Multi-platform build mode: ($PLATFORMS)"
fi

# Set action
if [ "$TEST" = true ]; then
    ACTION="load"
    print_info "Test mode: building locally (no push)"
else
    ACTION="push"
    if [ "$PUSH" = true ]; then
        print_info "Production mode: will push to Docker Hub"
    fi
fi

# Setup buildx (only for multi-platform or if not using default builder)
if [ "$MULTI" = true ] || [ "$FAST" = false ]; then
    setup_buildx
fi

# Login to Docker Hub if pushing
if [ "$PUSH" = true ]; then
    docker_login
fi

# Build the image
print_info "Starting build process..."
build_image "$VERSION" "$PLATFORMS" "$ACTION"

# Success message
echo ""
if [ "$TEST" = true ]; then
    print_status "✨ Local build completed successfully!"
    print_info "Test your image with:"
    print_info "  docker run --rm -it $IMAGE_NAME:$VERSION python validate_config.py"
else
    print_status "✨ Build and push completed successfully!"
    print_info "Image available at: $IMAGE_NAME:$VERSION"
    print_info "Users can now run:"
    print_info "  docker pull $IMAGE_NAME:$VERSION"
fi

print_dream "🎭 Dream has woven your creation into the fabric of the Docker realm..."
echo ""