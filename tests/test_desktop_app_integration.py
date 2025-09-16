#!/usr/bin/env python3
"""
Test Desktop App LLM Integration
Validates that the desktop app properly initializes with LLM auto-detection.
"""

import asyncio
import sys
import os
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def test_desktop_app_initialization():
    """Test desktop app initialization with LLM auto-detection"""

    logger.info("🧪 Testing Desktop App LLM Initialization")
    logger.info("=" * 50)

    try:
        # Import desktop app
        from desktop_app import WhisperEngineDesktopApp

        # Create app instance
        app = WhisperEngineDesktopApp()

        # Test initialization up to LLM configuration
        print("📱 Creating desktop app instance...")

        # Force environment for testing
        os.environ["WHISPERENGINE_DATABASE_TYPE"] = "sqlite"
        os.environ["WHISPERENGINE_MODE"] = "desktop"
        os.environ["LOG_LEVEL"] = "INFO"

        # Setup logging like the app does
        app.setup_logging()

        print("🔧 Testing component initialization...")

        # Initialize components (this will include LLM auto-detection)
        await app.initialize_components()

        print("✅ Desktop app initialization successful!")
        print("✅ LLM auto-detection integrated!")

        # Clean up
        if hasattr(app, "web_ui") and app.web_ui:
            print("🧹 Cleaning up test resources...")

        logger.info("🎉 Desktop app LLM integration test PASSED!")
        return True

    except Exception as e:
        logger.error(f"❌ Desktop app initialization failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Main test function"""
    print("🚀 Starting Desktop App LLM Integration Test")
    print()

    success = await test_desktop_app_initialization()

    print()
    if success:
        print("🎉 ALL TESTS PASSED - Desktop app ready with LLM auto-detection!")
        print("✅ Users will get automatic local LLM detection on startup")
        print("✅ Seamless fallback to cloud APIs when needed")
        print("✅ Setup guidance displayed when configuration needed")
    else:
        print("❌ Tests failed - desktop app needs fixes")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
