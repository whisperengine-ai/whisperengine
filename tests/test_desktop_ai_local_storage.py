#!/usr/bin/env python3
"""
Test script to verify desktop AI functionality with new local storage configuration
"""
import os
import sys
import asyncio
import logging

# Set environment mode at startup
os.environ["ENV_MODE"] = "desktop"

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment early
try:
    from env_manager import load_environment

    if load_environment():
        print("✅ Desktop environment configuration loaded successfully")
    else:
        print("⚠️ Environment loading failed, but continuing...")
except Exception as e:
    print(f"❌ Environment loading error: {e}")

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


async def test_desktop_ai_with_local_storage():
    """Test the NativeAIService with local storage configuration"""
    print("🔍 Testing Desktop AI with Local Storage Configuration...")
    print("=" * 60)

    try:
        from src.core.native_ai_service import NativeAIService

        # Create service instance
        print("📱 Creating NativeAIService...")
        ai_service = NativeAIService()

        # Test initialization
        print("🚀 Initializing AI service...")
        success = await ai_service.initialize()

        print(f"\n📊 Initialization Status:")
        print(f"  • Success: {success}")
        print(f"  • is_initialized: {ai_service.is_initialized}")
        print(f"  • universal_chat available: {ai_service.universal_chat is not None}")
        print(
            f"  • enhanced_core available: {getattr(ai_service, 'enhanced_core', None) is not None}"
        )

        if ai_service.universal_chat:
            print(f"  • universal_chat.bot_core: {ai_service.universal_chat.bot_core is not None}")

        if success:
            print("\n✅ AI Service initialized successfully!")

            # Test multiple conversations
            test_messages = [
                "Hello! Can you hear me?",
                "What's your name and what can you do?",
                "Remember that I like cats. Can you tell me about cat behavior?",
                "What did I just tell you about my preferences?",
            ]

            print(f"\n💬 Testing conversation with {len(test_messages)} messages...")

            for i, message in enumerate(test_messages, 1):
                print(f"\n📤 Message {i}: {message}")
                try:
                    response = await ai_service.process_message_async(message)
                    print(f"📥 Response {i}: {response.content}")

                    # Check response metadata
                    if hasattr(response, "emotions") and response.emotions:
                        print(f"   🎭 Emotions: {response.emotions}")
                    if hasattr(response, "suggestions") and response.suggestions:
                        print(f"   💡 Suggestions: {response.suggestions}")

                except Exception as e:
                    print(f"❌ Error processing message {i}: {e}")

            # Test conversation info
            print(f"\n📚 Conversation Management:")
            print(f"  • Current conversation ID: {ai_service.current_conversation_id}")
            print(f"  • Total conversations: {len(ai_service.conversations)}")

            for conv_id, conv_info in ai_service.conversations.items():
                print(
                    f"  • {conv_id}: {conv_info.message_count} messages, last active: {conv_info.last_active}"
                )

        else:
            print("❌ AI Service initialization failed")
            print("Check the logs above for specific error details")

    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback

        traceback.print_exc()


def check_environment_config():
    """Check what environment variables are loaded"""
    print("\n🔧 Environment Configuration Check:")
    print("=" * 40)

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
        value = os.getenv(var, "NOT SET")
        print(f"  • {var}: {value}")


async def main():
    """Main test function"""
    print("🖥️ WhisperEngine Desktop AI Local Storage Test")
    print("=" * 50)

    check_environment_config()
    await test_desktop_ai_with_local_storage()

    print("\n✅ Test completed")


if __name__ == "__main__":
    asyncio.run(main())
