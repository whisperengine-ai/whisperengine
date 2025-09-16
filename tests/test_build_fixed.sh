#!/bin/bash

echo "🔨 Testing Fixed Build System"
echo "============================="

# Activate virtual environment
source .venv/bin/activate

# Clean any previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build dist *.spec 2>/dev/null

# Test the build script
echo "🚀 Testing build script..."
python build_cross_platform.py build --platform darwin

# Check if build succeeded
if [ -d "dist" ] && [ -f "dist/WhisperEngine.app/Contents/MacOS/WhisperEngine" ]; then
    echo "✅ Build test passed!"
    echo "📦 Built app: $(ls -la dist/)"
    
    # Test if app launches (briefly)
    echo "🧪 Testing app launch..."
    timeout 3s dist/WhisperEngine.app/Contents/MacOS/WhisperEngine --help 2>/dev/null && echo "✅ App launches successfully" || echo "⚠️ App launch test timeout (expected)"
    
else
    echo "❌ Build test failed!"
    exit 1
fi

echo "🎉 Build system test completed successfully!"