#!/usr/bin/env python3
"""
Test script to         # Test specific CDL fields
        identity_description = manager.get_field("identity.description", "Not found")
        print(f"📋 Identity description: {identity_description[:100]}..." if len(str(identity_description)) > 100 else f"📋 Identity description: {identity_description}")
        
        # Test Big Five personality traits (we know these are in the database)
        openness = manager.get_field("personality.big_five.openness", "Not found")
        print(f"🎭 Openness trait: {openness}")
        
        # Test if we can access the full personality structure
        personality = manager.get_field("personality", {})
        if personality and 'big_five' in personality:
            big_five = personality['big_five']
            print(f"🧠 Big Five structure: {list(big_five.keys())}")
            print(f"🔓 Openness: {big_five.get('openness', 'Missing')}")
            print(f"🎯 Conscientiousness: {big_five.get('conscientiousness', 'Missing')}")
        else:
            print(f"❌ No Big Five personality data found. Personality keys: {list(personality.keys()) if personality else 'None'}")
        
        # Test personal knowledge access
        personal_info = manager.get_field("personal_information", {})
        print(f"📚 Personal information keys: {list(personal_info.keys()) if personal_info else 'None'}")te CDL database integration
"""

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, '/Users/markcastillo/git/whisperengine')

# Set up environment for Elena bot testing
os.environ['DISCORD_BOT_NAME'] = 'elena'
os.environ['CHARACTER_FILE'] = 'elena.json'

from src.characters.cdl.database_manager import get_database_cdl_manager

async def test_cdl_database():
    """Test the CDL database integration"""
    print("🧪 Testing CDL Database Integration (Elena)...")
    
    try:
        # Get the database CDL manager
        manager = get_database_cdl_manager()
        print("✅ Created database CDL manager")
        
        # Test getting character data
        data_summary = manager.get_data_summary()
        print(f"📊 Data summary: {data_summary}")
        
        # Test specific field access
        character_name = manager.get_character_name()
        print(f"👤 Character name: {character_name}")
        
        occupation = manager.get_character_occupation()
        print(f"💼 Occupation: {occupation}")
        
        # Test field existence
        has_metadata = manager.has_field("character.metadata.name")
        print(f"🔍 Has metadata.name field: {has_metadata}")
        
        # Test some specific CDL fields
        identity_description = manager.get_field("character.identity.description", "Not found")
        print(f"📋 Identity description: {identity_description[:100]}..." if len(str(identity_description)) > 100 else f"📋 Identity description: {identity_description}")
        
        personality_traits = manager.get_field("character.personality.big_five.openness", "Not found")
        print(f"🎭 Openness trait: {personality_traits}")
        
        print("🎉 CDL Database integration test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ CDL Database integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_cdl_database())
    exit(0 if success else 1)