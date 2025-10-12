#!/usr/bin/env python3
"""
Batch import all remaining characters to enhanced JSONB database
"""

import asyncio
import asyncpg
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.append('/Users/markcastillo/git/whisperengine')

from src.characters.enhanced_jsonb_manager import create_enhanced_cdl_manager

async def batch_import_characters():
    """Import all remaining characters to enhanced JSONB database"""
    
    print("🚀 Starting batch import of characters to enhanced JSONB database...")
    
    # Character file mappings
    characters_to_import = [
        {
            'name': 'Marcus Thompson',
            'normalized_name': 'marcus_thompson',
            'bot_name': 'marcus',
            'file_path': '/Users/markcastillo/git/whisperengine/characters/examples/marcus.json',
            'archetype': 'real_world'
        },
        {
            'name': 'Gabriel',
            'normalized_name': 'gabriel',
            'bot_name': 'gabriel', 
            'file_path': '/Users/markcastillo/git/whisperengine/characters/examples/gabriel.json',
            'archetype': 'real_world'
        },
        {
            'name': 'Jake Sterling',
            'normalized_name': 'jake_sterling',
            'bot_name': 'jake',
            'file_path': '/Users/markcastillo/git/whisperengine/characters/examples/jake.json',
            'archetype': 'real_world'
        },
        {
            'name': 'Ryan Chen',
            'normalized_name': 'ryan_chen',
            'bot_name': 'ryan',
            'file_path': '/Users/markcastillo/git/whisperengine/characters/examples/ryan.json',
            'archetype': 'real_world'
        },
        {
            'name': 'Sophia Blake',
            'normalized_name': 'sophia_blake',
            'bot_name': 'sophia',
            'file_path': '/Users/markcastillo/git/whisperengine/characters/examples/sophia.json',
            'archetype': 'real_world'
        }
    ]
    
    # Connect to database
    postgres_pool = await asyncpg.create_pool(
        host='localhost',
        port=5433,
        user='whisperengine',
        password='whisperengine_pass',
        database='whisperengine',
        min_size=1,
        max_size=10
    )
    
    print("✅ Connected to PostgreSQL database")
    
    # Create enhanced CDL manager
    cdl_manager = create_enhanced_cdl_manager(postgres_pool)
    
    successful_imports = []
    failed_imports = []
    
    for char_info in characters_to_import:
        try:
            print(f"\n📁 Processing {char_info['name']}...")
            
            # Check if file exists
            char_file = Path(char_info['file_path'])
            if not char_file.exists():
                print(f"❌ Character file not found: {char_file}")
                failed_imports.append(char_info['name'])
                continue
            
            # Load character data
            with open(char_file, 'r', encoding='utf-8') as f:
                char_data = json.load(f)
            
            # Extract character information
            character = char_data.get('character', {})
            metadata = character.get('metadata', {})
            
            # Import using enhanced JSONB manager
            char_id = await cdl_manager.upsert_character({
                'character': character,
                'character_archetype': char_info['archetype'],
                'metadata': metadata
            })
            
            if char_id:
                print(f"✅ {char_info['name']} imported successfully (ID: {char_id})")
                successful_imports.append(char_info['name'])
            else:
                print(f"❌ Failed to import {char_info['name']}")
                failed_imports.append(char_info['name'])
                
        except (ConnectionError, ValueError, json.JSONDecodeError) as e:
            print(f"❌ Error importing {char_info['name']}: {e}")
            failed_imports.append(char_info['name'])
    
    # Summary
    print("\n📊 Batch Import Summary:")
    print(f"✅ Successfully imported: {len(successful_imports)} characters")
    for name in successful_imports:
        print(f"   - {name}")
    
    if failed_imports:
        print(f"❌ Failed imports: {len(failed_imports)} characters")
        for name in failed_imports:
            print(f"   - {name}")
    
    # Verify all characters in database
    print("\n🔍 Verifying all characters in database:")
    async with postgres_pool.acquire() as conn:
        results = await conn.fetch("""
            SELECT name, normalized_name, bot_name, archetype,
                   cdl_data->'identity'->>'occupation' as occupation
            FROM characters_v2 
            ORDER BY name
        """)
        
        print(f"📚 Total characters in database: {len(results)}")
        for result in results:
            print(f"   - {result['name']} ({result['bot_name']}) - {result['occupation']}")
    
    await postgres_pool.close()
    
    if failed_imports:
        print("\n⚠️  Some imports failed. Check character files and database connectivity.")
        return False
    else:
        print("\n🎉 All characters successfully imported to enhanced JSONB database!")
        return True

if __name__ == "__main__":
    success = asyncio.run(batch_import_characters())
    if success:
        print("\n🚀 Ready to test all characters with enhanced JSONB CDL system!")
    else:
        print("\n💥 Some character imports failed - check errors above")