#!/usr/bin/env python3
"""
Test Complete Chat Interface Flow
Verify that the chat interface can send messages and receive AI responses
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


async def test_chat_flow():
    """Test the complete chat interface flow"""

    try:
        from src.core.native_ai_service import NativeAIService
        from universal_native_app import WhisperEngineUniversalApp

        # Test AI service integration
        ai_service = NativeAIService(user_id="test-chat-user")
        ai_service.start_event_loop()

        # Initialize AI service
        success = await ai_service.initialize()
        if not success:
            return False


        # Test message processing
        test_messages = [
            "Hello! What can you help me with?",
            "Can you explain what WhisperEngine is?",
            "How does the memory system work?",
        ]

        for i, message in enumerate(test_messages, 1):

            response = await ai_service.process_message_async(message)

            if response.message_type == "error":
                return False


            # Test conversation continuity
            if i > 1:
                # Check if response shows awareness of previous messages
                if any(
                    word in response.content.lower()
                    for word in ["previous", "earlier", "before", "context"]
                ):
                    pass


        # Test conversation info
        conversations = ai_service.get_conversations()

        if conversations:
            conv = conversations[0]

        return True

    except ImportError:
        return False
    except Exception:
        return False
    finally:
        if "ai_service" in locals():
            ai_service.stop_event_loop()


def test_chat_ui_components():
    """Test that the chat UI components can be created"""

    try:
        # Test that PySide6 components work
        from PySide6.QtCore import QCoreApplication
        from PySide6.QtWidgets import QApplication

        # Create minimal application for testing
        if not QCoreApplication.instance():
            QApplication([])

        # Test UI component creation
        from universal_native_app import WhisperEngineUniversalApp

        # Create app instance (without showing)
        chat_app = WhisperEngineUniversalApp()

        # Test that required components exist
        if hasattr(chat_app, "chat_display") and hasattr(chat_app, "message_input"):
            pass
        else:
            return False

        # Test tab widget structure
        if hasattr(chat_app, "tab_widget") and hasattr(chat_app, "logs_widget"):
            pass
        else:
            return False

        return True

    except ImportError:
        return False
    except Exception:
        return False


if __name__ == "__main__":

    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Test AI chat flow
    success1 = asyncio.run(test_chat_flow())

    # Test UI components
    success2 = test_chat_ui_components()

    overall_success = success1 and success2

    if overall_success:
        pass
    else:
        pass

    sys.exit(0 if overall_success else 1)
