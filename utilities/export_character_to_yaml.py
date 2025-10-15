#!/usr/bin/env python3
"""
Export Character CDL Data to YAML
Exports complete character data from structured RDBMS schema to YAML format
"""

import os
import sys
import asyncio
import asyncpg
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Database connection settings
os.environ.setdefault('POSTGRES_HOST', 'localhost')
os.environ.setdefault('POSTGRES_PORT', '5433')
os.environ.setdefault('POSTGRES_USER', 'whisperengine')
os.environ.setdefault('POSTGRES_PASSWORD', 'whisperengine_password')
os.environ.setdefault('POSTGRES_DB', 'whisperengine')


async def get_database_connection():
    """Get database connection"""
    return await asyncpg.connect(
        host=os.getenv('POSTGRES_HOST'),
        port=int(os.getenv('POSTGRES_PORT', '5432')),
        database=os.getenv('POSTGRES_DB'),
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD')
    )


async def export_character_to_yaml(character_name: str, output_dir: str = "exports") -> bool:
    """Export complete character CDL data to YAML format"""
    
    print(f"🚀 Exporting Character: {character_name}")
    print("=" * 70)
    
    # Connect to database
    try:
        conn = await get_database_connection()
        print("✅ Connected to database")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    
    try:
        # 1. Get main character record
        character = await conn.fetchrow("""
            SELECT id, name, normalized_name, occupation, description,
                   archetype, allow_full_roleplay, is_active,
                   created_at, updated_at
            FROM characters
            WHERE LOWER(normalized_name) = LOWER($1) OR LOWER(name) = LOWER($1)
        """, character_name)
        
        if not character:
            print(f"❌ Character '{character_name}' not found in database")
            await conn.close()
            return False
        
        char_id = character['id']
        char_name = character['name']
        print(f"✅ Found character: {char_name} (ID: {char_id})")
        
        # Initialize export data structure (Schema v2.0 - matches web UI format)
        export_data = {
            'name': char_name,
            'identity': {
                'name': char_name,
                'occupation': character['occupation'],
                'description': character['description'],
                'archetype': character['archetype'],
                'allow_full_roleplay_immersion': character['allow_full_roleplay']
            },
            'metadata': {
                'database_id': character['id'],
                'normalized_name': character['normalized_name'],
                'export_date': datetime.now().isoformat(),
                'created_at': character['created_at'].isoformat() if character['created_at'] else None,
                'updated_at': character['updated_at'].isoformat() if character['updated_at'] else None,
                'is_active': character['is_active'],
                'schema_version': '2.0',
                'source': 'whisperengine_python_export_comprehensive'
            }
        }
        
        # Export personality_traits and character_values
        print("\n🎭 Exporting personality traits and values...")
        trait_rows = await conn.fetch("""
            SELECT trait_name, trait_value, intensity, description
            FROM personality_traits WHERE character_id = $1
        """, char_id)
        
        value_rows = await conn.fetch("""
            SELECT value_key, value_description, importance_level, category
            FROM character_values WHERE character_id = $1
            ORDER BY importance_level DESC
        """, char_id)
        
        if trait_rows or value_rows:
            export_data['personality'] = {}
            
            # Big Five traits
            if trait_rows:
                big_five_names = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']
                big_five = {}
                
                for row in trait_rows:
                    trait_name = row['trait_name'].lower()
                    if trait_name in big_five_names:
                        big_five[trait_name] = row['trait_value']
                
                if big_five:
                    export_data['personality']['big_five'] = big_five
                    print(f"   ✅ Exported {len(big_five)} Big Five traits")
            
            # Values
            if value_rows:
                values = []
                for row in value_rows:
                    values.append(row['value_description'] or row['value_key'])
                
                export_data['personality']['values'] = values
                print(f"   ✅ Exported {len(values)} character values")

        # Export character_background
        print("\n📜 Exporting background...")
        background_rows = await conn.fetch("""
            SELECT id, category, period, title, description, date_range, importance_level
            FROM character_background WHERE character_id = $1
            ORDER BY importance_level DESC
        """, char_id)
        
        if background_rows:
            background_entries = []
            for row in background_rows:
                background_entries.append({
                    'id': row['id'],
                    'category': row['category'],
                    'title': row['title'],
                    'description': row['description'],
                    'period': row['period'],
                    'importance_level': row['importance_level']
                })
            export_data['background'] = {'entries': background_entries}
            print(f"   ✅ Exported {len(background_entries)} background entries")

        # Export character_interest_topics (comprehensive format)
        print("\n🎯 Exporting interests...")
        interest_rows = await conn.fetch("""
            SELECT id, category, interest_text, proficiency_level, importance
            FROM character_interest_topics WHERE character_id = $1
        """, char_id)
        
        if interest_rows:
            interest_entries = []
            for row in interest_rows:
                interest_entries.append({
                    'id': row['id'],
                    'category': row['category'],
                    'interest_text': row['interest_text'],
                    'proficiency_level': row['proficiency_level'],
                    'importance': row['importance']
                })
            export_data['interests'] = {'entries': interest_entries}
            print(f"   ✅ Exported {len(interest_entries)} interest entries")

        # Export character_communication_patterns
        print("\n💬 Exporting communication patterns...")
        comm_pattern_rows = await conn.fetch("""
            SELECT id, pattern_type, pattern_name, pattern_value, context, frequency
            FROM character_communication_patterns WHERE character_id = $1
        """, char_id)
        
        if comm_pattern_rows:
            comm_patterns = []
            for row in comm_pattern_rows:
                comm_patterns.append({
                    'id': row['id'],
                    'pattern_type': row['pattern_type'],
                    'pattern_name': row['pattern_name'],
                    'pattern_value': row['pattern_value'],
                    'context': row['context'],
                    'frequency': row['frequency']
                })
            export_data['communication_patterns'] = {'patterns': comm_patterns}
            print(f"   ✅ Exported {len(comm_patterns)} communication patterns")

        # Export character_speech_patterns (comprehensive format)
        print("\n🗨️  Exporting speech patterns...")
        speech_pattern_rows = await conn.fetch("""
            SELECT id, pattern_type, pattern_value, usage_frequency, context, priority
            FROM character_speech_patterns WHERE character_id = $1
            ORDER BY priority DESC
        """, char_id)
        
        if speech_pattern_rows:
            speech_patterns = []
            for row in speech_pattern_rows:
                speech_patterns.append({
                    'id': row['id'],
                    'pattern_type': row['pattern_type'],
                    'pattern_value': row['pattern_value'],
                    'usage_frequency': row['usage_frequency'],
                    'context': row['context'],
                    'priority': row['priority']
                })
            export_data['speech_patterns'] = {'patterns': speech_patterns}
            print(f"   ✅ Exported {len(speech_patterns)} speech patterns")

        # Export character_response_guidelines (response style)
        print("\n� Exporting response style...")
        response_rows = await conn.fetch("""
            SELECT id, guideline_type, guideline_content, priority
            FROM character_response_guidelines WHERE character_id = $1
            ORDER BY priority DESC
        """, char_id)
        
        if response_rows:
            response_items = []
            for row in response_rows:
                response_items.append({
                    'id': row['id'],
                    'item_type': row['guideline_type'],
                    'item_text': row['guideline_content'],
                    'sort_order': row['priority']
                })
            export_data['response_style'] = {'items': response_items}
            print(f"   ✅ Exported {len(response_items)} response style guidelines")
        
        await conn.close()
        
        # Summary
        total_sections = 0
        if 'personality' in export_data: total_sections += 1
        if 'background' in export_data: total_sections += 1
        if 'interests' in export_data: total_sections += 1
        if 'communication_patterns' in export_data: total_sections += 1
        if 'speech_patterns' in export_data: total_sections += 1
        if 'response_style' in export_data: total_sections += 1
        
        print(f"\n📊 Total sections exported: {total_sections}")
        print(f"📊 Export format: Schema v2.0 (compatible with character editor forms)")
        
        # Write to YAML file
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{character['normalized_name']}_comprehensive_export_{timestamp}.yaml"
        filepath = output_path / filename
        
        print(f"\n💾 Writing to file: {filepath}")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(export_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False, width=120)
        
        print("\n" + "=" * 70)
        print("🎉 Export Complete!")
        print("=" * 70)
        print(f"\n📄 File: {filepath}")
        print(f"📦 Character: {char_name}")
        print(f"🎭 Archetype: {character['archetype']}")
        print(f"📊 Total sections exported: {total_sections}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Export failed: {e}")
        import traceback
        traceback.print_exc()
        await conn.close()
        return False


async def list_characters():
    """List all available characters in the database"""
    try:
        conn = await get_database_connection()
        characters = await conn.fetch("""
            SELECT id, name, normalized_name, occupation, archetype, is_active
            FROM characters
            WHERE is_active = true
            ORDER BY name
        """)
        await conn.close()
        return characters
    except Exception as e:
        print(f"❌ Failed to list characters: {e}")
        return []


async def main():
    """Main export function"""
    
    if len(sys.argv) < 2:
        print("🎭 WhisperEngine CDL Character Export to YAML")
        print("=" * 70)
        print("\nUsage:")
        print("  python export_character_to_yaml.py <character_name> [output_dir]")
        print("\nExamples:")
        print("  python export_character_to_yaml.py aetheris")
        print("  python export_character_to_yaml.py elena exports/backups")
        print("\nAvailable characters:")
        
        characters = await list_characters()
        if characters:
            print()
            for char in characters:
                print(f"  • {char['name']} ({char['normalized_name']}) - {char['occupation']}")
        else:
            print("  (No characters found in database)")
        
        return
    
    character_name = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "exports"
    
    success = await export_character_to_yaml(character_name, output_dir)
    
    if success:
        print("\n✅ Export completed successfully!")
        print(f"   Character '{character_name}' exported to YAML format")
    else:
        print("\n❌ Export failed - see errors above")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
