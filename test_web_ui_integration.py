#!/usr/bin/env python3
"""
Test script to isolate the web UI AI integration issue.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from env_manager import load_environment
from src.config.adaptive_config import AdaptiveConfigManager
from src.database.database_integration import DatabaseIntegrationManager
from src.llm.llm_client import LLMClient
from src.platforms.universal_chat import (
    UniversalChatOrchestrator, Message, MessageType, 
    ChatPlatform, create_universal_chat_platform
)
from datetime import datetime


async def test_orchestrator_integration():
    """Test the Universal Chat Orchestrator integration"""
    print("🧪 Testing Universal Chat Orchestrator Integration")
    print("=" * 50)
    
    # Load environment
    if not load_environment():
        print("❌ Failed to load environment")
        return
    
    try:
        # Initialize components
        print("🔧 Initializing components...")
        config_manager = AdaptiveConfigManager()
        
        # Try to initialize database manager
        try:
            db_manager = DatabaseIntegrationManager()
            print("✅ Database manager initialized")
        except Exception as e:
            print(f"⚠️ Database manager failed (running without DB): {e}")
            db_manager = None
        
        # Initialize LLM client
        llm_client = LLMClient()
        print(f"✅ LLM client initialized: {llm_client.service_name}")
        
        # Test LLM client directly first
        print("\n📡 Testing LLM client directly...")
        test_messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Integration test successful' if you can read this."}
        ]
        
        try:
            direct_response = llm_client.get_chat_response(test_messages)
            print(f"✅ Direct LLM response: {direct_response}")
        except Exception as e:
            print(f"❌ Direct LLM test failed: {e}")
            return
        
        # Create orchestrator
        print("\n🎭 Testing Universal Chat Orchestrator...")
        if db_manager:
            orchestrator = UniversalChatOrchestrator(config_manager, db_manager, llm_client)
        else:
            # Create with None - the orchestrator should handle this gracefully
            print("⚠️ Creating orchestrator without database manager")
            return  # Skip orchestrator test if no DB
        
        print("✅ Orchestrator created")
        
        # Create test message
        test_message = Message(
            message_id="test_001",
            user_id="test_user",
            content="Hello, can you respond to this test message?",
            message_type=MessageType.TEXT,
            platform=ChatPlatform.WEB_UI,
            channel_id="test_channel"
        )
        
        print(f"\n💬 Testing message processing...")
        print(f"📝 Test message: {test_message.content}")
        
        # Get or create conversation
        conversation = await orchestrator.get_or_create_conversation(test_message)
        print(f"✅ Conversation created: {conversation.conversation_id}")
        
        # Test AI response generation
        print("\n🤖 Testing AI response generation...")
        try:
            ai_response = await orchestrator.generate_ai_response(test_message, conversation)
            print(f"✅ AI Response successful!")
            print(f"📤 Content: {ai_response.content}")
            print(f"🔧 Model: {ai_response.model_used}")
            print(f"⏱️ Generation time: {ai_response.generation_time_ms}ms")
            print(f"💰 Cost: ${ai_response.cost:.4f}")
            
        except Exception as e:
            print(f"❌ AI response generation failed: {e}")
            import traceback
            traceback.print_exc()
            return
        
        print("\n🎉 All tests passed! Web UI integration should work.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_orchestrator_integration())