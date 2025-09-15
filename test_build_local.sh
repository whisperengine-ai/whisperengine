#!/bin/bash
# Local Build Script for WhisperEngine
# Tests the same build process that GitHub Actions will use

set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔨 WhisperEngine Local Build Test${NC}"
echo "This script tests the same build process used by GitHub Actions"
echo ""

# Detect platform
PLATFORM=""
if [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="darwin"
    PLATFORM_NAME="macOS"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    PLATFORM="linux" 
    PLATFORM_NAME="Linux"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    PLATFORM="windows"
    PLATFORM_NAME="Windows"
else
    echo "❌ Unsupported platform: $OSTYPE"
    exit 1
fi

echo -e "${BLUE}📋 Detected platform:${NC} $PLATFORM_NAME"
echo ""

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo -e "${YELLOW}⚠️  Virtual environment not detected. Activating .venv...${NC}"
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
    elif [ -f ".venv/Scripts/activate" ]; then
        source .venv/Scripts/activate
    else
        echo "❌ Virtual environment not found. Please run: python -m venv .venv"
        exit 1
    fi
fi

# Check dependencies
echo -e "${BLUE}🔍 Checking dependencies...${NC}"
if ! python -c "import PyInstaller" 2>/dev/null; then
    echo "Installing PyInstaller..."
    pip install pyinstaller
fi

# Build for current platform
echo -e "${BLUE}🔨 Building WhisperEngine for $PLATFORM_NAME...${NC}"
python build_cross_platform.py build --platform $PLATFORM

# Check if build succeeded
if [ -d "dist" ]; then
    echo ""
    echo -e "${GREEN}✅ Build completed successfully!${NC}"
    echo ""
    echo -e "${BLUE}📦 Build artifacts:${NC}"
    ls -la dist/
    
    # Create distribution package
    cd dist
    VERSION="local-$(date +%Y%m%d-%H%M%S)"
    
    if [[ "$PLATFORM" == "darwin" ]] && [ -d "WhisperEngine.app" ]; then
        echo ""
        echo -e "${BLUE}📦 Creating macOS distribution...${NC}"
        zip -r "WhisperEngine-macOS-$VERSION.zip" WhisperEngine.app
        echo "Created: WhisperEngine-macOS-$VERSION.zip"
        
    elif [[ "$PLATFORM" == "windows" ]] && [ -f "WhisperEngine.exe" ]; then
        echo ""
        echo -e "${BLUE}📦 Creating Windows distribution...${NC}"
        zip "WhisperEngine-Windows-$VERSION.zip" WhisperEngine.exe
        echo "Created: WhisperEngine-Windows-$VERSION.zip"
        
    elif [[ "$PLATFORM" == "linux" ]] && [ -f "WhisperEngine" ]; then
        echo ""
        echo -e "${BLUE}📦 Creating Linux distribution...${NC}"
        tar -czf "WhisperEngine-Linux-$VERSION.tar.gz" WhisperEngine
        echo "Created: WhisperEngine-Linux-$VERSION.tar.gz"
    fi
    
    cd ..
    
    echo ""
    echo -e "${GREEN}🎉 Local build test completed successfully!${NC}"
    echo ""
    echo -e "${BLUE}📝 Next steps:${NC}"
    echo "1. Test the executable in dist/ folder"
    echo "2. Commit your changes and push"
    echo "3. Create a git tag to trigger automated builds:"
    echo "   git tag v1.0.0"
    echo "   git push origin v1.0.0"
    echo ""
    echo -e "${BLUE}🚀 Automated builds will create:${NC}"
    echo "- macOS: .app and .dmg files"
    echo "- Windows: .exe and .zip files"  
    echo "- Linux: executable and .tar.gz files"
    echo "- All architectures: x64, arm64 (where supported)"
    
else
    echo ""
    echo "❌ Build failed - no dist folder created"
    exit 1
fi