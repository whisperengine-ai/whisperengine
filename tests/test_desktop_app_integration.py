#!/usr/bin/env python3
"""
Test Desktop App LLM Integration
Validates that the desktop app properly initializes with LLM auto-detection.
"""

import asyncio
import logging
import os
import sys
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

        # Force environment for testing
        os.environ["WHISPERENGINE_DATABASE_TYPE"] = "sqlite"
        os.environ["WHISPERENGINE_MODE"] = "desktop"
        os.environ["LOG_LEVEL"] = "INFO"

        # Setup logging like the app does
        app.setup_logging()


        # Initialize components (this will include LLM auto-detection)
        await app.initialize_components()


        # Clean up
        if hasattr(app, "web_ui") and app.web_ui:
            pass

        logger.info("🎉 Desktop app LLM integration test PASSED!")
        return True

    except Exception as e:
        logger.error(f"❌ Desktop app initialization failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Main test function"""

    success = await test_desktop_app_initialization()

    if success:
        pass
    else:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
