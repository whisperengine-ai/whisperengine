#!/usr/bin/env python3
"""
Debug test for multi-entity manager availability
"""
import sys
import os
sys.path.append(os.path.abspath('.'))

from env_manager import load_environment

def test_multi_entity_availability():
    """Test what's happening with multi-entity component availability"""
    print("🔍 Testing Multi-Entity Component Availability...")
    
    # Load environment
    if not load_environment():
        print("❌ Environment loading failed")
        return
    print("✅ Environment loaded")
    
    # Test imports
    try:
        from src.graph_database.multi_entity_manager import MultiEntityRelationshipManager
        print("✅ MultiEntityRelationshipManager import successful")
    except ImportError as e:
        print(f"❌ MultiEntityRelationshipManager import failed: {e}")
        return
        
    try:
        from src.graph_database.ai_self_bridge import AISelfEntityBridge
        print("✅ AISelfEntityBridge import successful")
    except ImportError as e:
        print(f"❌ AISelfEntityBridge import failed: {e}")
        return
    
    # Test initialization
    try:
        manager = MultiEntityRelationshipManager()
        print("✅ MultiEntityRelationshipManager initialization successful")
    except Exception as e:
        print(f"❌ MultiEntityRelationshipManager initialization failed: {e}")
        return
        
    try:
        bridge = AISelfEntityBridge()
        print("✅ AISelfEntityBridge initialization successful")
    except Exception as e:
        print(f"❌ AISelfEntityBridge initialization failed: {e}")
        return
    
    # Test bot core imports
    try:
        from src.core.bot import DiscordBotCore
        print("✅ DiscordBotCore import successful")
        
        bot_core = DiscordBotCore(debug_mode=True)
        print("✅ DiscordBotCore initialization successful")
        
        components = bot_core.get_components()
        multi_entity_available = components.get('multi_entity_manager') is not None
        ai_self_available = components.get('ai_self_bridge') is not None
        
        print(f"✅ Components retrieved: multi_entity_manager={multi_entity_available}, ai_self_bridge={ai_self_available}")
        
        if multi_entity_available:
            print("✅ Multi-entity manager is available in components")
        else:
            print("❌ Multi-entity manager is NOT available in components")
            
        if ai_self_available:
            print("✅ AI self bridge is available in components")
        else:
            print("❌ AI self bridge is NOT available in components")
    
    except Exception as e:
        print(f"❌ Bot core test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_multi_entity_availability()