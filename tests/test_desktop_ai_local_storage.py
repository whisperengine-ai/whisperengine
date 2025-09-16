#!/usr/bin/env python3
"""
Test script to verify desktop AI functionality with new local storage configuration
"""
import asyncio
import logging
import os
import sys

# Set environment mode at startup
os.environ["ENV_MODE"] = "desktop"

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment early
try:
    from env_manager import load_environment

    if load_environment():
        pass
    else:
        pass
except Exception:
    pass

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


async def test_desktop_ai_with_local_storage():
    """Test the NativeAIService with local storage configuration"""

    try:
        from src.core.native_ai_service import NativeAIService

        # Create service instance
        ai_service = NativeAIService()

        # Test initialization
        success = await ai_service.initialize()


        if ai_service.universal_chat:
            pass

        if success:

            # Test multiple conversations
            test_messages = [
                "Hello! Can you hear me?",
                "What's your name and what can you do?",
                "Remember that I like cats. Can you tell me about cat behavior?",
                "What did I just tell you about my preferences?",
            ]


            for _i, message in enumerate(test_messages, 1):
                try:
                    response = await ai_service.process_message_async(message)

                    # Check response metadata
                    if hasattr(response, "emotions") and response.emotions:
                        pass
                    if hasattr(response, "suggestions") and response.suggestions:
                        pass

                except Exception:
                    pass

            # Test conversation info

            for _conv_id, _conv_info in ai_service.conversations.items():
                pass

        else:
            pass

    except Exception:
        import traceback

        traceback.print_exc()


def check_environment_config():
    """Check what environment variables are loaded"""

    important_vars = [
        "ENV_MODE",
        "USE_CHROMADB_HTTP",
        "USE_LOCAL_VECTOR_STORAGE",
        "USE_REDIS_CACHE",
        "USE_LOCAL_MEMORY_CACHE",
        "USE_SQLITE_DATABASE",
        "USE_POSTGRESQL",
        "ENABLE_GRAPH_DATABASE",
        "DESKTOP_MODE",
    ]

    for var in important_vars:
        os.getenv(var, "NOT SET")


async def main():
    """Main test function"""

    check_environment_config()
    await test_desktop_ai_with_local_storage()



if __name__ == "__main__":
    asyncio.run(main())
