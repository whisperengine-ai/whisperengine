#!/usr/bin/env python3
"""
Test Complete Chat Interface Flow
Verify that the chat interface can send messages and receive AI responses
"""

import sys
import asyncio
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

async def test_chat_flow():
    """Test the complete chat interface flow"""
    print("💬 Testing Complete Chat Interface Flow...")
    
    try:
        from src.core.native_ai_service import NativeAIService
        from universal_native_app import WhisperEngineUniversalApp
        
        # Test AI service integration
        print("🤖 Testing AI service...")
        ai_service = NativeAIService(user_id="test-chat-user")
        ai_service.start_event_loop()
        
        # Initialize AI service
        success = await ai_service.initialize()
        if not success:
            print("❌ AI service initialization failed")
            return False
        
        print("✅ AI service initialized")
        
        # Test message processing
        test_messages = [
            "Hello! What can you help me with?",
            "Can you explain what WhisperEngine is?",
            "How does the memory system work?"
        ]
        
        for i, message in enumerate(test_messages, 1):
            print(f"\n💬 Test {i}: Sending message: '{message}'")
            
            response = await ai_service.process_message_async(message)
            
            if response.message_type == "error":
                print(f"❌ Error response: {response.content}")
                return False
            
            print(f"✅ Received response ({len(response.content)} chars)")
            print(f"   Preview: {response.content[:100]}...")
            print(f"   Timestamp: {response.timestamp}")
            
            # Test conversation continuity
            if i > 1:
                # Check if response shows awareness of previous messages
                if any(word in response.content.lower() for word in ["previous", "earlier", "before", "context"]):
                    print("✅ Response shows conversation awareness")
        
        print("\n🔄 Testing conversation management...")
        
        # Test conversation info
        conversations = ai_service.get_conversations()
        print(f"✅ Retrieved {len(conversations)} conversations")
        
        if conversations:
            conv = conversations[0]
            print(f"   Conversation: {conv.title}")
            print(f"   Messages: {conv.message_count}")
            print(f"   Last active: {conv.last_active}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Chat flow test error: {e}")
        return False
    finally:
        if 'ai_service' in locals():
            ai_service.stop_event_loop()
            print("🛑 AI service stopped")

def test_chat_ui_components():
    """Test that the chat UI components can be created"""
    print("\n🖥️ Testing Chat UI Components...")
    
    try:
        # Test that PySide6 components work
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QCoreApplication
        
        # Create minimal application for testing
        if not QCoreApplication.instance():
            app = QApplication([])
        
        # Test UI component creation
        from universal_native_app import WhisperEngineUniversalApp
        
        # Create app instance (without showing)
        chat_app = WhisperEngineUniversalApp()
        print("✅ Chat application instance created")
        
        # Test that required components exist
        if hasattr(chat_app, 'chat_display') and hasattr(chat_app, 'message_input'):
            print("✅ Chat UI components (display and input) are available")
        else:
            print("❌ Chat UI components missing")
            return False
        
        # Test tab widget structure
        if hasattr(chat_app, 'tab_widget') and hasattr(chat_app, 'logs_widget'):
            print("✅ Tab widget structure (chat + logs) is available")
        else:
            print("❌ Tab widget structure incomplete")
            return False
        
        return True
        
    except ImportError as e:
        print(f"❌ UI component import error: {e}")
        return False
    except Exception as e:
        print(f"❌ UI component test error: {e}")
        return False

if __name__ == "__main__":
    print("💬 Chat Interface Integration Test")
    print("=" * 50)
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Test AI chat flow
    success1 = asyncio.run(test_chat_flow())
    
    # Test UI components
    success2 = test_chat_ui_components()
    
    overall_success = success1 and success2
    
    if overall_success:
        print("\n🎉 Chat Interface Integration Test PASSED")
        print("✅ Chat flow, AI responses, and UI components all working")
        print("💡 Try starting the app and testing manual chat interaction:")
        print("   python universal_native_app.py")
    else:
        print("\n❌ Chat Interface Integration Test FAILED")
    
    sys.exit(0 if overall_success else 1)