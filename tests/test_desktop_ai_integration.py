#!/usr/bin/env python3
"""
Test script to identify what's preventing full AI functionality in the desktop app
"""
import asyncio
import logging
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


async def test_native_ai_service():
    """Test the NativeAIService initialization and identify issues"""

    try:
        from src.core.native_ai_service import NativeAIService

        # Create service instance
        ai_service = NativeAIService()

        # Test initialization
        success = await ai_service.initialize()

        if success:

            # Test a simple message
            await ai_service.process_message_async("Hello, can you hear me?")

        else:
            pass

        # Check what components are available

        if ai_service.universal_chat:
            pass

    except Exception:
        import traceback

        traceback.print_exc()


async def test_universal_chat_direct():
    """Test UniversalChatOrchestrator directly"""

    try:
        from src.config.adaptive_config import AdaptiveConfigManager
        from src.database.database_integration import DatabaseIntegrationManager
        from src.platforms.universal_chat import UniversalChatOrchestrator

        # Initialize components
        config_manager = AdaptiveConfigManager()
        db_manager = DatabaseIntegrationManager(config_manager)

        # Create orchestrator
        orchestrator = UniversalChatOrchestrator(
            config_manager=config_manager,
            db_manager=db_manager,
            bot_core=None,
            use_enhanced_core=True,
        )

        # Test initialization
        success = await orchestrator.initialize()

        if success:
            # Test message processing
            import uuid

            from src.platforms.universal_chat import ChatPlatform, Message, MessageType

            message = Message(
                message_id=str(uuid.uuid4()),
                user_id="test_user",
                content="Hello, this is a test",
                message_type=MessageType.TEXT,
                platform=ChatPlatform.WEB_UI,
                channel_id="test_channel",
            )

            context = orchestrator.build_conversation_context("test_user", "test_channel", "Hello")
            await orchestrator.generate_ai_response(message, context)

    except Exception:
        import traceback

        traceback.print_exc()


async def main():
    """Main test function"""

    await test_native_ai_service()
    await test_universal_chat_direct()


if __name__ == "__main__":
    asyncio.run(main())
