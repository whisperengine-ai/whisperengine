#!/usr/bin/env python3
"""Simple test to understand Web UI Universal Chat initialization without FastAPI dependencies"""

import logging
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def test_universal_chat_initialization():
    """Test Universal Chat components without FastAPI"""

    try:
        # Test 1: Can we import the Universal Chat components?

        try:
            from src.platforms.universal_chat import (
                UniversalChatOrchestrator,
            )

        except Exception:
            return False

        # Test 2: Can we import the config manager?

        try:
            from src.config.adaptive_config import AdaptiveConfigManager

            config_manager = AdaptiveConfigManager()
        except Exception:
            return False

        # Test 3: Can we import database integration?

        try:
            from src.database.database_integration import DatabaseIntegrationManager

            db_manager = DatabaseIntegrationManager(config_manager)
        except Exception:
            return False

        # Test 4: Can we create Universal Chat Orchestrator?

        try:
            UniversalChatOrchestrator(config_manager=config_manager, db_manager=db_manager)
        except Exception:
            import traceback

            traceback.print_exc()
            return False

        # Test 5: Can we import LLM client?

        try:
            from src.llm.llm_client import LLMClient

            # Test if we can create an instance
            LLMClient()
        except Exception:
            return False

        return True

    except Exception:
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_universal_chat_initialization()
    sys.exit(0 if success else 1)
