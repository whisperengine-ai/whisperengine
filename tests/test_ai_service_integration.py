#!/usr/bin/env python3
"""
Test AI Service Integration
Simple test to verify the AI service can process messages correctly
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


async def test_ai_service():
    """Test the AI service integration"""

    # Configure logging
    logging.basicConfig(level=logging.INFO)

    try:
        from src.core.native_ai_service import NativeAIService

        # Create AI service with test user ID
        ai_service = NativeAIService(user_id="test-user-123")

        # Start the event loop
        ai_service.start_event_loop()

        # Initialize the service
        success = await ai_service.initialize()
        if success:
            pass
        else:
            return False

        # Test message processing
        test_message = "Hello! Can you tell me about yourself?"

        response = await ai_service.process_message_async(test_message)


        if response.message_type == "error":
            return False
        else:
            return True

    except ImportError:
        return False
    except Exception:
        return False
    finally:
        # Clean up
        if "ai_service" in locals():
            ai_service.stop_event_loop()


if __name__ == "__main__":
    success = asyncio.run(test_ai_service())
    if success:
        pass
    else:
        pass
    sys.exit(0 if success else 1)
