#!/usr/bin/env python3
"""
Test Desktop App Startup
Quick test to see if the desktop app can start with local database integration.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Override environment for local mode
os.environ["WHISPERENGINE_DATABASE_TYPE"] = "sqlite"
os.environ["WHISPERENGINE_MODE"] = "desktop"
os.environ["LOG_LEVEL"] = "INFO"

from src.database.local_database_integration import LocalDatabaseIntegrationManager

from src.config.adaptive_config import AdaptiveConfigManager


async def test_desktop_app_startup():
    """Test if desktop app components can initialize properly"""

    try:
        # Test 1: Configuration Manager
        config_manager = AdaptiveConfigManager()
        config_manager.get_deployment_info()

        # Test 2: Local Database Integration
        db_integration = LocalDatabaseIntegrationManager(config_manager)

        init_success = await db_integration.initialize()

        if init_success:

            # Test health check
            await db_integration.get_comprehensive_health_check()

            # Test storage statistics
            await db_integration.get_storage_statistics()

            # Test basic operations

            # Test vector storage
            db_integration.get_vector_storage()
            test_embedding = [0.1] * 384

            await db_integration.store_conversation_embedding(
                user_id="test_user",
                content="Hello from desktop app test!",
                embedding=test_embedding,
                metadata={"test": True},
            )

            # Test graph storage
            await db_integration.create_user_in_graph(
                user_id="test_user", username="desktop_tester", display_name="Desktop App Tester"
            )

            # Cleanup
            await db_integration.cleanup()

            return True

        else:
            return False

    except Exception:
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Main test function"""
    success = await test_desktop_app_startup()

    if success:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
