#!/usr/bin/env python3
"""
Test script to identify what's preventing full AI functionality in the desktop app
"""
import os
import sys
import asyncio
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


async def test_native_ai_service():
    """Test the NativeAIService initialization and identify issues"""
    print("🔍 Testing Native AI Service initialization...")

    try:
        from src.core.native_ai_service import NativeAIService

        # Create service instance
        ai_service = NativeAIService()
        print("✅ NativeAIService created")

        # Test initialization
        success = await ai_service.initialize()
        print(f"Initialization result: {success}")

        if success:
            print("✅ AI Service initialized successfully")

            # Test a simple message
            response = await ai_service.process_message_async("Hello, can you hear me?")
            print(f"Test response: {response.content}")

        else:
            print("❌ AI Service initialization failed")

        # Check what components are available
        print("\n🔍 Component Status:")
        print(f"  - is_initialized: {ai_service.is_initialized}")
        print(f"  - universal_chat: {ai_service.universal_chat is not None}")
        print(f"  - enhanced_core: {getattr(ai_service, 'enhanced_core', None) is not None}")

        if ai_service.universal_chat:
            print(f"  - universal_chat.bot_core: {ai_service.universal_chat.bot_core is not None}")

    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback

        traceback.print_exc()


async def test_universal_chat_direct():
    """Test UniversalChatOrchestrator directly"""
    print("\n🔍 Testing Universal Chat Orchestrator directly...")

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

        print("✅ UniversalChatOrchestrator created")

        # Test initialization
        success = await orchestrator.initialize()
        print(f"Orchestrator initialization: {success}")

        if success:
            # Test message processing
            from src.platforms.universal_chat import Message, MessageType, ChatPlatform
            import uuid

            message = Message(
                message_id=str(uuid.uuid4()),
                user_id="test_user",
                content="Hello, this is a test",
                message_type=MessageType.TEXT,
                platform=ChatPlatform.WEB_UI,
                channel_id="test_channel",
            )

            context = orchestrator.build_conversation_context("test_user", "test_channel", "Hello")
            response = await orchestrator.generate_ai_response(message, context)
            print(f"Test response: {response.content}")

    except Exception as e:
        print(f"❌ Error testing orchestrator: {e}")
        import traceback

        traceback.print_exc()


async def main():
    """Main test function"""
    print("🚀 WhisperEngine Desktop AI Integration Test")
    print("=" * 50)

    await test_native_ai_service()
    await test_universal_chat_direct()

    print("\n✅ Test completed")


if __name__ == "__main__":
    asyncio.run(main())
