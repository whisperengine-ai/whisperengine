#!/usr/bin/env python3
"""
Quick import script for Gabriel, Dream, and Aethys from legacy JSON files.
This script imports only the essential data needed for regression tests.
"""
import json
import asyncio
import asyncpg
import os
from pathlib import Path

async def import_character(conn, json_path: Path):
    """Import a single character from JSON file."""
    print(f"\n{'='*60}")
    print(f"Importing {json_path.name}...")
    print(f"{'='*60}")
    
    with open(json_path) as f:
        data = json.load(f)
    
    char = data['character']
    metadata = char['metadata']
    identity = char['identity']
    personality = char['personality']
    background = char['background']
    
    # Normalize name (first name only, lowercase)
    full_name = metadata['name']
    normalized_name = full_name.split()[0].lower()
    
    print(f"Character: {full_name} (normalized: {normalized_name})")
    print(f"Occupation: {identity.get('occupation', 'N/A')}")
    
    # Check if character exists
    existing = await conn.fetchrow(
        "SELECT id FROM characters WHERE normalized_name = $1",
        normalized_name
    )
    
    if existing:
        char_id = existing['id']
        print(f"✓ Character exists (ID: {char_id})")
        
        # Delete existing attributes to reimport fresh
        deleted = await conn.execute(
            "DELETE FROM character_attributes WHERE character_id = $1",
            char_id
        )
        print(f"✓ Cleared existing attributes: {deleted}")
    else:
        # Insert character
        char_id = await conn.fetchval("""
            INSERT INTO characters (name, normalized_name, occupation, description, archetype)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
        """, 
            full_name,
            normalized_name,
            identity.get('occupation', ''),
            identity.get('description', ''),
            identity.get('archetype', '')
        )
        print(f"✓ Created character (ID: {char_id})")
    
    # Import personality traits as attributes
    attributes = []
    
    # Primary traits
    if 'traits' in personality and isinstance(personality['traits'], dict):
        for trait in personality['traits'].get('primary', []):
            attributes.append({
                'category': 'personality_trait',
                'description': trait,
                'importance': 'high'
            })
        for trait in personality['traits'].get('secondary', []):
            attributes.append({
                'category': 'personality_trait',
                'description': trait,
                'importance': 'medium'
            })
    
    # Big Five personality dimensions
    if 'big_five' in personality:
        for dimension, value in personality['big_five'].items():
            if isinstance(value, (int, float)):
                attributes.append({
                    'category': 'big_five',
                    'description': f"{dimension}: {value}",
                    'importance': 'high'
                })
    
    # Values
    if 'values' in personality:
        values = personality['values']
        if isinstance(values, dict):
            for key, value_list in values.items():
                if isinstance(value_list, list):
                    for value in value_list:
                        attributes.append({
                            'category': 'value',
                            'description': f"{key}: {value}",
                            'importance': 'medium'
                        })
        elif isinstance(values, list):
            for value in values:
                attributes.append({
                    'category': 'value',
                    'description': value,
                    'importance': 'medium'
                })
    
    # Background elements
    if 'core_story' in background:
        attributes.append({
            'category': 'background',
            'description': background['core_story'],
            'importance': 'high'
        })
    
    # Insert all attributes
    if attributes:
        await conn.executemany("""
            INSERT INTO character_attributes (character_id, category, description, importance)
            VALUES ($1, $2, $3, $4)
        """, [(char_id, attr['category'], attr['description'], attr['importance']) 
              for attr in attributes])
        
        print(f"✓ Imported {len(attributes)} attributes")
        
        # Show sample attributes
        print("\nSample attributes:")
        for i, attr in enumerate(attributes[:5]):
            print(f"  {i+1}. [{attr['category']}] {attr['description'][:60]}...")
    else:
        print("⚠ No attributes to import")
    
    # Verify final count
    count = await conn.fetchval(
        "SELECT COUNT(*) FROM character_attributes WHERE character_id = $1",
        char_id
    )
    print(f"\n✓ Total attributes in database: {count}")
    
    return True

async def main():
    """Main import function."""
    # Database connection
    db_host = os.getenv('POSTGRES_HOST', 'localhost')
    db_port = os.getenv('POSTGRES_PORT', '5433')
    db_user = os.getenv('POSTGRES_USER', 'whisperengine')
    db_pass = os.getenv('POSTGRES_PASSWORD', 'whisperengine')
    db_name = os.getenv('POSTGRES_DB', 'whisperengine')
    
    print("Connecting to database...")
    print(f"  Host: {db_host}:{db_port}")
    print(f"  Database: {db_name}")
    
    conn = await asyncpg.connect(
        host=db_host,
        port=int(db_port),
        user=db_user,
        password=db_pass,
        database=db_name
    )
    
    try:
        # Legacy character files
        legacy_dir = Path("characters/examples_legacy_backup")
        character_files = ['gabriel.json', 'dream.json', 'aethys.json']
        
        success_count = 0
        for filename in character_files:
            json_path = legacy_dir / filename
            if json_path.exists():
                try:
                    await import_character(conn, json_path)
                    success_count += 1
                except Exception as e:
                    print(f"\n❌ Error importing {filename}: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"\n⚠ File not found: {json_path}")
        
        print(f"\n{'='*60}")
        print(f"Import complete: {success_count}/{len(character_files)} characters")
        print(f"{'='*60}\n")
        
        # Final verification
        print("Final character attribute counts:")
        result = await conn.fetch("""
            SELECT c.name, c.normalized_name, COUNT(ca.id) as attr_count
            FROM characters c
            LEFT JOIN character_attributes ca ON c.id = ca.character_id
            WHERE c.normalized_name IN ('gabriel', 'dream', 'aethys')
            GROUP BY c.name, c.normalized_name
            ORDER BY c.name
        """)
        
        for row in result:
            print(f"  {row['name']:20} ({row['normalized_name']:10}): {row['attr_count']:3} attributes")
    
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
