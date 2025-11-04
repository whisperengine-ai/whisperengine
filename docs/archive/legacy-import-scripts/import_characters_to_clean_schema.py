#!/usr/bin/env python3
"""
Import Characters to Clean RDBMS Schema
Imports character data from legacy JSON files to the new clean RDBMS schema
"""

import os
import sys
import json
import asyncio
import asyncpg
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up environment for database connection
os.environ['POSTGRES_HOST'] = 'localhost'
os.environ['POSTGRES_PORT'] = '5433'  # WhisperEngine uses port 5433
os.environ['POSTGRES_USER'] = 'whisperengine'
os.environ['POSTGRES_PASSWORD'] = 'whisperengine_password'
os.environ['POSTGRES_DB'] = 'whisperengine'

async def get_database_connection():
    """Get database connection"""
    postgres_host = os.getenv('POSTGRES_HOST', 'localhost')
    postgres_port = int(os.getenv('POSTGRES_PORT', '5432'))
    postgres_user = os.getenv('POSTGRES_USER', 'whisperengine')
    postgres_password = os.getenv('POSTGRES_PASSWORD', 'whisperengine_password')
    postgres_db = os.getenv('POSTGRES_DB', 'whisperengine')
    
    database_url = f"postgresql://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}"
    return await asyncpg.connect(database_url)

def normalize_character_name(name: str) -> str:
    """Create normalized name for database lookup"""
    return name.lower().replace(' ', '_').replace('-', '_')

def extract_big_five_traits(character_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract Big Five personality traits from character data"""
    traits = []
    
    # Try different possible locations for Big Five data
    big_five_data = None
    
    # Check personality.big_five
    if 'personality' in character_data and 'big_five' in character_data['personality']:
        big_five_data = character_data['personality']['big_five']
    
    # Check personality.traits (alternative location)
    elif 'personality' in character_data and 'traits' in character_data['personality']:
        big_five_data = character_data['personality']['traits']
    
    if big_five_data:
        for trait_name, trait_info in big_five_data.items():
            if isinstance(trait_info, dict):
                # Full trait object with value, description, etc.
                traits.append({
                    'trait_name': trait_name,
                    'trait_value': float(trait_info.get('value', 0.5)),
                    'intensity': trait_info.get('intensity', 'medium'),
                    'description': trait_info.get('description', f'{trait_name} personality trait')
                })
            elif isinstance(trait_info, (int, float)):
                # Simple numeric value
                traits.append({
                    'trait_name': trait_name,
                    'trait_value': float(trait_info),
                    'intensity': 'medium',
                    'description': f'{trait_name} personality trait'
                })
    
    return traits

def extract_communication_style(character_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract communication style from character data"""
    comm_data = character_data.get('communication', {})
    
    # Helper function to extract string values from complex structures
    def extract_string_value(value, default=''):
        if isinstance(value, str):
            return value
        elif isinstance(value, dict):
            # Try common keys for string values
            for key in ['value', 'description', 'text', 'content']:
                if key in value and isinstance(value[key], str):
                    return value[key]
            # If no string found, try to convert to string
            return str(value) if value else default
        else:
            return str(value) if value is not None else default
    
    # Helper function to extract float values
    def extract_float_value(value, default=0.7):
        if isinstance(value, (int, float)):
            return float(value)
        elif isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                return default
        elif isinstance(value, dict) and 'value' in value:
            try:
                return float(value['value'])
            except (ValueError, TypeError):
                return default
        else:
            return default
    
    return {
        'engagement_level': extract_float_value(comm_data.get('engagement_level'), 0.7),
        'formality': extract_string_value(comm_data.get('formality'), 'informal'),
        'emotional_expression': extract_float_value(comm_data.get('emotional_expression'), 0.6),
        'response_length': extract_string_value(comm_data.get('response_length'), 'medium'),
        'conversation_flow_guidance': extract_string_value(comm_data.get('conversation_flow_guidance'), ''),
        'ai_identity_handling': extract_string_value(comm_data.get('ai_identity_handling'), '')
    }

def extract_character_values(character_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract character values from character data"""
    values = []
    
    # Check values_and_beliefs section
    values_data = character_data.get('values_and_beliefs', {})
    
    for value_key, value_info in values_data.items():
        if isinstance(value_info, dict):
            values.append({
                'value_key': value_key,
                'value_description': value_info.get('description', value_key),
                'importance_level': value_info.get('importance', 'medium'),
                'category': value_info.get('category', 'general')
            })
        elif isinstance(value_info, str):
            values.append({
                'value_key': value_key,
                'value_description': value_info,
                'importance_level': 'medium',
                'category': 'general'
            })
    
    return values

async def import_character_from_json(conn, json_file_path: Path) -> bool:
    """Import a single character from JSON file"""
    try:
        print(f"📥 Importing character from: {json_file_path.name}")
        
        # Load JSON data
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle nested character structure (some files have data.character)
        if 'character' in data:
            character_data = data['character']
        else:
            character_data = data
        
        # Extract basic character information
        identity = character_data.get('identity', {})
        character_name = identity.get('name', json_file_path.stem.title())
        normalized_name = normalize_character_name(character_name)
        occupation = identity.get('occupation', '')
        description = identity.get('description', '')
        archetype = identity.get('archetype', 'real-world')
        allow_full_roleplay = character_data.get('allow_full_roleplay_immersion', False)
        
        print(f"   Character: {character_name} ({normalized_name})")
        print(f"   Occupation: {occupation}")
        
        # Check if character already exists
        existing = await conn.fetchrow(
            "SELECT id FROM characters WHERE normalized_name = $1",
            normalized_name
        )
        
        if existing:
            print(f"   ⚠️  Character {character_name} already exists, updating...")
            character_id = existing['id']
            
            # Update existing character
            await conn.execute("""
                UPDATE characters 
                SET name = $1, occupation = $2, description = $3, archetype = $4, allow_full_roleplay = $5
                WHERE id = $6
            """, character_name, occupation, description, archetype, allow_full_roleplay, character_id)
            
            # Delete existing traits, communication styles, and values to replace them
            await conn.execute("DELETE FROM personality_traits WHERE character_id = $1", character_id)
            await conn.execute("DELETE FROM communication_styles WHERE character_id = $1", character_id)
            await conn.execute("DELETE FROM character_values WHERE character_id = $1", character_id)
            
        else:
            # Insert new character
            character_id = await conn.fetchval("""
                INSERT INTO characters (name, normalized_name, occupation, description, archetype, allow_full_roleplay, is_active)
                VALUES ($1, $2, $3, $4, $5, $6, true)
                RETURNING id
            """, character_name, normalized_name, occupation, description, archetype, allow_full_roleplay)
        
        print(f"   ✅ Character record ready with ID: {character_id}")
        
        # Extract and insert personality traits
        traits = extract_big_five_traits(character_data)
        for trait in traits:
            await conn.execute("""
                INSERT INTO personality_traits (character_id, trait_name, trait_value, intensity, description)
                VALUES ($1, $2, $3, $4, $5)
            """, character_id, trait['trait_name'], trait['trait_value'], trait['intensity'], trait['description'])
        
        print(f"   ✅ Inserted {len(traits)} personality traits")
        
        # Extract and insert communication style
        comm_style = extract_communication_style(character_data)
        print(f"   Debug - Communication style values:")
        for key, value in comm_style.items():
            print(f"     {key}: {len(str(value))} chars - '{str(value)[:100]}{'...' if len(str(value)) > 100 else ''}'")
        
        await conn.execute("""
            INSERT INTO communication_styles (
                character_id, engagement_level, formality, emotional_expression,
                response_length, conversation_flow_guidance, ai_identity_handling
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        """, character_id, comm_style['engagement_level'], comm_style['formality'],
             comm_style['emotional_expression'], comm_style['response_length'],
             comm_style['conversation_flow_guidance'], comm_style['ai_identity_handling'])
        
        print(f"   ✅ Inserted communication style")
        
        # Extract and insert character values
        values = extract_character_values(character_data)
        for value in values:
            await conn.execute("""
                INSERT INTO character_values (character_id, value_key, value_description, importance_level, category)
                VALUES ($1, $2, $3, $4, $5)
            """, character_id, value['value_key'], value['value_description'], 
                 value['importance_level'], value['category'])
        
        print(f"   ✅ Inserted {len(values)} character values")
        print(f"   🎉 Successfully imported {character_name}!")
        
        return True
        
    except (OSError, json.JSONDecodeError, KeyError) as e:
        print(f"   ❌ Error importing {json_file_path.name}: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main import function"""
    print("🚀 Importing Characters to Clean RDBMS Schema")
    print("=" * 60)
    
    # Connect to database
    try:
        conn = await get_database_connection()
        print("✅ Connected to database")
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        return
    
    # Find character JSON files
    backup_dir = Path("characters/examples_legacy_backup")
    json_files = list(backup_dir.glob("*.json"))
    
    # Filter out backup files (keep only the main character files)
    main_character_files = []
    for json_file in json_files:
        # Skip backup files (contain .backup_ in name)
        if '.backup_' not in json_file.name:
            main_character_files.append(json_file)
    
    print(f"📁 Found {len(main_character_files)} character files to import")
    
    # Import each character
    successful_imports = 0
    failed_imports = 0
    
    for json_file in sorted(main_character_files):
        success = await import_character_from_json(conn, json_file)
        if success:
            successful_imports += 1
        else:
            failed_imports += 1
        print()  # Add spacing between characters
    
    # Close database connection
    await conn.close()
    
    # Summary
    print("📊 Import Summary")
    print("=" * 60)
    print(f"✅ Successful imports: {successful_imports}")
    print(f"❌ Failed imports: {failed_imports}")
    print(f"📁 Total files processed: {len(main_character_files)}")
    
    if successful_imports > 0:
        print(f"\n🎉 Successfully imported {successful_imports} characters!")
        print("Characters are now available in the clean RDBMS schema.")
    
    # Show final character count
    try:
        conn = await get_database_connection()
        total_characters = await conn.fetchval("SELECT COUNT(*) FROM characters WHERE is_active = true")
        await conn.close()
        print(f"📈 Total active characters in database: {total_characters}")
    except Exception as e:
        print(f"⚠️  Could not get final character count: {e}")

if __name__ == "__main__":
    asyncio.run(main())