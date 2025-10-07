#!/usr/bin/env python3
"""
Simplified CDL Database Debug Test
"""

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, '/Users/markcastillo/git/whisperengine')

# Set up environment for Elena bot testing
os.environ['DISCORD_BOT_NAME'] = 'elena'
os.environ['CHARACTER_FILE'] = 'elena.json'
os.environ['POSTGRES_HOST'] = 'localhost'
os.environ['POSTGRES_PORT'] = '5433'
os.environ['POSTGRES_DB'] = 'whisperengine'
os.environ['POSTGRES_USER'] = 'whisperengine'
os.environ['POSTGRES_PASSWORD'] = 'whisperengine_password'

from src.characters.cdl.database_manager import get_database_cdl_manager

def test_cdl_database_simple():
    """Simple sync test of CDL database"""
    print("🧪 Testing CDL Database Integration (Simple)...")
    
    try:
        # Get the database CDL manager
        manager = get_database_cdl_manager()
        print("✅ Created database CDL manager")
        
        # Test basic access
        character_name = manager.get_character_name()
        print(f"👤 Character name: {character_name}")
        
        occupation = manager.get_character_occupation()
        print(f"💼 Occupation: {occupation}")
        
        # Test field access for personality traits
        print("🧠 Testing personality trait access...")
        
        # Debug: check what's actually in personality
        personality = manager.get_field("personality", {})
        print(f"🎭 Personality keys: {list(personality.keys()) if personality else 'None'}")
        
        if personality and 'big_five_traits' in personality:
            big_five_traits = personality['big_five_traits']
            print(f"🧠 Big Five traits keys: {list(big_five_traits.keys())}")
            if 'openness' in big_five_traits:
                openness_data = big_five_traits['openness']
                print(f"🔓 Openness data: {openness_data}")
            
        # Try the correct path
        openness = manager.get_field("personality.big_five_traits.openness", "Not found")
        print(f"🔓 Openness (correct path): {openness}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_cdl_database_simple()
    exit(0 if success else 1)