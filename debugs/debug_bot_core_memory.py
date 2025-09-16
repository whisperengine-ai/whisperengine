#!/usr/bin/env python3
"""
Debug bot core memory manager to see what's actually available
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


async def debug_bot_core():
    """Debug what memory manager is available in bot core"""
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

        # Debug memory manager
        logger.info("🧠 Checking memory manager...")

        if hasattr(bot_core, "memory_manager"):
            memory_manager = bot_core.memory_manager
            logger.info(f"✅ Memory manager found: {type(memory_manager)}")

            if memory_manager is not None:
                logger.info(f"📝 Memory manager methods: {dir(memory_manager)}")

                # Test if it has the methods we need
                methods_to_check = [
                    "search_memories",
                    "store_conversation",
                    "get_user_conversations",
                ]
                for method in methods_to_check:
                    if hasattr(memory_manager, method):
                        logger.info(f"✅ Has method: {method}")
                    else:
                        logger.warning(f"❌ Missing method: {method}")
            else:
                logger.warning("⚠️ Memory manager is None")
        else:
            logger.warning("❌ No memory_manager attribute found on bot_core")

        # Check other components
        logger.info("🔍 Checking other bot core components...")
        components = ["llm_client", "safe_memory_manager", "database_manager"]
        for component in components:
            if hasattr(bot_core, component):
                value = getattr(bot_core, component)
                logger.info(f"✅ {component}: {type(value) if value else 'None'}")
            else:
                logger.warning(f"❌ Missing: {component}")

        return True

    except Exception as e:
        logger.error(f"❌ Debug failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Main debug function"""
    logger.info("🧪 Starting bot core debug...")

    success = await debug_bot_core()

    if success:
        logger.info("✅ Debug completed successfully!")
    else:
        logger.error("❌ Debug failed!")

    return success


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
