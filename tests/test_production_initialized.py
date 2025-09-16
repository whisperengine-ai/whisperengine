#!/usr/bin/env python3
"""
Test production system with properly initialized bot core
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_production_with_initialized_bot():
    """Test production system with fully initialized bot core"""
    try:
        # Import necessary components
        from env_manager import load_environment
        from src.core.bot import DiscordBotCore

        logger.info("🔧 Loading environment configuration...")
        if not load_environment():
            logger.error("❌ Failed to load environment configuration")
            return False

        logger.info("⚙️ Initializing Discord bot core...")
        bot_core = DiscordBotCore(debug_mode=True)

        # This is the missing step - we need to initialize all components!
        logger.info("🚀 Initializing ALL bot components...")
        bot_core.initialize_all()

        # Now test production system
        logger.info("🧪 Testing production system...")

        # Check if memory manager is now available
        if bot_core.memory_manager:
            logger.info(f"✅ Memory manager available: {type(bot_core.memory_manager)}")
        else:
            logger.warning("❌ Memory manager still None after initialize_all()")

        # Check production adapter
        if bot_core.production_adapter:
            logger.info(f"✅ Production adapter available: {type(bot_core.production_adapter)}")

            # Initialize production mode
            logger.info("🚀 Initializing production mode...")
            success = await bot_core.production_adapter.initialize_production_mode()

            if success:
                logger.info("✅ Production mode initialized successfully!")
            else:
                logger.warning("⚠️ Production mode initialization failed")

        else:
            logger.warning("❌ No production adapter available")

        return True

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Main test function"""
    logger.info("🧪 Testing production system with initialized bot core...")

    success = await test_production_with_initialized_bot()

    if success:
        logger.info("✅ Test completed successfully!")
    else:
        logger.error("❌ Test failed!")

    return success


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
