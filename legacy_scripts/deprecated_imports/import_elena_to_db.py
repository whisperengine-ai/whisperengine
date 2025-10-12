#!/usr/bin/env python3
"""
Import Elena character data to enhanced JSONB database
"""

import json
import asyncio
import asyncpg
from pathlib import Path

async def import_elena_character():
    """Import Elena's CDL data to the enhanced JSONB database"""
    
    # Load Elena's character file
    elena_file = Path("/Users/markcastillo/git/whisperengine/characters/examples/elena.json")
    
    if not elena_file.exists():
        print(f"❌ Elena character file not found: {elena_file}")
        return False
    
    # Read Elena's CDL data
    with open(elena_file, 'r', encoding='utf-8') as f:
        elena_data = json.load(f)
    
    print(f"📁 Loaded Elena character data from {elena_file}")
    
    # Extract character information
    character = elena_data.get('character', {})
    metadata = character.get('metadata', {})
    name = metadata.get('name', 'Elena Rodriguez')
    normalized_name = name.lower().replace(' ', '_')
    
    print(f"🎭 Character: {name} (normalized: {normalized_name})")
    
    # Connect to database
    try:
        conn = await asyncpg.connect(
            host='localhost',
            port=5433,
            user='whisperengine',
            password='whisperengine_pass',
            database='whisperengine'
        )
        print("✅ Connected to PostgreSQL database")
        
        # Import character using upsert function
        char_id = await conn.fetchval("""
            SELECT upsert_character_v2($1, $2, $3, $4, $5, $6, $7)
        """,
            name,                                    # p_name
            normalized_name,                         # p_normalized_name
            'elena',                                 # p_bot_name
            'real_world',                           # p_archetype
            json.dumps(character),                   # p_cdl_data (JSONB)
            '{}',                                   # p_workflow_data (empty for now)
            json.dumps(metadata)                     # p_metadata
        )
        
        print(f"✅ Elena character imported successfully with ID: {char_id}")
        
        # Verify the import by querying back
        result = await conn.fetchrow("""
            SELECT name, normalized_name, bot_name, archetype,
                   cdl_data->'identity'->>'occupation' as occupation,
                   cdl_data->'identity'->>'location' as location
            FROM characters_v2 
            WHERE normalized_name = $1
        """, normalized_name)
        
        if result:
            print("🔍 Verification:")
            print(f"   Name: {result['name']}")
            print(f"   Bot Name: {result['bot_name']}")
            print(f"   Archetype: {result['archetype']}")
            print(f"   Occupation: {result['occupation']}")
            print(f"   Location: {result['location']}")
        
        await conn.close()
        print("🎉 Elena character import completed successfully!")
        return True
        
    except (ConnectionError, ValueError) as e:
        print(f"❌ Database error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(import_elena_character())
    if success:
        print("\n🚀 Ready to test Elena bot with enhanced JSONB CDL system!")
    else:
        print("\n💥 Import failed - check database connection and schema")