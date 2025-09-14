#!/usr/bin/env python3
"""Test Web UI functionality with installed dependencies"""

import asyncio
import sys
import os
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def test_webui_with_dependencies():
    """Test Web UI functionality with actual dependencies installed"""
    
    print("🧪 Testing Web UI with Dependencies")
    print("=" * 50)
    
    try:
        # Test imports
        print("1. Testing imports...")
        from src.ui.web_ui import WhisperEngineWebUI
        from src.config.adaptive_config import AdaptiveConfigManager  
        from src.database.database_integration import DatabaseIntegrationManager
        print("✅ All imports successful")
        
        # Create components
        print("2. Creating components...")
        config_manager = AdaptiveConfigManager()
        db_manager = DatabaseIntegrationManager(config_manager)
        web_ui = WhisperEngineWebUI(db_manager=db_manager, config_manager=config_manager)
        print("✅ Components created")
        
        # Test Universal Chat Orchestrator
        print("3. Testing Universal Chat Orchestrator...")
        if hasattr(web_ui, 'chat_orchestrator') and web_ui.chat_orchestrator:
            print("✅ Universal Chat Orchestrator initialized")
            
            # Test AI response generation
            print("4. Testing AI response generation...")
            test_response = await web_ui.generate_ai_response("test_user", "Hello! Can you tell me about your capabilities?")
            
            print(f"📤 Response received:")
            print(f"   Content preview: {test_response['content'][:100]}...")
            print(f"   Metadata: {test_response['metadata']}")
            
            # Check if it's real AI or fallback
            status = test_response['metadata'].get('status', 'unknown')
            if status == 'real_ai':
                print("🎉 SUCCESS! Web UI is generating REAL AI responses!")
            elif status == 'fallback_error':
                print("⚠️  Still using fallback due to Universal Chat error")
            elif status == 'direct_llm':
                print("🔄 Using direct LLM fallback (Universal Chat issue)")
            elif status == 'dependency_error':
                print("❌ Still missing dependencies")
            else:
                print(f"🔍 Status: {status}")
            
            return status == 'real_ai'
            
        else:
            print("❌ Universal Chat Orchestrator not initialized")
            return False
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_webui_with_dependencies())
    if success:
        print("\n🚀 Web UI ready for testing with real AI responses!")
    else:
        print("\n⚠️  Web UI has issues - check logs above")