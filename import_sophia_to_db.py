#!/usr/bin/env python3
"""
Import Sophia character data to enhanced JSONB database
"""

import json
import asyncio
import asyncpg
import sys
from pathlib import Path

# Add project root to path
sys.path.append('/Users/markcastillo/git/whisperengine')

from src.characters.enhanced_jsonb_manager import create_enhanced_cdl_manager

async def import_sophia_character():
    """Import Sophia's CDL data to the enhanced JSONB database"""
    
    # Load Sophia's character file
    sophia_file = Path("/Users/markcastillo/git/whisperengine/characters/examples/sophia_v2.json")
    
    if not sophia_file.exists():
        print(f"❌ Sophia character file not found: {sophia_file}")
        return False
    
    # Read Sophia's CDL data
    with open(sophia_file, 'r', encoding='utf-8') as f:
        sophia_data = json.load(f)
    
    print(f"📁 Loaded Sophia character data from {sophia_file}")
    
    # Extract character information
    character = sophia_data.get('character', {})
    metadata = character.get('metadata', {})
    name = metadata.get('name', 'Sophia Blake')
    normalized_name = name.lower().replace(' ', '_')
    
    print(f"🎭 Character: {name} (normalized: {normalized_name})")
    
    # Connect to database
    try:
        postgres_pool = await asyncpg.create_pool(
            host='localhost',
            port=5433,
            user='whisperengine',
            password='whisperengine_pass',
            database='whisperengine',
            min_size=1,
            max_size=5
        )
        print("✅ Connected to PostgreSQL database")
        
        # Create enhanced CDL manager
        cdl_manager = create_enhanced_cdl_manager(postgres_pool)
        
        # Import character using upsert function
        char_id = await cdl_manager.upsert_character({
            'character': character,
            'character_archetype': 'real_world',
            'metadata': metadata
        })
        
        print(f"✅ Sophia character imported successfully with ID: {char_id}")
        
        # Verify the import by querying back
        result = await postgres_pool.fetchrow("""
            SELECT name, normalized_name, bot_name, archetype,
                   cdl_data->'identity'->>'occupation' as occupation,
                   cdl_data->'identity'->>'location' as location
            FROM characters_v2 
            WHERE name ILIKE '%sophia%'
        """)
        
        if result:
            print("🔍 Verification:")
            print(f"   Name: {result['name']}")
            print(f"   Bot Name: {result['bot_name']}")
            print(f"   Archetype: {result['archetype']}")
            print(f"   Occupation: {result['occupation']}")
            print(f"   Location: {result['location']}")
        
        await postgres_pool.close()
        print("🎉 Sophia character import completed successfully!")
        return True
        
    except (ConnectionError, ValueError) as e:
        print(f"❌ Database error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(import_sophia_character())
    if success:
        print("\n🚀 Sophia is now ready for enhanced JSONB CDL testing!")
    else:
        print("\n💥 Sophia import failed - check database connection and schema")