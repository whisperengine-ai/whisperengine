#!/bin/bash
# Quick rebuild script for multi-platform WhisperEngine containers
# This rebuilds and pushes both main container and Web UI with multi-platform support

set -e

echo "🚀 WhisperEngine Multi-Platform Rebuild"
echo "========================================"
echo ""

# Check for required environment variables
if [[ -z "$DOCKERHUB_USERNAME" ]]; then
    echo "❌ ERROR: DOCKERHUB_USERNAME not set"
    echo "   Set it with: export DOCKERHUB_USERNAME='whisperengine'"
    exit 1
fi

if [[ -z "$DOCKERHUB_TOKEN" ]]; then
    echo "❌ ERROR: DOCKERHUB_TOKEN not set"
    echo "   Set it with: export DOCKERHUB_TOKEN='your_token_here'"
    exit 1
fi

# Get version (default to v1.0.2)
VERSION="${1:-v1.0.2}"

echo "📋 Configuration:"
echo "   Username: $DOCKERHUB_USERNAME"
echo "   Version:  $VERSION"
echo "   Platforms: linux/amd64, linux/arm64"
echo ""

read -p "Continue with multi-platform build and push? (y/N): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cancelled"
    exit 1
fi

echo ""
echo "🔧 Running multi-platform build..."
echo ""

# Run the updated push script
./push-to-dockerhub.sh "$DOCKERHUB_USERNAME" "$VERSION"

echo ""
echo "✅ Multi-platform rebuild complete!"
echo ""
echo "🧪 Verify multi-platform support:"
echo "   docker buildx imagetools inspect ${DOCKERHUB_USERNAME}/whisperengine:${VERSION}"
echo ""
echo "🐧 Test on AMD64:"
echo "   docker run --rm --platform linux/amd64 ${DOCKERHUB_USERNAME}/whisperengine:${VERSION} python -c \"print('AMD64 OK')\""
echo ""
echo "🍎 Test on ARM64:"
echo "   docker run --rm --platform linux/arm64 ${DOCKERHUB_USERNAME}/whisperengine:${VERSION} python -c \"print('ARM64 OK')\""
echo ""
