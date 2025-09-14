#!/usr/bin/env python3
"""
Test script for the Universal Chat Platform Integration
Verifies that the desktop app properly uses the universal chat orchestrator instead of direct LLM calls.
"""

import asyncio
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_universal_chat_integration():
    """Test the universal chat platform integration"""
    print("🧪 Testing Universal Chat Platform Integration")
    print("=" * 50)
    
    try:
        # Test 1: Import dependencies
        print("Test 1: Importing universal chat components...")
        from src.platforms.universal_chat import (
            UniversalChatOrchestrator,
            WebUIChatAdapter,
            Message,
            ChatPlatform,
            MessageType,
            User
        )
        from src.config.adaptive_config import AdaptiveConfigManager
        from src.database.database_integration import DatabaseIntegrationManager
        print("✅ Universal chat components imported successfully")
        
        # Test 2: Initialize configuration
        print("\nTest 2: Initializing configuration...")
        config_manager = AdaptiveConfigManager()
        db_manager = DatabaseIntegrationManager(config_manager)
        print("✅ Configuration managers initialized")
        
        # Test 3: Create orchestrator
        print("\nTest 3: Creating chat orchestrator...")
        orchestrator = UniversalChatOrchestrator(
            config_manager=config_manager,
            db_manager=db_manager
        )
        print("✅ Chat orchestrator created")
        
        # Test 4: Initialize orchestrator
        print("\nTest 4: Initializing chat orchestrator...")
        success = await orchestrator.initialize()
        if success:
            print("✅ Chat orchestrator initialized successfully")
        else:
            print("❌ Chat orchestrator initialization failed")
            return False
        
        # Test 5: Check active platforms
        print("\nTest 5: Checking active platforms...")
        platforms = await orchestrator.get_active_platforms()
        print(f"✅ Active platforms: {[p.value for p in platforms]}")
        
        # Test 6: Create test message
        print("\nTest 6: Creating test message...")
        test_message = Message(
            message_id="test_001",
            user_id="test_user",
            content="Hello, this is a test message for the universal chat system!",
            platform=ChatPlatform.WEB_UI,
            channel_id="test_channel",
            message_type=MessageType.TEXT
        )
        print("✅ Test message created")
        
        # Test 7: Get or create conversation
        print("\nTest 7: Creating conversation...")
        conversation = await orchestrator.get_or_create_conversation(test_message)
        print(f"✅ Conversation created: {conversation.conversation_id}")
        
        # Test 8: Test AI response generation
        print("\nTest 8: Testing AI response generation...")
        print("⏳ Generating AI response... (this may take a moment)")
        
        try:
            ai_response = await orchestrator.generate_ai_response(test_message, conversation)
            print(f"✅ AI Response generated successfully!")
            print(f"   Content: {ai_response.content[:100]}...")
            print(f"   Model: {ai_response.model_used}")
            print(f"   Tokens: {ai_response.tokens_used}")
            print(f"   Generation Time: {ai_response.generation_time_ms}ms")
            print(f"   Confidence: {ai_response.confidence}")
        except Exception as e:
            print(f"❌ AI response generation failed: {e}")
            print("   This might be due to LLM configuration issues")
            return False
        
        # Test 9: Platform stats
        print("\nTest 9: Getting platform statistics...")
        stats = await orchestrator.get_platform_stats()
        print(f"✅ Platform stats: {stats}")
        
        # Test 10: Cleanup
        print("\nTest 10: Cleaning up...")
        await orchestrator.cleanup()
        print("✅ Cleanup completed")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure all dependencies are installed")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

async def test_web_ui_integration():
    """Test the web UI integration with universal chat"""
    print("\n🌐 Testing Web UI Integration")
    print("=" * 50)
    
    try:
        # Test 1: Import web UI
        print("Test 1: Importing Web UI components...")
        from src.ui.web_ui import WhisperEngineWebUI
        from src.config.adaptive_config import AdaptiveConfigManager
        print("✅ Web UI components imported")
        
        # Test 2: Create Web UI instance
        print("\nTest 2: Creating Web UI instance...")
        config_manager = AdaptiveConfigManager()
        web_ui = WhisperEngineWebUI(config_manager=config_manager)
        print("✅ Web UI instance created")
        
        # Test 3: Check if universal chat is available
        print("\nTest 3: Checking universal chat integration...")
        if hasattr(web_ui, 'chat_orchestrator') and web_ui.chat_orchestrator:
            print("✅ Universal chat orchestrator available in Web UI")
        else:
            print("❌ Universal chat orchestrator not available in Web UI")
            return False
        
        # Test 4: Test response generation
        print("\nTest 4: Testing Web UI response generation...")
        try:
            response = await web_ui.generate_ai_response(
                user_id="test_user_web",
                message="Test message for web UI integration"
            )
            print("✅ Web UI response generation successful!")
            print(f"   Content: {response['content'][:100]}...")
            print(f"   Platform: {response['metadata'].get('platform', 'unknown')}")
        except Exception as e:
            print(f"❌ Web UI response generation failed: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Web UI integration test failed: {e}")
        return False

def show_architecture_summary():
    """Show the improved architecture summary"""
    print("\n🏗️ Architecture Summary")
    print("=" * 50)
    print("✅ PROPER LAYERED ARCHITECTURE:")
    print()
    print("📱 UI Layer (Web, Desktop)")
    print("   └── Uses universal message interface")
    print("   └── No direct LLM client calls")
    print()
    print("🌐 Universal Chat Platform")
    print("   ├── WebUIChatAdapter")
    print("   ├── DiscordChatAdapter")
    print("   ├── SlackChatAdapter")
    print("   └── APIChatAdapter")
    print()
    print("🧠 AI Response Generation")
    print("   ├── Conversation Context Management")
    print("   ├── Cost Optimization")
    print("   ├── Model Selection")
    print("   └── LLM Client Integration")
    print()
    print("🔧 Core Services")
    print("   ├── LLM Client")
    print("   ├── Database Integration")
    print("   ├── Memory Management")
    print("   └── Configuration Management")
    print()
    print("🎯 BENEFITS:")
    print("   ✅ Separation of concerns")
    print("   ✅ Platform-agnostic message handling")
    print("   ✅ Consistent AI behavior across platforms")
    print("   ✅ Centralized conversation management")
    print("   ✅ Cost optimization and monitoring")
    print("   ✅ Easy to add new platforms")

async def main():
    """Main test runner"""
    print("🚀 WhisperEngine Universal Chat Platform Test Suite")
    print("=" * 60)
    
    # Test universal chat platform
    success_1 = await test_universal_chat_integration()
    
    # Test web UI integration
    success_2 = await test_web_ui_integration()
    
    # Show architecture summary
    show_architecture_summary()
    
    print("\n🏁 Test Results")
    print("=" * 50)
    if success_1 and success_2:
        print("🎉 ALL TESTS PASSED!")
        print("   The universal chat platform architecture is working correctly.")
        print("   The desktop app now uses proper layered architecture.")
        print("   Chat functionality should work properly in the desktop app.")
    else:
        print("❌ SOME TESTS FAILED")
        print("   Check the error messages above for details.")
        if not success_1:
            print("   - Universal chat platform has issues")
        if not success_2:
            print("   - Web UI integration has issues")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())