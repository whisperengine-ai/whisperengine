#!/usr/bin/env python3
"""Simple test to understand Web UI Universal Chat initialization without FastAPI dependencies"""

import sys
import os
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_universal_chat_initialization():
    """Test Universal Chat components without FastAPI"""
    
    print("🧪 Testing Universal Chat Initialization (without FastAPI)")
    print("=" * 60)
    
    try:
        # Test 1: Can we import the Universal Chat components?
        print("1. Testing Universal Chat imports...")
        
        try:
            from src.platforms.universal_chat import UniversalChatOrchestrator, ChatPlatform, Message
            print("✅ Universal Chat imports successful")
        except Exception as e:
            print(f"❌ Universal Chat import failed: {e}")
            return False
        
        # Test 2: Can we import the config manager?
        print("2. Testing Config Manager...")
        
        try:
            from src.config.adaptive_config import AdaptiveConfigManager
            config_manager = AdaptiveConfigManager()
            print("✅ Config Manager initialized")
        except Exception as e:
            print(f"❌ Config Manager failed: {e}")
            return False
        
        # Test 3: Can we import database integration?
        print("3. Testing Database Integration...")
        
        try:
            from src.database.database_integration import DatabaseIntegrationManager
            db_manager = DatabaseIntegrationManager(config_manager)
            print("✅ Database Integration Manager initialized")
        except Exception as e:
            print(f"❌ Database Integration failed: {e}")
            return False
        
        # Test 4: Can we create Universal Chat Orchestrator?
        print("4. Testing Universal Chat Orchestrator...")
        
        try:
            orchestrator = UniversalChatOrchestrator(
                config_manager=config_manager,
                db_manager=db_manager
            )
            print("✅ Universal Chat Orchestrator created")
        except Exception as e:
            print(f"❌ Universal Chat Orchestrator failed: {e}")
            print(f"   Error details: {repr(e)}")
            import traceback
            traceback.print_exc()
            return False
        
        # Test 5: Can we import LLM client?
        print("5. Testing LLM Client...")
        
        try:
            from src.llm.llm_client import LLMClient
            print("✅ LLM Client import successful")
            
            # Test if we can create an instance
            llm_client = LLMClient()
            print(f"✅ LLM Client initialized: {llm_client.service_name}")
        except Exception as e:
            print(f"❌ LLM Client failed: {e}")
            print(f"   This might be why Web UI falls back to mock responses")
            return False
        
        print("\n" + "=" * 60)
        print("🏁 Universal Chat Initialization Test Complete")
        print("✅ All components can be initialized - Web UI should work with real AI")
        return True
        
    except Exception as e:
        print(f"❌ Critical error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_universal_chat_initialization()
    sys.exit(0 if success else 1)