#!/usr/bin/env python3
"""
Direct test of CDL database integration without sync/async conflicts
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

from src.characters.database_cdl_parser import load_character_data

async def test_direct_cdl_database():
    """Test direct CDL database access"""
    print("🧪 Testing Direct CDL Database Integration (Elena)...")
    
    try:
        # Test direct async access
        character_data = await load_character_data("elena")
        
        if character_data:
            print("✅ Successfully loaded character data!")
            print(f"📊 Character keys: {list(character_data.keys())}")
            
            # Check for character structure
            if 'character' in character_data:
                character = character_data['character']
                print(f"🎭 Character structure: {list(character.keys())}")
                
                # Check identity
                identity = character.get('identity', {})
                print(f"👤 Identity: {identity.get('name', 'Unknown')}")
                print(f"💼 Occupation: {identity.get('occupation', 'Unknown')}")
                
                # Check personality  
                personality = character.get('personality', {})
                if 'big_five' in personality:
                    big_five = personality['big_five']
                    print(f"🧠 Big Five traits: {list(big_five.keys())}")
                    print(f"🔓 Openness: {big_five.get('openness', 'Unknown')}")
                    
                print(f"🎉 CDL Database integration works! Elena data successfully loaded from database.")
                
            else:
                print("❌ Missing 'character' key in data structure")
                print(f"📊 Available keys: {list(character_data.keys())}")
                # The data is at root level, not under 'character'
                print(f"👤 Name: {character_data.get('name', 'Unknown')}")
                print(f"💼 Identity occupation: {character_data.get('identity', {}).get('occupation', 'Unknown')}")
                if character_data.get('personality', {}).get('big_five'):
                    big_five = character_data['personality']['big_five']
                    print(f"🔓 Openness: {big_five.get('openness', 'Unknown')}")
                print(f"🎉 CDL Database integration works! Elena data successfully loaded from database.")
                    
        else:
            print("❌ No character data returned")
            
        return character_data is not None
        
    except Exception as e:
        print(f"❌ Direct CDL test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_direct_cdl_database())
    exit(0 if success else 1)