#!/usr/bin/env python3
"""
Test Simple CDL Manager with Clean RDBMS Schema
Tests the new simplified CDL manager against our clean database schema
"""

import os
import sys
import asyncio
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up environment
os.environ['DISCORD_BOT_NAME'] = 'elena'
os.environ['POSTGRES_HOST'] = 'localhost'
os.environ['POSTGRES_PORT'] = '5433'  # WhisperEngine uses port 5433
os.environ['POSTGRES_USER'] = 'whisperengine'
os.environ['POSTGRES_PASSWORD'] = 'whisperengine_password'
os.environ['POSTGRES_DB'] = 'whisperengine'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_simple_cdl_manager():
    """Test the simple CDL manager"""
    print("🧪 Testing Simple CDL Manager")
    print("=" * 50)
    
    try:
        from src.characters.cdl.simple_cdl_manager import get_simple_cdl_manager, get_cdl_field
        
        # Get manager instance
        manager = get_simple_cdl_manager()
        print(f"✅ Created CDL manager: {type(manager).__name__}")
        
        # Test character name
        character_name = manager.get_character_name()
        print(f"✅ Character name: {character_name}")
        
        # Test character occupation
        occupation = manager.get_character_occupation()
        print(f"✅ Character occupation: {occupation}")
        
        # Test field access
        description = manager.get_field('identity.description', 'No description')
        print(f"✅ Character description: {description[:100]}...")
        
        # Test Big Five personality traits
        openness = manager.get_field('personality.big_five.openness.value', 0.5)
        print(f"✅ Openness trait: {openness}")
        
        # Test communication style
        engagement = manager.get_field('communication.engagement_level', 0.7)
        print(f"✅ Engagement level: {engagement}")
        
        # Test compatibility function
        flow_guidelines = get_cdl_field('communication.conversation_flow_guidance', '')
        print(f"✅ Flow guidelines: {flow_guidelines[:100] if flow_guidelines else 'None'}...")
        
        # Test character object
        character_obj = manager.get_character_object()
        print(f"✅ Character object: {character_obj.identity.name} - {character_obj.identity.occupation}")
        
        print("\n🎉 All tests passed! Simple CDL Manager working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Error testing CDL manager: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cdl_ai_integration():
    """Test CDL AI integration with simple manager"""
    print("\n🧪 Testing CDL AI Integration")
    print("=" * 50)
    
    try:
        from src.prompts.cdl_ai_integration import CDLAIPromptIntegration
        
        # Create integration (without memory/LLM for basic test)
        integration = CDLAIPromptIntegration()
        print(f"✅ Created CDL AI integration: {type(integration).__name__}")
        
        # This will test that the import works and doesn't crash
        print("✅ CDL AI Integration loaded successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing CDL AI integration: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Testing Simple CDL Manager System")
    print("=" * 60)
    
    # Test 1: Simple CDL Manager
    success1 = test_simple_cdl_manager()
    
    # Test 2: CDL AI Integration
    success2 = test_cdl_ai_integration()
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 60)
    print(f"Simple CDL Manager: {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"CDL AI Integration: {'✅ PASS' if success2 else '❌ FAIL'}")
    
    if success1 and success2:
        print("\n🎉 All tests passed! Clean RDBMS CDL system is working!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Check the errors above.")
        sys.exit(1)