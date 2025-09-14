#!/usr/bin/env python3
"""Test to check exactly what fails during Web UI Universal Chat setup"""

import sys
import os
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_webui_setup_issue():
    """Test exactly what fails during Web UI setup"""
    
    print("🔍 Analyzing Web UI Setup Issue")
    print("=" * 40)
    
    try:
        # Test the exact setup process from web_ui.py
        print("1. Testing config manager...")
        from src.config.adaptive_config import AdaptiveConfigManager
        config_manager = AdaptiveConfigManager()
        print("✅ Config manager OK")
        
        print("2. Testing database manager...")
        from src.database.database_integration import DatabaseIntegrationManager
        db_manager = DatabaseIntegrationManager(config_manager)
        print("✅ Database manager OK")
        
        print("3. Testing Universal Chat Orchestrator creation...")
        from src.platforms.universal_chat import UniversalChatOrchestrator
        
        try:
            chat_orchestrator = UniversalChatOrchestrator(
                config_manager=config_manager,
                db_manager=db_manager
            )
            print("✅ Universal Chat Orchestrator created successfully")
            
            # This is the key test - can we actually generate a response?
            print("4. Testing AI response generation...")
            
            import asyncio
            
            async def test_ai_response():
                try:
                    # Create test message
                    from src.platforms.universal_chat import Message, ChatPlatform
                    
                    test_message = Message(
                        user_id="test_user",
                        content="Hello, test message",
                        platform=ChatPlatform.WEB_UI,
                        channel_id="test_channel",
                        message_id="test_001"
                    )
                    
                    # Get conversation
                    conversation = await chat_orchestrator.get_or_create_conversation(test_message)
                    
                    # Try to generate response
                    ai_response = await chat_orchestrator.generate_ai_response(test_message, conversation)
                    
                    print("✅ AI response generated successfully")
                    print(f"   Content: {ai_response.content[:50]}...")
                    print(f"   Model: {ai_response.model_used}")
                    
                    return True
                    
                except Exception as e:
                    print(f"❌ AI response generation failed: {e}")
                    print(f"   Error type: {type(e).__name__}")
                    import traceback
                    traceback.print_exc()
                    return False
            
            # Run the async test
            success = asyncio.run(test_ai_response())
            
            if not success:
                print("\n🔍 This explains why Web UI shows 'mock messages':")
                print("   - Universal Chat Orchestrator is created successfully")
                print("   - But AI response generation fails") 
                print("   - Web UI falls back to _generate_fallback_response()")
                print("   - User sees fallback responses instead of real AI")
            
            return success
            
        except Exception as e:
            print(f"❌ Universal Chat Orchestrator creation failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
    except Exception as e:
        print(f"❌ Setup test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_webui_setup_issue()