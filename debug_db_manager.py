#!/usr/bin/env python3
"""
Debug the CDL database manager directly
"""

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, '/Users/markcastillo/git/whisperengine')

# Set up environment
os.environ['POSTGRES_HOST'] = 'localhost'
os.environ['POSTGRES_PORT'] = '5433'
os.environ['POSTGRES_DB'] = 'whisperengine'
os.environ['POSTGRES_USER'] = 'whisperengine'
os.environ['POSTGRES_PASSWORD'] = 'whisperengine_password'

from src.database.cdl_database import CDLDatabaseManager

async def debug_database_manager():
    """Debug the database manager directly"""
    print("🔍 Debugging CDL Database Manager...")
    
    try:
        # Initialize database manager
        db_manager = CDLDatabaseManager()
        await db_manager.initialize_pool()
        print("✅ Database manager initialized")
        
        # Get character profile directly
        character_profile = await db_manager.get_character_by_name("elena")
        print(f"📊 Character profile keys: {list(character_profile.keys()) if character_profile else 'None'}")
        
        if character_profile:
            print(f"👤 Name: {character_profile.get('name')}")
            print(f"💼 Occupation: {character_profile.get('occupation')}")
            
            # Check personality traits
            personality_traits = character_profile.get('personality_traits', {})
            print(f"🎭 Personality traits type: {type(personality_traits)}")
            print(f"🎭 Personality traits: {personality_traits}")
            
            if isinstance(personality_traits, dict):
                print(f"🧠 Trait names: {list(personality_traits.keys())}")
                for trait_name, trait_data in personality_traits.items():
                    print(f"  {trait_name}: {trait_data}")
        
        await db_manager.close_pool()
        return True
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(debug_database_manager())
    exit(0 if success else 1)