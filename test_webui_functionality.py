#!/usr/bin/env python3
"""Test Web UI functionality to verify real AI responses vs mock/fallback responses"""

import asyncio
import sys
import os
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.ui.web_ui import WhisperEngineWebUI
from src.config.adaptive_config import AdaptiveConfigManager  
from src.database.database_integration import DatabaseIntegrationManager

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def test_webui_functionality():
    """Test if Web UI generates real AI responses or falls back to mock responses"""
    
    print("🧪 Testing Web UI Functionality")
    print("=" * 50)
    
    try:
        # Initialize Web UI components
        print("1. Initializing config manager...")
        config_manager = AdaptiveConfigManager()
        
        print("2. Initializing database manager...")
        db_manager = DatabaseIntegrationManager(config_manager)
        
        print("3. Creating Web UI instance...")
        web_ui = WhisperEngineWebUI(db_manager=db_manager, config_manager=config_manager)
        
        # Check if Universal Chat Orchestrator initialized
        print("4. Checking Universal Chat Orchestrator...")
        if hasattr(web_ui, 'chat_orchestrator') and web_ui.chat_orchestrator:
            print("✅ Universal Chat Orchestrator initialized successfully")
            
            # Test the orchestrator directly
            print("5. Testing Universal Chat Orchestrator directly...")
            
            # Create a test message
            from src.platforms.universal_chat import Message, ChatPlatform
            
            test_message = Message(
                user_id="test_user_123",
                content="Hello, can you tell me about your capabilities?",
                platform=ChatPlatform.WEB_UI,
                channel_id="web_test_channel",
                timestamp=None,
                message_id="test_msg_001"
            )
            
            # Get or create conversation
            conversation = await web_ui.chat_orchestrator.get_or_create_conversation(test_message)
            
            # Generate AI response
            ai_response = await web_ui.chat_orchestrator.generate_ai_response(test_message, conversation)
            
            print(f"✅ AI Response Generated:")
            print(f"   Content: {ai_response.content[:100]}...")
            print(f"   Model: {ai_response.model_used}")
            print(f"   Tokens: {ai_response.tokens_used}")
            print(f"   Cost: ${ai_response.cost:.4f}")
            print(f"   Generation Time: {ai_response.generation_time_ms}ms")
            
        else:
            print("❌ Universal Chat Orchestrator NOT initialized")
            print("   Web UI will fall back to direct LLM client")
            
            # Test fallback response
            print("6. Testing fallback response...")
            fallback_response = await web_ui._generate_fallback_response("test_user", "Hello, what are your capabilities?")
            
            print(f"📉 Fallback Response:")
            print(f"   Content: {fallback_response['content'][:100]}...")
            print(f"   Metadata: {fallback_response['metadata']}")
            
        # Test the full generate_ai_response method (what WebSocket actually calls)
        print("\n7. Testing full generate_ai_response method...")
        full_response = await web_ui.generate_ai_response("test_user_456", "What makes you different from other AI assistants?")
        
        print(f"🎯 Full Response Method:")
        print(f"   Content: {full_response['content'][:100]}...")
        print(f"   Metadata: {full_response['metadata']}")
        
        # Determine if real AI or fallback
        if 'platform' in full_response['metadata']:
            if full_response['metadata']['platform'] == 'fallback_direct':
                print("⚠️  Using FALLBACK direct LLM client")
            elif full_response['metadata']['platform'] == 'web_ui':
                print("✅ Using Universal Chat Orchestrator")
            else:
                print(f"🔍 Using platform: {full_response['metadata']['platform']}")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 50)
    print("🏁 Web UI Functionality Test Complete")
    return True

if __name__ == "__main__":
    asyncio.run(test_webui_functionality())